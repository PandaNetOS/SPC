# -*- coding: utf-8 -*-
"""versions.py — 版本索引的读取与一致性校验

核心职责：
  1. 读 versions.json（权威源，受 spec/version_index.schema.json 约束）
  2. 校验每个条目对应的文件**真实存在**
  3. 校验 A/B 级 .md 的**文件内版本行**与索引一致
  4. 校验 VERSION_INDEX.md 是 versions.json 的**最新派生物**（无漂移）
  5. 校验 C 级条目的 ref_version 与文件**实际值**一致

设计原则：**任何不一致都报出来，不静默容忍。**
"""
from __future__ import annotations

import json
import os
import re

__all__ = [
    "VersionsError",
    "load_versions",
    "verify_versions",
    "render_versions_summary",
]

# 文件内版本行的正则
_VERSION_LINE_RE = re.compile(
    r"^>\s*\*\*版本\*\*：`(?P<cv>[^`]+)`\s*｜\s*轮次\s*`(?P<it>[^`]+)`",
    re.MULTILINE,
)


class VersionsError(Exception):
    """版本索引相关错误。"""


def load_versions(repo_root: str) -> dict:
    p = os.path.join(repo_root, "versions.json")
    if not os.path.exists(p):
        raise VersionsError(f"versions.json 不存在: {p}")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise VersionsError(f"versions.json 不是合法 JSON: {e}") from e


def _file_version_line(path: str) -> tuple[str, str] | None:
    """读文件头 20 行内的版本行，返回 (content_version, iteration) 或 None。"""
    try:
        with open(path, encoding="utf-8") as f:
            head = [next(f) for _ in range(20)]
    except (StopIteration, OSError):
        try:
            with open(path, encoding="utf-8") as f:
                head = f.readlines()[:20]
        except OSError:
            return None
    m = _VERSION_LINE_RE.search("".join(head))
    if not m:
        return None
    return m.group("cv"), m.group("it")


def _extract_yaml_scalar(text: str, key: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(key)}\s*:\s*[\"']?([^\"'\n#]+)", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _dig(obj, dotted: str):
    """按点号路径取值，如 'inputs.data_version'。"""
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _extract_from_file(path: str, ref: str):
    """从文件读 ref 的值。ref 支持点号路径。"""
    if path.endswith(".json"):
        try:
            with open(path, encoding="utf-8") as f:
                obj = json.load(f)
            return _dig(obj, ref)
        except json.JSONDecodeError:
            txt = open(path, encoding="utf-8").read()
            return _extract_yaml_scalar(txt, ref)
    if path.endswith(".toml"):
        txt = open(path, encoding="utf-8").read()
        try:
            import tomllib  # py3.11+
            with open(path, "rb") as f:
                obj = tomllib.load(f)
            v = _dig(obj, ref)
            if v is not None:
                return v
        except Exception:  # noqa: BLE001
            pass
        return _extract_yaml_scalar(txt, ref)
    txt = open(path, encoding="utf-8").read()
    return _extract_yaml_scalar(txt, ref)


def verify_versions(repo_root: str) -> dict:
    """执行全部一致性检查。

    返回：
        {
          "errors": [...],     # 必须修
          "warnings": [...],   # 提示
          "stats": {...},      # 统计
        }
    """
    errors: list[str] = []
    warnings: list[str] = []
    d = load_versions(repo_root)

    entries = d.get("entries") or []
    if not entries:
        errors.append("versions.json 的 entries 为空")
        return {"errors": errors, "warnings": warnings, "stats": {}}

    by_lvl: dict[str, int] = {}
    n_missing = 0
    n_verline_ok = 0
    n_verline_need = 0
    n_c_ok = 0
    n_c_bad = 0

    # ---- 1. 逐条目检查
    for e in entries:
        path = e.get("path") or ""
        lvl = e.get("level")
        by_lvl[lvl] = by_lvl.get(lvl, 0) + 1

        if not path:
            errors.append("条目缺 path")
            continue

        full = os.path.join(repo_root, path)

        # 1.1 文件必须存在
        if not os.path.exists(full):
            errors.append(f"文件不存在: {path}")
            n_missing += 1
            continue

        # 1.2 版本号格式
        cv = e.get("content_version")
        if cv is not None and not re.fullmatch(r"\d+\.\d+", cv):
            errors.append(f"{path}: content_version 格式非法 '{cv}'（应为 x.y）")

        it = e.get("iteration")
        if it is not None and not re.fullmatch(r"r\d{2}", it):
            errors.append(f"{path}: iteration 格式非法 '{it}'（应为 rNN）")

        # 1.3 A/B 级 .md 必须有文件内版本行且与索引一致
        if lvl in ("A", "B") and path.endswith(".md") and cv:
            if path in ("VERSION_INDEX.md", "memory/facts/INDEX.md"):
                continue  # 派生物，版本由生成器负责
            n_verline_need += 1
            got = _file_version_line(full)
            if got is None:
                errors.append(
                    f"{path}: 索引记为 v{cv}，但**文件内没有版本行**"
                    f"（应加 `> **版本**：`{cv}` ｜ 轮次 `{it or 'rNN'}` ...`）"
                )
            elif got[0] != cv:
                errors.append(
                    f"{path}: 版本不一致 —— 索引 v{cv} vs 文件内 v{got[0]}"
                )
            else:
                if it and got[1] != it:
                    warnings.append(
                        f"{path}: 轮次不一致 —— 索引 {it} vs 文件内 {got[1]}"
                    )
                n_verline_ok += 1

        # 1.4 C 级：ref_version 必须与文件实际值一致
        if lvl == "C" and e.get("version_ref") and e.get("ref_version"):
            ref = e["version_ref"]
            want = e["ref_version"]
            try:
                got = _extract_from_file(full, ref)
            except OSError as ex:
                warnings.append(f"{path}: 读取失败 {ex}")
                got = None
            if got is None:
                warnings.append(f"{path}: 无法从文件读出 {ref}（跳过比对）")
            elif str(got) != str(want):
                errors.append(
                    f"{path}: {ref} 不一致 —— 索引 {want} vs 文件 {got}"
                )
                n_c_bad += 1
            else:
                n_c_ok += 1

    # ---- 2. VERSION_INDEX.md 必须是 versions.json 的最新派生物
    vi = os.path.join(repo_root, "VERSION_INDEX.md")
    if not os.path.exists(vi):
        errors.append("VERSION_INDEX.md 不存在（应跑 render_version_index.py --write）")
    else:
        try:
            import sys
            tools = os.path.join(repo_root, "tools")
            if tools not in sys.path:
                sys.path.insert(0, tools)
            import render_version_index as rvi  # type: ignore
            expected = rvi.gen()
            actual = open(vi, encoding="utf-8").read()
            if expected.strip() != actual.strip():
                warnings.append(
                    "VERSION_INDEX.md 与 versions.json 不同步 —— "
                    "跑 `python tools/render_version_index.py --write`"
                )
        except Exception as ex:  # noqa: BLE001
            warnings.append(f"无法比对 VERSION_INDEX.md（{type(ex).__name__}: {ex}）")

    # ---- 3. framework_version 与文件内声明一致
    fv = d.get("framework_version")
    if not fv:
        warnings.append("versions.json 缺 framework_version")

    stats = {
        "total": len(entries),
        "by_level": by_lvl,
        "file_version_lines_ok": n_verline_ok,
        "file_version_lines_needed": n_verline_need,
        "c_level_checked_ok": n_c_ok,
        "c_level_mismatch": n_c_bad,
        "missing_files": n_missing,
        "index_version": d.get("index_version"),
        "framework_version": fv,
        "current_iteration": d.get("current_iteration"),
    }
    return {"errors": errors, "warnings": warnings, "stats": stats}


def render_versions_summary(repo_root: str) -> str:
    """渲染版本概览（供 CLI 打印）。"""
    d = load_versions(repo_root)
    out: list[str] = []
    out.append(f"索引版本: {d.get('index_version')}   "
               f"框架版本: {d.get('framework_version')}   "
               f"当前轮次: {d.get('current_iteration')}")
    out.append("")

    entries = d.get("entries") or []
    by_lvl: dict[str, list[dict]] = {}
    for e in entries:
        by_lvl.setdefault(e["level"], []).append(e)

    names = {"A": "结论性内容", "B": "结构性文档/代码",
             "C": "机器契约", "D": "纯数据/脚本"}
    for lvl in "ABCD":
        rows = by_lvl.get(lvl, [])
        out.append(f"{lvl} 级 · {names[lvl]}：{len(rows)} 个")
        if lvl in ("A", "B"):
            with_v = [r for r in rows if r.get("content_version")]
            out.append(f"    其中带 content_version：{len(with_v)}")
        elif lvl == "C":
            out.append("    版本字段（镜像）：")
            for r in rows:
                ref = r.get("version_ref") or "-"
                val = r.get("ref_version") or "-（仅登记，不比对）"
                out.append(f"      {r['path']:52s} {ref:18s} = {val}")
        out.append("")

    hist = d.get("history") or []
    out.append(f"演化史：{len(hist)} 条")
    for h in hist:
        out.append(f"    v{h['version']}  {h['date']}  [{h.get('scope') or '-'}]  {h['change'][:60]}")
    return "\n".join(out)
