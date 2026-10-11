# -*- coding: utf-8 -*-
"""research_lib 原语测试 —— 无需 pytest，直接 `python tests/test_research_lib.py`

## 守什么

研究资本化（Y 方向）的机械防线：
  1. 原语结果可复现（同 seed 同输出；seed 覆盖 → 输出可不同但仍在合理范围）
  2. 统计正确性用**已知分布**验证（不依赖真实数据）：
     - 比率估计：构造 2:1 均值比样本 → ratio_and_boot 点估计逼近 2，CI 覆盖真值
     - bootstrap 覆盖：标准正态 → CI 覆盖 0
     - Wilson 区间：小样本比例 → 区间含真值、不对称（正态近似会对称）
  3. 分期判定：构造「前后段同向」与「方向相反」两个场景 → verdict 正确
  4. 样本不足 → None / unknown（不硬报显著）
"""
from __future__ import annotations

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "src"))

import numpy as np  # noqa: E402

from research_lib import bootstrap_ci, ratio_and_boot, wilson_interval  # noqa: E402
from research_lib.stability import ci_overlap, split_ratio_stability  # noqa: E402

_PASS = 0
_FAIL = 0
_FAILURES: list[str] = []


def check(cond: bool, label: str) -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  ✓ {label}")
    else:
        _FAIL += 1
        _FAILURES.append(label)
        print(f"  ✗ {label}")


def test_ratio_and_boot() -> None:
    rng = np.random.default_rng(7)
    a = rng.exponential(scale=2.0, size=800)   # 均值 ≈ 2
    b = rng.exponential(scale=1.0, size=800)   # 均值 ≈ 1 → 真比率 ≈ 2
    r = ratio_and_boot(a, b, n_boot=500, seed=20261011)
    check(r is not None and abs(r["ratio"] - 2.0) < 0.25,
          f"stats: 2:1 均值比点估计 ≈ 2（实际 {r['ratio'] if r else None}）")
    check(r["ci95"][0] < 2.0 < r["ci95"][1],
          f"stats: 真比率 2 在 CI 内（{r['ci95']}）")
    # 可复现性
    r2 = ratio_and_boot(a, b, n_boot=500, seed=20261011)
    check(r["ci95"] == r2["ci95"] and r["ratio"] == r2["ratio"],
          "stats: 同 seed 输出可复现")
    # 样本不足
    check(ratio_and_boot(np.array([]), b, n_boot=100) is None,
          "stats: 空样本 → None（不硬报）")
    check(ratio_and_boot(a, np.zeros(5), n_boot=100) is None,
          "stats: 分母均值为 0 → None（不硬报）")


def test_bootstrap_ci() -> None:
    rng = np.random.default_rng(3)
    x = rng.normal(0, 1, 2000)
    r = bootstrap_ci(x, np.mean, n_boot=500, seed=20261011)
    check(r["ci95"][0] < 0 < r["ci95"][1],
          f"stats: 标准正态 bootstrap CI 覆盖 0（{r['ci95']}）")
    r2 = bootstrap_ci(x, np.median, n_boot=500, seed=20261011)
    check(r2["ci95"][0] < 0 < r2["ci95"][1],
          f"stats: 中位数 bootstrap CI 覆盖 0（{r2['ci95']}）")
    check(bootstrap_ci(np.array([]), np.mean) is None,
          "stats: bootstrap 空样本 → None")


def test_wilson_interval() -> None:
    # 小样本：k=1, n=20 → p=0.05，Wilson 区间应不对称地含真值
    w = wilson_interval(1, 20)
    check(w is not None and abs(w["p"] - 0.05) < 1e-9,
          f"stats: Wilson 点估计 = 0.05（{w['p']}）")
    check(w["ci95"][0] <= 0.05 <= w["ci95"][1],
          f"stats: Wilson 区间含 0.05（{w['ci95']}）")
    check(w["ci95"][1] - w["p"] > w["p"] - w["ci95"][0],
          "stats: Wilson 区间不对称（上界更宽，正态近似会对称）")
    check(wilson_interval(0, 0) is None, "stats: Wilson n=0 → None")
    check(wilson_interval(20, 20)["p"] == 1.0, "stats: 全中 p=1")


def test_split_ratio_stability() -> None:
    rng = np.random.default_rng(11)
    n = 2000
    # 场景 1：前后段同向（mask 组均值 2 倍于非 mask 组）→ robust
    mask = (rng.random(n) < 0.5)
    x1 = rng.exponential(scale=2.0, size=n) * np.where(mask, 1, 0.5)
    x1 = x1 * np.where(mask, 2.0, 1.0)  # mask 组均值 ≈ 4，非 mask ≈ 1 → 比率 ≈ 4
    cut = np.arange(n) >= n // 2
    s1 = split_ratio_stability(x1, mask, cut, n_boot=300, seed=20261011)
    check(s1["same_sign"] and s1["verdict"] in ("robust", "sign_consistent_but_different"),
          f"stability: 前后段同向 → same_sign=True（{s1['verdict']}）")
    # 场景 2：前后段方向相反 → inconclusive
    x2 = x1.copy()
    n_cut_mask = int((cut & mask).sum())
    x2[cut & mask] = rng.exponential(scale=0.5, size=n_cut_mask)  # 后段 mask 均值 < 非 mask
    s2 = split_ratio_stability(x2, mask, cut, n_boot=300, seed=20261011)
    check(not s2["same_sign"] and s2["verdict"] == "inconclusive",
          f"stability: 前后段方向相反 → inconclusive（{s2['verdict']}）")
    # 场景 3：样本不足 → unknown
    x3 = np.zeros(n); x3[:5] = 1.0
    m3 = np.zeros(n, dtype=bool); m3[:1] = True
    s3 = split_ratio_stability(x3, m3, cut, n_boot=100, seed=20261011)
    check(s3["verdict"] == "unknown", "stability: 样本不足 → unknown（不硬推）")
    # ci_overlap
    check(ci_overlap([1.0, 2.0], [1.5, 3.0]) is True, "stability: 重叠 CI → True")
    check(ci_overlap([1.0, 1.5], [2.0, 3.0]) is False, "stability: 不重叠 CI → False")


if __name__ == "__main__":  # pragma: no cover
    test_ratio_and_boot()
    test_bootstrap_ci()
    test_wilson_interval()
    test_split_ratio_stability()
    print(f"\n通过 {_PASS}  失败 {_FAIL}")
    if _FAILURES:
        print("失败项：")
        for f in _FAILURES:
            print(f"  ✗ {f}")
    sys.exit(1 if _FAIL else 0)
