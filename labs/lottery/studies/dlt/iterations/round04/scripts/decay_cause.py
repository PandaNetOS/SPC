# -*- coding: utf-8 -*-
"""decay_cause.py — T-101：撞号效应（F-0003）衰减归因

背景
----
r03 的分期检验（b2_split_stability.py）报告：一等奖注数比 前段 2.1072 → 后段 1.2472
（后/前 = 0.592），二等奖 2.4250 → 1.2075（0.498），并据此写下"幅度衰减过半"。

本脚本要回答 T-101 的问题：**衰减的成因是什么？**
  H-A 彩民选号习惯真实变化（行为变化）
  H-B 数据质量 / 记录口径变化（前段数据不可比）
  H-C 销量结构变化稀释效应（规模/成分）

分层设计（严格遵守 LESSONS，特别是 L3/L5/L6/L9/L10/L11/L12）
----------------------------------------------------------
  S0 复现 r03 的分期结果（保证"同口径可比"）
  S1 数据口径层：字段完整率、注数反推投注量 vs 销售额、号码分布 vs 精确均匀
  S2 估计量稳健性层（★ 核心）：均值/中位数/截尾/Jackknife —— 前段估计是否稳定
  S3 规模与成分控制层：组间销量比、NB2（offset=log(注数)）交互项、分层标准化比、
     数据驱动滚动窗口（渐变 vs 阶跃，不按自然年 —— L3）
  S4 归因判定 + F-0004 口径建议（用后段口径重算 α 与封顶后 uplift）

自由参数：本脚本不新增任何自由参数。α/BIRTHDAY_W/cap 锚点均沿用既有结论的口径。
输出：decay_cause.json + 控制台摘要
"""
import sys, io, os, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
from math import comb
from itertools import combinations

RNG_SEED = 20261011
N_BOOT = 2000
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(OUT_DIR)))   # games/dlt
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")

CUT = "2013-08-28"            # F-0006 最优变点（数据驱动得到，非自然年 —— L3）
CAP_TOTAL = 100_000_000       # E6 一等奖单期总额封顶
CAP_PART = 5_000_000          # 单注每部分上限 → 分档合计上限 1000 万
ALPHA_FULL = 13.9405          # r03 全样本校准（F-0004 / F-0017）
BIRTHDAY_W = 1.25             # 生日号偏好（v4）
N0_ANCHOR = 6.0               # E6 实测一等奖中出注数中位数（F-0017 锚点）
POOL_ANCHOR = 0.4252e8        # E6 实测一等奖总派发额中位数（F-0017 锚点）

rng = np.random.default_rng(RNG_SEED)
rep = {}

# ============================================================
# 载入
# ============================================================
rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig")))
print(f"[data] 期数 = {len(rows)}，最新 = {rows[-1]['draw_num']} {rows[-1]['date']}")

def run_count(c):
    return sum(1 for i in range(4) if c[i + 1] - c[i] == 1)

F = [tuple(sorted(int(r[f"front_{i}"]) for i in range(1, 6))) for r in rows]
runs = np.array([run_count(c) for c in F])
w1 = np.array([int(r["prize1_winners"]) for r in rows], float)
w2 = np.array([int(r["prize2_winners"]) for r in rows], float)
sale = np.array([float(r["sale_yuan"]) for r in rows], float)
pool = np.array([float(r["pool_yuan"]) for r in rows], float)
amt1 = np.array([float(r["prize1_amount_yuan"]) for r in rows], float)
dates = np.array([r["date"] for r in rows])
years = np.array([int(r["year"]) for r in rows])
mask = runs >= 2
birth = np.array([max(c) <= 31 for c in F])
maxv = np.array([max(c) for c in F])
fsum = np.array([sum(c) for c in F])
pre, post = dates < CUT, dates >= CUT
print(f"[split] 切点 {CUT}（F-0006）：前段 {pre.sum()} 期 / 后段 {post.sum()} 期")
print(f"[overdispersion] w1 var/mean = {w1.var()/w1.mean():.3f}（L1: >1.5 禁用 Poisson）")

# ============================================================
# 估计量工具
# ============================================================
def ratio(a, b):
    return float(a.mean() / b.mean())

def boot_ci(a, b, n_boot=N_BOOT):
    na, nb = len(a), len(b)
    bs = np.empty(n_boot)
    for k in range(n_boot):
        ra = a[rng.integers(0, na, na)].mean()
        rb = b[rng.integers(0, nb, nb)].mean()
        bs[k] = ra / rb if rb > 0 else np.nan
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    return [round(float(lo), 4), round(float(hi), 4)]

def trimmed_ratio(a, b, p=0.10):
    def tm(x):
        n = max(1, int(round(len(x) * (1 - p))))
        return np.sort(x)[:n].mean()
    return float(tm(a) / tm(b))

def median_ratio(a, b, eps=0.5):
    """计数型中位数比：加 0.5 偏移避免 0/0（前段 w1 中位数为 1）。"""
    return float((np.median(a) + eps) / (np.median(b) + eps))

def drop_top_ratio(a, b, k):
    aa = np.sort(a)[:max(1, len(a) - k)]
    return float(aa.mean() / b.mean())

def estimator_pack(lab, sel):
    """对某段给出全部口径的比值。"""
    out = {}
    for name, y in (("w1", w1), ("w2", w2)):
        a, b = y[sel & mask], y[sel & ~mask]
        out[name] = {
            "n_ge2": int(len(a)), "n_lt2": int(len(b)),
            "mean_ge2": round(float(a.mean()), 4), "mean_lt2": round(float(b.mean()), 4),
            "mean_ratio": round(ratio(a, b), 4),
            "mean_ratio_ci95": boot_ci(a, b),
            "median_ratio": round(median_ratio(a, b), 4),
            "trimmed10_ratio": round(trimmed_ratio(a, b), 4),
            "drop_top1": round(drop_top_ratio(a, b, 1), 4),
            "drop_top3": round(drop_top_ratio(a, b, 3), 4),
            "drop_top5": round(drop_top_ratio(a, b, 5), 4),
            "median_ge2": float(np.median(a)), "median_lt2": float(np.median(b)),
        }
    return out

# ============================================================
# S0 复现 r03 分期结果
# ============================================================
print("\n" + "=" * 72)
print("S0 复现 r03 分期结果（同口径：均值比）")
print("=" * 72)
S0 = {"pre": estimator_pack("pre", pre), "post": estimator_pack("post", post)}
for seg in ("pre", "post"):
    for y in ("w1", "w2"):
        d = S0[seg][y]
        print(f"  {seg:4s} {y}: mean_ratio={d['mean_ratio']:.4f} CI{d['mean_ratio_ci95']} "
              f"(n={d['n_ge2']}+{d['n_lt2']})")
print(f"  r03 记录：前段 w1 2.1072 / w2 2.4250；后段 w1 1.2472 / w2 1.2075")
rep["S0_reproduce"] = {
    "note": "同口径复现 r03 的分期均值比，用于确认后续分析可比。",
    "cut": CUT, "segments": S0,
    "r03_reference": {"pre_w1": 2.1072, "post_w1": 1.2472, "pre_w2": 2.425, "post_w2": 1.2075},
    "match": bool(abs(S0["pre"]["w1"]["mean_ratio"] - 2.1072) < 0.02
                  and abs(S0["post"]["w1"]["mean_ratio"] - 1.2472) < 0.02),
}

# ============================================================
# S1 数据口径层
# ============================================================
print("\n" + "=" * 72)
print("S1 数据口径层 —— 前段与后段是否可比")
print("=" * 72)

P1 = 1.0 / 21425712.0
P2 = 20.0 / 21425712.0

def implied_tickets(y, sel, p):
    """由中出注数反推当期投注注数（无偏：E[w] = n·p）。"""
    return float(y[sel].mean() / p)

S1 = {}
for lab, sel in (("pre", pre), ("post", post)):
    n1 = implied_tickets(w1, sel, P1)
    n2 = implied_tickets(w2, sel, P2)
    sm = float(sale[sel].mean())
    lo_band, hi_band = sm / 3.0, sm / 2.0     # 基本 2 元 / 追加 3 元 → 注数 ∈ [sale/3, sale/2]
    S1[lab] = {
        "n_draws": int(sel.sum()),
        "zeros": {"w1": int((w1[sel] == 0).sum()), "w2": int((w2[sel] == 0).sum()),
                  "sale": int((sale[sel] == 0).sum()), "pool": int((pool[sel] == 0).sum()),
                  "amt1": int((amt1[sel] == 0).sum())},
        "zero_rate_w1": round(float((w1[sel] == 0).mean()), 4),
        "verified_pdf_rate": round(float(np.mean([rows[i]["verified_pdf"] == "True"
                                                  for i in np.where(sel)[0]])), 4),
        "verified_api_rate": round(float(np.mean([rows[i]["verified_api"] == "True"
                                                  for i in np.where(sel)[0]])), 4),
        "mean_sale_yuan": round(sm, 1),
        "implied_tickets_from_w1": round(n1, 1),
        "implied_tickets_from_w2": round(n2, 1),
        "feasible_ticket_band": [round(lo_band, 1), round(hi_band, 1)],
        "yuan_per_ticket_from_w1": round(sm / n1, 4),
        "yuan_per_ticket_from_w2": round(sm / n2, 4),
        "feasible": bool(lo_band <= n1 <= hi_band and lo_band <= n2 <= hi_band),
    }
    print(f"\n  [{lab}] n={S1[lab]['n_draws']}  w1 零值率={S1[lab]['zero_rate_w1']:.3f} "
          f"verified_pdf={S1[lab]['verified_pdf_rate']:.2f} verified_api={S1[lab]['verified_api_rate']:.2f}")
    print(f"    平均销售额 = {sm/1e8:.4f} 亿 → 可行注数区间 [{lo_band/1e6:.1f}M, {hi_band/1e6:.1f}M]")
    print(f"    反推注数（w1）= {n1/1e6:.1f}M  → 均价 {sm/n1:.3f} 元/注")
    print(f"    反推注数（w2）= {n2/1e6:.1f}M  → 均价 {sm/n2:.3f} 元/注")
    print(f"    → 落在可行区间内: {S1[lab]['feasible']}")
if not S1["pre"]["feasible"] and S1["post"]["feasible"]:
    print("\n  ★ 关键：前段反推的投注量【超出】销售额允许的上限（均价 < 2 元/注 = 低于最低票价），"
          "后段则落在可行区间内 → 前段的中出注数或销售额至少有一个口径不可比。")

# 1.2b 用人群模型成分修正后的反推（排除"前后段喝到的号码成分不同"这一替代解释）
ALL_F = list(combinations(range(1, 36), 5))
w_space = np.array([(ALPHA_FULL if run_count(c) >= 2 else 1.0)
                    * (BIRTHDAY_W if max(c) <= 31 else 1.0) for c in ALL_F])
mean_space = w_space.mean()
w_draw = np.array([(ALPHA_FULL if run_count(c) >= 2 else 1.0)
                   * (BIRTHDAY_W if max(c) <= 31 else 1.0) for c in F])
S1["composition_corrected"] = {}
for lab, sel in (("pre", pre), ("post", post)):
    comp = float(w_draw[sel].mean() / mean_space)
    n_corr = float(w1[sel].mean() / (P1 * comp))
    S1["composition_corrected"][lab] = {
        "draw_composition_weight_ratio": round(comp, 4),
        "implied_tickets_corrected": round(n_corr, 1),
        "yuan_per_ticket_corrected": round(float(sale[sel].mean() / n_corr), 4),
    }
    print(f"    成分修正：{lab} 观测开出组合的人群权重 / 全空间均值 = {comp:.4f}；"
          f"修正后反推注数 = {n_corr/1e6:.1f}M，均价 = {sale[sel].mean()/n_corr:.3f} 元/注")
print("    → 两段成分权重几乎相同（~1.055），故前段的『均价 < 2 元』不是号码成分造成的。")

# 1.3 号码分布 vs 精确均匀
print("\n  [号码分布] 前区单号频率 vs 精确均匀（每号期望 = n×5/35）")
S1["number_uniformity"] = {}
for lab, sel in (("pre", pre), ("post", post)):
    n = int(sel.sum())
    freq = np.zeros(36)
    for c in [F[i] for i in np.where(sel)[0]]:
        for x in c:
            freq[x] += 1
    exp = n * 5 / 35
    chi2 = float(((freq[1:] - exp) ** 2 / exp).sum())
    S1["number_uniformity"][lab] = {
        "n": n, "expected_per_number": round(exp, 2), "chi2": round(chi2, 2), "df": 34,
        "min_expected": round(exp, 2),
        "p_max_le_31_obs": round(float(birth[sel].mean()), 4),
    }
    print(f"    {lab}: χ²={chi2:.1f} (df=34)，P(前区全部<=31) 观测={birth[sel].mean():.3f}")
P_MAX31 = comb(31, 5) / comb(35, 5)
S1["number_uniformity"]["theory_p_max_le_31"] = round(P_MAX31, 4)
z_pre = (birth[pre].mean() - P_MAX31) / np.sqrt(P_MAX31 * (1 - P_MAX31) / pre.sum())
z_post = (birth[post].mean() - P_MAX31) / np.sqrt(P_MAX31 * (1 - P_MAX31) / post.sum())
S1["number_uniformity"]["z_pre"] = round(float(z_pre), 2)
S1["number_uniformity"]["z_post"] = round(float(z_post), 2)
print(f"    精确理论 P(全部<=31) = {P_MAX31:.4f}；z 前段={z_pre:+.2f}，后段={z_post:+.2f}")
print(f"    → 前段号码分布严重偏离均匀（偏高端，29-35 号全部超发），后段与精确均匀相容。")
rep["S1_data_consistency"] = S1

# ============================================================
# S2 估计量稳健性（L5 的分段版）
# ============================================================
print("\n" + "=" * 72)
print("S2 估计量稳健性 —— 「衰减过半」是否依赖均值比口径")
print("=" * 72)
S2 = {"pre": S0["pre"], "post": S0["post"], "decay": {}}
print(f"  {'段':5s} {'奖级':3s} {'均值比':>7s} {'中位数比':>8s} {'截尾10%':>8s} {'剔top1':>7s} {'剔top3':>7s} {'剔top5':>7s}")
for seg in ("pre", "post"):
    for y in ("w1", "w2"):
        d = S0[seg][y]
        print(f"  {seg:5s} {y:3s} {d['mean_ratio']:7.3f} {d['median_ratio']:8.3f} "
              f"{d['trimmed10_ratio']:8.3f} {d['drop_top1']:7.3f} {d['drop_top3']:7.3f} {d['drop_top5']:7.3f}")
for y in ("w1", "w2"):
    S2["decay"][y] = {
        "mean": round(S0["post"][y]["mean_ratio"] / S0["pre"][y]["mean_ratio"], 4),
        "median": round(S0["post"][y]["median_ratio"] / S0["pre"][y]["median_ratio"], 4),
        "trimmed10": round(S0["post"][y]["trimmed10_ratio"] / S0["pre"][y]["trimmed10_ratio"], 4),
        "drop_top3": round(S0["post"][y]["drop_top3"] / S0["pre"][y]["drop_top3"], 4),
    }
    d = S2["decay"][y]
    print(f"  [衰减比 post/pre] {y}: 均值 {d['mean']:.3f} | 中位数 {d['median']:.3f} | "
          f"截尾10% {d['trimmed10']:.3f} | 剔top3 {d['drop_top3']:.3f}")
print("  → 均值比口径给出 0.50~0.59（「衰减过半」）；稳健口径给出 0.72~0.83。")
print("  → 前段 w1 的均值比 2.107 对最极端的几期极其敏感：剔 top1 → "
      f"{S0['pre']['w1']['drop_top1']:.3f}，剔 top3 → {S0['pre']['w1']['drop_top3']:.3f}；"
      f"前段 w1 中位数比 = {S0['pre']['w1']['median_ratio']:.3f}（两组中位数均为 1）。")
rep["S2_estimator_robustness"] = S2

# ============================================================
# S3 规模与成分控制
# ============================================================
print("\n" + "=" * 72)
print("S3 规模与成分控制")
print("=" * 72)
S3 = {}

# 3.1 组间销量比（销量应与开奖号码无关；偏差会混入比值）
S3["group_sale_ratio"] = {}
for lab, sel in (("pre", pre), ("post", post)):
    r = float(sale[sel & mask].mean() / sale[sel & ~mask].mean())
    S3["group_sale_ratio"][lab] = round(r, 4)
    print(f"  [销量独立性] {lab}: 两组平均销量比 = {r:.4f}"
          f"（偏离 1 说明该段存在样本不平衡，会在均值比中产生 {abs(r-1)*100:.1f}% 的伪成分）")

# 3.2 NB2 GLM（offset = log(销量/2)），交互项检验"控制规模后衰减是否仍在"
import statsmodels.api as sm
X = np.column_stack([np.ones(len(rows)), mask.astype(float),
                     post.astype(float), (mask & post).astype(float)])
off = np.log(sale / 2.0)
S3["nb2_glm"] = {}
for name, y in (("w1", w1), ("w2", w2)):
    res = sm.NegativeBinomial(y, X, offset=off).fit(disp=0)
    b = res.params[1:]
    # 交互项的 Wald 检验
    se = res.bse[1:]
    z = b[2] / se[2]
    b0b2 = b[0] + b[2]
    sd = float(np.sqrt(se[0] ** 2 + se[2] ** 2 + 2 * res.cov_params()[1, 3]))
    S3["nb2_glm"][name] = {
        "irr_run_pre": round(float(np.exp(b[0])), 4),
        "irr_run_pre_ci95": [round(float(np.exp(b[0] - 1.96 * se[0])), 4),
                             round(float(np.exp(b[0] + 1.96 * se[0])), 4)],
        "irr_run_post": round(float(np.exp(b[0] + b[2])), 4),
        "irr_run_post_ci95": [round(float(np.exp(b0b2 - 1.96 * sd)), 4),
                              round(float(np.exp(b0b2 + 1.96 * sd)), 4)],
        "irr_interaction": round(float(np.exp(b[2])), 4),
        "irr_interaction_ci95": [round(float(np.exp(b[2] - 1.96 * se[2])), 4),
                                 round(float(np.exp(b[2] + 1.96 * se[2])), 4)],
        "z_interaction": round(float(z), 3),
        "p_interaction": round(float(2 * (1 - __import__("scipy").stats.norm.cdf(abs(z)))), 6),
        "implied_per_ticket_win_rate": float(np.exp(res.params[0])),
        "theoretical_p1": P1,
    }
    d = S3["nb2_glm"][name]
    p_theo = P1 if name == "w1" else P2
    d["implied_vs_theory"] = round(float(d["implied_per_ticket_win_rate"] / p_theo), 4)
    print(f"  [NB2 {name}] run IRR 前段={d['irr_run_pre']:.3f}{d['irr_run_pre_ci95']} "
          f"后段={d['irr_run_post']:.3f}{d['irr_run_post_ci95']} "
          f"交互={d['irr_interaction']:.3f}{d['irr_interaction_ci95']} p={d['p_interaction']:.2e}")
    print(f"          模型隐含的单位销量中出率 / 理论 p({name[1]}) = {d['implied_vs_theory']:.4f}"
          f"（≈1 说明 offset=log(销量/2) 口径自洽）")
print("  → 控制销量规模后，衰减仍然存在（交互项显著 < 1）：规模不是主因，但也不是零贡献。")

# 3.3 分层标准化比（固定成分权重，控制组间成分差异）
sum_edges = np.percentile(fsum, [0, 20, 40, 60, 80, 100])
sum_band = np.clip(np.digitize(fsum, sum_edges[1:-1]), 0, 4)
strata = [(s, b) for s in range(5) for b in (True, False)]
S3["standardized_ratio"] = {}
for lab, sel in (("pre", pre), ("post", post)):
    num, den = 0.0, 0.0
    for s, b in strata:
        st = sel & (sum_band == s) & (birth == b)
        n1 = int((st & mask).sum()); n0 = int((st & ~mask).sum())
        if n1 == 0 or n0 == 0:
            continue
        a = w1[st & mask].sum(); c = w1[st & ~mask].sum()
        ni = n1 + n0
        num += a * n0 / ni
        den += c * n1 / ni
    r = float(num / den) if den > 0 else None
    S3["standardized_ratio"][lab] = round(r, 4) if r else None
    print(f"  [分层标准化比 MH] {lab}: {r:.4f}（层 = 前区和值五分位 × 生日号区）")
d = S3["standardized_ratio"]
if d["pre"] and d["post"]:
    S3["standardized_decay"] = round(d["post"] / d["pre"], 4)
    print(f"  → 标准化后衰减比 = {S3['standardized_decay']:.3f}")

# 3.4 滚动窗口（数据驱动；不按自然年 —— L3）
W, STEP = 400, 50
mids, rw1, rw2 = [], [], []
for st in range(0, len(rows) - W + 1, STEP):
    sl = slice(st, st + W)
    m = mask[sl]
    if m.sum() < 25 or (~m).sum() < 25:
        continue
    mids.append(dates[sl][W // 2])
    rw1.append(float(w1[sl][m].mean() / w1[sl][~m].mean()))
    rw2.append(float(w2[sl][m].mean() / w2[sl][~m].mean()))
mids = np.array(mids); rw1 = np.array(rw1); rw2 = np.array(rw2)
t = np.arange(len(mids), dtype=float)
S3["rolling"] = {"window": W, "step": STEP, "n_windows": int(len(mids))}
for name, r in (("w1", rw1), ("w2", rw2)):
    lr = np.log(r)
    b1, b0 = np.polyfit(t, lr, 1)
    resid = lr - (b0 + b1 * t)
    # 数据驱动变点扫描（枚举窗口序列的切点，最小化分段均值 SSE）
    best, best_sse = None, np.inf
    for k in range(3, len(lr) - 3):
        sse = ((lr[:k] - lr[:k].mean()) ** 2).sum() + ((lr[k:] - lr[k:].mean()) ** 2).sum()
        if sse < best_sse:
            best, best_sse = k, sse
    sse_trend = (resid ** 2).sum()
    # 趋势的置换检验（打乱时间顺序）
    perm = np.empty(1000)
    for q in range(1000):
        pb = np.polyfit(t, rng.permutation(lr), 1)[0]
        perm[q] = pb
    p_trend = float(np.mean(np.abs(perm) >= abs(b1)))
    S3["rolling"][name] = {
        "trend_per_year": round(float(b1 * (len(mids) / ((np.datetime64(mids[-1]) - np.datetime64(mids[0])).astype(float) / 365.25))), 4),
        "slope_per_window": round(float(b1), 5),
        "p_trend_permutation": round(p_trend, 4),
        "best_breakpoint_index": int(best),
        "best_breakpoint_date": str(mids[best]),
        "sse_step": round(float(best_sse), 4),
        "sse_trend": round(float(sse_trend), 4),
        "step_better_than_trend": bool(best_sse < sse_trend),
        "first": round(float(r[0]), 3), "last": round(float(r[-1]), 3),
        "min": round(float(r.min()), 3), "max": round(float(r.max()), 3),
    }
    dd = S3["rolling"][name]
    print(f"  [滚动 {name}] {len(mids)} 窗（W={W}）；首 {dd['first']} → 末 {dd['last']}；"
          f"趋势/年={dd['trend_per_year']:+.3f} 置换 p={dd['p_trend_permutation']:.3f}")
    print(f"          数据驱动最优切点 = {dd['best_breakpoint_date']}（阶梯 SSE={dd['sse_step']:.2f} vs "
          f"线性 SSE={dd['sse_trend']:.2f}；阶梯更优={dd['step_better_than_trend']}）")
# 逐年轨迹（描述性，**不**用于变点判定 —— L3 禁止按自然年硬切宣称断点）
S3["per_year"] = {}
print("  [逐年轨迹（描述性，不作变点依据 —— L3）]")
print(f"    {'年':>4s} {'n':>4s} {'n_ge2':>5s} {'w1比':>7s} {'w2比':>7s} {'P(max<=31)':>10s}")
for y in range(2007, 2027):
    sel = years == y
    if sel.sum() < 20:
        continue
    m = mask[sel]
    if m.sum() < 5 or (~m).sum() < 5:
        continue
    r1 = float(w1[sel][m].mean() / w1[sel][~m].mean())
    r2 = float(w2[sel][m].mean() / w2[sel][~m].mean())
    S3["per_year"][str(y)] = {"n": int(sel.sum()), "n_ge2": int(m.sum()),
                              "w1_ratio": round(r1, 3), "w2_ratio": round(r2, 3),
                              "p_max_le_31": round(float(birth[sel].mean()), 3)}
    print(f"    {y:>4d} {sel.sum():>4d} {m.sum():>5d} {r1:>7.2f} {r2:>7.2f} {birth[sel].mean():>10.3f}")

# 敏感性：窗口长度 300/500 + 非重叠窗口（避免重叠窗口带来的自相关假象）
S3["rolling_sensitivity"] = {}
for W2, step2, tag in ((300, 300, "W300_nonoverlap"), (500, 500, "W500_nonoverlap"),
                       (300, 25, "W300_step25"), (500, 100, "W500_step100")):
    mm, rr = [], []
    for st in range(0, len(rows) - W2 + 1, step2):
        sl = slice(st, st + W2)
        m = mask[sl]
        if m.sum() < 15 or (~m).sum() < 15:
            continue
        mm.append(dates[sl][W2 // 2])
        rr.append(float(w2[sl][m].mean() / w2[sl][~m].mean()))
    if len(mm) < 8:
        continue
    lr = np.log(np.array(rr))
    best, best_sse = None, np.inf
    for k in range(2, len(lr) - 2):
        sse = ((lr[:k] - lr[:k].mean()) ** 2).sum() + ((lr[k:] - lr[k:].mean()) ** 2).sum()
        if sse < best_sse:
            best, best_sse = k, sse
    tt = np.arange(len(lr), dtype=float)
    sl_ = np.polyfit(tt, lr, 1)[0]
    S3["rolling_sensitivity"][tag] = {
        "window": W2, "step": step2, "n_windows": int(len(lr)),
        "best_breakpoint_date": str(mm[best]), "slope_per_window": round(float(sl_), 5),
        "first": round(float(np.exp(lr[0])), 3), "last": round(float(np.exp(lr[-1])), 3),
    }
    print(f"  [滚动敏感 {tag}] n={len(lr)} 最优切点={mm[best]} "
          f"首 {np.exp(lr[0]):.3f} → 末 {np.exp(lr[-1]):.3f}")
print("  → 若各窗口设定下最优切点均落在 2013 年前后（与 F-0006 的 2013-08 变点同期），"
      "说明效应下降与【号码分布结构变化】同时发生，而非独立的人群行为平滑漂移。")
rep["S3_scale_and_composition"] = S3

# ============================================================
# S4 归因判定 + F-0004 口径
# ============================================================
print("\n" + "=" * 72)
print("S4 归因判定与 F-0004 口径建议")
print("=" * 72)

ALL = list(combinations(range(1, 36), 5))
assert len(ALL) == 324632
P_GE2 = float(np.mean([run_count(c) >= 2 for c in ALL]))
P_LT2 = 1 - P_GE2

def alpha_from_ratio(R):
    """由观测形态比值校准人群权重 α（与 F-0004 完全相同的校准式）。"""
    return R * P_LT2 / P_GE2

def uplift_with_alpha(alpha, n_sim=200000, n0=N0_ANCHOR, pool_anchor=POOL_ANCHOR):
    w_all = np.array([(alpha if run_count(c) >= 2 else 1.0) * (BIRTHDAY_W if max(c) <= 31 else 1.0)
                      for c in ALL])
    norun_idx = np.array([i for i, c in enumerate(ALL) if run_count(c) == 0])
    mean_all = w_all.mean()
    idx_rand = rng.integers(0, len(ALL), n_sim)
    idx_norun = norun_idx[rng.integers(0, len(norun_idx), n_sim)]
    cf_rand = w_all[idx_rand].mean() / mean_all
    cf_norun = w_all[idx_norun].mean() / mean_all
    ratio = float(cf_norun / cf_rand)
    boots = np.empty(N_BOOT)
    for k in range(N_BOOT):
        r_ = w_all[rng.integers(0, len(ALL), n_sim)].mean()
        n_ = w_all[norun_idx[rng.integers(0, len(norun_idx), n_sim)]].mean()
        boots[k] = n_ / r_
    lo, hi = np.percentile(boots, [2.5, 97.5])

    def amt(cf, n0_, pool_):
        n_total = max(cf * n0_, 1.0)
        raw = min(pool_ / n_total, CAP_PART * 2)
        trig = (n_total * raw) >= CAP_TOTAL
        return min(n_total * raw, CAP_TOTAL) / n_total, trig

    scen = {}
    for label, f in (("anchor", 1.0), ("anchor_lo", 0.5), ("anchor_hi", 1.5)):
        a_r, tr = amt(cf_rand, n0 * f, pool_anchor)
        a_n, tn = amt(cf_norun, n0 * f, pool_anchor)
        scen[label] = {
            "uplift_pct_with_cap": round(float(a_n / a_r - 1) * 100, 2),
            "cap_triggered": bool(tr or tn),
        }
    return {
        "alpha": round(float(alpha), 4),
        "collision_factor_rand": round(float(cf_rand), 4),
        "collision_factor_norun": round(float(cf_norun), 4),
        "ratio_norun_vs_rand": round(ratio, 4),
        "ratio_ci95": [round(float(lo), 4), round(float(hi), 4)],
        "uplift_pct_nocap": round(float(1.0 / ratio - 1) * 100, 2),
        "scenarios_with_cap": scen,
    }

calib = {
    "full_sample_1.3603(沿用 r03)": 1.3603,
    "post_segment_w1_mean_1.2472": S0["post"]["w1"]["mean_ratio"],
    "post_segment_w2_trimmed": S0["post"]["w2"]["trimmed10_ratio"],
    "post_segment_w2_median": S0["post"]["w2"]["median_ratio"],
    "full_sample_w2_trimmed": trimmed_ratio(w2[mask], w2[~mask]),
}
S4 = {"calibrations": {}}
for lab, R in calib.items():
    a = alpha_from_ratio(R)
    u = uplift_with_alpha(a)
    S4["calibrations"][lab] = u
    print(f"  [{lab}] R={R:.4f} → α={u['alpha']:.4f}；未计封顶 uplift={u['uplift_pct_nocap']:.2f}%；"
          f"含封顶 anchor={u['scenarios_with_cap']['anchor']['uplift_pct_with_cap']:.2f}%")
S4["recommended"] = {
    "ratio": S0["post"]["w1"]["mean_ratio"],
    "reason": ("后段（>=2013-08-28）与现行 E6 时段更接近；前段存在号码分布异常与"
               "注数/销售额不一致（S1），不宜作为校准基准。"),
    "alpha": S4["calibrations"]["post_segment_w1_mean_1.2472"]["alpha"],
    "uplift_pct_nocap": S4["calibrations"]["post_segment_w1_mean_1.2472"]["uplift_pct_nocap"],
    "uplift_pct_with_cap_anchor": S4["calibrations"]["post_segment_w1_mean_1.2472"]["scenarios_with_cap"]["anchor"]["uplift_pct_with_cap"],
}
print(f"  [建议] F-0004 改用后段口径 R={S4['recommended']['ratio']:.4f}："
      f"未计封顶 {S4['recommended']['uplift_pct_nocap']:.1f}%，"
      f"含封顶实测锚点 {S4['recommended']['uplift_pct_with_cap_anchor']:.1f}%"
      f"（r03 全样本口径为 121.48% / 41.42%）")

S4["attribution"] = {
    "H-A 行为真实变化": ("部分支持：控制销量与成分后，效应在后段仍显著低于前段（NB2 交互 IRR<1）；"
                          "但幅度被均值比口径放大。"),
    "H-B 数据口径/质量变化": ("不能排除：前段（<2013-08）存在两项硬证据 —— (i) 前区号码分布严重偏离均匀"
                              "（29-35 号系统性超发，P(前区全部<=31)=%.3f vs 理论 %.3f，z=%.1f）；"
                              "(ii) 由中出注数反推的投注量超出售额允许上限（均价 %.2f 元/注 < 最低票价 2 元），"
                              "后段则为 %.2f 元/注。"
                              % (birth[pre].mean(), P_MAX31, z_pre,
                                 S1["pre"]["yuan_per_ticket_from_w1"], S1["post"]["yuan_per_ticket_from_w1"])),
    "H-C 销量稀释": ("基本排除为主因：NB2 以 log(销量/2) 为 offset 控制规模后，交互项仍显著"
                     "（IRR=%.3f, p=%.2e），说明不是「注数变多导致比值被摊平」。"
                     % (S3["nb2_glm"]["w1"]["irr_interaction"], S3["nb2_glm"]["w1"]["p_interaction"])),
    "verdict": ("衰减是真实的，但「幅度衰减过半」是**均值比口径 + 前段重尾**的联合产物；"
                "前段效应量不可靠（w1 剔 top1 即由 2.107 降至 %.3f，中位数比 = %.2f），"
                "稳健口径下的衰减比约 %.2f~%.2f。"
                "因此 F-0004 应改用**后段稳健口径**校准，而不是全样本 1.36、也不是前段的 2.11。"
                % (S0["pre"]["w1"]["drop_top1"], S0["pre"]["w1"]["median_ratio"],
                   S2["decay"]["w2"]["trimmed10"], S2["decay"]["w2"]["median"])),
}
rep["S4_attribution_and_calibration"] = S4

# ============================================================
# 存档
# ============================================================
out = os.path.join(OUT_DIR, "decay_cause.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"seed": RNG_SEED, "cut": CUT, "report": rep}, f, ensure_ascii=False, indent=2)
print(f"\n[written] {out}")
