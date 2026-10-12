# -*- coding: utf-8 -*-
"""spc.memory — 记忆层接口

本模块是 `platform/tools/memory.py` 的再导出 + 面向仓库的便捷封装。

分工：
  - `platform/tools/memory.py` —— 通用实现（彩种无关，可被外部复用）
  - `src/spc/memory.py` —— 本仓库的绑定（自动定位仓库根）

用法：
    from spc.memory import Memory
    mem = Memory()               # 自动定位仓库根
    mem.load_facts()
"""
from __future__ import annotations

import os
import sys

# 让 platform/tools 可导入（框架层不在 src/ 下）
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_TOOLS = os.path.join(_ROOT, "platform", "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

from memory import (  # noqa: E402  (platform/tools/memory.py)
    Memory as _Memory,
    MemoryError,
    RedLineViolation,
    VALID_CATEGORY,
    VALID_STATUS,
    RED_LINE_FIELD,
    FACT_REQUIRED,
)

__all__ = [
    "Memory",
    "MemoryError",
    "RedLineViolation",
    "VALID_CATEGORY",
    "VALID_STATUS",
    "RED_LINE_FIELD",
    "FACT_REQUIRED",
]


class Memory(_Memory):
    """绑定到本仓库的 Memory。

    repo_root 省略时自动定位（向上查找含 spec/ 与 games/ 的目录）。
    """

    def __init__(self, repo_root: str | None = None):
        super().__init__(repo_root or _ROOT)
