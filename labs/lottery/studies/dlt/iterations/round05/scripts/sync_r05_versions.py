# -*- coding: utf-8 -*-
"""sync_r05_versions.py — 同步工作台文件版本行 + README 树标注 + versions.json iteration。"""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\SPC"

# 1) 文件头版本行
patch = {
    os.path.join(ROOT, "memory", "workbench", "HYPOTHESES.md"): [
        ("> **版本**：`1.1` ｜ 轮次 `r04`", "> **版本**：`1.2` ｜ 轮次 `r05`"),
    ],
    os.path.join(ROOT, "memory", "workbench", "OPEN_QUESTIONS.md"): [
        ("> **版本**：`1.3` ｜ 轮次 `r04`", "> **版本**：`1.4` ｜ 轮次 `r05`"),
    ],
}
for p, subs in patch.items():
    s = open(p, encoding="utf-8").read()
    for old, new in subs:
        assert old in s, (p, old)
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("[header]", p)

# 2) README 目录树标注
p = os.path.join(ROOT, "README.md")
s = open(p, encoding="utf-8").read()
for old, new in [
    ("TODO.md            v1.5   ← 任务台账（P0 已清空）", "TODO.md            v1.6   ← 任务台账（P0 已清空）"),
    ("OPEN_QUESTIONS.md  v1.3   ← 开放问题（15，6 answered）", "OPEN_QUESTIONS.md  v1.4   ← 开放问题（15，7 answered）"),
    ("HYPOTHESES.md      v1.1   ← 假设（5；H-004 已推翻）", "HYPOTHESES.md      v1.2   ← 假设（6；H-004/H-005 已推翻）"),
]:
    assert old in s, old
    s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("[README tree] ok")

# 3) versions.json iteration 字段
vp = os.path.join(ROOT, "versions.json")
v = json.load(open(vp, encoding="utf-8"))
for e in v["entries"]:
    if e["path"] in [
        "labs/lottery/studies/dlt/memory/workbench/TODO.md",
        "labs/lottery/studies/dlt/memory/workbench/HYPOTHESES.md",
        "labs/lottery/studies/dlt/memory/workbench/OPEN_QUESTIONS.md",
        "AI_CONTEXT.md",
        "README.md",
    ]:
        e["iteration"] = "r05"
        print("[versions iteration]", e["path"], "->", e["iteration"])
json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("versions.json written")
