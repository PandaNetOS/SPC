# -*- coding: utf-8 -*-
"""T-030（round12）：策略有效性三档标准写入 strategy.schema.json（Q-008）"""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ---- 1) schema：schema_version 描述 + rules items 加 effectiveness_grade/basis
sp = r"spec\strategy.schema.json"
s = open(sp, encoding="utf-8").read()

old_required = '"required": ["id", "statement", "kind", "scope", "evidence_refs", "confidence", "expected_value_impact"],'
new_required = '"required": ["id", "statement", "kind", "scope", "evidence_refs", "confidence", "expected_value_impact", "effectiveness_grade"],'
assert old_required in s, "required anchor"
s = s.replace(old_required, new_required, 1)

eff_schema = '''          "effectiveness_grade": {
            "type": "string",
            "enum": ["A", "B", "C"],
            "description": "★ schema_version 1.4 新增（必填，T-030 / Q-008）。本规则『策略有效性』的三档标准：A=数学恒真（解析可证，无模型假设，如 R-002 自我摊薄公式）；B=统计确立（观测数据 + 样本外/测试窗验证 + 方向一致，如 R-001：后段 CI 下界>1 + r11 平台期 + r12 时序 hold-out 测试窗）；C=模型估计或探索性（依赖模型假设或样本有限）。任何规则不得声称提高中奖概率（各奖级恒定，红线）。"
          },
          "effectiveness_basis": {
            "type": "string",
            "minLength": 8,
            "description": "档位判定的依据（引用的观测/模拟/测试窗证据与口径），供消费者与复核者追溯。"
          },
'''
anchor = '          "evidence_refs": {'
assert anchor in s, "evidence_refs anchor"
s = s.replace(anchor, eff_schema + anchor, 1)
open(sp, "w", encoding="utf-8").write(s)
print("schema 1.4 已写入 effectiveness_grade")

# ---- 2) strategy.json：schema_version 1.4 + 三规则档位回填
jp = r"games\dlt\strategy\strategy.json"
j = json.load(open(jp, encoding="utf-8"))
j["schema_version"] = "1.4"
grades = {
    "R-001": ("B", "后段观测 R=1.2472（CI 下界 1.036）+ r11 F-0042 平台期 + r12 时序 hold-out 测试窗方向一致（cf=0.9531）——统计确立"),
    "R-002": ("A", "dup_share_ratio 解析公式 (1+m)/(K+m)（F-0027），数学恒真无模型假设"),
    "R-003": ("B", "F-0029 条件份额模拟 + r11 F-0043 代理确认（生日号区注数比稳定 ~1.2）+ r12 测试窗 cf=0.8721 方向一致——统计确立（量级含模型估计成分）"),
}
for r in j["rules"]:
    g, b = grades.get(r["id"], ("C", "待评估"))
    r["effectiveness_grade"] = g
    r["effectiveness_basis"] = b
json.dump(j, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("strategy.json → schema_version 1.4 + 三规则档位回填")
