# -*- coding: utf-8 -*-
"""smartpickcore — 彩票投注策略研究框架

两种用户：
  1. AI 分析者（每轮迭代）—— 用 memory / game 模块读写结论与数据
  2. 外部工具（选号器 / 前端）—— 用 strategy 模块消费 strategy.json

设计要点：
  - 框架/彩种分离：本包不含任何具体彩种参数，一律从 games/<id>/game.yaml 读
  - 契约优先：输入输出都受 spec/*.schema.json 约束
  - 红线强制：affects_win_probability 恒为 False

快速开始：
    from smartpickcore.api import SmartPick

    sp = SmartPick.for_game("dlt")
    print(sp.boundary())
    print(sp.strategy())
    print(sp.validate())
"""
from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "repo_root",
    "Memory",
    "RedLineViolation",
    "load_game_config",
    "compute_space",
]

import os


def repo_root(start: str | None = None) -> str:
    """向上查找仓库根（含 spec/ 与 games/ 的那一级）。"""
    cur = os.path.abspath(start or os.path.dirname(__file__))
    for _ in range(8):
        if os.path.isdir(os.path.join(cur, "spec")) and os.path.isdir(
            os.path.join(cur, "games")
        ):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    # 兜底：src/smartpickcore/ → 仓库根
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# 延迟导入，避免在无第三方依赖时报错
def __getattr__(name: str):  # pragma: no cover
    if name == "Memory":
        from .memory import Memory
        return Memory
    if name == "RedLineViolation":
        from .memory import RedLineViolation
        return RedLineViolation
    if name == "load_game_config":
        from .game import load_game_config
        return load_game_config
    if name == "compute_space":
        from .game import compute_space
        return compute_space
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
