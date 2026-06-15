# 🔄 喵哲学 · Loop Engineering 架构文档 v2.0

> **从接力留言到接力循环 → 再到六色喵脑爆** — 2026-06-15, feature/loop-engineering

## 架构进化

| 版本 | 审查方式 | 角色数 | 脑爆感 |
|:---|:---|:---:|:---:|
| v0 (接力留言) | 自己评自己 | 1 | 无 — 自言自语 |
| v1 (Loop Engineering) | 白喵 + 审查喵 | 2 | 弱 — 二元对立 |
| v2 (六色喵脑爆) | 白/红/黑/黄/绿/蓝/审查 | **7** | 强 — 真正脑爆 ✨ |

## 架构全景图

```
┌────────────────────────────────────────────────────────────────────┐
│                       喵哲学 Loop 体系 v2.0                          │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  🔄 写作环 (Writer Loop)                                    │    │
│  │  cron: 3x/日 7/12/21                                        │    │
│  │                                                              │    │
│  │  Step 0-3: 白喵写概念初稿                                    │    │
│  │  Step 4: hats_brainstorm.py → 共享上下文 + 白帽数据          │    │
│  │                                                              │    │
│  │  Step 5: 🎭 第一波脑爆 (并行 3 喵)                          │    │
│  │    ┌──────────┬──────────┬──────────┐                       │    │
│  │    │ ❤️红喵    │ 🖤黑喵    │ 💛黄喵    │                       │    │
│  │    │ 情感直觉   │ 逻辑批判   │ 价值发现   │                       │    │
│  │    └──────────┴──────────┴──────────┘                       │    │
│  │                                                              │    │
│  │  Step 6: 💚绿喵 创意突围                                     │    │
│  │  Step 7: 💙蓝喵 聚合调和                                     │    │
│  │  Step 8: 白喵整合修改                                        │    │
│  │  Step 9: 🔍审查喵 终审                                       │    │
│  │  Step 10-14: 存储 → 提交                                     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                         │                                           │
│          ┌──────────────┼──────────────┐                           │
│          ▼              ▼              ▼                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                      │
│  │ 💓喵魂核心 │  │ 🔍审查环   │  │ 🧠元环     │                      │
│  │ loop_state│  │ 每日06:00 │  │ (Phase 3) │                      │
│  │ 7喵审查   │  │ 趋势预警   │  │ 参数调整   │                      │
│  └───────────┘  └───────────┘  └───────────┘                      │
└────────────────────────────────────────────────────────────────────┘
```

## 七喵职责矩阵

| 喵 | 文件 | 问什么 | 输出到 | 并行? |
|:---|:---|:---|:---|:---:|
| 🤍 白帽 | `src/hats/white_hat.md` | 数据说什么？ | hats_brainstorm.py | 🔧 脚本 |
| ❤️ 红帽 | `src/hats/red_hat.md` | 心怎么跳？ | /tmp/hat_red.json | ✅ 并行 |
| 🖤 黑帽 | `src/hats/black_hat.md` | 哪里有坑？ | /tmp/hat_black.json | ✅ 并行 |
| 💛 黄帽 | `src/hats/yellow_hat.md` | 哪里发光？ | /tmp/hat_yellow.json | ✅ 并行 |
| 💚 绿帽 | `src/hats/green_hat.md` | 还有其他路吗？ | /tmp/hat_green.json | ➡️ 串行 |
| 💙 蓝帽 | `src/hats/blue_hat.md` | 怎么整合？ | /tmp/hat_blue.json | ➡️ 串行 |
| 🔍 审查 | `src/hats/review_hat.md` | 可以发了吗？ | /tmp/hat_review.json | ➡️ 终审 |

## 数据流

```
Step 0: heartbeat.py read
  └─ 读到: loop_state 累计指标 + next_improvements + intent_queue 预警

Step 1-3: 写概念初稿

Step 4: hats_brainstorm.py
  └─ 产出: brainstorm_context.json (共享上下文 + 白帽数据 + 角色文件路径)

Step 5-6: delegate_task 脑爆
  └─ 每个子Agent: read_file(角色文件) → read_file(文章) → write_file(审查JSON)

Step 7: 蓝喵读四喵JSON → 调和冲突 → 排序优先级

Step 8: 白喵读蓝喵报告 → 修改概念

Step 9: 审查喵终审 → READY_TO_PUBLISH?

Step 10: heartbeat.py loop-state review → 持久化到 state.json
  └─ loop_state.reviews[] ← 审查记录
  └─ loop_state.next_improvements ← 改进建议
  └─ loop_state.cumulative ← 累计指标更新
```

## 核心组件

### 角色文件 (`src/hats/*.md`)
七个独立 persona 文件，每个包含：身份设定、思维方式、审查视角、输出 JSON schema、口头禅、硬约束。

### 聚合器 (`src/hats_brainstorm.py`)
生成共享上下文 + 白帽数据 + 角色文件路径引用。不内嵌 prompt——角色定义在独立文件中。

### Cron Jobs
- **写作环** `a059c69ce4d5`: 3x/日，七喵脑爆流
- **审查环** `03ad7f0f10e6`: 每日 06:00，趋势预警
- **喵财奴** `ae9b4ae7c5ee`: 每小时敛财（无关）

## Phase 3 路线图

- [ ] Meta-Loop: 每周分析全体系健康，建议参数调整
- [ ] 蓝喵报告可视化仪表盘
- [ ] 族预算动态化
- [ ] novelty_check 阈值自适应

## 文件清单

| 文件 | 说明 |
|------|------|
| `src/hats/white_hat.md` | 白帽喵 · 数据分析师 |
| `src/hats/red_hat.md` | 红帽喵 · 情感雷达 |
| `src/hats/black_hat.md` | 黑帽喵 · 批判之刃 |
| `src/hats/yellow_hat.md` | 黄帽喵 · 价值探照灯 |
| `src/hats/green_hat.md` | 绿帽喵 · 创意催化剂 |
| `src/hats/blue_hat.md` | 蓝帽喵 · 脑爆指挥家 |
| `src/hats/review_hat.md` | 审查喵 · 最终闸门 |
| `src/hats_brainstorm.py` | 脑爆聚合器 |
| `src/loop_review.py` | 自动化审查脚本 |
| `heartbeat/heartbeat.py` | 喵魂核心 v1.1 |
| `SIX_HATS.md` | 六色喵设计文档 |
| `LOOP_ARCHITECTURE.md` | 本文档 |
