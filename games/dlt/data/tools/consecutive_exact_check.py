# -*- coding: utf-8 -*-
"""S5d: 连号开出率的关键复核 —— 上轮结论 vs 本轮"""
import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
from itertools import combinations
from collections import Counter

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _load import load_df, out_path
df = load_df()
arr=df[[f'front_{i}' for i in range(1,6)]].values
n=len(arr); out=[]; P=out.append

P("="*78)
P("S5d. 连号'开出率'精确复核（上轮称'与理论一致'）")
P("="*78)

# 精确理论分布：枚举全部 C(35,5)=324632 组合
allc=list(combinations(range(1,36),5))
tc=Counter()
for c in allc:
    tc[int((np.diff(c)==1).sum())]+=1
tot=len(allc)
theo=np.array([tc.get(k,0)/tot for k in range(5)])
P(f"\n精确理论分布(枚举 {tot} 组合):")
for k in range(5):
    if theo[k]>0: P(f"  run={k}: {theo[k]:.6f}  ({tc.get(k,0)} 组合)")

runs=np.array([int((np.diff(r)==1).sum()) for r in arr])
obs=np.array([np.sum(runs==k) for k in range(5)])/n
P(f"\n观测分布 (n={n}):")
for k in range(5):
    if theo[k]>0 or obs[k]>0:
        exp_n=theo[k]*n
        se=np.sqrt(n*theo[k]*(1-theo[k]))
        z=(obs[k]*n-exp_n)/se
        P(f"  run={k}: 观测={obs[k]:.6f}({int(obs[k]*n)}) 理论={theo[k]:.6f}({exp_n:.1f}) z={z:+.2f}")

# 卡方检验（run>=2 合并以避开小期望）
obs_c=np.array([np.sum(runs==0), np.sum(runs==1), np.sum(runs>=2)],dtype=float)
theo_c=np.array([theo[0], theo[1], theo[2:].sum()])
exp_c=theo_c*n
chi=((obs_c-exp_c)**2/exp_c).sum()
P(f"\n合并 run=(0,1,>=2) 卡方:")
P(f"  观测={obs_c.astype(int)} 理论={exp_c.round(1)}")
P(f"  chi2={chi:.3f} dof=2 p={stats.chi2.sf(chi,2):.4f}")
# MC 精确
rng=np.random.default_rng(9)
B=20000; cn=np.zeros(B)
for b in range(B):
    idx=np.sort(np.argsort(rng.random((n,35)),axis=1)[:,:5]+1,axis=1)
    rr=(np.diff(idx,axis=1)==1).sum(axis=1)
    oc=np.array([np.sum(rr==0),np.sum(rr==1),np.sum(rr>=2)],dtype=float)
    cn[b]=((oc-exp_c)**2/exp_c).sum()
P(f"  MC精确p={np.mean(cn>=chi):.4f}")

P("\n[关键] run>=2 的'开出率' vs '被选中率'分离:")
P(f"  开出率(run>=2): 观测={obs[2:].sum():.4f} 理论={theo[2:].sum():.4f} 比值={obs[2:].sum()/theo[2:].sum():.3f}")
P(f"  若该比值显著>1 → 连号既'更容易开出'又'更容易被选中'（双重效应）")

# 分期检验（是否早期缺陷所致）
P("\n分期:")
for st,en,name in [(0,957,'2007-2013.08'),(957,n,'2013.08-2026')]:
    rr=runs[st:en]; m=en-st
    o=np.array([np.sum(rr==0),np.sum(rr==1),np.sum(rr>=2)],dtype=float)/m
    e=theo_c
    c=((o*m-e*m)**2/(e*m)).sum()
    P(f"  {name}: n={m} run>=2占比={o[2]:.4f} (理论{theo_c[2]:.4f}) chi2={c:.2f} p={stats.chi2.sf(c,2):.4f}")

# 连号与中奖注数：剔除开出率差异后
P("\n[核心] 控制'开出率'后的连号效应 —— 这才是'避坑'的依据")
df['run_ge2']=(runs>=2).astype(int)
df['log_sale']=np.log(df.sale_yuan)
import statsmodels.api as sm
m=sm.GLM(df.prize1_winners.astype(float),
         sm.add_constant(df[['log_sale','run_ge2']].astype(float)),
         family=sm.families.Poisson()).fit()
P(f"  run_ge2 IRR={np.exp(m.params['run_ge2']):.4f} p={m.pvalues['run_ge2']:.2e}")
P(f"  含义：开出 run>=2 组合的期数，一等奖注数高 {(np.exp(m.params['run_ge2'])-1)*100:.1f}%")
P(f"  解读：run>=2 组合被彩民选择的密度更高 → 撞号概率高")

print("\n".join(out))
open(out_path('s5d_output.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out))
print('[written] ' + out_path('s5d_output.txt'))

