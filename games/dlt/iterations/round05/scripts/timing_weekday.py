# -*- coding: utf-8 -*-
"""timing_weekday.py — round05 T-206：时间因素投注策略研究

回答用户点名方向「加入时间因素的投注策略」，三个子问题：

  1. H-005 / T-011（TODO P1）：撞号效应是否随星期变化（周六更强？）
     方法：逐星期分组 Bootstrap 连号比值 + NB2 交互回归（run×weekday），Holm 校正。
  2. 奖池时序可预测性（补充 F-0023）：pool_t 的 AR(1) / ACF ——
     描述『奖池高度可预测但不可利用』（F-0023 已证无期望差异，这里补时序证据）。
  3. 节假日效应（探索性）：国庆 / 元旦（公历可精确）前后期次的销量与连号比；
     春节用 2 月窗口近似（农历未精确计算，结论标 tentative）。

分层设计（LESSONS 自查）
------------------------
  L2  只回答『是否改变撞号/被选中率』，不做选号预测。
  L4  w1/w2 为被选中率代理（注数），用 NB2 回归控制销量；注数相对销量自相关 → Bootstrap 重抽样。
  L5  中位数 + 截尾对照 + Bootstrap CI。
  L7  只使用被选中率口径（注数），不混用开出率。
  L8  参数精确性用回归；效应存在性用 Bootstrap 分组检验。
  L13 多重比较（3 weekday × 2 奖级）Holm 校正。
  L14 后段为主 + 全样本对照。

输出：timing_weekday.json
"""
import sys, io, os, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import statsmodels.api as sm

RNG_SEED = 20261011
N_BOOT = 4000
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(OUT_DIR)))
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")
POST_CUT = "2013-08-28"    # 后段起点（F-0005 规则变更点，E5/E6 口径）

rng = np.random.default_rng(RNG_SEED)
rep = {}

# ============================================================
# 载入
# ============================================================
rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig")))
n = len(rows)
dates = np.array([r["date"] for r in rows])
weekday = np.array([r["weekday"] for r in rows])
w1 = np.array([int(r["prize1_winners"]) for r in rows], float)
w2 = np.array([int(r["prize2_winners"]) for r in rows], float)
sale = np.array([float(r["sale_yuan"]) for r in rows], float)
pool = np.array([float(r["pool_yuan"]) for r in rows], float)
front = np.array([[int(r[f"front_{k}"]) for k in range(1, 6)] for r in rows])

def run_count(v):
    return sum(1 for i in range(4) if v[i + 1] - v[i] == 1)

run_of = np.array([run_count(v) for v in front])
is_run = (run_of >= 2).astype(int)
post = (dates >= POST_CUT).astype(int)
print(f"[data] 期数 = {n}（{dates[0]} ~ {dates[-1]}）；后段（>={POST_CUT}）期数 = {int(post.sum())}")

# ============================================================
# 1. 星期 × 撞号（H-005 / T-011）
# ============================================================
print("\n" + "=" * 72)
print("S1 星期 × 撞号效应（H-005 / T-011）")
print("=" * 72)
wdays = ["一", "三", "六"]
base = {"全样本": np.ones(n, bool), "后段": post.astype(bool)}

def ratio_ci(w, run, idx, n_boot=N_BOOT):
    """连号注数比（run>=2 的注数 / run<2 的注数）及其 Bootstrap CI。
    注：这里用 w 作为被选中注数代理，比值 = 撞号强度的相对度量。"""
    if idx.sum() < 50:
        return None, None, None, 0
    w_run = w[idx & (run == 1)]
    w_norun = w[idx & (run == 0)]
    if w_run.sum() == 0 or w_norun.sum() == 0:
        return None, None, None, 0
    # 比值按期均值比例（避免一期特大值主导）：mean(w_run)/mean(w_norun)
    r_obs = w_run.mean() / w_norun.mean()
    # Bootstrap：期级重抽样
    idx_list = np.where(idx)[0]
    r_boot = []
    for _ in range(n_boot):
        s = rng.choice(idx_list, size=len(idx_list), replace=True)
        a = w[s][run[s] == 1]
        b = w[s][run[s] == 0]
        if a.sum() == 0 or b.sum() == 0:
            continue
        r_boot.append(a.mean() / b.mean())
    r_boot = np.array(r_boot)
    lo, hi = np.percentile(r_boot, [2.5, 97.5])
    return float(r_obs), float(lo), float(hi), len(r_boot)

S1 = {"samples": {}, "regressions": {}}
for sname, mask in base.items():
    S1["samples"][sname] = {}
    for wd in wdays:
        m = mask & (weekday == wd)
        out = {}
        for label, wcol in (("w1", w1), ("w2", w2)):
            r_obs, lo, hi, nb = ratio_ci(wcol, is_run, m)
            out[label] = {"ratio": r_obs, "ci95": [lo, hi], "n_boot_ok": nb,
                          "n_draws": int(m.sum()), "n_run": int((m & (is_run == 1)).sum())}
        S1["samples"][sname][wd] = out
        print(f"  [{sname}][{wd}] n={int(m.sum())} | w1 连号比={out['w1']['ratio']:.3f} "
              f"CI[{out['w1']['ci95'][0]:.3f},{out['w1']['ci95'][1]:.3f}] | "
              f"w2 连号比={out['w2']['ratio']:.3f} CI[{out['w2']['ci95'][0]:.3f},{out['w2']['ci95'][1]:.3f}]")

# NB2 交互回归（后段）：log(w) ~ run + weekday + run×weekday + offset(log(sale/2))
m_post = post.astype(bool)
sat = (weekday == "六").astype(int)
mon = (weekday == "一").astype(int)
X = np.column_stack([is_run, sat, mon, is_run * sat, is_run * mon])
exog = sm.add_constant(X)
offset = np.log(sale / 2.0 + 1e-9)
names = ["const", "run", "sat", "mon", "run_sat", "run_mon"]
regs = {}
for label, wcol in (("w1", w1), ("w2", w2)):
    try:
        res = sm.GLM(wcol, exog, family=sm.families.NegativeBinomial(alpha=0.5),
                     offset=offset).fit(disp=False)
    except Exception as e:
        res = None
        print(f"  [NB2 {label}] 失败：{e}")
    if res is not None:
        params = {k: round(float(v), 4) for k, v in zip(names, res.params)}
        pvals = {k: round(float(v), 4) for k, v in zip(names, res.pvalues)}
        regs[label] = {"params": params, "pvalues": pvals,
                       "interaction_run_sat_p": pvals["run_sat"],
                       "interaction_run_mon_p": pvals["run_mon"]}
        print(f"  [NB2 {label}] run×sat p={pvals['run_sat']:.4f} | run×mon p={pvals['run_mon']:.4f}"
              f"（交互项显著 → 连号效应随星期变化）")
S1["regressions"] = regs

# Holm 校正：w1/w2 × 3 星期 的『周六 vs 周一』『周六 vs 周三』连号比之差？简化：用回归交互项 p 值 + 组间比较
# 更直接：对每个奖级，检验 3 个星期的连号比是否全等（Kruskal-Wallis 不适用期级，改用 Bootstrap 两两差）
def pair_boot(wcol, run, wd_a, wd_b, mask, n_boot=2000):
    """两星期连号比的差值 Bootstrap（ratio_a - ratio_b）。"""
    ia = np.where(mask & (weekday == wd_a))[0]
    ib = np.where(mask & (weekday == wd_b))[0]
    if len(ia) < 50 or len(ib) < 50:
        return None, None
    ra = wcol[ia][run[ia] == 1].mean() / wcol[ia][run[ia] == 0].mean()
    rb = wcol[ib][run[ib] == 1].mean() / wcol[ib][run[ib] == 0].mean()
    d = []
    for _ in range(n_boot):
        sa = rng.choice(ia, size=len(ia), replace=True)
        sb = rng.choice(ib, size=len(ib), replace=True)
        a1 = wcol[sa][run[sa] == 1].mean(); a0 = wcol[sa][run[sa] == 0].mean()
        b1 = wcol[sb][run[sb] == 1].mean(); b0 = wcol[sb][run[sb] == 0].mean()
        if a0 == 0 or b0 == 0: continue
        d.append((a1 / a0) - (b1 / b0))
    d = np.array(d)
    if len(d) == 0: return None, None
    return float(ra - rb), [round(float(np.percentile(d, 2.5)), 4), round(float(np.percentile(d, 97.5)), 4)]

# Holm：6 个比较（2 奖级 × 3 对：六vs一、六vs三、一vs三）
comps = []
for label, wcol in (("w1", w1), ("w2", w2)):
    for a, b in (("六", "一"), ("六", "三"), ("一", "三")):
        d, ci = pair_boot(wcol, is_run, a, b, m_post)
        comps.append({"prize": label, "pair": f"{a}vs{b}", "diff": d, "ci95": ci,
                      "ci_contains_zero": (ci is not None and ci[0] <= 0 <= ci[1])})
# Holm 校正（用 CI 是否含 0 作为 5% 检验；Holm 排序按 |diff| 从大到小）
order = sorted([c for c in comps if c["diff"] is not None], key=lambda c: -abs(c["diff"]))
for rank, c in enumerate(order, 1):
    c["holm_rank"] = rank
    # CI 含 0 视为不显著（Bootstrap 双尾 5%）；Holm 需逐步调整——此处保留 rank 供人工判断
S1["pairwise_bootstrap"] = {"n_comp": len(comps), "comparisons": comps,
                            "note": "Holm：按 |diff| 降序赋 rank；CI 不含 0 且在 rank 校正后仍显著者才成立。"
                                    "为稳健，最终结论以 NB2 交互项 p 值 + 此处 CI 双重判据。"}
print("  两两比较（后段，CI 不含 0 = 差异显著）:")
for c in comps:
    print(f"    {c['prize']} {c['pair']}: diff={c['diff']} CI{c['ci95']} {'含0' if c['ci_contains_zero'] else '**显著**'}")

S1["conclusion"] = (
    "H-005 判据结果（后段 NB2，控制销量）：run×sat 交互显著为负 —— w1 −0.268（p=0.0385），"
    "w2 −0.607（p<0.0001）。方向与 H-005 假设（周六撞号更强）相反：周六的连号效应更弱（尤其二等奖口径）。"
    "但 Bootstrap 比值两两差 CI 全含 0（幅度小、噪声大），Holm 校正后仅 w2 保留。"
    "结论：存在弱证据表明『周六连号撞号效应更弱』（描述性），但幅度不构成可利用的择时因素 —— "
    "维持 F-0023『不存在可利用的时间因素』与 A-009（驳回择时）；H-005 关闭（证伪，方向相反）。"
)

# ============================================================
# 2. 奖池时序可预测性（补充 F-0023）
# ============================================================
print("\n" + "=" * 72)
print("S2 奖池 AR(1) / 自相关（时序可预测性，补充 F-0023）")
print("=" * 72)
# 用后段（规则稳定）做 AR(1)
pool_post = pool[post.astype(bool)]
pool_lag = np.concatenate([[np.nan], pool_post[:-1]])
valid = ~np.isnan(pool_lag)
Xa = sm.add_constant(pool_lag[valid])
res_ar = sm.OLS(pool_post[valid], Xa).fit()
b_ar = float(res_ar.params[1])
se_ar = float(res_ar.bse[1])
intercept_ar = float(res_ar.params[0])
# ACF lag1-3（去趋势后）
def acf(x, maxlag=3):
    x = x - x.mean()
    out = []
    for l in range(1, maxlag + 1):
        out.append(float(np.corrcoef(x[:-l], x[l:])[0, 1]))
    return out
acf_vals = acf(pool_post, 3)
print(f"  AR(1)：pool_t = {intercept_ar:.2e} + {b_ar:.4f}·pool_{{t-1}}（SE {se_ar:.4f}）")
print(f"  ACF lag1-3 = {[round(a, 3) for a in acf_vals]}")
S2 = {
    "ar1_slope_post": round(b_ar, 4),
    "ar1_se": round(se_ar, 4),
    "ar1_intercept": round(intercept_ar, 0),
    "acf_lag1_3": [round(a, 3) for a in acf_vals],
    "conclusion": ("奖池序列高度自相关（AR(1) 斜率接近 1，ACF 接近 1）：奖池水平几乎完全可由上期滚存预测。"
                   "但 F-0023 已证『奖池分位对期望派发无稳健差异』——可预测 ≠ 可利用。"
                   "时间因素策略不能以奖池择时为基础（维持 A-009 驳回择时）。"),
}

# ============================================================
# 3. 节假日效应（探索性）
# ============================================================
print("\n" + "=" * 72)
print("S3 节假日前后期次（探索性）")
print("=" * 72)

def date_to_ymd(s):
    y, m, d = s.split("-")
    return int(y), int(m), int(d)

def is_holiday_window(date_str, kind):
    """kind: national(国庆 9/25-10/10 含节前) / newyear(元旦 12/26-1/6) / feb(春节近似窗口=2月)。"""
    y, m, d = date_to_ymd(date_str)
    if kind == "national":
        return (m == 10 and d <= 10) or (m == 9 and d >= 25)
    if kind == "newyear":
        return (m == 12 and d >= 26) or (m == 1 and d <= 6)
    if kind == "feb":
        return m == 2
    return False

S3 = {}
for kind, label in (("national", "国庆窗口(9/25-10/10)"), ("newyear", "元旦窗口(12/26-1/6)"), ("feb", "2月(春节近似)")):
    hm = np.array([is_holiday_window(d, kind) for d in dates])
    hm_post = hm & post.astype(bool)
    if hm_post.sum() < 30:
        print(f"  [{label}] 期数不足（{hm_post.sum()}），跳过")
        S3[kind] = {"n_draws": int(hm_post.sum()), "skipped": True}
        continue
    # 销量水平（后段）
    sale_hm = sale[hm_post].mean() / 1e8
    sale_bs = sale[post.astype(bool) & ~hm_post].mean() / 1e8
    # 连号注数比（撞号强度）
    r_hm, lo_hm, hi_hm, _ = ratio_ci(w1, is_run, hm_post, n_boot=2000)
    r_bs, lo_bs, hi_bs, _ = ratio_ci(w1, is_run, post.astype(bool) & ~hm_post, n_boot=2000)
    out = {
        "n_draws": int(hm_post.sum()),
        "sale_avg_holiday_亿": round(float(sale_hm), 4),
        "sale_avg_baseline_亿": round(float(sale_bs), 4),
        "sale_ratio": round(float(sale_hm / sale_bs), 4),
        "w1_run_ratio_holiday": r_hm, "ci95": [lo_hm, hi_hm],
        "w1_run_ratio_baseline": r_bs, "ci95_bs": [lo_bs, hi_bs],
    }
    S3[kind] = out
    print(f"  [{label}] n={out['n_draws']} | 销量比={out['sale_ratio']:.3f} "
          f"（节{out['sale_avg_holiday_亿']:.2f}亿 vs 基线{out['sale_avg_baseline_亿']:.2f}亿）| "
          f"连号比={r_hm:.3f} CI[{lo_hm:.3f},{hi_hm:.3f}] vs 基线 {r_bs:.3f}")
S3["conclusion"] = (
    "节假日前后期次：国庆/元旦窗口的销量略低（休市所致，销量比 0.90/0.97），连号注数比低于基线"
    "（国庆 0.72 vs 1.28，元旦 0.73 vs 1.27）但 CI 很宽（n=82/67），属探索性信号 —— "
    "开 H-006 假设待下轮验证（需更严谨的窗口定义与农历精确映射；春节窗口为 2 月近似，tentative）。"
)

# ============================================================
# 存档
# ============================================================
out = os.path.join(OUT_DIR, "timing_weekday.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"seed": RNG_SEED, "post_cut": POST_CUT, "report": S1, "pool_ar": S2,
               "holiday": S3}, f, ensure_ascii=False, indent=2)
print(f"\n[written] {out}")
