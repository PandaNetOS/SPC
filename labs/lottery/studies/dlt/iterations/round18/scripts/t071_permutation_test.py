# -*- coding: utf-8 -*-
"""t071_permutation_test.py — round18 置换检验 max|r| 多重比较校正

对 round17 的 40 个形态撞号比做置换检验：
原假设：形态标签与 w1（一等奖注数）无关。
做法：随机打乱 w1 的时间顺序，重新计算所有 40 个形态的撞号比，
记录 max|ratio - 1|，重复 B=2000 次得到零分布。
实际观测的 max|r| 在零分布中的位置 = 校正后 p 值。
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

SEED = 20261012
B = 2000
CUT_DATE = "2013-08-28"

ROOT = Path(__file__).resolve().parents[5]
CSV = ROOT / "games" / "dlt" / "data" / "raw" / "dlt_full_2933.csv"
OUT = Path(__file__).parent / "t071_permutation_test.json"


def feats(row) -> dict[str, bool]:
    f = sorted([row[f"front_{i}"] for i in range(1, 6)])
    b = sorted([row[f"back_{i}"] for i in range(1, 3)])
    res: dict[str, bool] = {}
    res["front_min_le5"] = f[0] <= 5
    res["front_max_ge31"] = f[-1] >= 31
    res["front_all_le17"] = all(x <= 17 for x in f)
    res["front_all_ge18"] = all(x >= 18 for x in f)
    res["front_all_le12"] = all(x <= 12 for x in f)
    res["front_all_ge25"] = all(x >= 25 for x in f)
    res["front_le12_ge3"] = sum(1 for x in f if x <= 12) >= 3
    res["front_ge25_ge2"] = sum(1 for x in f if x >= 25) >= 2
    res["front_center_ge3"] = sum(1 for x in f if 15 <= x <= 21) >= 3
    res["front_boundary_low_ge2"] = sum(1 for x in f if x <= 5) >= 2
    res["front_boundary_high_ge2"] = sum(1 for x in f if x >= 31) >= 2
    res["front_all_odd"] = all(x % 2 == 1 for x in f)
    res["front_all_even"] = all(x % 2 == 0 for x in f)
    res["front_odd_ge4"] = sum(1 for x in f if x % 2 == 1) >= 4
    res["front_odd_le1"] = sum(1 for x in f if x % 2 == 1) <= 1
    tails = [x % 10 for x in f]
    tail_counts = Counter(tails)
    res["front_tail_cluster3"] = max(tail_counts.values()) >= 3
    res["front_same_tail_any"] = any(c >= 2 for c in tail_counts.values())
    res["front_has_0tail"] = any(x % 10 == 0 for x in f)
    res["front_has_5tail"] = any(x % 10 == 5 for x in f)
    gaps = [f[i+1] - f[i] for i in range(4)]
    res["front_maxrun_ge3"] = _max_run(f) >= 3
    res["front_maxrun_ge4"] = _max_run(f) >= 4
    res["front_mingap_eq1"] = min(gaps) == 1
    res["front_mingap_eq2"] = min(gaps) == 2
    res["front_maxgap_ge10"] = max(gaps) >= 10
    res["front_has_mirror"] = any((36 - x) in set(f) for x in f)
    res["front_arith_ge2"] = _arith_triplets(f) >= 2
    res["front_center_dev_le2"] = sum(abs(x - 18) for x in f) / 5 <= 2
    lucky = {6, 8, 16, 18, 28}
    taboo = {4, 14, 24}
    res["front_lucky_ge2"] = sum(1 for x in f if x in lucky) >= 2
    res["front_taboo_ge1"] = sum(1 for x in f if x in taboo) >= 1
    res["front_has_4"] = any(x in taboo for x in f)
    res["front_has_8"] = any(x in {8, 18, 28} for x in f)
    res["back_all_odd"] = all(x % 2 == 1 for x in b)
    res["back_all_even"] = all(x % 2 == 0 for x in b)
    res["back_le6_both"] = all(x <= 6 for x in b)
    res["back_ge7_both"] = all(x >= 7 for x in b)
    res["back_same_tail"] = b[0] % 10 == b[1] % 10
    res["front_allodd_allbig"] = res["front_all_odd"] and res["front_all_ge18"]
    res["front_alleven_allsmall"] = res["front_all_even"] and res["front_all_le17"]
    res["front_run_and_birthday"] = res["front_mingap_eq1"] and all(x <= 31 for x in f)
    res["front_norun_noclueter"] = (not res["front_mingap_eq1"]) and (not res["front_tail_cluster3"])
    return res


def _max_run(f: list[int]) -> int:
    s = sorted(f)
    mx, cur = 1, 1
    for i in range(1, len(s)):
        if s[i] - s[i-1] == 1:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 1
    return mx


def _arith_triplets(f: list[int]) -> int:
    s = sorted(f)
    n = len(s)
    c = 0
    for i in range(n):
        for j in range(i+1, n):
            for k in range(j+1, n):
                if s[j] - s[i] == s[k] - s[j]:
                    c += 1
    return c


def compute_ratio_matrix(feat_matrix: np.ndarray, w1: np.ndarray) -> np.ndarray:
    """计算每个形态的撞号比。feat_matrix: (n_periods, n_features) boolean."""
    n, k = feat_matrix.shape
    ratios = np.ones(k)
    for j in range(k):
        mask = feat_matrix[:, j]
        n_in = mask.sum()
        n_out = n - n_in
        if n_in < 10 or n_out < 10:
            ratios[j] = 1.0
            continue
        mean_in = w1[mask].mean()
        mean_out = w1[~mask].mean()
        if mean_out > 0:
            ratios[j] = mean_in / mean_out
    return ratios


def main():
    df = pd.read_csv(CSV, encoding="utf-8-sig", dtype={"draw_num": str})
    df["date"] = pd.to_datetime(df["date"])
    post = df[df["date"] >= CUT_DATE].copy()
    print(f"后段期数: {len(post)}")

    feat_rows = [feats(row) for _, row in post.iterrows()]
    feat_df = pd.DataFrame(feat_rows)
    feat_cols = feat_df.columns.tolist()
    w1 = post["prize1_winners"].values.astype(float)
    feat_matrix = feat_df.values.astype(bool)

    # 实际观测
    obs_ratios = compute_ratio_matrix(feat_matrix, w1)
    obs_max_abs = np.max(np.abs(obs_ratios - 1.0))
    print(f"观测 max|r-1| = {obs_max_abs:.4f}")

    # 置换检验
    rng = np.random.default_rng(SEED)
    perm_max_abs = np.zeros(B)
    for i in range(B):
        # 随机打乱 w1 的顺序
        w1_perm = rng.permutation(w1)
        perm_ratios = compute_ratio_matrix(feat_matrix, w1_perm)
        perm_max_abs[i] = np.max(np.abs(perm_ratios - 1.0))

    # 校正后 p 值
    p_value = (perm_max_abs >= obs_max_abs).sum() / B
    print(f"置换检验 p = {p_value:.4f} (B={B})")

    # 每个形态的未校正 p 值（从原始 bootstrap CI 推断）
    # 这里我们用置换分布计算每个形态的校正后 p 值
    # 做法：对每个形态 j，看置换分布中 |ratio_j - 1| >= 观测值 的比例
    # 但这样计算量太大（40 * B），我们用 max|r| 校正的更简单形式：
    # 如果 obs_max_abs 在零分布中不显著，那所有形态都不显著
    # 如果 obs_max_abs 显著，再看哪些形态的 |r-1| 超过阈值

    # 计算零分布的 95% 分位数（阈值）
    threshold_95 = np.percentile(perm_max_abs, 95)
    print(f"零分布 95% 分位数 = {threshold_95:.4f}")

    # 每个形态的 |r-1|
    obs_abs = np.abs(obs_ratios - 1.0)
    sig_features = []
    for j, col in enumerate(feat_cols):
        if obs_abs[j] >= threshold_95:
            sig_features.append({
                "feature": col,
                "ratio": float(obs_ratios[j]),
                "abs_dev": float(obs_abs[j]),
                "significant_after_perm": True
            })

    result = {
        "meta": {
            "seed": SEED,
            "bootstrap_B": B,
            "n_periods": len(post),
            "n_features": len(feat_cols),
        },
        "observed": {
            "max_abs_dev": float(obs_max_abs),
        },
        "permutation_test": {
            "p_value": float(p_value),
            "threshold_95": float(threshold_95),
            "conclusion": "显著" if p_value < 0.05 else "不显著",
        },
        "significant_features_after_correction": sig_features,
    }

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n输出: {OUT}")


if __name__ == "__main__":
    main()
