# -*- coding: utf-8 -*-
"""apply_r04_strategy.py — round04 同步对外策略（games/dlt/strategy/strategy.json）

动作
----
  1. R-001 幅度口径：magnitude_pct 121.48 → 109.39（后段口径上界）；
     magnitude_pct_with_cap 41.42 → 40.64；caveats 重写（引用 F-0019~F-0022）
  2. A-006（后区）更新：refuted_by 增 F-0025，理由改为「开出率均匀 ≠ 被选中率均匀」（L7）
  3. 新增 A-009：按『奖池累积期』择时加注 —— 由 F-0023/F-0024 驳回
  4. evidence_index 按当前引用重建；provenance.iteration → round04；重算 evidence_hash

不改 rules 的 predicate / action / weight（规则是判断，不由代码生成）。
幂等：可重复运行。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from spc.evidence import evidence_digest   # noqa: E402

ST = os.path.join(ROOT, "games", "dlt", "strategy", "strategy.json")
FACTS = os.path.join(ROOT, "memory", "facts", "FACTS.jsonl")
TODAY = "2026-10-11"

with open(ST, encoding="utf-8") as f:
    st = json.load(f)
facts = {}
with open(FACTS, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            o = json.loads(line)
            facts[o["id"]] = o

# ---- 1. R-001
r1 = next(r for r in st["rules"] if r["id"] == "R-001")
ev = r1["expected_value_impact"]
ev["magnitude_pct"] = 109.39
ev["magnitude_pct_with_cap"] = 40.64
ev["ci95"] = [0.4487, 0.4543]
ev["magnitude_pct_full_sample_nocap"] = 120.59
ev["magnitude_pct_note"] = (
    "magnitude_pct = 109.39% 为**后段（>=2013-08-28）口径**下的未计封顶上界（F-0022）；"
    "全样本口径上界为 120.59%（r03 记录 121.48%）；含封顶实测锚点净值 40.64%。")
ev["caveats"] = [
    "109.39% 是『未计封顶』的后段口径上界（全样本口径为 120.59%）。计入现行 E6 的 1 亿元总额封顶后，"
    "实测锚点下净值约 40.6%（F-0022 / F-0017）；低注数情形会被单注 1000 万上限抹平至 0%。",
    "校准口径已由 r04 从全样本 1.3603 改为后段 1.2472（F-0022）；含封顶净值对校准口径不敏感（封顶饱和）。",
    "该数字来自条件份额模拟（依赖人群权重模型，含 1 个校准参数 α），属『模型估计』而非数学事实，置信度仅 ★★★☆☆。",
    "只在中奖时兑现。中奖概率 4.67e-08 不变，期望回报的提升被极小概率大幅折现。",
    "长期期望回报仍为负（约 −0.98 元/注），本规则不改变这一事实。",
    "【分期与归因已复核】效应仍成立但随时间弱化；『衰减过半』是均值比口径的说法，稳健口径为 0.65~0.83（F-0020）。"
    "弱化与 2013-08 号码结构变点同期，且前段数据本身不自洽（F-0019 / F-0021）—— 因此本规则的幅度不应按全样本恒定外推。",
]
r1["evidence_refs"] = ["F-0003", "F-0004", "F-0017", "F-0019", "F-0020", "F-0021", "F-0022"]
print("[fix] R-001 幅度口径 → 后段（109.39% / 含封顶 40.64%）")

# ---- 2. A-006
for a in st["avoid_list"]:
    if a["id"] == "A-006":
        a["refuted_by"] = ["F-0011", "F-0025"]
        a["reason"] = (
            "『开出率』与『被选中率』必须分开（L7）：后区 66 组合的开出率与均匀一致（χ²=64.09，MC p=0.51，F-0011 复现）；"
            "但后区**被选中率**（人群密度）并不均匀 —— 过散布 8.72×，最热/最冷对密度比 2.25×（F-0025）。"
            "不过该结构不可靠利用：前/后段交叉验证的避让收益 K=5/10 仅约 1~3%、95%CI 含 0，"
            "且『热门对』排名跨期漂移（F-0025）。故『按后区历史规律选号』仍然是被驳回的做法 —— "
            "驳回理由由『没有结构』更正为『结构存在但不可靠可利用』。")
        print("[fix] A-006 理由更正（引用 F-0011 + F-0025）")

# ---- 3. A-009 新增
if not any(a["id"] == "A-009" for a in st["avoid_list"]):
    st["avoid_list"].append({
        "id": "A-009",
        "statement": "按『奖池累积期 / 高奖池』择时加注（等奖池大了再买）",
        "refuted_by": ["F-0023", "F-0024"],
        "reason": (
            "在可观测的一/二等奖派发口径下不存在稳健的『高期望期』：全局期初奖池分位 top−bottom 的每元期望派发差"
            "+0.090（F-0023）由 epoch 组成与 2019 年一次性奖池排空驱动，剔除 2019 后归零；"
            "现行 E6 下无显著效应（+0.017, p=0.30）。"
            "另外，用『派发额/销售额』衡量择时会误判 —— 高奖池期每注均价下降造成的组成效应会伪装成收益（F-0024）。"
            "唯一的机制候选（E6 规则文本『奖池>=8 亿时三至七等奖 +20%~40%』）缺少三至七等奖实发数据，无法核验（L10）。"),
    })
    print("[new] A-009 择时加注被驳回")

# ---- 4. evidence_index 重建 + provenance
used = set()
for r in st["rules"]:
    used.update(r.get("evidence_refs") or [])
for a in st["avoid_list"]:
    used.update(a.get("refuted_by") or [])
st["evidence_index"] = [
    {"id": fid, "claim": facts[fid]["claim"], "status": facts[fid]["status"],
     "confidence": facts[fid]["confidence"]}
    for fid in sorted(used)
]
st["generated_at"] = TODAY
prov = st.setdefault("provenance", {})
prov["iteration"] = "round04"
prov["generator"] = "manual (round04 衰减归因轮)"
prov["note"] = ("r04：R-001 幅度改为后段口径（F-0022）；A-006 理由更正（F-0025，L7 口径混淆）；"
                "新增 A-009（择时被 F-0023/F-0024 驳回）。"
                "evidence_hash = 全部被引结论规范视图的 SHA256。")
prov["evidence_hash"] = evidence_digest(list(facts.values()), sorted(used))

with open(ST, "w", encoding="utf-8", newline="\n") as f:
    json.dump(st, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"[write] {ST}")
print(f"[index] evidence_index {len(st['evidence_index'])} 条：{sorted(used)}")
print(f"[hash] {prov['evidence_hash'][:16]}…")
