# -*- coding: utf-8 -*-
"""apply_r09_facts.py — r09 结论入库与工作台同步

新增 F-0037（T-046：R-002 magnitude_pct 实证量化）/ F-0038（T-020：逐号偏好结构）；
重校准重记 F-0016 / F-0017 / F-0022 / F-0023（维持，noop_count+1，T-047 NOOP 实战）；
strategy.json R-002 magnitude_pct 填入（T-046 产出，schema 不变）；
TODO T-046 / T-047 / T-020 → done。
"""
import hashlib
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
FACTS = os.path.join(ROOT, "memory", "facts", "FACTS.jsonl")
TODO = os.path.join(ROOT, "memory", "workbench", "TODO.md")
STRATEGY = os.path.join(ROOT, "games", "dlt", "strategy", "strategy.json")
TODAY = "2026-10-11"

S_T046 = "labs/lottery/studies/dlt/iterations/round09/scripts/t046_r002_quantify.py"
S_T020 = "labs/lottery/studies/dlt/iterations/round09/scripts/t020_number_weight.py"
S_T013 = "labs/lottery/studies/dlt/iterations/round09/scripts/t013_recalibrate_r09.py"


def sha256_of(rel):
    return hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()


facts = []
for line in open(FACTS, encoding="utf-8"):
    line = line.strip()
    if line:
        facts.append(json.loads(line))
byid = {o["id"]: o for o in facts}
print(f"[load] {len(facts)} 条")


def new_fact(fid, **kw):
    grade_map = {5: "high", 4: "high", 3: "moderate", 2: "low", 1: "insufficient"}
    base = {
        "id": fid, "game": "dlt", "status": "established", "affects_win_probability": False,
        "confidence": 3, "confidence_basis": "", "claim": "", "category": "methodology",
        "claim_type": "empirical", "evidence": {}, "caveats": [], "established_in": "round09",
        "supersedes": None, "superseded_by": None, "source": None, "tags": [],
        "created_at": TODAY, "updated_at": None, "confidence_grade": grade_map.get(kw.get("confidence", 3), "moderate"),
        "change_type": "initial", "valid_until": None, "recalibrate_every": None,
    }
    base.update(kw)
    base["confidence_grade"] = grade_map.get(base["confidence"], "moderate")
    if fid in byid:  # 幂等：已存在则整体替换为最新版（rehash 场景）
        facts.remove(byid[fid])
        print(f"[re-add] {fid}（幂等替换）")
    facts.append(base)
    byid[fid] = base
    print(f"[new] {fid}: {base['claim'][:70]}...")


# ============ F-0037 T-046：R-002 magnitude_pct 实证量化 ============
new_fact(
    "F-0037", confidence=4,
    confidence_basis=("m 的经验分布来自后段 1973 期一等奖中出注数（同号注数直接观测）；"
                      "修复增益解析式 (K-1)/(K+m)（F-0027 推导）代入经验分布，B=2000 percentile bootstrap，"
                      "CI 不含 0 → PASS（功效前置 E6 102 期 ≥ 5）。"),
    claim=("R-002（禁止完全相同号码）的期望修复增益完成实证量化：m（外部同号注数）取后段一等奖中出注数"
           "经验分布（中位 3、均值 4.86、p90=10、p99=28），K=2/5/10 的修复增益点估计"
           "20.72% / 47.82% / 65.49%（95% CI [20.23,21.23] / [47.09,48.53] / [64.86,66.16]，均不含 0）；"
           "E6 段敏感性 14.92% / 39.51% / 58.25%（E6 m 中位 6 更重 → 增益略低，仍显著）"),
    evidence={
        "method": "m 代理 = prize1_winners（一等奖号码唯一，中出注数即同号注数直接观测）；"
                  "修复增益 (K-1)/(K+m)；点估计 = 经验分布均值；CI = percentile bootstrap（2000，种子 20261011）；"
                  "三态判定 PASS/FAIL/INCONCLUSIVE；功效前置（T≥5）",
        "result_summary": "后段 n=1973：K=2 → +20.72% [20.23,21.23]；K=5 → +47.82% [47.09,48.53]；"
                          "K=10 → +65.49% [64.86,66.16]；E6 n=102 敏感性：14.92%/39.51%/58.25%。verdict_all=PASS。",
        "effect": {
            "m_proxy": "prize1_winners",
            "m_post": {"n": 1973, "median": 3, "mean": 4.86, "p90": 10, "p99": 28, "max": 106},
            "m_e6": {"n": 102, "median": 6, "mean": 6.45, "p90": 10, "p99": 36, "max": 37},
            "gain_pct_K2": 20.72, "gain_ci95_K2": [20.23, 21.23],
            "gain_pct_K5": 47.82, "gain_ci95_K5": [47.09, 48.53],
            "gain_pct_K10": 65.49, "gain_ci95_K10": [64.86, 66.16],
            "e6_sensitivity_pct": [14.92, 39.51, 58.25],
            "verdict_all": "PASS",
        },
        "ci95": None, "p_value": None, "n_observations": 1973,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_T046,
        "source_sha256": sha256_of(S_T046),
    },
    caveats=[
        "m 的代理是一等奖中出注数：它测『这个号码组合被多少人买』，是重复注决策者无法预知的事前随机变量 —— 增益是期望值。",
        "中奖概率恒定（F-0001）；增益只在中奖时兑现（F-0036 全奖级口径下也恒定）。",
        "若实际撞号更重（m 更大），增益缩小；E6 段 m 中位 6 与后段 3 不同 → 后段口径偏乐观，E6 为更保守敏感性。",
        "这是修复增益（相对买重复注），不是绝对回报；长期期望回报仍为负（F-0002）。",
    ],
    source=S_T046, tags=["r002", "cross_ticket", "magnitude", "collision"],
)

# ============ F-0038 T-020：逐号偏好结构 ============
new_fact(
    "F-0038", confidence=3,
    confidence_basis=("后段 1973 期 OLS 对照：逐号项加入后 R² 0.0087 → 0.0453（ΔR²=0.0366），"
                      "30/35 号码系数 |β|>0.05；生日可及段（1-31）与高段（32-35）相对强度差 +0.047"
                      "（CI [-0.011, 0.096] 含 0，不显著）。重尾噪声主导，解释力有限（绝对 R² 低）。"),
    claim=("逐号偏好结构真实存在但精细度高于『生日段』假设：后段逐号相对撞号强度 S_j（1.0=无偏好）"
           "在号码间有明显分异（如 9/11/19 偏高 ≈1.09-1.10，35 偏低 0.89），OLS 逐号项 ΔR²=0.0366 显著；"
           "但生日可及段（1-31）vs 高段（32-35）均值差 +0.047 不显著 → F-0004 的『生日号权重 1.25』"
           "是逐号结构的粗粒度代理，该具体系数缺乏独立支持（方向不推翻，口径需细化）"),
    evidence={
        "method": "逐号相对强度 S_j = mean(log1p(w1)|期含 j)/mean(log1p(w1)|期不含 j)（后段，log1p 抗重尾）；"
                  "区间对比 bootstrap（B=2000）；OLS log1p(w1) ~ 35 号码 indicator + run≥2 + 生日 vs 仅 α+生日",
        "result_summary": "S 1-31 均值 1.005 vs 32-35 0.958（差 +0.047，CI [-0.011, 0.096]）；"
                          "R² 基线 0.0087 → 全模型 0.0453（Δ0.0366）；30/35 系数 |β|>0.05。",
        "effect": {
            "S_1to31_mean": 1.005, "S_32to35_mean": 0.958, "S_diff": 0.047,
            "S_diff_ci95": [-0.0109, 0.0962],
            "r2_base_alpha_birthday": 0.0087, "r2_full_per_number": 0.0453, "r2_delta": 0.0366,
            "n_number_coefs_abs_gt_005": 30, "n_obs": 1973,
            "birthday_segment_supported": False,
        },
        "ci95": None, "p_value": None, "n_observations": 1973,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_T020,
        "source_sha256": sha256_of(S_T020),
    },
    caveats=[
        "绝对 R² 低（0.045）：w1 重尾噪声主导，逐号解释力有限 —— 结论是『存在结构』而非『可预测』。",
        "S_j 是相对撞号强度（被买概率的代理），不涉及开出率与中奖概率（F-0001 恒成立）。",
        "生日段不显著不代表无偏好：偏好结构更精细（如个位数段/吉祥号），单一 1-31 划分太粗。",
        "F-0004 方向（避连号提升中奖时期望奖金）未被推翻；本条目仅细化『生日权重 1.25』这一系数的支持度。",
    ],
    source=S_T020, tags=["number_preference", "collision", "q006", "h002"],
)

# ============ 重校准重记（F-0016/F-0017/F-0022/F-0023）+ NOOP ============
for fid in ("F-0016", "F-0017", "F-0022", "F-0023"):
    o = byid[fid]
    o["updated_at"] = TODAY
    ev = o.setdefault("evidence", {})
    ev["recalibrated_round09"] = {
        "date": TODAY, "result": "maintain",
        "script": S_T013,
        "note": ("动态锚点到期重校准（r09）：E6 一等奖总派发 max 0.9788 亿 < 1 亿、触发 0 次（F-0016）；"
                 "E6 锚点 w1 中位 6 / 派发额中位 0.4252 亿精确复现（F-0017/F-0022）；"
                 "E6 期初奖池 top−bottom er_t 差 +0.017 p=0.311 不显著（F-0023）。全部维持。"
                 f"原确立轮为 {o['established_in']}，重校准维持后刷新确立轮以清除到期告警。"),
    }
    if "recalibrated_round09" not in ev:
        ev["noop_count"] = (ev.get("noop_count") or 0) + 1  # T-047 NOOP 实战：每轮重校准至多 +1（幂等）
    o["established_in"] = "round09"  # 刷新确立轮：validate 按 established_in 判重校准到期
    print(f"[recalibrate+noop] {fid} maintain (noop_count={ev['noop_count']}, established_in→round09)")

# ============ strategy.json：R-002 magnitude_pct 填入 ============
s = json.load(open(STRATEGY, encoding="utf-8"))
for r in s["rules"]:
    if r.get("id") == "R-002":
        evi = r["expected_value_impact"]
        evi["magnitude_pct"] = 65.49
        evi["ci95"] = [64.86, 66.16]
        evi["note"] = ("K=10 注相同号码修复为单注的期望增益（后段口径，m=一等奖中出注数经验分布）；"
                       "K=2 → 20.72% [20.23,21.23]、K=5 → 47.82% [47.09,48.53]（F-0037，round09）")
        break
json.dump(s, open(STRATEGY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("[strategy] R-002 magnitude_pct 已填入（K=10 主数字 + K=2/5 附注）")

# ============ 排序回写 ============
facts.sort(key=lambda o: o["id"])
with open(FACTS, "w", encoding="utf-8") as f:
    for o in facts:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"[write] FACTS.jsonl {len(facts)} 条")

# ============ TODO ============
todo = open(TODO, encoding="utf-8").read()
for tid in ("T-046", "T-047", "T-020"):
    todo = re.sub(rf"- \[ \] \*\*{tid}\*\*", f"- [x] **{tid}**", todo)
open(TODO, "w", encoding="utf-8").write(todo)
print("[update] TODO.md T-046/T-047/T-020 → done")

print("done")
