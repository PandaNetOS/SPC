# -*- coding: utf-8 -*-
"""tools/render_task_brief.py — 下轮任务书生成器（B+G 升级）。

从 memory/workbench/TODO.md 待办池按价值评分排序，生成候选 TOP3 与
下轮任务书草稿 —— 把「AI 恰好想到挑哪个」变成可机械复核的排序。

评分（B+G：TODO 条目加 value 字段，0-100；无 value 时按 P 级基础分）：
    base：P0=100 / P1=80 / P2=60 / P3=40 / P4=20
    value：显式 `value: N` 直接覆盖基础分（影响面/置信度缺口/可证伪性）
    ★ 首推标记（`★ rNN 首推`）：+10

用法：
    python tools/render_task_brief.py [--round NN] [--write]
        # 默认下一轮 = 当前最大轮 + 1；--write 写 games/dlt/iterations/roundNN/TASK_BRIEF.md
    python tools/render_task_brief.py --score   # 只打印评分榜

依据：DOLPHIN（idea 生成→反馈闭环）、主动学习（按不确定性/价值采样）。
"""
from __future__ import annotations

import io
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

_BASE_BY_PRIORITY = {"P0": 100, "P1": 80, "P2": 60, "P3": 40, "P4": 20}
_PRIORITY_RE = re.compile(r"^##\s*(P[0-4])")
_ITEM_RE = re.compile(r"^-\s*\[\s\]\s*\*\*(T-\d{3})\*\*\s*(.*?)(?:\s*★\s*(.*))?$")


def _parse_todo(root: str) -> list[dict]:
    p = os.path.join(root, "memory", "workbench", "TODO.md")
    if not os.path.exists(p):
        return []
    items: list[dict] = []
    priority = "P4"
    with open(p, encoding="utf-8") as f:
        for line in f:
            m = _PRIORITY_RE.match(line.strip())
            if m:
                priority = m.group(1)
                continue
            im = _ITEM_RE.match(line.strip())
            if not im:
                continue
            tid, title, star = im.groups()
            value_m = re.search(r"value[:：]\s*(\d{1,3})", line)
            base = _BASE_BY_PRIORITY.get(priority, 40)
            score = int(value_m.group(1)) if value_m else base
            if star and "首推" in star:
                score += 10
            items.append({
                "tid": tid, "title": title.strip(), "priority": priority,
                "star": (star or "").strip(), "score": score,
                "line": line.strip(),
            })
    items.sort(key=lambda it: (-it["score"], it["tid"]))
    return items


def _next_round(root: str) -> int:
    best = 0
    d = os.path.join(root, "games", "dlt", "iterations")
    if os.path.isdir(d):
        for name in os.listdir(d):
            m = re.match(r"^round(\d{2})$", name)
            if m:
                best = max(best, int(m.group(1)))
    return best + 1


def _render_brief(root: str, items: list[dict], rnd: int) -> str:
    top = items[:3]
    lines = [
        f"# TASK_BRIEF —— round{rnd:02d} 任务书",
        "",
        f"> **版本**：`1.0` ｜ 轮次 `r{rnd:02d}` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`",
        "> 本任务书由 `tools/render_task_brief.py` 从 TODO 待办池按价值评分生成",
        "> （派生物草稿，人工确认后可改）。评分依据：TODO 条目 value / P 级 / ★首推。",
        "",
        "## 本轮候选（按评分排序 TOP3）",
        "",
        "| 排序 | 任务 | 优先级 | 评分 | 说明 |",
        "|---|---|---|---|---|",
    ]
    for i, it in enumerate(top, 1):
        lines.append(f"| {i} | {it['tid']} {it['title']} | {it['priority']} | {it['score']} | {it['star']} |")
    lines += [
        "",
        "## 本轮 P0 任务（必做，引用 TODO 原条目）",
        "",
        f"- [ ] **{top[0]['tid']}** —— 来源：`memory/workbench/TODO.md` 的 "
        f"`{top[0]['priority']}` 段（评分 {top[0]['score']}）。",
        "",
        "## 验收判据",
        "",
        "1. 完成任务后更新 FACTS.jsonl（新结论必须过三闸门，带 caveats）；",
        "2. `python cli/main.py validate --all` 全绿；",
        "3. 收轮四件套 + 版本登记 + 下轮任务书。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    rnd = _next_round(_ROOT)
    if "--round" in sys.argv:
        i = sys.argv.index("--round")
        rnd = int(sys.argv[i + 1])
    items = _parse_todo(_ROOT)
    if not items:
        print("TODO.md 无待办条目（或未按 T-nnn 格式），无法生成任务书。")
        return 1

    if "--score" in sys.argv:
        print("TODO 待办评分榜：")
        for it in items:
            print(f"  {it['tid']} [{it['priority']}] 评分 {it['score']:>3}  {it['title']}")
        return 0

    brief = _render_brief(_ROOT, items, rnd)
    out = os.path.join(_ROOT, "games", "dlt", "iterations", f"round{rnd:02d}", "TASK_BRIEF.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if "--write" in sys.argv:
        open(out, "w", encoding="utf-8").write(brief)
        print(f"✓ 已写 {os.path.relpath(out, _ROOT)}（候选 {len(items[:3])} 条）")
        return 0
    print(brief)
    print(f"（dry-run，未写；加 --write 写入 round{rnd:02d}/TASK_BRIEF.md）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
