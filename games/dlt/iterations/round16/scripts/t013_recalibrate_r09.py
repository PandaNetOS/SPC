# -*- coding: utf-8 -*-
"""t013_recalibrate_r09.py — P0：动态锚点重校准（F-0016 / F-0017 / F-0022 / F-0023）

validate 到期警告（6/6/5/5 轮）：F-0016 / F-0017 / F-0022 / F-0023。
SOP §6：核验锚点数值是否仍成立；成立则维持并重记（NOOP 语义），否则 update 通道。

核验项（数据版本 dlt_full_2933，E6 段 = 26014-26115，102 期）：
  1. F-0016：E6 一等奖总派发 max(w1×amt1) < 1 亿、触发 0 次 —— 参照 0.9788 亿
  2. F-0017/F-0022：E6 锚点 w1 中位 = 6、一等奖派发额中位 = 0.4252 亿 —— 参照 6 / 0.4252
  3. F-0023：E6 段期初奖池分位 top−bottom 的 er_t 均值差 —— 参照 +0.017 p≈0.27（不显著）

T-047 联动：全部维持 → NOOP 语义（evidence.noop_count 递增，不污染 status/change_type）。
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

P1 = 1.0 / 21425712.0      # 一等奖每注概率
P2 = 20.0 / 21425712.0     # 二等奖每注概率（5+1）


def main():
    with open(DATA, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    dts = np.array([date.fromisoformat(r["date"]) for r in rows])
    w1 = np.array([float(r["prize1_winners"]) for r in rows])
    amt1 = np.array([float(r["prize1_amount_yuan"]) for r in rows])
    amt2 = np.array([float(r["prize2_amount_yuan"]) for r in rows])
    pool = np.array([float(r["pool_yuan"]) for r in rows])
    e6 = dts >= date(2026, 2, 2)
    payout1 = w1 * amt1

    rep = {}

    # ---- 1. F-0016：封顶从未触发 ----
    e6_total1 = payout1[e6]
    mx = float(e6_total1.max())
    n_trig = int((e6_total1 >= 1e8).sum())
    rep["F0016_cap_trigger"] = {
        "n_e6": int(e6.sum()),
        "max_total1_yuan": mx,
        "n_triggered": n_trig,
        "cap_total_yuan": 1e8,
        "reference": "max 0.9788 亿 / 0 触发",
        "match": mx < 1e8 and n_trig == 0,
    }
    print("[F-0016] E6 一等奖总派发 max=%.4f 亿，触发 %d 次 → %s"
          % (mx / 1e8, n_trig, "维持（未触发）" if rep["F0016_cap_trigger"]["match"] else "UPDATE"))

    # ---- 2. F-0017 / F-0022：E6 锚点 ----
    w1_med = int(np.median(w1[e6]))
    pay_med = float(np.median(payout1[e6])) / 1e8
    rep["F0017_F0022_anchor"] = {
        "w1_median": w1_med,
        "payout1_median_yi": round(pay_med, 4),
        "reference_n0": 6, "reference_pool_yi": 0.4252,
        "match": w1_med == 6 and abs(pay_med - 0.4252) < 0.10,
    }
    print("[F-0017/22] E6 锚点 w1 中位=%d（参照 6）派发额中位=%.4f 亿（参照 0.4252）→ %s"
          % (w1_med, pay_med, "维持" if rep["F0017_F0022_anchor"]["match"] else "UPDATE"))

    # ---- 3. F-0023：E6 期初奖池分位 er_t 差 ----
    # er_t = (P1×amt1 + P2×amt2)/2（每 1 元基本投注的期望派发，仅一二等奖下界）
    er = (P1 * amt1 + P2 * amt2) / 2.0
    pool_prev = np.concatenate([[np.nan], pool[:-1]])  # 期初奖池 = 上期期末
    lo_q, hi_q = 0.25, 0.75
    e6_ok = e6 & np.isfinite(pool_prev)
    thr_lo, thr_hi = np.quantile(pool_prev[e6_ok], [lo_q, hi_q])
    A = er[e6_ok & (pool_prev <= thr_lo)]
    C = er[e6_ok & (pool_prev >= thr_hi)]
    diff = float(C.mean() - A.mean())
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(2000):
        ra = A[rng.integers(0, len(A), len(A))]
        rc = C[rng.integers(0, len(C), len(C))]
        boots.append(rc.mean() - ra.mean())
    boots = np.array(boots)
    p_two = float(min(1.0, 2 * min((boots <= 0).mean(), (boots >= 0).mean())))
    rep["F0023_pool_prev_er"] = {
        "n_e6_ok": int(e6_ok.sum()),
        "er_diff": round(float(diff), 4),
        "p": round(float(p_two), 3),
        "reference": "+0.017 / p≈0.27（不显著）",
        "match": p_two > 0.05,
    }
    print("[F-0023] E6 期初奖池 top−bottom er_t 差=%.4f p=%.3f → %s"
          % (diff, p_two, "维持（不显著）" if rep["F0023_pool_prev_er"]["match"] else "UPDATE"))

    # ---- 4. 汇合判定 ----
    matches = {k: v["match"] for k, v in rep.items()}
    verdict = all(matches.values())
    rep["verdict"] = (
        "维持（recalibrated）——F-0016/F-0017/F-0022/F-0023 的锚点与统计结论在当前数据版本"
        "（dlt_full_2933，含 26115）下仍成立。按 SOP 重记校准时间戳；NOOP 语义（noop_count+1，"
        "不污染 status/change_type）。" if verdict else
        "UPDATE 建议——存在漂移项，需走 change_type=update 通道。"
    )
    rep["noop_apply"] = {
        "fact_ids": ["F-0016", "F-0017", "F-0022", "F-0023"],
        "noop_count": 1,
        "recalibrated_in": "round09",
        "note": "T-047 NOOP 原子操作实战：证据不足/数值未变时显式记录『维持』，替代『什么都不写』的隐式状态。",
    }
    print("\n[verdict]", rep["verdict"])

    out = os.path.join(_OUT, "t013_recalibrate_r09.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print("[written]", out)


if __name__ == "__main__":
    main()
