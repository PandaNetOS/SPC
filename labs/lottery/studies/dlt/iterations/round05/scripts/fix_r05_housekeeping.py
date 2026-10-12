# -*- coding: utf-8 -*-
"""fix_r05_housekeeping.py — round05 收轮维护：
  1. 修复 FACTS.jsonl 4 条 tag（大写 → 小写，合规 ^[a-z0-9_-]+$）
  2. 更新 versions.json（current_iteration、版本/note、round05 新条目）
  3. README.md / AI_CONTEXT.md 计数与版本行同步
  4. labs/lottery/INDEX.md 结论数与轮次状态同步
"""
import sys, io, os, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"D:\PNOS\SPC"
TODAY = "2026-10-11"

# ============================================================
# 1. FACTS tags 修复
# ============================================================
FACTS = os.path.join(ROOT, "memory", "facts", "FACTS.jsonl")
facts = [json.loads(l) for l in open(FACTS, encoding="utf-8") if l.strip()]
tag_fix = {
    "F-0028": ["r002", "cross_scope", "simulation", "l2", "l5"],
    "F-0029": ["r003_candidate", "simulation", "birthday_effect", "l2", "l5"],
    "F-0030": ["timing", "weekday", "h005_closed", "collision", "l5", "l13"],
    "F-0032": ["holiday", "timing", "tentative", "h006", "l5"],
}
for f in facts:
    if f["id"] in tag_fix:
        f["tags"] = tag_fix[f["id"]]
        print(f"[tag] {f['id']} -> {f['tags']}")
with open(FACTS, "w", encoding="utf-8") as fh:
    for f in sorted(facts, key=lambda x: x["id"]):
        fh.write(json.dumps(f, ensure_ascii=False) + "\n")
print(f"[facts] {len(facts)} 条已写回")

# ============================================================
# 2. versions.json
# ============================================================
VP = os.path.join(ROOT, "versions.json")
v = json.load(open(VP, encoding="utf-8"))
v["current_iteration"] = "r05"

def bump(path, **kw):
    hit = False
    for e in v["entries"]:
        if e["path"] == path:
            e.update({k: val for k, val in kw.items() if val is not None})
            hit = True
    return hit

bump("labs/lottery/studies/dlt/memory/facts/FACTS.jsonl",
     content_version="1.5", note="32 条结论（F-0001~F-0032；F-0015/F-0007 superseded）；r05 新增 F-0026~F-0032（投注方式/时间因素）")
bump("labs/lottery/studies/dlt/memory/facts/INDEX.md",
     content_version="1.5", note="派生物，由 cli index 生成（32 条）")
bump("labs/lottery/studies/dlt/memory/workbench/HYPOTHESES.md",
     content_version="1.2", note="H-001~H-006；r04：H-004 被 F-0023 推翻；r05：H-005 被 F-0030 证伪（方向相反）、新增 H-006")
bump("labs/lottery/studies/dlt/memory/workbench/OPEN_QUESTIONS.md",
     content_version="1.4", note="15 问，7 answered（Q-001/Q-002/Q-004 r03；Q-003/Q-007/Q-010 r04；Q-012 r05）")
bump("labs/lottery/studies/dlt/memory/workbench/TODO.md",
     content_version="1.6", note="r05 清算 T-011/T-202/T-205/T-206；新增 T-016（H-006）；T-014/T-015 顺延 r06 首推")
bump("labs/lottery/studies/dlt/iterations/round05/TASK_BRIEF.md",
     status="active", note="已交付（round05 执行完毕；用户点名方向优先，T-201 顺延 r06）")
bump("AI_CONTEXT.md",
     content_version="1.5", note="单一入口；r05 同步投注方式等价性、R-002 量化不成立、H-005 证伪、32 条结论")
bump("README.md",
     content_version="1.13", note="仓库总览；r05 同步投注方式/时间因素研究要点、32 条结论")

# 新增 round05 条目（不存在则追加）
new_entries = [
    {"path": "labs/lottery/studies/dlt/iterations/round05/FINDINGS.md", "level": "A", "kind": "iteration_artifact",
     "content_version": "1.0", "iteration": "r05", "note": "投注方式数学层 + R-002 量化 + 时间因素证伪", "updated_at": TODAY, "status": "active"},
    {"path": "labs/lottery/studies/dlt/iterations/round05/HANDOFF.md", "level": "A", "kind": "iteration_artifact",
     "content_version": "1.0", "iteration": "r05", "note": "r05→r06 交接；策略变更待用户批准", "updated_at": TODAY, "status": "active"},
    {"path": "labs/lottery/studies/dlt/iterations/round05/manifest.json", "level": "B", "kind": "manifest",
     "content_version": "1.0", "iteration": "r05", "note": "", "updated_at": TODAY, "status": "active"},
    {"path": "labs/lottery/studies/dlt/memory/journal/round05.md", "level": "B", "kind": "journal",
     "content_version": "1.0", "iteration": "r05", "note": "叙事：R-002 量化不成立 + H-005 证伪", "updated_at": TODAY, "status": "active"},
    {"path": "labs/lottery/studies/dlt/iterations/round06/TASK_BRIEF.md", "level": "A", "kind": "iteration_artifact",
     "content_version": "1.0", "iteration": "r06", "note": "由 round05 HANDOFF 转写（planned；T-201 前段取证首推）", "updated_at": TODAY, "status": "active"},
]
existing = {e["path"] for e in v["entries"]}
for ne in new_entries:
    if ne["path"] not in existing:
        v["entries"].append(ne)
        print(f"[versions +] {ne['path']}")
    else:
        print(f"[versions ~] {ne['path']} 已存在")

with open(VP, "w", encoding="utf-8") as fh:
    json.dump(v, fh, ensure_ascii=False, indent=2)
print(f"[versions] current_iteration = {v['current_iteration']}，entries = {len(v['entries'])}")

# ============================================================
# 3. README.md / AI_CONTEXT.md
# ============================================================
def patch(path, subs):
    s = open(path, encoding="utf-8").read()
    for old, new in subs:
        if old not in s:
            print(f"  [WARN] 未找到替换目标（{path}）: {old[:60]}")
            continue
        s = s.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(s)
    print(f"[patch] {path}")

patch(os.path.join(ROOT, "README.md"), [
    ("> **版本**：`1.12` ｜ 轮次 `r04` ｜ 更新 2026-10-11",
     "> **版本**：`1.13` ｜ 轮次 `r05` ｜ 更新 2026-10-11"),
    ("FACTS.jsonl        v1.4   ← 结论台账（25 条，JSONL 追加式；每条带 claim_type + source_sha256）",
     "FACTS.jsonl        v1.5   ← 结论台账（32 条，JSONL 追加式；每条带 claim_type + source_sha256）"),
    ("INDEX.md           v1.4   ← 速览（派生物，CLI 生成，勿手改）",
     "INDEX.md           v1.5   ← 速览（派生物，CLI 生成，勿手改）"),
    ("| 记忆层 | ✅ **25 条结论**（每条带 `claim_type` 证据类型 + `source_sha256` 证据锚定）/ L1–L14 / 15 开放问题（6 answered）/ 5 假设（1 已推翻）/ 待办（P0 已清空） |",
     "| 记忆层 | ✅ **32 条结论**（每条带 `claim_type` 证据类型 + `source_sha256` 证据锚定）/ L1–L14 / 8 开放问题（7 answered）/ 6 假设（2 已推翻）/ 待办（P0 已清空） |"),
])

patch(os.path.join(ROOT, "AI_CONTEXT.md"), [
    ("> **版本**：`1.4` ｜ 轮次 `r04` ｜ 更新 2026-10-11",
     "> **版本**：`1.5` ｜ 轮次 `r05` ｜ 更新 2026-10-11"),
    ("**权威源是 `labs/lottery/studies/dlt/memory/facts/FACTS.jsonl`（25 条）**，此处只列最重要的几条。",
     "**权威源是 `labs/lottery/studies/dlt/memory/facts/FACTS.jsonl`（32 条）**，此处只列最重要的几条。"),
])

# ============================================================
# 4. labs/lottery/INDEX.md
# ============================================================
GI = os.path.join(ROOT, "games", "INDEX.md")
g = open(GI, encoding="utf-8").read()
g = g.replace("| `dlt` | 超级大乐透 | 21,425,712 | 4.667289469773513e-08 | 51% | 25 | round04 ✅ / round05 计划中 |",
              "| `dlt` | 超级大乐透 | 21,425,712 | 4.667289469773513e-08 | 51% | 32 | round05 ✅ |")
g = g.replace("│   └── round05/      #     计划中：TASK_BRIEF（前段数据取证 + R-002 量化）",
              "│   ├── round05/      #     已完成：投注方式 + 时间因素（FINDINGS / HANDOFF / manifest + 3 脚本 + 2 JSON）\n│   └── round06/      #     计划中：TASK_BRIEF（前段数据取证，r06 首推）")
open(GI, "w", encoding="utf-8").write(g)
print(f"[patch] {GI}")
for i, l in enumerate(g.split("\n"), 1):
    if any(k in l for k in ("结论数", "round0", "已完成", "计划中")):
        print(f"  {i}: {l.strip()[:130]}")
