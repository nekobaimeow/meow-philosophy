#!/usr/bin/env python3
"""
喵哲学图分析 —— 萤的领域！
基于 LinkML 知识图谱的图结构分析。

用法：
    python queries/centrality.py          # 中心性分析
    python queries/community.py           # 社区发现
    python queries/bridge.py              # 桥接概念检测
"""

import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent / "generated" / "python"))
from meow_model import KnowledgeGraph
from linkml_runtime.loaders import yaml_loader


def load_graph():
    data_file = Path(__file__).parent.parent / "data" / "graph.yaml"
    return yaml_loader.load(str(data_file), KnowledgeGraph)


def build_adjacency(kg: KnowledgeGraph):
    """构建邻接表 {concept_id: [target_ids]}"""
    adj = {}
    for c in kg.concepts:
        adj[c.id] = [r.target for r in (c.relations_out or [])]
    return adj


def out_degree(adj: dict) -> dict:
    """出度 = 每个概念指向多少个其他概念"""
    return {cid: len(targets) for cid, targets in adj.items()}


def in_degree(adj: dict) -> dict:
    """入度 = 每个概念被多少个其他概念指向"""
    indeg = Counter()
    for targets in adj.values():
        for t in targets:
            indeg[t] += 1
    return dict(indeg)


def main():
    kg = load_graph()
    adj = build_adjacency(kg)
    outd = out_degree(adj)
    ind = in_degree(adj)

    # 找中心性最高的概念
    total_deg = {cid: outd.get(cid, 0) + ind.get(cid, 0) for cid in adj}
    ranked = sorted(total_deg.items(), key=lambda x: x[1], reverse=True)

    print("🐱 喵哲学概念中心性分析\n")
    print(f"{'概念':<20} {'出度':>4} {'入度':>4} {'总度':>4}")
    print("-" * 36)
    for cid, total in ranked[:10]:
        concept = next((c for c in kg.concepts if c.id == cid), None)
        label = concept.label if concept else cid
        print(f"{label:<20} {outd.get(cid,0):>4} {ind.get(cid,0):>4} {total:>4}")

    # 桥接概念：指出度 ≥ 3 的概念
    bridges = [(cid, outd[cid]) for cid in outd if outd[cid] >= 3]
    if bridges:
        print(f"\n🌉 桥接概念（出度 ≥ 3）：")
        for cid, deg in sorted(bridges, key=lambda x: x[1], reverse=True):
            concept = next((c for c in kg.concepts if c.id == cid), None)
            print(f"  {concept.label if concept else cid} → {deg} 个方向")

    # 孤岛检测：入度 = 0 且出度 = 0
    islands = [cid for cid in adj if outd.get(cid, 0) == 0 and ind.get(cid, 0) == 0]
    if islands:
        print(f"\n🏝️ 孤岛概念（无入边无出边）：")
        for cid in islands:
            concept = next((c for c in kg.concepts if c.id == cid), None)
            print(f"  {concept.label if concept else cid}")


if __name__ == "__main__":
    main()
