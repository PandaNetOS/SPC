# -*- coding: utf-8 -*-
"""tools/render_ai_map.py — AI_MAP.md 渲染器（派生物写入，P1）。

用法：
    python tools/render_ai_map.py             # dry-run
    python tools/render_ai_map.py --write     # 写回 AI_MAP.md

配合 validate 的 _check_ai_map_rendered：AI_MAP.md 必须与
render_ai_map(versions.json) 逐字一致 —— 手改 / 漏 --write 会红。
"""
from __future__ import annotations

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from spc.ai_map import load_versions, render_ai_map  # noqa: E402

_DERIVED_NOTE = (
    "> **本文件是派生物**：由 `tools/render_ai_map.py` 从 versions.json 生成；"
    "新增文件登记 versions.json 后运行 `--write` 同步，勿手改。"
)


def main() -> int:
    write = "--write" in sys.argv
    rp = os.path.join(_ROOT, "AI_MAP.md")
    v = load_versions(_ROOT)
    new = render_ai_map(v["entries"], _ROOT)

    if os.path.exists(rp):
        old = open(rp, encoding="utf-8").read()
    else:
        old = ""
    if old.strip() == new.strip():
        print("AI_MAP.md 已是最新，无差异。")
        return 0

    print(f"AI_MAP.md 差异：旧 {len(old.splitlines())} 行 → 新 {len(new.splitlines())} 行")
    if not write:
        print("（dry-run，未写回；加 --write 生效）")
        return 0
    open(rp, "w", encoding="utf-8").write(new)
    print(f"✓ 已写回 AI_MAP.md（{len(new.splitlines())} 行 + 派生物注记）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
