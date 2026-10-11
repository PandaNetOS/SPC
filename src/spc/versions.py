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

# 版本行是仓库级**单一格式来源**：所有生成器（ai_map/depmap/flywheel/
# render_task_brief）与 tools/inject_version_lines.py 都必须用它，
# 禁止在任何地方手写或硬编码版本行格式。
VERSION_LINE_MARK = "> **版本**："


def version_line(cv: str, it: str, updated: str) -> str:
    """生成标准版本行（两行：版本行 + 版本规则见）。"""
    return (
        f"{VERSION_LINE_MARK}`{cv}` ｜ 轮次 `{it}` ｜ 更新 {updated} ｜ 权威源 `VERSION_INDEX.md`\n"
        f"> 版本规则见 `docs/VERSIONING_DOCS.md`"
    )


def registered_version(root: str, path: str) -> tuple[str | None, str, str]:
    """从 versions.json 取某登记条目的 (content_version, iteration, updated_at)。

    供各生成器写头部版本行使用（版本行单一来源 = 登记）。
    """
    try:
        d = load_versions(root)
        e = next(x for x in d["entries"] if x["path"] == path)
        return (e.get("content_version"), e.get("iteration") or "",
                e.get("updated_at") or "")
    except (VersionsError, StopIteration):
        return None, "", ""


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

    # ---- 1.5 轮次停滞检查（r14.2 根治）：活文档 iteration 必须 == current_iteration
    #
    # 背景（README 头部版本行滞后事故的通用形态）：此前全部检查都是
    # 「文件内版本行 ↔ 索引条目」的**同源双向比对**，而 current_iteration
    # 只作为 stats 打印、从不参与判定。于是索引条目一旦过期，
    # inject_version_lines.py 会照抄过期值写进文件头 —— 两边一致、照样全绿。
    # 校验器抓得住 A≠B，抓不住 A、B 一起过时。这里补上后者。
    cur = d.get("current_iteration")
    n_follow_ok = 0
    n_follow_lag = 0
    if cur:
        for e in entries:
            path = e.get("path") or ""
            it = e.get("iteration") or ""
            if not it:
                continue

            if e.get("follows_current"):
                # 活文档：硬性判据，落后即错（不是 warning —— warning 可被忽略）
                if it == cur:
                    n_follow_ok += 1
                else:
                    n_follow_lag += 1
                    errors.append(
                        f"{path}: 轮次停滞 —— 活文档登记轮次 {it} 落后于 "
                        f"current_iteration {cur}（follows_current=true）。"
                        f"跑 `python tools/bump_iteration.py --write` 对齐；"
                        f"若内容有实质变更，请同时提升 content_version"
                    )
                continue

            # 未标 follows_current 的条目**不做**「落后 N 轮」的泛化告警。
            #
            # 实测（r14.2）：这样做会一次性刷出 26 条（限 .md 后）／69 条（含代码）
            # 无操作价值的告警 —— 稳定文档的 iteration 语义本就是「创建/上次产出轮次」，
            # 落后不等于错；轮次产物（roundNN/*）与 journal 更是天生属于产出那一轮。
            # 警告一旦失去可操作性，就会淹没真正的错误信号（本仓库常态仅十余条警告）。
            # 故防停滞**只认显式声明**：想要护栏就在 versions.json 标 follows_current=true。
    else:
        warnings.append("versions.json 缺 current_iteration，跳过轮次停滞检查")

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

    # ---- 4. README 里的版本标注必须与 versions.json 一致
    #        支持两种写法（同一行可同时命中）：
    #          a) 目录树：  `<短路径>   vX.Y   ← 说明`
    #          b) 链接标题：`[**名字**](路径) ... `vX.Y``  或  `路径 — vX.Y`
    #        目录树/链接常用短名（如 `facts/INDEX.md`），按**后缀唯一匹配**解析；
    #        歧义（裸 `INDEX.md` 有 4 个候选）或多义时跳过，不误报。
    n_readme_ok = 0
    n_readme_bad = 0
    n_readme_skip = 0
    readme = os.path.join(repo_root, "README.md")
    if os.path.exists(readme):
        all_paths = [e.get("path") or "" for e in entries]
        by_path = {e.get("path"): e for e in entries}

        # 形式 a：行首短路径 + 2 空格以上 + vX.Y
        re_tree = re.compile(
            r"^\s*(?P<path>[^\s/]+(?:/[^\s]+)*?)\s{2,}v(?P<ver>\d+\.\d+)\s")
        # 形式 b：被 `(...)`（Markdown 链接）或 `` `...` `` 包裹的路径，
        #         其后 30 字符内出现 vX.Y（版本可再被反引号包裹）
        re_ref = re.compile(
            r"(?:\(|`)(?P<path>[A-Za-z0-9_./\-]+\.(?:md|json|jsonl|ya?ml|py|toml))"
            r"(?:\)|`)[^\n]{0,30}?`?v(?P<ver>\d+\.\d+)`?")

        def _resolve(raw: str) -> tuple[str | None, int]:
            """把短名/全路径解析成唯一条目。返回 (path|None, 状态)。

            状态：1=唯一命中  0=歧义/未登记（跳过）
            """
            raw = raw.lstrip("./")
            if raw in by_path:
                return raw, 1
            cands = [
                p for p in all_paths
                if p.endswith("/" + raw) or p.lower() == raw.lower()
                or p.lower().endswith("/" + raw.lower())
            ]
            if len(cands) == 1:
                return cands[0], 1
            return None, 0

        for lineno, line in enumerate(open(readme, encoding="utf-8"), 1):
            hits: list[tuple[str, str]] = []          # (path, ver)
            for m in re_tree.finditer(line):
                hits.append((m.group("path"), m.group("ver")))
            for m in re_ref.finditer(line):
                hits.append((m.group("path"), m.group("ver")))
            for raw, got in hits:
                cand, st = _resolve(raw)
                if st != 1 or cand is None:
                    n_readme_skip += 1
                    continue
                e = by_path.get(cand)
                want = (e or {}).get("content_version")
                if want is None:
                    n_readme_skip += 1  # 该文件不单独版本化
                elif got != want:
                    errors.append(
                        f"README.md:{lineno} 版本标注过期 —— "
                        f"README 写 v{got}，索引是 v{want}（'{cand}'）"
                    )
                    n_readme_bad += 1
                else:
                    n_readme_ok += 1

    stats = {
        "total": len(entries),
        "by_level": by_lvl,
        "file_version_lines_ok": n_verline_ok,
        "file_version_lines_needed": n_verline_need,
        "c_level_checked_ok": n_c_ok,
        "c_level_mismatch": n_c_bad,
        "readme_version_tags_ok": n_readme_ok,
        "readme_version_tags_bad": n_readme_bad,
        "readme_version_tags_skip": n_readme_skip,
        "missing_files": n_missing,
        "follows_current_ok": n_follow_ok,
        "follows_current_lagging": n_follow_lag,
        "index_version": d.get("index_version"),
        "framework_version": fv,
        "project_version": d.get("project_version"),
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
