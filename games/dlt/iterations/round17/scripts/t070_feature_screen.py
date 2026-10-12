# -*- coding: utf-8 -*-
"""t070_feature_screen.py — round17 全形态撞号比穷举筛选

对后段 1973 期（2013-08-28 起）的前区/后区号码，计算约 50 个 boolean 形态的
撞号比（含形态期一等奖注数均值 / 不含形态期一等奖注数均值）+ Bootstrap 95% CI。

输出：t070_feature_screen.json
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 20261012
B = 2000
CUT_DATE = "2013-08-28"  # F-0006 变点

ROOT = Path(__file__).resolve().parents[5]
CSV = ROOT / "games" / "dlt" / "data" / "raw" / "dlt_full_2933.csv"
OUT = Path(__file__).parent / "t070_feature_screen.json"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV, encoding="utf-8-sig", dtype={"draw_num": str})
    df["date"] = pd.to_datetime(df["date"])
    return df


# ─── 形态定义（纯函数，输入 front list / back list，输出 bool）───

def feats(row) -> dict[str, bool]:
    f = sorted([row[f"front_{i}"] for i in range(1, 6)])
    b = sorted([row[f"back_{i}"] for i in range(1, 3)])
    res: dict[str, bool] = {}

    # 大小类
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

    # 奇偶类
    res["front_all_odd"] = all(x % 2 == 1 for x in f)
    res["front_all_even"] = all(x % 2 == 0 for x in f)
    res["front_odd_ge4"] = sum(1 for x in f if x % 2 == 1) >= 4
    res["front_odd_le1"] = sum(1 for x in f if x % 2 == 1) <= 1

    # 尾数类
    tails = [x % 10 for x in f]
    from collections import Counter
    tail_counts = Counter(tails)
    res["front_tail_cluster3"] = max(tail_counts.values()) >= 3
    res["front_same_tail_any"] = any(c >= 2 for c in tail_counts.values())
    res["front_has_0tail"] = any(x % 10 == 0 for x in f)
    res["front_has_5tail"] = any(x % 10 == 5 for x in f)

    # 间隔/连号类
    gaps = [f[i+1] - f[i] for i in range(4)]
    res["front_maxrun_ge3"] = _max_run(f) >= 3
    res["front_maxrun_ge4"] = _max_run(f) >= 4
    res["front_mingap_eq1"] = min(gaps) == 1
    res["front_mingap_eq2"] = min(gaps) == 2
    res["front_maxgap_ge10"] = max(gaps) >= 10

    # 对称/等差类
    res["front_has_mirror"] = any((36 - x) in set(f) for x in f)
    res["front_arith_ge2"] = _arith_triplets(f) >= 2
    res["front_center_dev_le2"] = sum(abs(x - 18) for x in f) / 5 <= 2

    # 文化类
    lucky = {6, 8, 16, 18, 28}
    taboo = {4, 14, 24}
    res["front_lucky_ge2"] = sum(1 for x in f if x in lucky) >= 2
    res["front_taboo_ge1"] = sum(1 for x in f if x in taboo) >= 1
    res["front_has_4"] = any(x in taboo for x in f)
    res["front_has_8"] = any(x in {8, 18, 28} for x in f)

    # 后区类
    res["back_all_odd"] = all(x % 2 == 1 for x in b)
    res["back_all_even"] = all(x % 2 == 0 for x in b)
    res["back_le6_both"] = all(x <= 6 for x in b)
    res["back_ge7_both"] = all(x >= 7 for x in b)
    res["back_same_tail"] = b[0] % 10 == b[1] % 10

    # 组合类
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


# ─── 撞号比 + Bootstrap ───

def collision_ratio(w1_in: np.ndarray, w1_out: np.ndarray) -> dict:
    """撞号比 = mean(w1_in) / mean(w1_out)，Bootstrap CI。"""
    n_in, n_out = len(w1_in), len(w1_out)
    if n_in < 10 or n_out < 10:
        return {"n_in": n_in, "n_out": n_out, "ratio": None,
                "ci95": None, "verdict": "INCONCLUSIVE"}

    ratio = w1_in.mean() / w1_out.mean() if w1_out.mean() > 0 else None

    rng = np.random.default_rng(SEED)
    boot_ratios = []
    for _ in range(B):
        bi = rng.choice(w1_in, size=n_in, replace=True)
        bo = rng.choice(w1_out, size=n_out, replace=True)
        if bo.mean() > 0:
            boot_ratios.append(bi.mean() / bo.mean())
    boot_ratios = np.array(boot_ratios)
    ci = np.percentile(boot_ratios, [2.5, 97.5])

    if ci[0] > 1:
        verdict = "SIGNIFICANT_HIGH"
    elif ci[1] < 1:
        verdict = "SIGNIFICANT_LOW"
    else:
        verdict = "NOT_SIGNIFICANT"

    return {
        "n_in": n_in, "n_out": n_out,
        "mean_in": float(w1_in.mean()), "mean_out": float(w1_out.mean()),
        "ratio": float(ratio), "ci95": [float(ci[0]), float(ci[1])],
        "verdict": verdict,
    }


def main():
    df = load_data()
    post = df[df["date"] >= CUT_DATE].copy()
    print(f"后段期数: {len(post)}")

    # 对每期算形态
    feat_rows = []
    for _, row in post.iterrows():
        feat_rows.append(feats(row))
    feat_df = pd.DataFrame(feat_rows)
    feat_df["w1"] = post["prize1_winners"].values
    feat_df["date"] = post["date"].values

    # 分期
    mid = len(post) // 2
    early = feat_df.iloc[:mid]
    late = feat_df.iloc[mid:]

    results = {}
    for col in feat_df.columns:
        if col in ("w1", "date"):
            continue
        # 后段整体
        mask = feat_df[col].values
        w1_in = feat_df.loc[mask, "w1"].values.astype(float)
        w1_out = feat_df.loc[~mask, "w1"].values.astype(float)
        r = collision_ratio(w1_in, w1_out)

        # 分期
        mask_e = early[col].values
        w1_in_e = early.loc[mask_e, "w1"].values.astype(float)
        w1_out_e = early.loc[~mask_e, "w1"].values.astype(float)
        r_e = collision_ratio(w1_in_e, w1_out_e)

        mask_l = late[col].values
        w1_in_l = late.loc[mask_l, "w1"].values.astype(float)
        w1_out_l = late.loc[~mask_l, "w1"].values.astype(float)
        r_l = collision_ratio(w1_in_l, w1_out_l)

        # 分期同向判定
        same_dir = False
        if r["ratio"] and r_e["ratio"] and r_l["ratio"]:
            same_dir = (r["ratio"] > 1) == (r_e["ratio"] > 1) == (r_l["ratio"] > 1)

        results[col] = {
            "post_full": r,
            "post_early_half": r_e,
            "post_late_half": r_l,
            "same_direction": same_dir,
        }

    # 汇总
    sig_high = [k for k, v in results.items() if v["post_full"]["verdict"] == "SIGNIFICANT_HIGH"]
    sig_low = [k for k, v in results.items() if v["post_full"]["verdict"] == "SIGNIFICANT_LOW"]
    ns = [k for k, v in results.items() if v["post_full"]["verdict"] == "NOT_SIGNIFICANT"]
    inc = [k for k, v in results.items() if v["post_full"]["verdict"] == "INCONCLUSIVE"]

    output = {
        "meta": {
            "seed": SEED, "bootstrap_B": B, "cut_date": CUT_DATE,
            "n_post": len(post), "n_features": len(results),
        },
        "summary": {
            "significant_high": sig_high,
            "significant_low": sig_low,
            "not_significant": ns,
            "inconclusive": inc,
        },
        "results": results,
    }

    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== 汇总 ===")
    print(f"显著高（拥挤）: {len(sig_high)} 个 → {sig_high}")
    print(f"显著低（冷门）: {len(sig_low)} 个 → {sig_low}")
    print(f"不显著: {len(ns)} 个")
    print(f"样本不足: {len(inc)} 个")
    print(f"\n输出: {OUT}")


if __name__ == "__main__":
    main()
