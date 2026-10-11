# -*- coding: utf-8 -*-
"""research_lib.stability —— 分期稳健性原语（彩种无关）。

来源：round03/scripts/b2_split_stability.py（Q-001 清偿，F-0003 更新）：
  「效应是否在时段前后同向？幅度是否稳定？」→ 按切点分两段，各段出
  Bootstrap 比值 + CI，判定符号一致性与 CI 重叠。

判定语义（与 Q-001 验收判据一致）：
  - 两段 CI 下界均 > 1 → 稳健（同向成立）；
  - 两段 CI 不重叠 → 幅度差异显著（衰减/增强）；
  - 任一段样本不足（返回 None）→ 判定 unknown，禁止硬推。
"""
from __future__ import annotations

import numpy as np

from .stats import ratio_and_boot


def ci_overlap(ci_a: list[float], ci_b: list[float]) -> bool:
    """两个 95%CI 是否重叠（不重叠 = 幅度差异统计显著）。"""
    return not (ci_a[1] < ci_b[0] or ci_b[1] < ci_a[0])


def split_ratio_stability(
    x: np.ndarray,
    mask: np.ndarray,
    cut_mask: np.ndarray,
    n_boot: int = 2000,
    seed: int = 20261011,
) -> dict:
    """按 cut_mask 把样本切为前后两段，各段算『mask 组 / 非 mask 组』的比率 + CI。

    参数：
      x        : 指标值数组（如中出注数）
      mask     : 分组布尔（如『连号期 runs>=2』）
      cut_mask : 切点布尔（True = 后段，False = 前段）
    返回：
      {
        "pre":  {ratio, ci95, n_a, n_b, ...} 或 None,
        "post": {...} 或 None,
        "same_sign": 两段 ratio 是否都 > 1（任一段 None → False）,
        "ci_overlap": 两段 CI 是否重叠（任一段 None → None）,
        "verdict": "robust" | "sign_consistent_but_different" | "inconclusive" | "unknown",
      }
    """
    pre_r = ratio_and_boot(x[~cut_mask & mask], x[~cut_mask & ~mask], n_boot, seed)
    post_r = ratio_and_boot(x[cut_mask & mask], x[cut_mask & ~mask], n_boot, seed)

    if pre_r is None or post_r is None:
        return {
            "pre": pre_r, "post": post_r,
            "same_sign": False, "ci_overlap": None,
            "verdict": "unknown",
        }

    same_sign = pre_r["ratio"] > 1 and post_r["ratio"] > 1
    overlap = ci_overlap(pre_r["ci95"], post_r["ci95"])
    if same_sign and overlap:
        verdict = "robust"
    elif same_sign and not overlap:
        verdict = "sign_consistent_but_different"  # 同向但幅度显著变化
    elif not same_sign:
        verdict = "inconclusive"  # 方向不一致，效应不稳健
    else:  # pragma: no cover（防御）
        verdict = "unknown"
    return {
        "pre": pre_r, "post": post_r,
        "same_sign": same_sign, "ci_overlap": overlap,
        "verdict": verdict,
    }
