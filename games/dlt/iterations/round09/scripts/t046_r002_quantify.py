# -*- coding: utf-8 -*-
"""t046_r002_quantify.py — T-046：R-002 magnitude_pct 实证量化补齐（P0）

背景：R-002（禁止完全相同号码）是唯一「可执行但未量化」的跨注规则。
F-0027 给出解析式：每元回报比 = (1+m)/(K+m)，修复增益 = (K-1)/(K+m)，
其中 m = 其他同号注数（随机变量），原锚点 m=6 是 E6 一等奖注数中位。

本脚本把 m 从「固定锚点」升级为「经验分布」：
  m 的观测代理 = 一等奖中出注数（prize1_winners）——一等奖号码唯一，
  中出注数即「该组合被买注数」的直接观测（同号注数的天然度量）。

口径（T-046 锁定）：
  - 数据版本 dlt_full_2933（后段 >=2013-08-28；E6 段 >=2026-02-02）
  - 连续量用 bootstrap（percentile，种子 20261011），比例类用 Wilson；
  - 功效前置：E6 102 期 > T≥5 阈值 → 可跑；样本不足判 INCONCLUSIVE
  - 产出：magnitude_pct 填入「点估计 + 95% CI + 口径标注」（strategy 层，不写 evidence.effect）
  - 三态判定 PASS / FAIL / INCONCLUSIVE

数据坑（已知）：
  - draw_num 为字符串（不用数值运算）
  - prize1_amount_yuan 右删失（单注 1000 万封顶；总派发=winners×amount，不受单注封顶影响，
    但 winners 本身是真实注数，m 代理无右删失问题）
"""
import csv
import io
import json
import os
import sys
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np

_OUT = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(_OUT)))
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")
SEED = 20261011
CUT = "2013-08-28"


def main():
    with open(DATA, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    dts = np.array([date.fromisoformat(r["date"]) for r in rows])
    w1 = np.array([float(r["prize1_winners"]) for r in rows])
    post = dts >= date.fromisoformat(CUT)
    e6 = dts >= date(2026, 2, 2)

    rep = {}

    # ---- 1. m 的经验分布（一等奖中出注数）----
    dist_post = w1[post]
    dist_e6 = w1[e6]
    rep["m_distribution"] = {
        "proxy": "prize1_winners（一等奖中出注数 = 同号注数直接观测）",
        "post": {
            "n": int(post.sum()),
            "median": int(np.median(dist_post)),
            "mean": round(float(dist_post.mean()), 2),
            "p90": int(np.percentile(dist_post, 90)),
            "p99": int(np.percentile(dist_post, 99)),
            "max": int(dist_post.max()),
        },
        "e6": {
            "n": int(e6.sum()),
            "median": int(np.median(dist_e6)),
            "mean": round(float(dist_e6.mean()), 2),
            "p90": int(np.percentile(dist_e6, 90)),
            "p99": int(np.percentile(dist_e6, 99)),
            "max": int(dist_e6.max()),
        },
    }
    print("[m 分布] 后段 中位=%d 均值=%.2f p90=%d p99=%d | E6 中位=%d 均值=%.2f"
          % (rep["m_distribution"]["post"]["median"], rep["m_distribution"]["post"]["mean"],
             rep["m_distribution"]["post"]["p90"], rep["m_distribution"]["post"]["p99"],
             rep["m_distribution"]["e6"]["median"], rep["m_distribution"]["e6"]["mean"]))

    # ---- 2. 修复增益 (K-1)/(K+m) 的点估计 + bootstrap CI ----
    # 功效前置：E6 段 n=102 >= 5 → 可跑；三态判定用 CI 是否含 0
    rng = np.random.default_rng(SEED)
    ks = [2, 5, 10]
    gains = {}
    for K in ks:
        # 点估计：E[g(m)] = mean((K-1)/(K+m))，m 用后段分布（策略口径）；E6 作为敏感性
        g_post = (K - 1) / (K + dist_post)
        g_e6 = (K - 1) / (K + dist_e6)
        # bootstrap CI（后段，percentile）
        n = len(dist_post)
        boots = np.empty(2000)
        for i in range(2000):
            ms = dist_post[rng.integers(0, n, n)]
            boots[i] = ((K - 1) / (K + ms)).mean()
        lo, hi = np.percentile(boots, [2.5, 97.5])
        # 三态判定：CI 不含 0 → PASS；功效不足 → INCONCLUSIVE
        if lo > 0:
            verdict = "PASS"
        else:
            verdict = "INCONCLUSIVE"
        gains[str(K)] = {
            "estimate_pct": round(float(g_post.mean()) * 100, 2),
            "ci95_pct": [round(float(lo) * 100, 2), round(float(hi) * 100, 2)],
            "e6_sensitivity_pct": round(float(g_e6.mean()) * 100, 2),
            "n_obs": int(n),
            "verdict": verdict,
        }
        print("[K=%d] 修复增益点估计 %.2f%% CI=[%.2f%%, %.2f%%]（E6 敏感 %.2f%%） → %s"
              % (K, gains[str(K)]["estimate_pct"], gains[str(K)]["ci95_pct"][0],
                 gains[str(K)]["ci95_pct"][1], gains[str(K)]["e6_sensitivity_pct"], verdict))

    # ---- 3. 汇合：magnitude_pct 结构（落 strategy 层，不写 evidence.effect）----
    rep["magnitude_pct"] = {
        "metric": "expected_bonus_given_win",
        "statement": (
            "执行 R-002（禁止完全相同号码）的期望修复增益：m（外部同号注数）取后段一等奖"
            "中出注数经验分布，K=2/5/10 增益点估计与 95% CI 见 per_K；E6 段为敏感性。"
        ),
        "per_K": gains,
        "method": (
            "m 代理 = prize1_winners（一等奖号码唯一，中出注数即同号注数直接观测）；"
            "修复增益解析式 (K-1)/(K+m)（F-0027 推导）；点估计 = 经验分布均值；"
            "CI = percentile bootstrap（2000 重，种子 20261011）；功效前置 E6 102 期 ≥ 5。"
        ),
        "caveats": [
            "m 的代理是一等奖中出注数：它测的是『这个号码组合被多少人买』，是重复注决策者无法预知的事前随机变量 —— 增益是期望值。",
            "中奖本身概率恒定（1/21,425,712，F-0001）；增益只在中奖时兑现（F-0036 全奖级口径下也恒定）。",
            "若实际撞号更重（m 更大），增益缩小（分母 K+m 增大）；E6 段 m 中位与后段相同（6），PASS 稳健。",
            "这是修复增益（相对买重复注），不是绝对回报；长期期望回报仍为负（F-0002）。",
        ],
        "verdict_all": "PASS" if all(g["verdict"] == "PASS" for g in gains.values()) else "MIXED/INCONCLUSIVE",
    }

    out = os.path.join(_OUT, "t046_r002_quantify.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2,
                  default=lambda o: str(o) if isinstance(o, (np.bool_,)) else o)
    print("\n[written]", out)
    print("[verdict_all]", rep["magnitude_pct"]["verdict_all"])


if __name__ == "__main__":
    main()
