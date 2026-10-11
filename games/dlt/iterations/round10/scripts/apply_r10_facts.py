# -*- coding: utf-8 -*-
"""apply_r10_facts.py — r10 结论入库与工作台同步

新增 F-0039（T-050：全奖级概率表）/ F-0040（T-021：销量外生性）/ F-0041（T-022：形态撞号 H-001）；
F-0001 表述校正（奖级限定，不改结论）；
F-0028/F-0029/F-0031 重校准重记（维持 + noop_count）；
H-001 → partial；Q-005 / Q-017 → answered；TODO T-050/T-021/T-022 → done。
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
OQ = os.path.join(ROOT, "memory", "workbench", "OPEN_QUESTIONS.md")
HYP = os.path.join(ROOT, "memory", "workbench", "HYPOTHESES.md")
TODO = os.path.join(ROOT, "memory", "workbench", "TODO.md")
TODAY = "2026-10-11"

S_T050 = "games/dlt/iterations/round10/scripts/t050_calibration.py"
S_T021 = "games/dlt/iterations/round10/scripts/t021_sales_endogeneity.py"
S_T022 = "games/dlt/iterations/round10/scripts/t022_illusion.py"
S_T028 = "games/dlt/iterations/round10/scripts/t028_recalibrate_r10.py"


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
        "claim_type": "empirical", "evidence": {}, "caveats": [], "established_in": "round10",
        "supersedes": None, "superseded_by": None, "source": None, "tags": [],
        "created_at": TODAY, "updated_at": None, "confidence_grade": "moderate",
        "change_type": "initial", "valid_until": None, "recalibrate_every": None,
    }
    base.update(kw)
    base["confidence_grade"] = grade_map.get(base["confidence"], "moderate")
    if fid in byid:
        facts.remove(byid[fid])
        print(f"[re-add] {fid}（幂等替换）")
    facts.append(base)
    byid[fid] = base
    print(f"[new] {fid}: {base['claim'][:70]}...")


# ============ F-0039 T-050：全奖级概率表 ============
new_fact(
    "F-0039", confidence=5, category="prize_mechanism",
    confidence_basis=("解析计算（组合计数）：C(35,5)×C(12,2)=21,425,712，逐奖级中出注数由组合恒等式精确给出，"
                      "全奖级合计 1,429,197——确定性结果，非估计。"),
    claim=("大乐透现行（E6）9 个奖级的中奖概率精确值：一等奖 5+2 为 1/21,425,712（≈4.67e-08）；"
           "任一奖级（1-9 等）合计 1,429,197/21,425,712 ≈ 6.67%（约 1/15）；"
           "1-7 等累计 ≈ 1/1,497（0.067%）。『中奖概率』必须带奖级限定，不得与一等奖概率混用（r10 口径规范）"),
    evidence={
        "method": "解析组合计数：C(35,5)×C(12,2)；逐奖级匹配恒等式（5+2 / 5+1 / 5+0 / 4+2 / 4+1 / 3+2 / 4+0 / 3+1,2+2 / 3+0,2+1,1+2,0+2）",
        "result_summary": "总组合 21,425,712；九等奖 1,287,281 → 任一奖级合计 1,429,197（6.67%，1/15）；"
                          "八等奖 127,600（1/168）；七等奖 6,750（1/3,174）；……一等奖 1（1/21,425,712）。",
        "effect": {
            "total_combinations": 21425712,
            "first_prize": {"match": "5+2", "n": 1, "prob": "1/21425712"},
            "any_prize": {"n": 1429197, "prob": "≈1/15", "percent": 6.67},
            "prize_1to7": {"n": 14316, "prob": "≈1/1497", "percent": 0.067},
            "n_prize_levels": 9,
        },
        "ci95": None, "p_value": None, "n_observations": None,
        "data_version": None, "rules_epoch": "E6", "script": S_T050,
        "source_sha256": sha256_of(S_T050),
    },
    caveats=[
        "奖级表依现行 E6 规则（2019 改版后 9 奖级）；若规则变更需重核。",
        "中奖概率与选号无关（任何号码组合每奖级概率相同）；本条目仅校正口径，不改变 F-0001 结论。",
        "1-7 等累计口径仅为用户提问时使用的口径；对外一律使用全奖级（1-9 等）合计。",
    ],
    source=S_T050, tags=["probability", "prize_mechanism", "caliber", "r050"],
)

# ============ F-0040 T-021：销量外生性 ============
new_fact(
    "F-0040", confidence=3, category="robustness",
    confidence_basis=("后段 1973 期 Granger 因果（滞后 1-3）+ 含/不含销量两版注数模型对照；"
                      "Granger 检验功效有限（滞后阶选择、单期噪声），方向证据强但非因果定论。"),
    claim=("销量是内生变量但**不驱动一等奖中出注数**：Granger 检验（后段 1973 期，一阶差分口径）"
           "奖池→销量显著（滞后 1-3 p=0.008/0.0023/0.0208）、销量→注数不显著（p≈0.48-0.83）、"
           "奖池→注数显著（p≈0）；含销量后注数模型中奖池系数变化 −0.00111（<0.02）稳定 "
           "→ F-0003 注数模型无内生性偏误（销量不混杂连号效应估计）"),
    evidence={
        "method": "ADF 平稳性 + 双变量 Granger（手写 F 检验，滞后 1-3）+ 差分 OLS 对照（含/不含销量）",
        "result_summary": "ADF：logw1/sale/pool 差分后平稳；Granger：pool→sale 显著、sale→logw1 不显著、"
                          "pool→logw1 显著、logw1→sale 不显著；pool 系数含销量后 −0.00111 稳定。",
        "effect": {
            "granger_pool_to_sale": {"lag1": 0.008, "lag2": 0.0023, "lag3": 0.0208},
            "granger_sale_to_w1": {"lag1": 0.757, "lag2": 0.8273, "lag3": 0.4786},
            "granger_pool_to_w1": {"lag1": 0.0, "lag2": 0.0, "lag3": 0.0},
            "pool_coef_change_with_sale": -0.00111,
            "sales_is_endogenous": True,
            "sales_drives_w1": False,
        },
        "ci95": None, "p_value": None, "n_observations": 1973,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_T021,
        "source_sha256": sha256_of(S_T021),
    },
    caveats=[
        "Granger 是预测因果关系，非结构性因果；『销量不驱动注数』限于一等奖注数（w1）代理口径。",
        "销量本身确实内生（奖池驱动）——若未来研究把销量当独立变量需注意；对 F-0003 的注数模型无碍。",
        "含销量后模型 R² 差异极小；结论不改变 F-0003 的方向与量级。",
    ],
    source=S_T021, tags=["sales", "endogeneity", "robustness", "q005"],
)

# ============ F-0041 T-022：形态撞号（H-001） ============
new_fact(
    "F-0041", confidence=3, category="collision",
    confidence_basis=("后段 1973 期形态条件撞号强度（期含/不含 logw1 均值比）+ percentile bootstrap（2000）；"
                      "样本量足（等差 1 三连 n=96），其他形态 n≥20；功效一般，结论为『有/无证据』。"),
    claim=("『随机性错觉』形态的撞号溢价仅存在于三连号（等差 1）：期含三连号撞号比 1.1287（CI [1.0351, 1.2243]）"
           "显著高于基线；等差 2/3/5 三连、等差对、全奇、全偶、镜像对、低区聚集（≤20）均不显著 "
           "→ H-001（代表性启发式）部分支持：人群偏好集中于最显眼的连号形态，而非广义『不随机』形态"),
    evidence={
        "method": "形态枚举（等差三连 d=1/2/3/5、等差对、全奇/全偶、镜像对、低区聚集）+ 条件撞号比 bootstrap（B=2000，种子 20261011）",
        "result_summary": "等差 1 三连 n=96 ratio=1.1287 CI=[1.0351,1.2243] 显著；等差 2 三连 0.9136、等差 3 1.0142、"
                          "等差 5 0.9854、全奇 1.1274、全偶 0.915、镜像 0.9059、低区 1.0431 均不显著（CI 含 1）。",
        "effect": {
            "arith_d1_triplet": {"n": 96, "ratio": 1.1287, "ci95": [1.0351, 1.2243], "sig": True},
            "arith_d2_triplet": {"n": 110, "ratio": 0.9136, "sig": False},
            "arith_d3_triplet": {"n": 86, "ratio": 1.0142, "sig": False},
            "arith_d5_triplet": {"n": 70, "ratio": 0.9854, "sig": False},
            "all_odd_front": {"n": 47, "ratio": 1.1274, "sig": False},
            "all_even_front": {"n": 36, "ratio": 0.915, "sig": False},
            "mirrorish_pairs": {"n": 20, "ratio": 0.9059, "sig": False},
            "low_span_1to20": {"n": 122, "ratio": 1.0431, "sig": False},
            "h001_verdict": "partial",
        },
        "ci95": None, "p_value": None, "n_observations": 1973,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_T022,
        "source_sha256": sha256_of(S_T022),
    },
    caveats=[
        "等差 1 三连与 F-0003 的连号效应高度重叠（是 run≥2 的更强子形态），增量信息有限。",
        "其他形态 CI 较宽（n=20-122），『不显著』≠『无效应』——功效不足。",
        "撞号强度是相对结构（被买概率代理），不涉及开出率与中奖概率（F-0001 恒成立）。",
        "无法观测个体动机（L6 归因边界）：相关性不能证明『代表性启发式』这一心理机制。",
    ],
    source=S_T022, tags=["illusion", "collision", "h001", "pattern"],
)

# ============ F-0001 表述校正（奖级限定） ============
f1 = byid["F-0001"]
f1["claim"] = ("任何选号方式都不能改变单注各奖级的中奖概率"
               "（一等奖 1/21,425,712；任一奖级合计约 1/15；均解析可证）")
f1["updated_at"] = TODAY
f1.setdefault("evidence", {})["calibration_note_r10"] = {
    "date": TODAY, "note": "表述校正（T-050）：原『单注中奖概率』歧义为集合概念，现明确为『各奖级』+ 一等奖/任一奖级双口径。结论不变。",
}
print("[update] F-0001 表述校正（奖级限定，结论不变）")

# ============ F-0028/F-0029/F-0031 重校准重记 ============
for fid in ("F-0028", "F-0029", "F-0031"):
    o = byid[fid]
    o["updated_at"] = TODAY
    ev = o.setdefault("evidence", {})
    ev["recalibrated_round10"] = {
        "date": TODAY, "result": "maintain",
        "script": S_T028,
        "note": ("动态锚点到期重校准（r10）：F-0031 奖池 AR(1) slope=0.9994 SE=0.00064 ACF≈0.999 精确复现；"
                 "F-0028/F-0029 模拟参数无机制变化（E6 规则未改），E6 锚点 w1 中位 6 复现、后段连号撞号比复核稳定。"
                 f"原确立轮为 {o['established_in']}，重校准维持后刷新。"),
    }
    if "recalibrated_round10" not in ev or True:
        pass
    ev["noop_count"] = (ev.get("noop_count") or 0) + 1
    o["established_in"] = "round10"
    print(f"[recalibrate+noop] {fid} maintain (noop_count={ev['noop_count']})")

# ============ 排序回写 ============
facts.sort(key=lambda o: o["id"])
with open(FACTS, "w", encoding="utf-8") as f:
    for o in facts:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"[write] FACTS.jsonl {len(facts)} 条")

# ============ HYPOTHESES ============
hyp = open(HYP, encoding="utf-8").read()
hyp = hyp.replace("| **状态** | `unverified` |\n| **假设** | 彩民避开连号是因为认为\"连号看起来不像随机\"",
                  "| **状态** | `partial`（r10：F-0041 仅三连号形态有撞号溢价，其他『不随机』形态无证据） |\n| **假设** | 彩民避开连号是因为认为\"连号看起来不像随机\"")
open(HYP, "w", encoding="utf-8").write(hyp)
print("[update] HYPOTHESES.md H-001 → partial")

# ============ OPEN_QUESTIONS ============
oq = open(OQ, encoding="utf-8").read()
oq = oq.replace("> 当前 open：**Q-005 / Q-006 / Q-008 / Q-011 / Q-015 / Q-016**（6 个）",
                "> 当前 open：**Q-006 / Q-008 / Q-011 / Q-015 / Q-016**（5 个）")
oq = oq.replace("（r04 新增 Q-013~Q-016：前段数据取证 / 外部核对 / 机选代理 / 固定奖加成核验；r05 清偿 Q-012；r07 清偿 Q-013 / Q-014）",
                "（r04 新增 Q-013~Q-016：前段数据取证 / 外部核对 / 机选代理 / 固定奖加成核验；r05 清偿 Q-012；r07 清偿 Q-013 / Q-014；r10 清偿 Q-005 / Q-017）")
oq = oq.replace("| **状态** | `open` |\n| **由何而起** | F-0012 的 `caveats`；原任务书 T5.1 |",
                "| **状态** | `answered` → **F-0040**（r10：销量内生但不驱动注数，F-0003 无偏误） |\n| **由何而起** | F-0012 的 `caveats`；原任务书 T5.1 |")
oq = oq.replace("| **状态** | `open`（体系缺陷诊断） |",
                "| **状态** | `answered` → **T-050**（r10：概率口径标注根治已落地，validate 新增『概率口径』检查项） |")
open(OQ, "w", encoding="utf-8").write(oq)
print("[update] OPEN_QUESTIONS.md Q-005 / Q-017 → answered")

# ============ TODO ============
todo = open(TODO, encoding="utf-8").read()
for tid in ("T-050", "T-021", "T-022"):
    todo = re.sub(rf"- \[ \] \*\*{tid}\*\*", f"- [x] **{tid}**", todo)
open(TODO, "w", encoding="utf-8").write(todo)
print("[update] TODO.md T-050/T-021/T-022 → done")

print("done")
