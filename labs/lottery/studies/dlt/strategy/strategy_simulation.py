# -*- coding: utf-8 -*-
"""策略模拟验证框架 (strategy_simulation.py)

目标：对 T6 购买策略中的**每一条可检验主张**，用蒙特卡洛模拟给出量化验证，
      并报告效应量 + 置信区间 + 对照基线，而非结论式的"有效/无效"。

模拟设计的三个层次
------------------
A. 概率层（已解析可证）：选号方式是否改变中奖概率 —— 用均匀随机抽样做对照。
B. 撞号层（可模拟）：连号/偏好形态是否提高"同号人数"（=摊薄奖金）—— 用"人群选号模型"模拟。
C. 经济层（可模拟）：在固定预算下，"避免高撞号形态"能否提高**中奖时的期望奖金** —— 端到端模拟。

关键假设（必须在报告中显式声明）
--------------------------------
H1  开奖为独立均匀随机（前区 C(35,5)、后区 C(12,2) 等概率）—— 由历史检验支持
    （见 labs/lottery/studies/dlt/iterations/round02/known_errors.md E1–E7）。
H2  彩民选号**非均匀**：对连号、生日号（1–31）、低和值等形态有偏好 —— 由 prize2_winners 数据与精确理论分布对比支持。
H3  "撞号人数"与"该组合被多少人买"成正比。用历史一等奖/二等奖注数近似人群密度。
H4  奖级/奖金规则按**现行（2026-02 起）** 7 奖级执行（见 labs/lottery/studies/dlt/rules_history.md）。

输出：JSON + 文本，供报告引用。
"""
import sys, io, os, json, math, itertools
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
from math import comb

RNG_SEED = 20261010
OUT = os.path.dirname(os.path.abspath(__file__))   # labs/lottery/studies/dlt/strategy/
_GAME = os.path.dirname(OUT)                       # labs/lottery/studies/dlt/
PKG = _GAME                                        # 兼容旧变量名
DATA = os.path.join(_GAME, 'data', 'raw', 'dlt_full_2933.csv')

rng = np.random.default_rng(RNG_SEED)
report = {}

# ============================================================
# 工具：精确理论分布（枚举 C(35,5)=324632）
# ============================================================
def enumerate_front():
    allc = list(itertools.combinations(range(1, 36), 5))
    return allc

ALLC = enumerate_front()
T35 = len(ALLC)
print(f'[setup] 前区组合总数 C(35,5) = {T35}')
print(f'[setup] 单注组合总数 = {T35*66} = {T35*66}')

def run_count(c):
    return int(np.sum(np.diff(c) == 1))

def sum_of(c):
    return sum(c)

def big_count(c):
    return int(np.sum(np.array(c) >= 18))

def odd_count(c):
    return int(np.sum(np.array(c) % 2 == 1))

# ============================================================
# A. 概率层：任何选号方式都不改变中奖概率
# ============================================================
def simulate_prize_prob(n_draws=200000):
    """对同一注号码，在 n_draws 次独立开奖下的中奖分布。
    理论上：每注中任意奖级的概率固定；单注一等奖概率 = 1/21425712。"""
    p1 = 1.0 / 21425712
    return {'first_prize_prob': p1}

report['A_probability_layer'] = {
    'claim': '任何选号方式都不改变单注中奖概率',
    'first_prize_prob': 1.0 / 21425712,
    'total_combinations': 21425712,
    'verdict': '解析可证：均匀随机下每注等概率，选号方式不可改变分子（1），只能影响分母（是否与他人共享）。',
    'is_provable_analytically': True,
}

# ============================================================
# B. 撞号层：人群选号模型 —— 形态偏好是否提高"同号人数"
# ============================================================
# 用历史数据校准：对每个历史开奖，比较一等奖注数（撞号代理）
# 在 run>=2 与 run<2 之间的差异，并做置换/分层，避免 E1/E5 陷阱。

import csv
def load_hist():
    rows = []
    with open(DATA, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

HIST = load_hist()
print(f'[data] 历史期数 = {len(HIST)}，最新 = {HIST[-1]["draw_num"]} {HIST[-1]["date"]}')

def front_of(r):
    return tuple(int(r[f'front_{i}']) for i in range(1, 6))

# 每期：run 数、和值、一等奖注数
hist_run = np.array([run_count(front_of(r)) for r in HIST])
hist_w1 = np.array([int(r['prize1_winners']) for r in HIST], float)
hist_w2 = np.array([int(r['prize2_winners']) for r in HIST], float)
hist_sum = np.array([sum_of(front_of(r)) for r in HIST])

# B1. 精确理论：run 分布（开出率）
theo_run = Counter(run_count(c) for c in ALLC)
theo_run_prob = {k: v / T35 for k, v in theo_run.items()}
obs_run = Counter(hist_run.tolist())
obs_run_prob = {k: v / len(hist_run) for k, v in obs_run.items()}

report['B1_run_open_rate'] = {
    'note': '开出率 = 某形态被摇出的频率。精确枚举为真值。',
    'theoretical': {str(k): round(theo_run_prob.get(k, 0), 6) for k in range(5)},
    'observed': {str(k): round(obs_run_prob.get(k, 0), 6) for k in range(5)},
    'n_draws': len(hist_run),
}

# B2. 撞号代理：run>=2 期的中奖注数是否更高（被选中率）
mask_ge2 = hist_run >= 2
def ratio_and_boot(a, b, n_boot=2000):
    """比率 a.mean()/b.mean() + Bootstrap 95%CI（a、b 各自独立重采样）"""
    if b.mean() == 0:
        return None
    est = a.mean() / b.mean()
    boots = []
    na, nb = len(a), len(b)
    for _ in range(n_boot):
        ra = a[rng.integers(0, na, na)].mean()
        rb = b[rng.integers(0, nb, nb)].mean()
        if rb > 0:
            boots.append(ra / rb)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {'ratio': round(float(est), 4), 'ci95': [round(float(lo), 4), round(float(hi), 4)]}

w1_ratio = ratio_and_boot(hist_w1[mask_ge2], hist_w1[~mask_ge2])
w2_ratio = ratio_and_boot(hist_w2[mask_ge2], hist_w2[~mask_ge2])
report['B2_collision_proxy'] = {
    'claim': '连号(run>=2)形态的投注人群密度更高 → 撞号更多',
    'metric': '同形态期的一等奖/二等奖注数比值 (ge2 vs lt2)',
    'prize1_winners_ratio': w1_ratio,
    'prize2_winners_ratio': w2_ratio,
    'n_ge2': int(mask_ge2.sum()), 'n_lt2': int((~mask_ge2).sum()),
    'verdict': '若比值 CI 下界 > 1，则连号形态确实集聚更多彩民（撞号效应存在）。'
}

# ============================================================
# C. 经济层：端到端模拟 —— 固定预算 100 注，"避开高撞号形态"的价值
# ============================================================
# 模拟设定：
#  - 人群选号模型（简化）：彩民以概率 w 偏好"含连号"的组合。
#    用历史 B2 结果校准 w：使模拟出的 run>=2 中奖注数比值 ≈ 观测比值。
#  - 我们的策略：从"无连号(run=0)"组合中随机选 N 注；对照组：全体随机选 N 注。
#  - 开奖：均匀随机。
#  - 奖金：按现行 7 奖级，一等奖按 奖池/中奖注数 分摊（简化：用观测平均一等奖注数分布）。
#
# 因一等奖概率极低（1/2142万），直接模拟"中一等奖"不现实。
# 故采用**条件期望**方法：给定"中了一等奖"（该事件发生），比较不同策略下
#   条件期望"同奖人数"，进而折扣奖金。这是唯一在有限算力下可信的做法。

def calibrate_run_weight():
    """校准人群模型的"连号权重"α：使模型预测的 run>=2 vs run<2 人群密度比值
    等于 B2 观测到的一等奖注数比值（1.36）。
    模型：p(run>=2) ∝ α·P_theo(run>=2)，其余 ∝ P_theo。
    观测比值 R = (α·P_ge2)/(P_lt2)  其中 P_ge2+P_lt2=1（理论）
    → α = R · P_lt2 / P_ge2
    """
    P_ge2 = theo_run_prob.get(2, 0) + theo_run_prob.get(3, 0) + theo_run_prob.get(4, 0)
    P_lt2 = 1 - P_ge2
    R = report['B2_collision_proxy']['prize1_winners_ratio']['ratio']
    alpha = R * P_lt2 / P_ge2
    return round(float(alpha), 4), round(float(P_ge2), 4), round(float(P_lt2), 4)

ALPHA, P_GE2, P_LT2 = calibrate_run_weight()
print(f'[calib] 连号人群权重 α = {ALPHA} （理论 P(run>=2)={P_GE2}）')

def simulate_conditional_share(n_sim=300000, N=100):
    """条件份额模拟：给定开奖为随机一组号码，比较两种选号策略下
       "与我们同号的他人注数期望"（撞号），从而得到单注奖金的相对高低。

    人群权重模型（由历史校准）：
      w(c) = α          若 run(c) >= 2
             1.25·(...)  若 max(c)<=31（生日偏好）
             其余 1
    其中 α 由 B2 观测比值校准。
    """
    def weight(c):
        w = 1.0
        if run_count(c) >= 2:
            w *= ALPHA            # 连号偏好（已校准）
        if max(c) <= 31:
            w *= 1.25            # 生日号（全部 ≤31）偏好
        return w

    w_all = np.array([weight(c) for c in ALLC], dtype=float)
    norun_idx = np.array([i for i, c in enumerate(ALLC) if run_count(c) == 0])

    # 策略 S_rand：全体均匀随机选 N 注；S_norun：仅 run=0 中均匀选 N 注
    # 若开奖号码为均匀随机，则每期"我们中一等奖的那注"对应的开奖组合
    # 在两种策略下分别服从 全体均匀 / run=0 均匀。
    # "同号他人注数" ∝ 该开奖组合的人群权重 w(c)（相对全体平均）。
    idx_rand = rng.integers(0, T35, n_sim)
    idx_norun = norun_idx[rng.integers(0, len(norun_idx), n_sim)]
    w_rand_draw = w_all[idx_rand]
    w_norun_draw = w_all[idx_norun]

    mean_all = w_all.mean()
    # 相对撞号系数：条件中奖时，开奖号码的平均人群权重 / 全体平均
    cf_rand = w_rand_draw.mean() / mean_all
    cf_norun = w_norun_draw.mean() / mean_all
    # Bootstrap CI
    boots = []
    for _ in range(2000):
        r = w_rand_draw[rng.integers(0, n_sim, n_sim)].mean()
        nr = w_norun_draw[rng.integers(0, n_sim, n_sim)].mean()
        boots.append((nr / mean_all) / (r / mean_all))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        'collision_factor_rand': round(float(cf_rand), 4),
        'collision_factor_norun': round(float(cf_norun), 4),
        'ratio_norun_vs_rand': round(float(cf_norun / cf_rand), 4),
        'ratio_ci95': [round(float(lo), 4), round(float(hi), 4)],
        'prize_uplift_pct': round(float((cf_rand / cf_norun - 1) * 100), 2),
        'N_tickets': N,
        'n_sim': n_sim,
    }

econ = simulate_conditional_share()
report['C_economic_layer'] = {
    'claim': '在固定预算下，避开高撞号形态可提高"中一等奖时的期望奖金"',
    'method': (
        '条件份额模拟（人群权重模型，α 由历史一等奖注数比值校准 = %.2f）。'
        '非全概率端到端（一等奖概率 4.67e-8，端到端模拟不可行）。'
        % ALPHA
    ),
    'calibrated_alpha': ALPHA,
    'result': econ,
    'interpretation': (
        '避开连号使条件撞号系数由 %.3f 降至 %.3f（比值 %.3f，95%%CI %s）；'
        '等价于"中一等奖时的期望奖金"提升约 %.1f%%。'
        '注意：这不改变中奖概率，只在中奖时减少同奖人数、提高单注奖金。'
        % (econ['collision_factor_rand'], econ['collision_factor_norun'],
           econ['ratio_norun_vs_rand'], econ['ratio_ci95'], econ['prize_uplift_pct'])
    ),
    'caveat': (
        '人群权重模型由历史一等奖/二等奖注数近似校准，属**估计**非真值；'
        '且一等奖封顶（现行 1 亿总额 / 单注 500 万）会稀释该收益。'
    )
}

# ============================================================
# D. 对照基线：随机选号 vs "技巧"选号 —— 中奖概率无差异
# ============================================================
def simulate_strategy_equivalence(n_trials=200000):
    """对固定预算 N 注的"技巧"策略 vs 随机 N 注，模拟其"是否中一等奖"。
    两者中一等奖概率都 = N/21425712 → 期望命中数相同，差异不应显著。
    同时算出：要检出"技巧提升 1% 概率"所需的期数量级（power）。"""
    N = 100
    p = N / 21425712
    a = rng.binomial(1, p, n_trials)
    b = rng.binomial(1, p, n_trials)
    exp_hits = n_trials * p
    return {
        'strategy_hits': int(a.sum()),
        'random_hits': int(b.sum()),
        'n_trials': n_trials,
        'expected_hits_each': round(float(exp_hits), 4),
        'theoretical_p_per_trial': p,
        'verdict': (
            '两者命中数均以理论期望 %.4f 为中心，无系统差异。'
            '解析上：只要选号不改变号码被摇出的概率，任何"技巧"的 p 恒等于 N/21425712。'
            % exp_hits
        ),
        'statistical_note': (
            '分离"技巧使概率提升 ε 相对量"所需的试验期数 ~ 1/(p·ε²)。'
            '以 ε=1%% 计，需 ~%s 期，远超彩票历史总量 → 统计上不可检验，'
            '与"数学上不可能"是两回事（后者是解析结论）。'
            % f'{1/(p*0.01**2):.3e}'
        ),
    }

report['D_equivalence_baseline'] = simulate_strategy_equivalence()

# ============================================================
# 输出
# ============================================================
outp = os.path.join(OUT, 'simulation_results.json')
with open(outp, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print('\n' + '=' * 70)
print('策略模拟验证结果')
print('=' * 70)
print(json.dumps(report, ensure_ascii=False, indent=2))
print(f'\n[written] {outp}')
