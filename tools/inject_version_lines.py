# -*- coding: utf-8 -*-
"""inject_version_lines.py — 按 versions.json 给 .md 文件插入/更新版本行

版本行格式（紧跟 H1 标题之后，空一行）：
    > **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11
    > 权威源：`VERSION_INDEX.md` ｜ 版本规则见 `docs/VERSIONING_DOCS.md`

幂等：已存在版本行时**原地更新**，不重复插入。

用法：
    python tools/inject_version_lines.py --dry-run
    python tools/inject_version_lines.py --write
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

# 版本行标记（用于识别已有版本行，便于幂等更新）
MARK = "> **版本**："
TAIL = "｜ 版本规则见 `docs/VERSIONING_DOCS.md`"

# 这些文件不插（自动生成的派生物 / 有自身格式）
SKIP = {
    "memory/facts/INDEX.md",   # 由 cli index 生成，版本在生成器里加
    "VERSION_INDEX.md",        # 自身就是索引，头部已有版本信息
    "versions.json",           # JSON，无 markdown 头
}


def make_line(cv: str, it: str, updated: str) -> str:
    return (
        f"{MARK}`{cv}` ｜ 轮次 `{it}` ｜ 更新 {updated} ｜ 权威源 `VERSION_INDEX.md`\n"
        f"> 版本规则见 `docs/VERSIONING_DOCS.md`"
    )


def inject(text: str, line: str) -> tuple[str, str]:
    """返回 (新文本, 动作)。动作 ∈ {inserted, updated, unchanged}"""
    lines = text.split("\n")

    # 找到 H1 行
    h1 = None
    for i, l in enumerate(lines):
        if l.startswith("# "):
            h1 = i
            break
    if h1 is None:
        return text, "no-h1"

    # 找已有版本行（在 H1 之后的 12 行内）
    old_at = None
    for j in range(h1 + 1, min(h1 + 14, len(lines))):
        if lines[j].startswith(MARK):
            old_at = j
            break

    if old_at is not None:
        # 更新已有版本行（可能是两行：MARK 行 + TAIL 行）
        end = old_at + 1
        while end < len(lines) and lines[end].strip() and not lines[end].startswith("#"):
            if lines[end].startswith(">") and "版本规则见" in lines[end]:
                end += 1
                break
            end += 1
        new = lines[:old_at] + line.split("\n") + lines[end:]
        ntext = "\n".join(new)
        return (ntext, "unchanged") if ntext == text else (ntext, "updated")

    # 插入：在 H1 后空一行插版本行 + 空行
    ins = []
    # 跳过 H1 后紧跟的空行
    k = h1 + 1
    while k < len(lines) and not lines[k].strip():
        k += 1
    new = lines[:h1 + 1] + [""] + line.split("\n") + [""] + lines[k:]
    return "\n".join(new), "inserted"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    d = json.load(open(os.path.join(_ROOT, "versions.json"), encoding="utf-8"))
    targets = [
        e for e in d["entries"]
        if e["level"] in ("A", "B")
        and e["path"].endswith(".md")
        and e.get("content_version")
        and e["path"] not in SKIP
    ]

    stats = {"inserted": 0, "updated": 0, "unchanged": 0, "no-h1": 0}
    for e in sorted(targets, key=lambda x: x["path"]):
        p = os.path.join(_ROOT, e["path"])
        text = open(p, encoding="utf-8").read()
        line = make_line(e["content_version"], e.get("iteration") or "", e.get("updated_at") or "")
        ntext, act = inject(text, line)
        stats[act] = stats.get(act, 0) + 1
        icon = {"inserted": "+", "updated": "~", "unchanged": "=", "no-h1": "!"}.get(act, "?")
        print(f"  {icon} {e['path']}" + ("" if act != "no-h1" else "   ⚠️ 无 H1 标题"))
        if args.write and act in ("inserted", "updated"):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(ntext)

    print()
    print(f"目标 {len(targets)} 个 .md")
    for k in ("inserted", "updated", "unchanged", "no-h1"):
        if stats.get(k):
            print(f"  {k}: {stats[k]}")
    if not args.write:
        print("\n（dry-run；加 --write 落盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
