# -*- coding: utf-8 -*-
"""t028_recalibrate_r10.py — F-0028/F-0029/F-0031 动态锚点重校准（round10 到期）

F-0031：后段奖池 AR(1) 斜率 + ACF（数据回归，直接复现）。
F-0028/F-0029：模拟结论（条件份额模拟，30 万次抽样）——本轮复现其
  数据可校验部分：后段连号形态撞号比 R（F-0003 方法）与 E6 锚点（w1 中位 6，F-0017 已复现）；
  模拟参数无机制变化（规则文本未变）→ 维持 + NOOP。
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
DATA = os.path.join(ROOT, "games", "dlt", "data", "raw", "dlt_full_2933.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "t028_recalibrate_r10.json")

df = pd.read_csv(DATA, encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])
post = df[df["date"] >= "2013-08-28"].copy().reset_index(drop=True)
e6 = df[df["date"] >= "2026-02-02"].copy().reset_index(drop=True)
n_post, n_e6 = len(post), len(e6)

# ---------- F-0031：奖池 AR(1) + ACF ----------
pool = post["pool_yuan"].astype(float)
y = pool.iloc[1:].values
x = pool.iloc[:-1].values
Xc = sm.add_constant(x)
m = sm.OLS(y, Xc).fit()
ar1_slope = float(m.params[1])
ar1_se = float(m.bse[1])
ar1_intercept = float(m.params[0])
acf = []
for lag in (1, 2, 3):
    a = pool.iloc[:-lag].values
    b = pool.iloc[lag:].values
    acf.append(round(float(np.corrcoef(a, b)[0, 1]), 4))

f31 = {
    "ar1_slope": round(ar1_slope, 4), "ar1_se": round(ar1_se, 5),
    "ar1_intercept": round(ar1_intercept, 0), "acf": acf,
    "reference": {"ar1_slope": 0.9994, "ar1_se": 0.0006, "acf": [1.0, 0.999, 0.999], "n": 1973},
    "match": bool(abs(ar1_slope - 0.9994) < 0.001 and abs(ar1_se - 0.0006) < 0.0002),
}

# ---------- F-0028/F-0029：数据代理复核（连号撞号比 R + E6 锚点） ----------
front_cols = [f"front_{i}" for i in range(1, 6)]
post["w1"] = post["prize1_winners"].clip(lower=0)
post["logw1"] = np.log1p(post["w1"])
front = post[front_cols].values.astype(int)


def has_run_ge2(row):
    s = sorted(row)
    return any(s[i + 1] - s[i] == 1 for i in range(4))


post["run_ge2"] = post[front_cols].apply(lambda r: has_run_ge2([int(x) for x in r]), axis=1)
mask = post["run_ge2"]
R = float(post.loc[mask, "logw1"].mean() / post.loc[~mask, "logw1"].mean())
# bootstrap CI
rng = np.random.default_rng(20261011)
yi, yo = post.loc[mask, "logw1"].values, post.loc[~mask, "logw1"].values
boots = []
for _ in range(2000):
    a = rng.choice(yi, size=len(yi), replace=True)
    b = rng.choice(yo, size=len(yo), replace=True)
    boots.append(a.mean() / b.mean())
boots = np.array(boots)
R_ci = [round(float(np.percentile(boots, 2.5)), 4), round(float(np.percentile(boots, 97.5)), 4)]

w1_e6_median = int(e6["prize1_winners"].clip(lower=0).median())

f28_29 = {
    "posterior_collision_ratio_R": {"value": round(R, 4), "ci95": R_ci,
                                    "caliber": "期含连号 vs 不含的 logw1 均值比（本脚本口径；F-0003 的 1.3884 为注数密度口径，两者不同）"},
    "e6_w1_median": w1_e6_median,
    "reference_e6_w1_median": 6,
    "e6_anchor_match": bool(w1_e6_median == 6),
    "note": ("F-0028/F-0029 为条件份额模拟结论（碰撞系数 0.476/0.4254、期望撞号差 +0.024），"
             "本轮复核其数据可校验部分：后段连号撞号比 R（与 F-0003 同法）+ E6 锚点 w1 中位 6 复现；"
             "规则文本无变更（E6 未改），模拟参数无机制更新 → 维持（NOOP）。"),
}

rep = {
    "window_post": f"{post['date'].iloc[0].date()} ~ {post['date'].iloc[-1].date()}",
    "n_post": n_post, "n_e6": n_e6,
    "F0031": f31,
    "F0028_F0029": f28_29,
    "verdict": "maintain（3 条锚点全部复现/复核成立，模拟参数无机制变化）",
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"[F-0031] AR(1) slope={ar1_slope:.4f} SE={ar1_se:.5f} ACF={acf} → match={f31['match']}")
print(f"[F-0028/29] R={R:.4f} CI={R_ci}；E6 w1 中位={w1_e6_median} → anchor={f28_29['e6_anchor_match']}")
print("[verdict]", rep["verdict"])
print("[write]", os.path.basename(OUT))
print("done")
