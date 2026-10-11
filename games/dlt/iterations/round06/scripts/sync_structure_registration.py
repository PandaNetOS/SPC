# -*- coding: utf-8 -*-
"""sync_structure_registration.py — 结构完整性（P1-2）补登记 + 目录树写回。

1. versions.json 补登记 7 个受管文件（check_structure 首跑暴露）：
   round06 5 个脚本（A/1.0）、src/spc/tree.py + tools/render_readme_tree.py（B，代码不版本化）
2. 更新 tests/README.md 的过期 note（323 → 325 自举计数）
3. 写回 README 目录树（render_readme_tree --write）
4. 重渲染 VERSION_INDEX
"""
import io, sys, os, json, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\SPC"
TODAY = "2026-10-11"

vp = os.path.join(ROOT, "versions.json")
v = json.load(open(vp, encoding="utf-8"))
paths = {e["path"] for e in v["entries"]}

NEW = [
    {"path": "games/dlt/iterations/round06/scripts/fix_rename_remainder.py",
     "level": "A", "kind": "script", "content_version": "1.0", "iteration": "r06",
     "note": "改名残余引用修正（路径/import/标识）", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/rename_spc.py",
     "level": "A", "kind": "script", "content_version": "1.0", "iteration": "r06",
     "note": "全链路改名：git mv src→spc + 包/品牌替换", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/sync_guide_v14.py",
     "level": "A", "kind": "script", "content_version": "1.0", "iteration": "r06",
     "note": "STRATEGY_GUIDE v1.4 同步", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/sync_v2_final.py",
     "level": "A", "kind": "script", "content_version": "1.0", "iteration": "r06",
     "note": "v2.0 收尾：版本登记 + README 计数同步", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/versions_r06_strategy.py",
     "level": "A", "kind": "script", "content_version": "1.0", "iteration": "r06",
     "note": "r06 策略落地的版本登记", "updated_at": TODAY, "status": "active"},
    {"path": "src/spc/tree.py", "level": "B", "kind": "code",
     "iteration": "r06",
     "note": "目录树生成源（P1-2）：README 树 = 派生物", "updated_at": TODAY, "status": "active"},
    {"path": "tools/render_readme_tree.py", "level": "B", "kind": "code",
     "iteration": "r06",
     "note": "目录树渲染 CLI（--write 写回 README）", "updated_at": TODAY, "status": "active"},
]
added = 0
for ne in NEW:
    if ne["path"] not in paths:
        v["entries"].append(ne)
        added += 1
json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"[versions] +{added} 条登记，共 {len(v['entries'])} 条")

# tests/README.md note 更新（自举计数 323 → 325）
for e in v["entries"]:
    if e["path"] == "tests/README.md":
        e["note"] = "测试说明（自举计数：合计 325，无需 pytest）"
        e["updated_at"] = TODAY
json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("[versions] tests/README.md note 已更新")

# 写回 README 目录树
r = subprocess.run([sys.executable, "tools/render_readme_tree.py", "--write"],
                   cwd=ROOT, capture_output=True, text=True)
print("[tree]", (r.stdout or r.stderr).strip())

# 重渲染 VERSION_INDEX
r = subprocess.run([sys.executable, "tools/render_version_index.py", "--write"],
                   cwd=ROOT, capture_output=True, text=True)
print("[vindex]", (r.stdout or r.stderr).strip())
