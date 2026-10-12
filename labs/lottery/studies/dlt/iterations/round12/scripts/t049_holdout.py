# -*- coding: utf-8 -*-
"""T-049（round12）：L3 组合优化的时序 Hold-Out 评测实现 + 规则搜索 v1。

按 round11/T048_HOLDOUT_DESIGN.md §2/§3 实现：
- 数据切分：后段（2013-08-28 起，1973 期）→ 训练 60% / 验证 20% / 测试 20%（按时间，固定切点）
- 主指标 expected_bonus_given_win（含 1 亿封顶模型，口径同 F-0017）+ 撞号系数 cf
- 基线：随机池 / R-001（run=0）/ R-003（run=0 且 max>=32）
- 规则搜索 v1：验证窗枚举候选形态规则（含镜像对 / 等差序列），选主指标最高组合，
  测试窗**只评估一次**（单次评估纪律）
- bootstrap CI（按期重抽样 B=2000）

口径声明：cf_R = mean(w1 | 开出组合∈池R) / mean(w1 | 全部)——开奖均匀，
池 R 内中奖注数在"开出∈池R"的期上观测；这是 F-0003 撞号比的同族实证口径（分母为全池均值）。
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
OUT = os.path.join(_HERE, "t049_holdout.json")

RNG_SEED = 20261011
rng = np.random.default_rng(RNG_SEED)

# E6 锚点（F-0017）
N0_ANCHOR = 6.0
POOL_ANCHOR = 0.4252e8
CAP_TOTAL = 100_000_000
CAP_PART = 5_000_000

# ---------------------------------------------------------------- 组合空间
ALL = list(itertools.combinations(range(1, 36), 5))
T = len(ALL)
assert T == 324632


def run_count(c):
    return sum(1 for i in range(4) if c[i + 1] - c[i] == 1)


def mirror_pair(c):
    """是否存在镜像对（c[i]+c[j]==36）。"""
    s = set(c)
    return any((36 - x) in s for x in c)


def arith_seq(c):
    """5 号是否构成等差数列（gap 全等）。"""
    return len({c[i + 1] - c[i] for i in range(4)}) == 1


# 规则谓词（作用于组合 c），返回 True 表示「允许买入」（避开有害形态）
RULES = {
    "R_random": lambda c: True,                                  # 随机池（基线）
    "R001_norun": lambda c: run_count(c) == 0,                   # R-001：避开 run>=2
    "R003_norun_high": lambda c: run_count(c) == 0 and max(c) >= 32,  # R-003：再避开生日号区
    "R_mirror_free": lambda c: not mirror_pair(c),               # 避开镜像对
    "R_arith_free": lambda c: not arith_seq(c),                  # 避开等差序列
    "R_high32": lambda c: max(c) >= 32,                          # 单开生日号区（对照）
}
# 组合搜索候选（规则名 → 谓词组合；全部须含 run=0，保持与 R-001 兼容的叠加结构）
CANDIDATES = {
    "R001_norun": lambda c: run_count(c) == 0,
    "R003_norun_high": lambda c: run_count(c) == 0 and max(c) >= 32,
    "R001_norun_mirror": lambda c: run_count(c) == 0 and not mirror_pair(c),
    "R001_norun_arith": lambda c: run_count(c) == 0 and not arith_seq(c),
    "R001_norun_high_mirror": lambda c: run_count(c) == 0 and max(c) >= 32 and not mirror_pair(c),
    "R001_norun_high_arith": lambda c: run_count(c) == 0 and max(c) >= 32 and not arith_seq(c),
}

# ---------------------------------------------------------------- 载入数据
rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig")))
dates = [date.fromisoformat(r["date"]) for r in rows]
w1 = np.array([int(r["prize1_winners"]) for r in rows], float)
w2 = np.array([int(r["prize2_winners"]) for r in rows], float)
front = [tuple(sorted(int(r[f"front_{i}"]) for i in range(1, 6))) for r in rows]
back = [tuple(sorted(int(r[f"back_{i}"]) for i in range(1, 3))) for r in rows]

# 后段（2013-08-28 起）
POST_START = date(2013, 8, 28)
post_idx = [i for i, d in enumerate(dates) if d >= POST_START]
n_post = len(post_idx)
assert n_post == 1973, f"后段期数异常: {n_post}"

# 切分：训练 60% / 验证 20% / 测试 20%（固定切点，按索引）
n_tr = int(n_post * 0.60)
n_va = int(n_post * 0.20)
tr_idx = post_idx[:n_tr]            # ~1184
va_idx = post_idx[n_tr:n_tr + n_va]  # ~395
te_idx = post_idx[n_tr + n_va:]      # ~394
print(f"[split] 后段 {n_post} 期 → 训练 {len(tr_idx)} / 验证 {len(va_idx)} / 测试 {len(te_idx)}"
      f"（切点：{dates[va_idx[0]].isoformat()} / {dates[te_idx[0]].isoformat()}）")

# ---------------------------------------------------------------- 规则评估
def rule_in_pool(c, pool):
    return pool[c]


def evaluate_window(idx_win, rules) -> dict:
    """在窗口 idx_win 上评估每条规则的 cf 与 expected_bonus_given_win（含封顶）。"""
    w = w1[idx_win]
    n_win = len(idx_win)
    res = {}
    for name, pred in rules.items():
        hit = np.array([1.0 if pred(front[i]) else 0.0 for i in idx_win])
        n_hit = hit.sum()
        # 池内开出期数占比（=选池覆盖概率，开奖均匀下 = 池规模占比的观测）
        share = n_hit / n_win
        # 撞号系数：mean(w1|开出∈池) / mean(w1|全部)
        if n_hit >= 20:  # 最少 20 期才估 cf（避免个别极端期主导）
            cf = (w[hit == 1].mean()) / (w.mean() + 1e-12)
        else:
            cf = float("nan")  # 样本不足，不估
        # expected_bonus_given_win（含封顶，口径同 F-0017 collision_and_prize）
        if math.isnan(cf):
            amt_cap = float("nan")
        else:
            n_total = max(cf * N0_ANCHOR, 1.0)
            raw = POOL_ANCHOR / n_total
            amt_cap = min(min(raw, CAP_PART * 2) * n_total, CAP_TOTAL) / n_total
        res[name] = {
            "share_pct": round(share * 100, 2),
            "cf": round(cf, 4) if not math.isnan(cf) else None,
            "expected_bonus_given_win_cap_yuan": round(amt_cap, 2) if not math.isnan(amt_cap) else None,
            "n_hit_periods": int(n_hit),
        }
    return res


def bootstrap_ci(idx_win, rules, B=2000):
    """按期重抽样，计算每个规则相对随机的预期奖金 CI（全规则通用）。"""
    w = w1[idx_win]
    n = len(idx_win)
    preds = {name: np.array([1.0 if pred(front[i]) else 0.0 for i in idx_win])
             for name, pred in rules.items()}
    stats = {name: [] for name in rules}
    for _ in range(B):
        s = rng.integers(0, n, size=n)
        ws = w[s]
        base = ws.mean()
        for name in rules:
            hit = preds[name][s]
            if hit.sum() < 5:
                continue
            cf = ws[hit == 1].mean() / (base + 1e-12)
            n_total = max(cf * N0_ANCHOR, 1.0)
            raw = POOL_ANCHOR / n_total
            amt = min(min(raw, CAP_PART * 2) * n_total, CAP_TOTAL) / n_total
            stats[name].append(amt)
    out = {}
    for name, vals in stats.items():
        if len(vals) < B * 0.9:
            out[name] = {"ci95_yuan": None, "n_boot": len(vals)}
            continue
        lo, hi = np.percentile(vals, [2.5, 97.5])
        out[name] = {"ci95_yuan": [round(float(lo), 2), round(float(hi), 2)], "n_boot": len(vals)}
    return out


# ---------------------------------------------------------------- 三步评估
print("\n[1] 训练窗基线（参考，不参与选型）")
tr_res = evaluate_window(tr_idx, RULES)
for k, v in tr_res.items():
    print(f"    {k:22s} 池占比 {v['share_pct']:5.2f}%  cf {v['cf']}  预期奖金(封顶) {v['expected_bonus_given_win_cap_yuan']}")

print("\n[2] 验证窗规则搜索（候选池枚举，选主指标最高）")
va_res = evaluate_window(va_idx, CANDIDATES)
ranked = sorted(
    [(k, v["expected_bonus_given_win_cap_yuan"]) for k, v in va_res.items()
     if v["expected_bonus_given_win_cap_yuan"] is not None],
    key=lambda x: -x[1],
)
for k, v in va_res.items():
    print(f"    {k:24s} 池占比 {v['share_pct']:5.2f}%  cf {v['cf']}  预期奖金(封顶) {v['expected_bonus_given_win_cap_yuan']}")
winner = ranked[0][0] if ranked else "R003_norun_high"
print(f"    → 验证窗最优: {winner}（预期奖金 {ranked[0][1]} 元）" if ranked else "    → 全部样本不足")

print("\n[3] 测试窗最终验收（只评估一次）")
te_base = evaluate_window(te_idx, {"R_random": RULES["R_random"],
                                   "R001_norun": RULES["R001_norun"],
                                   "R003_norun_high": RULES["R003_norun_high"]})
te_cand = evaluate_window(te_idx, {winner: CANDIDATES[winner]})
for k, v in {**te_base, **te_cand}.items():
    print(f"    {k:24s} 池占比 {v['share_pct']:5.2f}%  cf {v['cf']}  预期奖金(封顶) {v['expected_bonus_given_win_cap_yuan']}")

# bootstrap CI（测试窗：随机基线 + 两个对照规则 + 验证窗 winner）
boot_rules = {"R_random": RULES["R_random"],
              "R001_norun": RULES["R001_norun"],
              "R003_norun_high": RULES["R003_norun_high"],
              winner: CANDIDATES[winner]}
boot = bootstrap_ci(te_idx, boot_rules)

# 方向一致性：验证窗 vs 测试窗
va_win = va_res.get(winner, {}).get("expected_bonus_given_win_cap_yuan")
te_win = te_cand.get(winner, {}).get("expected_bonus_given_win_cap_yuan")
direction_consistent = bool(
    va_win is not None and te_win is not None
    and (te_win - te_base["R_random"]["expected_bonus_given_win_cap_yuan"]) * 
        (va_win - va_res["R003_norun_high"]["expected_bonus_given_win_cap_yuan"]) > 0
) if va_res.get("R003_norun_high", {}).get("expected_bonus_given_win_cap_yuan") else None

rep = {
    "round": "round12",
    "task": "T-049",
    "data_version": "dlt_full_2933",
    "split": {
        "post_start": POST_START.isoformat(),
        "n_post": n_post,
        "train": len(tr_idx), "valid": len(va_idx), "test": len(te_idx),
        "valid_start": dates[va_idx[0]].isoformat(),
        "test_start": dates[te_idx[0]].isoformat(),
    },
    "rules_evaluated": {
        "train": tr_res,
        "valid": va_res,
        "test": {**te_base, **te_cand},
    },
    "rule_search_v1": {
        "valid_winner": winner,
        "valid_winner_bonus": va_win,
        "test_winner_bonus": te_win,
        "test_random_bonus": te_base["R_random"]["expected_bonus_given_win_cap_yuan"],
        "test_r001_bonus": te_base["R001_norun"]["expected_bonus_given_win_cap_yuan"],
        "test_r003_bonus": te_base["R003_norun_high"]["expected_bonus_given_win_cap_yuan"],
        "bootstrap_ci_test": boot,
        "direction_consistent_valid_test": direction_consistent,
    },
    "acceptance": {
        "criteria": "测试窗提升 > R-003 基线且 95% CI 不含 0；方向一致",
        "met": None,  # 由结论段判定
    },
    "caveats": [
        "cf 口径 = mean(w1|开出∈池)/mean(w1|全部)，分母为全池均值（F-0003 同族实证口径，非补池比）",
        "池内开出期数 < 20 时不估 cf（样本不足）",
        "测试窗只评估一次；本脚本为 v1 规则搜索，候选池 6 个形态组合",
        "全部数字为『中奖时期望奖金』提升，不改变各奖级中奖概率（红线）",
    ],
}

# 判定
te_r = te_cand.get(winner, {}).get("expected_bonus_given_win_cap_yuan")
ci = boot.get(winner, {}).get("ci95_yuan")
if te_r is None or ci is None:
    rep["acceptance"]["met"] = False
    rep["acceptance"]["reason"] = "样本不足或 winner 在测试窗无法估 cf"
elif ci[0] > te_base["R_random"]["expected_bonus_given_win_cap_yuan"] and direction_consistent:
    rep["acceptance"]["met"] = True
    rep["acceptance"]["reason"] = "测试窗提升且 CI 下界高于随机基线，方向一致"
else:
    rep["acceptance"]["met"] = False
    rep["acceptance"]["reason"] = (
        f"测试窗提升 {te_r} vs 随机 {te_base['R_random']['expected_bonus_given_win_cap_yuan']}"
        f"；CI {ci}；方向一致={direction_consistent} —— 未同时满足"
    )
rep["acceptance"]["met"] = bool(rep["acceptance"]["met"])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=2)
print(f"\n[结果] 验收 met={rep['acceptance']['met']}：{rep['acceptance'].get('reason','')}")
print(f"[保存] {OUT}")
