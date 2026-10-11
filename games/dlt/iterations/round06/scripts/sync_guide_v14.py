# -*- coding: utf-8 -*-
"""sync_guide_v14.py — STRATEGY_GUIDE §7 超链接后的版本同步（1.3 → 1.4）。"""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\smartpickcore"

vp = os.path.join(ROOT, "versions.json")
v = json.load(open(vp, encoding="utf-8"))
for e in v["entries"]:
    if e["path"] == "games/dlt/strategy/STRATEGY_GUIDE.md":
        e["content_version"] = "1.4"
        e["updated_at"] = "2026-10-11"
        e["note"] = "r06：R-002 重构 + R-003 新增；§7 参考表格加超链接"
        print("[versions] STRATEGY_GUIDE →", e["content_version"])
json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

rp = os.path.join(ROOT, "README.md")
s = open(rp, encoding="utf-8").read()
old1 = "STRATEGY_GUIDE.md) &nbsp;`v1.3`"
old2 = "版本 `v1.3`（轮次 `r06`，更新 2026-10-11）"
assert old1 in s and old2 in s, "README 标注未找到"
s = s.replace(old1, "STRATEGY_GUIDE.md) &nbsp;`v1.4`")
s = s.replace(old2, "版本 `v1.4`（轮次 `r06`，更新 2026-10-11）")
open(rp, "w", encoding="utf-8").write(s)
print("[README] 标注 → v1.4")

os.system(f'"{sys.executable}" tools/render_version_index.py --write')
print("[VERSION_INDEX] 已重渲染")
