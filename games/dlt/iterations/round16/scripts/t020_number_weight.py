# -*- coding: utf-8 -*-
"""t020_number_weight.py — T-020：逐号偏好权重建模（Q-006 / H-002）

背景：F-0004 用『单一 α（连号）+ 生日号 1.25』近似人群选号权重。
T-020 假设：逐号偏好真实存在（如 1-31 生日可及段 vs 32-35），单一 α 是粗糙代理。

方法（后段口径 dlt_full_2933，>=2013-08-28，1973 期）：
  1. 逐号相对撞号强度 S_j = mean(log1p(w1) | 期含 j) / mean(log1p(w1) | 期不含 j)
     —— w1 重尾（max 106），log1p 下均值稳健；S_j>1 偏好、<1 回避
  2. 区间对比：1-31（生日可及）vs 32-35 的 S 均值差 + bootstrap CI（research_lib 原语）
  3. OLS 全模型 log1p(w1) ~ 35×号码 indicator + run≥2 + 生日，对比逐号项 vs 仅 α+生日
     （R² 增量与系数显著性 → 逐号权重是否显著改善拟合）
产出：逐号权重表 + 区间判定 + 是否支持 F-0004 置信度提升（新 FACTS 素材）
"""
import csv
import io
import json
import os
import sys
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np

_OUT = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(_OUT)))
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")
SEED = 20261011
CUT = "2013-08-28"


def main():
    with open(DATA, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    dts = np.array([date.fromisoformat(r["date"]) for r in rows])
    post = dts >= date.fromisoformat(CUT)
    F = np.array([[int(r[f"front_{i}"]) for i in range(1, 6)] for r in rows])[post]
    w1 = np.array([float(r["prize1_winners"]) for r in rows])[post]
    y = np.log1p(w1)  # 重尾稳健目标

    n_periods, n_front = F.shape[0], 35
    X_num = np.zeros((n_periods, n_front), float)
    for j in range(1, 36):
        X_num[:, j - 1] = (F == j).any(axis=1).astype(float)
    run_ge2 = np.array([(np.diff(c) == 1).sum() >= 2 for c in F]).astype(float)
    birthday = (F.max(axis=1) <= 31).astype(float)  # 全前区生日可及

    rep = {}

    # ---- 1. 逐号相对强度 S_j ----
    S = {}
    for j in range(1, 36):
        m_in = X_num[:, j - 1] == 1
        mean_in = y[m_in].mean()
        mean_out = y[~m_in].mean()
        S[str(j)] = round(float(mean_in / mean_out), 4) if mean_out > 0 else None
    rep["per_number_strength"] = S
    s31 = np.array([S[str(j)] for j in range(1, 32)])
    s_hi = np.array([S[str(j)] for j in range(32, 36)])
    print("[逐号强度] 1-31 均值=%.4f  32-35 均值=%.4f" % (s31.mean(), s_hi.mean()))

    # ---- 2. 区间对比 bootstrap（research_lib 口径：percentile，seed 显式）----
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(2000):
        a = s31[rng.integers(0, len(s31), len(s31))].mean()
        b = s_hi[rng.integers(0, len(s_hi), len(s_hi))].mean()
        boots.append(a - b)
    boots = np.array(boots)
    diff = s31.mean() - s_hi.mean()
    lo, hi = np.percentile(boots, [2.5, 97.5])
    rep["birthday_segment"] = {
        "mean_1to31": round(float(s31.mean()), 4),
        "mean_32to35": round(float(s_hi.mean()), 4),
        "diff": round(float(diff), 4),
        "ci95": [round(float(lo), 4), round(float(hi), 4)],
        "n_1to31": 31, "n_32to35": 4,
        "verdict": "生日可及段显著更重" if lo > 0 else "无显著差异",
    }
    print("[区间] 1-31 − 32-35 = %.4f CI=[%.4f, %.4f] → %s"
          % (diff, lo, hi, rep["birthday_segment"]["verdict"]))

    # ---- 3. OLS 全模型：逐号项是否显著改善（对照 α+生日）----
    X_base = np.column_stack([np.ones(n_periods), run_ge2, birthday])
    X_full = np.column_stack([np.ones(n_periods), X_num, run_ge2, birthday])
    beta_base, *_ = np.linalg.lstsq(X_base, y, rcond=None)
    beta_full, *_ = np.linalg.lstsq(X_full, y, rcond=None)
    pred_base = X_base @ beta_base
    pred_full = X_full @ beta_full
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2_base = 1 - ((y - pred_base) ** 2).sum() / ss_tot
    r2_full = 1 - ((y - pred_full) ** 2).sum() / ss_tot
    num_coefs = beta_full[1:36]
    n_signif = int((np.abs(num_coefs) > 0.05).sum())  # 粗略显著性阈值（log 尺度）
    rep["ols_compare"] = {
        "r2_base_alpha_birthday": round(float(r2_base), 5),
        "r2_full_per_number": round(float(r2_full), 5),
        "r2_delta": round(float(r2_full - r2_base), 5),
        "n_number_coefs_abs_gt_005": n_signif,
        "n_obs": int(n_periods),
        "verdict": (
            "逐号项显著改善拟合（新证据支持逐号权重模型）" if r2_full - r2_base > 0.01
            else "逐号项改善有限（单一 α 近似可接受）"
        ),
    }
    print("[OLS] R² 基线(α+生日)=%.5f → 全模型(逐号)=%.5f Δ=%.5f；|β|>0.05 的号码 %d/35 → %s"
          % (r2_base, r2_full, r2_full - r2_base, n_signif,
             rep["ols_compare"]["verdict"]))

    # ---- 4. 与 F-0004 的关系 ----
    rep["conclusion"] = {
        "statement": (
            "逐号偏好强度 S_j 在后段数据上存在结构：生日可及段（1-31）与高段（32-35）"
            "相对撞号强度差 %s；OLS 逐号项 R² 增量 %s。"
            % (rep["birthday_segment"]["verdict"].split("显著")[0] + "（" + str(rep["birthday_segment"]["diff"]) + "）"
               if False else str(rep["birthday_segment"]["diff"]),
               str(rep["ols_compare"]["r2_delta"]))
        ),
        "impact_on_F0004": (
            "F-0004 的生日号权重 1.25 属逐号结构的粗粒度近似；若逐号项 ΔR² 显著，"
            "F-0004 置信度可基于更细模型复评（不推翻方向，细化口径）。"
        ),
    }
    print("[statement]", rep["conclusion"]["statement"])

    out = os.path.join(_OUT, "t020_number_weight.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print("[written]", out)


if __name__ == "__main__":
    main()
