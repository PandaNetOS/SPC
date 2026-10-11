# -*- coding: utf-8 -*-
"""tools/report_calibration.py — 置信度校准报告（D1）。

用法：
    python tools/report_calibration.py
"""
from __future__ import annotations

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from spc.flywheel import calibration_text, collect_metrics  # noqa: E402


def main() -> int:
    print(calibration_text(collect_metrics(_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
