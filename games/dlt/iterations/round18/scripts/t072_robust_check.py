# -*- coding: utf-8 -*-
"""t072_robust_check.py — round18 重尾稳健复核

一等奖注数 var/mean=8.46（重尾），均值比可能被极端值主导。
用中位数比 + 10% 截尾均值复核 5 个显著形态的效应。
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

CUT_DATE = "2013-08-28"
ROOT = Path(__file__).resolve().parents[5]
CSV = ROOT / "games" / "dlt" / "data" / "raw" / "dlt_full_2933.csv"
OUT = Path(__file__).parent / "t072_robust_check.json"


def feats(row) -> dict[str, bool]:
    f = sorted([row[f"front_{i}"] for i in range(1, 6)])
    b = sorted([row[f"back_{i}"] for i in range(1, 3)])
    res: dict[str, bool] = {}
    res["front_max_ge31"] = f[-1] >= 31
    res["front_mingap_eq2"] = min([f[i+1]-f[i] for i in range(4)]) == 2
    res["back_all_even"] = all(x % 2 == 0 for x in b)
    res["back_same_tail"] = b[0] % 10 == b[1] % 10
    res["front_run_and_birthday"] = min([f[i+1]-f[i] for i in range(4)]) == 1 and all(x <= 31 for x in f)
    return res


def trimmed_mean(x: np.ndarray, trim: float = 0.1) -> float:
    """截尾均值：去掉最高和最低各 trim 比例。"""
    n = len(x)
    k = int(n * trim)
    if n - 2 * k < 2:
        return float(np.mean(x))
    s = np.sort(x)
    return float(np.mean(s[k:n-k]))


def main():
    df = pd.read_csv(CSV, encoding="utf-8-sig", dtype={"draw_num": str})
    df["date"] = pd.to_datetime(df["date"])
    post = df[df["date"] >= CUT_DATE].copy()

    feat_rows = [feats(row) for _, row in post.iterrows()]
    feat_df = pd.DataFrame(feat_rows)
    w1 = post["prize1_winners"].values.astype(float)

    results = {}
    for col in feat_df.columns:
        mask = feat_df[col].values
        w_in = w1[mask]
        w_out = w1[~mask]

        mean_in = w_in.mean()
        mean_out = w_out.mean()
        ratio_mean = mean_in / mean_out if mean_out > 0 else None

        med_in = np.median(w_in)
        med_out = np.median(w_out)
        ratio_med = med_in / med_out if med_out > 0 else None

        tm_in = trimmed_mean(w_in, 0.1)
        tm_out = trimmed_mean(w_out, 0.1)
        ratio_trim = tm_in / tm_out if tm_out > 0 else None

        results[col] = {
            "n_in": int(mask.sum()),
            "n_out": int((~mask).sum()),
            "mean_ratio": float(ratio_mean) if ratio_mean else None,
            "median_ratio": float(ratio_med) if ratio_med else None,
            "trimmed_mean_ratio": float(ratio_trim) if ratio_trim else None,
            "w_in_mean": float(mean_in),
            "w_out_mean": float(mean_out),
            "w_in_median": float(med_in),
            "w_out_median": float(med_out),
        }

        print(f"{col}: mean={ratio_mean:.3f}, median={ratio_med:.3f}, trim={ratio_trim:.3f}")

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n输出: {OUT}")


if __name__ == "__main__":
    main()
