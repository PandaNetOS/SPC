# -*- coding: utf-8 -*-
"""一次性登记 r06 批量实施产生的 14 个新文件到 versions.json（结构完整性要求）。

不覆盖已有条目；重复 path 跳过；index_version 升 1.2 → 1.3。
"""
from __future__ import annotations

import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VP = os.path.join(_ROOT, "versions.json")

NEW = [
    {"path": "AGENTS.md", "level": "A", "kind": "doc", "content_version": "1.0",
     "iteration": "r06", "note": "给 AI 的操作规则极简入口（六域，指向 AI_CONTEXT）",
     "updated_at": "2026-10-11", "status": "active"},
    {"path": "AI_MAP.md", "level": "A", "kind": "doc", "content_version": "1.0",
     "iteration": "r06", "note": "机器地图（派生物，render_ai_map 生成）",
     "updated_at": "2026-10-11", "status": "generated"},
    {"path": "FLYWHEEL_HEALTH.md", "level": "A", "kind": "doc", "content_version": "1.0",
     "iteration": "r06", "note": "飞轮健康度仪表盘（派生物，render_flywheel_health 生成）",
     "updated_at": "2026-10-11", "status": "generated"},
    {"path": "DEPENDENCY_MAP.md", "level": "A", "kind": "doc", "content_version": "1.0",
     "iteration": "r06", "note": "跨文件依赖图（派生物，render_dependency_map 生成）",
     "updated_at": "2026-10-11", "status": "generated"},
    {"path": "src/spc/ai_map.py", "level": "B", "kind": "code",
     "note": "AI_MAP 生成源（llms.txt 式机器地图）", "updated_at": "2026-10-11"},
    {"path": "src/spc/flywheel.py", "level": "B", "kind": "code",
     "note": "飞轮健康度统计 + 置信度校准（K/D1）", "updated_at": "2026-10-11"},
    {"path": "src/spc/depmap.py", "level": "B", "kind": "code",
     "note": "跨文件依赖图生成源（C）", "updated_at": "2026-10-11"},
    {"path": "tools/render_ai_map.py", "level": "B", "kind": "code",
     "note": "AI_MAP.md 渲染器（--write 写回）", "updated_at": "2026-10-11"},
    {"path": "tools/render_flywheel_health.py", "level": "B", "kind": "code",
     "note": "FLYWHEEL_HEALTH.md 渲染器", "updated_at": "2026-10-11"},
    {"path": "tools/render_dependency_map.py", "level": "B", "kind": "code",
     "note": "DEPENDENCY_MAP.md 渲染器", "updated_at": "2026-10-11"},
    {"path": "tools/render_task_brief.py", "level": "B", "kind": "code",
     "note": "下轮任务书生成器（B+G 价值评分）", "updated_at": "2026-10-11"},
    {"path": "tools/report_calibration.py", "level": "B", "kind": "code",
     "note": "置信度校准报告（D1）", "updated_at": "2026-10-11"},
    {"path": "tests/test_flywheel.py", "level": "B", "kind": "test",
     "note": "K/D1/D2/C/F 测试（无需 pytest）", "updated_at": "2026-10-11"},
    {"path": "tests/test_ai_readability.py", "level": "B", "kind": "test",
     "note": "P1/P2/B/H/I 测试", "updated_at": "2026-10-11"},
    {"path": "tools/register_r06_upgrade.py", "level": "B", "kind": "code",
     "note": "r06 批量实施登记脚本（一次性，登记含自身）", "updated_at": "2026-10-11"},
]


def main() -> int:
    v = json.load(open(_VP, encoding="utf-8"))
    existing = {e["path"] for e in v["entries"]}
    added = 0
    for e in NEW:
        if e["path"] in existing:
            print(f"跳过（已登记）：{e['path']}")
            continue
        v["entries"].append(e)
        added += 1
    v["index_version"] = "1.3"
    json.dump(v, open(_VP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"新增 {added} 条（总计 {len(v['entries'])}），index_version 1.2 → 1.3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
