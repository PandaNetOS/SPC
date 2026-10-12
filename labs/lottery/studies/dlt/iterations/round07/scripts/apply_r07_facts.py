# -*- coding: utf-8 -*-
"""apply_r07_facts.py — r07 结论入库与工作台同步

新增 F-0033（T-014 根因定位）/ F-0034（T-015 外部核对）/ F-0035（T-016 节假日无证据）；
F-0004 / F-0005 重校准重记（recalibrated round07，锚点维持）；
Q-013 / Q-014 → answered；H-006 → refuted；TODO T-014/T-015/T-016 → done。
"""
import sys, io, os, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
FACTS = os.path.join(ROOT, "memory", "facts", "FACTS.jsonl")
OQ = os.path.join(ROOT, "memory", "workbench", "OPEN_QUESTIONS.md")
HYP = os.path.join(ROOT, "memory", "workbench", "HYPOTHESES.md")
TODO = os.path.join(ROOT, "memory", "workbench", "TODO.md")
TODAY = "2026-10-11"

S_T014 = "labs/lottery/studies/dlt/iterations/round07/scripts/t014_forensics.py"
S_T015 = "labs/lottery/studies/dlt/iterations/round07/scripts/t015_external.py"
S_T016 = "labs/lottery/studies/dlt/iterations/round07/scripts/t016_holiday.py"
S_T013 = "labs/lottery/studies/dlt/iterations/round07/scripts/t013_recalibrate.py"

facts = []
for line in open(FACTS, encoding="utf-8"):
    line = line.strip()
    if line:
        facts.append(json.loads(line))
byid = {o["id"]: o for o in facts}
print(f"[load] {len(facts)} 条")

def new_fact(fid, **kw):
    base = {
        "id": fid, "game": "dlt", "status": "established", "affects_win_probability": False,
        "confidence": 4, "confidence_basis": "", "claim": "", "category": "methodology",
        "claim_type": "empirical", "evidence": {}, "caveats": [], "established_in": "round07",
        "supersedes": None, "superseded_by": None, "source": None, "tags": [],
        "created_at": TODAY, "updated_at": None, "confidence_grade": "medium",
        "change_type": "initial", "valid_until": None, "recalibrate_every": None,
    }
    base.update(kw)
    facts.append(base)
    byid[fid] = base
    print(f"[new] {fid}: {base['claim'][:60]}...")

# ============ F-0033 T-014 根因定位 ============
new_fact(
    "F-0033", confidence=4,
    confidence_basis=("观测核算：三条恒等式逐期核对 + 12 期绝对违规（派发超最宽松资金池上界）+ 分年时间结构对照。"
                      "非解析结论，但硬违规与方向证据支撑『w1 偏大』。"),
    claim=("前段（<2013-08）数据不自洽的根因进一步定位：注数-销售额异常区间为 2008-01~2013-08"
           "（2007 全年正常，反推均价 2.93 元/注；2008-2013 连续 6 年 <2 元）；12 期一等奖派发总额"
           "超过『奖池+当期销售额×51%』最宽松上界（12074 期 w1=50、派发 2.56 亿 vs 资金池 1.16 亿，"
           "反推需 10.7 亿注）→ 前段一等奖中出注数 w1 系统性偏大（或销售额记录偏小）；"
           "号码分布异常（2007-2014 偏高端，z=-1.55~-4.55，2015 起收敛）与注数-销售额异常"
           "（2008-2013）时间结构不同 → 两者不同源"),
    evidence={
        "method": "三条恒等式逐期核对（E1 w2/w1≡20 人群模型无关恒等式；E2 反推注数×票价≤销售额；"
                  "E3 派发总额≤资金池）+ 滚动窗口时间轴 + 分年号码分布对照",
        "result_summary": (
            "E1：前段 w2/w1 聚合 18.66（理论 20，z=-2.82），后段 20.78（z=+3.66），逐期中位 15.0 vs 23.3；"
            "E2：前段 293/960 期反推注数>sale/2，后段 486/1973（逐期被重尾噪声主导，判定须用聚合口径）；"
            "E3：前段 12 期派发超『pool+sale×0.51』最宽松上界（后段 0 期），如 12074 期 w1=50、派发 2.56 亿 vs 资金池 1.16 亿；"
            "分年：2007 均价 2.93（正常）→ 2008-2013 均价 1.62-1.85（异常）→ 2014 起 ≥2.19（恢复）；"
            "号码分布 2007 z=-2.42 已偏 → 2014 z=-1.55 → 2015 +0.80 收敛。"),
        "effect": {
            "e1_pre_ratio": 18.658, "e1_post_ratio": 20.779, "e1_theory": 20.0,
            "e2_pre_violation_over_sale2": 0.305, "e2_post_violation_over_sale2": 0.246,
            "e3_loose_violations_pre": 12, "e3_loose_violations_post": 0,
            "worst_case_12074": {"w1": 50, "payout_yi": 2.56, "fund_pool_yi": 1.16, "implied_tickets_required": 10.7},
            "anomaly_window_sale_ticket": "2008-01 ~ 2013-08（2007 正常）",
            "anomaly_window_number_distribution": "2007 ~ 2014（2015 起收敛）",
            "two_anomalies_different_source": True,
        },
        "ci95": None, "p_value": None, "n_observations": 2933,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_T014,
    },
    caveats=[
        "无法 100% 区分『w1 记录偏大』vs『销售额记录偏小』——方向证据（低销售额期 w1 异常大、派发超资金池）偏向 w1 偏大，但非定论。",
        "号码分布异常（2007-2014）成因仍不可归因（L6：无摇奖设备/球组记录）。",
        "E2 逐期违规率两段相似，被 w1 重尾/零值噪声主导 → 逐期口径不可单独用于判定；聚合/分组口径为准。",
        "E0 单注封顶实为 800 万（07077 期触顶 8,009,863 元），r04 的『超封顶』111 期系规则误读，已修正——不影响 F-0019 主体。",
        "F-0003 全样本 1.3603 与 F-0018 中位数比 1.5 含异常段 → 官方发布口径必须注明『历史口径』；策略引用一律用后段（F-0022 已执行）。",
    ],
    source=S_T014, tags=["forensics", "data_quality", "l3"],
)

# ============ F-0034 T-015 外部核对 ============
new_fact(
    "F-0034", confidence=5,
    confidence_basis=("102 期外部样本（覆盖 2008/2012/2013 三个区间）与本地 CSV 逐期精确比对，"
                      "号码/一等奖注数/销售额 100% 一致——确定性比对，非推断。"),
    claim=("本地 CSV 前段数据与外部独立公开源（500.com 历史库，转载自官方开奖公告）102/102 期完全一致"
           "（2008 年 40 期 + 2012 年 33 期 + 2013 年 29 期；号码 7 位 + 一等奖注数 + 销售额，含 12074 w1=50、"
           "13017 w1=39 等极端期）→ 本地转录/录入环节无错，前段不自洽定位到公共数据链路上游"
           "（官方公告原始口径或公共转载源），排除『本仓库转录损坏』这一根因"),
    evidence={
        "method": "外部抓取（datachart.500.com/dlt/history/newinc/history.php，2026-10-11）+ 逐期精确比对",
        "result_summary": "n=102，一致 102，不一致 0，一致率 100.00%；无缺失期、无差异期。",
        "effect": {"n_external": 102, "n_match": 102, "n_mismatch": 0, "match_rate": 1.0,
                    "windows": ["08001-08100", "12060-12100", "13001-13040"]},
        "ci95": None, "p_value": None, "n_observations": 102,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_T015,
    },
    caveats=[
        "500.com 与本地可能同源转载（同取官方公告），不能视为对官方原始公告的独立验证；但足以排除『本地录入/转录损坏』。",
        "2007/2009-2011 段未抽样（判定方向已定：公共链路上游口径问题）；如需 100% 覆盖可续抓。",
        "前段 verified_pdf/api 覆盖率 0%（2020 起 100%）——前段公共转载源本身未经官方核验标记。",
    ],
    source=S_T015, tags=["external_check", "data_quality", "l3"],
)

# ============ F-0035 T-016 节假日窗口 ============
new_fact(
    "F-0035", confidence=4,
    confidence_basis=("同一数据、四种口径（run≥1/run≥2 × 均值/加总）交叉复验：窗口连号比均 ≈1.0，"
                      "且 F-0032 数字全部不可复现；CI 极宽提示功效不足，结论为『无证据』。"),
    claim=("节假日窗口无『连号撞号减弱』证据：春节（农历精确映射正月初一±7天）后段连号注数比 1.005、"
           "国庆 1.010、元旦 1.003（基线 1.388，CI 均宽含基线）；r05 的 F-0032 探索性数字"
           "（国庆 0.719 / 元旦 0.734 / 基线 1.28）在当前数据四种口径下均不可复现 → F-0032 信号失效，"
           "H-006 无证据支持（refuted）"),
    evidence={
        "method": "农历春节日期精确映射（2007-2026 正月初一公历表）+ 窗口 Bootstrap（B=2000，加总口径）"
                  "+ run≥1/run≥2 与均值/加总四口径对照",
        "result_summary": "后段基线 ratio_sum=1.388（run≥2）；春节窗口 n=33 ratio=1.005、国庆 n=82 ratio=1.010、"
                          "元旦 n=33 ratio=1.003；F-0032 报 0.719/0.734 无法在任何口径复现（run≥1/run≥2 × 均值/加总均 ≈1.0）。",
        "effect": {
            "baseline_post_ratio": 1.388, "baseline_ci95": [1.0420, 1.5167],
            "spring_exact": {"n": 33, "ratio": 1.005, "ci95": [0.009, 86.556]},
            "national": {"n": 82, "ratio": 1.010, "ci95": [0.106, 7.806]},
            "newyear": {"n": 33, "ratio": 1.003, "ci95": [0.074, 13.243]},
            "f0032_reproducible": False,
        },
        "ci95": None, "p_value": None, "n_observations": 1973,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_T016,
    },
    caveats=[
        "窗口样本小（33-82 期）→ 功效不足，CI 含基线；结论是『无证据』而非『效应不存在』。",
        "F-0032 的 0.719/0.734 不可复现可能源于其窗口定义或口径细节未记录——建议后续重跑 r05 脚本核对其实现。",
        "只涉及被选中率结构，不涉及开出率与中奖概率（恒 1/21,425,712）。",
    ],
    source=S_T016, tags=["holiday", "timing", "collision"],
)

# ============ F-0004 / F-0005 重校准重记 ============
for fid in ("F-0004", "F-0005"):
    o = byid[fid]
    o["updated_at"] = TODAY
    o.setdefault("evidence", {})["recalibrated_round07"] = {
        "date": TODAY, "result": "maintain",
        "script": S_T013,
        "note": "动态锚点 5 轮到期重校准：E6 锚点（w1 中位 6、派发额中位 0.4252 亿）精确复现；"
                "后段 R 仍显著>1（1.3884 CI [1.0420,1.5167]，含记录值 1.2472）；后段开出率 p=0.164 不显著维持。",
    }
    print(f"[recalibrate] {fid} maintain")

# ============ 排序回写 ============
facts.sort(key=lambda o: o["id"])
with open(FACTS, "w", encoding="utf-8") as f:
    for o in facts:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"[write] FACTS.jsonl {len(facts)} 条")

# ============ OPEN_QUESTIONS ============
oq = open(OQ, encoding="utf-8").read()
oq = oq.replace("| **状态** | `open` |\n| **由何而起** | F-0019（r04 发现前段三者不自洽） |",
                "| **状态** | `answered` → **F-0033/F-0034**（r07 根因定位 + 外部核对） |\n| **由何而起** | F-0019（r04 发现前段三者不自洽） |")
oq = oq.replace("| **状态** | `open` |\n| **由何而起** | F-0019 |",
                "| **状态** | `answered` → **F-0034**（r07 外部核对 102/102 一致） |\n| **由何而起** | F-0019 |")
open(OQ, "w", encoding="utf-8").write(oq)
print("[update] OPEN_QUESTIONS.md Q-013/Q-014 → answered")

# ============ HYPOTHESES ============
hyp = open(HYP, encoding="utf-8").read()
hyp = hyp.replace("| **状态** | `unverified` |\n| **假设** | 国庆/元旦等休市窗口前后，购彩人群构成不同",
                  "| **状态** | `refuted`（r07：F-0035 无证据，F-0032 不可复现） |\n| **假设** | 国庆/元旦等休市窗口前后，购彩人群构成不同")
open(HYP, "w", encoding="utf-8").write(hyp)
print("[update] HYPOTHESES.md H-006 → refuted")

# ============ TODO ============
todo = open(TODO, encoding="utf-8").read()
for tid in ("T-014", "T-015", "T-016"):
    todo = re.sub(rf"- \[ \] \*\*{tid}\*\*", f"- [x] **{tid}**", todo)
open(TODO, "w", encoding="utf-8").write(todo)
print("[update] TODO.md T-014/T-015/T-016 → done")

print("done")
