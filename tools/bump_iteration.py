# -*- coding: utf-8 -*-
"""tools/bump_iteration.py — 活文档轮次对齐（防「登记停滞」）

**为什么有这个工具**（r14.2 根治，README 头部版本行滞后事故）：

    校验器此前只做「文件内版本行 ↔ 索引条目」的**同源双向比对**，
    而 current_iteration 只作为 stats 打印、从不参与判定。
    于是索引条目一旦过期，inject_version_lines.py 会照抄过期值写进
    文件头 —— 两边一致、照样全绿。抓得住 A≠B，抓不住 A、B 一起过时。

    `src/spc/versions.py` 的轮次停滞检查补上了**发现端**（err），
    本工具是配套的**修复端**：把 versions.json 中 follows_current=true
    的活文档条目 iteration 对齐到 current_iteration，
    使后续 render_* + inject_version_lines 能写出正确的版本行。

⚠️ **顺序不可颠倒**：bump_iteration → render_* → inject_version_lines
   反过来会先把旧轮次刷进文件头、再改索引，白跑一轮（且当轮仍全绿）。

用法：
    python tools/bump_iteration.py --dry-run
    python tools/bump_iteration.py --write
    python tools/bump_iteration.py --write --to r15      # 同时推进 current_iteration
    python tools/bump_iteration.py --write --bump-content  # 同时 +0.1 content_version
"""
from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_VP = os.path.join(_ROOT, "versions.json")


def _bump_minor(cv: str | None) -> str | None:
    """内容版本 +0.1（1.16 → 1.17）。用整数运算，避开浮点误差。"""
    if not cv or not re.fullmatch(r"\d+\.\d+", cv):
        return cv
    major, minor = cv.split(".")
    return f"{major}.{int(minor) + 1}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="落盘（默认只 dry-run）")
    ap.add_argument("--dry-run", action="store_true", help="只显示将发生的改动")
    ap.add_argument("--to", metavar="rNN", default=None,
                    help="同时把 current_iteration 推进到该轮次（收尾时用）")
    ap.add_argument("--bump-content", action="store_true",
                    help="被对齐的条目同时 content_version +0.1"
                         "（仅当内容确有实质变更时使用，避免版本通胀）")
    args = ap.parse_args()

    raw = open(_VP, encoding="utf-8").read()
    had_trailing_nl = raw.endswith("\n")
    d = json.loads(raw)

    cur = d.get("current_iteration")
    if args.to:
        if not re.fullmatch(r"r\d{2}", args.to):
            print(f"✗ --to 格式非法 '{args.to}'（应为 rNN）")
            return 1
        if cur and args.to != cur:
            print(f"  ↑ current_iteration: {cur} → {args.to}")
        cur = args.to
        d["current_iteration"] = args.to
    if not cur:
        print("✗ versions.json 缺 current_iteration，无法对齐")
        return 1

    today = _dt.date.today().isoformat()
    changed: list[str] = []
    for e in d.get("entries") or []:
        if not e.get("follows_current"):
            continue
        path = e.get("path") or ""
        old = e.get("iteration") or ""
        if old == cur and e.get("updated_at") == today:
            continue
        if old == cur:
            # 轮次已对齐，但日期还是旧的 —— 只刷日期
            e["updated_at"] = today
            changed.append(f"  ~ {path}  (轮次 {cur} 已对齐，刷新 updated_at)")
            continue
        e["iteration"] = cur
        e["updated_at"] = today
        if args.bump_content and e.get("content_version"):
            nv = _bump_minor(e["content_version"])
            changed.append(f"  ~ {path}  轮次 {old} → {cur}，content_version "
                           f"{e['content_version']} → {nv}")
            e["content_version"] = nv
        else:
            changed.append(f"  ~ {path}  轮次 {old} → {cur}")

    n_follow = sum(1 for e in d.get("entries") or [] if e.get("follows_current"))
    print(f"current_iteration = {cur}；活文档（follows_current=true）共 {n_follow} 个")
    if not changed:
        print("  ✓ 全部已对齐，无需改动")
        return 0
    print(f"将改动 {len(changed)} 个条目：")
    for line in changed:
        print(line)

    if args.write:
        out = json.dumps(d, ensure_ascii=False, indent=2)
        if had_trailing_nl:
            out += "\n"
        with open(_VP, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        print(f"\n✓ 已写入 versions.json（{len(changed)} 项）")
        print("  下一步必须依次执行渲染与注入（顺序不可反）：")
        print("    python tools/render_readme_tree.py --write")
        print("    python tools/render_version_index.py --write")
        print("    python tools/render_ai_map.py --write")
        print("    python tools/render_dependency_map.py --write")
        print("    python tools/render_flywheel_health.py --write")
        print("    python tools/inject_version_lines.py --write")
    else:
        print("\n（dry-run；加 --write 落盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
