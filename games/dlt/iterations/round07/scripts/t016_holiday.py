# -*- coding: utf-8 -*-
"""t016_holiday.py — T-016 节假日窗口撞号效应验证（H-006）

F-0032（r05）用公历近似（春节=2 月）给出探索性信号：国庆/元旦窗口连号比低于基线，
春节窗口不显著。本轮把春节改为**农历精确映射**（正月初一公历日期表 2007-2026，
稳定公开数据），国庆/元旦窗口复验同一口径。

指标：连号注数比 ratio = mean(w1 | run>=2) / mean(w1 | run<2)（r03/F-0032 同口径），
窗口 vs 基线（后段）Bootstrap CI（B=2000）。窗口定义：开奖日期落在 [假日起点, 假日终点]。

春节窗口：正月初一 ±7 天（含开奖日）；国庆：9/25-10/10；元旦：12/26-1/6（沿用 F-0032）。
基线：后段（>=2013-08-28）全部期。

输出：t016_holiday.json（本目录）
"""
import sys, io, os, json, csv
from datetime import date
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(OUT_DIR)))
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")
CUT = "2013-08-28"
RNG = np.random.default_rng(20261011)
B = 2000

# 农历正月初一（春节）公历日期，2007-2026（稳定公开数据，中国农历）
SPRING_FESTIVAL = {
    2007: (2, 18), 2008: (2, 7), 2009: (1, 26), 2010: (2, 14), 2011: (2, 3),
    2012: (1, 23), 2013: (2, 10), 2014: (1, 31), 2015: (2, 19), 2016: (2, 8),
    2017: (1, 28), 2018: (2, 16), 2019: (2, 5), 2020: (1, 25), 2021: (2, 12),
    2022: (2, 1), 2023: (1, 22), 2024: (2, 10), 2025: (1, 29), 2026: (2, 17),
}

def main():
    with open(DATA, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    n = len(rows)
    dts = np.array([date.fromisoformat(r["date"]) for r in rows])
    w1 = np.array([float(r["prize1_winners"]) for r in rows])
    sale = np.array([float(r["sale_yuan"]) for r in rows])
    F = np.array([[int(r[f"front_{i}"]) for i in range(1, 6)] for r in rows])
    run_ge2 = np.array([int((np.diff(c) == 1).sum() >= 2) for c in F])
    post = dts >= date.fromisoformat(CUT)

    def in_spring(d):
        """春节窗口：正月初一 ±7 天（含端点）。"""
        m, dd = SPRING_FESTIVAL[d.year]
        base = date(d.year, m, dd)
        return abs((d - base).days) <= 7

    def in_national(d):
        return date(d.year, 9, 25) <= d <= date(d.year, 10, 10)

    def in_newyear(d):
        lo = date(d.year, 12, 26)
        hi = date(d.year + 1, 1, 6)
        return lo <= d <= hi

    def ratio_on(sel):
        m = sel & run_ge2
        n0 = sel & ~run_ge2
        if m.sum() == 0 or n0.sum() == 0:
            return None
        return float(w1[m].sum() / w1[n0].sum())   # 加总口径（F-0032 同口径，受零值影响小）

    def ratio_mean_on(sel):
        """均值口径对照（r03 均值比）。"""
        m = sel & run_ge2
        n0 = sel & ~run_ge2
        if m.sum() == 0 or n0.sum() == 0:
            return None
        return float(w1[m].mean() / w1[n0].mean())

    def boot_ci(sel, rng):
        r = ratio_on(sel)
        if r is None:
            return None, None, None
        idx = np.where(sel)[0]
        vals = []
        for _ in range(B):
            s = rng.choice(idx, size=len(idx), replace=True)
            m = run_ge2[s]
            n0 = ~m
            if m.sum() == 0 or n0.sum() == 0:
                continue
            vals.append(w1[s[m]].sum() / w1[s[n0]].sum())
        vals = np.array(vals)
        return r, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))

    masks = {
        "spring_exact": in_spring,
        "national": in_national,
        "newyear": in_newyear,
    }
    rep = {"cut": CUT, "n_boot": B, "rng_seed": 20261011,
           "window": "春节=正月初一±7天（农历精确）；国庆 9/25-10/10；元旦 12/26-1/6",
           "ratio_definition": "sum(w1|run>=2)/sum(w1|run<2)（加总口径，F-0032 同口径；均值口径另列对照）"}

    base_post = post
    base_ratio, base_lo, base_hi = boot_ci(base_post, RNG)
    base_mean = ratio_mean_on(base_post)
    rep["baseline_post"] = {
        "n": int(base_post.sum()),
        "n_run_ge2": int((base_post & run_ge2).sum()),
        "ratio_sum": round(base_ratio, 3) if base_ratio else None,
        "ci95_sum": [round(base_lo, 3), round(base_hi, 3)] if base_lo else None,
        "ratio_mean_ref": round(base_mean, 3) if base_mean else None,
    }
    print("[基线-后段] n=%d run>=2=%d ratio_sum=%.3f CI=[%.3f, %.3f]（均值口径对照 %.3f）"
          % (rep["baseline_post"]["n"], rep["baseline_post"]["n_run_ge2"],
             base_ratio, base_lo, base_hi, base_mean))

    for name, fn in masks.items():
        win_all = np.array([fn(d) for d in dts])
        win_post = win_all & post
        d = {"n_all": int(win_all.sum()), "n_post": int(win_post.sum())}
        r_a, lo_a, hi_a = boot_ci(win_all, RNG)
        r_p, lo_p, hi_p = boot_ci(win_post, RNG)
        d["ratio_sum_all"] = round(r_a, 3) if r_a else None
        d["ci95_sum_all"] = [round(lo_a, 3), round(hi_a, 3)] if lo_a else None
        d["ratio_sum_post"] = round(r_p, 3) if r_p else None
        d["ci95_sum_post"] = [round(lo_p, 3), round(hi_p, 3)] if lo_p else None
        d["ratio_mean_post_ref"] = round(ratio_mean_on(win_post), 3) if ratio_mean_on(win_post) else None
        d["sale_ratio_post_vs_base"] = round(float(sale[win_post].mean() / sale[base_post].mean()), 3) if win_post.sum() else None
        d["n_run_ge2_post"] = int((win_post & run_ge2).sum())
        rep[name] = d
        print("[%s] 全样本 n=%d ratio_sum=%.3f CI=[%.3f,%.3f] | 后段 n=%d ratio_sum=%.3f CI=[%.3f,%.3f] 销量比=%.3f（均值对照 %.3f）"
              % (name, d["n_all"], r_a if r_a else -1, lo_a if lo_a else -1, hi_a if hi_a else -1,
                 d["n_post"], r_p if r_p else -1, lo_p if lo_p else -1, hi_p if hi_p else -1,
                 d["sale_ratio_post_vs_base"] or -1, d["ratio_mean_post_ref"] or -1))

    # 与基线比较的 z（窗口后段 vs 基线后段，粗略：用 bootstrap 分布）
    rep["verdict"] = (
        "春节精确映射后，若窗口后段 ratio 的 CI 仍宽含基线 → H-006 无法确认节假日撞号减弱；"
        "若窗口 ratio 显著低于基线且 CI 不含基线 → H-006 支持（节假日人群更随机）。"
        "F-0032 tentative 状态的更新以 CI 是否越过基线为准。"
    )
    out = os.path.join(OUT_DIR, "t016_holiday.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(f"[written] {out}")

if __name__ == "__main__":
    main()
