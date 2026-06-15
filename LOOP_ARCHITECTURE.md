# 🔄 喵哲学 · Loop Engineering 架构文档

> **从接力留言到接力循环** — 2026-06-15, feature/loop-engineering

## 概述

喵哲学概念生成系统从「接力留言」（线性传递）升级为「接力循环」（闭环反馈），借鉴 Loop Engineering 的核心理念：

- **写评分离**：写作和审查由不同 Agent 执行
- **环间反馈**：审查结果持久化，影响下一轮写作行为
- **Loop 监督 Loop**：独立质量审查环持续观察写作环

## 架构全景图

```
┌──────────────────────────────────────────────────────────────────┐
│                        喵哲学 Loop 体系                           │
│                                                                   │
│  ┌─────────────────────────┐     ┌──────────────────────────┐    │
│  │  🔄 写作环 (Writer Loop) │     │  🔍 审查环 (Review Loop)  │    │
│  │  cron: 3x/日 7/12/21    │     │  cron: 每日 06:00        │    │
│  │                         │     │                          │    │
│  │  Step 0: heartbeat read │     │  Step 1: read loop_state │    │
│  │    ← 读到审查建议 ✨     │     │  Step 2: scan new概念    │    │
│  │  Step 1-3: 写概念       │     │  Step 3: loop_review.py  │    │
│  │  Step 4: delegate_task  │     │  Step 4: trend analysis  │    │
│  │    → 🔍 审查喵评骨架层  │     │  Step 5: push-intent ⚠️  │    │
│  │  Step 5: loop-state     │     │  Step 6: loop-state      │    │
│  │    review store ←──┐    │     │    review store ────────┘    │
│  │  Step 6-8: 收尾     │    │     │                          │
│  │                     │    │     │                          │
│  └─────────────────────┘    │     └──────────────────────────┘    │
│           │                 │               │                     │
│           └─────────┬───────┘───────────────┘                     │
│                     ▼                                              │
│         ┌──────────────────────┐                                  │
│         │   💓 喵魂核心          │                                  │
│         │   state.json          │                                  │
│         │   ├── loop_state      │  ← 审查结果 + 改进建议 + 指标    │
│         │   ├── intent_queue    │  ← 质量预警                     │
│         │   └── heartbeat_log   │  ← 接力留言                     │
│         └──────────────────────┘                                  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  🧠 Meta-Loop (元环) — 未来 Phase 3                        │    │
│  │  cron: 每周日 06:00                                        │    │
│  │  分析全体系健康 → 建议参数调整 → 主人审批                   │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. heartbeat.py — 喵魂核心

路径：`~/.hermes/meow-soul/heartbeat.py`（运行时）→ `heartbeat/heartbeat.py`（源码）

新增 `loop-state` 子命令：

```bash
# 初始化 loop_state 字段（幂等）
heartbeat.py loop-state init

# 存储审查结果（自动更新累计指标 + 改进建议）
heartbeat.py loop-state review '<json>'

# 读取 loop_state 摘要
heartbeat.py loop-state read

# 手动管理累计指标
heartbeat.py loop-state metrics [get|set <field> <value>]
```

`cmd_read()` 现在自动显示 loop_state 摘要，包括：
- 累计审查篇数、平均喵味骨架分、连续 descriptive 数
- 上次审查结果（判定 + 分数）
- **审查喵改进建议**（写作环 Step 0 自动看到）

### 2. loop_review.py — 自动化审查器

路径：`src/loop_review.py`

可量化的自动化检查（被审查子 Agent 调用）：

| 检查项 | 方法 | 输出 |
|--------|------|------|
| 喵味表面层 5 项 | 正则匹配 | meow_surface (0-5) |
| 新度验证 | 调用 novelty_check.py | similarity score |
| 目的对齐 | 提取文章中的 purpose_alignment | alignment type |
| 族污染 | novelty_check 的 graph_family_check | contamination map |
| descriptive streak | purpose_drift_check | streak count |

定性检查（喵味骨架层 5 项）留给审查子 Agent 的 LLM 判断。

输出：结构化 JSON → 直接喂给 `heartbeat.py loop-state review`。

### 3. Cron Jobs

#### 写作环 (a059c69ce4d5) — 喵哲学 · 每日三省

- 调度: `21 7,12,21 * * *` (每日 3 次)
- Toolsets: web, terminal, file, session_search, cronjob, **delegation**, skills
- Skills: meow-philosophy
- 新增: Step 4 delegate_task 审查块 → 写评分离

#### 审查环 (03ad7f0f10e6) — 喵哲学 · 每日质量审查环 🔍

- 调度: `0 6 * * *` (每日 06:00，写作环 07:21 之前)
- Persona: 萤 (ying profile)
- 职责: 观察、评分、预警、推送 intent → 不写概念
- 输出: intent_queue HIGH priority 预警 + loop_state 审查记录

## 数据流

```
写作环 (07:21)
  │
  ├─ Step 0: heartbeat.py read
  │   └─ 读到: loop_state.next_improvements
  │      "💡 织体类比可以更浅出"
  │      "💡 emotional_arc 评分3/5需注意"
  │
  ├─ Step 1-3: 写概念（受改进建议影响）
  │
  ├─ Step 4: delegate_task → 审查喵评骨架层
  │   └─ 审查喵: 读文章 + loop_review.py 结果 → 产出骨架分 + improvements
  │
  ├─ Step 5: heartbeat.py loop-state review '<json>'
  │   └─ 存储: next_improvements 更新 + cumulative 累加
  │
  └─ Step 6-8: 收尾

审查环 (06:00, 次日)
  │
  ├─ 读 loop_state
  ├─ 扫描新概念
  ├─ 趋势分析（喵味↓？新度收敛？ds streak?）
  ├─ push-intent HIGH "喵味退化预警"
  └─ loop-state review 存储
```

## 从接力留言到接力循环

| 维度 | 接力留言（旧） | 接力循环（新） |
|------|:---:|:---:|
| 写评关系 | 同一个 Agent 写+评 | 写作猫 ≠ 审查喵 |
| 反馈方向 | 单向（留言往前传） | 闭环（审查回传给下一轮） |
| 质量追踪 | 无（不知道上次写得怎么样） | 累计指标 + 趋势分析 |
| 自适应 | 无（参数固定） | 审查建议自动注入下一次咚 |
| 监督 | 无外部观察者 | 独立审查环持续监控 |
| 持久化 | 接力留言是叙事文本 | 结构化 loop_state JSON |

## 文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| heartbeat.py | `heartbeat/heartbeat.py` | 喵魂核心 v1.1 — 新增 loop-state 子命令 |
| loop_review.py | `src/loop_review.py` | 自动化审查器 v1.0 |
| CRON.md | `LOOP_ARCHITECTURE.md` | 本文档 |
| Cron job 写作环 | `a059c69ce4d5` | 更新：插入 delegate_task 审查块 |
| Cron job 审查环 | `03ad7f0f10e6` | 新建：每日质量审查环 |

## Phase 3 路线图

- [ ] Meta-Loop: 每周分析全体系健康，建议参数调整
- [ ] 审查喵用独立 profile（萤）实现真正的模型级写评分离
- [ ] loop_state 中的喵味趋势可视化
- [ ] novelty_check 阈值自适应（太容易 PASS → 收紧）
- [ ] 族预算动态化（基于概念密度而非硬编码 3）
