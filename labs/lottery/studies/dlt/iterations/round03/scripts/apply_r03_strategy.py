# -*- coding: utf-8 -*-
"""apply_r03_strategy.py — T-004：把 r03 结论同步进 strategy.json

改动
----
  R-001.expected_value_impact
    · 新增 magnitude_pct_with_cap（封顶后净值）
    · caveats 重写：删掉「已实测触发封顶」的错误表述，改为「E6 从未触发但存在压缩」
    · caveats[4]「分期稳健性尚未验证」→ 已验证（幅度衰减）
  evidence_index
    · F-0003 / F-0004 的 claim 同步为更新后表述
    · 追加 F-0016 / F-0017 / F-0018 摘要
  R-001.applicable_epochs = ["E6"]
  provenance.iteration = "round03"
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.chdir(r"D:\PNOS\SPC")

PATH = "labs/lottery/studies/dlt/strategy/strategy.json"
d = json.load(open(PATH, encoding="utf-8"))

# ---- R-001 ----
r0 = d["rules"][0]
assert r0["id"] == "R-001", r0["id"]
ev = r0["expected_value_impact"]
ev["magnitude_pct"] = 121.48
ev["magnitude_pct_with_cap"] = 41.42
ev["magnitude_pct_with_cap_note"] = (
    "计 1 亿总额封顶后的实测锚点净值（F-0017）；121.48 为未计封顶上界。"
    "低注数情形会被单注 1000 万上限抹平至 0%。"
)
ev["caveats"] = [
    "121.48% 是『未计封顶』的上界。计入现行规则（E6）1 亿元总额封顶后，"
    "实测锚点下净值约 41.4%（F-0017）；低注数情形会被单注 1000 万上限抹平至 0%。",
    "封顶条款在 E6 现行规则 102 期中【从未实际触发】（F-0016），"
    "但其存在会压缩收益差 —— 早期版本的『已实测触发（26113 期）』表述有误，已由 F-0016 取代。",
    "该数字来自条件份额模拟（依赖人群权重模型，含 1 个校准参数 α=13.9405），"
    "属『模型估计』而非数学事实，置信度仅 ★★★☆☆。",
    "只在中奖时兑现。中奖概率 4.67e-08 不变，期望回报的提升被极小概率大幅折现。",
    "长期期望回报仍为负（约 −0.98 元/注），本规则不改变这一事实。",
    "【分期稳健性已完成】撞号效应在 2013-08 前后两段均同向且显著，"
    "但幅度衰减过半（前段一等奖比 2.11 → 后段 1.25；后段 CI 下界仅 1.03）。"
    "效应仍成立，但不应按全样本 1.36 恒定外推（F-0003 / T-001）。",
]
r0["applicable_epochs"] = ["E6"]
print("[fix] R-001.expected_value_impact 已同步（新增封顶后净值 + 重写 caveats）")

# ---- evidence_index ----
ei = {e["id"]: e for e in d["evidence_index"]}

if "F-0003" in ei:
    ei["F-0003"]["claim"] = (
        "连号形态（run>=2）的投注人群密度更高，撞号效应真实存在"
        "（全样本比 1.36；分期后幅度衰减过半但仍显著）"
    )
if "F-0004" in ei:
    ei["F-0004"]["claim"] = (
        "在固定预算下避开连号形态，可提高『中奖时的期望奖金』——"
        "未计封顶上界 121%，计入封顶后实测锚点下约 41%"
    )

# 追加新结论
for nid, claim, status, conf in [
    ("F-0016", "封顶条款在现行规则（E6）102 期中从未触发：一等奖总额最大仅 0.9788 亿",
     "established", 5),
    ("F-0017", "计入 1 亿封顶后，避开连号的期望奖金提升由 121% 降至实测锚点下约 41%",
     "established", 3),
    ("F-0018", "F-0003 的撞号效应不依赖均值比：中位数比 1.5 与截尾检验均支持，L5 技术债可清偿",
     "established", 4),
]:
    if nid not in ei:
        d["evidence_index"].append({"id": nid, "claim": claim,
                                    "status": status, "confidence": conf})
        print(f"[add] evidence_index += {nid}")

# F-0015 若在 index 中（superseded）→ 标 superseded
if "F-0015" in ei:
    ei["F-0015"]["status"] = "superseded"
    ei["F-0015"]["claim"] = (
        "【已修正】26113 期 37 注一等奖的单注 239 万是自然摊薄，并非封顶触发"
    )
    print("[fix] evidence_index F-0015 → superseded")

# ---- provenance ----
d.setdefault("provenance", {})
d["provenance"]["iteration"] = "round03"
d["generated_at"] = "2026-10-11"
if d.get("generated_by"):
    d["generated_by"] = "spc-cli/0.1.0"
print("[fix] provenance.iteration = round03, generated_at = 2026-10-11")

# ---- 写回 ----
with open(PATH, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"[write] {PATH}")
print(f"  rules={len(d['rules'])}  evidence_index={len(d['evidence_index'])}  "
      f"avoid_list={len(d['avoid_list'])}")
