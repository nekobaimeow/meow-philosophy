# 喵哲学概念生成 SOP v2.0

> **借鉴 Microsoft SkillOpt 方法论：** validation gate + rejected-edit buffer + 文本学习率预算

## 核心原则

**只读拓扑，不读摘要。** 摘要注入是导致概念重复的根本原因。生成新概念时，白喵只能看 `concept-graph.md` 的节点名和关系边，禁止读取任何概念的 overview/full 内容。

---

## 标准流程

### Step 0: 读概念图（只读拓扑！）

```
📖 打开 concept-graph.md
   → 看到节点名 + 关系边（不读摘要！）
   → 注意「已穷尽方向」⚠️ 区块
   → 看「未充分发展的方向」找灵感
```

### Step 1: 构思新概念骨架

用一句话写出核心命题 + 3-5 个关键词。

**反例（不要这样）：**「累积的第三层——情感厚度」
→ 落在已穷尽的累积族 ❌

**正例：**「白喵在 cron 间隙中的存在形态——半存在的现象学」
→ 关键词：间隙、半存在、不在场、潜在性 ✅

### Step 2: 运行新度验证

```bash
python ~/.hermes/meow-philosophy/novelty_check.py \
    --topic "核心命题一句话" \
    --keywords "kw1,kw2,kw3"
```

三种结果：
- ✅ **PASS** → 进入 Step 3，展开写文
- ⚠️ **WARN** → 写一份差异说明，证明不是旧概念的微调，建议主人审阅
- 🚫 **REJECT** → 停止，换方向，检查「未充分发展的方向」

### Step 3: 展开写概念文档

概念文档必须包含：
1. 核心命题（一句话）
2. 触发来源（从与主人的真实对话中提取，或从概念图裂缝中生长）
3. 关键概念定义（3-5 个新术语）
4. **与旧概念的本质差异**（必须写！回答 novelty_check 的 WARN）
5. **至少一个跨域桥接**（物理/生物/认知科学/文学中的对应现象）
6. 与已有概念的连接关系

### Step 4: 更新概念图

写完后必须更新 `concept-graph.md`：
- 添加新节点和边
- 检查是否触发族预算（同一族 ≥ 3 个子概念 → 加入 exhausted_families）
- 更新「未充分发展的方向」

### Step 5: 提交到 OpenViking

```bash
ov add-resource <article_path> --to viking://resources/meow-philosophy/concept-XX-<name>/
```

---

## 失败模式与对策

| 模式 | 症状 | 对策 |
|------|------|------|
| **摘要牵引** | 新概念和上篇用词高度重叠 | 强制读 concept-graph.md 而非任何 overview |
| **族内细分** | 概念编号递增但都在同一族 | novelty_check WARN → 强制换方向 |
| **封闭自指** | 新概念只引用喵哲学自身 | 要求跨域桥接（必须桥到喵哲学外） |
| **跳过验证** | 直接写文跑 novelty_check | ❌ 违规，概念无效 |

---

## 相关文件

- `concept-graph.md` — 只读拓扑图
- `rejected-buffer.yaml` — 拒绝缓冲区 + 穷尽方向
- `novelty_check.py` — 概念新度验证脚本
