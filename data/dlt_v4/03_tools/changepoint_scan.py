# -*- coding: utf-8 -*-
"""S3: 挑战点2 —— 变点检测 + 2015 断点混杂变量排查"""
import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
import ruptures as rpt

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _load import load_df, out_path
df = load_df()
F = df[[f'front_{i}' for i in range(1,6)]].values
B = df[[f'back_{i}' for i in range(1,3)]].values
out=[]; P=out.append
rng = np.random.default_rng(2026)

P("="*78)
P("S3. 挑战点2：2015 断点是否为最优？替代切点/混杂是否排除？")
P("="*78)

n = len(df)

# ---------- 3.1 逐年卡方（复核上轮）----------
P("\n[3.1] 逐年前区卡方（复核）:")
rows=[]
for y, g in df.groupby('year'):
    cnt = np.zeros(36)
    for r in g[[f'front_{i}' for i in range(1,6)]].values:
        for v in r: cnt[v]+=1
    obs = cnt[1:]; exp = obs.sum()/35
    chi = ((obs-exp)**2/exp).sum()
    pv = stats.chi2.sf(chi, 34)
    rows.append((y, len(g), chi, pv))
yr = pd.DataFrame(rows, columns=['year','n','chi2','p'])
P(yr.to_string(index=False))

# ---------- 3.2 手工切点扫描：所有候选断点 ----------
P("\n[3.2] 切点扫描：对每个候选切点 t，比较前后两段号码分布的 2×35 列联表卡方")
# 用"号码使用计数"构造 2×35 表
def seg_chi(t):
    c1 = np.zeros(36); c2 = np.zeros(36)
    for r in F[:t]:
        for v in r: c1[v]+=1
    for r in F[t:]:
        for v in r: c2[v]+=1
    tbl = np.vstack([c1[1:], c2[1:]])
    chi2, p, dof, _ = stats.chi2_contingency(tbl, correction=False)
    return chi2, p

# 从第 300 期扫到 n-300
ts = np.arange(300, n-300, 10)
res = np.array([seg_chi(t) for t in ts])
best_i = np.argmax(res[:,0])
P(f"    扫描范围 t=300..{n-300} (步长10), 共 {len(ts)} 个候选")
P(f"    最大分段卡方出现在 t={ts[best_i]} 即日期 {df.date.iloc[ts[best_i]]} "
  f"(期号 {df.draw_num.iloc[ts[best_i]]})  chi2={res[best_i,0]:.1f} p={res[best_i,1]:.2e}")

# Top10 切点
order = np.argsort(-res[:,0])[:12]
P("\n    卡方最大的 12 个候选切点:")
for i in order:
    P(f"      t={ts[i]:4d}  {df.date.iloc[ts[i]]}  期号={str(df.draw_num.iloc[ts[i]]):>5s}  "
      f"chi2={res[i,0]:7.1f}  p={res[i,1]:.2e}")

# 2015-01-01 对应的 t
t2015 = int((df.date < '2015-01-01').sum())
P(f"\n    2015-01-01 切点对应 t={t2015} (期号 {df.draw_num.iloc[t2015]}, {df.date.iloc[t2015]})")
c15, p15 = seg_chi(t2015)
P(f"    该切点 chi2={c15:.1f} p={p15:.2e}")
P(f"    在全部候选中排名第 {int((res[:,0]>c15).sum())+1} / {len(ts)}")

# ---------- 3.3 ruptures 正式变点检测 ----------
P("\n[3.3] ruptures 变点检测（Pelt, 多模型）:")
# 构造信号：每期号码的"高区(29-35)占比"，最能反映早期偏倚
sig = np.array([np.mean([v>=29 for v in r]) for r in F]).reshape(-1,1)
for pen in [3, 5, 10, 20]:
    algo = rpt.Pelt(model="l2").fit(sig)
    bkps = algo.predict(pen=pen)
    bkps_dates = [df.date.iloc[b-1] if b-1 < n else 'end' for b in bkps]
    P(f"    Pelt l2 pen={pen:2d}: 变点期序={bkps[:-1]}  日期={bkps_dates[:-1]}")

# 用和值信号
sig2 = df.front_sum.values.astype(float).reshape(-1,1)
for pen in [5, 10, 20]:
    algo = rpt.Pelt(model="l2").fit(sig2)
    bkps = algo.predict(pen=pen)
    P(f"    Pelt(和值) pen={pen}: 变点={[str(df.date.iloc[b-1]) if b-1<n else 'end' for b in bkps[:-1]]}")

# 用号码分布向量 35维信号
sig3 = np.zeros((n, 35))
for t, r in enumerate(F):
    for v in r: sig3[t, v-1] = 1
for pen in [50, 100, 200]:
    algo = rpt.Pelt(model="l2").fit(sig3)
    bkps = algo.predict(pen=pen)
    P(f"    Pelt(35维号码) pen={pen}: 变点={[str(df.date.iloc[b-1]) if b-1<n else 'end' for b in bkps[:-1]]}")

# ---------- 3.4 Power analysis：各年检验力 ----------
P("\n[3.4] Power analysis：给定各年期数，检测中等效应(Cohen w=0.15)的检验力")
from statsmodels.stats.power import GofChisquarePower
gp = GofChisquarePower()
for y, g in df.groupby('year'):
    n_eff = len(g)*5  # 每年号码抽取数
    try:
        pw = gp.power(effect_size=0.0834, nobs=n_eff, n_bins=35, alpha=0.05)
    except Exception:
        pw = np.nan
    P(f"    {y}: 期数={len(g):3d} 号码数={n_eff:4d} power(w=0.083)={pw:.3f}")
P("    注：若早期与后期 power 相近，则'早期显著后期不显著'不能归因于样本量")

# ---------- 3.5 混杂变量：早期/晚期的其它变化 ----------
P("\n[3.5] 2015 前后其它系统性差异（混杂候选）:")
df['period'] = np.where(df.year <= 2014, '早期(07-14)', '后期(15-26)')
metrics = ['sale_yuan','pool_yuan','prize1_winners','front_sum','front_span',
           'front_odd','front_big','prize2_winners']
P(f"    {'指标':14s} {'早期均值':>14s} {'后期均值':>14s} {'t':>8s} {'p':>10s}")
for m in metrics:
    a = df[df.period=='早期(07-14)'][m]; b = df[df.period=='后期(15-26)'][m]
    t, p = stats.ttest_ind(a, b, equal_var=False)
    P(f"    {m:14s} {a.mean():14.3f} {b.mean():14.3f} {t:+8.2f} {p:10.2e}")

# 这些差异与"号码偏倚"是否相关？检查号码分布变化是否伴随其它变化
P("\n    关键检验：号码偏倚断点 与 其它指标断点 是否同位？")
for m in ['sale_yuan','prize1_winners','front_sum','front_span','front_odd','front_big']:
    s = df[m].values.astype(float).reshape(-1,1)
    algo = rpt.Pelt(model="l2").fit(s)
    bkps = algo.predict(pen=10)
    bd = [str(df.date.iloc[b-1]) if b-1<n else 'end' for b in bkps[:-1]]
    P(f"    {m:16s} 变点={bd}")

print("\n".join(out))
open(out_path('s3_output.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out))
print('[written] ' + out_path('s3_output.txt'))

