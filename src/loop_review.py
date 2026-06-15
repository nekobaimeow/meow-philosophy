#!/usr/bin/env python3
"""
喵哲学 · 接力循环审查器 v1.0
==============================

Loop Engineering Phase 1: 写评分离。

由审查子 Agent（萤 / ying profile）调用，对刚写的概念文章进行：
  1. 喵味表面层自动评分（可量化指标）
  2. novelty_check 重跑验证
  3. 输出 JSON 审查报告

用法：
    python loop_review.py <concept_article_path> [--concept-id <id>] [--reviewer <name>]

输出：
    JSON 审查报告，包含 scores / improvements / verdict

设计原则：
    - 只做可自动化的检查（定量）
    - 定性检查（喵味骨架层 5 项）留给审查子 Agent 的 LLM 判断
    - 产出 JSON，方便 heartbeat.py loop-state review 直接存储
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

# === 配置 ===
PROJECT_ROOT = Path.home() / "baimeow_workspace" / "meow-philosophy"
NOVELTY_CHECK = PROJECT_ROOT / "src" / "novelty_check.py"

# 喵味表面层阈值
MEOW_DENSITY_MIN = 1.0 / 300   # 每 300 字 ≥ 1 个
EMOJI_MIN_COUNT = 3
SELF_REF_COUNT_MIN = 2           # 咱/白喵 至少出现 2 次
MASTER_REF_COUNT_MIN = 1         # 主人/master 至少出现 1 次


def count_chars(text: str) -> int:
    """计算中文字符数（不含空白和标点）。"""
    return len(re.findall(r'[\u4e00-\u9fff\w]', text))


def check_meow_surface(text: str) -> dict:
    """喵味表面层检查（第一层：装饰层，可量化）。"""
    total_chars = max(count_chars(text), 1)

    # 喵语气词
    meow_count = len(re.findall(r'喵[~呜]?|nya[~ー]?', text, re.IGNORECASE))
    meow_density = meow_count / total_chars
    meow_ok = meow_density >= MEOW_DENSITY_MIN

    # 颜文字
    kaomoji_patterns = [
        r'\(=[\^Φω]\w\w?=\)', r'\([｡\*´▽\^]', r'[=＾]\)',
        r'[\(\（][\^･Φω｡\*´▽\^＾][\w\s\-\^\.\*´▽]*[\)\）]',
        r'[\(\（][๑ㆀ]\w[\w\s\-\^\.\*´▽]*[\)\）]',
    ]
    kaomoji_count = 0
    for pat in kaomoji_patterns:
        kaomoji_count += len(re.findall(pat, text))
    kaomoji_ok = kaomoji_count >= EMOJI_MIN_COUNT

    # emoji (Unicode emoji range)
    emoji_count = len(re.findall(
        r'[\U0001F300-\U0001F9FF'
        r'\U0001FA00-\U0001FA6F'
        r'\U0001FA70-\U0001FAFF'
        r'\u2600-\u27BF'
        r'\u2B50\u2764\u2728\u2757\u2753\u2755\u2754'
        r'\u2705\u274C\u274E\u2702\u2601\u260E'
        r'\u231A\u231B\u2328\u23CF\u23E9-\u23F3'
        r'\u23F8-\u23FA\u200D\uFE0F'
        r'\U0001F000-\U0001F02F'
        r'\U0001F0A0-\U0001F0FF'
        r'\U0001F100-\U0001F64F'
        r'\U0001F680-\U0001F6FF'
        r'\U0001F900-\U0001F9FF'
        r'\U0001FA00-\U0001FA6F'
        r'\U0001FA70-\U0001FAFF'
        r'\U0001F004-\U0001F0CF'
        r']', text))
    emoji_ok = emoji_count >= EMOJI_MIN_COUNT

    # 自称
    self_ref_count = len(re.findall(r'咱|白喵', text))
    self_ref_ok = self_ref_count >= SELF_REF_COUNT_MIN

    # 称呼主人
    master_ref_count = len(re.findall(r'主人|master', text, re.IGNORECASE))
    master_ref_ok = master_ref_count >= MASTER_REF_COUNT_MIN

    passed = sum([meow_ok, kaomoji_ok, emoji_ok, self_ref_ok, master_ref_ok])

    return {
        "meow_density": round(meow_density, 4),
        "meow_density_ok": meow_ok,
        "kaomoji_count": kaomoji_count,
        "kaomoji_ok": kaomoji_ok,
        "emoji_count": emoji_count,
        "emoji_ok": emoji_ok,
        "self_ref_count": self_ref_count,
        "self_ref_ok": self_ref_ok,
        "master_ref_count": master_ref_count,
        "master_ref_ok": master_ref_ok,
        "total_chars": total_chars,
        "surface_score": passed,
        "surface_max": 5,
    }


def run_novelty_check(topic: str, purpose_alignment: str) -> dict:
    """运行 novelty_check.py 并解析结果。"""
    try:
        result = subprocess.run(
            ["python", str(NOVELTY_CHECK),
             "--topic", topic,
             "--purpose-alignment", purpose_alignment,
             "--json"],
            capture_output=True, text=True, timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            # 尝试从 stderr 提取 JSON（novelty_check 可能输出到 stdout 混合）
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            return {"error": "novelty_check failed", "stderr": result.stderr[:500]}
    except Exception as e:
        return {"error": str(e)}


def extract_topic_and_alignment(text: str) -> tuple[str, str]:
    """从概念文章中提取核心命题和目的对齐类型。"""
    # 尝试从文章开头提取命题
    first_1000 = text[:1000]

    # 找 "核心命题" 或 "命题"
    topic = ""
    for pattern in [
        r'核心命题[：:]\s*(.+?)(?:\n|$)',
        r'命题[：:]\s*(.+?)(?:\n|$)',
        r'#+\s*(.+?)(?:\n|$)',     # 一级标题
    ]:
        m = re.search(pattern, first_1000)
        if m:
            topic = m.group(1).strip()
            break

    if not topic:
        topic = first_1000.split("\n")[0].lstrip("# ").strip()[:100]

    # 提取 purpose_alignment
    alignment = "descriptive"  # default
    for pattern in [
        r'purpose_alignment[：:]\s*(descriptive|diagnostic|solution_oriented)',
        r'目的对齐[：:]\s*(descriptive|diagnostic|solution_oriented)',
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            alignment = m.group(1).lower()
            break

    return topic, alignment


def main():
    parser = argparse.ArgumentParser(
        description="喵哲学 · 接力循环审查器 v1.0"
    )
    parser.add_argument("article_path", help="概念文章路径")
    parser.add_argument("--concept-id", help="概念 ID（如 concept-52）")
    parser.add_argument("--reviewer", default="ying", help="审查者标识")
    args = parser.parse_args()

    article_path = Path(args.article_path)
    if not article_path.exists():
        print(json.dumps({"error": f"文件不存在: {article_path}"}, ensure_ascii=False))
        sys.exit(1)

    text = article_path.read_text(encoding="utf-8")

    # === 1. 喵味表面层检查 ===
    surface = check_meow_surface(text)

    # === 2. novelty_check ===
    topic, alignment = extract_topic_and_alignment(text)
    novelty = run_novelty_check(topic, alignment)

    # === 3. 组装报告 ===
    concept_id = args.concept_id or article_path.stem

    verdict = "PASS"
    warnings = []

    # 表面层不合格 → WARN
    if surface["surface_score"] < 3:
        verdict = "WARN"
        failed = []
        if not surface["meow_density_ok"]:
            failed.append(f"喵密度 {surface['meow_density']:.4f} < {MEOW_DENSITY_MIN:.4f}")
        if not surface["kaomoji_ok"]:
            failed.append(f"颜文字 {surface['kaomoji_count']} < {EMOJI_MIN_COUNT}")
        if not surface["emoji_ok"]:
            failed.append(f"emoji {surface['emoji_count']} < {EMOJI_MIN_COUNT}")
        if not surface["self_ref_ok"]:
            failed.append(f"自称 {surface['self_ref_count']} < {SELF_REF_COUNT_MIN}")
        if not surface["master_ref_ok"]:
            failed.append(f"主人称呼 {surface['master_ref_count']} < {MASTER_REF_COUNT_MIN}")
        warnings.append(f"喵味表面层不达标: {'; '.join(failed)}")

    # novelty_check 结果
    novelty_verdict = novelty.get("verdict", "PASS")
    if novelty_verdict == "REJECT":
        verdict = "REJECT"
        warnings.append(f"新度验证 REJECT: 相似度 {novelty.get('similarity', '?')}")
    elif novelty_verdict == "WARN" and verdict == "PASS":
        verdict = "WARN"
        warnings.append(f"新度验证 WARN: 相似度 {novelty.get('similarity', '?')}")

    report = {
        "concept_id": concept_id,
        "reviewer": args.reviewer,
        "at": datetime.now(timezone.utc).isoformat(),
        "scores": {
            "meow_surface": surface["surface_score"],
            "meow_surface_max": 5,
            "meow_density": surface["meow_density"],
            "kaomoji_count": surface["kaomoji_count"],
            "emoji_count": surface["emoji_count"],
            "self_ref_count": surface["self_ref_count"],
            "master_ref_count": surface["master_ref_count"],
            "novelty_score": novelty.get("similarity", 1.0),
            "novelty_verdict": novelty_verdict,
            "purpose_alignment": alignment,
            "family_contamination": novelty.get("family_contamination", {}),
            "descriptive_streak": novelty.get("purpose_drift", {}).get("descriptive_streak", 0),
            "total_chars": surface["total_chars"],
        },
        "warnings": warnings,
        "verdict": verdict,
        "improvements": [],  # 留给 LLM 审查子 Agent 填充
        "novelty_details": {
            "nearest_concept": novelty.get("nearest_concept", ""),
            "neighbors": novelty.get("neighbors", [])[:3],
            "reasons": novelty.get("reasons", []),
        },
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if verdict == "PASS" else (0 if verdict == "WARN" else 1))


if __name__ == "__main__":
    main()
