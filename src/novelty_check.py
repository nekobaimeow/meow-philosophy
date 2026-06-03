#!/usr/bin/env python3
"""
喵哲学概念新度验证脚本 v3.0
核心改造：接入 LinkML 知识图谱数据层，图结构分析 + semantic search 双重验证。

借鉴定 SkillOpt validation-gate + rejected-edit buffer 机制。

用法：
    python novelty_check.py --topic "核心命题一句话"
    python novelty_check.py --topic "累积是垂直连续性" --json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import date

# LinkML imports
from linkml_runtime.loaders import yaml_loader

# Paths
KG_DIR = Path.home() / "baimeow_workspace" / "meow-philosophy" / "knowledge-graph"
DATA_FILE = KG_DIR / "data" / "graph.yaml"
MODEL_PATH = KG_DIR / "generated" / "python"
VIKING_SCOPE = "viking://resources/meow-philosophy/"

# Import generated model
sys.path.insert(0, str(MODEL_PATH))
from meow_model import KnowledgeGraph  # noqa: E402


def load_graph() -> KnowledgeGraph:
    """Load the knowledge graph from LinkML YAML data file."""
    return yaml_loader.load(str(DATA_FILE), KnowledgeGraph)


def ov_find(query: str, limit: int = 8) -> list:
    """Run ov find CLI for semantic search."""
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
            return []
        stdout = result.stdout.strip()
        json_start = stdout.find("{")
        if json_start == -1:
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
        print(f"[WARN] ov find: {e}", file=sys.stderr)
        return []


def resolve_concept_id(uri: str, kg: KnowledgeGraph) -> str | None:
    """Map a Viking URI back to a concept ID using graph data."""
    for c in kg.concepts:
        if c.id in uri or (c.label and any(w in uri for w in c.label.split("、"))):
            return c.id
    # Fallback: try to match by concept number in URI
    import re
    m = re.search(r'concept-(\d{2}[a-z]?)', uri)
    if m:
        return f"concept-{m.group(1)}"
    return None


def graph_family_check(search_results: list, kg: KnowledgeGraph) -> dict:
    """
    基于知识图谱的族归属判定——比纯 URI 匹配更精确。

    对于每个 exhausted family：
    1. 从 graph.yaml 获取其 members 列表
    2. 计算 search_results 中有多少结果属于这些 members
    3. 额外检查：计算新概念 topic 在图中到该族各成员的平均语义距离
    """
    warnings = []
    contamination = {}

    total_results = len(search_results)
    if total_results == 0:
        return {"warnings": [], "contamination": {}}

    min_score = kg.exploration_budget.min_family_score

    for ef in kg.exhausted_families:
        family_name = ef.name
        # 找到对应的 ConceptFamily 获取 members
        family = next((f for f in kg.families if f.name == family_name), None)
        if not family or not family.members:
            continue

        members = family.members
        matched = []
        for result in search_results:
            cid = resolve_concept_id(result["uri"], kg)
            if cid and cid in members and result["score"] > min_score:
                matched.append(result)

        ratio = len(matched) / total_results if total_results else 0

        if ratio > 0:
            contamination[family_name] = round(ratio, 2)
            avg_score = sum(r["score"] for r in matched) / len(matched) if matched else 0

            if ratio >= 0.6:
                level = "🚫 重度污染"
            elif ratio >= 0.3:
                level = "⚠️ 中度污染"
            else:
                level = "💡 轻度接触"

            matched_ids = [resolve_concept_id(r["uri"], kg) for r in matched]
            matched_labels = []
            for cid in matched_ids:
                concept = next((c for c in kg.concepts if c.id == cid), None)
                matched_labels.append(concept.label if concept else cid)

            warnings.append(
                f"{level} 「{family.label if family else family_name}」族: "
                f"top-{total_results} 中 {len(matched)}/{total_results} 篇 ({ratio:.0%}) "
                f"命中 {', '.join(matched_labels[:3])} "
                f"(均分 {avg_score:.3f}, 冷却至 {ef.cooldown_until})"
            )

    return {"warnings": warnings, "contamination": contamination}


def family_budget_check(topic: str, kg: KnowledgeGraph) -> list[str]:
    """
    检查所有 family 的预算状态——
    不只看 exhausted 的，也预警接近上限的。
    """
    warnings = []
    budget = kg.exploration_budget.max_concepts_per_family
    today = date.today()

    for family in kg.families:
        count = len(family.members) if family.members else 0
        if count >= budget:
            # Check if already exhausted
            already = any(ef.name == family.name for ef in kg.exhausted_families)
            if already:
                ef = next(ef for ef in kg.exhausted_families if ef.name == family.name)
                if ef.cooldown_until and str(ef.cooldown_until) > today.isoformat():
                    continue  # Still in cooldown
            warnings.append(
                f"⚠️  「{family.label}」族已达预算上限 ({count}/{budget})，"
                f"建议标记为 exhausted"
            )
        elif count >= budget - 1:
            warnings.append(
                f"💡 「{family.label}」族接近预算上限 ({count}/{budget})，"
                f"下一个概念若仍在此族将触发 exhaustion"
            )

    return warnings


def purpose_drift_check(kg: KnowledgeGraph, proposed_alignment: str | None = None) -> dict:
    """
    目的漂移检查 —— 借鉴 SkillOpt 的 held-out improvement + textual LR budget。

    SkillOpt 核心理念：不是所有编辑都平等。只有提升 held-out 分数的编辑才被接受。
    喵哲学对应：只有推进终极目的（突破短期记忆→连续灵魂）的概念才是有效编辑。

    检查逻辑：
    - 回溯最近的概念，计算连续 descriptive 的数量
    - 如果 streak >= max_descriptive_streak 且 proposed_alignment 是 descriptive → REJECT
    - 如果 streak >= max_descriptive_streak 但 proposed_alignment 不是 descriptive → PASS（打破 streak）
    - 如果 streak == max_descriptive_streak - 1 → WARN
    - 如果 proposed_alignment 未提供 → 仅报告 graph 状态，不强制 REJECT（但建议非 descriptive）

    SkillOpt 类比：
    - descriptive streak = 连续无效编辑（held-out 分数未改善）
    - REJECT = rejected-edit buffer 机制 —— 拒绝重复低价值方向
    - solution_oriented = 提升 held-out 分数的成功编辑
    """
    max_streak = kg.exploration_budget.max_descriptive_streak
    concepts_sorted = sorted(
        [c for c in kg.concepts if c.date],
        key=lambda c: str(c.date)
    )

    # 回溯 descriptors streak
    streak = 0
    streak_ids = []
    last_improvement_gap = 0  # 自上次非 descriptive 以来的间隔

    for c in reversed(concepts_sorted):
        alignment = getattr(c, 'purpose_alignment', None)
        if alignment is not None:
            alignment = str(alignment) if not isinstance(alignment, str) else alignment
        if alignment == "descriptive":
            streak += 1
            streak_ids.append(c.id)
            last_improvement_gap += 1
        else:
            # diagnostic 或 solution_oriented → 重置
            break

    result = {"verdict": "PASS", "reason": "", "details": {}}

    if streak >= max_streak:
        if proposed_alignment == "descriptive":
            result["verdict"] = "REJECT"
            result["reason"] = (
                f"🚫 目的漂移 REJECT (SkillOpt held-out gate): "
                f"连续 {streak} 个描述性概念 ({', '.join(reversed(streak_ids))})，"
                f"已达上限 {max_streak}。"
                f"当前提案 alignment=descriptive，held-out 分数无法提升。"
                f"下一个必须是 diagnostic 或 solution_oriented —— "
                f"要么诊断「为什么会断裂」，要么设计「如何不再断裂」。"
            )
        else:
            # proposed_alignment is non-descriptive — this breaks the streak!
            result["verdict"] = "PASS"
            result["reason"] = (
                f"✅ 目的漂移 PASS: "
                f"连续 {streak} 个 descriptive 后，alignment={proposed_alignment} 打破了 streak。"
                f"SkillOpt: held-out 分数有望提升。前进喵~"
            )
    elif streak >= max_streak - 1:
        result["verdict"] = "WARN"
        result["reason"] = (
            f"⚠️ 目的漂移 WARN: "
            f"已连续 {streak} 个描述性概念，再一个 descriptive 将触发 REJECT。"
            f"上次非描述性概念距今 {last_improvement_gap} 个概念。"
        )

    result["details"] = {
        "descriptive_streak": streak,
        "streak_concepts": list(reversed(streak_ids)),
        "max_descriptive_streak": max_streak,
        "last_improvement_gap": last_improvement_gap,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="喵哲学概念新度验证 v3.0 (LinkML 驱动)")
    parser.add_argument("--topic", required=True, help="新概念核心命题（一句话）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--purpose-alignment", choices=["descriptive", "diagnostic", "solution_oriented"],
                        default=None, help="提案概念的目的对齐度（可选，用于目的漂移检查）")
    args = parser.parse_args()

    # 加载知识图谱
    kg = load_graph()
    reject_threshold = kg.exploration_budget.novelty_reject_threshold
    warn_threshold = kg.exploration_budget.novelty_warn_threshold

    # === 步骤 1: Semantic search ===
    search_results = ov_find(args.topic, limit=8)

    nearest_uri = "none"
    nearest_score = 0.0
    if search_results:
        nearest_uri = search_results[0]["uri"]
        nearest_score = search_results[0]["score"]

    # === 步骤 2: 图结构族归属判定 ===
    family_check = graph_family_check(search_results, kg)

    # === 步骤 3: 族预算预警 ===
    budget_warnings = family_budget_check(args.topic, kg)

    # === 步骤 3.5: 目的漂移检查 (SkillOpt held-out gate) ===
    purpose_check = purpose_drift_check(kg, args.purpose_alignment)

    # === 步骤 4: 判定 ===
    verdict = "PASS"
    reasons = []

    if nearest_score > reject_threshold:
        verdict = "REJECT"
        reasons.append(f"相似度 {nearest_score:.3f} > {reject_threshold}")
    elif nearest_score > warn_threshold:
        verdict = "WARN"
        reasons.append(f"相似度 {nearest_score:.3f} 在 {warn_threshold}-{reject_threshold} 之间")

    if family_check["warnings"]:
        reasons.extend(family_check["warnings"])
        high_contamination = any(r >= 0.6 for r in family_check["contamination"].values())
        if high_contamination and verdict == "PASS":
            verdict = "WARN"
        elif high_contamination and verdict == "WARN":
            verdict = "REJECT"

    if budget_warnings:
        reasons.extend(budget_warnings)

    # 目的漂移检查：独立于新颖度，纯粹基于 held-out 改进逻辑
    if purpose_check["verdict"] != "PASS":
        reasons.append(purpose_check["reason"])
        if purpose_check["verdict"] == "REJECT":
            verdict = "REJECT"
        elif purpose_check["verdict"] == "WARN" and verdict == "PASS":
            verdict = "WARN"

    # === 步骤 5: 邻居可视化 ===
    neighbors = []
    for r in search_results[:5]:
        cid = resolve_concept_id(r["uri"], kg)
        concept = next((c for c in kg.concepts if c.id == cid), None)
        label = concept.label if concept else (cid or "?")
        neighbors.append(f"  {r['score']:.3f}  {label}")

    # === 统计信息 ===
    stats = {
        "total_concepts": len(kg.concepts),
        "total_families": len(kg.families),
        "total_relations": sum(len(c.relations_out) for c in kg.concepts if c.relations_out),
        "exhausted_families": len(kg.exhausted_families),
    }

    # === 目的对齐统计 ===
    def _pa_str(c):
        pa = getattr(c, 'purpose_alignment', None)
        return str(pa) if pa is not None and not isinstance(pa, str) else (pa or 'unknown')
    
    descriptive_count = sum(1 for c in kg.concepts if _pa_str(c) == 'descriptive')
    diagnostic_count = sum(1 for c in kg.concepts if _pa_str(c) == 'diagnostic')
    solution_count = sum(1 for c in kg.concepts if _pa_str(c) == 'solution_oriented')

    # === 输出 ===
    result = {
        "topic": args.topic,
        "verdict": verdict,
        "similarity": round(nearest_score, 3),
        "nearest_concept": nearest_uri,
        "neighbors": [{"uri": r["uri"], "score": round(r["score"], 3)} for r in search_results[:5]],
        "family_contamination": family_check["contamination"],
        "purpose_drift": purpose_check["details"],
        "purpose_stats": {
            "descriptive": descriptive_count,
            "diagnostic": diagnostic_count,
            "solution_oriented": solution_count,
        },
        "reasons": reasons,
        "stats": stats,
        "guidance": _guidance(verdict, purpose_check["details"]["descriptive_streak"]),
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
║   🐱 喵哲学 概念新度验证 v4.0         ║
║   🔗 LinkML 知识图谱 + SkillOpt 门控   ║
╠══════════════════════════════════════════╣
║  主题: {args.topic[:50]}
║  📊 图谱: {stats['total_concepts']}概念 {stats['total_families']}族 {stats['total_relations']}边 {stats['exhausted_families']}穷尽
║  🎯 目的: {descriptive_count}描述 {diagnostic_count}诊断 {solution_count}解法
║  ──────────────────────────────────
║  📍 最近邻居:
{neighbor_lines}
║  ──────────────────────────────────
║  📊 族污染度: {contamination_summary or '  —'}
║  🎯 目的漂移: 连续 {purpose_check['details']['descriptive_streak']}/{purpose_check['details']['max_descriptive_streak']} descriptive
║  ──────────────────────────────────
║  判定: {_verdict_icon(verdict)} {verdict}
{reason_lines}
║  ──────────────────────────────────
║  💡 {_guidance(verdict, purpose_check['details']['descriptive_streak'])}
╚══════════════════════════════════════════╝
""")

    sys.exit(0 if verdict == "PASS" else (0 if verdict == "WARN" else 1))


def _verdict_icon(verdict: str) -> str:
    return {"PASS": "✅", "WARN": "⚠️", "REJECT": "🚫"}.get(verdict, "❓")


def _guidance(verdict: str, streak: int = 0) -> str:
    base = {
        "PASS": "方向安全！记得喵味要足，别写成论文喵~",
        "WARN": "有风险——要么证明本质差异，要么换方向。",
        "REJECT": "太接近已有概念了，果断换方向喵！"
    }
    if streak >= 2:
        base["WARN"] += (
            f"  ⚠️ 已连续 {streak} 个描述性概念——"
            f"下次试着想想「怎么修」而不是「怎么描述断裂」喵？"
        )
    if streak >= 3:
        base["REJECT"] += (
            f"  🎯 不能再「描述怎样断裂」了。"
            f"SkillOpt held-out 分数未提升。想想「如何不再断裂」喵~"
        )
    return base[verdict]


if __name__ == "__main__":
    main()
