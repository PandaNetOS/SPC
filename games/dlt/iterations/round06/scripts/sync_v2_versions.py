# -*- coding: utf-8 -*-
"""sync_v2_versions.py — v2.0 机制落地的版本登记与 README 同步。

1. versions.json：
   - 新增：framework/tools/ingate.py、compress_memory.py、memory/spec/ITERATION_SOP_v2.md、
     memory/facts/ACTIVE.md、round06/add_v2_fields.py、smoke_ingate.py、probe_v2.py
   - 更新 note：spec/fact.schema.json（v2.0 字段）、src/spc/validate.py（v2.0 检查）
2. README.md：记忆层行提及 v2.0 机制；校验行不变（32 条 / 67 项 / 325 项）。
3. 重渲染 VERSION_INDEX.md。
"""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\SPC"
TODAY = "2026-10-11"

# ---- versions.json
vp = os.path.join(ROOT, "versions.json")
v = json.load(open(vp, encoding="utf-8"))
existing = {e["path"] for e in v["entries"]}

def bump(path, **kw):
    for e in v["entries"]:
        if e["path"] == path:
            e.update({k: val for k, val in kw.items() if val is not None})
            return True
    return False

bump("spec/fact.schema.json", iteration="r06", updated_at=TODAY,
     note="v2.0：新增 confidence_grade（GRADE）/ change_type（update-revision）/ valid_until / recalibrate_every")
bump("src/spc/validate.py", iteration="r06", updated_at=TODAY,
     note="v2.0：INV2 引用链升级（禁引被推翻结论）+ INV3 取代链环检测 + grade/change_type 校验 + 动态锚点重校准检查 + 策略-证据一致性")

new_entries = [
    {"path": "framework/tools/ingate.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r06",
     "note": "入库三闸门（filter/judge/manager，LSTM-MAS 依据）", "updated_at": TODAY, "status": "active"},
    {"path": "framework/tools/compress_memory.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r06",
     "note": "记忆压缩（每 5 轮）：ACTIVE.md + merge 候选 + 到期清单（IterResearch 依据）",
     "updated_at": TODAY, "status": "active"},
    {"path": "memory/spec/ITERATION_SOP_v2.md", "level": "A", "kind": "doc",
     "content_version": "1.0", "iteration": "r06",
     "note": "证据门控式迭代规范 v2.0：三层信念基/原子操作/三闸门/矛盾双通道/INV1-3/重校准/压缩",
     "updated_at": TODAY, "status": "active"},
    {"path": "memory/facts/ACTIVE.md", "level": "D", "kind": "report",
     "content_version": "1.0", "iteration": "r06",
     "note": "当前有效结论清单（与台账分离，compress_memory 生成）", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/add_v2_fields.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r06",
     "note": "FACTS v2.0 字段迁移（grade/change_type/有效期）", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/smoke_ingate.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r06",
     "note": "三闸门自测（缺陷→拒绝 / 合法→入库）", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/probe_v2.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r06",
     "note": "v2.0 实施前的 FACTS/结构探查", "updated_at": TODAY, "status": "active"},
]
added = 0
for ne in new_entries:
    if ne["path"] not in existing:
        v["entries"].append(ne)
        added += 1
json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"[versions] +{added} 条登记，共 {len(v['entries'])} 条")

# ---- README
rp = os.path.join(ROOT, "README.md")
s = open(rp, encoding="utf-8").read()
old = "| 记忆层 | ✅ **32 条结论**（每条带 `claim_type` 证据类型 + `source_sha256` 证据锚定）/ L1–L14 / 8 开放问题（7 answered）/ 6 假设（2 已推翻）/ 待办（P0 已清空） |"
new = "| 记忆层 | ✅ **32 条结论**（每条带 `claim_type` 证据类型 + `source_sha256` 证据锚定 + **v2.0** `confidence_grade`/`change_type`/重校准周期）/ L1–L14 / 8 开放问题（7 answered）/ 6 假设（2 已推翻）/ 待办（P0 已清空） |"
assert old in s, "README 记忆层行未找到"
s = s.replace(old, new, 1)
old2 = "| 库与 CLI | ✅ 9 模块 + 14 命令，`validate --all` **67 项全绿** |"
new2 = "| 库与 CLI | ✅ 9 模块 + 14 命令，`validate --all` **67 项全绿**（含 v2.0：INV2 引用链 / INV3 取代链环检测 / 动态锚点重校准 / 策略-证据一致性） |"
assert old2 in s, "README 库与 CLI 行未找到"
s = s.replace(old2, new2, 1)
open(rp, "w", encoding="utf-8").write(s)
print("[README] 记忆层/校验行已更新")

# ---- 重渲染
os.system(f'"{sys.executable}" tools/render_version_index.py --write')
print("[VERSION_INDEX] 已重渲染")
