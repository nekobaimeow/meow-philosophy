# 喵哲学知识工程修补计划 v4.1

> 诊断依据：Concept 22 偏离"开干"方向 → 根因为族封顶+门控失效+动态预算缺失

## 任务清单

### T1 🔴 purpose_drift 硬约束（novelty_check.py）

**问题**：`--purpose-alignment` 可选参数，缺则只报告不 REJECT
**修复**：
- 改成必传参数（`required=True`）
- 首次运行不带参数时给出友好错误
- 新增 `--skip-purpose` 逃生舱（紧急绕过用）
- Cron prompt 中注入 `--purpose-alignment {alignment}`

### T2 🔴 graph.yaml 注册新族：间隙层

**问题**：concept-graph.md 有"间隙层"聚类（10/12/14），但 graph.yaml 未注册
**修复**：
- knowledge-graph/data/graph.yaml 新增 `gap-existence` 族
- 将 concept-10/12/14 写入 family members
- concept-graph.md 更新标记
- `make validate` 校验通过

### T3 🔴 落地 Concept 21 MVP：喵魂核心

**问题**：Concept 21 画了蓝图但代码一行没写
**修复**：
- 创建 `~/.hermes/meow-soul/state.json` 初始心跳文件
- 写 `tools/heartbeat.py` 脚本（读/写 state.json）
- 修改 cron job `a059c69ce4d5` prompt，开头注入心跳快照块
- Cron 末尾追加心跳更新钩子

### T4 🟡 族预算动态化方案

**问题**：硬编码 3/族 无理论依据
**方向**：公式驱动的动态预算（不立刻实现，先写方案）
- 方案输出到 `knowledge-graph/docs/dynamic-budget-proposal.md`
- 核心公式：`budget = base(2) + purpose_weight + output_bonus - saturation_penalty`

## 执行顺序

1. `git add -A && git commit` 备份当前状态
2. T1 → T2 → T3 → T4 顺序执行
3. 每步完成后校验
4. 最终 `git commit` 保存所有改动
