# -*- coding: utf-8 -*-
"""S4: 挑战点3 —— ACF 存活 lag 的置换检验 + 日历对应"""
import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _load import load_df, out_path
df = load_df()
n=len(df); out=[]; P=out.append
rng=np.random.default_rng(2026)

P("="*78)
P("S4. 挑战点3：ACF 存活 lag(6/10/18/23) 是真周期还是假阳性？")
P("="*78)

series = {
 'front_sum': df.front_sum.values.astype(float),
 'front_odd': df.front_odd.values.astype(float),
 'front_big': df.front_big.values.astype(float),
 'front_span': df.front_span.values.astype(float),
 'back_span': df.back_span.values.astype(float),
}

def acf_vals(x, maxlag=30):
    x = x - x.mean()
    denom = (x**2).sum()
    return np.array([ (x[:n-k]*x[k:]).sum()/denom for k in range(1, maxlag+1) ])

# ---------- 4.1 复核 FDR ----------
P("\n[4.1] 复核 BH-FDR（5指标 × lag1-30 = 150检验）:")
allp=[]; keys=[]
for name, s in series.items():
    r = acf_vals(s)
    for k, rk in enumerate(r, start=1):
        # 双侧 p（大样本近似: se=1/sqrt(n)）
        se = 1/np.sqrt(n)
        z = rk/se
        pv = 2*stats.norm.sf(abs(z))
        allp.append(pv); keys.append((name,k,rk))
allp=np.array(allp)
rej, padj, _, _ = multipletests(allp, alpha=0.05, method='fdr_bh')
P(f"    单检验名义显著(p<0.05): {int((allp<0.05).sum())} / 150")
P(f"    BH-FDR 存活: {int(rej.sum())}")
for i in np.where(rej)[0]:
    P(f"      {keys[i][0]} lag={keys[i][1]} r={keys[i][2]:+.4f} p={allp[i]:.2e} p_adj={padj[i]:.4f}")

# ---------- 4.2 置换检验：打乱序列重算 ACF，看存活 lag 的假阳性率 ----------
P("\n[4.2] 置换检验（打乱序列 10000 次，检验每个具体 lag 的 r 分布）:")
# 对每个 lag，用打乱序列得到 r 的 null 分布
for name, lagset in [('front_sum',[1,6,10,18,23]), ('front_big',[6])]:
    s = series[name]
    obs = acf_vals(s)
    null = np.zeros((10000, len(lagset)))
    for b in range(10000):
        sp = rng.permutation(s)
        rb = acf_vals(sp)
        null[b] = [rb[l-1] for l in lagset]
    P(f"\n    [{name}]")
    for j, l in enumerate(lagset):
        r_obs = obs[l-1]
        # 双侧经验 p
        p_emp = np.mean(np.abs(null[:,j]) >= abs(r_obs))
        p_norm = 2*stats.norm.sf(abs(r_obs)*np.sqrt(n))
        P(f"      lag={l:2d}: r_obs={r_obs:+.4f} 经验p(置换)={p_emp:.4f} 正态近似p={p_norm:.4f}")
    # 多重比较：对 lagset 做 max-|r| 联合检验
    maxnull = np.abs(null).max(axis=1)
    P(f"      联合检验(max|r|): 观测最大|r|={np.abs([obs[l-1] for l in lagset]).max():.4f} "
      f"家族经验p={np.mean(maxnull >= np.abs([obs[l-1] for l in lagset]).max()):.4f}")

# ---------- 4.3 lag 与开奖日历的对应 ----------
P("\n[4.3] lag 与 '每周3期' 开奖节奏的对应:")
P(f"    lag=6  = 2周(6期);  lag=10 ≈ 3周+1期;  lag=18 = 6周;  lag=23 ≈ 7.67周")
P(f"    若真存在'周内效应'，lag=3(同周次日)、lag=7、lag=14 应该更强——但:")
for name, s in series.items():
    r = acf_vals(s)
    P(f"      {name:11s}: lag3={r[2]:+.4f} lag6={r[5]:+.4f} lag7={r[6]:+.4f} lag14={r[13]:+.4f} lag21={r[20]:+.4f}")
P("    → 若 lag3/7/14 不显著而 lag6/10/18/23 '显著'，则与开奖日历无关（日历周期是3/7）")

# ---------- 4.4 分段稳定性（关键判据）----------
P("\n[4.4] 存活 lag 的分段稳定性（若真周期，各段应同向）:")
seg_bounds=[(0,586),(586,1172),(1172,1758),(1758,2344),(2344,n)]
for name, lags in [('front_sum',[6,10,18,23]), ('front_big',[6])]:
    s=series[name]
    P(f"    [{name}]")
    for l in lags:
        vals=[]
        for st,en in seg_bounds:
            ss=s[st:en]; ss=ss-ss.mean()
            d=(ss**2).sum()
            if len(ss)>l:
                vals.append((ss[:-l]*ss[l:]).sum()/d)
        P(f"      lag={l:2d}: 各段 r = [" + ", ".join(f"{v:+.3f}" for v in vals) + 
          f"]  同号段数={sum(1 for v in vals if v>0)}/{len(vals)}")

# ---------- 4.5 用 lag 做实际预测：能否盈利 ----------
P("\n[4.5] 用'显著' lag 做预测的实际效果（回归 y_t ~ y_{t-lag}）:")
for name, lags in [('front_sum',[6,10,18,23]),('front_big',[6])]:
    s=series[name]; P(f"    [{name}]")
    for l in lags:
        x=s[:-l]; y=s[l:]
        sl,ic,r,p,se=stats.linregress(x,y)
        # 样本外 R² （前半训练后半测试）
        m=len(x)//2
        sl2,ic2,_,_,_=stats.linregress(x[:m],y[:m])
        pred=sl2*x[m:]+ic2
        sse=((y[m:]-pred)**2).sum(); sst=((y[m:]-y[m:].mean())**2).sum()
        P(f"      lag={l:2d}: 全样本R²={r**2:.5f} 前半训练→后半测试 R²={1-sse/sst:+.5f}")

print("\n".join(out))
open(out_path('s4_output.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out))
print('[written] ' + out_path('s4_output.txt'))

