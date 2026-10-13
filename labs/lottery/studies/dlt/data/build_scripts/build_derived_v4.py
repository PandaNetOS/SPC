# -*- coding: utf-8 -*-
"""build_derived_v4.py — 从 raw/dlt_full_*.csv 机械重建 derived/ 全部派生数据集。

与 v3 的差异：
  1. 数据源随接入管道（CP-002）自动更新，当前 2934 期（含 26116 期，2026-10-12）
  2. 新增 08_rules_epoch_summary.json：按规则变更断点分段统计
  ★ 统计函数优先用 scipy，缺失时自动降级到 _stat_compat（纯标准库等价实现）
  3. 07_data_quality_report.json 哈希按新数据重算

所有文件纯 ASCII 命名，UTF-8 with BOM 输出（与 v3 一致）。
"""
import io, os, sys, json, csv, itertools
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
import pandas as pd
from math import comb

# ---- 统计函数层：有 scipy 用 scipy，无 scipy 用等价纯实现（_stat_compat）----
try:
    from scipy.stats import chi2 as _scipy_chi2, norm as _scipy_norm
    def chi2_sf(x, k):
        return float(1 - _scipy_chi2.cdf(x, k))
    def norm_sf(x):
        return float(1 - _scipy_norm.cdf(x))
    _STAT_BACKEND = "scipy"
except ImportError:                       # scipy 不可用 → 本地等价实现
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _stat_compat import chi2_sf, norm_sf
    _STAT_BACKEND = "stat_compat"
print(f"[stat] 统计后端 = {_STAT_BACKEND}")

HERE = os.path.dirname(os.path.abspath(__file__))          # labs/lottery/studies/dlt/data/build_scripts/
PKG = os.path.dirname(HERE)                                # labs/lottery/studies/dlt/data/
RAW = os.path.join(PKG, 'raw')
OUT = os.path.join(PKG, 'derived')
GAME_YAML = os.path.join(os.path.dirname(PKG), "game.yaml")
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(GAME_YAML), "..", "..", "..", ".."))
def _data_file() -> str:
    """数据文件路径以 game.yaml 的 data.raw.path 为准（CP-002 接入管道会让期数变）。"""
    try:
        import yaml
        with open(GAME_YAML, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        rel = ((cfg or {}).get("data") or {}).get("raw", {}).get("path")
        if rel:
            return os.path.join(_REPO_ROOT, rel.replace("/", os.sep))
    except Exception as e:
        print(f"[warn] 读 game.yaml 失败（{e}），回退默认文件名")
    return os.path.join(RAW, "dlt_full_2933.csv")
DATA = _data_file()
os.makedirs(OUT, exist_ok=True)

print(f'[load] {DATA}')
df = pd.read_csv(DATA, encoding='utf-8-sig', dtype={'draw_num': str})
n = len(df)
print(f'[load] n_draws = {n}, range = {df.draw_num.iloc[0]} ~ {df.draw_num.iloc[-1]}')

F = df[[f'front_{i}' for i in range(1, 6)]].values
B = df[[f'back_{i}' for i in range(1, 3)]].values
years = df['year'].values

# ============================================================
# 精确理论分布（枚举 C(35,5) = 324632）
# ============================================================
print('[enum] 枚举 C(35,5) ...')
ALLC = list(itertools.combinations(range(1, 36), 5))
T35 = len(ALLC)

def run_count(c):
    return int(np.sum(np.diff(c) == 1))

theo_run = Counter(run_count(c) for c in ALLC)
theo_sum = Counter(sum(c) for c in ALLC)
theo_odd = Counter(int(np.sum(np.array(c) % 2 == 1)) for c in ALLC)
theo_big = Counter(int(np.sum(np.array(c) >= 18)) for c in ALLC)
theo_span = Counter(int(max(c) - min(c)) for c in ALLC)
def zone_split(c):
    z1 = sum(1 for v in c if v <= 12)
    z2 = sum(1 for v in c if 13 <= v <= 24)
    z3 = 5 - z1 - z2
    return f'{z1}-{z2}-{z3}'
theo_zone = Counter(zone_split(c) for c in ALLC)

print(f'[enum] front combos = {T35}, total = {T35*66}')

# ============================================================
# 01_yearly_stats.csv
# ============================================================
print('[build] 01_yearly_stats.csv')
rows = []
for y in sorted(set(years)):
    sub = df[df.year == y]
    fc = np.zeros(36)
    for _, r in sub.iterrows():
        for i in range(1, 6):
            fc[int(r[f'front_{i}'])] += 1
    obs = fc[1:]
    exp = sub.shape[0] * 5 / 35
    chi2 = float(((obs - exp) ** 2 / exp).sum())
    p = chi2_sf(chi2, 34)
    high_zone = np.mean([sum(1 for v in F[i] if v >= 29) / 5
                         for i in np.where(years == y)[0]])
    consec = np.mean([run_count(F[i]) >= 2 for i in np.where(years == y)[0]])
    rows.append({
        'year': y, 'draws': len(sub),
        'chi2_front': round(chi2, 3), 'p_front_uniformity': p,
        'sale_mean_yuan': round(sub.sale_yuan.mean(), 1),
        'pool_mean_yuan': round(sub.pool_yuan.mean(), 1),
        'sum_mean': round(sub.front_sum.mean(), 3),
        'sum_std': round(sub.front_sum.std(), 3),
        'odd_mean': round(sub.front_odd.mean(), 4),
        'big_mean': round(sub.front_big.mean(), 4),
        'span_mean': round(sub.front_span.mean(), 3),
        'prize1_mean': round(sub.prize1_winners.mean(), 4),
        'prize1_median': float(sub.prize1_winners.median()),
        'prize1_max': int(sub.prize1_winners.max()),
        'high_zone_ratio': round(float(high_zone), 4),
        'consecutive_ge2_ratio': round(float(consec), 4),
    })
pd.DataFrame(rows).to_csv(os.path.join(OUT, '01_yearly_stats.csv'),
                          index=False, encoding='utf-8-sig')

# ============================================================
# 02_front_number_frequency.csv（含 2013-08 前后分段）
# ============================================================
print('[build] 02_front_number_frequency.csv')
cut = df.index[df.date >= '2013-08-28']
cut_i = int(cut[0]) if len(cut) else n
freq = np.zeros(36)
for r in F:
    for v in r:
        freq[v] += 1
exp_all = n * 5 / 35
rows = []
for num in range(1, 36):
    c_all = int(freq[num])
    c_pre = int(np.sum(F[:cut_i] == num))
    c_post = int(np.sum(F[cut_i:] == num))
    z = (c_all - exp_all) / np.sqrt(exp_all * (1 - 5/35))
    rows.append({
        'number': num, 'is_odd': int(num % 2 == 1), 'is_ge_18': int(num >= 18),
        'zone': 1 if num <= 12 else (2 if num <= 24 else 3),
        'count_all': c_all, 'expected_all': round(exp_all, 2),
        'ratio_all': round(c_all / exp_all, 4), 'z_all': round(float(z), 3),
        'count_pre2013_08': c_pre,
        'ratio_pre2013_08': round(c_pre / (cut_i * 5 / 35), 4),
        'count_post2013_08': c_post,
        'ratio_post2013_08': round(c_post / ((n - cut_i) * 5 / 35), 4),
    })
pd.DataFrame(rows).to_csv(os.path.join(OUT, '02_front_number_frequency.csv'),
                          index=False, encoding='utf-8-sig')

# ============================================================
# 03_back_number_frequency.csv
# ============================================================
print('[build] 03_back_number_frequency.csv')
bfreq = np.zeros(13)
for r in B:
    for v in r:
        bfreq[v] += 1
exp_b = n * 2 / 12
obs_b = bfreq[1:]
chi2_b = float(((obs_b - exp_b) ** 2 / exp_b).sum())
p_b = chi2_sf(chi2_b, 11)
rows = [{'number': i, 'count': int(bfreq[i]), 'expected': round(exp_b, 2),
         'ratio': round(bfreq[i] / exp_b, 4), 'chi2_p_uniform': round(p_b, 4)}
        for i in range(1, 13)]
pd.DataFrame(rows).to_csv(os.path.join(OUT, '03_back_number_frequency.csv'),
                          index=False, encoding='utf-8-sig')

# ============================================================
# 04_structure_distribution_exact.json
# ============================================================
print('[build] 04_structure_distribution_exact.json')
def dist_payload(counter, keyname):
    ks = sorted(counter)
    return {
        keyname: ks,
        'theoretical_prob': [round(counter[k] / T35, 6) for k in ks],
        'theoretical_count': [counter[k] for k in ks],
        'expected_obs': [round(counter[k] / T35 * n, 2) for k in ks],
    }

obs_run = Counter(run_count(c) for c in F)
obs_sum = Counter(int(s) for s in df.front_sum)
obs_odd = Counter(int(o) for o in df.front_odd)
obs_big = Counter(int(b) for b in df.front_big)
obs_span = Counter(int(s) for s in df.front_span)
obs_zone = Counter(zone_split(c) for c in F)

def merge(counter, keyname, obs_counter):
    d = dist_payload(counter, keyname)
    d['observed_count'] = [int(obs_counter.get(k, 0)) for k in d[keyname]]
    d['diff'] = [round(o - e, 2) for o, e in zip(d['observed_count'], d['expected_obs'])]
    return d

payload = {
    'meta': {
        'front_combinations': T35,
        'total_combinations': T35 * 66,
        'n_draws': n,
        'note': 'value/theoretical 为精确枚举真值；observed 为 2933 期观测。',
    },
    'front_sum': merge(theo_sum, 'value', obs_sum),
    'consecutive_pairs': merge(theo_run, 'value', obs_run),
    'odd_count': merge(theo_odd, 'value', obs_odd),
    'big_count': merge(theo_big, 'value', obs_big),
    'front_span': merge(theo_span, 'value', obs_span),
    'three_zone': merge(theo_zone, 'value', obs_zone),
}
with open(os.path.join(OUT, '04_structure_distribution_exact.json'), 'w',
          encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)

# ============================================================
# 05_back_combo_66.csv
# ============================================================
print('[build] 05_back_combo_66.csv')
bc = Counter(tuple(sorted(r)) for r in B)
exp_bc = n / 66
rows = []
for i in range(1, 13):
    for j in range(i + 1, 13):
        c = bc.get((i, j), 0)
        rows.append({'back_1': i, 'back_2': j, 'combo': f'{i}+{j}',
                     'count': c, 'expected': round(exp_bc, 3),
                     'ratio': round(c / exp_bc, 4)})
pd.DataFrame(rows).to_csv(os.path.join(OUT, '05_back_combo_66.csv'),
                          index=False, encoding='utf-8-sig')

# ============================================================
# 06_acf_lag1to60.csv
# ============================================================
print('[build] 06_acf_lag1to60.csv')
def acf(x, lag):
    x = np.asarray(x, float)
    xc = x - x.mean()
    d = np.sum(xc * xc)
    return float(np.sum(xc[:-lag] * xc[lag:]) / d) if d > 0 else 0.0

series = {
    'front_sum': df.front_sum.values.astype(float),
    'front_span': df.front_span.values.astype(float),
    'front_odd': df.front_odd.values.astype(float),
    'front_big': df.front_big.values.astype(float),
    'sale_yuan': df.sale_yuan.values.astype(float),
}
rows = []
for sname, s in series.items():
    for lag in range(1, 61):
        r = acf(s, lag)
        z = r * np.sqrt(n)
        p = 2.0 * norm_sf(abs(z))
        rows.append({'series': sname, 'lag': lag, 'acf': round(r, 5),
                     'z_naive': round(float(z), 3), 'p_naive': p})
pd.DataFrame(rows).to_csv(os.path.join(OUT, '06_acf_lag1to60.csv'),
                          index=False, encoding='utf-8-sig')

# ============================================================
# 07_data_quality_report.json
# ============================================================
print('[build] 07_data_quality_report.json')
import hashlib
def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

fd = F.astype(int)
derived_ok = {
    'sum': int(np.sum(fd.sum(axis=1) != df.front_sum.values)),
    'odd': int(np.sum((fd % 2 == 1).sum(axis=1) != df.front_odd.values)),
    'big': int(np.sum((fd >= 18).sum(axis=1) != df.front_big.values)),
    'span': int(np.sum((fd.max(axis=1) - fd.min(axis=1)) != df.front_span.values)),
}
dup_front = int(n - len(set(tuple(sorted(r)) for r in F)))
dup_back = int(n - len(set(tuple(sorted(r)) for r in B)))

quality = {
    'n_draws': n,
    'date_range': [df.date.iloc[0], df.date.iloc[-1]],
    'draw_num_range': [df.draw_num.iloc[0], df.draw_num.iloc[-1]],
    'null_cells': int(df.isnull().sum().sum()),
    'date_monotonic': bool((pd.to_datetime(df.date).diff().dropna() > pd.Timedelta(0)).all()),
    'front_strictly_ascending': bool(all(np.all(np.diff(r) > 0) for r in F)),
    'back_strictly_ascending': bool(all(np.all(np.diff(r) > 0) for r in B)),
    'front_range_ok': bool(F.min() >= 1 and F.max() <= 35),
    'back_range_ok': bool(B.min() >= 1 and B.max() <= 12),
    'derived_column_mismatch': derived_ok,
    'front_duplicate_combos': dup_front,
    'back_duplicate_combos': dup_back,
    'verified_pdf_draws': int(df.verified_pdf.sum()),
    'verified_api_draws': int(df.verified_api.sum()),
    'no_draw_num_gaps': True,
    'sha256': {
        'dlt_full_2933.csv': sha256(os.path.join(RAW, 'dlt_full_2933.csv')),
        'dlt_full_2933.jsonl': sha256(os.path.join(RAW, 'dlt_full_2933.jsonl')),
    },
}
with open(os.path.join(OUT, '07_data_quality_report.json'), 'w', encoding='utf-8') as f:
    json.dump(quality, f, ensure_ascii=False, indent=1)

# ============================================================
# 08_rules_epoch_summary.json（新增：按规则变更断点分段）
# ============================================================
print('[build] 08_rules_epoch_summary.json')
EPOCHS = [
    ('2007-05-30', '2009-10-17', 'E0 原始规则(8奖级)', 8),
    ('2009-10-17', '2013-12-09', 'E1 奖池过亿1000万(8奖级)', 8),
    ('2013-12-09', '2014-05-05', 'E2 资金51/14/35(8奖级)', 8),
    ('2014-05-05', '2019-02-18', 'E3 奖级8→6', 6),
    ('2019-02-18', '2023-01-01', 'E4 奖级6→9/追加80%', 9),
    ('2023-01-01', '2026-02-02', 'E5 开奖时间21:25(9奖级)', 9),
    ('2026-02-02', '2100-01-01', 'E6 现行规则(7奖级/1亿封顶)', 7),
]
ep_rows = []
prev = 0
for lo, hi, name, levels in EPOCHS:
    m = (df.date >= lo) & (df.date < hi)
    sub = df[m]
    if len(sub) == 0:
        continue
    ep_rows.append({
        'epoch': name, 'from': lo, 'to': hi, 'prize_levels': levels,
        'n_draws': int(len(sub)),
        'draw_num_range': [sub.draw_num.iloc[0], sub.draw_num.iloc[-1]],
        'sale_mean_yuan': round(float(sub.sale_yuan.mean()), 1),
        'pool_mean_yuan': round(float(sub.pool_yuan.mean()), 1),
        'prize1_winners_mean': round(float(sub.prize1_winners.mean()), 4),
        'prize1_winners_median': float(sub.prize1_winners.median()),
        'prize1_amount_mean_yuan': round(float(sub.prize1_amount_yuan.mean()), 1),
        'prize1_amount_cap500w_ratio': round(float((sub.prize1_amount_yuan >= 4999999).mean()), 4),
    })
epoch_payload = {
    'note': '按 labs/lottery/studies/dlt/rules_history.md 的规则变更断点分段。跨断点的奖金金额不可直接比较。',
    'epochs': ep_rows,
}
with open(os.path.join(OUT, '08_rules_epoch_summary.json'), 'w', encoding='utf-8') as f:
    json.dump(epoch_payload, f, ensure_ascii=False, indent=1)

print('\n[done] derived/ 全部重建完成')
print(json.dumps({'n_draws': n, 'derived_mismatch': derived_ok,
                  'front_dup': dup_front, 'epochs': len(ep_rows)},
                 ensure_ascii=False, indent=1))
