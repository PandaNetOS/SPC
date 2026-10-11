# -*- coding: utf-8 -*-
"""research_lib.stats —— 统计原语（彩种无关）。

来源：
  - `ratio_and_boot` ← round03/scripts/b2_split_stability.py::ratio_and_boot
    （F-0003 同口径估计器；中位数比/均值比/NB2 对照见 b2_robust_estimators.py）
  - `wilson_interval` ← T-046 方法纪律：比例类用 Wilson 区间
    （文献 27/28/29；小样本禁用 CLT 正态近似）

纪律（沿用 STATISTICAL_DISCIPLINE.md）：
  - 所有重抽样必须显式传 `seed`（默认 20261011，统一种子），保证可复现；
  - CI 用分位数（percentile），不用正态近似（重尾分布下 CLT 不可靠）；
  - 样本为空或分母为 0 时返回 None（不硬报显著）。
"""
from __future__ import annotations

import numpy as np

DEFAULT_SEED = 20261011  # 统一种子（L0 锚点），与历史轮次脚本一致


def bootstrap_ci(
    sample: np.ndarray,
    stat_fn,
    n_boot: int = 2000,
    seed: int = DEFAULT_SEED,
    ci: tuple[float, float] = (2.5, 97.5),
) -> dict | None:
    """通用 bootstrap：对样本独立重采样，应用 stat_fn，输出点估计 + 分位 CI。

    参数：
      sample : 1-D 数组（观测样本）
      stat_fn: 接收重采样数组、返回标量的统计函数（如 np.mean / np.median）
    返回：
      {"estimate": 点估计, "ci95": [lo, hi], "n": len(sample)}
      样本为空时返回 None。
    """
    if sample is None or len(sample) == 0:
        return None
    rng = np.random.default_rng(seed)
    n = len(sample)
    est = float(stat_fn(sample))
    boots = np.empty(n_boot)
    for k in range(n_boot):
        rs = sample[rng.integers(0, n, n)]
        try:
            boots[k] = float(stat_fn(rs))
        except (ValueError, ZeroDivisionError):  # noqa: S110
            boots[k] = np.nan
    lo, hi = np.nanpercentile(boots, ci)
    return {
        "estimate": round(est, 6),
        "ci95": [round(float(lo), 6), round(float(hi), 6)],
        "n": int(n),
    }


def ratio_and_boot(
    a: np.ndarray,
    b: np.ndarray,
    n_boot: int = 2000,
    seed: int = DEFAULT_SEED,
) -> dict | None:
    """比率 a.mean()/b.mean() + Bootstrap 95%CI（a、b 各自独立重采样）。

    来源：round03/scripts/b2_split_stability.py::ratio_and_boot（F-0003 同口径）。
    返回 None 当任一段为空或 b 均值为 0（样本不足，禁止硬报）。
    """
    if a is None or b is None or len(a) == 0 or len(b) == 0 or b.mean() == 0:
        return None
    rng = np.random.default_rng(seed)
    est = a.mean() / b.mean()
    na, nb = len(a), len(b)
    boots = np.empty(n_boot)
    for k in range(n_boot):
        ra = a[rng.integers(0, na, na)].mean()
        rb = b[rng.integers(0, nb, nb)].mean()
        boots[k] = ra / rb if rb > 0 else np.nan
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    return {
        "ratio": round(float(est), 4),
        "ci95": [round(float(lo), 4), round(float(hi), 4)],
        "n_a": int(na),
        "n_b": int(nb),
        "mean_a": round(float(a.mean()), 4),
        "mean_b": round(float(b.mean()), 4),
    }


def wilson_interval(k: int, n: int, z: float = 1.96) -> dict | None:
    """Wilson 分数区间（比例类首选，小样本不用正态近似）。

    来源：T-046 方法纪律（文献 27/28/29）。
    返回 {"p": 点估计, "ci95": [lo, hi], "k": k, "n": n}；n<=0 返回 None。
    """
    if n <= 0:
        return None
    p = k / n
    if p == 0.0:
        return {"p": 0.0, "ci95": [0.0, 0.0], "k": int(k), "n": int(n)}
    if p == 1.0:
        return {"p": 1.0, "ci95": [1.0, 1.0], "k": int(k), "n": int(n)}
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return {
        "p": round(float(p), 6),
        "ci95": [round(float(lo), 6), round(float(hi), 6)],
        "k": int(k),
        "n": int(n),
    }
