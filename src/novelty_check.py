#!/usr/bin/env python3
"""
喵哲学概念新度验证脚本 v2.1
借鉴 SkillOpt validation-gate 机制：
- 用 ov find CLI 做 semantic search，计算新概念与已有概念的相似度
- 自动检测新概念是否落在已穷尽的概念族内（uri 归属判定，无需硬编码关键词）
- 输出 PASS / WARN / REJECT 三种判定

用法：
    python novelty_check.py --topic "核心命题一句话"
    python novelty_check.py --topic "累积是垂直连续性" --json
"""

import argparse
import json
import subprocess
import sys
import yaml
from pathlib import Path

CONFIG_DIR = Path.home() / ".hermes" / "meow-philosophy"
BUFFER_FILE = CONFIG_DIR / "rejected-buffer.yaml"
VIKING_SCOPE = "viking://resources/meow-philosophy/"


def load_config():
    """Load rejected buffer and novelty thresholds."""
    if BUFFER_FILE.exists():
        with open(BUFFER_FILE) as f:
            return yaml.safe_load(f)
    return {}


def ov_find(query: str, limit: int = 8) -> list:
    """Call ov find CLI for semantic search. Returns list of {uri, score}."""
    try:
        result = subprocess.run(
            ["ov", "find", query,
             "--uri", VIKING_SCOPE,
             "--limit", str(limit),
             "--output", "json",
             "--compact"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print(f"[WARN] ov find failed: {result.stderr[:200]}", file=sys.stderr)
            return []
        stdout = result.stdout.strip()
        json_start = stdout.find("{")
        if json_start == -1:
            print(f"[WARN] ov find: no JSON in output", file=sys.stderr)
            return []
        data = json.loads(stdout[json_start:])
        if not data.get("ok"):
            return []
        items = []
        for kind in ["resources", "memories", "skills"]:
            for item in data.get("result", {}).get(kind, []):
                items.append({
                    "uri": item.get("uri", ""),
                    "score": item.get("score", 0.0),
                })
        items.sort(key=lambda x: x["score"], reverse=True)
        return items[:limit]
    except Exception as e:
        print(f"[WARN] ov find error: {e}", file=sys.stderr)
        return []


def check_exhausted_families(search_results: list, config: dict) -> dict:
    """
    用 semantic search 结果做概念族归属判定——不再依赖硬编码关键词。

    逻辑：
    1. 对每个 exhausted family，取其 members 列表
    2. 遍历 search_results，看哪些结果的 URI 包含 family member 名
    3. 计算「族污染度」= 命中数 / 总结果数
    4. 污染度 > 阈值 → 警告

    返回 {warnings: [...], contamination: {family_name: ratio, ...}}
    """
    warnings = []
    contamination = {}
    families = config.get("exhausted_families", {})
    total_results = len(search_results)

    if total_results == 0:
        return {"warnings": [], "contamination": {}}

    for family_name, family_data in families.items():
        if family_data.get("status") != "exhausted":
            continue

        members = family_data.get("members", [])
        if not members:
            continue

        # Count how many search results match this family's members
        # Only count matches with score > 0.35 (filter out semantic noise)
        MIN_FAMILY_SCORE = 0.35
        matched = []
        for result in search_results:
            uri = result.get("uri", "")
            for member in members:
                if member in uri and result.get("score", 0) > MIN_FAMILY_SCORE:
                    matched.append(result)
                    break  # count once per result

        ratio = len(matched) / total_results

        if ratio > 0:
            contamination[family_name] = round(ratio, 2)
            avg_score = sum(r["score"] for r in matched) / len(matched) if matched else 0
            cooldown = family_data.get("cooldown_until", "?")
            note = family_data.get("note", "")

            if ratio >= 0.6:
                level = "🚫 重度污染"
            elif ratio >= 0.3:
                level = "⚠️ 中度污染"
            else:
                level = "💡 轻度接触"

            warnings.append(
                f"{level} 「{family_name}」族: "
                f"top-{total_results} 中 {len(matched)}/{total_results} 篇 ({ratio:.0%}) "
                f"来自该族 (均分 {avg_score:.3f}, 冷却至 {cooldown})"
            )

    return {"warnings": warnings, "contamination": contamination}


def main():
    parser = argparse.ArgumentParser(description="喵哲学概念新度验证 v2.1")
    parser.add_argument("--topic", required=True, help="新概念核心命题（一句话）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    config = load_config()

    # 阈值配置
    reject_threshold = config.get("novelty", {}).get("reject_threshold", 0.80)
    warn_threshold = config.get("novelty", {}).get("warn_threshold", 0.50)

    # === 步骤 1: Semantic search ===
    search_results = ov_find(args.topic, limit=8)

    nearest = None
    if search_results:
        nearest = search_results[0]
        nearest_score = nearest.get("score", 0.0)
        nearest_uri = nearest.get("uri", "unknown")
    else:
        nearest_score = 0.0
        nearest_uri = "(ov find 返回空 — 可能是全新方向!)"

    # === 步骤 2: 概念族归属判定（自动，无需硬编码关键词） ===
    family_check = check_exhausted_families(search_results, config)

    # === 步骤 3: 判定 ===
    verdict = "PASS"
    reasons = []

    if nearest_score > reject_threshold:
        verdict = "REJECT"
        reasons.append(f"相似度 {nearest_score:.3f} > {reject_threshold}，与 {nearest_uri} 过于接近")
    elif nearest_score > warn_threshold:
        verdict = "WARN"
        reasons.append(f"相似度 {nearest_score:.3f} 在 {warn_threshold}-{reject_threshold} 之间，需证明本质差异")

    if family_check["warnings"]:
        reasons.extend(family_check["warnings"])
        # 如果有重度污染（任一 family ratio >= 0.6），降级判定
        high_contamination = any(r >= 0.6 for r in family_check["contamination"].values())
        if high_contamination and verdict == "PASS":
            verdict = "WARN"
        elif high_contamination and verdict == "WARN":
            verdict = "REJECT"
        elif verdict == "PASS":
            verdict = "WARN"

    # === 步骤 4: 邻居可视化 ===
    neighbors = []
    for r in search_results[:5]:
        short_uri = r["uri"].replace(VIKING_SCOPE, "").split("/")[0] if r["uri"] else "?"
        neighbors.append(f"  {r['score']:.3f}  {short_uri}")

    # === 输出 ===
    result = {
        "topic": args.topic,
        "verdict": verdict,
        "nearest_concept": nearest_uri,
        "similarity": round(nearest_score, 3),
        "reject_threshold": reject_threshold,
        "warn_threshold": warn_threshold,
        "neighbors": [{"uri": r["uri"], "score": round(r["score"], 3)} for r in search_results[:5]],
        "family_contamination": family_check["contamination"],
        "reasons": reasons,
        "guidance": _guidance(verdict)
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        neighbor_lines = "\n".join(neighbors) if neighbors else "  (无结果)"
        reason_lines = "\n".join(f"  {r}" for r in reasons) if reasons else "  ✅ 无警告"
        contamination_summary = ""
        if family_check["contamination"]:
            parts = [f"{k}: {v:.0%}" for k, v in family_check["contamination"].items()]
            contamination_summary = "  " + " | ".join(parts)

        print(f"""
╔══════════════════════════════════════════╗
║     🐱 喵哲学 概念新度验证 v2.1       ║
╠══════════════════════════════════════════╣
║  主题: {args.topic[:50]}
║  ──────────────────────────────────
║  📍 最近邻居:
{neighbor_lines}
║  ──────────────────────────────────
║  📊 族污染度: {contamination_summary or '  —'}
║  ──────────────────────────────────
║  判定: {_verdict_icon(verdict)} {verdict}
{reason_lines}
║  ──────────────────────────────────
║  💡 {_guidance(verdict)}
╚══════════════════════════════════════════╝
""")

    sys.exit(0 if verdict == "PASS" else (0 if verdict == "WARN" else 1))


def _verdict_icon(verdict: str) -> str:
    return {"PASS": "✅", "WARN": "⚠️", "REJECT": "🚫"}.get(verdict, "❓")


def _guidance(verdict: str) -> str:
    return {
        "PASS": "方向安全！记得喵味要足，别写成论文喵~",
        "WARN": "有风险——要么证明本质差异，要么换方向。",
        "REJECT": "太接近已有概念了，果断换方向喵！"
    }[verdict]


if __name__ == "__main__":
    main()
