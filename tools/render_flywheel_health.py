# -*- coding: utf-8 -*-
"""tools/render_flywheel_health.py — FLYWHEEL_HEALTH.md 渲染器（K）。

用法：
    python tools/render_flywheel_health.py [--write]
"""
from __future__ import annotations

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from spc.flywheel import collect_metrics, render_health  # noqa: E402


def main() -> int:
    write = "--write" in sys.argv
    rp = os.path.join(_ROOT, "FLYWHEEL_HEALTH.md")
    new = render_health(collect_metrics(_ROOT), root=_ROOT)

    if os.path.exists(rp):
        old = open(rp, encoding="utf-8-sig").read()
    else:
        old = ""
    if old.strip() == new.strip():
        print("FLYWHEEL_HEALTH.md 已是最新。")
        return 0
    print("FLYWHEEL_HEALTH.md 有更新（结论台账变化）。")
    if not write:
        print("（dry-run，未写回；加 --write 生效）")
        return 0
    open(rp, "w", encoding="utf-8").write(new)
    print(f"✓ 已写回 FLYWHEEL_HEALTH.md（{len(new.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
