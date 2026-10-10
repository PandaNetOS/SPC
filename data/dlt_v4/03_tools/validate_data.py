# -*- coding: utf-8 -*-
"""Stage 1: 数据完整性 + 可复现性独立校验"""
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _load import load_df, out_path
import numpy as np, pandas as pd
from scipy import stats
from collections import Counter

df = load_df()   # 从包内 01_data/ 读取；draw_num 已强制 str
out = []
P = out.append

P("=" * 78)
P("S1. 数据完整性与可复现性独立校验")
P("=" * 78)
P(f"shape = {df.shape}")
P(f"draw range = {df.draw_num.iloc[0]} .. {df.draw_num.iloc[-1]}")
P(f"date range = {df.date.iloc[0]} .. {df.date.iloc[-1]}")

# 1. 空值
P(f"\n[1] 空值总数 = {int(df.isna().sum().sum())}")

# 2. 日期单调
d = pd.to_datetime(df.date)
P(f"[2] 日期单调递增 = {bool(d.is_monotonic_increasing)}; 重复日期数 = {int(d.duplicated().sum())}")

# 3. 期号唯一
P(f"[3] 期号唯一数 = {df.draw_num.nunique()} / {len(df)}")

# 4. 前区升序&范围
F = df[[f'front_{i}' for i in range(1, 6)]].values
B = df[[f'back_{i}' for i in range(1, 3)]].values
asc_f = bool(np.all(np.diff(F, axis=1) > 0))
asc_b = bool(np.all(np.diff(B, axis=1) > 0))
P(f"[4] 前区严格升序={asc_f} 范围合规={bool(F.min()>=1 and F.max()<=35)}; "
  f"后区严格升序={asc_b} 范围合规={bool(B.min()>=1 and B.max()<=12)}")

# 5. 派生列与主数据一致性（关键：验证派生字段没算错）
chk_sum = int((F.sum(axis=1) != df.front_sum.values).sum())
chk_odd = int(((F % 2 == 1).sum(axis=1) != df.front_odd.values).sum())
chk_big = int(((F >= 18).sum(axis=1) != df.front_big.values).sum())
chk_span = int((F.max(axis=1) - F.min(axis=1) != df.front_span.values).sum())
chk_bspan = int((B.max(axis=1) - B.min(axis=1) != df.back_span.values).sum())
P(f"[5] 派生列不一致数: sum={chk_sum} odd={chk_odd} big={chk_big} span={chk_span} bspan={chk_bspan}")

# 6. 组合重复
fc = Counter(map(tuple, F))
dup_front = sum(1 for v in fc.values() if v > 1)
dup_draws_front = sum(v for v in fc.values() if v > 1)
bc = Counter(map(tuple, B))
dup_back = sum(1 for v in bc.values() if v > 1)
full = Counter(map(tuple, np.hstack([F, B])))
dup_full = sum(v for v in full.values() if v > 1)
P(f"[6] 前区重复组合数={dup_front} 涉及期数={dup_draws_front} (唯一={len(fc)})")
P(f"    后区重复组合数={dup_back} (唯一={len(bc)}/66)")
P(f"    前区+后区整体重复期数={dup_full}")

# 7. 碰撞期望（同口径复核）
n = len(df); N = 324632
exp_collisions = n * (n - 1) / 2 / N
P(f"[7] 前区碰撞期望对数={exp_collisions:.2f}  观测重复对(组内两两)="
  f"{sum(v*(v-1)//2 for v in fc.values() if v>1)}")

# 8. 官方校验覆盖
P(f"[8] verified_pdf=True: {int(df.verified_pdf.sum())} 期; verified_api=True: {int(df.verified_api.sum())} 期")
vp = df[df.verified_pdf == True]
vu = df[df.verified_api == True]
if len(vp): P(f"    pdf校验区间: {vp.date.min()} ~ {vp.date.max()}")
if len(vu): P(f"    api校验区间: {vu.date.min()} ~ {vu.date.max()}")

# 9. 开奖日 weekday 分布
P("\n[9] 开奖星期分布:")
for k, v in df.weekday.value_counts().sort_index().items():
    P(f"    {k}: {v}")

# 10. 销售额/奖池异常值
P(f"\n[10] sale_yuan: min={df.sale_yuan.min():,.0f} max={df.sale_yuan.max():,.0f} "
  f"nan={int(df.sale_yuan.isna().sum())} zero={int((df.sale_yuan<=0).sum())}")
P(f"     pool_yuan: min={df.pool_yuan.min():,.0f} max={df.pool_yuan.max():,.0f} "
  f"nan={int(df.pool_yuan.isna().sum())}")

# 11. 奖级完整性
P(f"\n[11] prize1_winners: nan={int(df.prize1_winners.isna().sum())} "
  f"mean={df.prize1_winners.mean():.3f} median={df.prize1_winners.median()} max={df.prize1_winners.max()}")
P(f"     prize1 封顶500万占比 = {(df.prize1_amount_yuan>=5e6).mean()*100:.1f}%")

# 12. 销售额分段核验（2020疫情期）
P("\n[12] 各年期数:")
for y, g in df.groupby('year'):
    P(f"    {y}: {len(g)}期  sale均值={g.sale_yuan.mean()/1e8:.2f}亿")

json.dump({"status": "ok", "shape": list(df.shape)}, open(out_path('s1_result.json'),'w'))
print("\n".join(out))
open(out_path('s1_output.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out))
print('[written] ' + out_path('s1_output.txt'))

