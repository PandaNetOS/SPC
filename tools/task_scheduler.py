# -*- coding: utf-8 -*-
"""task_scheduler.py — 研究任务调度器（平台侧任务池视图）

管理研究组待办池：列出 / 取下一个 / 追加 / 勾选。

**与 tools/render_task_brief.py 的分工**：
    · render_task_brief —— 按 value / P 级 / ★ 首推**评分排序**，生成下轮任务书
    · 本工具 —— 简单 CRUD 视图（list / next / add / done），供人快速查看

TODO 条目格式（以仓库现行格式为准，见 workbench/TODO.md）：
    - [ ] **T-064** value: 30 ★ r16 派生：H-002 三段单调检验 ✅ **r16 完成** → F-0048
    - [x] **T-063** value: 30 P4 ...

用法：
    python tools/task_scheduler.py list          # 列出未完成任务
    python tools/task_scheduler.py next          # 取编号最小的未完成任务
    python tools/task_scheduler.py add <标题>    # 追加新任务
    python tools/task_scheduler.py done <T-nnn>  # 勾选为已完成
"""
from __future__ import annotations

import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, os.path.join(_ROOT, "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from spc import paths  # noqa: E402 路径单一权威

# 仓库现行条目格式：- [ ] **T-064** value: 30 ... （id 是 **T-nnn**，不是 T-nnn:）
_ITEM_RE = re.compile(r"^-\s*\[([ xX])\]\s*\*\*(T-\d{3})\*\*(.*)$")


def _todo_path(root: str = ".") -> str:
    return os.path.join(paths.workbench_dir("dlt", root=root), "TODO.md")


def list_tasks(root: str = ".") -> list[dict]:
    """读 TODO.md，解析为任务列表（兼容仓库现行的 **T-nnn** 格式）。"""
    path = _todo_path(root)
    if not os.path.exists(path):
        return []

    tasks: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            m = _ITEM_RE.match(line.strip())
            if not m:
                continue
            mark, tid, rest = m.groups()
            title = rest.strip()
            # 去掉 value / P 级 / ★ 首推等评分前缀，只留可读标题
            title = re.sub(r"^(value:\s*\d+\s*)", "", title).strip()
            title = re.sub(r"^(★\s*)?(r\d{2}\s*)?", "", title).strip()
            tasks.append({
                "id": tid,
                "title": title,
                "status": "done" if mark.strip().lower() == "x" else "open",
                "line": lineno,
            })
    return tasks


def next_task(root: str = ".") -> dict | None:
    """编号最小的未完成任务。"""
    open_tasks = [t for t in list_tasks(root) if t["status"] == "open"]
    if not open_tasks:
        return None
    open_tasks.sort(key=lambda t: t["id"])
    return open_tasks[0]


def add_task(title: str, root: str = ".") -> str:
    """追加新任务到 TODO.md（沿用仓库现行条目格式）。"""
    path = _todo_path(root)
    tasks = list_tasks(root)
    ids = [int(t["id"].split("-")[1]) for t in tasks if t["id"].startswith("T-")]
    next_num = (max(ids) if ids else 0) + 1
    task_id = f"T-{next_num:03d}"

    with open(path, "a", encoding="utf-8") as f:
        f.write(f"- [ ] **{task_id}** {title}\n")

    return task_id


def done_task(task_id: str, root: str = ".") -> bool:
    """把指定任务勾选为已完成。找不到返回 False。"""
    path = _todo_path(root)
    if not os.path.exists(path):
        return False
    tid = task_id.upper()
    lines = open(path, encoding="utf-8").read().splitlines()
    out, hit = [], False
    for ln in lines:
        m = _ITEM_RE.match(ln.strip())
        if m and m.group(2).upper() == tid and m.group(1).strip() != "x":
            ln = ln.replace("[ ]", "[x]", 1)
            hit = True
        out.append(ln)
    if hit:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + ("\n" if lines and lines[-1] else ""))
    return hit


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：")
        print("  python tools/task_scheduler.py list          # 列出未完成任务")
        print("  python tools/task_scheduler.py next          # 取编号最小的未完成任务")
        print("  python tools/task_scheduler.py add <标题>    # 追加新任务")
        print("  python tools/task_scheduler.py done <T-nnn>  # 勾选为已完成")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        tasks = list_tasks()
        open_tasks = [t for t in tasks if t["status"] == "open"]
        print(f"未完成任务（{len(open_tasks)} 个 / 共 {len(tasks)} 个）：")
        for t in open_tasks:
            print(f"  {t['id']}: {t['title'][:80]}")
    elif cmd == "next":
        t = next_task()
        if t:
            print(f"下一个任务：{t['id']}: {t['title'][:80]}")
        else:
            print("没有未完成任务")
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("请提供任务标题")
            sys.exit(1)
        tid = add_task(" ".join(sys.argv[2:]))
        print(f"已添加：{tid}")
    elif cmd == "done":
        if len(sys.argv) < 3:
            print("请提供任务 id（如 T-064）")
            sys.exit(1)
        ok = done_task(sys.argv[2])
        print(f"已勾选：{sys.argv[2].upper()}" if ok else f"未找到：{sys.argv[2].upper()}")
        sys.exit(0 if ok else 1)
    else:
        print(f"未知命令：{cmd}")
        sys.exit(1)
