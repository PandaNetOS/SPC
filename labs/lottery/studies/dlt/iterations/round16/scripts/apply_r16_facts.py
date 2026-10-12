# -*- coding: utf-8 -*-
"""apply_r16_facts.py — r16 动态锚点重校准入库（B1）

validate 到期告警的 7 条结论，本轮全部**重跑脚本复现**后判定：

| 结论 | 原确立轮 | 复现脚本 | 判定 |
|---|---|---|---|
| F-0016 / F-0017 / F-0022 / F-0023 | round09 | `t013_recalibrate_r09.py` | maintain |
| F-0028 / F-0029 / F-0031 | round10 | `t028_recalibrate_r10.py` | maintain |

维持的处置（沿用 r09/r10 的 NOOP 语义 + 刷新确立轮）：
  - `evidence.recalibrated_round16` = 本次校验记录（脚本 / 数值 / 结论）
  - `evidence.noop_count` += 1（幂等：同一轮重复跑不重复计数）
  - `established_in` → `round16`（**关键**：validate 的 `check_recalibration`
    按 `established_in` 计时，只写 recalibrated_* 而不刷新它是**清不掉告警**的）
  - `status` / `change_type` 不动 —— 维持不是变更

同时修正 T-020 的历史记录缺口（见 `fix_t020_record`）：
T-020 的产出其实已在 r09 入库为 **F-0038**，但 TODO 条目始终没有
`✅ rXX 完成 → F-xxxx` 记录，导致 r15 开轮时误判为「已勾选但未产出」。
本脚本只补记录、不改结论。
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
FACTS = os.path.join(ROOT, "memory", "facts", "FACTS.jsonl")
TODO = os.path.join(ROOT, "memory", "workbench", "TODO.md")
QUESTIONS = os.path.join(ROOT, "memory", "workbench", "OPEN_QUESTIONS.md")
TODAY = "2026-10-12"
ROUND = "round16"

S_R09 = "labs/lottery/studies/dlt/iterations/round16/scripts/t013_recalibrate_r09.py"
S_R10 = "labs/lottery/studies/dlt/iterations/round16/scripts/t028_recalibrate_r10.py"

R09_NOTE = (
    "动态锚点到期重校准（r16 复跑 r09 脚本）：E6 一等奖总派发 max 0.9788 亿 < 1 亿、"
    "触发 0 次（F-0016）；E6 锚点 w1 中位 6 / 派发额中位 0.4252 亿精确复现"
    "（F-0017/F-0022）；E6 期初奖池 top−bottom er_t 差 +0.0171 p=0.311 不显著"
    "（F-0023，参照 p≈0.27）。全部维持。"
)
R10_NOTE = (
    "动态锚点到期重校准（r16 复跑 r10 脚本）：F-0031 奖池 AR(1) 斜率 0.9994"
    "（SE 0.00064）、ACF lag1-3 = 0.9996/0.9991/0.9986 精确复现；"
    "F-0028/F-0029 的可校验部分复核成立（后段连号撞号比 R=1.0250 CI [0.981,1.0692]，"
    "E6 w1 中位 6），规则文本与模拟参数无机制变化。全部维持。"
)

GROUPS = [
    (["F-0016", "F-0017", "F-0022", "F-0023"], S_R09, R09_NOTE),
    (["F-0028", "F-0029", "F-0031"], S_R10, R10_NOTE),
]


def main() -> int:
    facts = []
    for line in open(FACTS, encoding="utf-8"):
        line = line.strip()
        if line:
            facts.append(json.loads(line))
    byid = {o["id"]: o for o in facts}
    print(f"[load] {len(facts)} 条")

    n_done = 0
    for ids, script, note in GROUPS:
        for fid in ids:
            o = byid.get(fid)
            if o is None:
                print(f"  ! 未找到 {fid}，跳过")
                continue
            ev = o.setdefault("evidence", {})
            key = f"recalibrated_{ROUND}"
            if key in ev:
                print(f"  = {fid} 本轮已重记，跳过（幂等）")
                continue
            ev[key] = {
                "date": TODAY,
                "result": "maintain",
                "script": script,
                "note": f"原确立轮为 {o.get('established_in')}，{note}"
                        f"重校准维持后刷新确立轮以清除到期告警。",
            }
            ev["noop_count"] = (ev.get("noop_count") or 0) + 1
            o["established_in"] = ROUND
            o["updated_at"] = TODAY
            n_done += 1
            print(f"  ~ {fid} maintain（noop_count={ev['noop_count']}，"
                  f"established_in→{ROUND}）")

    with open(FACTS, "w", encoding="utf-8") as f:
        for o in facts:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(f"[write] FACTS.jsonl（重校准 {n_done} 条）")

    add_f0048(facts, byid)
    fix_t020_record()
    close_q006()
    update_h002()
    return 0


def add_f0048(facts: list, byid: dict) -> None:
    """入库 F-0048（H-002 三段单调检验）。

    只加一次（按 id 幂等）。结论是**部分支持**：端点差显著、中间分段不显著、
    序型置换检验 p=0.2103 未达显著 —— 因此 claim 里把三件事分开写，
    不以「H-002 成立」概括。
    """
    if "F-0048" in byid:
        print("  = F-0048 已存在，跳过")
        return
    res = json.load(open(os.path.join(ROOT, "games", "dlt", "iterations",
                                      "round16", "scripts",
                                      "t064_h002_segment.json"), encoding="utf-8"))
    sm = res["segment_means"]
    pw = res["pairwise_diff"]
    facts.append({
        "id": "F-0048",
        "game": "dlt",
        # claim 上限 300 字符（fact.schema.json）：细节放 evidence.result_summary，
        # 一句话结论只保留「支持什么 / 不支持什么」这对可证伪判断。
        "claim": (
            "H-002『生日偏好按号递减』三段检验：点估计全序单调"
            f"（S_j 均值 {sm['1-12']:.4f} > {sm['13-31']:.4f} > {sm['32-35']:.4f}），"
            "但仅端点差显著"
            f"（1-12 − 32-35 = {pw['1-12_vs_32-35']['diff']:+.4f}，"
            f"CI [{pw['1-12_vs_32-35']['ci95'][0]:+.4f}, "
            f"{pw['1-12_vs_32-35']['ci95'][1]:+.4f}]）；中间分段差 CI 含 0，"
            f"序型置换检验 p={res['monotonicity_permutation_p']} → 支持『小号段更易撞车』，"
            "不支持『严格三段递减』。不改变中奖概率。"
        ),
        "status": "established",
        "confidence": 3,
        "confidence_basis": (
            "在 F-0038 已估出的 35 个号相对撞号强度 S_j（n=1973 后段期）上复算，"
            "分层 bootstrap B=10000 + 序型置换检验 20000 次；"
            "端点差 CI 下界仅 +0.0045（勉强排除 0），故不给更高置信度"
        ),
        "confidence_grade": "moderate",
        "change_type": "initial",
        "valid_until": "2028-10-12",
        "recalibrate_every": None,
        "category": "structure_preference",
        "claim_type": "empirical",
        "affects_win_probability": False,
        "evidence": {
            "method": (
                "取 F-0038 的 S_j（`round09/scripts/t020_number_weight.py`，后段 1973 期）；"
                "按 1-12 / 13-31 / 32-35 分段求均值；段间差用分层有放回 bootstrap（B=10000），"
                "序型用固定段大小（12/19/4）的随机置换检验（20000 次）"
            ),
            "result_summary": (
                f"段均值 {sm['1-12']:.4f} / {sm['13-31']:.4f} / {sm['32-35']:.4f}；"
                f"1-12−13-31 {pw['1-12_vs_13-31']['diff']:+.4f} "
                f"CI [{pw['1-12_vs_13-31']['ci95'][0]:+.4f}, {pw['1-12_vs_13-31']['ci95'][1]:+.4f}]；"
                f"13-31−32-35 {pw['13-31_vs_32-35']['diff']:+.4f} "
                f"CI [{pw['13-31_vs_32-35']['ci95'][0]:+.4f}, {pw['13-31_vs_32-35']['ci95'][1]:+.4f}]；"
                f"1-12−32-35 {pw['1-12_vs_32-35']['diff']:+.4f} "
                f"CI [{pw['1-12_vs_32-35']['ci95'][0]:+.4f}, {pw['1-12_vs_32-35']['ci95'][1]:+.4f}]；"
                f"序型置换 p={res['monotonicity_permutation_p']}"
            ),
            "effect": {
                "segment_means": sm,
                "segment_n": res["segment_n"],
                "segment_sd": res["segment_sd"],
                "pairwise_diff": pw,
                "monotonicity_permutation_p": res["monotonicity_permutation_p"],
                "n_boot": res["n_boot"],
                "n_perm": res["n_perm"],
                "seed": res["seed"],
            },
            "ci95": pw["1-12_vs_32-35"]["ci95"],
            "p_value": res["monotonicity_permutation_p"],
            "n_observations": 1973,
            "data_version": "dlt_full_2933",
            "rules_epoch": "E6",
            "script": "labs/lottery/studies/dlt/iterations/round16/scripts/t064_h002_segment.py",
            "source_sha256": None,
            "upstream_fact": "F-0038",
            "noop_count": 0,
        },
        "caveats": [
            "32-35 段只有 **4 个号**，段均值极不稳定（sd=0.0613）—— 端点差 CI 下界仅 +0.0045，"
            "属『勉强显著』，不宜作为策略分段的强依据。",
            "与 F-0038 不矛盾但**口径不同**：F-0038 比的是 1-31 整段 vs 32-35（差 0.047，CI 含 0）；"
            "本条比的是 1-12 月段 vs 32-35。1-12 是 1-31 中信号最强的子集，"
            "把 13-31 并进来会稀释效应 → 整段不显著、月段勉强显著，二者可并存。",
            "序型置换检验 p=0.2103 说明：即使点估计单调，这样的三段全序在随机分配下也有约 21% 概率出现，"
            "因此**不能**宣称『严格三段递减』成立。",
            "S_j 是撞号强度代理（由一等奖中出注数反推），不等于个体偏好本身；"
            "逐号权重与连号形态可能共线（连号集中在小号区），未做 VIF 诊断。",
            "不改变任一奖级中奖概率（红线）。",
        ],
        "established_in": "round16",
        "supersedes": None,
        "superseded_by": None,
        "source": "labs/lottery/studies/dlt/iterations/round16/scripts/t064_h002_segment.py",
        "created_at": TODAY,
        "updated_at": TODAY,
        "tags": ["h002", "birthday", "per_number", "segment", "collision"],
    })
    with open(FACTS, "w", encoding="utf-8") as f:
        for o in facts:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print("  + F-0048 入库（H-002 三段检验：端点显著、序型不显著）")


def update_h002() -> None:
    """H-002：`unverified` → `partial`（F-0048 端点支持、精细结构不支持）。"""
    p = os.path.join(ROOT, "memory", "workbench", "HYPOTHESES.md")
    txt = open(p, encoding="utf-8").read()
    old = "| **状态** | `unverified` |"
    if old not in txt:
        print("  = H-002 状态已非 unverified，跳过")
        return
    new = ("| **状态** | `partial`（r16：F-0048 端点差显著 1-12 > 32-35 "
           "(+0.0633, CI [+0.0045,+0.1211])，但中间分段差不显著、序型置换 p=0.2103 "
           "→ 支持『小号段更易撞车』，不支持『严格三段递减』） |")
    open(p, "w", encoding="utf-8").write(txt.replace(old, new, 1))
    print("  ~ H-002 → partial（F-0048）")


def fix_t020_record() -> None:
    """补 T-020 的完成记录。

    r15 曾把 T-020 判为「存疑：已勾选但无产出」——这是**误判**，根因是
    TODO 条目缺 `✅ rXX 完成 → F-xxxx` 记录，而产出其实已由 r09 入库为 F-0038。
    本函数补记录 + 留痕说明误判来源，防止后人再踩。
    """
    txt = open(TODO, encoding="utf-8").read()
    old = "- [x] **T-020** 逐号偏好权重建模（Q-006 / H-002）"
    if old not in txt:
        print("  ! TODO 未找到 T-020 条目，跳过")
        return
    if "F-0038" in txt.split("- [x] **T-021**")[0].split("T-020")[1][:400]:
        print("  = T-020 已有 F-0038 记录，跳过")
        return
    new = ("- [x] **T-020** 逐号偏好权重建模（Q-006 / H-002）✅ **r09 完成** → "
           "**F-0038**：后段逐号相对撞号强度 S_j（1.0=无偏好）号码间明显分异"
           "（9/11/19 偏高、35 偏低），生日段（1-31）均值 1.005 vs 高段（32-35）0.958"
           "（差 0.047，CI [-0.0109, 0.0962] 含 0 → 段级无显著差异）；"
           "OLS 逐号项 R² 由 0.00869 → 0.04527（ΔR²=0.03657，30/35 个号系数 |β|>0.05），"
           "n=1973。脚本 `round09/scripts/t020_number_weight.py`。\n"
           "      **⚠ r16 补记**：本条此前**缺完成记录**，导致 r15 误判为"
           "「已勾选但无产出」（见 `round15/HANDOFF.md` §4）。产出一直存在（F-0038），"
           "缺口只是登记 —— 已完成项的 `✅ → F-xxxx` 记录不是装饰，是下轮不被误判的依据。")
    open(TODO, "w", encoding="utf-8").write(txt.replace(old, new))
    print("  ~ T-020 补完成记录（→ F-0038），并留痕 r15 误判来源")


def close_q006() -> None:
    """Q-006 → answered（产出 = F-0038，r09 已入库但未同步问题状态）。"""
    txt = open(QUESTIONS, encoding="utf-8").read()
    marker = "## Q-006 — 人群权重模型过于简化（仅两个特征）"
    if marker not in txt:
        print("  ! OPEN_QUESTIONS 未找到 Q-006，跳过")
        return
    seg = txt.split(marker, 1)[1]
    if "| **状态** | `answered`" in seg[:400]:
        print("  = Q-006 已 answered，跳过")
        return
    old = "| **状态** | `open` |"
    head, rest = seg.split(old, 1)
    new_state = "| **状态** | `answered` → **F-0038**（r09 产出，r16 同步问题状态） |"
    # split 已把 old 从 seg 中摘掉，重建时用它替换回来（不要在 head 上 replace，
    # head 里并不包含 old）
    txt = txt.split(marker, 1)[0] + marker + head + new_state + rest
    # 头部计数与标题
    txt = txt.replace("**15 个开放问题 | **14 answered**",
                      "**15 个开放问题 | **15 answered**")
    txt = txt.replace(marker, marker + " ✅ answered by r09（r16 同步）", 1)
    open(QUESTIONS, "w", encoding="utf-8").write(txt)
    print("  ~ Q-006 → answered（F-0038）")


if __name__ == "__main__":
    sys.exit(main())
