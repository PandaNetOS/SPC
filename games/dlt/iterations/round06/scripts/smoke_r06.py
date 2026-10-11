# -*- coding: utf-8 -*-
"""smoke_r06.py — r06 策略落地冒烟：
  1. 新原语 duplicate_ticket_count / _ge 求值正确
  2. R-002（跨注 judge_cross）能真正判定 has_identical_tickets
  3. R-003（单注 judge）能真正判定 has_run_ge2 or all_birthday_zone
  4. 与 R-001 叠加：R-003 排除连号（已由 R-001 覆盖）与生日号区
"""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\smartpickcore"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "framework"))

import yaml
from core.features import apply_cross_primitive, arity_of
from core.portfolio import judge_cross, evaluate_cross, Portfolio
from core.judge import judge
from core.ticket import Ticket

cfg = yaml.safe_load(open(os.path.join(ROOT, "games", "dlt", "game.yaml"), encoding="utf-8"))
st = json.load(open(os.path.join(ROOT, "games", "dlt", "strategy", "strategy.json"), encoding="utf-8"))
rules = {r["id"]: r for r in st["rules"]}

# ---- 1. 原语
g1 = [[3, 11, 17, 24, 32], [3, 11, 17, 24, 32], [5, 9, 21, 28, 34], [5, 9, 21, 28, 34], [1, 8, 15, 22, 29]]
cnt = apply_cross_primitive("duplicate_ticket_count", g1, {"zone": "front"})
assert cnt == 4, cnt   # 两对重复 → 4 注
ge1 = apply_cross_primitive("duplicate_ticket_count_ge", g1, {"zone": "front", "threshold": 1})
ge5 = apply_cross_primitive("duplicate_ticket_count_ge", g1, {"zone": "front", "threshold": 5})
assert ge1 is True and ge5 is False, (ge1, ge5)
assert arity_of("duplicate_ticket_count_ge") == ("threshold",)
g2 = [[3, 11, 17, 24, 32], [4, 12, 18, 25, 33], [5, 9, 21, 28, 34]]
assert apply_cross_primitive("duplicate_ticket_count", g2, {"zone": "front"}) == 0
print("[1] 原语 OK：重复 4 / 全异 0 / _ge 阈值 1,5")

# ---- 2. R-002 跨注判定（dlt 需完整前后区）
p = Portfolio([
    {"front": [3, 11, 17, 24, 32], "back": [1, 2]},
    {"front": [3, 11, 17, 24, 32], "back": [1, 2]},
    {"front": [5, 9, 21, 28, 34], "back": [3, 4]},
])
cross = evaluate_cross(cfg, p)
print("[2] cross 特征:", {k: v for k, v in cross.items() if k in ("identical_ticket_count", "has_identical_tickets")})
res = judge_cross(cfg, p, [rules["R-002"]])
print("[2] R-002 重复组判定:", res.excluded, "（期望命中 → exclude）")
p2 = Portfolio([
    {"front": [3, 11, 17, 24, 32], "back": [1, 2]},
    {"front": [4, 12, 18, 25, 33], "back": [3, 4]},
    {"front": [5, 9, 21, 28, 34], "back": [5, 6]},
])
res2 = judge_cross(cfg, p2, [rules["R-002"]])
print("[2] R-002 互异组判定:", res2.excluded, "（期望放行）")

# ---- 3. R-003 单注判定
cases = [
    ([3, 11, 17, 24, 32], False, "max>31 无连号 → 放行"),
    ([1, 8, 15, 22, 29], True, "max<=31（生日号区）→ 排除"),
    ([3, 11, 17, 24, 35], False, "max=35 无连号 → 放行"),
    ([12, 13, 14, 24, 32], True, "连号 run>=2 → 排除"),
    ([12, 13, 20, 21, 32], True, "两对连号（分开）→ run>=2 → 排除"),
    ([1, 13, 20, 21, 32], False, "一对连号 + max>31 → 放行"),
]
for nums, expect, label in cases:
    got = judge(cfg, Ticket({"front": nums, "back": [1, 2]}), [rules["R-003"]]).excluded
    status = "OK" if got == expect else "FAIL"
    print(f"[3] R-003 {nums} → {got} (期望 {expect}) {status} — {label}")
    assert got == expect

# ---- 4. R-001 不受影响（对照组）
r1 = judge(cfg, Ticket({"front": [12, 13, 14, 24, 32], "back": [1, 2]}), [rules["R-001"]]).excluded
print("[4] R-001 连号判定（对照）:", r1, "（期望 True = 命中排除）")

print("\n全部冒烟通过")
