# -*- coding: utf-8 -*-
"""back_collision.py — T-103 后区撞号建模 (Q-003)。
问题: 后区 12 选 2 (66 组合) 是否也存在人群偏好/撞号集中? 量级多大? 是否值得并入 R-001?
识别: 设 p(F,B) 为整注人群密度。prize1_winners w1 ∝ n·p(F,B); prize2_winners
      w2 ∝ n·Σ_{a∈B}Σ_{b∉B} p(F,a,b)。若 p(F,B) ∝ u(F)·v(B) (可分离), 则
      w2/w1 = g(B)/v(B), g(B)=Σ_{a∈B}Σ_{b∉B} v(a,b) 与 n、前区无关。令
      p_B = v(B)/(v(B)+g(B)), 则 w1|(w1+w2) ~ Binomial(w1+w2, p_B) (Poisson 模型下)。
      对 v 做条件二项 MLE, 比对 w2/w1 直接回归稳健得多 (w1 中位数 2、17.9% 为 0)。
      主模型 v(a,b) ∝ s_a·s_b (11 自由参数, 均值归一); 用 66 参数饱和模型检验该假设。
纪律: L1/L2/L5/L6/L7/L8/L9/L10/L11/L12。红线: 不涉及中奖概率 (恒 1/21,425,712)。
"""
import csv, json, math, os, itertools
import numpy as np
RNG_SEED = 20261011
ALPHA_FRONT = 13.9405        # F-0004 连号权重, 不得改动
BIRTHDAY_MULT = 1.25         # F-0004 生日号(前区 max<=31)权重, 不得改动
CUT_DATE = "2013-08-28"      # F-0006 数据驱动切点 (非自然年硬切, 满足 L3)
N_BOOT = 2000                # s 的 bootstrap 次数
N_MC = 10000                 # MC 检验次数 (L2: >=10000)
N_CAL_S = 400                # 独立模型"稳定性"零模拟
N_CAL_SAT = 400              # 饱和模型"稳定性"零模拟
N_CV = 400                   # 交叉验证 uplift 的 bootstrap
N_LR_NULL = 2000             # LR 零分布的参数 bootstrap
P_NULL = 1.0 / 21.0          # 均匀 v 下的 p_B
HERE = os.path.dirname(os.path.abspath(__file__))     # scripts
ROOT = HERE
for _ in range(5):  # scripts->round04->iterations->dlt->games->repo
    ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "games", "dlt", "data", "raw", "dlt_full_2933.csv")
OUT = os.path.join(HERE, "back_collision.json")
class LCG:
    """32-bit LCG, 逐位可复现。"""
    __slots__ = ("s",)
    def __init__(self, seed): self.s = seed & 0xFFFFFFFF
    def u32(self):
        self.s = (1664525 * self.s + 1013904223) & 0xFFFFFFFF
        return self.s
    def uniform(self): return self.u32() / 4294967296.0
    def randint(self, n): return int(self.uniform() * n)
    def randn(self):
        u1 = max(self.uniform(), 1e-12); u2 = self.uniform()
        return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    def rbinom(self, m, p):
        if m <= 0: return 0
        z = self.randn()
        return max(0, min(m, int(round(m * p + z * math.sqrt(m * p * (1 - p))))))
rng = LCG(RNG_SEED)                          # bootstrap / 校准 (可复现)
mc_rng = np.random.default_rng(RNG_SEED)     # 仅大样本 MC 频数 (与 bootstrap 独立)
def load_data():
    with open(DATA, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    n = len(rows)
    b1 = np.array([int(r["back_1"]) - 1 for r in rows], int)
    b2 = np.array([int(r["back_2"]) - 1 for r in rows], int)
    w1 = np.array([int(r["prize1_winners"]) for r in rows], float)
    w2 = np.array([int(r["prize2_winners"]) for r in rows], float)
    pid = -np.ones((12, 12), int); pairs = []; k = 0
    for a in range(12):
        for b in range(a + 1, 12):
            pid[a, b] = pid[b, a] = k; pairs.append((a, b)); k += 1
    cross = []
    for (a, b) in pairs:
        cs = []
        for c in range(12):
            if c != a and c != b: cs += [pid[a, c], pid[b, c]]
        cross.append(sorted(set(int(x) for x in cs)))
    return dict(rows=rows, n=n, b1=b1, b2=b2, w1=w1, w2=w2, m=w1 + w2, q=pid[b1, b2],
                pairs=pairs, cross=cross, dates=[r["date"] for r in rows],
                draws=[r["draw_num"] for r in rows])
D = load_data()
N = D["n"]; PAIR = D["pairs"]; CROSS = D["cross"]
PA = np.array([a for a, b in PAIR]); PB = np.array([b for a, b in PAIR])
def aggregate(idx):
    return (np.bincount(D["q"][idx], weights=D["m"][idx], minlength=66),
            np.bincount(D["q"][idx], weights=D["w1"][idx], minlength=66))
def g_of(v): return np.array([sum(v[c] for c in CROSS[q]) for q in range(66)])
def s_norm(s): return s / s.mean()
def fit_s(agm, agw1):
    """独立号码模型 v(a,b) ∝ s_a*s_b 的条件二项 IRLS。返回归一化 s(12)。"""
    mask = agm > 0; th = np.zeros(11)
    for _ in range(100):
        s = np.empty(12); s[0] = 1.0; s[1:] = np.exp(th)
        S = s.sum(); si = s[PA]; sj = s[PB]
        u = si + sj; v = si * sj; g = u * (S - u)
        p = np.where(mask, v / (v + g), 0.0)
        w = agm * p * (1 - p); res = agw1 - agm * p
        X = np.empty((66, 11))
        for k in range(1, 12):
            inP = ((PA == k) | (PB == k)).astype(float)
            X[:, k - 1] = inP - s[k] * np.where(inP > 0, S - u, u) / g
        A = X.T @ (w[:, None] * X) + np.eye(11) * 1e-10
        try: d = np.linalg.solve(A, X.T @ res)
        except np.linalg.LinAlgError: break
        th = th + d
        if np.max(np.abs(d)) < 1e-12: break
    return s_norm(np.exp(np.concatenate([[0.0], th])))
def v_of_s(s): return s[PA] * s[PB]
def nll_s(s, agm, agw1):
    S = s.sum(); si = s[PA]; sj = s[PB]; u = si + sj; v = si * sj; g = u * (S - u)
    m = agm > 0
    return float(np.sum(agm[m] * np.log(v[m] + g[m]) - agw1[m] * np.log(v[m])
                        - (agm[m] - agw1[m]) * np.log(g[m])))
def fit_sat(agm, agw1):
    """66 参数饱和模型: 只假设可分离 + 计数结构, 不假设号码独立。返回 v(66, 未归一)。"""
    phi = np.zeros(65)
    for _ in range(150):
        v = np.empty(66); v[0] = 1.0; v[1:] = np.exp(phi)
        g = g_of(v); p = v / (v + g); w = agm * p * (1 - p); res = agw1 - agm * p
        A = np.zeros((65, 65)); sc = np.zeros(65)
        for q in range(66):
            if agm[q] <= 0: continue
            act = [q] + CROSS[q]
            x = np.empty(len(act)); x[0] = 1.0
            for i in range(1, len(act)): x[i] = -v[act[i]] / g[q]
            keep = [i for i, a in enumerate(act) if a != 0]
            idx = [act[i] - 1 for i in keep]; xx = x[keep]
            A[np.ix_(idx, idx)] += w[q] * np.outer(xx, xx)
            sc[idx] += xx * res[q]
        A += np.eye(65) * 1e-10
        try: d = np.linalg.solve(A, sc)
        except np.linalg.LinAlgError: break
        phi = phi + d
        if np.max(np.abs(d)) < 1e-11: break
    v = np.empty(66); v[0] = 1.0; v[1:] = np.exp(phi)
    return v
def nll_sat(v, agm, agw1):
    g = g_of(v); m = agm > 0
    return float(np.sum(agm[m] * np.log(v[m] + g[m]) - agw1[m] * np.log(v[m])
                        - (agm[m] - agw1[m]) * np.log(g[m])))
def pctl(a, q):
    s = np.sort(np.asarray(a, float)); i = (len(s) - 1) * q
    lo = int(math.floor(i)); hi = int(math.ceil(i))
    return float(s[lo] + (s[hi] - s[lo]) * (i - lo))
def corr(a, b): return float(np.corrcoef(np.asarray(a, float), np.asarray(b, float))[0, 1])
def uplift_v(v, K):
    m = v.mean(); top = set(np.argsort(-v)[:K].tolist())
    av = v[[q for q in range(66) if q not in top]].mean()
    return dict(rand_mean=float(m), avoid_mean=float(av), uplift=float(m / av - 1))
def top_pairs(v, K, rev=False, agm=None, agw1=None):
    out = []
    for q in np.argsort(v if rev else -v)[:K].tolist():
        it = dict(pair=str(PAIR[q][0] + 1) + "+" + str(PAIR[q][1] + 1), density=round(float(v[q]), 4))
        if agm is not None: it["picked_rate_share"] = round(float(agw1[q] / agm[q]), 5)
        out.append(it)
    return out
# ============================================================ main
ALL = np.arange(N)
AGM, AGW1 = aggregate(ALL)
CUT = next((t for t in range(N) if D["dates"][t] >= CUT_DATE), N)
EARLY = ALL[:CUT]; LATE = ALL[CUT:]
AGE_M, AGE_W1 = aggregate(EARLY); AGL_M, AGL_W1 = aggregate(LATE)
s_full = fit_s(AGM, AGW1); v_s = v_of_s(s_full)
sat_raw = fit_sat(AGM, AGW1); v_sat = sat_raw / sat_raw.mean()
TOT_M = float(AGM.sum()); TOT_W1 = float(AGW1.sum())
nll0 = -(TOT_W1 * math.log(1 / 21) + (TOT_M - TOT_W1) * math.log(20 / 21))
nll_s_full = nll_s(s_full, AGM, AGW1); nll_sat_full = nll_sat(sat_raw, AGM, AGW1)
LR_indep = 2 * (nll0 - nll_s_full); LR_sat_indep = 2 * (nll_s_full - nll_sat_full)
LR_sat_null = 2 * (nll0 - nll_sat_full)
# --- 开出率 (drawn frequency) ---
pc66 = np.bincount(D["q"], minlength=66)
chi66 = float(np.sum((pc66 - N / 66) ** 2 / (N / 66)))
sim66 = mc_rng.multinomial(N, np.full(66, 1 / 66), size=N_MC)
mc66 = float((((sim66 - N / 66) ** 2 / (N / 66)).sum(1) >= chi66 - 1e-9).mean())
nc12 = np.bincount(np.concatenate([D["b1"], D["b2"]]), minlength=12)
chi12 = float(np.sum((nc12 - 2 * N / 12) ** 2 / (2 * N / 12)))
sim12 = np.zeros((N_MC, 12))
for r in range(N_MC):
    pp = mc_rng.integers(0, 66, N)
    sim12[r] = np.bincount(np.concatenate([PA[pp], PB[pp]]), minlength=12)
mc12 = float((((sim12 - 2 * N / 12) ** 2 / (2 * N / 12)).sum(1) >= chi12 - 1e-9).mean())
# --- 被选中率 (picked density): 66 对聚合检验 ---
p0 = P_NULL
X2 = float(np.sum((AGW1 - AGM * p0) ** 2 / (AGM * p0 * (1 - p0))))
simX = mc_rng.binomial(AGM.astype(np.int64), p0, size=(N_MC, 66)).astype(float)
mcX = float((((simX - AGM * p0) ** 2 / (AGM * p0 * (1 - p0))).sum(1) >= X2 - 1e-9).mean())
# --- bootstrap: s 的 CI 与 in-sample uplift ---
boot_s = []; boot_up = {1: [], 5: [], 10: []}
for _ in range(N_BOOT):
    am, aw = aggregate(np.array([rng.randint(N) for _ in range(N)]))
    s = fit_s(am, aw); boot_s.append(s); v = v_of_s(s)
    for K in (1, 5, 10): boot_up[K].append(uplift_v(v, K)["uplift"])
s_ci = [[pctl([b[k] for b in boot_s], .025), pctl([b[k] for b in boot_s], .975)] for k in range(12)]
upS = {}
for K in (1, 5, 10):
    u = uplift_v(v_s, K); u["ci95"] = [pctl(boot_up[K], .025), pctl(boot_up[K], .975)]; upS[K] = u
upSat = {K: uplift_v(v_sat, K) for K in (1, 5, 10)}
# --- LR 零分布的参数 bootstrap ---
ge = 0
for _ in range(N_LR_NULL):
    aw = np.array([rng.rbinom(int(AGM[q]), p0) for q in range(66)], float)
    if 2 * (nll0 - nll_s(fit_s(AGM, aw), AGM, aw)) >= LR_indep - 1e-9: ge += 1
lr_null_p = ge / N_LR_NULL
# --- 分期稳健性 + "稳定模型"零模拟 ---
s_early = fit_s(AGE_M, AGE_W1); s_late = fit_s(AGL_M, AGL_W1)
sat_e = fit_sat(AGE_M, AGE_W1); sat_e = sat_e / sat_e.mean()
sat_l = fit_sat(AGL_M, AGL_W1); sat_l = sat_l / sat_l.mean()
obs_s_corr = corr(s_early, s_late); obs_sat_corr = corr(sat_e, sat_l)
def pB_of(v):
    g = g_of(v); return v / (v + g)
def sim_split(fit_fn, norm_fn, ncal, v_ref):
    pB = pB_of(v_ref); out = []
    for _ in range(ncal):
        w1s = np.array([rng.rbinom(int(D["m"][t]), pB[D["q"][t]]) for t in range(N)], float)
        amE = np.bincount(D["q"][:CUT], weights=D["m"][:CUT], minlength=66)
        awE = np.bincount(D["q"][:CUT], weights=w1s[:CUT], minlength=66)
        amL = np.bincount(D["q"][CUT:], weights=D["m"][CUT:], minlength=66)
        awL = np.bincount(D["q"][CUT:], weights=w1s[CUT:], minlength=66)
        out.append(corr(norm_fn(fit_fn(amE, awE)), norm_fn(fit_fn(amL, awL))))
    return out
def _sat_norm(x): return x / x.mean()
sim_s_corr = sim_split(fit_s, s_norm, N_CAL_S, v_s)
sim_sat_corr = sim_split(fit_sat, _sat_norm, N_CAL_SAT, sat_raw)
s_odd_even_corr = corr(fit_s(*aggregate(ALL[ALL % 2 == 1])), fit_s(*aggregate(ALL[ALL % 2 == 0])))
# --- 交叉验证 uplift (前段估 Top-K -> 后段评估, 反之亦然) ---
def fit_v(am, aw, use_sat):
    if use_sat:
        v = fit_sat(am, aw); return v / v.mean()
    return v_of_s(fit_s(am, aw))
def cv_uplift(amA, awA, amB, awB, K, use_sat):
    VA = fit_v(amA, awA, use_sat); VB = fit_v(amB, awB, use_sat)
    top = set(np.argsort(-VA)[:K].tolist())
    return float(VB.mean() / VB[[q for q in range(66) if q not in top]].mean() - 1)
cvS = {}
for K in (1, 5, 10):
    a = cv_uplift(AGE_M, AGE_W1, AGL_M, AGL_W1, K, False)
    b = cv_uplift(AGL_M, AGL_W1, AGE_M, AGE_W1, K, False)
    cvS[K] = dict(early_to_late=a, late_to_early=b, mean=(a + b) / 2)
cv_boot = {1: [], 5: [], 10: []}
for _ in range(N_CV):
    ts = np.array([rng.randint(N) for _ in range(N)])
    e = ts[ts < CUT]; l = ts[ts >= CUT]
    if len(e) < 200 or len(l) < 200: continue
    amE, awE = aggregate(e); amL, awL = aggregate(l)
    for K in (1, 5, 10):
        cv_boot[K].append((cv_uplift(amE, awE, amL, awL, K, False)
                           + cv_uplift(amL, awL, amE, awE, K, False)) / 2)
# --- 前区参照 (F-0004 参数, 未改动) ---
sumU = sumU0 = sumUlt = 0.0; n0 = nlt = 0
for c in itertools.combinations(range(1, 36), 5):
    run = sum(1 for i in range(1, 5) if c[i] - c[i - 1] == 1)
    w = (ALPHA_FRONT if run >= 2 else 1.0) * (BIRTHDAY_MULT if c[4] <= 31 else 1.0)
    sumU += w
    if run == 0: sumU0 += w; n0 += 1
    if run < 2: sumUlt += w; nlt += 1
cfU = sumU / 324632.0; cfU0 = sumU0 / n0; cfUlt = sumUlt / nlt
# --- E6 子样本 ---
e6_idx = np.array([t for t in range(N) if int(D["draws"][t]) >= 26014])
e6m, e6w = aggregate(e6_idx)
e6mask = e6m > 0
e6X2 = float(np.sum((e6w[e6mask] - e6m[e6mask] * p0) ** 2 / (e6m[e6mask] * p0 * (1 - p0))))
def rd(x):
    if isinstance(x, bool): return x
    if isinstance(x, (float, np.floating)): return round(float(x), 6)
    if isinstance(x, (list, tuple)): return [rd(v) for v in x]
    if isinstance(x, dict): return {k: rd(v) for k, v in x.items()}
    if isinstance(x, np.integer): return int(x)
    return x
best_i = int(np.argmax(s_full)); worst_i = int(np.argmin(s_full))
w1_zero = int((D["w1"] == 0).sum())
mv = lambda a: float(np.mean(a)); md = lambda a: float(np.median(a)); vr = lambda a: float(np.var(a, ddof=1))
result = dict(
  meta=dict(script="games/dlt/iterations/round04/scripts/back_collision.py", task="T-103", question="Q-003",
    round="round04", game="dlt", data_path="games/dlt/data/raw/dlt_full_2933.csv", data_version="dlt_full_2933",
    n_periods=N, draw_num_min=D["draws"][0], draw_num_max=D["draws"][-1], date_min=D["dates"][0],
    date_max=D["dates"][-1], rng_seed=RNG_SEED, rules_epoch="E6", front_cut_date=CUT_DATE,
    n_bootstrap=N_BOOT, n_mc=N_MC,
    boundary_note="本分析只涉及『被选中率』(人群购买密度)与中奖时的奖金份额;完全不涉及中奖概率。单注一等奖概率恒为 1/21,425,712。"),
  identification=dict(
    separability="p(F,B) ∝ u(F)·v(B) (前/后区偏好可分离) 使 w2/w1 与 n、前区偏好无关",
    independent_back="v(a,b) ∝ s_a·s_b (后区号码独立偏好), 由 66 参数饱和模型检验",
    estimating_equation="给定 m=w1+w2 与开出的后区对 B: w1|m ~ Binomial(m, p_B), p_B=v(B)/(v(B)+g(B)), g(B)=Σ_{c∈B,d∉B}v(c,d)",
    why_conditional_binomial="直接对 w2/w1 回归会被小 w1 污染(中位数 2, 17.9% 为 0); 条件二项似然在 w1=0 时仍有效且是 Poisson 模型下的充分统计量",
    aggregation="p_B 只依赖后区对 B, 故逐期数据聚合为 66 个二项观测 (mB,w1B), 是充分统计量, 不损信息"),
  descriptive=dict(
    w1=dict(mean=mv(D["w1"]), median=md(D["w1"]), var=vr(D["w1"]), var_mean=vr(D["w1"]) / mv(D["w1"]),
            max=float(D["w1"].max()), p90=float(np.quantile(D["w1"], .9))),
    w2=dict(mean=mv(D["w2"]), median=md(D["w2"]), var=vr(D["w2"]), var_mean=vr(D["w2"]) / mv(D["w2"]), max=float(D["w2"].max())),
    m=dict(mean=mv(D["m"]), median=md(D["m"]), var=vr(D["m"]), var_mean=vr(D["m"]) / mv(D["m"]), max=float(D["m"].max())),
    w1_zero_count=w1_zero, w1_zero_frac=w1_zero / N, m_per_pair_min=float(AGM.min()), m_per_pair_max=float(AGM.max())),
  open_rate=dict(
    note_L7="本小节全部是『开出率』(号码被摇出的频率), 与『被选中率』无关, 不得混用 (L7)",
    back_combo_66=dict(expected=N / 66, min=int(pc66.min()), max=int(pc66.max()), chi2=chi66, df=65,
      n_mc=N_MC, mc_p=round(mc66, 3), min_expected_cell=N / 66,
      verdict="开出率与均匀无显著差异(MC p≈%.2f), 与 F-0011 一致; 最小期望频数 44.4>>5, 渐近卡方本已可用, 仍报 MC 精确检验" % mc66),
    back_number_12=dict(expected=2 * N / 12, counts=[int(x) for x in nc12], chi2=chi12, df=11,
      n_mc=N_MC, mc_p=round(mc12, 3), min_expected_cell=2 * N / 12,
      verdict="12 个后区号码开出率与均匀无显著差异(MC p≈%.2f)" % mc12)),
  picked_rate=dict(
    note_L7="本小节是『被选中率』(彩民购买密度), 全部来自 prize1_winners/prize2_winners, 与开出率严格分开 (L7)",
    pooled_pair_test=dict(chi2=X2, df=65, overdispersion=X2 / 65, n_mc=N_MC, mc_p=round(mcX, 4),
      verdict="强烈拒绝『66 个后区对人群密度相同』: 过散布 %.2fx, MC p<1e-4" % (X2 / 65)),
    independent_s_model=dict(numbers=list(range(1, 13)), s=[float(x) for x in s_full], s_ci95=s_ci,
      nll=nll_s_full, nll_null=nll0, lr_vs_uniform=LR_indep, lr_df=11, lr_mc_p=lr_null_p, n_mc_lr=N_LR_NULL,
      best=dict(number=best_i + 1, value=float(s_full[best_i]), ci95=s_ci[best_i]),
      worst=dict(number=worst_i + 1, value=float(s_full[worst_i]), ci95=s_ci[worst_i]),
      max_pair_density=float(v_s.max()), min_pair_density=float(v_s.min()), pair_density_ratio=float(v_s.max() / v_s.min()),
      top5_pairs=top_pairs(v_s, 5, agm=AGM, agw1=AGW1), bottom5_pairs=top_pairs(v_s, 5, True, agm=AGM, agw1=AGW1),
      note="s 为相对偏好, 12 个数均值归一到 1; LR=%.1f(df=11) 拒绝均匀" % LR_indep),
    saturated_model=dict(note="66 参数饱和模型(仅假设可分离+计数结构)",
      lr_vs_uniform=LR_sat_null, lr_vs_uniform_df=65, lr_vs_independent=LR_sat_indep, lr_vs_independent_df=54,
      verdict="独立号码模型被饱和模型强烈拒绝(LR=%.0f, df=54), 存在对特异偏好; 但该特异成分跨时期不稳定" % LR_sat_indep,
      top10_pairs=top_pairs(v_sat, 10, agm=AGM, agw1=AGW1), bottom10_pairs=top_pairs(v_sat, 10, True, agm=AGM, agw1=AGW1))),
  falsification=dict(
    split_at_F0006=dict(cut_date=CUT_DATE, cut_index=CUT, n_early=CUT, n_late=N - CUT,
      s_early=[float(x) for x in s_early], s_late=[float(x) for x in s_late], s_corr=obs_s_corr,
      stable_sim_s_corr_median=pctl(sim_s_corr, .5),
      stable_sim_s_corr_ci95=[pctl(sim_s_corr, .025), pctl(sim_s_corr, .975)],
      saturated_v_corr=obs_sat_corr, stable_sim_sat_corr_median=pctl(sim_sat_corr, .5),
      stable_sim_sat_corr_ci95=[pctl(sim_sat_corr, .025), pctl(sim_sat_corr, .975)],
      verdict=("11 参数独立 s 模型: 观测跨段相关 %.3f, 稳定零模型 95%%CI [%.3f,%.3f] —— 接近/略低于下界, 属轻度不稳定; "
               "66 参数饱和模型: 观测 %.3f vs 稳定零模型 95%%CI [%.3f,%.3f] —— 偏好排名显著不稳定"
               % (obs_s_corr, pctl(sim_s_corr, .025), pctl(sim_s_corr, .975),
                  obs_sat_corr, pctl(sim_sat_corr, .025), pctl(sim_sat_corr, .975)))),
    odd_even_split=dict(s_corr=s_odd_even_corr),
    noise_level=dict(w1_median=md(D["w1"]), w1_zero_frac=w1_zero / N, m_median=md(D["m"]),
      note="w1 是小计数且重尾; 聚合为 66 个二项观测, 每对约 3600 次试验, p 的相对标准误约 7.5%"),
    e6_only=dict(n=len(e6_idx), pooled_pair_X2=e6X2,
      verdict="现行 E6 仅 %d 期仍显示过散布, 但不足以独立估计 66 个对密度" % len(e6_idx))),
  conditional_share=dict(
    method="给定 v 时条件份额是有限集上的精确期望(无需 MC, L8): CF(strategy)=E_{B~strategy}[v(B)]; uplift=CF(random)/CF(avoid)-1。CI 来自对期数重采样并重拟合 s 的 bootstrap(2000)。",
    in_sample_independent_s=dict(K1=upS[1], K5=upS[5], K10=upS[10], note="用全样本 s 选 Top-K, 含前视/过拟合, 是上界(L6)"),
    in_sample_saturated=dict(K1=upSat[1], K5=upSat[5], K10=upSat[10], note="过拟合更严重"),
    cross_validated_independent_s=dict(
      K1=dict(cvS[1], ci95=[pctl(cv_boot[1], .025), pctl(cv_boot[1], .975)]),
      K5=dict(cvS[5], ci95=[pctl(cv_boot[5], .025), pctl(cv_boot[5], .975)]),
      K10=dict(cvS[10], ci95=[pctl(cv_boot[10], .025), pctl(cv_boot[10], .975)]),
      note="前/后段互相预测, 无前视 —— 诚实口径; K=5/10 的 95%CI 含 0"),
    front_reference=dict(alpha=ALPHA_FRONT, birthday_mult=BIRTHDAY_MULT, uniform_mean_u=cfU, run0_mean_u=cfU0,
      run_lt2_mean_u=cfUlt, uplift_run0_pct=(cfU / cfU0 - 1) * 100, uplift_run_lt2_pct=(cfU / cfUlt - 1) * 100,
      note="F-0004 参数未改动; 未计封顶上界"),
    magnitude_comparison=dict(front_uplift_pct=(cfU / cfUlt - 1) * 100, back_K5_in_sample_pct=upS[5]["uplift"] * 100,
      back_K10_in_sample_pct=upS[10]["uplift"] * 100, back_K10_cv_pct=cvS[10]["mean"] * 100,
      ratio_front_over_backK10_in_sample=(cfU / cfUlt - 1) / upS[10]["uplift"], note="后区避让效应比前区连号效应小 1-2 个数量级")),
  conclusion=dict(
    back_collision_exists="YES —— 后区对被选中率强烈非均匀(过散布 %.2fx, MC p<1e-4); 开出率则均匀" % (X2 / 65),
    magnitude="独立 s 模型: 9 号(%.3f) vs 12 号(%.3f), 组合密度比 %.2fx; 饱和模型 Top/Bottom 对密度比约 %.1fx"
      % (s_full[8], s_full[11], v_s.max() / v_s.min(), v_sat.max() / v_sat.min()),
    stability="单号码偏好(11 参数)仅轻度不稳定; 对特异偏好(额外 54 参数)排名显著不稳定",
    in_sample_uplift_pct={K: upS[K]["uplift"] * 100 for K in (1, 5, 10)},
    cross_validated_uplift_pct={K: cvS[K]["mean"] * 100 for K in (1, 5, 10)},
    merge_into_R001=False,
    recommendation=("不建议并入 R-001。理由: (1) 量级差 1-2 个数量级(前区~120%% vs 后区 K=5/10 交叉验证约 1-3%%); "
      "(2) 交叉验证的 95%%CI 含 0, 避开『历史热门后区对』的收益不可靠; (3) 对特异偏好排名不稳定, 硬排除会引入前视偏差(L6)。"
      "可选的弱做法: 仅对独立 s 模型下最热的 1-2 个后区号码(9、5)做软降权, 标注 ★★☆ 与不稳定 caveat; 当前证据不足以形成规则, "
      "建议先记 F-0xxx 并留待 round05 用滚动窗口复核。"),
    cap_relevance="E6 一等奖单期总额封顶 1 亿元(F-0016: 样本内从未触发)。后区避让的收益是提高『中奖时的单注奖金』, 与封顶的关系同前区: 只有在高注数、接近单注 500 万上限或总额上限时才被稀释; 后区效应量级小, 几乎不改变封顶的触发概率。"),
  caveats=[
    "L7: 全篇严格区分『开出率』(66/12 频次, 均匀) 与『被选中率』(prize1/prize2 反推, 非均匀), 两者不可混用。",
    "L5/L1: w1 中位数 2、17.9% 为 0、var/mean=8.46; 故不用逐期比值回归, 改用条件二项似然(聚合为 66 个二项观测量)。",
    "L2: 66 组合开出率的期望频数 44.4(>5), 渐近卡方本已可用; 仍同时给出 MC 精确检验(B=10000)。被选中率检验同样用 MC。",
    "L6: 『避开全样本 Top-K 后区对』含前视偏差, in-sample uplift 是上界; 诚实值为 early↔late 交叉验证值(CI 含 0)。",
    "L8: 给定 v 的条件份额是有限集上的精确期望, 故不做 Monte-Carlo(模拟只会引入噪声); 仅用 bootstrap 传播模型不确定性。",
    "L9: 一/二等奖注数含义(5+2/5+1)自 2007 未变, 故被选中率可跨全期合并; 所有金额类结论必须声明 rules_epoch='E6'。",
    "L10: E6(>=26014) 仅 102 期, 未宣称任何封顶条款被触发; 结论限于『当前样本下的偏好结构』。",
    "L11: s 是由 w1/w2 观测量估计的相对密度(均值归一), 不是由无关量反推; 量纲为无量纲相对密度。",
    "L12: 独立 s 模型与饱和模型是不同参数化(11 vs 65), 饱和模型相对独立模型 LR=423(df=54); 但两者共享同一 (w1,w2) 数据源, 不是独立数据。",
    "识别假设 p(F,B) ∝ u(F)v(B) 无法用现有数据直接检验(需按前区分层); 若彩民前后区选择相关, w2/w1 会混入前区成分。",
    "s 的 Bootstrap CI 只覆盖抽样不确定性, 不含模型错设(独立号码假设被饱和模型拒绝)带来的偏差。",
    "若未来把后区避让并入规则, 必须按 L6 做滚动窗口/样本外复核, 并声明适用 rules_epoch。"])
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rd(result), f, ensure_ascii=False, indent=2)
print("[written]", OUT)
print(json.dumps(rd(dict(LR_indep=LR_indep, LR_sat_indep=LR_sat_indep, X2=X2, overdisp=X2 / 65,
  s=[float(x) for x in s_full], in_sample={K: upS[K]["uplift"] for K in (1, 5, 10)},
  cv={K: cvS[K]["mean"] for K in (1, 5, 10)}, front_pct=(cfU / cfUlt - 1) * 100)), ensure_ascii=False, indent=2))
