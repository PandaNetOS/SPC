# -*- coding: utf-8 -*-
"""S3b: 变点精细定位 + power + 规则变更查证（精简输出）"""
import sys, io, warnings, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
import ruptures as rpt
from statsmodels.stats.power import GofChisquarePower

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _load import load_df, out_path
df = load_df()
F = df[[f'front_{i}' for i in range(1,6)]].values
n=len(df); out=[]; P=out.append

P("="*78); P("S3b. 变点精细定位"); P("="*78)

def seg_chi(t):
    c1=np.zeros(36); c2=np.zeros(36)
    for r in F[:t]:
        for v in r: c1[v]+=1
    for r in F[t:]:
        for v in r: c2[v]+=1
    tbl=np.vstack([c1[1:],c2[1:]])
    chi2,p,dof,_=stats.chi2_contingency(tbl,correction=False)
    return chi2,p

# 精细扫描 800..1300
ts=np.arange(800,1301,5)
res=np.array([seg_chi(t) for t in ts])
bi=np.argmax(res[:,0])
P(f"\n[精细扫描 800-1300] 最优切点 t={ts[bi]} = {df.date.iloc[ts[bi]]} (期号{df.draw_num.iloc[ts[bi]]}) chi2={res[bi,0]:.1f}")

# 用 ruptures 定位(35维信号, 高敏感)
sig=np.zeros((n,35))
for t,r in enumerate(F):
    for v in r: sig[t,v-1]=1
algo=rpt.Pelt(model="l2").fit(sig)
for pen in [5,10,15,20,30]:
    bk=algo.predict(pen=pen)
    ds=[str(df.date.iloc[b-1]) for b in bk[:-1] if b-1<n]
    P(f"  Pelt(35维) pen={pen:2d}: {len(ds)}个变点, 前几个={ds[:6]}")

# Binseg 强制找 3 个变点
algo2=rpt.Binseg(model="l2").fit(sig)
bk3=algo2.predict(n_bkps=3)
P(f"\n  Binseg 强制3变点: {[str(df.date.iloc[b-1]) for b in bk3[:-1]]}")
bk5=algo2.predict(n_bkps=5)
P(f"  Binseg 强制5变点: {[str(df.date.iloc[b-1]) for b in bk5[:-1]]}")

# 用"高区占比"信号(最直接)
sig2=np.array([[np.mean([v>=29 for v in r])] for r in F])
algo3=rpt.Binseg(model="l2").fit(sig2)
P(f"\n  高区(29-35)占比 Binseg 3变点: {[str(df.date.iloc[b-1]) for b in algo3.predict(n_bkps=3)[:-1]]}")

# 分段最优：2013 vs 2015 谁解释力更强？
P("\n[2013 vs 2015 断点对比]")
for t,label in [(960,'2013-08-28'), (1168,'2015-01-03'), (1050,'2014-04-02')]:
    c,p=seg_chi(t)
    # 前段/后段各自卡方
    P(f"  切点 {label} (t={t}): 2x35列联表 chi2={c:.1f} p={p:.2e}")

# 最优 2013 切点后，前后两段各自的均匀性
for t,label in [(960,'最优2013'), (1168,'2015')]:
    for st,en,sname in [(0,t,'前段'),(t,n,'后段')]:
        cnt=np.zeros(36)
        for r in F[st:en]:
            for v in r: cnt[v]+=1
        obs=cnt[1:]; exp=obs.sum()/35
        chi=((obs-exp)**2/exp).sum(); pv=stats.chi2.sf(chi,34)
        P(f"    最佳切点{label} {sname}({st}-{en}): chi2={chi:.1f} p={pv:.2e}")

# Power analysis
P("\n[Power analysis]")
gp=GofChisquarePower()
P(f"  {'期段':16s} {'n_号码':>7s} {'power(w=0.083)':>15s} {'power(w=0.15)':>14s}")
for y0,y1,name in [(2007,2014,'2007-2014(8年)'),(2008,2013,'2008-2013(核心)'),(2015,2026,'2015-2026')]:
    m=(df.year.astype(int)>=y0)&(df.year.astype(int)<=y1)
    nn=int(m.sum())*5
    p1=gp.power(effect_size=0.0834,nobs=nn,n_bins=35,alpha=0.05)
    p2=gp.power(effect_size=0.15,nobs=nn,n_bins=35,alpha=0.05)
    P(f"  {name:16s} {nn:7d} {p1:15.3f} {p2:14.3f}")

# 检测"缺陷窗口"：逐年高区占比
P("\n[逐年 高区(29-35)号码占比]")
for y,g in df.groupby('year'):
    arr=g[[f'front_{i}' for i in range(1,6)]].values
    hi=np.mean(arr>=29)
    P(f"  {y}: {hi*100:5.1f}%  (均匀理论 20.0%)")

print("\n".join(out))
open(out_path('s3b_output.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out))
print('[written] ' + out_path('s3b_output.txt'))

