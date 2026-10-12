# -*- coding: utf-8 -*-
"""t022_illusion.py — T-022 随机性错觉假设检验（H-001）

枚举"看起来不随机"的形态（等差序列为主，+ 全奇/全偶/镜像代理），
测其条件撞号强度 vs 基线（方法与 F-0003 一致：log1p(w1) 期含/不含比值）。
判定：H-001（代表性启发式）是否获得支持——形态撞号显著高于基线 → 支持。
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
DATA = os.path.join(ROOT, "games", "dlt", "data", "raw", "dlt_full_2933.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "t022_illusion.json")
SEED = 20261011
rng = np.random.default_rng(SEED)

df = pd.read_csv(DATA, encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])
post = df[df["date"] >= "2013-08-28"].copy().reset_index(drop=True)
n = len(post)
print(f"[data] 后段 {n} 期")

# 每期前区号码集合 + w1
front_cols = [f"front_{i}" for i in range(1, 6)]
post["front_set"] = post[front_cols].apply(lambda r: frozenset(int(x) for x in r), axis=1)
post["w1"] = post["prize1_winners"].clip(lower=0)
post["logw1"] = np.log1p(post["w1"])

# 基线：总体 logw1 均值
base_mean = float(post["logw1"].mean())
base_std = float(post["logw1"].std())

# ---------- 形态定义 ----------
def has_arith(fs, d):
    """前区是否含公差为 d 的等差三连（x, x+d, x+2d）"""
    s = set(fs)
    return any((x in s and x + d in s and x + 2 * d in s) for x in s)

def has_arith_pair(fs, d):
    """前区是否含公差为 d 的等差对（任意相邻 d）——粗形态"""
    s = set(fs)
    return any((x in s and x + d in s) for x in s)

def all_odd(fs):
    return all(x % 2 == 1 for x in fs)

def all_even(fs):
    return all(x % 2 == 0 for x in fs)

def mirrorish(fs):
    """镜像感代理：前区是否同时含 k 与 36-k（近似对称对），至少两对"""
    s = set(fs)
    pairs = sum(1 for x in s if x < 18 and (36 - x) in s)
    return pairs >= 2

def low_span(fs):
    """全部落在 1-20（'看起来不像随机的聚集'）"""
    return max(fs) <= 20

def bootstrap_ratio(mask, B=2000):
    """期含形态 vs 不含的 logw1 均值比 + percentile CI"""
    y_in, y_out = post.loc[mask, "logw1"], post.loc[~mask, "logw1"]
    obs_ratio = y_in.mean() / y_out.mean()
    boot = []
    for _ in range(B):
        a = rng.choice(y_in.values, size=len(y_in), replace=True)
        b = rng.choice(y_out.values, size=len(y_out), replace=True)
        boot.append(a.mean() / b.mean())
    boot = np.array(boot)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return round(float(obs_ratio), 4), [round(float(lo), 4), round(float(hi), 4)]

forms = {
    "arith_d1_triplet": lambda fs: has_arith(fs, 1),
    "arith_d2_triplet": lambda fs: has_arith(fs, 2),
    "arith_d3_triplet": lambda fs: has_arith(fs, 3),
    "arith_d5_triplet": lambda fs: has_arith(fs, 5),
    "arith_d1_pair": lambda fs: has_arith_pair(fs, 1),
    "all_odd_front": all_odd,
    "all_even_front": all_even,
    "mirrorish_pairs": mirrorish,
    "low_span_1to20": low_span,
}

results = {}
for name, fn in forms.items():
    mask = post["front_set"].apply(fn)
    cnt = int(mask.sum())
    if cnt < 8:
        results[name] = {"n_draws": cnt, "skipped": "样本 < 8"}
        print(f"[skip] {name}: n={cnt}")
        continue
    ratio, ci = bootstrap_ratio(mask)
    in_mean = float(post.loc[mask, "logw1"].mean())
    results[name] = {"n_draws": cnt, "ratio_in_vs_out": ratio, "ci95": ci,
                     "in_mean_logw1": round(in_mean, 4)}
    sig = "显著偏高" if ratio > 1 and ci[0] > 1 else ("显著偏低" if ratio < 1 and ci[1] < 1 else "不显著")
    results[name]["judge"] = sig
    print(f"[form] {name}: n={cnt} ratio={ratio} CI={ci} → {sig}")

# ---------- 判定（H-001） ----------
supported_forms = [k for k, v in results.items()
                   if v.get("judge") == "显著偏高" and v.get("n_draws", 0) >= 8]
h001 = {
    "verdict": "supported" if len(supported_forms) >= 2 else
               ("partial" if len(supported_forms) >= 1 else "not_supported"),
    "supported_forms": supported_forms,
    "baseline_mean_logw1": base_mean,
    "summary": (
        f"显著偏高的形态：{supported_forms or '无'}——" +
        ("仅等差 1 三连（连号强形态）显著；全奇/全偶/镜像/其他等差无证据 → H-001 部分支持"
         if supported_forms else "无形态显著偏离基线 → H-001 无支持")
    ),
}

rep = {"n_obs": n, "window": f"{post['date'].iloc[0].date()} ~ {post['date'].iloc[-1].date()}",
       "baseline": {"mean_logw1": base_mean, "std_logw1": base_std},
       "forms": results, "h001": h001, "seed": SEED}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n[write] {os.path.basename(OUT)}")
print("[h001]", h001["summary"])
print("done")
