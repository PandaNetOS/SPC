# -*- coding: utf-8 -*-
"""t021_sales_endogeneity.py — T-021 销量内生性检验（Q-005）

Granger 因果（奖池→销量→注数）+ 含/不含销量两版注数模型对比。
数据：后段 1973 期（date >= 2013-08-28），字段 pool_yuan / sale_yuan / prize1_winners。
判定：销量是否为内生变量（受奖池驱动且反馈影响注数）。
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
import statsmodels.api as sm

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
DATA = os.path.join(ROOT, "games", "dlt", "data", "raw", "dlt_full_2933.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "t021_sales_endogeneity.json")
SEED = 20261011

df = pd.read_csv(DATA, encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])
post = df[df["date"] >= "2013-08-28"].copy().reset_index(drop=True)
n = len(post)
print(f"[data] 后段 {n} 期（{post['date'].iloc[0].date()} ~ {post['date'].iloc[-1].date()}）")

# 变量：注数代理 w1（一等奖中出注数，log1p 抗重尾）、销量 sale（亿元）、奖池 pool（亿元）
post["w1"] = post["prize1_winners"]
post["logw1"] = np.log1p(post["w1"].clip(lower=0))
post["sale_yi"] = post["sale_yuan"] / 1e8
post["pool_yi"] = post["pool_yuan"] / 1e8

# ---------- 1. 平稳性（ADF） ----------
adf = {}
for name in ("logw1", "sale_yi", "pool_yi"):
    x = post[name].dropna()
    stat, p, *_ = adfuller(x, autolag="AIC")
    adf[name] = {"adf_stat": round(float(stat), 4), "p": round(float(p), 4),
                 "stationary": bool(p < 0.05)}
    print(f"[ADF] {name}: stat={stat:.3f} p={p:.4f} {'平稳' if p < 0.05 else '非平稳'}")

# 非平稳则一阶差分（检验差分后）
diff_ok = {}
for name in ("logw1", "sale_yi", "pool_yi"):
    if not adf[name]["stationary"]:
        d = post[name].diff().dropna()
        stat, p, *_ = adfuller(d, autolag="AIC")
        diff_ok[name] = {"adf_stat": round(float(stat), 4), "p": round(float(p), 4),
                         "stationary_diff": bool(p < 0.05)}
        print(f"[ADF-diff] {name}: p={p:.4f} {'平稳' if p < 0.05 else '仍非平稳'}")

# Granger 用一阶差分序列（若原序列非平稳）；平稳则用原序列
def series_for(name):
    return post[name].diff().dropna().values if not adf[name]["stationary"] else post[name].values

g_names = ["logw1", "sale_yi", "pool_yi"]

# ---------- 2. Granger 因果（滞后 1-3，双变量） ----------
def granger(x, y, maxlag=3):
    """x 是否 Granger 引起 y：回归 y_t ~ y_{t-1..k} + x_{t-1..k}，F 检验 x 滞后项联合显著"""
    xx, yy = series_for(x), series_for(y)
    m = min(len(xx), len(yy))
    xx, yy = xx[-m:], yy[-m:]
    res = {}
    for k in range(1, maxlag + 1):
        X = []
        for t in range(k, m):
            row = list(yy[t - k:t][::-1]) + list(xx[t - k:t][::-1])
            X.append(row)
        X = np.array(X)
        Y = yy[k:]
        Xc = sm.add_constant(X)
        ols_full = sm.OLS(Y, Xc).fit()
        rss_full = ols_full.ssr
        Xr = sm.add_constant(X[:, :k])  # 只保留 Y 自身滞后
        ols_reduced = sm.OLS(Y, Xr).fit()
        rss_reduced = ols_reduced.ssr
        df1, df2 = k, len(Y) - Xc.shape[1]
        f = ((rss_reduced - rss_full) / df1) / (rss_full / df2)
        from scipy import stats as st
        p = float(1 - st.f.cdf(f, df1, df2))
        res[k] = {"F": round(float(f), 4), "p": round(p, 4), "sig": bool(p < 0.05)}
    return res

pairs = [("pool_yi", "sale_yi"), ("sale_yi", "pool_yi"),
         ("pool_yi", "logw1"), ("sale_yi", "logw1"),
         ("logw1", "sale_yi")]
granger_res = {}
for x, y in pairs:
    granger_res[f"{x}→{y}"] = granger(x, y)
    sigs = [v["sig"] for v in granger_res[f"{x}→{y}"].values()]
    print(f"[Granger] {x} → {y}: 滞后1-3 p = " +
          ", ".join(str(granger_res[f"{x}→{y}"][k]["p"]) for k in (1, 2, 3)) +
          f" → {'存在' if any(sigs) else '无'}")

# ---------- 3. 含/不含销量两版注数模型 ----------
# 注数模型：logw1 ~ pool（+sale 对比）。差分口径（若非平稳）
X1 = sm.add_constant(post["pool_yi"].diff().dropna())
Y = post["logw1"].diff().dropna().reindex(X1.index).dropna()
X1 = X1.reindex(Y.index)
m1 = sm.OLS(Y, X1).fit()  # 不含销量
X2 = sm.add_constant(pd.DataFrame({"pool": post["pool_yi"].diff(), "sale": post["sale_yi"].diff()}).dropna())
Y2 = post["logw1"].diff().dropna().reindex(X2.index).dropna()
X2 = X2.reindex(Y2.index)
m2 = sm.OLS(Y2, X2).fit()  # 含销量

def model_rep(m, names):
    return {names[i]: {"coef": round(float(m.params.iloc[i]), 5), "p": round(float(m.pvalues.iloc[i]), 4)}
            for i in range(len(names))}

model_no_sale = {"r2": round(float(m1.rsquared), 4), **model_rep(m1, ["const", "pool"])}
model_with_sale = {"r2": round(float(m2.rsquared), 4), **model_rep(m2, ["const", "pool", "sale"])}
pool_coef_change = None
if model_no_sale.get("pool") and model_with_sale.get("pool"):
    pool_coef_change = round(float(m2.params.iloc[1] - m1.params.iloc[1]), 5)

# ---------- 判定 ----------
sale_inner = any(granger_res.get("pool_yi→sale_yi", {}).get(k, {}).get("sig") for k in (1, 2, 3))
sale_drives_w1 = any(granger_res.get("sale_yi→logw1", {}).get(k, {}).get("sig") for k in (1, 2, 3))
pool_drives_w1 = any(granger_res.get("pool_yi→logw1", {}).get(k, {}).get("sig") for k in (1, 2, 3))
coef_stable = pool_coef_change is not None and abs(pool_coef_change) < 0.02

verdict = {
    "sales_is_endogenous": bool(sale_inner and sale_drives_w1),
    "pool_drives_sales": bool(sale_inner),
    "sales_drives_w1": bool(sale_drives_w1),
    "pool_drives_w1": bool(pool_drives_w1),
    "pool_coef_stable_without_sale": bool(coef_stable),
    "summary": (
        f"奖池→销量 {sale_inner}；销量→注数 {sale_drives_w1}；奖池→注数 {pool_drives_w1}；"
        f"含销量后 pool 系数变化 {pool_coef_change}（<0.02 视为稳定）"
    ),
}

rep = {
    "n_obs": n, "window": f"{post['date'].iloc[0].date()} ~ {post['date'].iloc[-1].date()}",
    "adf": adf, "adf_diff": diff_ok,
    "granger": granger_res,
    "model_no_sale": model_no_sale,
    "model_with_sale": model_with_sale,
    "pool_coef_change_with_sale": pool_coef_change,
    "verdict": verdict,
    "seed": SEED,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n[write] {os.path.basename(OUT)}")
print("[verdict]", verdict["summary"])
print("done")
