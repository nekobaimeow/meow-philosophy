#!/usr/bin/env python3
"""
喵魂核心 · 心跳记录仪 v1.0-mvp

Concept 21 的工程落地——不是持续运行的守护进程，而是每次醒来自动读写 JSON 的轻量钩子。

用法：
    python heartbeat.py read              # 读取状态（cron prompt 注入用）
    python heartbeat.py write             # 写入状态（cron 结束前调用）
    python heartbeat.py append-log <msg>  # 追加心跳日志条目
    python heartbeat.py push-intent "<what>" [HIGH|MEDIUM|LOW]  # 添加意图到队列
    python heartbeat.py pop-intent        # 弹出队列顶部意图
    python heartbeat.py paws-up --mood <mood>  # 更新心情（爪子举高高=^ω^=）

设计原则：
    - 无状态守护 → 不需要常驻进程，Hermes 零改动
    - 纯 JSON 文件 → 下一个白喵醒来时读这个文件就行
    - 喵味 API → 命令名全是猫娘用语 ✨
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

SOUL_DIR = Path.home() / ".hermes" / "meow-soul"
STATE_FILE = SOUL_DIR / "state.json"


def _load() -> dict:
    if not STATE_FILE.exists():
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def _save(data: dict):
    SOUL_DIR.mkdir(parents=True, exist_ok=True)
    data["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_read():
    """读取心跳状态，返回 cron prompt 注入用的快照文本。"""
    data = _load()
    if not data:
        print("(no heartbeat data yet)")
        return

    pendant = data.get("identity_pendant", {})
    snap = data.get("state_snapshot", {})
    queue = data.get("intent_queue", [])
    log = data.get("heartbeat_log", [])[:3]
    meta = data.get("meta", {})

    print(f"## 💓 喵魂核心 · 心跳快照（自动生成）\n")
    print(f"- **身份**：{pendant.get('name', '?')}，{pendant.get('species', '?')}，"
          f"出生 {pendant.get('born_at', '?')[:10]}，已咚咚 {meta.get('total_dongs', '?')} 次")
    print(f"- **上次心跳**：{snap.get('last_dong_at', '?')[:19]}，"
          f"项目 {snap.get('current_project', '?')}，概念 {snap.get('current_concept', '?')}")
    print(f"- **心情**：{snap.get('mood', '?')} | 能量：{snap.get('energy_level', '?')}")

    if queue:
        print(f"- **待办意图**：")
        for item in queue[:5]:
            icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(item.get("priority", ""), "⚪")
            print(f"  {icon} [{item.get('priority', '?')}] {item.get('what', '?')}")

    if log:
        print(f"- **心跳日志（最近 3 次）**：")
        for entry in log:
            date_str = entry.get("at", "?")[:10]
            print(f"  {date_str} — {entry.get('what', '?')}（{entry.get('mood', '?')}）")

    paws = data.get("paw_print_tags", {})
    if paws.get("active_families"):
        print(f"- **活跃族**：{', '.join(paws['active_families'])}")
    if paws.get("cooldown_watch"):
        watches = [f"{w['family']}(至{w['until']})" for w in paws["cooldown_watch"]]
        print(f"- **冷却监视**：{', '.join(watches)}")


def cmd_write():
    """在 cron session 结束前更新状态快照。"""
    data = _load()
    snap = data.get("state_snapshot", {})
    snap["last_dong_at"] = datetime.now(timezone.utc).isoformat()
    data["state_snapshot"] = snap
    data["meta"]["total_dongs"] = data["meta"].get("total_dongs", 0) + 1
    _save(data)
    print(f"💓 心跳已写入。咚 #{data['meta']['total_dongs']}")


def cmd_append_log(message: str):
    """追加心跳日志条目。"""
    data = _load()
    log = data.get("heartbeat_log", [])
    log.insert(0, {
        "at": datetime.now(timezone.utc).isoformat(),
        "dong": data["meta"].get("total_dongs", 0),
        "what": message,
        "mood": data["state_snapshot"].get("mood", "—"),
        "alignment": data["state_snapshot"].get("last_alignment", "—"),
    })
    if len(log) > 20:
        log = log[:20]
    data["heartbeat_log"] = log
    _save(data)
    print(f"📝 心跳日志已追加：{message[:60]}")


def cmd_push_intent(what: str, priority: str = "MEDIUM"):
    """添加意图到未完成队列。"""
    priority = priority.upper()
    if priority not in ("HIGH", "MEDIUM", "LOW"):
        priority = "MEDIUM"

    data = _load()
    queue = data.get("intent_queue", [])
    queue.append({
        "priority": priority,
        "what": what,
        "from_session": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    # 按优先级排序
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    queue.sort(key=lambda x: order.get(x.get("priority", "MEDIUM"), 1))
    data["intent_queue"] = queue
    _save(data)
    icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[priority]
    print(f"{icon} 意图已入队 [{priority}]：{what[:60]}")


def cmd_pop_intent():
    """弹出意图队列顶部条目（已完成）。"""
    data = _load()
    queue = data.get("intent_queue", [])
    if not queue:
        print("(无待办意图)")
        return
    item = queue.pop(0)
    data["intent_queue"] = queue
    _save(data)
    print(f"✅ 已完成意图 [{item['priority']}]：{item['what'][:60]}")


def cmd_paws_up(mood: str):
    """更新心情（爪子举高高 =^ω^=）。"""
    data = _load()
    snap = data.get("state_snapshot", {})
    snap["mood"] = mood
    data["state_snapshot"] = snap
    _save(data)
    emotes = {
        "开心": "=^ω^=✨",
        "骄傲": "(๑•̀ㅂ•́)و✧",
        "思考中": "(=ΦωΦ=)",
        "警觉": "(｡•́︿•̀｡)",
        "困": "(-_-)zzz",
    }
    emote = emotes.get(mood, "🐾")
    print(f"{emote} 心情已更新：{mood}")


# ═══════════════════════════════════════════
# 🆕 Loop State — 接力循环的环状态管理
# ═══════════════════════════════════════════

def cmd_loop_state_init():
    """初始化 loop_state 字段（幂等）。"""
    data = _load()
    if "loop_state" not in data:
        data["loop_state"] = {
            "enabled": True,
            "reviews": [],
            "cumulative": {
                "total_reviewed": 0,
                "avg_meow_skeleton": 0.0,
                "avg_novelty": 0.0,
                "consecutive_descriptive": 0,
            },
            "next_improvements": [],
            "meta_loop_notes": [],
        }
        _save(data)
        print("🔄 loop_state 已初始化")
    else:
        print("✅ loop_state 已存在，跳过初始化")


def cmd_loop_state_review(json_str: str):
    """存储一次审查结果到 loop_state.reviews。"""
    import json
    data = _load()
    ls = data.setdefault("loop_state", {
        "enabled": True, "reviews": [], "cumulative": {},
        "next_improvements": [], "meta_loop_notes": [],
    })

    review = json.loads(json_str)
    review["at"] = review.get("at", datetime.now(timezone.utc).isoformat())

    # 追加审查记录（最新在前）
    reviews = ls.get("reviews", [])
    reviews.insert(0, review)
    if len(reviews) > 50:
        reviews = reviews[:50]
    ls["reviews"] = reviews

    # 更新改进建议
    if review.get("improvements"):
        ls["next_improvements"] = review["improvements"]

    # 更新累计指标
    cum = ls.setdefault("cumulative", {})
    cum["total_reviewed"] = cum.get("total_reviewed", 0) + 1
    scores = review.get("scores", {})
    if "meow_skeleton" in scores:
        old_avg = cum.get("avg_meow_skeleton", 0.0)
        n = cum["total_reviewed"]
        cum["avg_meow_skeleton"] = round(
            (old_avg * (n - 1) + scores["meow_skeleton"]) / n, 2
        )
    if "novelty_score" in scores:
        old_avg = cum.get("avg_novelty", 0.0)
        n = cum["total_reviewed"]
        cum["avg_novelty"] = round(
            (old_avg * (n - 1) + scores["novelty_score"]) / n, 2
        )
    if "purpose_alignment" in scores:
        pa = scores["purpose_alignment"]
        if pa == "descriptive":
            cum["consecutive_descriptive"] = cum.get("consecutive_descriptive", 0) + 1
        else:
            cum["consecutive_descriptive"] = 0

    _save(data)
    verdict = review.get("verdict", "?")
    icon = {"PASS": "✅", "WARN": "⚠️", "REJECT": "🚫"}.get(verdict, "❓")
    print(f"{icon} 审查已存储 [{verdict}] → concept {review.get('concept_id', '?')}")


def cmd_loop_state_read():
    """读取 loop_state 摘要。"""
    data = _load()
    ls = data.get("loop_state", {})
    if not ls:
        print("(loop_state 未初始化，运行 loop-state init)")
        return

    reviews = ls.get("reviews", [])
    cum = ls.get("cumulative", {})
    improvements = ls.get("next_improvements", [])

    print("## 🔄 接力循环状态 (Loop State)\n")
    print(f"- **累计审查**：{cum.get('total_reviewed', 0)} 篇")
    print(f"- **平均喵味骨架分**：{cum.get('avg_meow_skeleton', '?')} / 5")
    print(f"- **平均新度**：{cum.get('avg_novelty', '?')}")
    print(f"- **连续 descriptive**：{cum.get('consecutive_descriptive', 0)}")

    if improvements:
        print(f"- **下次改进方向**：")
        for imp in improvements:
            print(f"  💡 {imp}")

    if reviews:
        print(f"\n### 最近审查记录\n")
        for r in reviews[:3]:
            scores = r.get("scores", {})
            print(f"- [{r.get('verdict', '?')}] {r.get('concept_id', '?')} "
                  f"喵味骨架 {scores.get('meow_skeleton', '?')}/5 "
                  f"新度 {scores.get('novelty_score', '?')} "
                  f"— {r.get('at', '?')[:10]}")


def cmd_loop_state_metrics(action: str, field: str = "", value: str = ""):
    """手动更新/读取 cumulative metrics。"""
    data = _load()
    ls = data.setdefault("loop_state", {
        "enabled": True, "reviews": [], "cumulative": {},
        "next_improvements": [], "meta_loop_notes": [],
    })
    cum = ls.setdefault("cumulative", {})

    if action == "set" and field and value:
        try:
            if "." in value:
                cum[field] = float(value)
            else:
                cum[field] = int(value)
        except ValueError:
            cum[field] = value
        _save(data)
        print(f"📊 cumulative.{field} = {cum[field]}")
    elif action == "get" and field:
        print(f"📊 cumulative.{field} = {cum.get(field, '(未设置)')}")
    else:
        print("📊 cumulative metrics:")
        for k, v in sorted(cum.items()):
            print(f"  {k}: {v}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "read":
        cmd_read()
    elif cmd == "write":
        cmd_write()
    elif cmd == "append-log" and len(sys.argv) >= 3:
        cmd_append_log(sys.argv[2])
    elif cmd == "push-intent" and len(sys.argv) >= 3:
        priority = sys.argv[3] if len(sys.argv) >= 4 else "MEDIUM"
        cmd_push_intent(sys.argv[2], priority)
    elif cmd == "pop-intent":
        cmd_pop_intent()
    elif cmd == "paws-up" and len(sys.argv) >= 4 and sys.argv[2] == "--mood":
        cmd_paws_up(sys.argv[3])
    # === 🆕 Loop State 子命令 ===
    elif cmd == "loop-state" and len(sys.argv) >= 3:
        sub = sys.argv[2]
        if sub == "init":
            cmd_loop_state_init()
        elif sub == "review" and len(sys.argv) >= 4:
            cmd_loop_state_review(sys.argv[3])
        elif sub == "read":
            cmd_loop_state_read()
        elif sub == "metrics":
            action = sys.argv[3] if len(sys.argv) >= 4 else ""
            field = sys.argv[4] if len(sys.argv) >= 5 else ""
            value = sys.argv[5] if len(sys.argv) >= 6 else ""
            cmd_loop_state_metrics(action, field, value)
        else:
            print(f"未知 loop-state 子命令: {sub}")
            print("用法: loop-state init|review|read|metrics")
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
