# -*- coding: utf-8 -*-
"""smoke_ingate.py — 入库三闸门自测（缺陷样例→拒绝，合法样例→入库）。"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"D:\PNOS\SPC\framework")
from tools.ingate import run  # noqa: E402

BAD = {
    "id": "F-9XXX", "claim": "某个没有任何证据支撑的经验断言缺乏数据版本说明",
    "claim_type": "empirical", "evidence": {"method": "观测"},
}
GOOD = {
    "id": "F-9YYY",
    "claim": "后段数据中冷热号码的长期期望收益差保持统计不显著且置信区间过零",
    "claim_type": "empirical",
    "evidence": {"method": "观测+Bootstrap", "data_version": "dlt_full_2933",
                 "n_observations": 1973, "effect": {"d": 0.012},
                 "ci95": [-0.031, 0.055], "p_value": 0.58},
    "caveats": ["仅覆盖后段口径", "锚点变化会改变基线"],
}
print("########## 样例 1：缺陷（预期 exit=2 建议拒绝） ##########")
r1 = run(BAD)
print("exit =", r1)
print("\n########## 样例 2：合法（预期 exit=0 直接入库） ##########")
r2 = run(GOOD)
print("exit =", r2)
assert r1 == 2, f"缺陷样例应拒绝，实际 {r1}"
assert r2 == 0, f"合法样例应通过，实际 {r2}"
print("\n[SMOKE] 三闸门全部符合预期")
