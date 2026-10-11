# -*- coding: utf-8 -*-
"""probe_r06.py — 探查原语与结论原文。"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

s = open(r"D:\PNOS\SPC\framework\core\features.py", encoding="utf-8").read()
keys = re.findall(r'"([a-z_0-9]+)"\s*:', s)
print("原语键（含重复类关键词）:", [k for k in keys if any(w in k for w in ["dup", "ident", "struct", "same", "exact", "repeat", "unique"])])
m = re.search(r"PRIMITIVES\s*=\s*\{", s)
if m:
    print("PRIMITIVES 定义位置:", m.start(), "上下文:")
    print(s[m.start():m.start()+1200])
else:
    print("PRIMITIVES 未找到，打印 features.py 前 60 行:")
    print("\n".join(s.split("\n")[:60]))

facts = [json.loads(l) for l in open(r"D:\PNOS\SPC\memory\facts\FACTS.jsonl", encoding="utf-8") if l.strip()]
for fid in ["F-0027", "F-0028", "F-0029"]:
    f = next(x for x in facts if x["id"] == fid)
    print("====", fid, f["status"], f["confidence"])
    print("claim:", f["claim"][:260])
