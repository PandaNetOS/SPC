# -*- coding: utf-8 -*-
import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _load import load_df, out_path
df = load_df()
out=[]; P=out.append
y=df.prize1_winners.values.astype(float)
P("="*78); P("S5a. 过度离散 + 模型族 + HAC稳健标准误"); P("="*78)
P(f"\nmean={y.mean():.3f} var={y.var():.3f} var/mean={y.var()/y.mean():.3f}")

X=sm.add_constant(df[['log_sale','run','heat','sum_z','span_z']].astype(float))
mp=sm.GLM(y,X,family=sm.families.Poisson()).fit()
mu=mp.fittedvalues
aux=((y-mu)**2-y)/mu
ar=sm.OLS(aux,mu).fit()
P(f"过度离散检验 alpha_hat={ar.params.iloc[0]:.4f} t={ar.tvalues.iloc[0]:.2f} p={ar.pvalues.iloc[0]:.2e}")
P(f"  → 显著过度离散 ⇒ Poisson 标准误被低估 {np.sqrt(ar.params.iloc[0]+1):.2f}倍量级")

mq=sm.GLM(y,X,family=sm.families.Poisson()).fit(scale='X2')
P(f"\nQuasiPoisson 尺度因子={mq.scale:.3f}")
P(f"{'var':10s} {'Pois IRR':>10s} {'Pois p':>11s} {'QP p':>11s}")
for c in ['log_sale','run','heat','sum_z','span_z']:
    P(f"{c:10s} {np.exp(mp.params[c]):10.4f} {mp.pvalues[c]:11.2e} {mq.pvalues[c]:11.2e}")

try:
    mnb=sm.NegativeBinomial(y,X).fit(disp=0)
    alpha=mnb.params.iloc[-1]
    P(f"\nNegBin2: alpha={alpha:.4f}  (alpha>0 确认过度离散)")
    P(f"{'var':10s} {'NB IRR':>10s} {'NB p':>11s}")
    for c in ['log_sale','run','heat','sum_z','span_z']:
        P(f"{c:10s} {np.exp(mnb.params[c]):10.4f} {mnb.pvalues[c]:11.2e}")
except Exception as e:
    P(f"NegBin err: {e}")

P(f"\nAIC: Poisson={mp.aic:.1f}")
P(f"\n[HAC Newey-West 稳健标准误]")
for L in [0,5,10,20]:
    m=sm.OLS(y,X).fit(cov_type='HAC',cov_kwds={'maxlags':L})
    P(f"  maxlags={L:2d}: heat coef={m.params['heat']:+.4f} se={m.bse['heat']:.4f} t={m.tvalues['heat']:+.2f} p={m.pvalues['heat']:.2e}")
print("\n".join(out))
open(out_path('s5a_output.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out))
print('[written] ' + out_path('s5a_output.txt'))

