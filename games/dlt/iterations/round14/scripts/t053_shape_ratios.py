# -*- coding: utf-8 -*-
"""T-053（round14）：F-0041 补强 —— run 细分形态的撞号比复验（后段，CI 收窄）。

F-0041（r10）结论：『随机性错觉』形态撞号溢价仅存在于等差 1 三连（期含三连号 1.1287，
CI [1.0351,1.2243] 显著），其余形态均不显著；但部分形态 n 小（等差 1 三连 n=96）CI 宽。
T-053 补强：把 F-0003 的 run>=2 整体口径**拆分为 run=2 / run>=3**，并在后段 1973 期
（F-0006 变点后的稳健口径）分别估条件撞号比 + bootstrap CI（B=2000，样本更大 → CI 收窄），
同时复验全奇/全偶/镜像对/低区在后段的稳健性。

口径：ratio = mean(w1|开出∈形态) / mean(w1|全部)（F-0003 同族实证口径）。
红线：形态撞号比只反映『中奖注数密度』，不改变任一奖级中奖概率。
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from datetime import date

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "..", ".."))
DATA = os.path.join(_ROOT, "games", "dlt", "data", "raw", "dlt_full_2933.csv")
OUT = os.path.join(_HERE, "t053_shape_ratios.json")

RNG_SEED = 20261011
rng = np.random.default_rng(RNG_SEED)
B = 2000

rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig")))
dates = [date.fromisoformat(r["date"]) for r in rows]
w1 = np.array([int(r["prize1_winners"]) for r in rows], float)
front = [tuple(sorted(int(r[f"front_{i}"]) for i in range(1, 6))) for r in rows]

POST_START = date(2013, 8, 28)
post_idx = [i for i, d in enumerate(dates) if d >= POST_START]
assert len(post_idx) == 1973


def run_count(c):
    return sum(1 for i in range(4) if c[i + 1] - c[i] == 1)


def max_run(c):
    best = cur = 1
    for i in range(4):
        cur = cur + 1 if c[i + 1] - c[i] == 1 else 1
        best = max(best, cur)
    return best


def mirror_pair(c):
    s = set(c)
    return any((36 - x) in s for x in c)


SHAPES = {
    "run_eq_2": lambda c: max_run(c) == 2,          # 恰一对连号
    "run_ge_3": lambda c: max_run(c) >= 3,          # 三连及以上
    "all_odd": lambda c: all(x % 2 == 1 for x in c),
    "all_even": lambda c: all(x % 2 == 0 for x in c),
    "mirror_pair": lambda c: mirror_pair(c),
    "low_zone_le20": lambda c: max(c) <= 20,
    "high_zone_ge32": lambda c: max(c) >= 32,
}


def ratio_ci(idx):
    w = w1[idx]
    n = len(idx)
    out = {}
    for name, pred in SHAPES.items():
        hit = np.array([1.0 if pred(front[i]) else 0.0 for i in idx])
        n_hit = hit.sum()
        if n_hit < 20:
            out[name] = {"n": int(n_hit), "ratio": None, "ci95": None}
            continue
        obs = (w[hit == 1].mean()) / (w.mean() + 1e-12)
        vals = []
        for _ in range(B):
            s = rng.integers(0, n, size=n)
            ws = w[s]
            hs = hit[s]
            if hs.sum() < 5:
                continue
            vals.append((ws[hs == 1].mean()) / (ws.mean() + 1e-12))
        lo, hi = np.percentile(vals, [2.5, 97.5])
        out[name] = {"n": int(n_hit), "ratio": round(float(obs), 4),
                     "ci95": [round(float(lo), 4), round(float(hi), 4)],
                     "significant_gt1": bool(lo > 1.0)}
    return out


post_res = ratio_ci(post_idx)
rep = {
    "round": "round14",
    "task": "T-053",
    "data_version": "dlt_full_2933",
    "scope": "后段 1973 期（2013-08-28 起，F-0006 变点后稳健口径）",
    "method": "run 细分（run=2 / run>=3）+ 形态枚举；条件撞号比 ratio=mean(w1|形态)/mean(w1|全部)，bootstrap B=2000",
    "shapes": post_res,
    "interpretation": {
        "run_ge_3": "若显著（CI 下界>1）：与 F-0041 等差 1 三连显著一致，撞号溢价集中于最长连号",
        "run_eq_2": "若不显著：连号溢价只在三连及以上，两连人群密度未见系统性撞号",
        "all_odd/all_even/mirror/low/high": "F-0041 均不显著的形态在后段复验，防变点后漂移",
    },
    "caveats": [
        "ratio 口径 = 中奖注数密度比（F-0003 同族），不改变任一奖级中奖概率（红线）",
        "后段口径与 F-0041 全样本口径可比性：F-0041 用全 2933 期，本脚本用后段 1973 期（稳健口径）",
        "形态 n<20 不估（样本不足）",
    ],
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=2)
print("[T-053] 后段形态撞号比：")
for k, v in post_res.items():
    print(f"  {k:14s} n={v['n']:4d} ratio={v['ratio']} CI={v['ci95']} 显著>1: {v.get('significant_gt1')}")
print(f"[保存] {OUT}")
