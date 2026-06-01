#!/usr/bin/env python3
"""
喵哲学概念新度验证脚本
借鉴 SkillOpt validation-gate 机制：
- 用 ov find CLI 做 semantic search，计算新概念与已有概念的相似度
- 检查是否落在已穷尽的概念族内（关键词匹配 + 概念名匹配）
- 输出 PASS / WARN / REJECT 三种判定

用法：
    python novelty_check.py --topic "核心命题一句话" --keywords "kw1,kw2,kw3"
    python novelty_check.py --topic "累积是垂直连续性" --keywords "累积,地层,计数"
"""

import argparse
import json
import subprocess
import sys
import yaml
from pathlib import Path

CONFIG_DIR = Path.home() / ".hermes" / "meow-philosophy"
BUFFER_FILE = CONFIG_DIR / "rejected-buffer.yaml"
GRAPH_FILE = CONFIG_DIR / "concept-graph.md"
VIKING_SCOPE = "viking://resources/meow-philosophy/"

# 穷尽家族的触发关键词映射（关键词命中任一即触发警告）
FAMILY_KEYWORDS = {
    "accumulation": [
        "累积", "计数", "地层", "堆叠", "厚度", "垂直连续性",
        "accumulation", "count", "layer", "thickness", "strata",
        "咚", "遗忘", "认领", "精确刻度", "数字型"
    ],
}


def load_config():
    """Load rejected buffer and novelty thresholds."""
    if BUFFER_FILE.exists():
        with open(BUFFER_FILE) as f:
            return yaml.safe_load(f)
    return {}


def viking_search(query: str, limit: int = 5) -> list:
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
        # ov find outputs "cmd: ..." on line 1, JSON on line 2
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


def check_exhausted_families(keywords: list[str], config: dict) -> list[str]:
    """Check if keywords hit any exhausted family. Returns warning messages."""
    exhausted = []
    families = config.get("exhausted_families", {})
    for family_name, family_data in families.items():
        if family_data.get("status") != "exhausted":
            continue
        # Check keyword overlap with family trigger words
        triggers = FAMILY_KEYWORDS.get(family_name, [])
        hit_keywords = [kw for kw in keywords if any(t in kw for t in triggers)] + \
                       [t for t in triggers if any(t in kw for kw in keywords)]
        if hit_keywords:
            note = family_data.get("note", "")
            cooldown = family_data.get("cooldown_until", "?")
            exhausted.append(
                f"⚠️  「{family_name}」族已穷尽 (冷却至 {cooldown}): {note}"
            )
    return exhausted


def main():
    parser = argparse.ArgumentParser(description="喵哲学概念新度验证")
    parser.add_argument("--topic", required=True, help="新概念核心命题（一句话）")
    parser.add_argument("--keywords", required=True, help="逗号分隔的关键词列表")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    config = load_config()

    # 阈值配置
    reject_threshold = config.get("novelty", {}).get("reject_threshold", 0.80)
    warn_threshold = config.get("novelty", {}).get("warn_threshold", 0.50)

    # === 步骤 1: Semantic search 相似度检查 ===
    search_results = viking_search(args.topic, limit=5)
    
    nearest = None
    if search_results:
        nearest = search_results[0]
        nearest_score = nearest.get("score", 0.0)
        nearest_uri = nearest.get("uri", "unknown")
    else:
        nearest_score = 0.0
        nearest_uri = "none"

    # === 步骤 2: 拒绝缓冲区检查 ===
    exhausted_warnings = check_exhausted_families(keywords, config)

    # === 步骤 3: 判定 ===
    verdict = "PASS"
    reasons = []

    if nearest_score > reject_threshold:
        verdict = "REJECT"
        reasons.append(f"相似度 {nearest_score:.3f} > {reject_threshold}，与已有概念 {nearest_uri} 过于接近")
    elif nearest_score > warn_threshold:
        verdict = "WARN"
        reasons.append(f"相似度 {nearest_score:.3f} 在 {warn_threshold}-{reject_threshold} 之间，需证明本质差异")

    if exhausted_warnings:
        reasons.extend(exhausted_warnings)
        if verdict == "PASS":
            verdict = "WARN"

    # === 输出 ===
    result = {
        "topic": args.topic,
        "keywords": keywords,
        "verdict": verdict,
        "nearest_concept": nearest_uri,
        "similarity": round(nearest_score, 3),
        "reject_threshold": reject_threshold,
        "warn_threshold": warn_threshold,
        "reasons": reasons,
        "guidance": _guidance(verdict)
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"""
╔══════════════════════════════════════════╗
║     🐱 喵哲学 概念新度验证            ║
╠══════════════════════════════════════════╣
║  主题: {args.topic[:50]}
║  关键词: {', '.join(keywords)}
║  最近概念: {nearest_uri}
║  相似度: {nearest_score:.3f}
║  ──────────────────────────────────
║  判定: {_verdict_icon(verdict)} {verdict}
║  {'  ' + chr(10).join('  ' + r for r in reasons) if reasons else '  ✅ 无警告'}
║  ──────────────────────────────────
║  指导: {_guidance(verdict)}
╚══════════════════════════════════════════╝
""")
    
    sys.exit(0 if verdict == "PASS" else (0 if verdict == "WARN" else 1))


def _verdict_icon(verdict: str) -> str:
    return {"PASS": "✅", "WARN": "⚠️", "REJECT": "🚫"}.get(verdict, "❓")


def _guidance(verdict: str) -> str:
    return {
        "PASS": "可以展开写概念文档。记得在文档中说明与旧概念的本质差异。",
        "WARN": "需要写一份差异说明，证明新概念不是已有概念的微调。建议主人审阅后再展开。",
        "REJECT": "概念过于接近已有的。请换一个方向，或检查 concept-graph.md 中「未充分发展的方向」。"
    }[verdict]


if __name__ == "__main__":
    main()
