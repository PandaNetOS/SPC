# -*- coding: utf-8 -*-
"""probe_v2.py — 探查 FACTS 全部条目概要 + game.yaml 迭代字段。"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\SPC"

facts = [json.loads(l) for l in open(ROOT + r"\memory\facts\FACTS.jsonl", encoding="utf-8") if l.strip()]
print("total:", len(facts))
for f in facts:
    dyn = []
    ev = f.get("evidence") or {}
    eff = ev.get("effect") or {}
    txt = (f.get("claim", "") + str(eff)).lower()
    for kw in ("pool", "奖池", "封顶", "e6", "锚点", "n0", "1000万", "1亿"):
        if kw in txt:
            dyn.append(kw)
    print(f["id"], f["status"], f["claim_type"], f["confidence"],
          f["established_in"], "| dyn:", ",".join(dyn) or "-")

print("=== game.yaml 相关行 ===")
s = open(ROOT + r"\games\dlt\game.yaml", encoding="utf-8").read()
for i, l in enumerate(s.split("\n"), 1):
    if re.search(r"iteration|last_round|current_round|round_", l):
        print(i, l.strip()[:100])
