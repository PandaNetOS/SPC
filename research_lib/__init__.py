# -*- coding: utf-8 -*-
"""research_lib —— 研究资本化方法库（Y 方向）。

把历史轮次脚本里反复使用的统计原语提炼为彩种无关的可复用模块，
让新任务的研发出「重写脚本」变成「组合原语」—— 每轮不仅产出结论，
还产出方法资产（研究复利）。

来源映射见 `research_lib/README.md`（脚本 → 原语 → 历史验证结论）。
"""
from .stats import bootstrap_ci, ratio_and_boot, wilson_interval
from .stability import split_ratio_stability

__all__ = [
    "bootstrap_ci",
    "ratio_and_boot",
    "wilson_interval",
    "split_ratio_stability",
]
