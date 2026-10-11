# -*- coding: utf-8 -*-
"""sync_v2_final.py — 收尾：补登记 sync_v2_versions.py、更新 README 版本体系行、重渲染。"""
import io, sys, os, json
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\SPC"
TODAY = "2026-10-11"

vp = os.path.join(ROOT, "versions.json")
v = json.load(open(vp, encoding="utf-8"))
paths = {e["path"] for e in v["entries"]}

if "games/dlt/iterations/round06/scripts/sync_v2_versions.py" not in paths:
    v["entries"].append({
        "path": "games/dlt/iterations/round06/scripts/sync_v2_versions.py",
        "level": "A", "kind": "script", "content_version": "1.0",
        "iteration": "r06", "note": "v2.0 版本登记与 README 同步",
        "updated_at": TODAY, "status": "active"})
    print("[versions] + sync_v2_versions.py")
json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

c = Counter(e.get("level") for e in v["entries"])
total = len(v["entries"])
print(f"[versions] 共 {total} 条：{dict(c)}")

rp = os.path.join(ROOT, "README.md")
s = open(rp, encoding="utf-8").read()
old = f"| 版本体系 | ✅ A/B/C/D 四级分区，**159 条**登记（A=59 B=60 C=13 D=27），版本行全部一致 |"
new = (f"| 版本体系 | ✅ A/B/C/D 四级分区，**{total} 条**登记"
       f"（A={c['A']} B={c['B']} C={c['C']} D={c['D']}），版本行全部一致 |")
assert old in s, "README 版本体系行未找到"
s = s.replace(old, new, 1)
open(rp, "w", encoding="utf-8").write(s)
print(f"[README] 版本体系行 → {total} 条")

os.system(f'"{sys.executable}" tools/render_version_index.py --write')
print("[VERSION_INDEX] 已重渲染")
