# -*- coding: utf-8 -*-
"""add_v2_fields.py — 给 FACTS.jsonl 全部条目加 v2.0 字段（一次性迁移）。

新增字段（spec/fact.schema.json 已同步）：
  confidence_grade  : GRADE 式置信度映射（5/4→high, 3→moderate, 2/1→low）
  change_type       : initial（历史条目全部为首立；后续 update/revision 由新条目携带）
  valid_until       : 显式过期日，动态锚点类结论可标（本次全部 null）
  recalibrate_every : 动态锚点类结论的重校准周期（轮数）= 5；其余 null

动态锚点类（依赖奖池/封顶/E6/锚点数值，随开奖变化）：
  F-0004 F-0005 F-0016 F-0017 F-0022 F-0023 F-0028 F-0029 F-0031
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\SPC"
FP = ROOT + r"\memory\facts\FACTS.jsonl"

GRADE_MAP = {5: "high", 4: "high", 3: "moderate", 2: "low", 1: "low"}
DYNAMIC_ANCHOR = {"F-0004", "F-0005", "F-0016", "F-0017", "F-0022",
                  "F-0023", "F-0028", "F-0029", "F-0031"}

rows = [json.loads(l) for l in open(FP, encoding="utf-8") if l.strip()]
out = []
for f in rows:
    fid = f["id"]
    f["confidence_grade"] = GRADE_MAP[f["confidence"]]
    f["change_type"] = "initial"
    if fid in DYNAMIC_ANCHOR:
        f["valid_until"] = None
        f["recalibrate_every"] = 5
    else:
        f["valid_until"] = None
        f["recalibrate_every"] = None
    out.append(f)

with open(FP, "w", encoding="utf-8") as fh:
    for f in out:
        fh.write(json.dumps(f, ensure_ascii=False) + "\n")
print(f"[add_v2_fields] 已更新 {len(out)} 条 FACTS（动态锚点 {len(DYNAMIC_ANCHOR)} 条 recalibrate_every=5）")

# 校验：schema 合规 + 映射一致
import subprocess
r = subprocess.run([sys.executable, "cli/main.py", "validate", "--all"],
                   capture_output=True, text=True, cwd=ROOT)
print(r.stdout[-400:] if r.stdout else r.stderr[-400:])
