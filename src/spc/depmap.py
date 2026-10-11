# -*- coding: utf-8 -*-
"""spc.depmap — 跨文件依赖图（DEPENDENCY_MAP.md 生成源，C 升级）。

仓库级 AI 理解的关键缺口是「跨文件/多跳依赖」（SWE-QA 的瓶颈）：
改动 A 会影响谁？结论靠什么文件立住？本模块把**显式声明的引用关系**
汇总成一张可读的依赖图（派生物）。

覆盖的关系：
  1. 策略 → 结论：strategy.json rules[].evidence_refs / avoid_list[].refuted_by → FACTS
  2. 彩种特征 → 原语：game.yaml features[].primitive → framework/core/features.py
  3. 数据 → 契约：game.yaml / FACTS / strategy 声明的 schema → spec/*.schema.json
  4. 结论 → 证据：FACTS evidence.source / script → 文件（锚定链）

学术依据：REPOGRAPH（ICLR 2025：仓库级代码图提升 AI SWE 性能）；
SWE-QA（arXiv 2509.14635：跨文件推理是仓库理解主要瓶颈）。
"""
from __future__ import annotations

import json
import os

_ROOT_HINT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_json(root: str, rel: str) -> dict | list | None:
    p = os.path.join(root, rel)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _first_game(root: str) -> str | None:
    """发现第一个含 game.yaml 的彩种目录（库代码不硬编码彩种名）。"""
    gd = os.path.join(root, "games")
    if not os.path.isdir(gd):
        return None
    for name in sorted(os.listdir(gd)):
        if os.path.isfile(os.path.join(gd, name, "game.yaml")):
            return name
    return None


def build_dependencies(root: str | None = None,
                       game: str | None = None) -> list[tuple[str, str, str]]:
    """返回 (subject, relation, object) 三元组列表。"""
    root = root or _ROOT_HINT
    game = game or _first_game(root)
    deps: list[tuple[str, str, str]] = []
    gprefix = f"games/{game}/" if game else ""

    # 1. 策略 → 结论
    st = _load_json(root, f"{gprefix}strategy/strategy.json")
    if isinstance(st, dict):
        for r in st.get("rules", []):
            rid = r.get("id", "?")
            for ref in r.get("evidence_refs") or []:
                deps.append((f"strategy.json:{rid}", "evidence_refs→", f"FACTS:{ref}"))
        for a in st.get("avoid_list", []):
            aid = a.get("id", "?")
            for ref in a.get("refuted_by") or []:
                deps.append((f"strategy.json:{aid}", "refuted_by→", f"FACTS:{ref}"))
        prov = st.get("provenance") or {}
        if prov.get("evidence_hash"):
            deps.append(("strategy.json:provenance", "evidence_hash→",
                         "FACTS.jsonl（规范视图摘要）"))

    # 2. 结论 → 证据文件（source / script 锚定链）
    fp = os.path.join(root, "memory", "facts", "FACTS.jsonl")
    if os.path.exists(fp):
        with open(fp, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ft = json.loads(line)
                except json.JSONDecodeError:
                    continue
                fid = ft.get("id", "?")
                src = ft.get("source")
                if src:
                    deps.append((f"FACTS:{fid}", "source→", src))
                ev = ft.get("evidence") or {}
                scr = ev.get("script")
                if scr:
                    deps.append((f"FACTS:{fid}", "script→", scr))
                if ev.get("source_sha256"):
                    deps.append((f"FACTS:{fid}", "sha256锚→", src or "?"))

    # 3. 彩种特征 → 原语（game.yaml features → framework/core/features.py）
    gy = os.path.join(root, gprefix, "game.yaml")
    if os.path.exists(gy):
        try:
            import yaml  # type: ignore
            with open(gy, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            for feat in cfg.get("features") or []:
                name = feat.get("name") or "?"
                prim = feat.get("primitive")
                if prim:
                    deps.append((f"game.yaml:{name}", "primitive→",
                                 f"features.py:{prim}"))
            for epoch in (cfg.get("prize_model") or {}).get("epochs", []):
                eid = epoch.get("id")
                if eid:
                    deps.append(("game.yaml:prize_model", "epoch→", f"epochs:{eid}"))
        except Exception:  # noqa: BLE001
            pass

    # 4. 数据 → 契约（schema 归属）
    for rel, schema_field in (
        (f"{gprefix}game.yaml", "schema"),
        (f"{gprefix}strategy/strategy.json", "schema"),
    ):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        try:
            import yaml  # type: ignore
            with open(p, encoding="utf-8") as f:
                obj = yaml.safe_load(f) if rel.endswith(".yaml") else json.load(f)
            s = (obj or {}).get("schema") if isinstance(obj, dict) else None
        except Exception:  # noqa: BLE001
            s = None
        if isinstance(s, str) and s.startswith("spec/"):
            deps.append((rel, "schema→", s))

    # 去重保序
    seen: set[tuple[str, str, str]] = set()
    out: list[tuple[str, str, str]] = []
    for t in deps:
        if t not in seen:
            seen.add(t)
            out.append(t)
    out.sort(key=lambda t: (t[0], t[1]))
    return out


def render_dependency_map(root: str | None = None) -> str:
    """渲染 DEPENDENCY_MAP.md（派生物）。"""
    root = root or _ROOT_HINT
    deps = build_dependencies(root)

    by_subject: dict[str, list[tuple[str, str]]] = {}
    for sub, rel, obj in deps:
        by_subject.setdefault(sub, []).append((rel, obj))

    lines = [
        "# DEPENDENCY_MAP —— 跨文件依赖图",
        "",
        "> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`",
        "",
        "> **本文件是派生物**：由 `tools/render_dependency_map.py` 从 strategy.json /",
        "> FACTS.jsonl / game.yaml / versions.json 显式引用关系生成；改动后运行",
        "> `--write` 同步，勿手改。",
        "",
        "> 改动任何文件前，先看它被谁依赖（反向引用）；跨文件/多跳依赖是",
        "> AI 理解仓库的主要瓶颈（SWE-QA / REPOGRAPH）。",
        "",
    ]
    for sub in sorted(by_subject):
        lines.append(f"## {sub}")
        for rel, obj in by_subject[sub]:
            lines.append(f"- {rel} `{obj}`")
        lines.append("")
    if not deps:
        lines.append("（当前无显式依赖关系）\n")
    return "\n".join(lines).rstrip() + "\n"
