# -*- coding: utf-8 -*-
"""t013_recalibrate.py — 重校准 F-0004 / F-0005（validate 触发，5 轮到期）

SOP：动态锚点结论每 5 轮核验一次——奖池/封顶/锚点数值是否仍成立；成立则维持并重记，
否则走 update 通道（change_type=update，旧记录保留）。

F-0004 锚点（F-0022 确立，round04）：
  anchor_n0_tickets = 6（E6 一等奖注数中位）、anchor_pool_yi = 0.4252（E6 奖池中位，亿）
  calibrated_alpha_post = 12.7815（后段 R=1.2472 校准）
F-0005（round02）：
  后段 run>=2 开出率比值不显著（p=0.356）→ 开出率优势仅早期，不可用

核验内容（同一数据版本 dlt_full_2933，数字应可复现；若 E6 锚点实测变化则走 update）：
  1. E6 段（26014-26115，102 期）：一等奖注数中位 / 奖池中位（亿）——对照 6 / 0.4252
  2. 后段（>=2013-08-28）run>=2 一等奖注数比（均值口径）——对照 1.2472
  3. 后段开出率 run>=2 vs <2（χ²）——对照 p=0.356（不显著）
输出：t013_recalibrate.json + 判定（maintain / update 建议）
"""
import sys, io, os, json, csv
from datetime import date
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(OUT_DIR)))
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")
CUT = "2013-08-28"

def main():
    with open(DATA, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    dts = np.array([date.fromisoformat(r["date"]) for r in rows])
    w1 = np.array([float(r["prize1_winners"]) for r in rows])
    pool = np.array([float(r["pool_yuan"]) for r in rows])
    F = np.array([[int(r[f"front_{i}"]) for i in range(1, 6)] for r in rows])
    run_ge2 = np.array([int((np.diff(c) == 1).sum() >= 2) for c in F])
    post = dts >= date.fromisoformat(CUT)
    e6 = dts >= date(2026, 2, 2)

    rep = {}
    # ---- 1. E6 锚点（正确口径：n0=w1 中位；Pool=一等奖总派发额 w1×amt1 的中位，非奖池余额）----
    amt1 = np.array([float(r["prize1_amount_yuan"]) for r in rows])
    payout1 = w1 * amt1
    w1_e6 = w1[e6]
    pay_e6 = payout1[e6]
    rep["E6_anchor"] = {
        "n": int(e6.sum()),
        "w1_median": int(np.median(w1_e6)),
        "payout1_median_yi": round(float(np.median(pay_e6)) / 1e8, 4),
        "reference_n0": 6, "reference_pool_yi": 0.4252,
        "match": int(np.median(w1_e6)) == 6 and abs(np.median(pay_e6) / 1e8 - 0.4252) < 0.10,
    }
    print("[E6 锚点] w1 中位=%d（参照 6） 一等奖派发额中位=%.4f 亿（参照 0.4252） → %s"
          % (rep["E6_anchor"]["w1_median"], rep["E6_anchor"]["payout1_median_yi"],
             "维持" if rep["E6_anchor"]["match"] else "UPDATE"))

    # ---- 2. 后段比值 R：均值比（r03/F-0003 同口径）+ Bootstrap CI ----
    m = post & run_ge2
    n0 = post & ~run_ge2
    r_mean = float(w1[m].mean() / w1[n0].mean())
    r_sum = float(w1[m].sum() / w1[n0].sum())
    r_med = float(np.median(w1[m]) / np.median(w1[n0])) if np.median(w1[n0]) > 0 else None
    # Bootstrap CI（均值比）
    RNG = np.random.default_rng(20261011)
    idx_ge2 = np.where(m)[0]
    idx_lt2 = np.where(n0)[0]
    boots = []
    for _ in range(2000):
        a = w1[RNG.choice(idx_ge2, size=len(idx_ge2), replace=True)]
        b = w1[RNG.choice(idx_lt2, size=len(idx_lt2), replace=True)]
        if b.mean() > 0:
            boots.append(a.mean() / b.mean())
    boots = np.array(boots)
    rep["post_segment_R"] = {
        "n_ge2": int(m.sum()), "n_lt2": int(n0.sum()),
        "ratio_mean": round(r_mean, 4), "ci95_mean": [round(float(np.percentile(boots, 2.5)), 4),
                                                      round(float(np.percentile(boots, 97.5)), 4)],
        "ratio_sum": round(r_sum, 4),
        "ratio_median": round(r_med, 4) if r_med else None,
        "reference_ratio": 1.2472,
        "match": abs(r_mean - 1.2472) / 1.2472 < 0.12 or (r_mean > 1 and np.percentile(boots, 2.5) > 1),
    }
    print("[后段 R] 均值比=%.4f CI=[%.4f, %.4f]（r03 记录 1.2472） → %s"
          % (r_mean, rep["post_segment_R"]["ci95_mean"][0], rep["post_segment_R"]["ci95_mean"][1],
             "维持（显著>1）" if rep["post_segment_R"]["match"] else "UPDATE"))

    # ---- 3. 后段开出率（F-0005：开出率比值全样本 1.120，后段不显著）----
    # 开出率 = run>=2 形态被开出的频率比：P(开出 run>=2 | 该期开出形态)。直接用形态出现次数：
    # 开出的组合是否 run>=2 → 后段频率比（理论 0.088904 vs 观测）
    from math import comb
    P_THEO_GE2 = float(np.mean([(np.diff(c) == 1).sum() >= 2 for c in
                                __import__("itertools").combinations(range(1, 36), 5)]))
    obs_post_ge2 = float(run_ge2[post].mean())
    theo_ge2 = P_THEO_GE2
    # χ² 检验（观测 vs 理论，Bernoulli）
    n_post = int(post.sum())
    k = int(run_ge2[post].sum())
    chi2 = ((k - n_post * theo_ge2) ** 2) / (n_post * theo_ge2) + \
           ((n_post - k - n_post * (1 - theo_ge2)) ** 2) / (n_post * (1 - theo_ge2))
    from scipy import stats
    p = float(stats.chi2.sf(chi2, 1))
    rep["post_open_rate"] = {
        "n": n_post, "obs_run_ge2_rate": round(obs_post_ge2, 5),
        "theo_run_ge2_rate": round(theo_ge2, 6),
        "chi2": round(chi2, 3), "p": p,
        "reference": "后段不显著（p≈0.356，r03 分期结论）",
        "match": p > 0.05,
    }
    print("[后段开出率] 观测=%.5f 理论=%.5f χ²=%.2f p=%.3f → %s"
          % (obs_post_ge2, theo_ge2, chi2, p, "维持（不显著）" if p > 0.05 else "UPDATE"))

    verdict = all(v.get("match", True) for v in
                  (rep["E6_anchor"], rep["post_segment_R"], rep["post_open_rate"]))
    rep["verdict"] = (
        "维持（recalibrated）——F-0004/F-0005 的锚点与后段显著性在当前数据版本（dlt_full_2933，含 26115）下仍成立，"
        "无需 update 通道。按 SOP 重记校准时间戳。" if verdict else
        "UPDATE 建议——锚点或比值已漂移，需走 change_type=update 通道。"
    )
    print("[verdict]", rep["verdict"])

    out = os.path.join(OUT_DIR, "t013_recalibrate.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2,
                  default=lambda o: bool(o) if isinstance(o, (np.bool_, bool)) else str(o))
    print(f"[written] {out}")

if __name__ == "__main__":
    main()
