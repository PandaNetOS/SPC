# -*- coding: utf-8 -*-
"""apply_r06_strategy.py — round06 同步对外策略（labs/lottery/studies/dlt/strategy/strategy.json）

用户已批准三项策略变更（2026-10-11）：
  ① R-002 权重 0.5 → 1.0：改为 action=exclude（不 penalize 结构同构）
  ② R-002 语义重构为「禁止完全相同号码」：predicate has_duplicated_structure →
     has_identical_tickets（F-0027/F-0028）
  ③ 新增 R-003：避开连号 + 生日号区（max<=31），predicate
     `has_run_ge2 == true or all_birthday_zone == true`（F-0029）

配套（已在脚本外完成）：
  - platform/core/features.py：新增跨注原语 duplicate_ticket_count(_ge)
  - labs/lottery/studies/dlt/game.yaml：新增 identical_ticket_count / has_identical_tickets 特征

幂等：可重复运行（R-003 已存在则跳过新增）。
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

# ---- 1+2. R-002 语义重构（权重语义 → exclude；predicate 换为完全相同号码）
r2 = next(r for r in st["rules"] if r["id"] == "R-002")
r2["statement"] = (
    "投注组合内**禁止出现完全相同的号码**（买 K 注相同号码 = 自我摊薄："
    "K=10、锚点 m=6 时每元期望回报损失 56.2%，见 F-0027）；"
    "号码不同但结构同构的组合**不在此列**（F-0028 已证：期望奖金与方差均无益）"
)
r2["machine_rule"] = {
    "predicate": "has_identical_tickets == true",
    "action": "exclude",
    "weight": None,
}
r2["evidence_refs"] = ["F-0027", "F-0028"]
r2["confidence"] = 3
ev2 = r2["expected_value_impact"]
ev2["metric"] = "bonus_given_win"
ev2["direction"] = "increase"
ev2["magnitude_pct"] = None
ev2["ci95"] = None
ev2["changes_win_probability"] = False
ev2["caveats"] = [
    "【r06 语义重构（用户批准）】旧 predicate has_duplicated_structure（结构同构）经量化后期望效应与方差理由均不成立"
    "（F-0028，Q-012 判据 not_established）—— 故不再 penalize 结构同构。",
    "真正有害的『重复』是**完全相同号码**：K 注相同 → 每元期望回报 = (1+m)/(K+m)；锚点 m=6 下 K=2/5/10 "
    "损失 12.5%/36.4%/56.2%（F-0027，解析结论）。",
    "predicate has_identical_tickets 为 r06 新增跨注特征（identical_ticket_count >= 1），"
    "需**整组号码**上下文（platform/core/portfolio.py 的 judge_cross() 执行）。",
    "本规则的 magnitude_pct 不填单一数字：修复增益依赖组内重复注数 K 与外部同号注数 m，解析式为 "
    "(K-1)/(K+m)（m=6 时 K=2 → +14.3%、K=10 → +128.6% 的上限参照）。",
    "不改变中奖概率（4.67e-08 恒定）；长期期望回报仍为负（约 −0.98 元/注）。",
]
r2["applicable_epochs"] = []
print("[fix] R-002 → 禁止完全相同号码（exclude / F-0027+F-0028）")

# ---- 3. R-003 新增
if not any(r["id"] == "R-003" for r in st["rules"]):
    st["rules"].append({
        "id": "R-003",
        "statement": (
            "避开『生日号区』：前区号码**不要全部落在 1~31**（max 须 >= 32）。"
            "与 R-001（避开连号）叠加：撞号系数 0.476 → 0.425，"
            "未计封顶期望奖金提升 +111.2% → **+136.2%**（F-0029）"
        ),
        "kind": "collision_avoidance",
        "scope": "single",
        "machine_rule": {
            "predicate": "has_run_ge2 == true or all_birthday_zone == true",
            "action": "exclude",
            "weight": None,
        },
        "evidence_refs": ["F-0003", "F-0004", "F-0022", "F-0029"],
        "confidence": 3,
        "expected_value_impact": {
            "metric": "bonus_given_win",
            "direction": "increase",
            "magnitude_pct": 136.2,
            "ci95": None,
            "changes_win_probability": False,
            "caveats": [
                "数字来自条件份额模拟（F-0029），依赖人群权重模型（连号 α=12.7815 + 生日号偏好 1.25，F-0022 校准），"
                "属『模型估计』，置信度 ★★★☆☆。",
                "含封顶口径：锚点 n0=6 处与 R-001 同为 +41.8%（单注 1000 万上限饱和抹平）；"
                "n0=9 处 +112.2% vs R-001 +110.6%。",
                "与 R-001 叠加执行：R-001 已排除连号（has_run_ge2==true），R-003 在其上再排除生日号区"
                "（all_birthday_zone==true，即 max<=31）。",
                "只在中奖时兑现。中奖概率 4.67e-08 不变，期望回报提升被极小概率大幅折现。",
                "长期期望回报仍为负（约 −0.98 元/注），本规则不改变这一事实。",
            ],
            "magnitude_pct_with_cap": 41.8,
            "magnitude_pct_with_cap_note": "锚点 n0=6（E6 基准注数）下的含封顶净值（F-0029/F-0017）；"
                                           "n0=9 处为 +112.2%。低注数情形会被单注上限抹平。",
        },
        "applicable_epochs": ["E6"],
    })
    print("[new] R-003 → 避开连号 + 生日号区（F-0029）")

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
prov["iteration"] = "round06"
prov["generator"] = "apply_r06_strategy.py (user-approved)"
prov["note"] = (
    "r06（用户批准三项）：R-002 语义重构为『禁止完全相同号码』（F-0027/F-0028），"
    "权重语义由 penalize 0.5 改为 exclude；新增 R-003（避开连号+生日号区，F-0029）。"
    "evidence_hash = 全部被引结论规范视图的 SHA256。")
prov["evidence_hash"] = evidence_digest(list(facts.values()), sorted(used))

with open(ST, "w", encoding="utf-8", newline="\n") as f:
    json.dump(st, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"[write] {ST}")
print(f"[rules] {len(st['rules'])} 条：{[r['id'] for r in st['rules']]}")
print(f"[index] evidence_index {len(st['evidence_index'])} 条：{sorted(used)}")
print(f"[hash] {prov['evidence_hash'][:16]}…")
