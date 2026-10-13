# -*- coding: utf-8 -*-
"""spc — 彩票投注策略研究框架

两种用户：
  1. AI 分析者（每轮迭代）—— 用 memory / game 模块读写结论与数据
  2. 外部工具（选号器 / 前端）—— 用 strategy 模块消费 strategy.json

设计要点：
  - 框架/彩种分离：本包不含任何具体彩种参数，一律从 labs/<lab>/studies/<id>/game.yaml 读
  - 契约优先：输入输出都受 spec/*.schema.json 约束
  - 红线强制：affects_win_probability 恒为 False
  - 路径单一权威：所有路径一律走 spc.paths，禁止在调用点拼装路径片段

快速开始：
    from spc.api import SmartPick

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
    """向上查找仓库根（含 `spec/` 与 `labs/` 的那一级）。

    实现委托给 `spc.paths.repo_root`（路径的单一权威来源）——
    此处保留同名函数只为向后兼容既有调用点，**新代码请直接用 spc.paths**。
    迁移后 `games/` 已删除，判据改为 `labs/`；旧 checkout 仍可通过
    paths 的兼容探测回落。
    """
    from .paths import repo_root as _repo_root

    return _repo_root(start)


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
