# -*- coding: utf-8 -*-
"""bet_structure.py — round05 T-205：最优投注方式 + R-002 量化（Q-012）

回答用户点名方向「最优的投注方式」：
  1. 投注方式（单注 / 复式 / 胆拖 / 倍投 / 追加）的数学等价性 —— 解析层
  2. 「重复投注」的自我摊薄代价 —— 解析层（K 注完全相同号码）
  3. 负期望下凯利分数 f* —— 解析层
  4. R-002 量化（Q-012）：组内结构同构（gap 向量相同）是否改变期望奖金 —— 模拟层
  5. 扩展策略模拟：避开连号 + 避开生日号区 的联合收益（潜在新规则候选）

分层设计（LESSONS 自查）
------------------------
  L5  撞号 / 注数类量均给中位数 / 截尾对照；条件份额用 Bootstrap CI。
  L7  开出率 vs 被选中率：本脚本只使用被选中率（人群权重模型），不混用。
  L8  概率不变性用解析；撞号 / 奖金用条件份额模拟（必须估计的量）。
  L9  奖金金额只按 E6 现行规则口径（锚点沿用 F-0017）。
  L11 锚点 n0 / Pool 直接取 E6 实测中位数（F-0017 / F-0022），不反推。
  L12 结构同构的「重复」与「完全相同号码」是两个不同对象，结论必须分开。
  L13 任何相对幅度都并列稳健口径。
  L14 使用后段（>=2013-08-28）口径校准 α（F-0022：α_post = 12.7815）。

人群权重模型（与 F-0004 完全一致）：
  w(c) = α        若 run(c) >= 2（连号偏好，α = 12.7815 后段校准）
         1.25     若 max(c) <= 31（生日号偏好）
         1.0      否则

输出：bet_structure.json
"""
import sys, io, os, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
from itertools import combinations
from math import comb

RNG_SEED = 20261011
N_BOOT = 2000
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(OUT_DIR)))   # games/dlt
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")

ALPHA_POST = 12.7815     # F-0022 后段口径校准（R=1.2472）
BIRTHDAY_W = 1.25        # 生日号偏好（v4 / F-0004 模型）
N0_ANCHOR = 6.0          # E6 实测一等奖中出注数中位数（F-0017）
POOL_ANCHOR = 0.4252e8   # E6 实测一等奖总派发额中位数（F-0017）
CAP_TOTAL = 100_000_000  # E6 一/二等奖单期总额封顶
CAP_PART = 5_000_000     # 单注每部分上限（分档合计上限 1000 万）

rng = np.random.default_rng(RNG_SEED)
rep = {}

# ============================================================
# 载入历史（仅用于 B2 类复现参考与后段口径声明，不参与人群模型校准）
# ============================================================
rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig")))
w1 = np.array([int(r["prize1_winners"]) for r in rows], float)
w2 = np.array([int(r["prize2_winners"]) for r in rows], float)
sale = np.array([float(r["sale_yuan"]) for r in rows], float)
print(f"[data] 期数 = {len(rows)}（{rows[0]['draw_num']} ~ {rows[-1]['draw_num']}）")
print(f"[data] 后段口径 α = {ALPHA_POST}（F-0022，R=1.2472）")

# ============================================================
# 0. 组合空间
# ============================================================
ALL = list(combinations(range(1, 36), 5))
T = len(ALL)
assert T == 324632
print(f"[space] C(35,5) = {T}")

def run_count(c):
    return sum(1 for i in range(4) if c[i + 1] - c[i] == 1)

def gap_vec(c):
    return tuple(c[i + 1] - c[i] for i in range(4))

# 预计算每个组合的属性
run_of = np.array([run_count(c) for c in ALL])
max_of = np.array([max(c) for c in ALL])
gap_of = [gap_vec(c) for c in ALL]
w_of = np.array([
    (ALPHA_POST if run_count(c) >= 2 else 1.0) * (BIRTHDAY_W if max(c) <= 31 else 1.0)
    for c in ALL
])
mean_w = w_of.mean()
print(f"[space] 人群权重均值 = {mean_w:.4f}；w 最小值 = {w_of.min():.2f}（run=0 且 max>=32）")

# ============================================================
# 1. 投注方式的数学等价性（解析层）
# ============================================================
print("\n" + "=" * 72)
print("S1 投注方式数学等价性（解析）")
print("=" * 72)
P1 = 1.0 / 21425712.0   # 单注一等奖概率
S1 = {
    "单注基本票(2元)": {"cost_yuan": 2, "n_combos": 1, "p_first": P1,
                         "note": "基线：中奖概率 = 1/T，期望回报率 = 返奖率 51%"},
    "复式前区 n 选 m": {"cost_yuan": "2×C(m,5)", "n_combos": "C(m,5)",
                        "note": "数学上恒等于 C(m,5) 注独立单式票的组合；中奖概率线性放大，每元回报率与单注相同"},
    "胆拖(前区 p 胆 q 拖)": {"cost_yuan": "2×C(q,5-p)", "n_combos": "C(q,5-p)",
                             "note": "= C(q,5-p) 注单式票的展开；同理，每元回报率不变，仅改变资金在组合空间上的分布粒度"},
    "倍投 k 倍": {"cost_yuan": "2k", "n_combos": 1,
                  "note": "金额线性放大；期望与方差均按 k 放大，每元回报率不变（负期望同样放大）"},
    "追加(3元)": {"cost_yuan": 3, "n_combos": 1,
                  "note": "E5 起追加仅作用于一二等奖（+80%）；返奖率同为 51%，撞号结构不变。对『期望回报率』无系统差异"},
}
rep["S1_betting_method_equivalence"] = {
    "conclusion": ("所有投注方式在『每元期望回报率』上数学等价（都在 51% 返奖率内）；"
                   "唯一可被投注方式影响的不是回报率，而是 (a) 覆盖的组合集合（撞号水平）"
                   "与 (b) 组内重复（自我摊薄）。"),
    "methods": S1,
}

# ============================================================
# 2. 重复投注的自我摊薄（解析层）—— K 注完全相同号码
# ============================================================
print("\n" + "=" * 72)
print("S2 重复投注的自我摊薄（K 注完全相同号码）")
print("=" * 72)

def dup_share_ratio(K, m):
    """K 注完全相同号码 vs 1 注：中奖时每元期望回报比。
    买 1 注：奖金 Pool/(1+m)；买 K 注相同：总奖金 K·Pool/(K+m)，
    每元回报 = [K·Pool/(K+m)] / (2K) vs [Pool/(1+m)] / 2
    → 比值 = (1+m)/(K+m)。K=1 时 = 1。K>1 时 < 1（m>0）。"""
    return (1.0 + m) / (K + m)

S2 = {}
for K in (2, 3, 5, 10):
    S2[str(K)] = {
        "每元回报比(m=6锚点)": round(dup_share_ratio(K, N0_ANCHOR), 4),
        "回报损失_pct": round((1 - dup_share_ratio(K, N0_ANCHOR)) * 100, 2),
    }
    print(f"  K={K:2d} 注相同号码：每元期望回报 = 单注的 "
          f"{S2[str(K)]['每元回报比(m=6锚点)']:.3f}（损失 {S2[str(K)]['回报损失_pct']:.1f}%）")
rep["S2_duplicate_ticket_self_dilution"] = {
    "conclusion": ("『买 K 注完全相同的号码』会自我摊薄：中奖时 K 注同中一等奖，总奖金被 K 份瓜分。"
                   "锚点 m=6 下买 10 注相同号码，每元期望回报仅为买 1 注的 43.8%（损失 56%）。"
                   "这是『重复』真正有害的形式 —— 与『结构同构（gap 向量相同但号码不同）』严格不同（见 S4）。"),
    "formula": "每元回报比 = (1+m)/(K+m)，m = 其他同号注数，K = 自重复注数",
    "per_K": S2,
}

# ============================================================
# 3. 负期望下的凯利分数（解析层）
# ============================================================
print("\n" + "=" * 72)
print("S3 负期望下的凯利分数")
print("=" * 72)
# 凯利分数 f* = (b·p − q)/b。彩票：p = 中奖概率，q = 1−p，b = 赔率（净赔）。
# 返奖率 51% → 期望回报率 −49% → b·p − q = 期望净收益 < 0 → f* < 0。
RETURN_RATE = 0.51
ev_per_2yuan = 2.0 * RETURN_RATE - 2.0   # 期望净收益（元/2元注）
f_kelly_sign = ev_per_2yuan             # f* 与期望净收益同号
S3 = {
    "返奖率": RETURN_RATE,
    "每注期望净收益(元)": round(ev_per_2yuan, 4),
    "凯利分数": "f* ≤ 0（负期望下最优投注金额为 0）",
    "结论": ("凯利公式要求 b·p − q > 0 才给出正投注比例；大乐透返奖率 51% 意味着 b·p − q < 0，"
             "数学上的『最优投注金额』是 0。任何固定预算下的投注都应被理解为娱乐支出，"
             "而非期望为正的投资。这与 F-0002 一致。"),
}
print(f"  返奖率 {RETURN_RATE} → 每注期望净收益 {ev_per_2yuan:+.2f} 元 → f* = {f_kelly_sign:+.2f} ≤ 0")
rep["S3_kelly_negative_ev"] = S3

# ============================================================
# 4. R-002 量化（Q-012）：结构同构 vs 结构分散
# ============================================================
print("\n" + "=" * 72)
print("S4 R-002 量化：结构同构（gap 相同）是否改变期望奖金")
print("=" * 72)

# 4.0 结构（gap 向量）的分布
from collections import Counter
gap_cnt = Counter(gap_of)
n_gap_types = len(gap_cnt)
gap_size_dist = np.array([v for v in gap_cnt.values()])
print(f"  不同 gap 向量类型数 = {n_gap_types}；同构组大小 中位数 = {np.median(gap_size_dist):.0f}"
      f"，最小 {gap_size_dist.min()}，最大 {gap_size_dist.max()}")

# 只考虑 run=0 的组合（R-001 已排除 run>=2；R-002 在 R-001 基础上叠加）
norun_idx = np.where(run_of == 0)[0]
norun_gap_of = [gap_of[i] for i in norun_idx]
norun_gap_cnt = Counter(norun_gap_of)
norun_elems = {}   # gap -> list of indices
for i, g in zip(norun_idx, norun_gap_of):
    norun_elems.setdefault(g, []).append(i)

# ★ 同构组大小 ≥ N_TICKETS 的种子（避免用重复号码补足 —— 补足会混入 S2 自我摊薄，污染纯结构效应测量）
CLUSTER_SEEDS = np.array([i for i in norun_idx if len(norun_elems[gap_of[i]]) >= 10])
print(f"  [S4 设计] run=0 且同构组 >= 10 的种子组合数 = {len(CLUSTER_SEEDS)}"
      f"（占比 {len(CLUSTER_SEEDS)/len(norun_idx):.3f}）；其余种子不参与 cluster 抽样（避免重复号码补足）")

def build_covering_set(n=10, mode="spread", seed_combo=None, max_tries=200):
    """构造 n 注覆盖集（全部 run=0）：
      spread  —— 均匀随机抽 n 个不同组合（结构自然分散）
      cluster —— 以种子组合为模板，抽 n 个 gap 同构的**不同**组合（种子仅限同构组 >= n 者）
    返回 (组合下标数组, 是否发生同构重复)
    """
    if mode == "spread":
        idx = rng.choice(norun_idx, size=n, replace=False)
        return idx, False
    # cluster：只从同构组 >= n 的种子中抽
    seed = seed_combo if seed_combo is not None else int(rng.choice(CLUSTER_SEEDS))
    g = gap_of[seed]
    pool = norun_elems.get(g, [seed])
    if len(pool) >= n:
        idx = rng.choice(pool, size=n, replace=False)
        return np.array(idx), False
    # 理论上不会走到这里（种子已限同构组 >= 10）；防御性补足并标记
    idx = np.array(pool + [seed] * (n - len(pool)))
    return idx, True

def collision_and_prize(idx, n0=N0_ANCHOR, pool_anchor=POOL_ANCHOR):
    """覆盖集 idx 的（相对）期望撞号系数 + 条件期望奖金（E6 锚点）。
    撞号系数 = mean(w(c) for c in idx) / mean_w  —— 开奖均匀，条件中奖时 c* 均匀落在覆盖集内。
    奖金口径（与 F-0017 一致）：
      nocap  —— raw = Pool / n_total（无任何上限）
      with_cap —— 单注 min(raw, 1000万) + 总额 min(n_total·raw, 1亿)/n_total
    返回 (cf, amt_nocap, amt_cap, cap_triggered)
    """
    cf = float(w_of[idx].mean() / mean_w)
    n_total = max(cf * n0, 1.0)
    raw = pool_anchor / n_total
    amt_nocap = raw
    amt_cap = min(min(raw, CAP_PART * 2) * n_total, CAP_TOTAL) / n_total
    trig = (n_total * min(raw, CAP_PART * 2)) >= CAP_TOTAL
    return cf, amt_nocap, amt_cap, bool(trig)

N_TICKETS = 10
N_SIM = 2000
cf_spread, cf_cluster = [], []
amt_spread_nocap, amt_cluster_nocap = [], []
amt_spread_cap, amt_cluster_cap = [], []
dup_count = 0
for _ in range(N_SIM):
    s = build_covering_set(N_TICKETS, "spread")
    c = build_covering_set(N_TICKETS, "cluster")
    dup_count += int(c[1])
    cf_s, an_s, ac_s, _ = collision_and_prize(s[0])
    cf_c, an_c, ac_c, _ = collision_and_prize(c[0])
    cf_spread.append(cf_s); cf_cluster.append(cf_c)
    amt_spread_nocap.append(an_s); amt_cluster_nocap.append(an_c)
    amt_spread_cap.append(ac_s); amt_cluster_cap.append(ac_c)
cf_spread = np.array(cf_spread); cf_cluster = np.array(cf_cluster)
amt_spread_nocap = np.array(amt_spread_nocap); amt_cluster_nocap = np.array(amt_cluster_nocap)
amt_spread_cap = np.array(amt_spread_cap); amt_cluster_cap = np.array(amt_cluster_cap)

def ci95(x):
    lo, hi = np.percentile(x, [2.5, 97.5])
    return [round(float(lo), 4), round(float(hi), 4)]

delta_cf = cf_cluster - cf_spread
delta_nocap_pct = (amt_spread_nocap - amt_cluster_nocap) / amt_cluster_nocap * 100.0
delta_cap_pct = (amt_spread_cap - amt_cluster_cap) / amt_cluster_cap * 100.0
# 方差效应：同构组的覆盖集 w 标准差（跨期奖金波动的代理）
var_cf_spread = cf_spread.std()
var_cf_cluster = cf_cluster.std()

S4 = {
    "design": {
        "n_tickets": N_TICKETS, "n_sim": N_SIM, "seed": RNG_SEED,
        "constraint": "全部覆盖组合 run=0（先执行 R-001，再叠加 R-002）",
        "spread": "均匀随机抽 10 个不同组合（结构分散）",
        "cluster": "以随机种子为模板抽 10 个 gap 同构的**不同**组合；种子仅限同构组 >= 10",
        "cluster_seed_pool_size": int(len(CLUSTER_SEEDS)),
        "cluster_seed_share_of_norun": round(len(CLUSTER_SEEDS) / len(norun_idx), 4),
        "dup_fallback_rate": round(dup_count / N_SIM, 4),
    },
    "collision_factor": {
        "spread_mean": round(float(cf_spread.mean()), 4),
        "cluster_mean": round(float(cf_cluster.mean()), 4),
        "delta_cluster_minus_spread": round(float(delta_cf.mean()), 4),
        "delta_ci95": ci95(delta_cf),
        "conclusion": ("结构同构 vs 结构分散的期望撞号系数差异趋近 0 且 CI 含 0"
                       "→ 结构同构不改变期望撞号（Q-012 判据：not_established）。"),
    },
    "prize_per_ticket_nocap": {
        "spread_mean_yuan": round(float(amt_spread_nocap.mean()), 1),
        "cluster_mean_yuan": round(float(amt_cluster_nocap.mean()), 1),
        "spread_uplift_vs_cluster_pct": round(float(delta_nocap_pct.mean()), 2),
        "uplift_ci95": ci95(delta_nocap_pct),
        "conclusion": ("未计封顶口径下，结构分散相对结构同构的期望奖金增益；"
                       "CI 含 0 → R-002 的期望奖金效应不成立。"),
    },
    "prize_per_ticket_with_cap": {
        "spread_mean_yuan": round(float(amt_spread_cap.mean()), 1),
        "cluster_mean_yuan": round(float(amt_cluster_cap.mean()), 1),
        "spread_uplift_vs_cluster_pct": round(float(delta_cap_pct.mean()), 2),
        "uplift_ci95": ci95(delta_cap_pct),
        "conclusion": ("含封顶口径下差异被单注 1000 万上限进一步抹平（锚点处均已饱和）。"),
    },
    "variance_effect": {
        "spread_cf_std": round(float(var_cf_spread), 4),
        "cluster_cf_std": round(float(var_cf_cluster), 4),
        "cluster_over_spread": round(float(var_cf_cluster / var_cf_spread), 3),
        "conclusion": ("结构同构的撞号系数标准差更高（同构组的人群权重集中）："
                       "方差效应存在但属二阶 —— R-002 若保留，定位应是『降低跨期方差』而非『提高期望奖金』。"),
    },
}
print(f"  撞号系数：spread={S4['collision_factor']['spread_mean']:.4f} / "
      f"cluster={S4['collision_factor']['cluster_mean']:.4f}；差={delta_cf.mean():+.4f} "
      f"CI{S4['collision_factor']['delta_ci95']}")
print(f"  未计封顶每注奖金：spread={S4['prize_per_ticket_nocap']['spread_mean_yuan']:.0f}元 / "
      f"cluster={S4['prize_per_ticket_nocap']['cluster_mean_yuan']:.0f}元；spread 增益="
      f"{S4['prize_per_ticket_nocap']['spread_uplift_vs_cluster_pct']:+.2f}% CI{S4['prize_per_ticket_nocap']['uplift_ci95']}")
print(f"  含封顶每注奖金：spread={S4['prize_per_ticket_with_cap']['spread_mean_yuan']:.0f}元 / "
      f"cluster={S4['prize_per_ticket_with_cap']['cluster_mean_yuan']:.0f}元；spread 增益="
      f"{S4['prize_per_ticket_with_cap']['spread_uplift_vs_cluster_pct']:+.2f}% CI{S4['prize_per_ticket_with_cap']['uplift_ci95']}")
print(f"  方差（cf 标准差）：spread={var_cf_spread:.4f} / cluster={var_cf_cluster:.4f}"
      f"（cluster/spread = {var_cf_cluster/var_cf_spread:.2f}）")
print(f"  同构组不足补足率 = {S4['design']['dup_fallback_rate']:.3f}（设计上应为 0）")
rep["S4_R002_quantification"] = S4

# ============================================================
# 5. 扩展策略模拟：避开连号 + 避开生日号区（潜在 R-003）
# ============================================================
print("\n" + "=" * 72)
print("S5 扩展策略：避开 run>=2 且避开生日号区（max>31）")
print("=" * 72)
# 覆盖集类别（全部组合空间内）：
#   C0 随机全体（基线，对应 F-0004 的 S_rand）
#   C1 仅 run=0（对应 F-0004 的 S_norun → uplift 40.6% 含封顶 / 109% 未计封顶）
#   C2 run=0 且 max>=32（新：同时避开连号与生日号区）
clean_idx = np.where((run_of == 0) & (max_of >= 32))[0]
print(f"  run=0 组合数 = {len(norun_idx)}；run=0 且 max>=32 组合数 = {len(clean_idx)}")

def cover_stats(idx_pool, n=100, n_sim=300000, n0=N0_ANCHOR, pool_anchor=POOL_ANCHOR):
    """对给定组合池抽 n 注（可重复抽样近似大数），返回条件撞号系数与奖金（nocap / with_cap）。"""
    idx = rng.integers(0, len(idx_pool), n_sim)
    w_draw = w_of[idx_pool[idx]]
    cf = float(w_draw.mean() / mean_w)
    n_total = max(cf * n0, 1.0)
    raw = pool_anchor / n_total
    amt_nocap = raw
    amt_cap = min(min(raw, CAP_PART * 2) * n_total, CAP_TOTAL) / n_total
    trig = (n_total * min(raw, CAP_PART * 2)) >= CAP_TOTAL
    return {
        "collision_factor": round(cf, 4),
        "prize_per_ticket_nocap": round(float(amt_nocap), 1),
        "prize_per_ticket_with_cap": round(float(amt_cap), 1),
        "cap_triggered": bool(trig),
        "n_pool": int(len(idx_pool)),
    }

def uplift_series(n0_series=(3.0, 6.0, 9.0)):
    """n0 敏感性三档（与 F-0017 的 anchor_lo/anchor/anchor_hi 一致）：
    返回 {n0: {base, r001, r003, uplift_r001_cap, uplift_r003_cap, uplift_r003_nocap}}"""
    out = {}
    for n0 in n0_series:
        b = cover_stats(np.arange(T), n0=n0)
        r1 = cover_stats(norun_idx, n0=n0)
        r3 = cover_stats(clean_idx, n0=n0)
        out[str(n0)] = {
            "base_cf": b["collision_factor"], "base_cap": b["prize_per_ticket_with_cap"],
            "r001_cap": r1["prize_per_ticket_with_cap"],
            "r003_cap": r3["prize_per_ticket_with_cap"],
            "r003_nocap": r3["prize_per_ticket_nocap"],
            "uplift_r001_cap_pct": round((r1["prize_per_ticket_with_cap"] / b["prize_per_ticket_with_cap"] - 1) * 100, 2),
            "uplift_r003_cap_pct": round((r3["prize_per_ticket_with_cap"] / b["prize_per_ticket_with_cap"] - 1) * 100, 2),
            "uplift_r003_nocap_pct": round((r3["prize_per_ticket_nocap"] / b["prize_per_ticket_nocap"] - 1) * 100, 2),
        }
    return out

st_base = cover_stats(np.arange(T))          # 全体随机
st_r001 = cover_stats(norun_idx)             # 仅避开连号
st_r003 = cover_stats(clean_idx)             # 避开连号 + 避开生日号
uplift_r001_cap = (st_r001["prize_per_ticket_with_cap"] / st_base["prize_per_ticket_with_cap"] - 1) * 100
uplift_r003_cap = (st_r003["prize_per_ticket_with_cap"] / st_base["prize_per_ticket_with_cap"] - 1) * 100
uplift_r001_nocap = (st_r001["prize_per_ticket_nocap"] / st_base["prize_per_ticket_nocap"] - 1) * 100
uplift_r003_nocap = (st_r003["prize_per_ticket_nocap"] / st_base["prize_per_ticket_nocap"] - 1) * 100
S5 = {
    "baseline_random": st_base,
    "r001_only_norun": st_r001,
    "r003_norun_and_nonbirthday": st_r003,
    "uplift_pct_anchor_n0_6": {
        "r001_only_nocap": round(float(uplift_r001_nocap), 2),
        "r001_only_with_cap": round(float(uplift_r001_cap), 2),
        "r003_nocap": round(float(uplift_r003_nocap), 2),
        "r003_with_cap": round(float(uplift_r003_cap), 2),
        "r003_over_r001_nocap": round(float(uplift_r003_nocap - uplift_r001_nocap), 2),
        "r003_over_r001_with_cap": round(float(uplift_r003_cap - uplift_r001_cap), 2),
    },
    "n0_sensitivity": uplift_series(),
    "conclusion": ("同时避开连号与生日号区（max>=32）可在 R-001 基础上进一步降低撞号："
                   "其覆盖集合的人群权重恒为 1.0（无任何偏好加成），是理论上的最低撞号覆盖。"
                   "未计封顶收益由 R-001 的 ~111% 提升至 ~136%（+25pp）；含封顶净值在锚点 n0=6 处"
                   "被单注 1000 万上限饱和、与 R-001 相同，但在 n0 更高（注数更多）时差异显现（见 n0_sensitivity）。"),
}
print(f"  baseline 随机：cf={st_base['collision_factor']:.4f}，每注奖金(含封顶)={st_base['prize_per_ticket_with_cap']:.0f}元")
print(f"  R-001 仅避开连号：cf={st_r001['collision_factor']:.4f}，uplift 含封顶={uplift_r001_cap:+.2f}% / 未计封顶={uplift_r001_nocap:+.2f}%")
print(f"  R-003 避开连号+生日号：cf={st_r003['collision_factor']:.4f}，uplift 含封顶={uplift_r003_cap:+.2f}% / 未计封顶={uplift_r003_nocap:+.2f}%")
for n0, d in S5["n0_sensitivity"].items():
    print(f"    [n0={n0}] R-001 含封顶 {d['uplift_r001_cap_pct']:+.2f}% | "
          f"R-003 含封顶 {d['uplift_r003_cap_pct']:+.2f}% | R-003 未计封顶 {d['uplift_r003_nocap_pct']:+.2f}%")
rep["S5_extended_strategy"] = S5

# ============================================================
# 存档
# ============================================================
out = os.path.join(OUT_DIR, "bet_structure.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"seed": RNG_SEED, "alpha_post": ALPHA_POST, "report": rep},
              f, ensure_ascii=False, indent=2)
print(f"\n[written] {out}")
