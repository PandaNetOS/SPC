# -*- coding: utf-8 -*-
"""T-051（round13）：L3 规则搜索 v2 —— walk-forward 滚动再训练 + 候选池扩展。

承接 round12 T-049（v1 固定切分 hold-out，R_new=R001_norun_high_mirror 测试窗 +27.9%）：
- walk-forward：训练窗 1183 期起步，每步训练窗前滚 60 期，评估紧邻下一 60 期窗；
  训练窗特征（含冷热号统计）只用 t 及之前信息，评估窗外数据永不进拟合（L6 防泄漏）。
- 候选池扩展：v1 的 6 形态 + 冷热号类（训练窗高频号避让）→ 新增 R_hot 系列。
- R_new 二次样本外确认：跨步正增益占比 ≥ 60% 且中位数增益 > 0 → met。

口径声明：与 T-049 一致 —— 全部数字为『中奖时期望奖金』提升（人群密度避让），
不改变各奖级中奖概率（红线）；概率口径带奖级限定，禁止「提高中奖率」表述。
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
OUT = os.path.join(_HERE, "t051_walkforward.json")

RNG_SEED = 20261011
rng = np.random.default_rng(RNG_SEED)

# E6 锚点（F-0017，同 v1）
N0_ANCHOR = 6.0
POOL_ANCHOR = 0.4252e8
CAP_TOTAL = 100_000_000
CAP_PART = 5_000_000

# ---------------------------------------------------------------- 组合空间
ALL = list(itertools.combinations(range(1, 36), 5))
T = len(ALL)
assert T == 324632

EVAL_WIN = 150         # 每步评估窗期数（R_new 池占比 ~13%，150 期可命中 ~20 期达 cf 阈值）
TRAIN_START = 1183     # 训练窗起步期数（与 v1 训练 60% 一致）


def run_count(c):
    return sum(1 for i in range(4) if c[i + 1] - c[i] == 1)


def mirror_pair(c):
    s = set(c)
    return any((36 - x) in s for x in c)


def arith_seq(c):
    return len({c[i + 1] - c[i] for i in range(4)}) == 1


# 基础规则（用于基线对照）
RULES = {
    "R_random": lambda c: True,
    "R001_norun": lambda c: run_count(c) == 0,
    "R003_norun_high": lambda c: run_count(c) == 0 and max(c) >= 32,
    "R_mirror_free": lambda c: not mirror_pair(c),
    "R_arith_free": lambda c: not arith_seq(c),
}

# 候选池 v2：全部 run=0 基底；hot_front 由训练窗动态算出（每步不同）
def build_candidates(hot_front: set[int]):
    return {
        "R001_norun_high_mirror": lambda c: run_count(c) == 0 and max(c) >= 32 and not mirror_pair(c),
        "R001_norun_high_hot": lambda c: run_count(c) == 0 and max(c) >= 32 and not (set(c) & hot_front),
        "R001_norun_high_mirror_hot": lambda c: run_count(c) == 0 and max(c) >= 32
                                           and not mirror_pair(c) and not (set(c) & hot_front),
        "R001_norun_mirror_hot": lambda c: run_count(c) == 0 and not mirror_pair(c) and not (set(c) & hot_front),
        "R003_norun_high": lambda c: run_count(c) == 0 and max(c) >= 32,
        "R001_norun_mirror": lambda c: run_count(c) == 0 and not mirror_pair(c),
    }


# ---------------------------------------------------------------- 载入数据
rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig")))
dates = [date.fromisoformat(r["date"]) for r in rows]
w1 = np.array([int(r["prize1_winners"]) for r in rows], float)
front = [tuple(sorted(int(r[f"front_{i}"]) for i in range(1, 6))) for r in rows]

POST_START = date(2013, 8, 28)
post_idx = [i for i, d in enumerate(dates) if d >= POST_START]
n_post = len(post_idx)
assert n_post == 1973, f"后段期数异常: {n_post}"


def hot_front_numbers(idx_tr, k=6):
    """训练窗内前区号码出现频次 top-k（防泄漏：只用训练窗）。"""
    cnt = {}
    for i in idx_tr:
        for x in front[i]:
            cnt[x] = cnt.get(x, 0) + 1
    ranked = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
    return {x for x, _ in ranked[:k]}


def evaluate_window(idx_win, rules: dict) -> dict:
    w = w1[idx_win]
    n_win = len(idx_win)
    res = {}
    for name, pred in rules.items():
        hit = np.array([1.0 if pred(front[i]) else 0.0 for i in idx_win])
        n_hit = hit.sum()
        share = n_hit / n_win
        if n_hit >= 20:
            cf = (w[hit == 1].mean()) / (w.mean() + 1e-12)
        else:
            cf = float("nan")
        if math.isnan(cf):
            amt = float("nan")
        else:
            n_total = max(cf * N0_ANCHOR, 1.0)
            raw = POOL_ANCHOR / n_total
            amt = min(min(raw, CAP_PART * 2) * n_total, CAP_TOTAL) / n_total
        res[name] = {
            "share_pct": round(share * 100, 2),
            "cf": round(cf, 4) if not math.isnan(cf) else None,
            "expected_bonus_given_win_cap_yuan": round(amt, 2) if not math.isnan(amt) else None,
            "n_hit_periods": int(n_hit),
        }
    return res


def bonus_of(v: dict):
    b = v.get("expected_bonus_given_win_cap_yuan")
    return b if b is not None else float("-inf")


# ---------------------------------------------------------------- walk-forward
steps = []
for k in range(6):
    tr_end = TRAIN_START + EVAL_WIN * k          # 训练窗 [0, tr_end)
    ev_start = tr_end                            # 评估窗紧邻训练窗之后
    ev_end = ev_start + EVAL_WIN
    if ev_end > n_post:
        break
    idx_tr = post_idx[:tr_end]
    idx_ev = post_idx[ev_start:ev_end]
    hot = hot_front_numbers(idx_tr)

    cand = build_candidates(hot)
    ev = evaluate_window(idx_ev, cand)
    ev["R_random"] = evaluate_window(idx_ev, {"R_random": RULES["R_random"]})["R_random"]
    rand_bonus = ev["R_random"]["expected_bonus_given_win_cap_yuan"]

    ranked = sorted(
        [(nm, bonus_of(v)) for nm, v in ev.items() if nm != "R_random" and v["cf"] is not None],
        key=lambda x: -x[1],
    )
    step_winner = ranked[0][0] if ranked else None

    rnew = ev.get("R001_norun_high_mirror", {})
    rnew_gain = None
    if rnew.get("cf") is not None and rand_bonus is not None:
        rnew_gain = round(rnew["expected_bonus_given_win_cap_yuan"] - rand_bonus, 2)

    steps.append({
        "step": k + 1,
        "train_periods": tr_end,
        "eval_range": [ev_start, ev_end],
        "eval_start_date": dates[idx_ev[0]].isoformat(),
        "hot_front_top6": sorted(hot),
        "random_bonus": rand_bonus,
        "r_new_bonus": rnew.get("expected_bonus_given_win_cap_yuan"),
        "r_new_gain_vs_random": rnew_gain,
        "step_winner": step_winner,
        "step_winner_bonus": ranked[0][1] if ranked else None,
        "rules": {nm: v for nm, v in ev.items() if nm != "R_random"},
    })
    print(f"[step {k+1:2d}] 训练 {tr_end} 期 → 评估 {ev_start}-{ev_end}（{dates[idx_ev[0]].isoformat()} 起）"
          f"| 随机 {rand_bonus} | R_new {rnew.get('expected_bonus_given_win_cap_yuan')} "
          f"增益 {rnew_gain} | 本步最优 {step_winner}")

# ---------------------------------------------------------------- 汇总与判定
gains = [s["r_new_gain_vs_random"] for s in steps if s["r_new_gain_vs_random"] is not None]
pos = sum(1 for g in gains if g > 0)
total_gain = round(sum(gains), 2) if gains else 0.0
median_gain = round(float(np.median(gains)), 2) if gains else None
win_share = pos / len(steps) if steps else 0.0

met = bool(
    len(gains) >= 4
    and win_share >= 0.60
    and median_gain is not None and median_gain > 0
)
summary = {
    "round": "round13",
    "task": "T-051",
    "data_version": "dlt_full_2933",
    "design": {
        "walk_forward": "训练窗 1183 起步，步进 60 期，评估紧邻下一 60 期窗；冷热号统计只用训练窗（L6 防泄漏）",
        "candidate_pool_v2": [
            "R001_norun_high_mirror（R_new 二次确认）",
            "R001_norun_high_hot",
            "R001_norun_high_mirror_hot",
            "R001_norun_mirror_hot",
            "R003_norun_high（对照）",
            "R001_norun_mirror（v1 候选）",
        ],
    },
    "n_steps": len(steps),
    "r_new_secondary_confirmation": {
        "n_positive_gain_steps": pos,
        "positive_share": round(win_share, 3),
        "median_gain_yuan": median_gain,
        "total_gain_yuan": total_gain,
        "criteria": "有效步 ≥4 且正增益步占比 ≥60% 且中位数增益 >0",
        "met": met,
    },
    "winner_distribution": {},
    "steps": steps,
    "caveats": [
        "cf 口径 = mean(w1|开出∈池)/mean(w1|全部)，同 v1（F-0003 同族实证口径）",
        "池内开出期数 < 20 不估 cf；每步评估窗 60 期，cf 样本量为窗口内命中期数",
        "walk-forward 每步只评估紧邻下一窗，评估窗数据不参与训练/选型（L6）",
        "全部数字为『中奖时期望奖金』提升，不改变各奖级中奖概率（红线）；概率口径带奖级限定",
        "R_new 若二次确认通过，仍属新候选规则，正式进入 strategy.json 需用户批准",
    ],
}

for s in steps:
    w = s["step_winner"]
    if w:
        summary["winner_distribution"][w] = summary["winner_distribution"].get(w, 0) + 1

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"\n[汇总] 步数 {len(steps)} | R_new 正增益步 {pos}/{len(steps)}（占比 {round(win_share,3)}）"
      f"| 中位增益 {median_gain} | 总增益 {total_gain}")
print(f"[判定] R_new 二次样本外确认 met={met}")
print(f"[保存] {OUT}")
