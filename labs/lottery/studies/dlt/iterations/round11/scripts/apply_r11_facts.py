# -*- coding: utf-8 -*-
"""apply_r11_facts.py — round11 入库（三闸门）
F-0042（T-023 效应平台期）新增；F-0043（T-024 代理可观测）新增；
F-0021 caveats 更新（补 r11 代理证据 + 概率口径限定）；
Q-011/Q-015 → answered；TODO T-023/T-024/T-048 → done。
"""
import datetime
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TODAY = datetime.date.today().isoformat()
BASE = r"D:\PNOS\SPC"
FACTS = BASE + r"\memory\facts\FACTS.jsonl"
OQ = BASE + r"\memory\workbench\OPEN_QUESTIONS.md"
TODO = BASE + r"\memory\workbench\TODO.md"

# ---------- 1. FACTS.jsonl：新增 F-0042 / F-0043 + 更新 F-0021 ----------
facts = [json.loads(l) for l in open(FACTS, encoding="utf-8") if l.strip()]
ids = {f["id"] for f in facts}

new_facts = []

f42 = {
    "id": "F-0042",
    "game": "dlt",
    "status": "established",
    "affects_win_probability": False,
    "confidence": 3,
    "confidence_basis": "后段 1973 期滚动窗口（W=300/500，步长 50）效应量序列：OLS 趋势 + Kendall tau + 头/尾 1/3 Mann-Whitney；节假日分时段样本 65/47/52 期，中等样本，标探索性。",
    "claim": "后段内部（2013-08-28 起）连号撞号效应进入平台期：滚动窗口下 R_run 斜率均不显著（W=300: slope=-0.0027 p=0.136；W=500: slope=-0.001 p=0.401）、Kendall tau 不显著、前 1/3 vs 后 1/3 窗口均值无显著差异（p=0.646/0.910）→ 2013-08 前段→后段的大幅弱化（F-0003: 2.107→1.247）之后效应不再持续弱化，稳定于 ~1.0-1.1；节假日窗口效应分时段（2008-14: 0.385 / 2015-19: 1.217 / 2020-26: 0.888）波动无单调弱化趋势（样本有限，探索性）",
    "category": "structure_preference",
    "claim_type": "empirical",
    "evidence": {
        "method": "滚动窗口复验（W=300/500 步长 50，后段 1973 期）+ OLS 趋势 + Kendall tau + 头尾 1/3 Mann-Whitney；节假日春节精确映射 ±14 天窗口分三时段对比（L3 不硬切）",
        "result_summary": "W=300: 34 窗 slope=-0.0027 p=0.1361 tau=-0.0766 p=0.524 头均 1.083 尾均 1.037 p=0.646；W=500: 30 窗 slope=-0.001 p=0.401 tau=-0.044 p=0.750 头均 1.039 尾均 1.031 p=0.910；节假日窗口 R: 2008-14=0.385(65 期) 2015-19=1.217(47 期) 2020-26=0.888(52 期) vs 各段全年基线 ~1.04-1.15",
        "effect": {
            "W300": {"slope": -0.0027, "p_slope": 0.1361, "kendall_tau": -0.0766, "head_mean": 1.0829, "tail_mean": 1.037, "p_head_tail": 0.6458, "n_windows": 34},
            "W500": {"slope": -0.001, "p_slope": 0.4007, "kendall_tau": -0.0437, "head_mean": 1.0394, "tail_mean": 1.031, "p_head_tail": 0.9097, "n_windows": 30},
            "holiday_segments": {"2008-2014": {"R": 0.385, "n": 65}, "2015-2019": {"R": 1.217, "n": 47}, "2020-2026": {"R": 0.888, "n": 52}},
        },
    },
    "caveats": [
        "『平台期』结论只覆盖后段内部（2013-08 之后）；前段→后段的大幅弱化（F-0003）不受本条影响。",
        "滚动窗口互相重叠，窗口间不独立，趋势检验功效受限。",
        "节假日分时段样本 47-65 期，R 波动大，仅探索性，不推翻 H-006 的 established 结论。",
    ],
    "related": ["F-0003", "F-0021", "H-006"],
    "established_in": "round11",
    "noop_count": 0,
    "data_version": "E6（后段 1973 期，2026-10 最新）",
}
new_facts.append(f42)

f43 = {
    "id": "F-0043",
    "game": "dlt",
    "status": "established",
    "affects_win_probability": False,
    "confidence": 3,
    "confidence_basis": "后段 1973 期滚动窗口（W=300 步长 50）三个代理量的数据驱动变点扫描（置换检验 B=2000）；P2/P3 显著（p=0.0005），P1 边缘（p=0.055），代理为间接量，构念效度有限。",
    "claim": "机选占比的可观测代理成立：连号一等奖注数比 R_run 有显著变点（p=0.0005，切点窗口起点 2015-04，头 1.231→尾 1.009，与 F-0021 行为变化区间 2013-04~2014-04 在滚动窗分辨率 ±24 月内同窗对齐）；号码偏好浓度（w1 基尼）显著下降（p=0.0005，2022-12，0.144→0.118）→ 近年偏好浓度下降、机选占比或上升；生日号区注数比 R_low 全段稳定 ~1.2（变点 p=0.055 不显著）→ 低号偏好未弱化，R-003 避开生日号策略的撞号优势可能依然成立；代理×销量不显著（r=-0.154 p=0.384）→ 与 F-0021 一致，效应非销量稀释",
    "category": "structure_preference",
    "claim_type": "empirical",
    "evidence": {
        "method": "代理构造（P1 生日号区注数比 / P2 连号注数比 / P3 w1 号码偏好基尼）+ 数据驱动变点扫描（置换检验 B=2000，L3 不硬切）+ 代理×销量 Pearson",
        "result_summary": "P1 R_low 变点 p=0.055（head 1.245→tail 1.167）；P2 R_run 变点 p=0.0005（head 1.231→tail 1.009，cut 2015-04）；P3 gini_w1 变点 p=0.0005（head 0.144→tail 0.118，cut 2022-12）；R_low×销量 r=-0.154 p=0.384",
        "effect": {
            "P1_R_low": {"changepoint_p": 0.055, "head_mean": 1.2454, "tail_mean": 1.1666, "cut_date": "2017-04-01", "stable_high": True},
            "P2_R_run": {"changepoint_p": 0.0005, "head_mean": 1.2311, "tail_mean": 1.009, "cut_date": "2015-04-18", "aligns_F0021_m24m": True},
            "P3_gini_w1": {"changepoint_p": 0.0005, "head_mean": 0.1439, "tail_mean": 0.118, "cut_date": "2022-12-19"},
            "proxy_x_sales": {"pearson_r": -0.154, "p": 0.384},
        },
    },
    "caveats": [
        "代理为间接量：R_run/R_low/基尼由中出注数 w1 反推（L7 口径：被选中强度×开出事件），非直接机选占比观测。",
        "『机选占比或上升』是方向推断（偏好浓度下降与机选占比上升相容），非直接测量；不可用于预测（L6）。",
        "变点切点为滚动窗序列索引（分辨率受步长 50 限制），与 F-0021 的整段最优切点方法不同，对齐判定用 ±24 月容差。",
    ],
    "related": ["F-0021", "F-0003", "F-0029"],
    "established_in": "round11",
    "noop_count": 0,
    "data_version": "E6（后段 1973 期）",
}
new_facts.append(f43)

# F-0021 caveats 更新（r11 代理证据 + 概率口径限定）
for f in facts:
    if f["id"] == "F-0021":
        f["caveats"] = [
            c for c in f["caveats"]
            if "本数据集没有投注方式字段" not in c and "不涉及中奖概率" not in c
        ]
        f["caveats"].append(
            "r11 T-024 已构造可观测代理（F-0043）：连号偏好弱化（2014-15 变点显著）与近年偏好浓度下降"
            "（2022-23 显著）可观测，生日号低号偏好稳定（~1.2）——『行为变化』通道存在且部分可检验，"
            "代理为间接量，非直接机选占比。"
        )
        f["caveats"].append("不涉及中奖概率（各奖级概率恒定，一等奖恒 1/21,425,712）；本条只关乎撞号密度的时变。")
        f["related"] = sorted(set(f.get("related", []) + ["F-0042", "F-0043"]))
        print("F-0021 caveats 更新完成")

# 追加新 fact（ID 冲突保护）
for nf in new_facts:
    if nf["id"] in ids:
        print("SKIP 已存在", nf["id"])
        continue
    facts.append(nf)
    print("新增", nf["id"])

with open(FACTS, "w", encoding="utf-8") as fh:
    for f in facts:
        fh.write(json.dumps(f, ensure_ascii=False) + "\n")
print("FACTS.jsonl:", len(facts), "条")

# ---------- 2. OPEN_QUESTIONS.md：Q-011 / Q-015 → answered ----------
oq = open(OQ, encoding="utf-8").read()
oq = oq.replace("## Q-011 — 后段 CI 下界逼近 1，E6 内会否弱化至不显著？（r03 新增）",
                "## Q-011 — 后段 CI 下界逼近 1，E6 内会否弱化至不显著？（r03 新增）✅ answered in r11")
oq = oq.replace("| **状态** | `open` |\n| **由何而起** | r03 的 T-001：后段一等奖 CI 下界仅 1.0315、二等奖 1.0475 |",
                "| **状态** | `answered`（r11 → F-0042） |\n| **由何而起** | r03 的 T-001：后段一等奖 CI 下界仅 1.0315、二等奖 1.0475 |")
oq = oq.replace("## Q-015 — 「机选占比」是否有可观测代理变量（r04 新增）",
                "## Q-015 — 「机选占比」是否有可观测代理变量（r04 新增）✅ answered in r11")
oq = oq.replace("| **状态** | `open` |\n| **由何而起** | F-0021 的未观测混杂：数据集没有投注方式字段 |",
                "| **状态** | `answered`（r11 → F-0043） |\n| **由何而起** | F-0021 的未观测混杂：数据集没有投注方式字段 |")
# 头部 open 列表 5→3
oq = oq.replace("> 当前 open：**Q-006 / Q-008 / Q-011 / Q-015 / Q-016**（5 个）",
                "> 当前 open：**Q-006 / Q-008 / Q-016**（3 个）")
# 验收判据补 r11 结果
oq = oq.replace("| **验收判据** | 给出滚动估计轨迹；若趋势持续，须在 F-0003 标注\"效应可能继续弱化\" |",
                "| **验收判据** | 给出滚动估计轨迹；若趋势持续，须在 F-0003 标注\"效应可能继续弱化\" |\n| **✅ 结果（r11）** | 滚动轨迹给出（W=300/500 各 34/30 窗）：后段内部 R_run 无显著持续弱化（slope p=0.136/0.401，头尾 p=0.646/0.910）→ 效应进入平台期，F-0003 **无需**新增弱化标注（F-0042） |")
oq = oq.replace("| **验收判据** | 至少给出 1 个代理量的构造与检验；若全部失败，明确写「当前数据无法构造有效代理」（合格结论） |",
                "| **验收判据** | 至少给出 1 个代理量的构造与检验；若全部失败，明确写「当前数据无法构造有效代理」（合格结论） |\n| **✅ 结果（r11）** | P2 连号注数比变点 p=0.0005（2014-15，与 F-0021 同窗）、P3 偏好基尼变点 p=0.0005（2022-23）→ 代理可观测；P1 低号偏好稳定 ~1.2（F-0043） |")
open(OQ, "w", encoding="utf-8").write(oq)
print("OPEN_QUESTIONS.md: Q-011/Q-015 answered，open 5→3")

# ---------- 3. TODO.md：T-023 / T-024 / T-048 → done ----------
td = open(TODO, encoding="utf-8").read()
td = td.replace("- [ ] **T-048** ★ r08 新增：L3 组合优化预备（hold-out 评测设计，**本轮只做设计文档不落 L2**）",
                "- [x] **T-048** ✅ **r11 完成**：L3 组合优化预备——时序 hold-out 评测设计文档（`round11/T048_HOLDOUT_DESIGN.md`，含切分/指标/防泄漏/组合搜索边界/验收护栏；不落 L2）")
td = td.replace("- [ ] **T-023** 效应弱化的滚动复验（Q-011）★ r03 新增\n      随数据增长重跑分期；若持续弱化须在 F-0003 标注",
                "- [x] **T-023** 效应弱化的滚动复验（Q-011）✅ **r11 完成** → F-0042：后段内部效应进入平台期（W=300/500 滚动复验无显著持续弱化），F-0003 无需弱化标注")
td = td.replace("- [ ] **T-024** 机选占比的代理变量（Q-015）★ r04 新增\n      用分布熵 / 重复结构率 / 低号占比构造代理，检验 F-0021 的「行为变化」通道是否可观测\n      产出：新增 F-0xxx 或更新 F-0021 的 caveats",
                "- [x] **T-024** 机选占比的代理变量（Q-015）✅ **r11 完成** → F-0043：连号注数比/偏好基尼代理可观测（显著变点），F-0021 caveats 已更新（补代理证据 + 概率口径限定）")
open(TODO, "w", encoding="utf-8").write(td)
print("TODO.md: T-023/T-024/T-048 done")

print("入库完成")
