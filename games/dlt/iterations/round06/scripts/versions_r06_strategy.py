# -*- coding: utf-8 -*-
"""versions_r06_strategy.py — r06 策略落地的版本登记与 README 同步。

1. versions.json：
   - STRATEGY_GUIDE.md → 1.3 / r06
   - strategy.json → 1.3 / r06（note 更新）
   - game.yaml → note 更新（跨注特征 3→5；R-002 判定量变更）
   - features.py → note 更新（新增 duplicate_ticket_count/_ge）
   - 新增 round05 scripts 条目（bet_structure/timing_weekday/apply_r05_facts/fix_r05_housekeeping/sync_r05_versions）
   - 新增 round06 scripts 条目（apply_r06_strategy/smoke_r06/probe_r06）
2. README.md：test_cross_scope 62→64、共 323→325、『3 跨注』→『5 跨注』、
   『2 规则』→『3 规则』、版本行 1.13→1.14、r05 行补策略落地状态。
3. 重渲染 VERSION_INDEX.md。
"""
import io, sys, os, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:\PNOS\smartpickcore"
TODAY = "2026-10-11"

# ---- 1. versions.json
vp = os.path.join(ROOT, "versions.json")
v = json.load(open(vp, encoding="utf-8"))

def bump(path, **kw):
    for e in v["entries"]:
        if e["path"] == path:
            e.update({k: val for k, val in kw.items() if val is not None})
            return True
    return False

bump("games/dlt/strategy/STRATEGY_GUIDE.md",
     content_version="1.3", iteration="r06", updated_at=TODAY,
     note="r06：R-002 语义重构（禁止完全相同号码，F-0027/F-0028）、新增 R-003（生日号区，F-0029）")
bump("games/dlt/strategy/strategy.json",
     content_version="1.3", iteration="r06", updated_at=TODAY,
     note="r06（用户批准）：R-002 → exclude + 禁止完全相同号码；新增 R-003（F-0029）；provenance round06")
bump("games/dlt/game.yaml",
     content_version=None, iteration="r06", updated_at=TODAY,
     note="跨注特征 3→5（新增 identical_ticket_count / has_identical_tickets）；has_duplicated_structure 改为无规则引用（R-002 已重构）")
bump("framework/core/features.py",
     content_version=None, iteration="r06", updated_at=TODAY,
     note="新增跨注原语 duplicate_ticket_count / duplicate_ticket_count_ge（F-0027 判定量）")

new_entries = [
    {"path": "games/dlt/iterations/round05/scripts/bet_structure.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r05", "note": "投注方式 + R-002 量化 + R-003 候选模拟", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round05/scripts/bet_structure.json", "level": "A", "kind": "report",
     "content_version": "1.0", "iteration": "r05", "note": "", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round05/scripts/timing_weekday.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r05", "note": "星期/奖池时序/节假日窗口", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round05/scripts/timing_weekday.json", "level": "A", "kind": "report",
     "content_version": "1.0", "iteration": "r05", "note": "", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round05/scripts/apply_r05_facts.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r05", "note": "F-0026~F-0032 落地", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round05/scripts/fix_r05_housekeeping.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r05", "note": "收轮维护（tags/versions/计数）", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round05/scripts/sync_r05_versions.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r05", "note": "", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/apply_r06_strategy.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r06", "note": "用户批准三项策略变更落地", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/smoke_r06.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r06", "note": "新原语 + R-002/R-003 可执行性冒烟", "updated_at": TODAY, "status": "active"},
    {"path": "games/dlt/iterations/round06/scripts/probe_r06.py", "level": "A", "kind": "script",
     "content_version": "1.0", "iteration": "r06", "note": "探查原语与结论原文", "updated_at": TODAY, "status": "active"},
]
existing = {e["path"] for e in v["entries"]}
for ne in new_entries:
    if ne["path"] not in existing:
        v["entries"].append(ne)
        print("[versions +]", ne["path"])
json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"[versions] entries = {len(v['entries'])}")

# ---- 2. README.md
rp = os.path.join(ROOT, "README.md")
s = open(rp, encoding="utf-8").read()
subs = [
    ("> **版本**：`1.13` ｜ 轮次 `r05`", "> **版本**：`1.14` ｜ 轮次 `r06`"),
    ("`test_cross_scope.py` **62**", "`test_cross_scope.py` **64**"),
    ("共 **323** 项", "共 **325** 项"),
    ("11 单注 + **3 跨注**特征全原语化", "11 单注 + **5 跨注**特征全原语化"),
    ("`strategy.json`（schema **1.1**，2 规则 + 9 条 avoid_list）",
     "`strategy.json`（schema **1.1**，**3 规则** + 9 条 avoid_list）"),
    ("+ **round05 完成**（投注方式等价 / R-002 量化不成立 / 时间因素证伪）+ round06 任务书",
     "+ **round05 完成**（投注方式等价 / R-002 量化不成立 / 时间因素证伪）+ **r06 策略落地**（R-002 重构 / R-003 新增，用户批准）+ round06 任务书"),
]
for old, new in subs:
    if old not in s:
        print("  [WARN] README 未找到:", old[:50])
        continue
    s = s.replace(old, new, 1)
open(rp, "w", encoding="utf-8").write(s)
print("[README] 同步完成")

# ---- 3. 重渲染 VERSION_INDEX
os.system(f'"{sys.executable}" tools/render_version_index.py --write')
print("[VERSION_INDEX] 已重渲染")
