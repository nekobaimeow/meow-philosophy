# 喵哲学知识工程 Makefile
# 用法：make [target]
# 由 LinkML 驱动，白喵、主人、萤三方协作

SCHEMA := schema/meow_philosophy.yaml
DATA   := data/graph.yaml
GEN_DIR := generated

.PHONY: all validate generate test clean

# 默认：验证 + 生成
all: validate generate

# ── 验证 ──────────────────────────────
validate:
	@echo "🔍 验证 schema..."
	linkml-lint $(SCHEMA)
	@echo "🔍 验证数据..."
	linkml-validate -s $(SCHEMA) $(DATA)
	@echo "✅ 全部通过"

# ── 代码生成 ──────────────────────────
generate: generate-python generate-json-schema generate-er

generate-python:
	@echo "🐍 生成 Python dataclasses..."
	@mkdir -p $(GEN_DIR)/python
	linkml generate python $(SCHEMA) > $(GEN_DIR)/python/meow_model.py
	@echo "   ✅ $(GEN_DIR)/python/meow_model.py"

generate-json-schema:
	@echo "📋 生成 JSON Schema..."
	linkml generate json-schema $(SCHEMA) -t KnowledgeGraph > $(GEN_DIR)/meow_philosophy.schema.json
	@echo "   ✅ $(GEN_DIR)/meow_philosophy.schema.json"

generate-er:
	@echo "📊 生成 ER 图..."
	linkml generate erdiagram $(SCHEMA) > $(GEN_DIR)/er_diagram.md
	@echo "   ✅ $(GEN_DIR)/er_diagram.md"

# ── 图分析（萤的领域）────────────────
query-stats:
	@python3 -c "\
import sys; sys.path.insert(0, '$(GEN_DIR)/python'); \
from meow_model import KnowledgeGraph; \
from linkml_runtime.loaders import yaml_loader; \
kg = yaml_loader.load('$(DATA)', KnowledgeGraph); \
print(f'概念: {len(kg.concepts)} | 族: {len(kg.families)} | 穷尽族: {len(kg.exhausted_families)}'); \
edges = sum(len(c.relations_out) for c in kg.concepts if c.relations_out); \
print(f'关系边: {edges}'); \
for f in kg.families: \
    print(f'  [{f.label}] {\", \".join(f.members or [])} ({len(f.members or [])}个)')"

query-centrality:
	@python3 queries/centrality.py

# ── 清理 ──────────────────────────────
clean:
	rm -rf $(GEN_DIR)/*
	@echo "🧹 已清理生成文件"
