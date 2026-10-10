# -*- coding: utf-8 -*-
import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
from math import comb

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _load import load_df, out_path
df = load_df()
F = df[[f'front_{i}' for i in range(1,6)]].values
n=len(df); out=[]; P=out.append
rng=np.random.default_rng(5)

P("="*78); P("S5b. 精确检验 + 后区条件独立性"); P("="*78)

# 预生成 MC 样本（一次生成，多处复用）
B=5000
idx_all=np.argsort(rng.random((B,n,35)),axis=2)[:,:,:5]+1  # (B,n,5)
P(f"[MC] 生成 {B} × {n} 期随机样本完成")

# 5.3a 前区均匀性
cnt=np.array([(F==i).sum() for i in range(36)],dtype=float)[1:]
exp=cnt.sum()/35; chi_obs=((cnt-exp)**2/exp).sum()
chi_null=np.array([((np.bincount(idx_all[b].ravel(),minlength=36)[1:].astype(float)-exp)**2/exp).sum() for b in range(B)])
P(f"\n[5.3a] 前区均匀性: 观测chi2={chi_obs:.2f} MC精确p={np.mean(chi_null>=chi_obs):.4f} 渐近p={stats.chi2.sf(chi_obs,34):.2e}")

# 5.3b 奇偶分布（超几何理论）
theo=np.array([comb(18,k)*comb(17,5-k)/comb(35,5) for k in range(6)])
eh=np.bincount(df.front_odd.values,minlength=6).astype(float)
chi_odd=((eh-theo*n)**2/(theo*n)).sum()
cn=np.array([((np.bincount((idx_all[b]%2==1).sum(axis=1),minlength=6).astype(float)-theo*n)**2/(theo*n)).sum() for b in range(B)])
P(f"[5.3b] 奇偶分布: 观测={eh.astype(int)} 理论={np.round(theo*n,1)}")
P(f"       chi2={chi_odd:.2f} MC精确p={np.mean(cn>=chi_odd):.4f} 渐近p={stats.chi2.sf(chi_odd,5):.2e}")

# 5.3c 和值（精确组合分布）
# 用 MC 生成和值分布
sums=idx_all.sum(axis=2).ravel()
# 观测和值卡方（分箱）—— 直接用 KS
from scipy.stats import kstest
sum_obs=df.front_sum.values
# 理论 CDF 用 MC 估计
mc_sums=idx_all.sum(axis=2).ravel()
ks=kstest(sum_obs, lambda x: np.searchsorted(np.sort(mc_sums),x)/len(mc_sums))
P(f"[5.3c] 和值 KS(观测 vs MC理论): D={ks.statistic:.4f} p={ks.pvalue:.4f}")

# 5.4 后区条件独立性
P("\n[5.4] 后区条件独立性（给定前区）")
df['sumq']=pd.qcut(df.front_sum,3,labels=['低','中','高'])
df['bq']=pd.qcut(df.back_span,3,labels=['小','中','大'])
ct=pd.crosstab(df.sumq,df.bq); chi2,p,dof,_=stats.chi2_contingency(ct)
P(f"  前区和值档×后区跨度档: chi2={chi2:.2f} dof={dof} p={p:.4f}")
ct2=pd.crosstab(df.front_odd,df.back_span); c2b,p2b,d2,_=stats.chi2_contingency(ct2)
P(f"  前区奇偶×后区跨度: chi2={c2b:.2f} dof={d2} p={p2b:.4f}")
ct3=pd.crosstab(df.front_big,df.back_span); c3,p3,d3,_=stats.chi2_contingency(ct3)
P(f"  前区大号×后区跨度: chi2={c3:.2f} dof={d3} p={p3:.4f}")

def mi(a,b):
    c=pd.crosstab(a,b).values.astype(float); N=c.sum()
    pa=c.sum(1,keepdims=True)/N; pb=c.sum(0,keepdims=True)/N; pab=c/N; mk=pab>0
    return (pab[mk]*np.log(pab[mk]/(pa@pb)[mk])).sum()
P(f"\n  互信息 I(和值;后区跨度)={mi(df.front_sum,df.back_span):.5f} nats")
P(f"  互信息 I(奇偶;后区跨度)={mi(df.front_odd,df.back_span):.5f}")
P(f"  互信息 I(大号;后区跨度)={mi(df.front_big,df.back_span):.5f}")
minull=np.array([mi(df.front_sum, rng.permutation(df.back_span.values)) for _ in range(1000)])
P(f"  置换基准: 均值={minull.mean():.5f} 95分位={np.percentile(minull,95):.5f}")

# 5.7 Ljung-Box
from statsmodels.stats.diagnostic import acorr_ljungbox
P("\n[5.7] Ljung-Box(和值)")
for L in [5,10,20,30]:
    lb=acorr_ljungbox(sum_obs,lags=[L],return_df=True)
    P(f"  lag={L:2d}: Q={lb['lb_stat'].iloc[0]:8.2f} p={lb['lb_pvalue'].iloc[0]:.4f}")

print("\n".join(out))
open(out_path('s5b_output.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out))
print('[written] ' + out_path('s5b_output.txt'))

