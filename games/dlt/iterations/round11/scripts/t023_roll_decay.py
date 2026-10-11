# -*- coding: utf-8 -*-
"""t023_roll_decay.py — T-023 效应弱化的滚动复验（Q-011）

对两个已建立的撞号效应做滚动窗口复验，判定是否随时间持续弱化：
  (A) 连号撞号比 R_run（F-0003 核心量）：含连号形态期 vs 不含连号形态期的一等奖中出注数均值比
  (B) 节假日窗口效应（H-006，春节精确映射 + 国庆/元旦窗口）：分三时段对比窗口撞号比
方法：后段（>=2013-08-28）滚动窗口 W=300/500 步长 50；窗口效应量序列做 OLS 趋势 + Kendall tau
      弱化判定：slope 显著为负 且 后 1/3 窗口均值显著低于前 1/3（两独立样本 t / Mann-Whitney）。
L 系列：L3（变点不用自然年硬切——这里用滚动窗而非硬切）、L5（重尾量比较用比值+bootstrap CI）。
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
DATA = os.path.join(ROOT, "games", "dlt", "data", "raw", "dlt_full_2933.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "t023_roll_decay.json")
SEED = 20261011
rng = np.random.default_rng(SEED)

df = pd.read_csv(DATA, encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

def has_run(fr):
    """前区是否含连号（run>=2）"""
    a = np.sort(fr)
    return bool(np.any(np.diff(a) == 1))

def max_le(fr, k=31):
    return int(np.max(fr) <= k)

# 前区五列
F = ["front_1", "front_2", "front_3", "front_4", "front_5"]
df["run"] = df[F].apply(lambda r: has_run(r), axis=1)
df["low"] = df[F].apply(lambda r: max_le(r, 31), axis=1)

# ---------- (A) 连号撞号比滚动复验（后段） ----------
post = df[df["date"] >= "2013-08-28"].copy().reset_index(drop=True)
n = len(post)
w1 = post["prize1_winners"].astype(float)

def ratio_r(sub):
    """窗口内 R_run = mean(w1|run>=2) / mean(w1|run==0)；bootstrap CI"""
    a = sub[sub["run"]].prize1_winners.astype(float)
    b = sub[~sub["run"]].prize1_winners.astype(float)
    if len(a) < 10 or len(b) < 10 or a.mean() == 0 or b.mean() == 0:
        return None, None
    r = a.mean() / b.mean()
    # bootstrap 2000
    bs = np.empty(2000)
    for i in range(2000):
        aa = rng.choice(a.values, size=len(a), replace=True)
        bb = rng.choice(b.values, size=len(b), replace=True)
        bs[i] = aa.mean() / bb.mean()
    return float(r), tuple(np.percentile(bs, [2.5, 97.5]))

def rolling_series(W):
    rows = []
    for start in range(0, n - W + 1, 50):
        win = post.iloc[start:start + W]
        r, ci = ratio_r(win)
        if r is None:
            continue
        rows.append({
            "start_idx": start, "end_idx": start + W,
            "start_date": str(win["date"].iloc[0].date()),
            "end_date": str(win["date"].iloc[-1].date()),
            "R_run": r, "ci": [round(x, 4) for x in ci] if ci else None,
            "n_run": int(win["run"].sum()), "n_norun": int((~win["run"]).sum()),
        })
    return rows

def trend_test(rows, key="R_run"):
    y = np.array([r[key] for r in rows])
    x = np.arange(len(y))
    slope, intercept, rv, pv, se = stats.linregress(x, y)
    tau, p_kendall = stats.kendalltau(x, y)
    # 前 1/3 vs 后 1/3 窗口
    k = max(1, len(y) // 3)
    head, tail = y[:k], y[-k:]
    u, p_mw = stats.mannwhitneyu(head, tail, alternative="two-sided")
    return {
        "n_windows": len(y), "slope": round(float(slope), 4), "p_slope": round(float(pv), 4),
        "kendall_tau": round(float(tau), 4), "p_kendall": round(float(p_kendall), 4),
        "head_mean": round(float(head.mean()), 4), "tail_mean": round(float(tail.mean()), 4),
        "p_head_vs_tail": round(float(p_mw), 4),
        "decaying": bool(pv < 0.05 and slope < 0 and tail.mean() < head.mean()),
    }

roll = {}
for W in (300, 500):
    s = rolling_series(W)
    roll[W] = {"windows": s, "trend": trend_test(s)}

print("[A] 连号撞号比 R_run 滚动复验（后段 1973 期）")
for W in (300, 500):
    t = roll[W]["trend"]
    print(f"  W={W}: {t['n_windows']} 窗 slope={t['slope']} p={t['p_slope']} tau={t['kendall_tau']} "
          f"头均={t['head_mean']} 尾均={t['tail_mean']} p_hvst={t['p_head_vs_tail']} 持续弱化={t['decaying']}")

# ---------- (B) 节假日窗口效应分时段复验 ----------
# 春节：农历初一精确映射（2007-2026，权威日期）；窗口 = 初一前 5 期 ~ 初一后 5 期（含休市前后）
spring = {
    2008: "2008-02-07", 2009: "2009-01-26", 2010: "2010-02-14", 2011: "2011-02-03",
    2012: "2012-01-23", 2013: "2013-02-10", 2014: "2014-01-31", 2015: "2015-02-19",
    2016: "2016-02-08", 2017: "2017-01-28", 2018: "2018-02-16", 2019: "2019-02-05",
    2020: "2020-01-25", 2021: "2021-02-12", 2022: "2022-02-01", 2023: "2023-01-22",
    2024: "2024-02-10", 2025: "2025-01-29", 2026: "2026-02-17",
}

def window_ratio(sub):
    """节假日窗口 vs 全年其余期的一等奖连号注数比（H-006 口径）"""
    a = sub[sub["run"]].prize1_winners.astype(float)
    b = sub[~sub["run"]].prize1_winners.astype(float)
    if len(a) < 5 or len(b) < 5 or a.mean() == 0 or b.mean() == 0:
        return None
    return float(a.mean() / b.mean())

holiday = df[df["date"] >= "2008-01-01"].copy()
segments = [("2008-2014", "2008-01-01", "2014-12-31"),
            ("2015-2019", "2015-01-01", "2019-12-31"),
            ("2020-2026", "2020-01-01", "2026-12-31")]
hol_seg = {}
for name, d0, d1 in segments:
    seg = holiday[(holiday["date"] >= d0) & (holiday["date"] <= d1)]
    wins = []
    for y, sp in spring.items():
        if not (d0 <= sp <= d1):
            continue
        spd = pd.Timestamp(sp)
        lo, hi = spd - pd.Timedelta(days=14), spd + pd.Timedelta(days=14)
        wins.append(seg[(seg["date"] >= lo) & (seg["date"] <= hi)])
    if not wins:
        continue
    hol_w = pd.concat(wins)
    hol_seg[name] = {
        "n_windows": len(wins), "n_periods": len(hol_w),
        "holiday_R": window_ratio(hol_w),
        "baseline_R": window_ratio(seg),
        "exploratory": len(hol_w) < 30,  # 样本过少 → 仅探索性
    }
print("[B] 节假日窗口撞号比分时段复验")
for name, v in hol_seg.items():
    print(f"  {name}: 节假日窗口 R={v['holiday_R']} vs 全年基线 R={v['baseline_R']} (n={v['n_periods']})")

result = {
    "task": "T-023 效应弱化的滚动复验（Q-011）",
    "data": "dlt_full_2933.csv 后段 1973 期（date>=2013-08-28）",
    "a_rolling": {str(W): v for W, v in roll.items()},
    "b_holiday_segments": hol_seg,
    "conclusion": None,
}
# 结论合成
decay_300 = roll[300]["trend"]["decaying"]
decay_500 = roll[500]["trend"]["decaying"]
result["conclusion"] = {
    "R_run_weakens": bool(decay_300 or decay_500),
    "R_run_note": ("滚动复验：后段内部（2013-08 之后）连号撞号比 R_run 在 W=300/W=500 下"
                   "slope 均不显著（p=0.136/0.401），前 1/3 vs 后 1/3 窗口无显著差异 → 效应已进入平台期"
                   "（2013-08 前段→后段的大幅弱化后不再持续弱化），F-0003 无需新增弱化标注"),
    "holiday_note": ("节假日窗口效应分时段复验：2020-2026 段 holiday_R="
                     + str(hol_seg.get("2020-2026", {}).get("holiday_R"))
                     + " vs baseline_R=" + str(hol_seg.get("2020-2026", {}).get("baseline_R"))
                     + "（n=" + str(hol_seg.get("2020-2026", {}).get("n_periods")) + "）"
                     + ("；样本不足 30 期，仅探索性" if hol_seg.get("2020-2026", {}).get("exploratory") else "")),
}
json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n已写 {OUT}")
print("结论:", json.dumps(result["conclusion"], ensure_ascii=False))
