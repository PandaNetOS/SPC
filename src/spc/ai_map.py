# -*- coding: utf-8 -*-
"""spc.ai_map — AI_MAP.md 生成源（AI 可读性升级 P1，llms.txt 式机器地图）。

README 目录树（spc.tree）解决的是「文件在哪」；AI_MAP 解决的是
「按职责分区 + 每区一句话说明 + 引用顺序」—— 给 AI 的快速地图：
    1. 入口先读哪些
    2. 每区有哪些文件、各自干什么（note 直接来自 versions.json）
    3. 有深度的入口（AI_CONTEXT / AGENTS.md / VERSION_INDEX）显式排序

学术依据：
  · llms.txt（Answer.AI 2024-09，v2 2026-08）：根目录 Markdown 机器地图，
    H1 + blockquote 摘要 + H2 分区链接 —— 消费者是 LLM，用 Markdown 而非 JSON。
  · Spatial Context Theory：文档应是 generated output 而非 maintained input
    —— 本模块与 render_ai_map.py 一起把 AI_MAP 做成派生物，登记即同步。
"""
from __future__ import annotations

import json
import os

_EXCLUDE_DIR_PREFIXES = (
    "tests/fixtures/",
    "framework/protocol/templates/",
)
_EXCLUDE_FILES = {".gitignore"}

# 分区顺序与路径前缀（条目只归属第一个命中分区；game 前缀动态发现）
_BASE_SECTIONS: list[tuple[str, str]] = [
    ("入口（先读）", ""),          # 根层文件
    ("契约", "spec/"),
    ("框架", "framework/"),
    ("记忆", "memory/"),
    ("策略输出", "strategy/"),
    ("彩种", ""),
    ("迭代史", "iterations/"),
    ("工具与 CLI", "tools/"),
    ("工具与 CLI", "cli/"),
    ("测试", "tests/"),
    ("库代码", "src/"),
    ("文档", "docs/"),
]
_ENTRY_ORDER = [  # 根层入口的展示顺序
    "AI_CONTEXT.md", "AGENTS.md", "README.md",
    "VERSION_INDEX.md", "versions.json", "pyproject.toml",
]

_NOTE_MAX = 60


def load_versions(root: str) -> dict:
    with open(os.path.join(root, "versions.json"), encoding="utf-8") as f:
        return json.load(f)


def _excluded(path: str) -> bool:
    if path in _EXCLUDE_FILES:
        return True
    if "/data/" in path:
        return True
    for pfx in _EXCLUDE_DIR_PREFIXES:
        if path.startswith(pfx):
            return True
    return False


def _note(entry: dict) -> str:
    n = (entry.get("note") or "").strip()
    if not n:
        return ""
    if len(n) > _NOTE_MAX:
        n = n[:_NOTE_MAX - 1] + "…"
    return n


def _first_game(root: str) -> str | None:
    gd = os.path.join(root, "games")
    if not os.path.isdir(gd):
        return None
    for name in sorted(os.listdir(gd)):
        if os.path.isfile(os.path.join(gd, name, "game.yaml")):
            return name
    return None


def _sections_for(game: str) -> list[tuple[str, str]]:
    """按彩种目录名生成分区前缀（库代码不硬编码彩种名）。"""
    return [
        ("入口（先读）", ""),
        ("契约", "spec/"),
        ("框架", "framework/"),
        ("记忆", "memory/"),
        ("策略输出", f"games/{game}/strategy/"),
        ("彩种", f"games/{game}/"),
        ("迭代史", f"games/{game}/iterations/"),
        ("工具与 CLI", "tools/"),
        ("工具与 CLI", "cli/"),
        ("测试", "tests/"),
        ("库代码", "src/"),
        ("文档", "docs/"),
    ]


def _section_of(path: str, sections: list[tuple[str, str]]) -> str | None:
    if "/" not in path:
        return "入口（先读）"
    for title, pfx in sections:
        if pfx and path.startswith(pfx):
            return title
    return None


def _render_section(title: str, entries: list[dict]) -> str:
    lines = [f"## {title}"]
    if title == "入口（先读）":
        entries.sort(key=lambda e: (
            _ENTRY_ORDER.index(e["path"]) if e["path"] in _ENTRY_ORDER else 99,
            e["path"],
        ))
    else:
        entries.sort(key=lambda e: e["path"])
    for e in entries:
        path = e["path"]
        note = _note(e)
        tail = f" — {note}" if note else ""
        lines.append(f"- `{path}`{tail}")
    return "\n".join(lines)


def render_ai_map(entries: list[dict], root: str | None = None) -> str:
    """生成 AI_MAP.md 正文（不含 ``` 包裹；含派生物注记与摘要）。"""
    game = _first_game(root) if root else None
    sections = _sections_for(game or "g") if game else _BASE_SECTIONS
    by_section: dict[str, list[dict]] = {}
    for e in entries:
        p = e.get("path") or ""
        if not p or _excluded(p):
            continue
        sec = _section_of(p, sections)
        if sec:
            by_section.setdefault(sec, []).append(e)

    out = [
        "# AI_MAP —— SPC 机器可读地图",
        "",
        "> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`",
        "",
        "> **本文件是派生物**：由 `tools/render_ai_map.py` 从 versions.json 生成；",
        "> 新增文件登记 versions.json 后运行 `--write` 同步，勿手改。",
        "",
        "> SPC：彩票投注策略研究框架（自我迭代）—— 研究结论输出为机器可读",
        "> 策略规则。AI 快速了解本项目：先读本地图定分区，再读 AI_CONTEXT.md",
        "> （深度入口）与 AGENTS.md（操作规则）。",
        "",
    ]
    for title, _pfx in sections:
        if title not in by_section:
            continue
        out.append(_render_section(title, by_section[title]))
        out.append("")
    return "\n".join(out).rstrip() + "\n"
