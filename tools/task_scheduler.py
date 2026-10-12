# -*- coding: utf-8 -*-
"""task_scheduler.py — 研究任务调度器

管理 TODO 池：优先级排序、依赖关系、自动分配下一轮任务。

用法：
    python tools/task_scheduler.py list          # 列出所有待办
    python tools/task_scheduler.py next          # 获取下一个最高优先级任务
    python tools/task_scheduler.py add <title>   # 添加任务
    python tools/task_scheduler.py done <id>    # 标记完成
"""

import os
import sys
import json
from datetime import date


def _todo_path(root: str = ".") -> str:
    return os.path.join(root, "memory", "workbench", "TODO.md")


def list_tasks(root: str = ".") -> list:
    """读取 TODO.md，解析为任务列表。"""
    path = _todo_path(root)
    if not os.path.exists(path):
        return []

    tasks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- [ ] T-"):
                # 格式：- [ ] T-064: 标题
                parts = line[6:].split(":", 1)
                if len(parts) == 2:
                    tasks.append({
                        "id": parts[0].strip(),
                        "title": parts[1].strip(),
                        "status": "open",
                    })
            elif line.startswith("- [x] T-"):
                parts = line[6:].split(":", 1)
                if len(parts) == 2:
                    tasks.append({
                        "id": parts[0].strip(),
                        "title": parts[1].strip(),
                        "status": "done",
                    })
    return tasks


def next_task(root: str = ".") -> dict | None:
    """获取下一个最高优先级任务（按 ID 排序，小的先做）。"""
    tasks = list_tasks(root)
    open_tasks = [t for t in tasks if t["status"] == "open"]
    if not open_tasks:
        return None
    open_tasks.sort(key=lambda t: t["id"])
    return open_tasks[0]


def add_task(title: str, root: str = ".") -> str:
    """添加新任务到 TODO.md。"""
    path = _todo_path(root)
    tasks = list_tasks(root)
    done_ids = [int(t["id"].split("-")[1]) for t in tasks if t["id"].startswith("T-")]
    next_num = max(done_ids) + 1 if done_ids else 1
    task_id = f"T-{next_num:03d}"

    with open(path, "a", encoding="utf-8") as f:
        f.write(f"- [ ] {task_id}: {title}\n")

    return task_id


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：")
        print("  python tools/task_scheduler.py list          # 列出所有待办")
        print("  python tools/task_scheduler.py next          # 获取下一个任务")
        print("  python tools/task_scheduler.py add <title>   # 添加任务")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        tasks = list_tasks()
        open_tasks = [t for t in tasks if t["status"] == "open"]
        print(f"待办任务（{len(open_tasks)} 个）：")
        for t in open_tasks:
            print(f"  {t['id']}: {t['title']}")
    elif cmd == "next":
        t = next_task()
        if t:
            print(f"下一个任务：{t['id']}: {t['title']}")
        else:
            print("没有待办任务")
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("请提供任务标题")
            sys.exit(1)
        tid = add_task(" ".join(sys.argv[2:]))
        print(f"已添加：{tid}")
    else:
        print(f"未知命令：{cmd}")
