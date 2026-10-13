# -*- coding: utf-8 -*-
"""spc.flywheel — 迭代飞轮健康度统计（K）与置信度校准（D1）。

把「飞轮是否在正向升级」从定性论证变成可量化的机械指标：
  · 结论演化：总数 / active / superseded+refuted（推翻率）/ tentative
  · 每轮新增结论分布（飞轮是否持续产出）
  · claim_type 分布（证据结构是否多元）
  · 置信度分层存活率（D1 校准：5★ 的推翻率应 < 3★，否则置信度系统性虚高）

产物：
  · render_health()    → FLYWHEEL_HEALTH.md（派生物，含生成注记）
  · calibration_text() → 控制台校准报告（tools/report_calibration.py 用）

学术依据：
  · AIDE²（arXiv 2609.26457）：AI 研究 agent 连续改进可测量（8 天 7 项），
    且 reward hacking 55%→32% —— 自我改进循环必须带可量化健康指标。
  · IterResearch：记忆与结论的「存活/被推翻」是迭代质量的核心观测。
"""
from __future__ import annotations

import json
import os
import sys

_ROOT_HINT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SRC = os.path.join(_ROOT_HINT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from spc import paths  # noqa: E402 路径单一权威（飞轮不得自己拼记忆路径）


def load_facts(root: str | None = None, study: str | None = None) -> list[dict]:
    """读 FACTS.jsonl（权威源）。

    study 省略时自动发现第一个研究组 —— 飞轮不硬编码彩种名。
    路径一律经 spc.paths，避免架构迁移后仪表盘空转（2026-10-12 事故）。
    """
    root = root or _ROOT_HINT
    study = study or paths.first_study(root=root)
    if not study:
        return []
    p = paths.facts_path(study, root=root)
    facts: list[dict] = []
    if not os.path.exists(p):
        return facts
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                facts.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return facts


def collect_metrics(root: str | None = None) -> dict:
    """统计飞轮健康指标，返回结构化 dict。"""
    root = root or _ROOT_HINT
    facts = load_facts(root)

    total = len(facts)
    by_status: dict[str, int] = {}
    by_round: dict[int, int] = {}
    by_type: dict[str, int] = {}
    by_confidence: dict[int, dict[str, int]] = {}

    import re
    for ft in facts:
        st = ft.get("status") or "unknown"
        by_status[st] = by_status.get(st, 0) + 1

        est = ft.get("established_in") or ""
        m = re.match(r"^round(\d{2})$", est)
        if m:
            r = int(m.group(1))
            by_round[r] = by_round.get(r, 0) + 1

        ct = ft.get("claim_type") or "<缺失>"
        by_type[ct] = by_type.get(ct, 0) + 1

        conf = ft.get("confidence")
        if isinstance(conf, int):
            cell = by_confidence.setdefault(conf, {"total": 0, "dead": 0, "active": 0})
            cell["total"] += 1
            if st in ("superseded", "refuted"):
                cell["dead"] += 1
            else:
                cell["active"] += 1

    dead = by_status.get("superseded", 0) + by_status.get("refuted", 0)
    return {
        "total": total,
        "active": by_status.get("established", 0) + by_status.get("tentative", 0),
        "superseded": by_status.get("superseded", 0),
        "refuted": by_status.get("refuted", 0),
        "dead": dead,
        "by_status": by_status,
        "by_round": dict(sorted(by_round.items())),
        "by_type": dict(sorted(by_type.items())),
        "by_confidence": dict(sorted(by_confidence.items())),
        "survival": (1 - dead / total) if total else 1.0,
    }


def render_health(metrics: dict, round_label: str = "r06",
                  root: str | None = None) -> str:
    """渲染 FLYWHEEL_HEALTH.md（派生物）。"""
    m = metrics
    rows = []
    by_round = m["by_round"]
    round_rows = "\n".join(
        f"| round{r:02d} | {n} |" for r, n in by_round.items()
    ) or "| — | 0 |"
    rows.append(f"| 总结论数 | **{m['total']}** |")
    rows.append(f"| 有效结论（established+tentative） | **{m['active']}** |")
    rows.append(f"| 被推翻（superseded+refuted） | **{m['dead']}** |")
    rows.append(f"| 结论存活率 | **{m['survival']:.1%}** |")
    conf_rows = []
    for c, cell in m["by_confidence"].items():
        rate = cell["dead"] / cell["total"] if cell["total"] else 0
        conf_rows.append(f"| {c}★ | {cell['total']} | {cell['dead']} | {rate:.0%} |")
    conf_txt = "\n".join(conf_rows) or "| — | 0 | 0 | — |"
    type_rows = "\n".join(f"| {k} | {v} |" for k, v in m["by_type"].items())
    # 头部版本行：单一来源 = versions.json 登记（勿手写/硬编码）
    vl = ""
    if root:
        from .versions import registered_version, version_line
        cv, it, upd = registered_version(root, "FLYWHEEL_HEALTH.md")
        if cv:
            vl = "\n\n" + version_line(cv, it, upd) + "\n"
    return f"""# FLYWHEEL_HEALTH —— 迭代飞轮健康度
{vl}
> **本文件是派生物**：由 `tools/render_flywheel_health.py` 从 FACTS.jsonl 统计生成；
> 结论变更后运行 `--write` 同步，勿手改。｜ 统计轮 {round_label}

> 飞轮是否正向升级的可量化观测（AIDE² 式：连续改进 + 自评信号）。
> 连续 3 轮指标不退化（存活率、产出、通过率）视为飞轮正常。

## 结论演化

| 指标 | 值 |
|---|---|
{"\n".join(rows)}

## 每轮新增结论（产出是否持续）

| 轮 | 新增 |
|---|---|
{round_rows}

## 置信度分层存活率（D1 校准信号）

| 置信度 | 总数 | 已推翻 | 推翻率 |
|---|---|---|---|
{conf_txt}

## 证据类型分布

| claim_type | 条数 |
|---|---|
{type_rows}
"""


def calibration_text(metrics: dict) -> str:
    """D1 置信度校准：按置信度分层对比存活率，输出可读报告。"""
    m = metrics
    out = [f"置信度校准报告（{m['total']} 条结论，存活率 {m['survival']:.1%}）"]
    out.append(f"{'置信度':<6}{'总数':<6}{'已推翻':<8}{'推翻率':<8}")
    for c, cell in m["by_confidence"].items():
        rate = cell["dead"] / cell["total"] if cell["total"] else 0
        out.append(f"{c}★    {cell['total']:<6}{cell['dead']:<8}{rate:.0%}")
    # 系统性失配判定：高置信度（4-5★）推翻率不应高于低置信度（1-2★）
    hi = sum(cell["dead"] for c, cell in m["by_confidence"].items() if c >= 4)
    hi_t = sum(cell["total"] for c, cell in m["by_confidence"].items() if c >= 4)
    lo = sum(cell["dead"] for c, cell in m["by_confidence"].items() if c <= 2)
    lo_t = sum(cell["total"] for c, cell in m["by_confidence"].items() if c <= 2)
    if hi_t >= 3 and lo_t >= 3:
        hi_r, lo_r = hi / hi_t, lo / lo_t
        verdict = ("⚠ 失配：高置信度推翻率高于低置信度 —— 置信度可能系统性虚高"
                   if hi_r > lo_r else
                   "✓ 匹配：高置信度推翻率不高于低置信度")
        out.append(f"高置信度（4-5★）推翻率 {hi_r:.0%} vs 低置信度（1-2★）{lo_r:.0%}：{verdict}")
    else:
        out.append("样本不足（高/低置信度任一侧 <3 条），不做失配判定")
    return "\n".join(out)
