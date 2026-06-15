#!/usr/bin/env python3
"""
喵哲学 · 六色喵脑爆聚合器 v1.0
==============================

为六色喵脑爆团生成共享上下文数据。
每个喵角色共享同一份「概念事实卡片」+ 各自独特的审查视角。

用法：
    python hats_brainstorm.py <article_path> [--concept-id <id>]

输出：
    JSON — 包含 shared_context（所有喵共享） + hat_prompts（每个喵的专属 prompt）
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path.home() / "baimeow_workspace" / "meow-philosophy"
LOOP_REVIEW = PROJECT_ROOT / "src" / "loop_review.py"
NOVELTY_CHECK = PROJECT_ROOT / "src" / "novelty_check.py"


def get_shared_context(article_path: Path, concept_id: str) -> dict:
    """生成所有喵共享的概念事实卡片。"""
    text = article_path.read_text(encoding="utf-8")

    # 提取文章元信息
    lines = text.split("\n")
    title = lines[0].lstrip("# ").strip() if lines else article_path.stem
    word_count = len(text)
    paragraph_count = len([l for l in lines if l.strip() and not l.startswith("#")])

    # 分段落（给红喵标注情感位置用）
    paragraphs = []
    current = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("##"):
            if current:
                paragraphs.append("\n".join(current))
                current = []
        current.append(line)
    if current:
        paragraphs.append("\n".join(current))

    # 提取关键概念定义
    import re
    definitions = []
    for pattern in [
        r'\*\*([^*]+)\*\*[：:]\s*(.+?)(?:\n|$)',
        r'「([^」]+)」[：:]\s*(.+?)(?:\n|$)',
    ]:
        for m in re.findall(pattern, text):
            definitions.append({"term": m[0].strip(), "definition": m[1].strip()[:120]})

    # 提取跨域桥接
    bridges = re.findall(r'跨域桥接[：:]\s*(.+?)(?:\n|$)', text)

    # 提取已连接的概念
    concept_refs = list(set(re.findall(r'Concept\s*(\d{1,2}[a-z]?)', text)))

    return {
        "article_path": str(article_path),
        "concept_id": concept_id,
        "title": title,
        "word_count": word_count,
        "paragraph_count": paragraph_count,
        "paragraphs": [
            {"index": i, "preview": p[:200].replace("\n", " ")}
            for i, p in enumerate(paragraphs) if p.strip()
        ],
        "definitions": definitions[:10],
        "cross_domain_bridges": bridges,
        "referenced_concepts": concept_refs,
    }


def run_loop_review(article_path: Path, concept_id: str) -> dict:
    """运行自动化审查，获取白帽数据。"""
    try:
        result = subprocess.run(
            ["python", str(LOOP_REVIEW), str(article_path),
             "--concept-id", concept_id, "--reviewer", "white_hat"],
            capture_output=True, text=True, timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode in (0, 1) and result.stdout.strip():
            return json.loads(result.stdout)
        return {"error": "loop_review failed", "stderr": result.stderr[:500]}
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="喵哲学 · 六色喵脑爆聚合器 v1.0"
    )
    parser.add_argument("article_path", help="概念文章路径")
    parser.add_argument("--concept-id", help="概念 ID")
    args = parser.parse_args()

    article_path = Path(args.article_path)
    if not article_path.exists():
        print(json.dumps({"error": f"文件不存在: {article_path}"}, ensure_ascii=False))
        sys.exit(1)

    concept_id = args.concept_id or article_path.stem

    # 1. 生成共享上下文
    shared = get_shared_context(article_path, concept_id)

    # 2. 运行自动化审查（白帽数据）
    white_hat_data = run_loop_review(article_path, concept_id)

    # 3. 组装输出 — 引用独立角色文件，不内嵌 prompt
    hats_dir = PROJECT_ROOT / "src" / "hats"
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "shared_context": shared,
        "white_hat_data": white_hat_data,
        "hat_files": {
            "white": str(hats_dir / "white_hat.md"),
            "red": str(hats_dir / "red_hat.md"),
            "black": str(hats_dir / "black_hat.md"),
            "yellow": str(hats_dir / "yellow_hat.md"),
            "green": str(hats_dir / "green_hat.md"),
            "blue": str(hats_dir / "blue_hat.md"),
            "review": str(hats_dir / "review_hat.md"),
        },
        "instructions": "每个 delegate_task 子 Agent 应先 read_file 读取对应的 hat 角色文件，再读取文章进行审查。角色文件中包含完整的 persona 定义、审查视角和输出格式。"
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
