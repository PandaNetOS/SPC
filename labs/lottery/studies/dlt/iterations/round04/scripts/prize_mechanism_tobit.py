# -*- coding: utf-8 -*-
"""prize_mechanism_tobit.py — T-102 (round04)

问题（Q-007）：是否存在"奖池累积期"这类单期期望回报（每元销售额对应的实际派发额）
高于平均的投注时机？若存在，优势多少、适用条件是什么、在现行 E6 规则下是否仍成立？

分层
----
S1 可观测层  —— 用一/二等奖注数反推投注量并与 sale_yuan 交叉验证；计算
                r_t = (w1*amt1 + w2*amt2)/sale_yuan 与 er_t = (p1*amt1+p2*amt2)/2。
S2 删失回归层 —— prize1_amount_yuan 右删失（封顶值按 epoch 实测众数确定），
                Tobit MLE 拟合 log(amt1) ~ 期初奖池 + log(投注量) + 星期。
S3 高期望期检验 —— 期初奖池分位分组比较 r_t / er_t（Bootstrap B=2000，
                同时报均值/中位数/10%截尾），并做销量摊薄、相对奖池、独立口径复核。
S4 结论。

纪律：pool_prev = pool_yuan.shift(1)（L6）；按 rules_epoch 分段（L9）；
      不直接 OLS（删失偏误）；重尾报稳健口径（L5）；不比较不同口径的锚点（L11）。
      不做任何中奖概率断言 —— 单注一等奖概率恒为 1/21,425,712。

RNG_SEED = 20261011（写死，独立可复现）。结果写 prize_mechanism_tobit.json
(ensure_ascii=False, indent=2)。
"""
import os, sys, json
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm

RNG_SEED = 20261011
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))  # 5 级上溯
DATA = os.path.join(ROOT, "games", "dlt", "data", "raw", "dlt_full_2933.csv")
OUT = os.path.join(HERE, "prize_mechanism_tobit.json")

P1 = 1.0 / 21425712.0
P2 = 20.0 / 21425712.0
EPOCHS = [("E0", 7001, 9120), ("E1", 9121, 13144), ("E2", 13145, 14051),
          ("E3", 14052, 19018), ("E4", 19019, 23000), ("E5", 23001, 26013),
          ("E6", 26014, 10 ** 9)]

def epoch_of(dn):
    v = int(dn)
    for name, lo, hi in EPOCHS:
        if lo <= v <= hi:
            return name
    return "?"

def cap_for(e, pool_prev):
    """封顶值：数据实测众数。E0=5e6；E1 按 2009-10-17 规则 pool_prev>=1亿 时 1e7；E2-E6=1e7。"""
    if e == "E0":
        return 5.0e6
    if e == "E1":
        return 5.0e6 if pool_prev < 1.0e8 else 1.0e7
    return 1.0e7

# ---------------- 数据 ----------------
df = pd.read_csv(DATA, encoding="utf-8-sig", dtype={"draw_num": str})
df = df.sort_values("draw_num").reset_index(drop=True)
for c in ["pool_yuan", "sale_yuan", "prize1_winners", "prize1_amount_yuan",
          "prize2_winners", "prize2_amount_yuan"]:
    df[c] = pd.to_numeric(df[c])
df["epoch"] = df["draw_num"].map(epoch_of)
df["pool_prev"] = df["pool_yuan"].shift(1)                 # L6：期初奖池 = 上期期末奖池
df["r_t"] = (df.prize1_winners * df.prize1_amount_yuan
             + df.prize2_winners * df.prize2_amount_yuan) / df.sale_yuan
df["er_t"] = (P1 * df.prize1_amount_yuan + P2 * df.prize2_amount_yuan) / 2.0
df["n1"] = df.prize1_winners / P1
df["n2"] = df.prize2_winners / P2
df["price"] = df.sale_yuan / df.n2
d = df[np.isfinite(df.pool_prev)].copy()

def q(a, p):
    a = np.asarray([x for x in a if np.isfinite(x)])
    return float(np.quantile(a, p)) if a.size else float("nan")

def mean(a):
    a = np.asarray([x for x in a if np.isfinite(x)])
    return float(a.mean()) if a.size else float("nan")

def trim_mean(a, p=0.10):
    a = np.sort(np.asarray([x for x in a if np.isfinite(x)]))
    k = int(len(a) * p)
    b = a[k:len(a) - k] if len(a) - k > k else a
    return float(b.mean()) if b.size else float("nan")

rng = np.random.default_rng(RNG_SEED)
def boot_diff(A, C, stat, B=2000):
    A = np.asarray([x for x in A if np.isfinite(x)]); C = np.asarray([x for x in C if np.isfinite(x)])
    dd = np.empty(B)
    for b in range(B):
        ra = A[rng.integers(0, len(A), len(A))]; rc = C[rng.integers(0, len(C), len(C))]
        dd[b] = stat(rc) - stat(ra)
    p = min(1.0, 2 * min((dd <= 0).mean(), (dd >= 0).mean()))
    return {"pt": float(stat(C) - stat(A)), "ci": [float(np.quantile(dd, .025)), float(np.quantile(dd, .975))], "p": float(p)}

def holm(tests):
    s = sorted(tests, key=lambda t: t["p"]); mx = 0.0; out = []
    for i, t in enumerate(s):
        adj = min(1.0, t["p"] * (len(s) - i)); mx = max(mx, adj)
        out.append({"id": t["id"], "p": round(t["p"], 4), "holm": round(mx, 4)})
    return out

def R(x, n=4):
    return None if x is None or not np.isfinite(x) else round(float(x), n)
def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (float, np.floating)): return None if not np.isfinite(o) else float(o)
    return o

rep = {"task": "T-102", "question": "Q-007", "seed": RNG_SEED,
       "data": {"path": "labs/lottery/studies/dlt/data/raw/dlt_full_2933.csv", "n_draws": int(len(df)),
                "n_with_lagged_pool": int(len(d)),
                "draw_range": [df.draw_num.iloc[0], df.draw_num.iloc[-1]],
                "date_range": [df.date.iloc[0], df.date.iloc[-1]]},
       "conventions": {"p1": "1/21425712", "p2": "20/21425712",
                       "pool_prev": "pool_yuan.shift(1) —— 期初奖池（L6）",
                       "r_t": "(w1*amt1+w2*amt2)/sale_yuan（总返奖率下界）",
                       "er_t": "(p1*amt1+p2*amt2)/2（每 1 元基本投注、仅一/二等奖的期望派发）"}}

# ---------------- S1 ----------------
def price_stats(sub):
    p1 = sub[sub.n1 > 0]; v1 = (p1.sale_yuan / p1.n1).values; v2 = sub.price.values
    return {"n": int(len(sub)), "price_n1_med": R(q(v1, .5), 3), "price_n1_p10": R(q(v1, .1), 3),
            "price_n1_p90": R(q(v1, .9), 3), "price_n2_med": R(q(v2, .5), 3),
            "price_n2_p10": R(q(v2, .1), 3), "price_n2_p90": R(q(v2, .9), 3),
            "agg_price_n1": R(sub.sale_yuan.sum() / sub.n1.sum(), 3),
            "agg_price_n2": R(sub.sale_yuan.sum() / sub.n2.sum(), 3),
            "frac_n2_in_2_3": R(float(((v2 >= 2) & (v2 <= 3)).mean()), 3)}
S1 = {"ticket_reconstruction": {"note": "n1=w1/p1, n2=w2/p2；每注均价=sale/n 应落在 [2,3] 元。",
                                "full_sample": price_stats(df),
                                "by_epoch": {e: price_stats(df[df.epoch == e]) for e, _, _ in EPOCHS}},
      "payout_ratio_r_t": {"by_epoch": {e: {"n": int((df.epoch == e).sum()), "mean": R(mean(df[df.epoch == e].r_t)),
          "median": R(q(df[df.epoch == e].r_t, .5)), "trim10": R(trim_mean(df[df.epoch == e].r_t)),
          "p90": R(q(df[df.epoch == e].r_t, .9))} for e, _, _ in EPOCHS}},
      "expected_return_er_t": {"by_epoch": {e: {"n": int((df.epoch == e).sum()), "mean": R(mean(df[df.epoch == e].er_t)),
          "median": R(q(df[df.epoch == e].er_t, .5)), "trim10": R(trim_mean(df[df.epoch == e].er_t))} for e, _, _ in EPOCHS}}}
rep["S1"] = S1

# ---------------- S2 Tobit ----------------
def tobit_nll(par, X, y, logcap, cens):
    k = X.shape[1]; beta = par[:k]; sig = np.exp(par[k])
    xb = X @ beta
    ll = np.where(cens, np.log(np.maximum(norm.cdf((xb - logcap) / sig), 1e-300)),
                  -par[k] - 0.5 * np.log(2 * np.pi) - 0.5 * ((y - xb) / sig) ** 2)
    return -ll.sum()

def tobit_fit(Xraw, y, caps, cens, cont):
    Xraw = np.asarray(Xraw, float); y = np.asarray(y, float); caps = np.asarray(caps, float); cens = np.asarray(cens, bool)
    mu = np.zeros(Xraw.shape[1]); sc = np.ones(Xraw.shape[1])
    for j in cont:
        mu[j] = Xraw[:, j].mean(); sc[j] = Xraw[:, j].std() or 1.0
    X = Xraw.copy()
    for j in cont:
        X[:, j] = (X[:, j] - mu[j]) / sc[j]
    k = X.shape[1]; logcap = np.log(caps)
    # 起点：删失当未删失的 OLS
    A = np.column_stack([X, np.ones(len(X))]); bb, *_ = np.linalg.lstsq(A, y, rcond=None)
    p0 = np.concatenate([bb[:k], [np.log(max(np.std(y - X @ bb[:k]), 1e-3))]])
    res = minimize(tobit_nll, p0, args=(X, y, logcap, cens), method="Nelder-Mead",
                   options={"maxiter": 20000, "xatol": 1e-9, "fatol": 1e-9})
    p = res.x
    # 数值 Hessian -> 观测信息 -> SE
    h = 1e-4; n = len(p); H = np.zeros((n, n)); f0 = tobit_nll(p, X, y, logcap, cens)
    for i in range(n):
        pi = p.copy(); pi[i] += h; mi = p.copy(); mi[i] -= h
        H[i, i] = (tobit_nll(pi, X, y, logcap, cens) - 2 * f0 + tobit_nll(mi, X, y, logcap, cens)) / h ** 2
        for j in range(i + 1, n):
            pp = p.copy(); pp[i] += h; pp[j] += h; pm = p.copy(); pm[i] += h; pm[j] -= h
            mp = p.copy(); mp[i] -= h; mp[j] += h; mm = p.copy(); mm[i] -= h; mm[j] -= h
            H[i, j] = H[j, i] = (tobit_nll(pp, X, y, logcap, cens) - tobit_nll(pm, X, y, logcap, cens)
                                 - tobit_nll(mp, X, y, logcap, cens) + tobit_nll(mm, X, y, logcap, cens)) / (4 * h * h)
    try:
        seS = np.sqrt(np.maximum(np.diag(np.linalg.inv(H)), 0))
    except np.linalg.LinAlgError:
        seS = np.full(n, np.nan)
    beta = np.array([p[j] / sc[j] if j in cont else p[j] for j in range(k)])
    se = np.array([seS[j] / sc[j] if j in cont else seS[j] for j in range(k)])
    return beta, se, float(np.exp(p[k])), float(res.fun)

S2 = {"model": {"response": "log(amt1)", "regressors": ["1", "pool_prev_yi", "log(n2)", "wed", "sat"],
                "estimator": "Tobit MLE (Nelder-Mead)；SE=数值 Hessian 观测信息"},
      "cap_scheme": {"E0": "5,000,000", "E1": "pool_prev<1亿?5,000,000:10,000,000", "E2-E6": "10,000,000",
                     "note": "封顶值取各 epoch 实测众数；高于封顶的观测（E0 至 2.056e7；E1 1.4-1.5e7 集中在 2011-05..07）按未删失处理。"},
      "by_epoch": {}}
for e, _, _ in EPOCHS:
    sub = d[(d.epoch == e) & (d.prize1_winners > 0)]
    if len(sub) < 30:
        S2["by_epoch"][e] = {"n": int(len(sub)), "note": "winner draws too few"}; continue
    caps = np.array([cap_for(e, pp) for pp in sub.pool_prev])
    y = np.log(sub.prize1_amount_yuan.values)
    cens = np.abs(sub.prize1_amount_yuan.values - caps) < 1.0   # 删失=恰在封顶值；高于封顶者按未删失处理
    Xf = np.column_stack([np.ones(len(sub)), sub.pool_prev.values / 1e8, np.log(sub.n2.values),
                          (sub.weekday.values == "三").astype(float), (sub.weekday.values == "六").astype(float)])
    Xu = np.column_stack([np.ones(len(sub)), sub.pool_prev.values / 1e8])
    def fmt(b, s, i):
        return {"coef": R(b[i], 6), "se": R(s[i], 6), "semi_elast_pct": R((np.exp(b[i]) - 1) * 100, 2),
                "ci95_pct": [R((np.exp(b[i] - 1.96 * s[i]) - 1) * 100, 2), R((np.exp(b[i] + 1.96 * s[i]) - 1) * 100, 2)],
                "t": R(b[i] / s[i], 2)}
    ent = {"n": int(len(sub)), "censored_frac": R(cens.mean(), 3), "cap_yuan": float(caps[0]),
           "n_above_cap": int((sub.prize1_amount_yuan.values > caps + 1).sum())}
    try:
        b, s, sig, nll = tobit_fit(Xu, y, caps, cens, [1]); ent["univariate_pool_only"] = {**fmt(b, s, 1), "sigma": R(sig)}
    except Exception as ex:
        ent["univariate_pool_only"] = {"error": str(ex)}
    try:
        b, s, sig, nll = tobit_fit(Xf, y, caps, cens, [1, 2])
        ent["controlled"] = {"pool": fmt(b, s, 1), "log_n2": fmt(b, s, 2), "b_wed": R(b[3]), "b_sat": R(b[4]),
                             "sigma": R(sig), "nll": R(nll, 2)}
    except Exception as ex:
        ent["controlled"] = {"error": str(ex)}
    S2["by_epoch"][e] = ent
S2["by_epoch"]["E0"]["reliability_note"] = "E0 结构歧义（5M/8M 双轨 + 超封顶值），Tobit 半弹性不可外推，仅存档。"
rep["S2"] = S2

# ---------------- S3 ----------------
def qgroups(sub, key):
    v = sub[key].values; cuts = [q(v, .25), q(v, .5), q(v, .75)]
    g = [[], [], [], []]
    for _, row in sub.iterrows():
        x = row[key]; g[0 if x < cuts[0] else 1 if x < cuts[1] else 2 if x < cuts[2] else 3].append(row)
    return cuts, g

def group_report(sub, key, scale):
    cuts, g = qgroups(sub, key); out = {"n": int(len(sub)), "cuts": [R(c / scale, 3) for c in cuts], "groups": [], "diff": {}}
    for i, a in enumerate(g):
        if not a: continue
        a = pd.DataFrame(a)
        out["groups"].append({"q": i + 1, "n": int(len(a)), "key_med": R(q(a[key].values, .5) / scale, 3),
                              "r_mean": R(mean(a.r_t)), "r_med": R(q(a.r_t, .5)), "r_trim": R(trim_mean(a.r_t)),
                              "er_mean": R(mean(a.er_t)), "er_med": R(q(a.er_t, .5)),
                              "sale_med_yi": R(q(a.sale_yuan, .5) / 1e8, 3), "price_med": R(q(a.price, .5), 3)})
    A = pd.DataFrame(g[0]); C = pd.DataFrame(g[3])
    for nm, stat in [("r_mean", mean), ("r_median", lambda x: q(x, .5)), ("r_trim10", trim_mean),
                     ("er_mean", mean), ("er_median", lambda x: q(x, .5))]:
        src = "r_t" if nm.startswith("r_") else "er_t"
        dd = boot_diff(A[src].values, C[src].values, stat)
        out["diff"][nm] = {"pt": R(dd["pt"]), "ci": [R(dd["ci"][0]), R(dd["ci"][1])], "p": R(dd["p"])}
    return out

S3 = {"pool_prev_quantile_global": group_report(d, "pool_prev", 1e8),
      "pool_prev_quantile_by_epoch": {e: group_report(d[d.epoch == e], "pool_prev", 1e8)
                                      for e, _, _ in EPOCHS if (d.epoch == e).sum() >= 50},
      "E4_excluding_2019": group_report(d[(d.epoch == "E4") & (d.draw_num.astype(int) >= 20001)], "pool_prev", 1e8),
      "sales_dilution": {"definition": "OLS log(sale_yuan) ~ a + b*pool_prev(亿)"}}
for e, _, _ in EPOCHS:
    sub = d[d.epoch == e]; x = sub.pool_prev.values / 1e8; yv = np.log(sub.sale_yuan.values)
    X = np.column_stack([np.ones(len(x)), x]); bb, *_ = np.linalg.lstsq(X, yv, rcond=None)
    r = yv - X @ bb; se = np.sqrt((r @ r) / (len(x) - 2) / ((x - x.mean()) @ (x - x.mean())))
    S3["sales_dilution"][e] = {"b_pct_per_yi": R(bb[1] * 100, 3), "se_pct": R(se * 100, 3), "t": R(bb[1] / se, 2)}
# 相对奖池（累积期）：pool_prev / 近 52 期滚动中位数
df["pool_rel"] = np.nan
pp = df.pool_prev.values
for i in range(len(df)):
    w = pp[max(0, i - 52):i]; w = w[np.isfinite(w)]
    if np.isfinite(pp[i]):
        df.loc[i, "pool_rel"] = pp[i] / (np.median(w) if w.size else pp[i])
S3["relative_accumulation_by_epoch"] = {e: group_report(df[(df.epoch == e) & np.isfinite(df.pool_rel)], "pool_rel", 1.0)
                                         for e in ["E3", "E4", "E5", "E6"]}
# E6 固定奖加成（规则文本，解析情景）
T = 21425712
lo_cnt = {3: 195, 4: 3000, 5: 11100, 6: 127600, 7: 1287281}
amt_lo = {3: 5000, 4: 300, 5: 150, 6: 15, 7: 5}
amt_hi = {3: 6666, 4: 380, 5: 200, 6: 18, 7: 7}
def fixed_py(a): return sum(lo_cnt[k] * a[k] for k in lo_cnt) / T / 2.0
e6 = d[d.epoch == "E6"]; hi = e6[e6.pool_prev >= 8e8]; lo = e6[e6.pool_prev < 8e8]
S3["E6_fixed_prize_boost"] = {
    "rules_epoch": "E6", "rule_text": "奖池>=8亿时三至七等奖单注奖金提升20%-40%（rules_history.md §3.3）",
    "fixed_tier_expected_per_yuan_lt8": R(fixed_py(amt_lo)), "fixed_tier_expected_per_yuan_ge8": R(fixed_py(amt_hi)),
    "boost_delta_per_yuan": R(fixed_py(amt_hi) - fixed_py(amt_lo)),
    "pool_prev_lt8": {"n": int(len(lo)), "er_mean": R(mean(lo.er_t)), "fixed": R(fixed_py(amt_lo)),
                      "total_mean": R(mean(lo.er_t) + fixed_py(amt_lo))},
    "pool_prev_ge8": {"n": int(len(hi)), "er_mean": R(mean(hi.er_t)), "fixed": R(fixed_py(amt_hi)),
                      "total_mean": R(mean(hi.er_t) + fixed_py(amt_hi))},
    "frac_draws_pool_prev_ge8": R(len(hi) / len(e6), 3),
    "pool_prev_range_yi": [R(e6.pool_prev.min() / 1e8, 3), R(e6.pool_prev.max() / 1e8, 3)],
    "total_gap_per_yuan": R((mean(hi.er_t) + fixed_py(amt_hi)) - (mean(lo.er_t) + fixed_py(amt_lo))),
    "caveat": "解析推算，非观测（L10）：数据集缺三至七等奖派发额，仅确认必要条件。"}
# 独立口径复核：按注数（n2）归一化
cuts, g = qgroups(d, "pool_prev")
A = pd.DataFrame(g[0]); C = pd.DataFrame(g[3])
rb = lambda a: (a.prize1_winners * a.prize1_amount_yuan + a.prize2_winners * a.prize2_amount_yuan) / a.n2
dd = boot_diff(rb(A).values, rb(C).values, mean)
S3["cross_validation"] = {"definition": "r_t^bet=(w1*amt1+w2*amt2)/n2 对比 r_t（每元）",
    "independence_caveat": "n2=w2/p2 含 w2，与分子二等奖项同源，不是独立证据（L12）",
    "global": {"cuts": [R(c / 1e8, 2) for c in cuts], "q1_mean": R(mean(rb(A))), "q4_mean": R(mean(rb(C))),
               "diff": {"pt": R(dd["pt"]), "ci": [R(dd["ci"][0]), R(dd["ci"][1])], "p": R(dd["p"])}}}
# 确认性主检验族（E1-E6）
fam = []
for e, _, _ in EPOCHS:
    sub = d[d.epoch == e]
    if len(sub) < 50 or e == "E0": continue
    _, g = qgroups(sub, "pool_prev"); A = pd.DataFrame(g[0]); C = pd.DataFrame(g[3])
    dd = boot_diff(A.er_t.values, C.er_t.values, mean)
    fam.append({"epoch": e, "delta_er_mean": R(dd["pt"]), "ci": [R(dd["ci"][0]), R(dd["ci"][1])], "p": R(dd["p"])})
S3["primary_family"] = {"description": "E1-E6：pool_prev 最高 vs 最低分位对 mean er_t 的效应，B=2000，Holm 校正。",
                        "tests": fam, "holm": holm([{"id": f["epoch"], "p": f["p"]} for f in fam])}
S3["multiplicity_disclosure"] = {"outcomes": ["r_t", "er_t", "per-bet payout"],
    "robust_estimators": ["mean", "median", "10% trim"], "treatment_cuts": ["pool_prev 分位(全局/分段)", "E4 剔 2019", "相对奖池", "连号 streak"],
    "correction": "确认性主检验族固定为 E1-E6 的 6 个 within-epoch er_t 检验并做 Holm；其余为探索性。"}
rep["S3"] = S3

# ---------------- S4 ----------------
e6max = float((e6.prize1_winners * e6.prize1_amount_yuan).max())
rep["S4"] = {"on_observable_tier12_existence": False,
    "cap_trigger_E6": {"cap_total_yuan": 1e8, "max_w1_times_amt1_yuan": R(e6max, 2),
                       "n_triggered": int(((e6.prize1_winners * e6.prize1_amount_yuan) >= 1e8).sum()),
                       "note": "E6 一/二等奖单期总额 1 亿封顶从未触发（复核 F-0016）。"},
    "observable_evidence": "within-epoch pool 分位对 er_t：E3(n=735) Δ=+0.005 不显著；E4 剔 2019 Δ=+0.002 不显著；E6 Δ=+0.017 p=0.27。E4 全样本 +0.173、全局 +0.090 由 2019 一次性奖池排空与 epoch 组成驱动。",
    "r_t_vs_er_t": "E4 剔 2019 后 r_t 仍升而 er_t 不升 → r_t 上升是每注均价（追加占比）组成效应，非每注期望上升（L12）。",
    "relative_accumulation": "pool_prev/近52期中位数 分组：E4 Δer=-0.074（负）；E3 ≈0；E5 +0.026 微弱；E6 不显著。『累积期』无稳健正效应。",
    "E6_verdict": "pool_prev 被钉在 6.93-8.75 亿（中位 7.91），浮动奖无可测择时效应。唯一机制候选是『奖池>=8亿→固定奖 +20-40%』：解析 +0.095 元/元（0.523→0.636），36.3% 期数满足必要条件，但无法用本数据集核验（L10）。",
    "recommendation": "暂不新增择时规则。若做，唯一有机制支撑的候选是 E6 下 pool_prev>=8亿（固定奖加成），但须先用三至七等奖实发数据核验，且 E6 仅 102 期、功效不足。"}
rep["caveats"] = [
    "prize1_amount_yuan 非干净右删失：存在超封顶观测（E0 至 2.056e7；E1 1.4-1.5e7 集中在 2011-05..07，疑似派奖期），按未删失处理，Tobit 斜率不可全域外推。",
    "E6 一/二等奖单期总额 1 亿封顶从未触发（最大 %.4f 亿）；真正截断的是单注 1000 万封顶。" % (e6max / 1e8),
    "r_t 与 er_t 不独立：高奖池 E4 期的 r_t 因每注均价更低而被抬高（追加占比下降），er_t 才是单注基本投注的正确每元期望口径。",
    "n2 反推注数在 E0（1.984）、E1（1.814）低于可行下界 2 元，E2-E6 为 2.25-2.41 → 数据一致性异常，未修正。",
    "E2 仅 60 期、E6 仅 102 期，功效低；E0 奖金结构最混乱，Tobit 以 E4/E5 最稳。",
    "E6 固定奖加成采用规则文本金额，无三至七等奖实发数据 → 解析情景（L10），非已发生事件。",
    "不做任何中奖概率断言：单注一等奖概率恒为 1/21,425,712；结论仅关乎中奖条件下的派发额。"]

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(clean(rep), f, ensure_ascii=False, indent=2)
print("[written]", OUT)
print("S2 E4/E5/E6 pool semi-elasticity:",
      S2["by_epoch"]["E4"]["univariate_pool_only"]["semi_elast_pct"],
      S2["by_epoch"]["E5"]["univariate_pool_only"]["semi_elast_pct"],
      S2["by_epoch"]["E6"]["univariate_pool_only"]["semi_elast_pct"])
print("primary family:", S3["primary_family"]["holm"])
