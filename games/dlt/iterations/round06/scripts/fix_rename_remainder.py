# -*- coding: utf-8 -*-
"""fix_rename_remainder.py — 修正首轮改名遗漏的引用。

规则：
  · 可执行路径/import：src/smartpickcore → src/spc；D:\\PNOS\\smartpickcore → D:\\PNOS\\SPC
  · 包名/import：smartpickcore → spc（pyproject scripts/include/package-data、src/__init__、历史脚本 import）
  · 品牌显示：smartpickcore → SPC（docs 标题/说明、strategy generated_by → spc-cli、versions.json repo → PandaNetOS/SPC）
"""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\smartpickcore"

def edit(p, pairs, tag):
    if not os.path.exists(p):
        return False
    s = open(p, encoding="utf-8").read()
    before = s
    for old, new in pairs:
        s = s.replace(old, new)
    if s != before:
        open(p, "w", encoding="utf-8").write(s)
        print(f"[{tag}] {p.replace(ROOT + chr(92), '')}")
        return True
    return False

PATH_OLD = "src/smartpickcore"
PATH_NEW = "src/spc"
DIR_OLD = r"D:\PNOS\smartpickcore"
DIR_NEW = r"D:\PNOS\SPC"
PKG_OLD = "smartpickcore"
PKG_NEW = "spc"

# 1. pyproject：scripts / include / package-data
edit(os.path.join(ROOT, "pyproject.toml"), [
    ('smartpickcore = "cli.main:main"', 'spc = "cli.main:main"'),
    ('include = ["smartpickcore*", "core*"]', 'include = ["spc*", "core*"]'),
    ('smartpickcore = ["py.typed"]', 'spc = ["py.typed"]'),
], "pyproject")

# 2. src/__init__.py 注释
edit(os.path.join(ROOT, "src", "__init__.py"), [(PKG_OLD, PKG_NEW)], "src-init")

# 3. strategy.json generated_by（不含 dlt 细节，纯标识）
edit(os.path.join(ROOT, "games", "dlt", "strategy", "strategy.json"),
     [('"generated_by": "smartpickcore-cli/0.1.0"', '"generated_by": "spc-cli/0.1.0"')], "strategy")

# 4. 历史/现行脚本：路径 + import + generated_by
script_files = [
    "games/dlt/iterations/round03/scripts/apply_r03_strategy.py",
    "games/dlt/iterations/round04/scripts/apply_r04_strategy.py",
    "games/dlt/iterations/round05/scripts/fix_r05_housekeeping.py",
    "games/dlt/iterations/round05/scripts/sync_r05_versions.py",
    "games/dlt/iterations/round06/scripts/add_v2_fields.py",
    "games/dlt/iterations/round06/scripts/apply_r06_strategy.py",
    "games/dlt/iterations/round06/scripts/probe_r06.py",
    "games/dlt/iterations/round06/scripts/probe_v2.py",
    "games/dlt/iterations/round06/scripts/smoke_ingate.py",
    "games/dlt/iterations/round06/scripts/smoke_r06.py",
    "games/dlt/iterations/round06/scripts/sync_guide_v14.py",
    "games/dlt/iterations/round06/scripts/sync_v2_final.py",
    "games/dlt/iterations/round06/scripts/sync_v2_versions.py",
    "games/dlt/iterations/round06/scripts/versions_r06_strategy.py",
]
for rel in script_files:
    edit(os.path.join(ROOT, rel), [
        (DIR_OLD, DIR_NEW),
        (PATH_OLD, PATH_NEW),
        ("smartpickcore-cli", "spc-cli"),
        ("from smartpickcore.", "from spc."),
    ], "script")

# 5. framework/core/__init__.py
edit(os.path.join(ROOT, "framework", "core", "__init__.py"), [
    ("smartpickcore.core", "spc.core"),
    (PATH_OLD, PATH_NEW),
    (PKG_OLD, PKG_NEW),
], "framework-core")

# 6. 文档：路径 → 小写 spc；标题/说明 → SPC
doc_pairs = [
    (PATH_OLD, PATH_NEW),
    (DIR_OLD, DIR_NEW),
    ("smartpickcore", "SPC"),
]
for rel in ("docs/ARCHITECTURE.md", "docs/METHODOLOGY.md",
            "docs/PROPOSAL_SINGLE_TICKET_CORE.md",
            "games/dlt/iterations/round02/FINDINGS.md",
            "games/dlt/iterations/round02/HANDOFF.md",
            "games/dlt/iterations/round05/HANDOFF.md",
            "memory/workbench/TODO.md", "memory/spec/ITERATION_SOP_v2.md"):
    edit(os.path.join(ROOT, rel), doc_pairs, "docs")

# 7. versions.json 根级 repo 字段
vp = os.path.join(ROOT, "versions.json")
v = json.load(open(vp, encoding="utf-8"))
if v.get("repo") == "PandaNetOS/smartpickcore":
    v["repo"] = "PandaNetOS/SPC"
    json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[versions] repo → PandaNetOS/SPC")

# 8. tests fixture generated_by（纯标识，一致性）
edit(os.path.join(ROOT, "tests", "fixtures", "shadow", "strategy", "strategy.json"),
     [('smartpickcore-tests/fixtures（人工夹具，非 CLI 生成）',
       'spc-tests/fixtures（人工夹具，非 CLI 生成）')], "fixture")

print("[fix_rename_remainder] 完成")
