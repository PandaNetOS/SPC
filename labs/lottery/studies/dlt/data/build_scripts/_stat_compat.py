# -*- coding: utf-8 -*-
"""_stat_compat.py — scipy.stats 的最小可用替代（纯标准库 + math）

为什么存在：build_derived_v4.py 只用到三个函数 ——
chi2.sf(x, k)（卡方上尾）与 norm.sf(x)（正态上尾）。
为它们拖一个 scipy 依赖不划算，且 scipy 是含 C 扩展的大包，
某些环境装不上（离线/无编译器/无临时目录）。

实现：卡方用不完全伽马函数（正则化下阶 Gamma P(k/2, x/2)），
用 math.lgamma + 级数/连分数展开；正态用 erf。
数值精度足够本仓库用途（p 值只做量级判断与排序）。
"""
from __future__ import annotations

import math

__all__ = ["chi2_sf", "norm_sf"]


def _gammainc_lower_reg(s: float, x: float) -> float:
    """正则化下阶不完全伽马 P(s,x)。数值方法（Lentz 连分数 / 级数）。"""
    if x <= 0.0:
        return 0.0
    if x < s + 1.0:
        # 级数展开
        return _gser(s, x)
    return 1.0 - _gcf(s, x)


def _gser(s: float, x: float, itmax: int = 300, eps: float = 3e-14) -> float:
    gln = math.lgamma(s)
    ap = s
    total = 1.0 / s
    delta = total
    for _ in range(itmax):
        ap += 1.0
        delta *= x / ap
        total += delta
        if abs(delta) < abs(total) * eps:
            break
    return total * math.exp(-x + s * math.log(x) - gln)


def _gcf(s: float, x: float, itmax: int = 300, eps: float = 3e-14) -> float:
    gln = math.lgamma(s)
    tiny = 1e-300
    b = x + 1.0 - s
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, itmax + 1):
        an = -i * (i - s)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return math.exp(-x + s * math.log(x) - gln) * h


def chi2_sf(x: float, k: int) -> float:
    """卡方上尾概率 P(X > x)，df=k。"""
    if x <= 0.0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - _gammainc_lower_reg(k / 2.0, x / 2.0)))


def norm_sf(x: float) -> float:
    """正态上尾概率 P(Z > x)。"""
    return 0.5 * math.erfc(x / math.sqrt(2.0))


if __name__ == "__main__":
    # 自检：与常见临界值对照
    # chi2(0.95, df=1) ≈ 3.841 ; chi2(0.95, df=34) ≈ 48.602 ; chi2(0.95,df=11)≈19.675
    for df, crit in [(1, 3.8415), (11, 19.6751), (34, 48.6024)]:
        got_p = chi2_sf(crit, df)
        print(f"chi2_sf({crit}, df={df}) = {got_p:.5f}  (expect ~0.05)")
    for z in [1.96, 2.576, 3.0]:
        print(f"norm_sf({z}) = {norm_sf(z):.5f}  (expect ~0.025/0.005/0.00135)")
