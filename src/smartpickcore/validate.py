# -*- coding: utf-8 -*-
"""smartpickcore.validate — 契约校验器

校验四类对象（受 spec/*.schema.json 约束）：
  1. game.yaml            → game_config.schema.json
  2. FACTS.jsonl 每行     → fact.schema.json
  3. strategy.json        → strategy.schema.json
  4. iterations/**/manifest.json → iteration.schema.json

**本模块是本仓库纪律的执行者。** 它检查的不只是语法，还有：

  - 红线段落恒为期望值（affects_win_probability / changes_win_probability /
    optimizable_target / sum_affects_numbers）
  - 外键引用存在（strategy.evidence_refs → FACTS.jsonl）
  - source / evidence.script 指向的文件真实存在
  - supersedes ↔ superseded_by 双向一致

用法：
    from smartpickcore.validate import validate_all
    errs = validate_all()
    if errs: ...
"""
from __future__ import annotations

import json
import os
from typing import Any

__all__ = [
    "ValidationReport",
    "validate_all",
    "validate_game",
    "validate_facts",
    "validate_strategy",
    "validate_iterations",
]

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ValidationReport:
    """校验报告。errors 非空即失败。"""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checked: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self, msg: str) -> None:
        self.checked.append(msg)

    @property
    def passed(self) -> bool:
        return not self.errors

    def render(self, verbose: bool = False) -> str:
        out = []
        if verbose:
            for c in self.checked:
                out.append(f"  ✓ {c}")
        if self.warnings:
            out.append(f"\n⚠ {len(self.warnings)} 项警告：")
            for w in self.warnings:
                out.append(f"  ! {w}")
        if self.errors:
            out.append(f"\n✗ {len(self.errors)} 项错误：")
            for e in self.errors:
                out.append(f"  ✗ {e}")
        else:
            out.append(f"\n✓ 全部通过（{len(self.checked)} 项检查）")
        return "\n".join(out)


# ---------------------------------------------------------------- schema

def _load_schema(name: str) -> dict | None:
    p = os.path.join(_ROOT, "spec", name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _jsonschema_check(obj: Any, schema_name: str, label: str, rep: ValidationReport) -> None:
    """用 jsonschema 校验。未安装时降级为"跳过并警告"。"""
    schema = _load_schema(schema_name)
    if schema is None:
        rep.warn(f"{label}: schema 文件 {schema_name} 不存在，跳过结构校验")
        return
    try:
        import jsonschema  # type: ignore
    except ImportError:
        rep.warn(
            f"{label}: jsonschema 未安装，跳过 schema 结构校验"
            f"（安装: pip install jsonschema）"
        )
        return
    try:
        jsonschema.validate(instance=obj, schema=schema)
        rep.ok(f"{label} 合规于 {schema_name}")
    except jsonschema.ValidationError as e:
        loc = "/".join(str(p) for p in e.absolute_path) or "(根)"
        rep.err(f"{label}: {schema_name} 校验失败 @ {loc}: {e.message}")
    except jsonschema.SchemaError as e:
        rep.err(f"{label}: schema 本身有误 {schema_name}: {e.message}")


# ---------------------------------------------------------------- game

def validate_game(game: str, repo_root: str | None = None,
                  rep: ValidationReport | None = None) -> ValidationReport:
    rep = rep or ValidationReport()
    root = repo_root or _ROOT
    path = os.path.join(root, "games", game, "game.yaml")
    if not os.path.exists(path):
        rep.err(f"game {game}: 配置不存在 {path}")
        return rep

    try:
        import yaml  # type: ignore
    except ImportError:
        rep.warn("PyYAML 未安装，跳过 game.yaml 校验")
        return rep

    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    _jsonschema_check(cfg, "game_config.schema.json", f"game.yaml[{game}]", rep)

    # 特征声明可执行性（framework/core 的静态检查）
    # 这是「machine_rule.predicate 可被求值」的前提：
    # 若 features[] 声明了不存在的 primitive、或 args 缺参数，
    # 则所有引用该特征的规则都无法执行。
    try:
        import sys as _sys
        _fw = os.path.join(root, "framework")
        if _fw not in _sys.path:
            _sys.path.insert(0, _fw)
        from core.game_util import validate_feature_declarations  # type: ignore

        ferrs = validate_feature_declarations(cfg)
        for e in ferrs:
            rep.err(f"game {game}: {e}")
        if not ferrs:
            n_exec = sum(1 for f in cfg.get("features", []) if f.get("primitive"))
            n_all = len(cfg.get("features", []))
            rep.ok(
                f"game {game}: features 声明可执行 "
                f"({n_exec}/{n_all} 个含 primitive)"
            )
    except ImportError as e:
        rep.warn(f"game {game}: 无法加载 framework/core 做特征声明检查（{e}）")

    # 红线：奖金规则不影响号码分布
    for e in (cfg.get("prize_model") or {}).get("epochs", []):
        if e.get("sum_affects_numbers") is not False:
            rep.err(
                f"game {game}: epoch {e.get('id')} 的 sum_affects_numbers "
                f"必须为 False（红线）"
            )

    # 数据文件与 SHA256
    raw = (cfg.get("data") or {}).get("raw") or {}
    raw_path = raw.get("path")
    if raw_path:
        abs_raw = os.path.join(root, raw_path)
        if not os.path.exists(abs_raw):
            rep.err(f"game {game}: data.raw.path 不存在: {raw_path}")
        else:
            declared = raw.get("sha256")
            if declared:
                import hashlib
                h = hashlib.sha256()
                with open(abs_raw, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
                got = h.hexdigest()
                if got != declared:
                    rep.err(
                        f"game {game}: {raw_path} 的 SHA256 不符\n"
                        f"      声明 = {declared}\n"
                        f"      实际 = {got}"
                    )
                else:
                    rep.ok(f"game {game}: SHA256 一致 ({raw_path})")
            else:
                rep.warn(f"game {game}: data.raw 未声明 sha256")

    # derived 文件存在性
    der = (cfg.get("data") or {}).get("derived") or {}
    der_dir = der.get("path")
    if der_dir:
        for fn in der.get("files", []):
            if not os.path.exists(os.path.join(root, der_dir, fn)):
                rep.err(f"game {game}: derived 文件缺失 {der_dir}/{fn}")
    rebuild = der.get("rebuild_script")
    if rebuild and not os.path.exists(os.path.join(root, rebuild)):
        rep.err(f"game {game}: rebuild_script 不存在: {rebuild}")

    # strategy_output 指向的 schema 存在
    so = cfg.get("strategy_output") or {}
    if so.get("schema") and not os.path.exists(os.path.join(root, so["schema"])):
        rep.err(f"game {game}: strategy_output.schema 不存在: {so['schema']}")

    return rep


# ---------------------------------------------------------------- facts

def validate_facts(repo_root: str | None = None,
                   rep: ValidationReport | None = None) -> ValidationReport:
    """校验 FACTS.jsonl：schema + 红线 + 外键 + 双向取代 + caveats 非空。"""
    rep = rep or ValidationReport()
    root = repo_root or _ROOT
    facts_path = os.path.join(root, "memory", "facts", "FACTS.jsonl")
    if not os.path.exists(facts_path):
        rep.err(f"FACTS.jsonl 不存在: {facts_path}")
        return rep

    facts: list[dict] = []
    with open(facts_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                facts.append(json.loads(line))
            except json.JSONDecodeError as e:
                rep.err(f"FACTS.jsonl:{lineno} JSON 解析失败: {e}")
                return rep

    if not facts:
        rep.err("FACTS.jsonl 为空")
        return rep

    by_id: dict[str, dict] = {}
    for i, ft in enumerate(facts):
        fid = ft.get("id", f"<line {i+1}>")

        # schema
        _jsonschema_check(ft, "fact.schema.json", f"FACT {fid}", rep)

        # 重复 id
        if fid in by_id:
            rep.err(f"FACT {fid}: id 重复")
        by_id[fid] = ft

        # 红线（显式再查一次，schema 失败时也能报出）
        if ft.get("affects_win_probability") is not False:
            rep.err(
                f"FACT {fid}: 红线违反 affects_win_probability="
                f"{ft.get('affects_win_probability')!r}，必须为 False"
            )

        # source 存在
        src = ft.get("source")
        if src and not os.path.exists(os.path.join(root, src)):
            rep.err(f"FACT {fid}: source 不存在: {src}")

        # evidence.script 存在
        ev = ft.get("evidence") or {}
        scr = ev.get("script")
        if scr and not os.path.exists(os.path.join(root, scr)):
            rep.err(f"FACT {fid}: evidence.script 不存在: {scr}")

        # caveats 非空（本仓库约定）
        if not ft.get("caveats"):
            rep.err(
                f"FACT {fid}: caveats 为空。本仓库约定必须非空"
                f"（否则 caveat→问题 的自我迭代传导断裂）"
            )

    # 双向取代一致性
    for fid, ft in by_id.items():
        sb, ss = ft.get("superseded_by"), ft.get("supersedes")
        if sb:
            if sb not in by_id:
                rep.err(f"FACT {fid}: superseded_by={sb} 不存在")
            elif by_id[sb].get("supersedes") != fid:
                rep.err(
                    f"FACT {fid}: 双向不一致 — {sb}.supersedes="
                    f"{by_id[sb].get('supersedes')!r}，应为 {fid!r}"
                )
            if ft.get("status") != "superseded":
                rep.err(
                    f"FACT {fid}: 有 superseded_by 但 status={ft.get('status')!r}"
                    f"（应为 superseded）"
                )
        if ss:
            if ss not in by_id:
                rep.err(f"FACT {fid}: supersedes={ss} 不存在")
            elif by_id[ss].get("superseded_by") != fid:
                rep.err(
                    f"FACT {fid}: 双向不一致 — {ss}.superseded_by="
                    f"{by_id[ss].get('superseded_by')!r}，应为 {fid!r}"
                )
        if ft.get("status") == "superseded" and not sb:
            rep.err(f"FACT {fid}: status=superseded 但未填 superseded_by")

    rep.ok(f"FACTS.jsonl: {len(facts)} 条，红线/外键/双向取代/caveats 全部检查")
    return rep


def load_fact_ids(repo_root: str | None = None) -> set[str]:
    root = repo_root or _ROOT
    p = os.path.join(root, "memory", "facts", "FACTS.jsonl")
    ids: set[str] = set()
    if not os.path.exists(p):
        return ids
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    ids.add(json.loads(line)["id"])
                except Exception:
                    pass
    return ids


# ---------------------------------------------------------------- strategy

def validate_strategy(game: str, repo_root: str | None = None,
                      rep: ValidationReport | None = None) -> ValidationReport:
    """校验 strategy.json：schema + 红线 + evidence_refs 外键存在。"""
    rep = rep or ValidationReport()
    root = repo_root or _ROOT
    p = os.path.join(root, "games", game, "strategy", "strategy.json")
    if not os.path.exists(p):
        rep.warn(f"game {game}: strategy.json 不存在，跳过（尚未生成？）")
        return rep

    with open(p, encoding="utf-8") as f:
        try:
            st = json.load(f)
        except json.JSONDecodeError as e:
            rep.err(f"game {game}: strategy.json JSON 解析失败: {e}")
            return rep

    _jsonschema_check(st, "strategy.schema.json", f"strategy[{game}]", rep)

    # 红线
    dis = st.get("disclaimer") or {}
    if dis.get("changes_win_probability") is not False:
        rep.err(
            f"strategy[{game}]: 红线违反 disclaimer.changes_win_probability="
            f"{dis.get('changes_win_probability')!r}，必须为 False"
        )
    if dis.get("is_negative_ev") is not True:
        rep.err(
            f"strategy[{game}]: 红线违反 disclaimer.is_negative_ev="
            f"{dis.get('is_negative_ev')!r}，必须为 True"
        )
    bd = st.get("boundary") or {}
    if bd.get("optimizable_target") != "expected_bonus_given_win":
        rep.err(
            f"strategy[{game}]: 红线违反 boundary.optimizable_target="
            f"{bd.get('optimizable_target')!r}，只能是 'expected_bonus_given_win'"
        )

    # evidence_refs 外键
    fact_ids = load_fact_ids(root)
    for rule in st.get("rules", []):
        rid = rule.get("id", "?")
        refs = rule.get("evidence_refs") or []
        if not refs:
            rep.err(f"strategy[{game}].{rid}: evidence_refs 为空（每条规则必须有证据）")
        for r in refs:
            if r not in fact_ids:
                rep.err(f"strategy[{game}].{rid}: evidence_refs 指向不存在的结论 {r}")
        evi = rule.get("expected_value_impact") or {}
        if evi.get("changes_win_probability") is not False:
            rep.err(
                f"strategy[{game}].{rid}: 红线违反 "
                f"expected_value_impact.changes_win_probability 必须为 False"
            )
    for a in st.get("avoid_list", []):
        aid = a.get("id", "?")
        for r in a.get("refuted_by") or []:
            if r not in fact_ids:
                rep.err(f"strategy[{game}].{aid}: refuted_by 指向不存在的结论 {r}")

    # evidence_index 应覆盖被引用的全部结论
    idx_ids = {e.get("id") for e in st.get("evidence_index", [])}
    used: set[str] = set()
    for rule in st.get("rules", []):
        used.update(rule.get("evidence_refs") or [])
    for a in st.get("avoid_list", []):
        used.update(a.get("refuted_by") or [])
    missing = used - idx_ids
    if missing:
        rep.warn(
            f"strategy[{game}]: evidence_index 未覆盖被引用的结论 {sorted(missing)}"
            f"（消费者需回读 FACTS.jsonl 才能获得摘要）"
        )

    # machine_rule 的 predicate 引用完整性 + 作用域
    # 这是「规则可被执行」的关键检查：
    #   · 引用了未声明的特征 → 任何实现都无法求值
    #   · 引用跨注特征 → 单注层无法判定（属 L3，应显式声明而非悄悄失败）
    try:
        import sys as _sys
        _fw = os.path.join(root, "framework")
        if _fw not in _sys.path:
            _sys.path.insert(0, _fw)
        from core.judge import PredicateError, apply_scope, parse_predicate  # type: ignore
    except ImportError as e:
        rep.warn(f"strategy[{game}]: 无法加载 framework/core 做 predicate 检查（{e}）")
        return rep

    cfg_path = os.path.join(root, "games", game, "game.yaml")
    declared: list[str] = []
    if os.path.exists(cfg_path):
        try:
            import yaml  # type: ignore
            with open(cfg_path, encoding="utf-8") as f:
                _cfg = yaml.safe_load(f)
            declared = [f["key"] for f in (_cfg.get("features") or [])]
        except Exception:
            pass

    single_cnt = cross_cnt = 0
    for rule in st.get("rules", []):
        rid = rule.get("id", "?")
        mr = rule.get("machine_rule") or {}
        pred = mr.get("predicate")
        if not pred:
            continue
        if declared:
            try:
                unknown = [f for f in parse_predicate(pred).features()
                           if f not in declared]
            except PredicateError as e:
                rep.err(f"strategy[{game}].{rid}: predicate 解析失败: {e}")
                continue
            if unknown:
                # 不是错误：可能是跨注特征。但要显式区分「跨注」与「拼错」
                rep.warn(
                    f"strategy[{game}].{rid}: predicate 引用了未声明的特征 "
                    f"{unknown} —— 该规则**单注层无法判定**，"
                    f"若这是跨注特征（如组合分散度）应属 L3；"
                    f"若是拼写错误则须修正。"
                )
                cross_cnt += 1
            else:
                single_cnt += 1
    if declared and (single_cnt or cross_cnt):
        rep.ok(
            f"strategy[{game}]: predicate 作用域 单注层 {single_cnt} 条 / "
            f"跨注或未声明 {cross_cnt} 条"
        )

    return rep


# ---------------------------------------------------------------- iteration

def validate_iterations(game: str, repo_root: str | None = None,
                        rep: ValidationReport | None = None) -> ValidationReport:
    """校验各轮 manifest.json。"""
    rep = rep or ValidationReport()
    root = repo_root or _ROOT
    it_dir = os.path.join(root, "games", game, "iterations")
    if not os.path.isdir(it_dir):
        rep.warn(f"game {game}: iterations/ 不存在")
        return rep

    fact_ids = load_fact_ids(root)
    n = 0
    for name in sorted(os.listdir(it_dir)):
        mf = os.path.join(it_dir, name, "manifest.json")
        if not os.path.isfile(mf):
            continue
        n += 1
        with open(mf, encoding="utf-8") as f:
            try:
                m = json.load(f)
            except json.JSONDecodeError as e:
                rep.err(f"{name}/manifest.json JSON 解析失败: {e}")
                continue
        _jsonschema_check(m, "iteration.schema.json", f"iteration[{game}/{name}]", rep)

        # fact id 引用存在
        out = m.get("outputs") or {}
        for key in ("new_fact_ids", "superseded_fact_ids", "refuted_fact_ids"):
            for fid in out.get(key) or []:
                if fid not in fact_ids:
                    rep.err(f"{name}/manifest.json: {key} 指向不存在的结论 {fid}")
        inp = m.get("inputs") or {}
        for fid in inp.get("upstream_fact_ids") or []:
            if fid not in fact_ids:
                rep.err(f"{name}/manifest.json: inputs.upstream_fact_ids 指向不存在的结论 {fid}")

        # deliverables 文件存在
        for d in m.get("deliverables") or []:
            dp = d.get("path")
            if dp and not os.path.exists(os.path.join(root, dp)):
                rep.err(f"{name}/manifest.json: deliverable 不存在 {dp}")

    if n:
        rep.ok(f"iterations: 检查了 {n} 个 manifest.json")
    return rep


# ---------------------------------------------------------------- all

def validate_all(repo_root: str | None = None, verbose: bool = False) -> ValidationReport:
    """全量校验。"""
    root = repo_root or _ROOT
    rep = ValidationReport()

    # 彩种
    games = []
    gd = os.path.join(root, "games")
    if os.path.isdir(gd):
        for name in sorted(os.listdir(gd)):
            if name.startswith("_") or name.startswith("."):
                continue
            if os.path.isfile(os.path.join(gd, name, "game.yaml")):
                games.append(name)
    if not games:
        rep.warn("games/ 下未发现任何彩种（含 game.yaml 的目录）")

    for g in games:
        validate_game(g, root, rep)
        validate_strategy(g, root, rep)
        validate_iterations(g, root, rep)

    validate_facts(root, rep)

    # 协议文档存在性（软检查）
    docs = [
        "AI_CONTEXT.md",
        "memory/lessons/LESSONS.md",
        "memory/INDEX.md",
        "framework/protocol/ITERATION_PROTOCOL.md",
        "framework/protocol/MEMORY_PROTOCOL.md",
        "framework/methodology/MATH_BOUNDARY.md",
        "framework/methodology/STATISTICAL_DISCIPLINE.md",
        "spec/README.md",
        "spec/VERSIONING.md",
    ]
    for d in docs:
        if not os.path.exists(os.path.join(root, d)):
            rep.warn(f"协议/文档缺失: {d}")
        else:
            rep.ok(f"文档存在: {d}")

    return rep


if __name__ == "__main__":  # pragma: no cover
    import sys

    r = validate_all(verbose="-v" in sys.argv)
    print(r.render(verbose="-v" in sys.argv))
    sys.exit(0 if r.passed else 1)
