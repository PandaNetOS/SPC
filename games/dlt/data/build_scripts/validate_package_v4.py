# -*- coding: utf-8 -*-
"""validate_package_v4.py — 包完整性校验"""
import io, os, sys, json, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # games/dlt/data/
GAME_DIR = os.path.dirname(DATA_DIR)                                    # games/dlt/
ok = []
fail = []

def check(name, cond, detail=''):
    (ok if cond else fail).append((name, detail))

# 1. manifest 可解析（源包 manifest 保留为 games/dlt/manifest_v4_source.json）
mp = os.path.join(GAME_DIR, 'manifest_v4_source.json')
try:
    M = json.load(open(mp, encoding='utf-8'))
    check('manifest.json 可解析', True, f'version={M["package"]["version"]}')
except Exception as e:
    check('manifest.json 可解析', False, str(e))
    M = None

# 2. 必需文件存在
required = [
    'manifest_v4_source.json', 'rules_history.md',
    'data/raw/dlt_full_2933.csv', 'data/raw/dlt_full_2933.jsonl',
    'data/derived/01_yearly_stats.csv', 'data/derived/02_front_number_frequency.csv',
    'data/derived/03_back_number_frequency.csv', 'data/derived/04_structure_distribution_exact.json',
    'data/derived/05_back_combo_66.csv', 'data/derived/06_acf_lag1to60.csv',
    'data/derived/07_data_quality_report.json', 'data/derived/08_rules_epoch_summary.json',
    'data/tools/_load.py', 'data/tools/validate_data.py',
    'data/build_scripts/build_derived_v4.py',
    'strategy/strategy_simulation.py', 'strategy/simulation_results.json',
]
missing = [f for f in required if not os.path.exists(os.path.join(GAME_DIR, f))]
check('必需文件齐全', not missing, f'missing={missing}' if missing else f'{len(required)} files')

# 3. 数据装载 + 完整性
df = pd.read_csv(os.path.join(DATA_DIR, 'raw/dlt_full_2933.csv'),
                 encoding='utf-8-sig', dtype={'draw_num': str})
check('数据行数 == 2933', len(df) == 2933, f'got {len(df)}')
check('draw_num 首尾', df.draw_num.iloc[0] == '07001' and df.draw_num.iloc[-1] == '26115',
      f'{df.draw_num.iloc[0]} ~ {df.draw_num.iloc[-1]}')
check('日期范围', df.date.iloc[0] == '2007-05-30' and df.date.iloc[-1] == '2026-10-10',
      f'{df.date.iloc[0]} ~ {df.date.iloc[-1]}')
check('无空值', df.isnull().sum().sum() == 0, f'{df.isnull().sum().sum()}')
check('期号唯一', df.draw_num.nunique() == 2933, f'{df.draw_num.nunique()}')

# 4. SHA256 与 manifest 一致
def h(p):
    x = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            x.update(c)
    return x.hexdigest()

if M:
    for rel, expect in M['data']['sha256'].items():
        got = h(os.path.join(DATA_DIR, 'raw', os.path.basename(rel)))
        check(f'SHA256 {rel}', got == expect, got[:16] + (' == ' if got == expect else ' != ') + expect[:16])

# 5. 质量报告与数据一致
q = json.load(open(os.path.join(DATA_DIR, 'derived/07_data_quality_report.json'), encoding='utf-8'))
check('质量报告 n_draws=2933', q['n_draws'] == 2933, f'{q["n_draws"]}')
check('质量报告 draw 范围', q['draw_num_range'] == ['07001', '26115'], str(q['draw_num_range']))
check('派生列 0 不一致', all(v == 0 for v in q['derived_column_mismatch'].values()),
      str(q['derived_column_mismatch']))

# 6. epoch 分段总和 == 2933
ep = json.load(open(os.path.join(DATA_DIR, 'derived/08_rules_epoch_summary.json'), encoding='utf-8'))
tot = sum(e['n_draws'] for e in ep['epochs'])
check('epoch 期数总和 == 2933', tot == 2933, f'{tot}')
check('最新 epoch 为 7 奖级', ep['epochs'][-1]['prize_levels'] == 7,
      f"prize_levels={ep['epochs'][-1]['prize_levels']}")

# 7. 模拟结果 JSON 可解析且关键字段存在
sim = json.load(open(os.path.join(GAME_DIR, 'strategy/simulation_results.json'), encoding='utf-8'))
for k in ['A_probability_layer', 'B1_run_open_rate', 'B2_collision_proxy',
          'C_economic_layer', 'D_equivalence_baseline']:
    check(f'sim 含 {k}', k in sim)
check('sim B2 CI 下界 > 1',
      sim['B2_collision_proxy']['prize1_winners_ratio']['ci95'][0] > 1,
      str(sim['B2_collision_proxy']['prize1_winners_ratio']))

# 8. 精确理论分布总和校验
st = json.load(open(os.path.join(DATA_DIR, 'derived/04_structure_distribution_exact.json'), encoding='utf-8'))
check('前区组合总数 == 324632', st['meta']['front_combinations'] == 324632,
      str(st['meta']['front_combinations']))
check('单注组合总数 == 21425712', st['meta']['total_combinations'] == 21425712,
      str(st['meta']['total_combinations']))
s_theo = sum(st['front_sum']['theoretical_count'])
check('和值理论计数总和 == 324632', s_theo == 324632, str(s_theo))

print('=' * 70)
print(f'通过 {len(ok)} 项，失败 {len(fail)} 项')
print('=' * 70)
for n, d in ok:
    print(f'  [OK]   {n}: {d}')
for n, d in fail:
    print(f'  [FAIL] {n}: {d}')
sys.exit(1 if fail else 0)
