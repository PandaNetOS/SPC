# -*- coding: utf-8 -*-
"""T-054（round14）：walk-forward 每步 bootstrap CI（T-051 遗留补强）。

T-051 的 5 步 walk-forward 中，R_new（R001_norun_high_mirror）有 4 步可估 cf（点估计）；
第 5 步命中不足 20 期未估。本脚本复用 T-051 的滚动结构，对每步 R_new 相对随机的
『中奖时期望奖金增益』做期重抽样 bootstrap CI（B=1000），并把跨步增益汇总为
『显著正增益步数 / 总有效步数』，作为 F-0045 判据的不确定性补充。

口径与红线：同 F-0045 —— 数字为『中奖时期望奖金』提升（人群密度避让），
不改变任一奖级中奖概率。
"""
from __future__ import annotations

import csv
import io
import itertools
import json
import math
import os
import sys
from datetime import date

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "..", ".."))
DATA = os.path.join(_ROOT, "games", "dlt", "data", "raw", "dlt_full_2933.csv")
OUT = os.path.join(_HERE, "t054_walkforward_ci.json")

RNG_SEED = 20261011
rng = np.random.default_rng(RNG_SEED)
B = 1000
EVAL_WIN = 150
TRAIN_START = 1183

N0_ANCHOR = 6.0
POOL_ANCHOR = 0.4252e8
CAP_TOTAL = 100_000_000
CAP_PART = 5_000_000

ALL = list(itertools.combinations(range(1, 36), 5))
T = len(ALL)


def run_count(c):
    return sum(1 for i in range(4) if c[i + 1] - c[i] == 1)


def mirror_pair(c):
    s = set(c)
    return any((36 - x) in s for x in c)


R_NEW = lambda c: run_count(c) == 0 and max(c) >= 32 and not mirror_pair(c)  # noqa: E731

rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig")))
dates = [date.fromisoformat(r["date"]) for r in rows]
w1 = np.array([int(r["prize1_winners"]) for r in rows], float)
front = [tuple(sorted(int(r[f"front_{i}"]) for i in range(1, 6))) for r in rows]

POST_START = date(2013, 8, 28)
post_idx = [i for i, d in enumerate(dates) if d >= POST_START]
n_post = len(post_idx)
assert n_post == 1973


def capped_bonus(cf):
    n_total = max(cf * N0_ANCHOR, 1.0)
    raw = POOL_ANCHOR / n_total
    return min(min(raw, CAP_PART * 2) * n_total, CAP_TOTAL) / n_total


def gain_of(idx_ev, resample=None):
    """R_new 相对随机的期望奖金增益（可选：bootstrap 重抽样索引）。"""
    idx = idx_ev if resample is None else [idx_ev[i] for i in resample]
    w = w1[idx]
    n = len(idx)
    hit_rn = np.array([1.0 if R_NEW(front[i]) else 0.0 for i in idx])
    if hit_rn.sum() < 5:
        return None
    base = w.mean() + 1e-12
    cf_rn = (w[hit_rn == 1].mean()) / base
    gain = capped_bonus(cf_rn) - capped_bonus(1.0)
    return float(gain)


steps = []
for k in range(6):
    tr_end = TRAIN_START + EVAL_WIN * k
    ev_start, ev_end = tr_end, tr_end + EVAL_WIN
    if ev_end > n_post:
        break
    idx_ev = post_idx[ev_start:ev_end]
    pt = gain_of(idx_ev)
    vals = []
    for _ in range(B):
        s = rng.integers(0, len(idx_ev), size=len(idx_ev))
        g = gain_of(idx_ev, resample=s)
        if g is not None:
            vals.append(g)
    ci = None
    if len(vals) >= B * 0.9:
        lo, hi = np.percentile(vals, [2.5, 97.5])
        ci = [round(float(lo), 2), round(float(hi), 2)]
    steps.append({
        "step": k + 1,
        "eval_range": [ev_start, ev_end],
        "eval_start_date": dates[idx_ev[0]].isoformat(),
        "r_new_gain_point_yuan": round(pt, 2) if pt is not None else None,
        "gain_ci95_yuan": ci,
        "n_boot": len(vals),
        "significant_gt0": bool(ci and ci[0] > 0),
    })
    print(f"[step {k+1}] 增益点估计 {pt} | CI {ci} | 显著>0: {bool(ci and ci[0] > 0)}")

sig = sum(1 for s in steps if s.get("significant_gt0"))
rep = {
    "round": "round14",
    "task": "T-054",
    "data_version": "dlt_full_2933",
    "method": "复用 T-051 滚动结构（训练窗 1183 起步、步进 150、评估紧邻 150 期窗）；每步期重抽样 B=1000",
    "steps": steps,
    "summary": {
        "n_steps": len(steps),
        "n_significant_positive": sig,
        "share": round(sig / len(steps), 3) if steps else None,
    },
    "caveats": [
        "bootstrap 按期重抽样（同 T-049）；单步窗口 150 期，R_new 命中约 20 期，CI 宽度反映小样本现实",
        "增益口径 = 中奖时期望奖金（含 1 亿封顶），不改变任一奖级中奖概率（红线）",
        "显著>0 判据：95% CI 下界 >0",
    ],
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=2)
print(f"[保存] {OUT}（显著正增益 {sig}/{len(steps)}）")
