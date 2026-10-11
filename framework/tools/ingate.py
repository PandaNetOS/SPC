# -*- coding: utf-8 -*-
"""framework/tools/ingate.py — 入库三闸门（v2.0）

学术依据：LSTM-MAS（arXiv 2601.11913）的 filter / judge / manager 门控，
防错误累积与幻觉传播；TiM（arXiv 2311.08719）的 merge 操作。

用途：一条新结论（fact dict）进 FACTS.jsonl 之前，先过三闸门：

  · Filter 闸 —— 冗余削减
      新 claim 与现有 active F 的关键词 Jaccard 相似度过高 → 提示重复/可 merge
  · Judge 闸 —— 检错
      claim_type 结构性约束（与 spec/fact.schema.json 的 allOf 同判据）
      数据口径：涉及数据的结论必须声明 data_version（后段），且不能缺样本量
      统计判据：empirical/simulation 必须有 effect + CI/p（或可复现参数）
      矛盾检测：与同 category 的 active F 存在互斥关键词时提示人工核验
  · Manager 闸 —— 全局调控
      列出会受影响的策略规则（evidence_refs 主题重叠）
      提示 FACTS 变更后的联动：rehash --strategy → validate --all → 版本 bump

用法：
    python framework/tools/ingate.py < fact.json        # 从 stdin 读一条 fact
    python framework/tools/ingate.py --file fact.json
    python framework/tools/ingate.py --draft-id F-0033  # 编辑器中快速自检

退出码：0=可直接入库；1=建议降级 tentative；2=建议拒绝（有硬错误）。
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

VALID_CLAIM_TYPES = {"analytic", "empirical", "simulation", "documentary", "methodological"}
MUTEX_PAIRS = [
    # (claim 中出现的词, 与之互斥的词) —— 用于 Judge 闸的粗粒度矛盾提示
    ("生日", "均匀分布"),
    ("连号", "无结构"),
    ("可预测", "不可预测"),
    ("星期六", "星期日"),
    ("提高", "降低"),
    ("正相关", "负相关"),
    ("有利", "不利"),
    ("不存在", "存在"),
    ("不显著", "显著"),
    ("弱于", "强于"),
    ("均匀", "偏好"),
    ("不可利用", "可利用"),
    ("无效应", "有效应"),
    ("等于", "不等于"),
    ("更多", "更少"),
]

# D2 增强：方向冲突对（同一主题内正/负方向断言互斥）
_DIRECTION_PAIRS = [
    ("提高", "降低"), ("上升", "下降"), ("增加", "减少"),
    ("正相关", "负相关"), ("有利", "不利"), ("更强", "更弱"),
    ("更热", "更冷"), ("更高", "更低"), ("显著", "不显著"),
]

# D2 增强：核心主题词（启发式词典，不引 embedding）
# 新结论与同主题 active F 若 claim_type 相同且方向相反 → 疑似矛盾
_TOPIC_TERMS = [
    "连号", "生日", "星期", "奖池", "复式", "胆拖", "倍投", "追加",
    "凯利", "封顶", "销售额", "机选", "开奖", "奇偶", "后区", "前区",
    "撞号", "中奖", "返奖", "期望", "均衡", "热号", "冷号", "春节",
    "节假日", "周六", "周一", "周三", "一等奖", "二等奖", "翻倍",
]


def load_active_facts(root: str = ROOT) -> list[dict]:
    p = os.path.join(root, "memory", "facts", "FACTS.jsonl")
    out = []
    if not os.path.exists(p):
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("status") == "established":
                out.append(d)
    return out


def _kw(claim: str) -> set[str]:
    toks = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", claim.lower())
    return {t for t in toks if len(t) >= 2}


# ---------------------------------------------------------------- Filter 闸

def gate_filter(fact: dict, active: list[dict]) -> list[str]:
    msgs: list[str] = []
    claim = fact.get("claim", "")
    kws = _kw(claim)
    if not kws:
        msgs.append("[Filter] claim 过短，无法做冗余检测")
        return msgs
    for a in active:
        ak = _kw(a.get("claim", ""))
        if not ak:
            continue
        inter = len(kws & ak)
        union = len(kws | ak)
        if union and inter / union >= 0.6:
            msgs.append(
                f"[Filter] 与 {a['id']} 高度相似（Jaccard={inter/union:.2f}）"
                f" —— 重复入库或应走 merge（TiM）"
            )
    if not msgs:
        msgs.append("[Filter] 无高度相似结论，冗余风险低")
    return msgs


# ---------------------------------------------------------------- Judge 闸

def _semantic_conflict(fact: dict, active: list[dict]) -> list[str]:
    """D2 增强：结构化矛盾检测（不引 embedding，关键词/反模式启发式）。

    三维检测：
      1. 方向冲突 —— 同主题下新结论与 active F 含相反方向词（更强/更弱、提高/降低…）
      2. 范畴断言冲突 —— 新结论称「提高/改变中奖概率」，违反红线（F-0001）
      3. 主题重复反向 —— 同 claim_type、同主题、方向相反且都有证据 → 冲突

    依据：Wright（arXiv 2506.17331）禁止自欺 —— 新结论与既有结论的矛盾
    必须显式可见（走 revision 取代链，而非悄悄并存）；TiM merge 操作。
    """
    msgs: list[str] = []
    claim = fact.get("claim", "") or ""
    ct = fact.get("claim_type")
    topics = [t for t in _TOPIC_TERMS if t in claim]

    def _dirs(text: str) -> set[str]:
        return {w for w, _ in _DIRECTION_PAIRS if w in text} | \
               {w for _, w in _DIRECTION_PAIRS if w in text}

    def _opposed(nd: set[str], ad: set[str]) -> bool:
        for w in nd:
            opp = {w2 for w1, w2 in _DIRECTION_PAIRS if w1 == w} | \
                  {w1 for w1, w2 in _DIRECTION_PAIRS if w2 == w}
            if opp & ad:
                return True
        return False

    # 1+3. 同主题方向冲突（含同 claim_type 反向强化提示）
    for a in active:
        if a.get("id") == fact.get("id"):
            continue
        aclaim = a.get("claim", "") or ""
        shared = set(topics) & {t for t in _TOPIC_TERMS if t in aclaim}
        if not shared:
            continue
        nd = _dirs(claim)
        ad = _dirs(aclaim)
        if nd and ad and _opposed(nd, ad):
            msgs.append(
                f"[Judge] 与 {a['id']} 疑似矛盾（同主题「{'/'.join(sorted(shared))}」，"
                f"方向词 {sorted(nd)} vs {sorted(ad)}）—— 请人工核验或走 revision 取代链"
            )
            if a.get("claim_type") == ct:
                msgs.append(
                    f"[Judge] 与 {a['id']} 同 claim_type({ct}) 同主题但方向相反"
                    f"（{sorted(nd)} vs {sorted(ad)}）—— 必须显式 revision，不得并存"
                )

    # 2. 范畴断言冲突（红线：任何结论不得提高/改变中奖概率）
    raises_prob = ("提高中奖概率" in claim or "增加中奖概率" in claim or
                   ("改变中奖概率" in claim and "不改变" not in claim
                    and "不能改变" not in claim))
    if raises_prob:
        for a in active:
            aclaim = a.get("claim", "") or ""
            if "中奖概率" in aclaim and ("不能改变" in aclaim or "不改变" in aclaim):
                msgs.append(
                    f"[Judge] 与 {a['id']} 冲突：新结论声称「提高/改变中奖概率」，"
                    f"违反红线（任何选号方式都不能改变单注的中奖概率）"
                )
    return msgs


def gate_judge(fact: dict, active: list[dict]) -> list[str]:
    msgs: list[str] = []
    ct = fact.get("claim_type")
    ev = fact.get("evidence") or {}

    if ct not in VALID_CLAIM_TYPES:
        msgs.append(f"[Judge] claim_type={ct!r} 非法：{sorted(VALID_CLAIM_TYPES)}")
        return msgs

    # claim_type 结构性约束（与 validate.check_claim_type 同判据）
    if ct == "analytic":
        for k in ("p_value", "ci95"):
            if ev.get(k) is not None:
                msgs.append(f"[Judge] analytic 却带 {k} —— 解析结论不含抽样不确定性")
    elif ct == "empirical":
        if not ev.get("data_version"):
            msgs.append("[Judge] empirical 未声明 data_version —— 消费者无法判断数据适用性")
        if not isinstance(ev.get("n_observations"), int) or ev["n_observations"] < 1:
            msgs.append("[Judge] empirical 缺 n_observations（须为正整数）")
        if ev.get("data_version") not in (None, "dlt_full_2933"):
            msgs.append(
                f"[Judge] data_version={ev.get('data_version')!r} 非后段口径"
                f"（策略数字一律用 dlt_full_2933，见 F-0019）"
            )
    elif ct == "simulation":
        eff = ev.get("effect") or {}
        if not (isinstance(eff, dict) and ("n_sim" in eff or "rng_seed" in eff)):
            msgs.append("[Judge] simulation 的 effect 缺 n_sim 或 rng_seed —— 不可复现")
        if len(fact.get("caveats") or []) < 2:
            msgs.append("[Judge] simulation 的 caveats 少于 2 条 —— 模型假设必须显式列出")
        if ev.get("effect") and isinstance(ev.get("effect"), dict):
            if "rng_seed" not in (ev.get("effect") or {}):
                msgs.append("[Judge] simulation 建议显式给出 rng_seed（统一种子 20261011）")
    elif ct == "documentary":
        if not ev.get("rules_epoch"):
            msgs.append("[Judge] documentary 未声明 rules_epoch（规则已 6 次变更）")
    elif ct == "methodological":
        if not fact.get("caveats"):
            msgs.append("[Judge] methodological 的 caveats 为空")

    # 统计判据：empirical/simulation 的效应量应有 CI/p 或可复现参数
    if ct in ("empirical", "simulation"):
        eff = ev.get("effect")
        ci = ev.get("ci95")
        p = ev.get("p_value")
        if (not isinstance(eff, dict)) or (ci is None and p is None):
            msgs.append("[Judge] empirical/simulation 缺效应量支撑 —— 结论无法复核")

    # 矛盾检测（D2 增强：互斥词 + 结构化的方向/主题/范畴三维检测）
    claim = fact.get("claim", "")
    for w1, w2 in MUTEX_PAIRS:
        if w1 in claim:
            for a in active:
                if w2 in (a.get("claim", "") or ""):
                    msgs.append(
                        f"[Judge] 与 {a['id']} 疑似矛盾（新结论含「{w1}」、"
                        f"旧结论含「{w2}」）—— 请人工核验或走 revision 取代链"
                    )
    msgs.extend(_semantic_conflict(fact, active))

    if not msgs:
        msgs.append("[Judge] claim_type 结构 / 口径 / 统计判据全部通过")
    return msgs


# ---------------------------------------------------------------- Manager 闸

def gate_manager(fact: dict, active: list[dict], root: str = ROOT) -> list[str]:
    msgs: list[str] = []
    kw = _kw(fact.get("claim", ""))
    if not kw:
        return ["[Manager] claim 过短，无法评估策略影响面"]
    st_path = os.path.join(root, "games", "dlt", "strategy", "strategy.json")
    if os.path.exists(st_path):
        try:
            with open(st_path, encoding="utf-8") as f:
                st = json.load(f)
        except json.JSONDecodeError:
            st = {}
        for rule in st.get("rules") or []:
            refs = rule.get("evidence_refs") or []
            for r in refs:
                f = next((x for x in active if x.get("id") == r), None)
                if f and (_kw(f.get("claim", "")) & kw):
                    msgs.append(
                        f"[Manager] 新结论可能与规则 {rule.get('id')} 的"
                        f"evidence_refs（{refs}）主题重叠 —— 检查是否需更新策略"
                    )
                    break
        msgs.append("[Manager] FACTS 变更后联动：`python cli/main.py rehash --strategy`"
                    " → `validate --all` → 版本 bump（versions.json + VERSION_INDEX）")
    return msgs


def _load_refs(refs: list[str], root: str) -> list[dict]:
    """按 id 从 FACTS.jsonl 载入被引用条目（Manager 闸主题重叠检测用）。"""
    p = os.path.join(root, "memory", "facts", "FACTS.jsonl")
    out = []
    if not os.path.exists(p):
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("id") in refs:
                out.append(d)
    return out


# ---------------------------------------------------------------- 汇总

def run(fact: dict, root: str = ROOT) -> int:
    active = load_active_facts(root)
    all_msgs = (gate_filter(fact, active) + gate_judge(fact, active)
                + gate_manager(fact, active, root))

    hard = [m for m in all_msgs
            if m.startswith("[Judge]") and ("缺" in m or "非法" in m)]
    suggest_tentative = [m for m in all_msgs
                         if m.startswith("[Filter] 与")          # 真相似警告，排除「无高度相似」否定句
                         or (m.startswith("[Judge]") and "疑似矛盾" in m)]

    print("=== 入库三闸门报告 ===")
    print(f"候选结论：{fact.get('id', '?')} | {fact.get('claim', '')[:60]}")
    for m in all_msgs:
        print("  " + m)
    print(f"--- 结论：直接入库({len(hard) == 0 and len(suggest_tentative) == 0})"
          f" / 建议 tentative({len(suggest_tentative) > 0})"
          f" / 建议拒绝({len(hard) > 0}) ---")
    if hard:
        return 2
    if suggest_tentative:
        return 1
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    args = [a for a in sys.argv[1:]]
    if "--file" in args:
        i = args.index("--file")
        with open(args[i + 1], encoding="utf-8") as f:
            fact = json.load(f)
    elif args and args[0] == "--draft-id":
        # 自检模式：打印说明
        print("自检模式：把待入库 fact（json 单行）通过 stdin 传入")
        sys.exit(1)
    else:
        data = sys.stdin.read()
        fact = json.loads(data)
    sys.exit(run(fact))
