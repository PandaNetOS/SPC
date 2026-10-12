# -*- coding: utf-8 -*-
"""spc.tree — README 目录树的生成源（结构完整性根治，P1-2）。

README 的 `## 目录结构` 代码块从此是**派生物**：数据源 = versions.json entries，
由本模块渲染；新增文件 → 登记 versions.json → 运行
`python tools/render_readme_tree.py --write`，目录树自动同步，永不手改。

为什么需要（根因，2026-10-11）：
  目录树曾是手工维护的静态文本，与文件系统无绑定——v2.0 落地新增 8 个
  文件/目录时只更新了 grep 命中的行，树整片漏掉 13 处。根治 = 树从登记
  数据生成，新增文件只要登记 versions.json（validate check_structure 强制），
  树自动同步。

裁剪/聚合规则（防树膨胀、防误报）：
  · 排除：`*/data/**`（D 级数据走 SHA256 清单）、`tests/fixtures/**`（夹具）、
    `platform/protocol/templates/**`（模板）、`.gitignore`——不进入目录树；
  · 聚合：目录名 == `scripts` 时折叠为一行 `scripts/ ← N 个脚本`；
  · 标注：A/B/C 级有 content_version → `vX.Y`；version_ref 条目 → `v{ref_version}`；
    D 级 → `—`；
  · 注释：entry.note 截断（36 字符）作行尾 `← note`。
"""
from __future__ import annotations

import os
import json

_EXCLUDE_DIR_PREFIXES = (
    "tests/fixtures/",
    "platform/protocol/templates/",
)
_EXCLUDE_PATHS = {".gitignore"}

# 根层展示顺序（其余按字母序，目录排文件后）
_TOP_ORDER = [
    "pyproject.toml",
    "AI_CONTEXT.md",
    "VERSION_INDEX.md",
    "versions.json",
    "README.md",
]

_NOTE_MAX = 36
_VER_COL = 8  # 版本列定宽（等宽字体下 ← 注释列对齐）


def load_versions(root: str) -> dict:
    with open(os.path.join(root, "versions.json"), encoding="utf-8") as f:
        return json.load(f)


def _excluded(path: str) -> bool:
    if path in _EXCLUDE_PATHS:
        return True
    if "/data/" in path:  # games/*/data/** 与任何 data 子目录
        return True
    for pfx in _EXCLUDE_DIR_PREFIXES:
        if path.startswith(pfx):
            return True
    return False


def _annotation(entry: dict) -> str:
    cv = entry.get("content_version")
    if cv:
        return f"v{cv}"
    if entry.get("version_ref"):
        return f"v{entry.get('ref_version')}"
    return "—"


def _note(entry: dict) -> str:
    n = entry.get("note") or ""
    n = n.strip()
    if not n:
        return ""
    if len(n) > _NOTE_MAX:
        n = n[:_NOTE_MAX - 1] + "…"
    return f"← {n}"


def _is_dir(node) -> bool:
    """目录节点 = 嵌套 dict 且**不是**条目（条目必有 path 字段）。"""
    return isinstance(node, dict) and "path" not in node


def _sort_key(name: str, is_dir: bool) -> tuple:
    # 目录排文件后；根层按 _TOP_ORDER，其余按 (is_dir, 码点) 稳定排序
    return (0 if is_dir else 1, name)


def _build_tree(entries: list[dict]) -> dict:
    """entries → 嵌套 dict：{name: entry_or_dict}。"""
    root: dict = {}
    for e in entries:
        p = e.get("path") or ""
        if not p or _excluded(p):
            continue
        parts = p.split("/")
        node = root
        for part in parts[:-1]:
            nxt = node.get(part)
            if not isinstance(nxt, dict):
                nxt = {}
                node[part] = nxt
            node = nxt
        node[parts[-1]] = e
    return root


def _render_lines(nodes: dict, prefix: str = "") -> list[str]:
    """渲染节点树为行列表。nodes: name -> entry | dict。"""
    items = []
    for name, node in nodes.items():
        is_dir = isinstance(node, dict)
        items.append((_sort_key(name, is_dir), name, node, is_dir))
    items.sort(key=lambda t: t[0])

    # 同层 name 宽度对齐（目录名不 pad，文件 pad 到最大宽度）
    file_names = [it[1] for it in items if not it[3]]
    max_w = max((len(n) for n in file_names), default=0)

    lines: list[str] = []
    for i, (_, name, node, is_dir) in enumerate(items):
        last = i == len(items) - 1
        branch = "└── " if last else "├── "
        if _is_dir(node):
            # scripts 聚合：直接子项全为文件 → 折叠一行
            sub_files = [
                (n, nd) for n, nd in node.items()
                if not _is_dir(nd)
            ]
            if name == "scripts" and sub_files and len(sub_files) == len(node):
                lines.append(
                    f"{prefix}{branch}scripts/  ← 轮次脚本（{len(sub_files)} 个）"
                )
                continue
            lines.append(f"{prefix}{branch}{name}/")
            child_prefix = prefix + ("    " if last else "│   ")
            lines.extend(_render_lines(node, child_prefix))
        else:
            pad = name.ljust(max_w)
            ann = _annotation(node)
            note = _note(node)
            row = f"{prefix}{branch}{pad}  {ann.ljust(_VER_COL)}"
            if note:
                row += f"  {note}"
            lines.append(row.rstrip())
    return lines


def render_tree(entries: list[dict]) -> str:
    """渲染完整目录树文本（不含 ``` 包裹）。"""
    nodes = _build_tree(entries)
    # 根层排序：_TOP_ORDER 优先，其余字母序，目录排后
    items = []
    for name, node in nodes.items():
        is_dir = isinstance(node, dict)
        if name in _TOP_ORDER:
            key = (0, _TOP_ORDER.index(name))
        else:
            key = (1, _sort_key(name, is_dir)[0], name)
        items.append((key, name, node, is_dir))
    items.sort(key=lambda t: t[0])

    file_names = [it[1] for it in items if not it[3]]
    max_w = max((len(n) for n in file_names), default=0)

    lines: list[str] = []
    for i, (_, name, node, is_dir) in enumerate(items):
        last = i == len(items) - 1
        branch = "└── " if last else "├── "
        if _is_dir(node):
            sub_files = [
                (n, nd) for n, nd in node.items()
                if not _is_dir(nd)
            ]
            if name == "scripts" and sub_files and len(sub_files) == len(node):
                lines.append(f"{branch}scripts/  ← 轮次脚本（{len(sub_files)} 个）")
                continue
            lines.append(f"{branch}{name}/")
            child_prefix = ("    " if last else "│   ")
            lines.extend(_render_lines(node, child_prefix))
        else:
            pad = name.ljust(max_w)
            ann = _annotation(node)
            note = _note(node)
            row = f"{branch}{pad}  {ann.ljust(_VER_COL)}"
            if note:
                row += f"  {note}"
            lines.append(row.rstrip())
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    v = load_versions(root)
    print(render_tree(v["entries"]))
