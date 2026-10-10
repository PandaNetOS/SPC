# -*- coding: utf-8 -*-
"""build_versions.py — 穷举全仓库文件，生成 versions.json

用法：
    python tools/build_versions.py            # 只统计
    python tools/build_versions.py --write    # 写 versions.json

分级（四级）：
    A  结论性内容 —— 文件内版本行 + 索引登记
    B  结构性文档 / 框架代码 / 库代码 —— .md 加版本行；.py 只登记索引
    C  机器契约 —— 用自身既有版本字段（schema_version / config_version /
       data_version），索引**镜像**其值，不重复加版本
    D  纯数据 / 分析脚本 —— 不版本化；raw 数据用 SHA256（比版本号更强的保证）
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

TODAY = "2026-10-11"
FRAMEWORK_VERSION = "1.0"

# ---------------------------------------------------------------- 分级规则
RULES: list[tuple[str, str, str]] = [
    (r"^\.gitignore$",                                "D", "meta"),
    (r"^pyproject\.toml$",                            "C", "package_manifest"),

    (r"^AI_CONTEXT\.md$",                             "B", "entry_point"),
    (r"^README\.md$",                                 "B", "doc"),
    (r"^VERSION_INDEX\.md$",                          "B", "version_index_doc"),
    (r"^versions\.json$",                             "B", "version_index"),

    (r"^spec/.*\.schema\.json$",                      "C", "schema"),
    (r"^spec/VERSIONING\.md$",                        "B", "doc"),
    (r"^spec/README\.md$",                            "B", "doc"),

    (r"^framework/protocol/templates/.*\.md$",        "B", "template"),
    (r"^framework/protocol/.*\.md$",                  "B", "protocol"),
    (r"^framework/methodology/.*\.md$",               "B", "methodology"),
    (r"^framework/core/.*\.py$",                      "B", "framework_core"),
    (r"^framework/core/README\.md$",                  "B", "doc"),
    (r"^framework/tools/.*\.py$",                     "B", "framework_tool"),
    (r"^framework/README\.md$",                       "B", "doc"),
    (r"^framework/INDEX\.md$",                        "B", "index"),

    (r"^memory/facts/FACTS\.jsonl$",                  "A", "fact_ledger"),
    (r"^memory/facts/INDEX\.md$",                     "A", "fact_index"),
    (r"^memory/lessons/LESSONS\.md$",                 "A", "lesson_library"),
    (r"^memory/workbench/.*\.md$",                    "A", "workbench"),
    (r"^memory/journal/.*\.md$",                      "A", "journal"),
    (r"^memory/INDEX\.md$",                           "A", "index"),

    (r"^games/_template/game\.yaml$",                 "C", "game_config"),
    (r"^games/_template/strategy/strategy\.json$",    "C", "strategy"),
    (r"^games/_template/.*",                          "B", "template_game"),
    (r"^games/INDEX\.md$",                            "B", "index"),

    (r"^games/.*/game\.yaml$",                        "C", "game_config"),
    (r"^games/.*/strategy/strategy\.json$",           "C", "strategy"),
    (r"^games/.*/strategy/STRATEGY_GUIDE\.md$",       "A", "strategy_guide"),
    (r"^games/.*/strategy/simulation_results\.json$", "D", "analysis_output"),
    (r"^games/.*/strategy/.*\.py$",                   "D", "analysis_script"),
    (r"^games/.*/iterations/.*/manifest\.json$",      "C", "iteration_manifest"),
    (r"^games/.*/iterations/.*",                      "A", "iteration_artifact"),
    (r"^games/.*/rules_history\.md$",                 "A", "rules_history"),
    (r"^games/.*/manifest_v4_source\.json$",          "D", "source_manifest"),
    (r"^games/.*/data/raw/.*",                        "D", "raw_data"),
    (r"^games/.*/data/derived/.*",                    "D", "derived_data"),
    (r"^games/.*/data/tools/.*\.py$",                 "D", "analysis_script"),
    (r"^games/.*/data/build_scripts/.*\.py$",         "D", "build_script"),
    (r"^games/.*/data/.*\.md$",                       "D", "data_readme"),

    (r"^src/.*\.py$",                                 "B", "library"),
    (r"^cli/.*\.py$",                                 "B", "cli"),
    (r"^tests/.*\.py$",                               "B", "test"),
    (r"^tests/.*\.md$",                               "B", "doc"),
    (r"^tools/.*\.py$",                               "B", "repo_tool"),
    (r"^docs/.*\.md$",                                "B", "doc"),
]

# 内容版本（人工维护）。键 = 仓库相对路径。
CONTENT_VERSIONS: dict[str, tuple[str, str, str | None]] = {
    # path: (content_version, iteration, note)
    "memory/facts/FACTS.jsonl":            ("1.0", "r02", "15 条结论（F-0001~F-0015）"),
    "memory/facts/INDEX.md":               ("1.0", "r02", "派生物，由 cli index 生成"),
    "memory/lessons/LESSONS.md":           ("1.0", "r02", "L1–L9，只增不删"),
    "memory/workbench/OPEN_QUESTIONS.md":  ("1.0", "r02", "Q-001~Q-008；Q-009 待补"),
    "memory/workbench/HYPOTHESES.md":      ("1.0", "r02", "H-001~H-005"),
    "memory/workbench/TODO.md":            ("1.0", "r02", "16 项未完成"),
    "memory/journal/round02.md":           ("1.0", "r02", "整理入库轮"),
    "memory/INDEX.md":                     ("1.0", "r02", "记忆层说明"),
    "games/dlt/rules_history.md":          ("1.0", "r02", "E0~E6 共 7 段"),
    "games/dlt/strategy/STRATEGY_GUIDE.md": ("1.0", "r03", "面向普通读者的策略说明书（人话版）"),
    "games/dlt/iterations/round02/FINDINGS.md":     ("1.0", "r02", "整理入库轮发现"),
    "games/dlt/iterations/round02/HANDOFF.md":      ("1.0", "r02", "r02→r03 交接"),
    "games/dlt/iterations/round02/TASK_BRIEF.md":   ("1.0", "r02", "已交付"),
    "games/dlt/iterations/round02/PRIORITY_TASKS.md": ("1.0", "r02", None),
    "games/dlt/iterations/round02/known_errors.md": ("1.0", "r02", "E1~E9 避坑手册"),
    "games/dlt/iterations/round02/legacy_findings/README.md": ("1.0", "r02", "归档，设使用门槛"),
    "games/dlt/iterations/round03/TASK_BRIEF.md":   ("1.0", "r03", "planned"),
}

# 归档条目（A 级，但状态标 archived）
ARCHIVED = {
    "games/dlt/iterations/round02/legacy_findings/_round3_reference/round3_independent_review.html",
    "games/dlt/iterations/round02/legacy_findings/round2_deep_analysis.txt",
    "games/dlt/iterations/round02/legacy_findings/round2_glm_analysis.txt",
    "games/dlt/iterations/round02/legacy_findings/round2_main_report.md",
    "games/dlt/iterations/round02/legacy_findings/round2_verify_analysis.txt",
}

# B 级文档的版本（含框架文档）
DOC_VERSIONS: dict[str, tuple[str, str]] = {
    "AI_CONTEXT.md":                              ("1.0", "r02"),
    "README.md":                                  ("1.0", "r02"),
    "VERSION_INDEX.md":                           ("1.0", "r02"),
    "versions.json":                              ("1.0", "r02"),
    "spec/README.md":                             ("1.0", "r02"),
    "spec/VERSIONING.md":                         ("1.0", "r02"),
    "framework/README.md":                        ("1.0", "r02"),
    "framework/INDEX.md":                         ("1.0", "r02"),
    "framework/core/README.md":                   ("1.0", "r02"),
    "framework/protocol/README.md":               ("1.0", "r02"),
    "framework/protocol/ITERATION_PROTOCOL.md":   ("1.0", "r02"),
    "framework/protocol/MEMORY_PROTOCOL.md":      ("1.0", "r02"),
    "framework/protocol/templates/TASK_BRIEF.template.md": ("1.0", "r02"),
    "framework/protocol/templates/FINDINGS.template.md":   ("1.0", "r02"),
    "framework/protocol/templates/HANDOFF.template.md":    ("1.0", "r02"),
    "framework/methodology/MATH_BOUNDARY.md":              ("1.0", "r02"),
    "framework/methodology/STATISTICAL_DISCIPLINE.md":     ("1.0", "r02"),
    "docs/ARCHITECTURE.md":                       ("1.0", "r02"),
    "docs/CONSUMING.md":                          ("1.1", "r02"),
    "docs/ITERATION_GUIDE.md":                    ("1.0", "r02"),
    "docs/METHODOLOGY.md":                        ("1.0", "r02"),
    "docs/PROPOSAL_SINGLE_TICKET_CORE.md":        ("1.0", "r02"),
    "docs/VERSIONING_DOCS.md":                    ("1.0", "r02"),
    "games/INDEX.md":                             ("1.0", "r02"),
    "tests/README.md":                            ("1.0", "r02"),
}

# C 级：镜像既有版本字段
# ref 支持点号路径（如 inputs.data_version）
C_LEVELS: dict[str, tuple[str, str, str | None]] = {
    # path: (ref_field, ref_value, note)
    "games/dlt/game.yaml":                          ("config_version", "2.0", "★ 2026-10-11 由 1.0 升 2.0（features 原语化）"),
    "games/_template/game.yaml":                    ("config_version", "2.0", "2026-10-11 与 dlt 同步升至 2.0（features 原语化）"),
    "games/_template/strategy/strategy.json":       ("config_version", "2.0", "模板策略，2026-10-11 随 game.yaml 同步至 2.0"),
    "games/dlt/strategy/strategy.json":             ("schema_version", "1.0", "契约版本；内容版本见 content_version"),
    "games/dlt/iterations/round02/manifest.json":   ("inputs.data_version", "dlt_full_2933", None),
    "games/dlt/iterations/round03/manifest.json":   ("inputs.data_version", "dlt_full_2933", None),
    "pyproject.toml":                               ("project.version", "0.1.0", "包版本"),
    # spec schema 自身无版本字段（它『约束』别人的 schema_version，自己不声明）
    # → 只登记，不比对（version_ref 留空）
    "spec/fact.schema.json":                        (None, None, "schema 自身无版本；约束 fact.schema_version"),
    "spec/game_config.schema.json":                 (None, None, "schema 自身无版本；约束 game_config.config_version"),
    "spec/iteration.schema.json":                   (None, None, "schema 自身无版本；约束 iteration 结构"),
    "spec/strategy.schema.json":                    (None, None, "schema 自身无版本；约束 strategy.schema_version"),
    "spec/version_index.schema.json":               (None, None, "schema 自身无版本；约束 versions.index_version"),
}


def _git_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=_ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    if out.returncode != 0:
        raise SystemExit(f"✗ git ls-files 失败: {out.stderr}")
    return [l for l in out.stdout.splitlines() if l.strip()]


def classify(path: str) -> tuple[str, str] | None:
    for pat, lvl, kind in RULES:
        if re.search(pat, path):
            return lvl, kind
    return None


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(os.path.join(_ROOT, path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    files = _git_files()
    # 排除本工具自身与骨架产物
    files = [f for f in files if not f.startswith("tools/_")]

    entries: list[dict] = []
    unclassified: list[str] = []

    for p in files:
        c = classify(p)
        if c is None:
            unclassified.append(p)
            continue
        lvl, kind = c
        e: dict = {"path": p, "level": lvl, "kind": kind}

        if lvl == "A":
            cv = CONTENT_VERSIONS.get(p)
            if cv:
                e["content_version"] = cv[0]
                e["iteration"] = cv[1]
                if cv[2]:
                    e["note"] = cv[2]
            else:
                e["content_version"] = "1.0"
                e["iteration"] = "r02"
            e["updated_at"] = TODAY
            e["status"] = "archived" if p in ARCHIVED else "active"
            if p in ARCHIVED:
                e["note"] = "历史归档，设使用门槛（防锚定）"

        elif lvl == "B":
            dv = DOC_VERSIONS.get(p)
            if dv:
                e["content_version"] = dv[0]
                e["iteration"] = dv[1]
                e["updated_at"] = TODAY
            if p.endswith(".py"):
                # 代码文件：只登记，不加文件内版本行
                e["content_version"] = None
                e["note"] = "代码文件：不写文件内版本行（用 git blame）"
                e["iteration"] = "r02"
            e["status"] = "generated" if p in ("versions.json",) else "active"
            if p in ("VERSION_INDEX.md",):
                e["note"] = "版本索引（人读），权威源是 versions.json"

        elif lvl == "C":
            cl = C_LEVELS.get(p)
            if cl:
                if cl[0]:
                    e["version_ref"] = cl[0]
                    e["ref_version"] = cl[1]
                if cl[2]:
                    e["note"] = cl[2]
            e["status"] = "active"

        else:  # D
            if kind == "raw_data":
                e["sha256"] = sha256_of(p)
                e["note"] = "SHA256 为准，不做内容版本"
            e["status"] = "active"

        entries.append(e)

    entries.sort(key=lambda x: (x["level"], x["path"]))

    out = {
        "index_version": "1.0",
        "repo": "PandaNetOS/smartpickcore",
        "generated_at": TODAY,
        "current_iteration": "r03",
        "framework_version": FRAMEWORK_VERSION,
        "levels": {
            "A": {
                "name": "结论性内容",
                "versioned": True,
                "field": "content_version",
                "reason": "随轮次演化、重复写错代价最高。文件内版本行 + 索引登记。",
            },
            "B": {
                "name": "结构性文档 / 框架与库代码",
                "versioned": True,
                "field": "content_version",
                "reason": "随框架演进但无『结论』性质。.md 加版本行；.py 只登记索引。",
            },
            "C": {
                "name": "机器契约",
                "versioned": False,
                "field": None,
                "reason": "已有 schema_version / config_version / data_version / version 字段，各答不同问题。索引镜像其值，不重复加版本。",
            },
            "D": {
                "name": "纯数据 / 分析脚本",
                "versioned": False,
                "field": None,
                "reason": "raw 数据用 SHA256（比版本号更强的保证）；分析脚本随结论归档，不单独版本化。",
            },
        },
        "entries": entries,
        "history": [
            {
                "version": "1.0",
                "date": TODAY,
                "scope": "全仓库",
                "change": "建立版本体系：引入 content_version（内容版本）与 framework_version（框架版本），与既有 schema_version / config_version / data_version 并存分区；登记 A/B/C/D 四级共 %d 个文件。" % len(entries),
            },
            {
                "version": "1.0",
                "date": "2026-10-10",
                "scope": "framework/",
                "change": "单注层通用架构落地（framework/core/ 6 模块 / 21 原语），记为 framework_version 1.0。",
            },
        ],
    }

    if unclassified:
        print("⚠️ 未分类：")
        for p in unclassified:
            print("   ", p)

    by_lvl: dict[str, int] = {}
    for e in entries:
        by_lvl[e["level"]] = by_lvl.get(e["level"], 0) + 1
    print(f"登记条目: {len(entries)}")
    for k in "ABCD":
        print(f"  {k}: {by_lvl.get(k, 0)}")

    n_cv = sum(1 for e in entries if e.get("content_version"))
    n_verline = sum(
        1 for e in entries
        if e.get("content_version") and (e["path"].endswith(".md") and e["level"] in "AB")
    )
    print(f"  含 content_version: {n_cv}")
    print(f"  需写文件内版本行: {n_verline}")

    if args.write:
        p = os.path.join(_ROOT, "versions.json")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"\n✓ 已写 versions.json（{len(entries)} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
