# -*- coding: utf-8 -*-
"""tools/render_readme_tree.py — README 目录树渲染器（派生物写入）。

README 的 `## 目录结构` 代码块 = `spc.tree.render_tree(versions.json entries)`
的产物。本脚本把代码块整体替换为最新渲染结果，并维护"派生物"注记。

用法：
    python tools/render_readme_tree.py            # dry-run：只打印差异
    python tools/render_readme_tree.py --write    # 写回 README.md

配合 validate 的 check_structure_completeness（实际文件↔登记双向比对），
新增文件只要登记 versions.json → --write → validate 全绿，树自动同步。
"""
from __future__ import annotations

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from spc.tree import load_versions, render_tree  # noqa: E402

_MARKER = "## 目录结构"
_DERIVED_NOTE = (
    "> **目录树为派生物**：由 `tools/render_readme_tree.py` 从 versions.json 生成；"
    "新增文件登记 versions.json 后运行 `--write` 同步，勿手改。"
)


def _extract_block(text: str) -> tuple[int, int, int]:
    """定位目录结构代码块，返回 (start_```, end_```, end_derived_zone)。"""
    lines = text.split("\n")
    start = end = None
    for i, ln in enumerate(lines):
        if ln.strip() == _MARKER:
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "```":
                    start = j
                    break
            break
    if start is None:
        raise SystemExit("README 未找到「## 目录结构」区块")
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == "```":
            end = j
            break
    if end is None:
        raise SystemExit("目录结构代码块未闭合")
    return start, end, end + 1


def main() -> int:
    write = "--write" in sys.argv
    rp = os.path.join(_ROOT, "README.md")
    text = open(rp, encoding="utf-8").read()
    start, end, after = _extract_block(text)

    v = load_versions(_ROOT)
    new_tree = render_tree(v["entries"])
    old_tree = "\n".join(text.split("\n")[start + 1:end]).strip()

    lines = text.split("\n")
    if new_tree.strip() == old_tree and _DERIVED_NOTE in text:
        print("目录树已是最新，无差异。")
        return 0

    print("目录树差异：")
    old_set = old_tree.split("\n")
    new_set = new_tree.split("\n")
    print(f"  旧 {len(old_set)} 行 → 新 {len(new_set)} 行")

    if not write:
        print("（dry-run，未写回；加 --write 生效）")
        return 0

    new_lines = lines[:start] + ["```", new_tree, "```"]
    # 在代码块后维护派生物注记（紧跟代码块结束行之后插入，若不存在）
    tail = lines[end + 1:]
    idx = 0
    while idx < len(tail) and tail[idx].strip().startswith(">"):
        if "派生物" in tail[idx]:
            tail[idx] = _DERIVED_NOTE
            has_note = True
            break
        idx += 1
    else:
        has_note = False
    if not has_note:
        tail.insert(0, "")
        tail.insert(1, _DERIVED_NOTE)
    new_lines.extend(tail)
    open(rp, "w", encoding="utf-8").write("\n".join(new_lines))
    print(f"✓ 已写回 README.md（目录树 {len(new_tree.splitlines())} 行 + 派生物注记）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
