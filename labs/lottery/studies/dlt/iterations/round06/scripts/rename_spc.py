# -*- coding: utf-8 -*-
"""rename_spc.py — 仓库改名 smartpickcore → SPC（全链路本地部分）。

策略：
  · 包名/import：smartpickcore → spc（PEP 503 小写；src/smartpickcore → src/spc，git mv 保留历史）
  · 品牌显示（文档/标题/说明）：smartpickcore → SPC
  · GitHub repo 标识：PandaNetOS/smartpickcore → PandaNetOS/SPC

执行：
  1. git mv src/smartpickcore src/spc
  2. 代码文件（src/spc、cli、tests、framework）：import/包路径 smartpickcore → spc
  3. 品牌文件（README/AI_CONTEXT/docs/INDEX/render/build_versions/spec $id）：smartpickcore → SPC
  4. versions.json：path src/smartpickcore/ → src/spc/，其余 → SPC
  5. pyproject name → "spc"
"""
import io, sys, os, re, json, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\smartpickcore"

# 1. git mv 包目录
src_old = os.path.join(ROOT, "src", "smartpickcore")
src_new = os.path.join(ROOT, "src", "spc")
if os.path.isdir(src_old) and not os.path.isdir(src_new):
    r = subprocess.run(["git", "mv", "src/smartpickcore", "src/spc"],
                       cwd=ROOT, capture_output=True, text=True)
    print("[git mv]", "OK" if r.returncode == 0 else r.stderr.strip())
elif os.path.isdir(src_new):
    print("[git mv] src/spc 已存在，跳过")

# 2. 代码文件：smartpickcore → spc（包名/import）
code_files = []
for rel in ("cli/main.py",):
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        code_files.append(p)
for name in os.listdir(os.path.join(ROOT, "tests")):
    if name.endswith(".py"):
        code_files.append(os.path.join(ROOT, "tests", name))
for name in os.listdir(src_new):
    if name.endswith(".py"):
        code_files.append(os.path.join(src_new, name))
for rel in ("platform/core/evaluate.py", "platform/core/features.py",
            "platform/core/game_util.py", "platform/core/generate.py",
            "platform/core/judge.py", "platform/core/portfolio.py",
            "platform/core/ticket.py", "platform/tools/memory.py",
            "platform/tools/ingate.py", "platform/tools/compress_memory.py"):
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        code_files.append(p)

n_code = 0
for p in code_files:
    s = open(p, encoding="utf-8").read()
    if "smartpickcore" not in s:
        continue
    s2 = s.replace("smartpickcore", "spc")
    open(p, "w", encoding="utf-8").write(s2)
    n_code += 1
print(f"[code] {n_code} 个代码文件 smartpickcore → spc")

# 3. 品牌文件：smartpickcore → SPC（含 repo 标识）
brand_files = [
    "README.md", "AI_CONTEXT.md", "VERSION_INDEX.md",
    "docs/CONSUMING.md", "labs/lottery/INDEX.md", "memory/INDEX.md",
    "tools/build_versions.py", "tools/render_version_index.py",
    "spec/README.md", "spec/VERSIONING.md",
    "spec/fact.schema.json", "spec/game_config.schema.json",
    "spec/iteration.schema.json", "spec/strategy.schema.json",
    "spec/version_index.schema.json",
]
n_brand = 0
for rel in brand_files:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        continue
    s = open(p, encoding="utf-8").read()
    if "smartpickcore" not in s:
        continue
    open(p, "w", encoding="utf-8").write(s.replace("smartpickcore", "SPC"))
    n_brand += 1
print(f"[brand] {n_brand} 个品牌文件 smartpickcore → SPC")

# 4. versions.json：path src/smartpickcore/ → src/spc/，其余 → SPC
vp = os.path.join(ROOT, "versions.json")
v = json.load(open(vp, encoding="utf-8"))
for e in v["entries"]:
    if "smartpickcore" in (e.get("path") or ""):
        e["path"] = e["path"].replace("smartpickcore", "spc")
    for k in ("note",):
        if "smartpickcore" in (e.get(k) or ""):
            e[k] = e[k].replace("smartpickcore", "SPC")
json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"[versions] path/note 已同步（{len(v['entries'])} 条）")

# 5. pyproject name
pp = os.path.join(ROOT, "pyproject.toml")
s = open(pp, encoding="utf-8").read()
s = s.replace('name = "smartpickcore"', 'name = "spc"')
open(pp, "w", encoding="utf-8").write(s)
print("[pyproject] name → spc")

# 6. platform/protocol、methodology 里的路径引用
for rel in ("platform/protocol/ITERATION_PROTOCOL.md",
            "platform/protocol/MEMORY_PROTOCOL.md",
            "platform/methodology/MATH_BOUNDARY.md",
            "platform/methodology/STATISTICAL_DISCIPLINE.md"):
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        if "smartpickcore" in s:
            open(p, "w", encoding="utf-8").write(s.replace("smartpickcore", "SPC"))
            print(f"[brand] {rel}")
print("[rename_spc] 完成")
