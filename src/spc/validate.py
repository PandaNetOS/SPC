# -*- coding: utf-8 -*-
"""spc.validate — 契约校验器

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
    from spc.validate import validate_all
    errs = validate_all()
    if errs: ...
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from .tree import load_versions, render_tree

__all__ = [
    "ValidationReport",
    "validate_all",
    "validate_game",
    "validate_facts",
    "validate_strategy",
    "validate_iterations",
    "validate_versions",
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
        from core.game_util import (  # type: ignore
            cross_feature_keys,
            single_feature_keys,
            validate_feature_declarations,
        )

        ferrs = validate_feature_declarations(cfg)
        for e in ferrs:
            rep.err(f"game {game}: {e}")
        if not ferrs:
            n_exec = sum(1 for f in cfg.get("features", []) if f.get("primitive"))
            n_all = len(cfg.get("features", []))
            n_cross = len(cross_feature_keys(cfg))
            n_single = len(single_feature_keys(cfg))
            rep.ok(
                f"game {game}: features 声明可执行 "
                f"({n_exec}/{n_all} 个含 primitive；"
                f"单注 {n_single} / 跨注 {n_cross})"
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


# ---------------------------------------------------------------- v2.0 增强

# confidence(0-5) → GRADE grade 的映射（仅允许因降级理由低于映射值，不得高于）
GRADE_FROM_CONFIDENCE = {5: "high", 4: "high", 3: "moderate", 2: "low", 1: "low"}
GRADE_ORDER = {"insufficient": 0, "low": 1, "moderate": 2, "high": 3}


def check_v2_fields(ft: dict, fid: str, rep: ValidationReport) -> None:
    """v2.0 字段检查：confidence_grade / change_type / valid_until / recalibrate_every。

    - confidence_grade 必须在枚举内，且不得『高于』confidence 数值的映射档
      （只能因 GRADE 五维降级理由低于映射值 —— 不允许自我拔高）。
    - change_type 必须在枚举内（initial / update / revision）。
    - valid_until 格式为 YYYY-MM-DD 或 null。
    - recalibrate_every 为 ≥1 整数或 null。
    """
    conf = ft.get("confidence")
    grade = ft.get("confidence_grade")
    if grade is None:
        rep.err(f"FACT {fid}: 缺 confidence_grade（v2.0 必填）")
    elif grade not in GRADE_ORDER:
        rep.err(f"FACT {fid}: confidence_grade={grade!r} 不在枚举内"
                f"（high/moderate/low/insufficient）")
    elif conf is not None and grade in GRADE_ORDER and conf in GRADE_FROM_CONFIDENCE:
        allowed_max = GRADE_ORDER[GRADE_FROM_CONFIDENCE[conf]]
        if GRADE_ORDER[grade] > allowed_max:
            rep.err(
                f"FACT {fid}: confidence_grade={grade!r} 高于 confidence={conf}"
                f" 的映射档 {GRADE_FROM_CONFIDENCE[conf]!r}"
                f" —— 只允许因降级理由低于映射值，不允许自我拔高"
            )

    ct = ft.get("change_type")
    if ct is None:
        rep.err(f"FACT {fid}: 缺 change_type（v2.0 必填，initial/update/revision）")
    elif ct not in ("initial", "update", "revision"):
        rep.err(f"FACT {fid}: change_type={ct!r} 不在枚举内"
                f"（initial=首立 / update=世界变了走重校准 / revision=信念错了走取代）")
    if ct == "revision" and ft.get("status") not in ("superseded", "refuted"):
        rep.err(f"FACT {fid}: change_type=revision 但 status={ft.get('status')!r}"
                f"（revision 必须落到 superseded / refuted）")

    vu = ft.get("valid_until")
    if vu is not None and not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", str(vu)):
        rep.err(f"FACT {fid}: valid_until={vu!r} 格式非法（应为 YYYY-MM-DD 或 null）")

    re_ = ft.get("recalibrate_every")
    if re_ is not None and (not isinstance(re_, int) or re_ < 1):
        rep.err(f"FACT {fid}: recalibrate_every={re_!r} 应为 ≥1 整数或 null")
    if re_ is not None and ft.get("status") == "superseded":
        rep.warn(f"FACT {fid}: 已 superseded 但仍标 recalibrate_every —— "
                 f"失效结论无需重校准，建议清空")


def current_iteration_round(root: str) -> int:
    """从 games/<game>/iterations/ 目录推断当前轮号（roundNN → NN）。"""
    it_dir = os.path.join(root, "games")
    best = 0
    if os.path.isdir(it_dir):
        for g in os.listdir(it_dir):
            d = os.path.join(it_dir, g, "iterations")
            if not os.path.isdir(d):
                continue
            for name in os.listdir(d):
                m = re.match(r"^round(\d{2})$", name)
                if m:
                    best = max(best, int(m.group(1)))
    return best


def check_recalibration(ft: dict, fid: str, root: str, rep: ValidationReport) -> None:
    """v2.0 重校准检查：动态锚点结论 established_in + N 轮后须重验锚点。

    对应 Katsuno & Mendelzon 的 update 通道：奖池/封顶/E6 锚点随开奖变化，
    结论本身没错、但支撑它的数字会过时 —— 过期应被看见（warning），
    由轮次收尾时统一走『重校准流程』而非静默沿用。
    """
    n = ft.get("recalibrate_every")
    if not n:
        return
    est = ft.get("established_in") or ""
    m = re.match(r"^round(\d{2})$", est)
    if not m:
        return
    est_round = int(m.group(1))
    cur = current_iteration_round(root)
    if cur - est_round >= n:
        rep.warn(
            f"FACT {fid}: 动态锚点结论已 {cur - est_round} 轮未重校准"
            f"（established_in={est}，周期 {n} 轮，当前 round{cur:02d}）"
            f" —— 请核验奖池/封顶/锚点数值是否仍成立；"
            f"成立则维持并重记，否则走 update 通道（标 change_type=update，旧记录保留）"
        )


def check_supersede_cycles(by_id: dict[str, dict], rep: ValidationReport) -> None:
    """INV3 全局一致性：取代链（supersedes →）不得成环。

    若 A supersedes B 且 B 的取代链最终回到 A，双向一致性检查也会通过，
    但整条链自相矛盾 —— 环的存在意味着『谁取代谁』不可判定。
    """
    for fid, ft in by_id.items():
        seen: set[str] = set()
        cur: str | None = fid
        while cur:
            if cur in seen:
                chain = " → ".join(seen | {cur})
                rep.err(f"FACT {fid}: 取代链成环 [{chain}] —— supersedes 关系自相矛盾")
                break
            seen.add(cur)
            nxt = by_id[cur].get("supersedes")
            cur = nxt if nxt in by_id else None


# ---------------------------------------------------------------- facts

# ★ claim_type：结论的『证据类型』。判据是『它会在什么情况下变错』，
#   不是『它用了什么方法』 —— 后者只是描述，前者才能推出该强制哪些字段。
#
#   与 spec/fact.schema.json 的 allOf 约束一一对应。此处再实现一遍，
#   是为了在 jsonschema 未安装时仍能报出（红线字段也是同样的双保险写法）。
CLAIM_TYPES: dict[str, str] = {
    "analytic": "只有模型定义错了才会错（组合数 / 概率恒等式）",
    "empirical": "数据换了或时段移位就会错",
    "simulation": "模型假设变了就会错",
    "documentary": "官方规则文本变了就会错",
    "methodological": "关于方法本身的判断（稳健性 / 伪显著 / 口径）",
}


def check_claim_type(ft: dict, fid: str, rep: ValidationReport) -> None:
    """按 claim_type 施加结构性约束（缺字段即报错，不静默放过）。"""
    ct = ft.get("claim_type")
    if ct is None:
        rep.err(
            f"FACT {fid}: 缺 claim_type —— 无法判断这条结论靠什么立住。"
            f"可选：{sorted(CLAIM_TYPES)}"
        )
        return
    if ct not in CLAIM_TYPES:
        rep.err(
            f"FACT {fid}: claim_type={ct!r} 不在枚举内。可选：{sorted(CLAIM_TYPES)}"
        )
        return

    ev = ft.get("evidence") or {}

    if ct == "analytic":
        # 解析结论没有『抽样误差』这个概念。带 p / CI 说明它其实依赖数据。
        for k in ("p_value", "ci95"):
            if ev.get(k) is not None:
                rep.err(
                    f"FACT {fid}: claim_type=analytic 但 evidence.{k}="
                    f"{ev.get(k)!r} —— 解析结论不含抽样不确定性；"
                    f"若它其实依赖数据，应改标 empirical"
                )
    elif ct == "empirical":
        if not ev.get("data_version"):
            rep.err(
                f"FACT {fid}: claim_type=empirical 但未声明 evidence.data_version"
                f" —— 消费者无法判断它对自己这份数据还成不成立"
            )
        if not isinstance(ev.get("n_observations"), int) or ev["n_observations"] < 1:
            rep.err(
                f"FACT {fid}: claim_type=empirical 但 evidence.n_observations="
                f"{ev.get('n_observations')!r}（须为正整数）"
            )
    elif ct == "simulation":
        eff = ev.get("effect")
        if not isinstance(eff, dict) or (
            "n_sim" not in eff and "rng_seed" not in eff
        ):
            rep.err(
                f"FACT {fid}: claim_type=simulation 但 effect 里既无 n_sim 也无 "
                f"rng_seed —— 不可复现的模拟等于不可检验"
            )
        if len(ft.get("caveats") or []) < 2:
            rep.err(
                f"FACT {fid}: claim_type=simulation 但 caveats 少于 2 条"
                f" —— 模型假设必须写出来，藏起来就和拍脑袋没区别"
            )
    elif ct == "documentary":
        if not ev.get("rules_epoch"):
            rep.err(
                f"FACT {fid}: claim_type=documentary 但未声明 evidence.rules_epoch"
                f" —— 规则已变更 6 次（F-0014），脱离 epoch 引用会产生无意义结论"
            )
    elif ct == "methodological":
        if not ft.get("caveats"):
            rep.err(
                f"FACT {fid}: claim_type=methodological 但 caveats 为空"
                f" —— 方法论结论的价值全在『什么情况下不成立』"
            )


def check_source_anchor(ft: dict, fid: str, src: str | None, ev: dict,
                         root: str, rep: ValidationReport) -> None:
    """★ 证据锚定：实算 `source` 的 SHA256 与锚定值比对。

    只锚 `source`，不锚 `evidence.script`：
    脚本会被正常重构（改名、加注释、换库），把脚本哈希当基线
    会制造持续的误报 —— **会误报的检查比没有检查更坏**。
    而 `source` 是结论数字的出处，它变了就意味着"这条结论的担保物变了"。
    """
    declared = ev.get("source_sha256")
    if declared is None:
        rep.warn(
            f"FACT {fid}: 未锚定 evidence.source_sha256 —— "
            f"`{src}` 若被修改无法检出，结论可能已失效。"
            f"重算：python cli/main.py rehash --id {fid}"
        )
        return

    if not src or not os.path.exists(os.path.join(root, src)):
        # 缺失已由上面的 source 存在性检查报错，这里不重复报
        return

    try:
        from .evidence import sha256_file
        got = sha256_file(os.path.join(root, src))
    except OSError as e:
        rep.err(f"FACT {fid}: 无法读取 source 计算哈希: {e}")
        return

    if got != declared:
        rep.err(
            f"FACT {fid}: 证据文件已变更 —— 结论可能失效\n"
            f"      source  = {src}\n"
            f"      锚定值  = {declared}\n"
            f"      实际值  = {got}\n"
            f"      处理：① 确认结论是否仍成立；② 仍成立则重算基线 "
            f"`python cli/main.py rehash --id {fid}`；"
            f"③ 不成立则改 status 并写新结论（旧条不得删）"
        )


def validate_facts(repo_root: str | None = None,
                   rep: ValidationReport | None = None) -> ValidationReport:
    """校验 FACTS.jsonl：schema + 红线 + 外键 + 双向取代 + caveats + claim_type + 证据锚定。"""
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

        # ★ 证据锚定：source 内容漂移检测
        #   路径还在 ≠ 内容没变。若 source 被改，结论里那串数字就失去了担保。
        check_source_anchor(ft, fid, src, ev, root, rep)

        # caveats 非空（本仓库约定）
        if not ft.get("caveats"):
            rep.err(
                f"FACT {fid}: caveats 为空。本仓库约定必须非空"
                f"（否则 caveat→问题 的自我迭代传导断裂）"
            )

        # ★ claim_type 结构性约束
        check_claim_type(ft, fid, rep)

        # ★ v2.0 字段：grade / change_type / valid_until / recalibrate_every
        check_v2_fields(ft, fid, rep)

        # ★ v2.0 重校准：动态锚点结论按轮数到期检查（update 通道）
        check_recalibration(ft, fid, root, rep)

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

    # ★ INV3：取代链无环
    check_supersede_cycles(by_id, rep)

    dist: dict[str, int] = {}
    for ft in facts:
        ct = ft.get("claim_type") or "<缺失>"
        dist[ct] = dist.get(ct, 0) + 1
    summary = " / ".join(f"{k} {v}" for k, v in sorted(dist.items()))

    rep.ok(
        f"FACTS.jsonl: {len(facts)} 条，红线/外键/双向取代/caveats/claim_type 全部检查"
    )
    rep.ok(f"结论证据类型分布：{summary}")
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

    # evidence_refs 外键 + INV2（v2.0：策略不得建立在被推翻的结论上）
    fact_ids = load_fact_ids(root)
    try:
        from .evidence import load_facts  # noqa: PLC0415
        fact_status = {f["id"]: f.get("status") for f in load_facts(root)}
    except Exception:  # noqa: BLE001
        fact_status = {}
    for rule in st.get("rules", []):
        rid = rule.get("id", "?")
        refs = rule.get("evidence_refs") or []
        if not refs:
            rep.err(f"strategy[{game}].{rid}: evidence_refs 为空（每条规则必须有证据）")
        for r in refs:
            if r not in fact_ids:
                rep.err(f"strategy[{game}].{rid}: evidence_refs 指向不存在的结论 {r}")
                continue
            st_ = fact_status.get(r)
            if st_ in ("superseded", "refuted"):
                rep.err(
                    f"strategy[{game}].{rid}: evidence_refs 指向已被推翻的结论 {r}"
                    f"（status={st_}）—— INV2：策略规则不得建立在被取代/证伪的结论上，"
                    f"应改引其取代者（superseded_by）或更新规则"
                )
        # ★ P1-3 策略-证据一致性：每条规则至少 1 条 established 支撑
        active = [r for r in refs if fact_status.get(r) == "established"]
        if not active and refs:
            rep.err(
                f"strategy[{game}].{rid}: 引用集合中无 established 结论"
                f"（{refs}）—— 策略不得只建立在 tentative/失效证据上"
            )
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

    # ★ 证据摘要锚定：策略引用的结论若被改动（数字 / 状态 / 口径 / 减损项），
    #   provenance.evidence_hash 必然变化 —— 让"策略与证据脱节"变成可检出的错误，
    #   而不是靠人记得回来复查。
    prov = st.get("provenance") or {}
    declared_hash = prov.get("evidence_hash")
    if declared_hash is None:
        rep.warn(
            f"strategy[{game}]: provenance.evidence_hash 为 null —— "
            f"被引用的结论若被修改无法检出，策略可能建立在旧结论上。"
            f"重算：`python cli/main.py rehash --strategy`"
        )
    else:
        try:
            from .evidence import evidence_digest, load_facts
            got_hash = evidence_digest(load_facts(root), sorted(used))
        except Exception as e:  # noqa: BLE001
            rep.err(f"strategy[{game}]: 计算证据摘要失败: {e}")
        else:
            if got_hash != declared_hash:
                rep.err(
                    f"strategy[{game}]: 证据摘要不符 —— 策略引用的结论已变更，"
                    f"本策略可能建立在旧结论上\n"
                    f"      锚定值  = {declared_hash}\n"
                    f"      实际值  = {got_hash}\n"
                    f"      处理：① 复核被引用的结论变更了什么；"
                    f"② 仍适用则重算基线 `python cli/main.py rehash --strategy`；"
                    f"③ 不适用则改规则并更新 evidence_refs"
                )
            else:
                rep.ok(
                    f"strategy[{game}]: 证据摘要一致 "
                    f"（{len(used)} 条被引结论，{declared_hash[:16]}…）"
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
        from core.judge import (  # type: ignore
            PredicateError,
            classify_rules,
        )
    except ImportError as e:
        rep.warn(f"strategy[{game}]: 无法加载 framework/core 做 predicate 检查（{e}）")
        return rep

    cfg_path = os.path.join(root, "games", game, "game.yaml")
    cfg: dict[str, Any] | None = None
    if os.path.exists(cfg_path):
        try:
            import yaml  # type: ignore
            with open(cfg_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
        except Exception:
            cfg = None

    if cfg is None:
        rep.warn(f"strategy[{game}]: 读不到 game.yaml，跳过 predicate 作用域检查")
        return rep

    scopes = classify_rules(cfg, st.get("rules", []))

    # ① 未声明特征 = 配置缺陷（拼错 / 漏声明）。这是**错误**，不是警告：
    #    引用了谁都不认识的特征，任何实现都执行不了该规则。
    for r in scopes.undeclared:
        rid = r.get("id", "?")
        mr = r.get("machine_rule") or {}
        rep.err(
            f"strategy[{game}].{rid}: predicate 引用了未声明的特征 —— "
            f"{mr.get('predicate')!r} 中的特征既不在单注声明里、"
            f"也不在跨注声明里。若是跨注性质，请在 game.yaml 用 "
            f"`scope: cross` 声明它；若是拼写错误则须修正。"
        )

    # ② scope 声明与实际作用域不符 = 契约自相矛盾
    for r in st.get("rules", []):
        rid = r.get("id", "?")
        declared_scope = r.get("scope")
        if declared_scope not in (None, "single", "cross"):
            rep.err(
                f"strategy[{game}].{rid}: scope={declared_scope!r} 非法，"
                f"只能是 'single' 或 'cross'"
            )
            continue
        if not r.get("machine_rule"):
            continue
        actual = ("cross" if r in scopes.cross
                  else "undeclared" if r in scopes.undeclared
                  else "single")
        if declared_scope is None:
            rep.warn(
                f"strategy[{game}].{rid}: 未声明 scope（契约 1.1 起必填），"
                f"按其引用特征推断为 {actual}"
            )
        elif declared_scope != actual and actual != "undeclared":
            rep.err(
                f"strategy[{game}].{rid}: 声明 scope={declared_scope!r}，"
                f"但其 predicate 引用的特征实为 {actual!r} —— 自相矛盾，"
                f"消费者会按声明去调错的执行入口。"
            )

    # ③ 跨注规则必须能被 portfolio 真正执行（不能只是"声明了 cross"）
    if scopes.cross:
        try:
            from core.portfolio import Portfolio, judge_cross  # type: ignore
            from core.generate import sample_uniform  # type: ignore
            import random as _random

            _rng = _random.Random(20261011)
            _pf = Portfolio([sample_uniform(cfg, _rng) for _ in range(3)])
            _jr = judge_cross(cfg, _pf, scopes.cross)
            rep.ok(
                f"strategy[{game}]: 跨注规则 {[r.get('id') for r in scopes.cross]} "
                f"可在整组上下文执行（实测 3 注样本，求得特征 "
                f"{sorted(_jr.features)}）"
            )
        except Exception as e:  # noqa: BLE001
            rep.err(
                f"strategy[{game}]: 跨注规则声明为可执行，但实测失败 —— {e}。"
                f"跨注规则执行不了等于契约缺一层（1.0 的 R-002 正是此病）。"
            )

    n_s, n_c = len(scopes.single), len(scopes.cross)
    if n_s or n_c:
        rep.ok(
            f"strategy[{game}]: predicate 作用域 单注层 {n_s} 条 / "
            f"跨注层 {n_c} 条（可整组执行）"
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


# ---------------------------------------------------------------- versions

def validate_versions(repo_root: str | None = None,
                      rep: ValidationReport | None = None) -> ValidationReport:
    """版本一致性：文件内版本行 ↔ versions.json ↔ VERSION_INDEX.md。"""
    root = repo_root or _ROOT
    rep = rep if rep is not None else ValidationReport()

    try:
        from .versions import VersionsError, verify_versions
    except ImportError as e:  # pragma: no cover
        rep.warn(f"versions 模块不可用: {e}")
        return rep

    try:
        r = verify_versions(root)
    except VersionsError as e:
        rep.err(f"版本索引: {e}")
        return rep

    s = r["stats"]
    for e in r["errors"]:
        rep.err(f"版本: {e}")
    for w in r["warnings"]:
        rep.warn(f"版本: {w}")

    if not r["errors"]:
        by = s.get("by_level", {})
        rep.ok(
            f"版本索引: {s.get('total')} 条登记 "
            f"(A={by.get('A', 0)} B={by.get('B', 0)} "
            f"C={by.get('C', 0)} D={by.get('D', 0)})，"
            f"文件内版本行 {s.get('file_version_lines_ok')}/"
            f"{s.get('file_version_lines_needed')} 一致"
        )
        rep.ok(f"framework_version = {s.get('framework_version')}，"
               f"index_version = {s.get('index_version')}，"
               f"project_version = {s.get('project_version')}")

    # 顶层版本必须等于 pyproject 的 project.version（单一事实来源）
    _check_project_version(root, s.get("project_version"), rep)

    # versions.json 自身合规于 schema
    vp = os.path.join(root, "versions.json")
    if os.path.exists(vp):
        try:
            import json as _json
            with open(vp, encoding="utf-8") as f:
                _jsonschema_check(_json.load(f), "version_index.schema.json",
                                  "versions.json", rep)
        except Exception as e:  # noqa: BLE001
            rep.err(f"versions.json 读取失败: {e}")
    else:
        rep.err("versions.json 不存在")

    _check_consumes_freshness(root, rep)
    _check_consumes_completeness(root, rep)
    _check_summary_counts(root, rep)
    _check_readme_tree_versions(root, rep)
    return rep


def _check_project_version(root: str, declared: str | None, rep: "ValidationReport") -> None:
    """顶层 project_version 必须与 pyproject.toml 的 project.version 一致。

    避免『versions.json 写的 release 版本』和『实际打包的版本』漂移 ——
    这种漂移是最隐蔽的：两个数字都对，但彼此对不上。
    """
    import tomllib

    pp = os.path.join(root, "pyproject.toml")
    if not os.path.exists(pp):
        rep.warn("pyproject.toml 不存在，跳过 project_version 一致性检查")
        return
    try:
        with open(pp, "rb") as f:
            cfg = tomllib.load(f)
    except Exception as e:  # noqa: BLE001
        rep.warn(f"pyproject.toml 解析失败，跳过 project_version 一致性检查: {e}")
        return
    actual = (cfg.get("project") or {}).get("version")
    if not actual:
        rep.warn("pyproject.toml 无 project.version，跳过 project_version 一致性检查")
        return
    if declared is None:
        rep.err(f"versions.json 未声明 project_version，但 pyproject 的 project.version = {actual}")
        return
    if declared != actual:
        rep.err(f"顶层版本不一致: versions.json project_version={declared}，"
                f"pyproject project.version={actual}")
    else:
        rep.ok(f"project_version 一致（={declared}，源自 pyproject）")


def _load_superseded_facts(root: str) -> dict[str, str]:
    """返回 {被取代的 F-id: 取代它的 F-id}。

    只关心『已被推翻』的结论 —— 下游若仍引用且未更新，即为沉默。
    """
    out: dict[str, str] = {}
    p = os.path.join(root, "memory", "facts", "FACTS.jsonl")
    if not os.path.exists(p):
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:  # noqa: BLE001, S112
                continue
            if d.get("status") == "superseded":
                out[d.get("id", "")] = d.get("superseded_by") or "?"
    return out


def _check_consumes_freshness(root: str, rep: ValidationReport) -> None:
    """★ 下游新鲜度检查：引用了『已被推翻结论』的下游文档，是否同步更新过？

    背景（r03 真实案例）：r03 推翻了 F-0015（『1 亿封顶已触发』为误判），
    但 `STRATEGY_GUIDE.md`（给普通用户看的说明书）仍在传播该错误结论，
    而其 content_version 停在 1.0 —— **旧校验器只看版本号自洽，完全看不见**。

    判据（刻意保守，避免误报）：
        条目声明了 `consumes`（引用的 F-id 列表）；若其中任一 F-id
        在 FACTS.jsonl 里 `status == "superseded"` → 报 warning，
        提示「你引用的结论已被取代，请确认内容已同步并提升 content_version」。

    为什么用 warning 而非 error：引用 superseded 结论**未必**是错的
    （可能是『历史沿革』式的正当引用，如说明『早期误判已成过往』）。
    但**必须让人看见**，不能沉默。
    """
    vp = os.path.join(root, "versions.json")
    if not os.path.exists(vp):
        return
    try:
        with open(vp, encoding="utf-8") as f:
            vd = json.load(f)
    except Exception:  # noqa: BLE001
        return

    superseded = _load_superseded_facts(root)
    if not superseded:
        rep.ok("下游新鲜度: 无 superseded 结论，跳过")
        return

    n_declared = 0
    n_dirty = 0
    for e in vd.get("entries") or []:
        consumes = e.get("consumes")
        if not consumes:
            continue
        n_declared += 1
        path = e.get("path", "?")
        hits = sorted(set(consumes) & set(superseded))
        if not hits:
            continue
        mapping = ", ".join(f"{f}→{superseded[f]}" for f in hits)
        # 结构性声明：若条目明确标注为历史引用（正当沿革），则不告警，
        # 反而确认已同步 —— 把『warning 可忽略』升级为可机器核对的声明。
        if e.get("consumes_superseded") == "historical":
            rep.ok(
                f"下游新鲜度: {path} 声明为历史引用，已承认取代关系 [{mapping}]"
                f"（正当沿革，cv={e.get('content_version')}，不告警）"
            )
            continue
        n_dirty += 1
        rep.warn(
            f"下游新鲜度: {path} 引用了已被取代的结论 [{mapping}] "
            f"（cv={e.get('content_version')}, it={e.get('iteration')}）"
            f" —— 请确认内容已同步；若属『历史沿革』式正当引用，"
            f"请在 versions.json 该条目加 consumes_superseded: historical"
        )

    if n_dirty == 0:
        rep.ok(
            f"下游新鲜度: {n_declared} 个条目声明了 consumes，"
            f"引用 superseded 结论的均已同步（0 项沉默）"
        )


def _check_consumes_completeness(root: str, rep: ValidationReport) -> None:
    """★ 逆向新鲜度检查：正文引用了结论，但未登记 consumes —— 堵住人工登记遗漏。

    背景（r07 发现）：STRATEGY_GUIDE 正文引用了 F-0026~F-0029（r05 新增的投注方式/时间因素
    结论）与 F-0002，但 versions.json 的 consumes 声明停在 r04/r06 时代，从未登记它们。
    下游新鲜度检查（_check_consumes_freshness）是**单行道**——只查『声明了的结论是否被推翻』，
    看不见『正文引用了但没声明』。声明遗漏 = 永久盲区：这些结论一旦被推翻，
    引用它们的文档会静默过期而校验器全绿。

    判据：对声明了 consumes 的 .md 条目，扫描正文 F-xxxx 引用并与声明比对；
    正文引用未声明 → kind=strategy_guide / strategy 报 error（策略文档是高风险下游），
    其余报 warning。历史沿革式提及（上下文含『作废/已废除/已证伪/更正/取代/替代/历史』等词）
    豁免 —— 这类提及是陈述过往，不构成依赖，强行要求登记会造成永久噪音。
    """
    vp = os.path.join(root, "versions.json")
    if not os.path.exists(vp):
        return
    try:
        with open(vp, encoding="utf-8") as f:
            vd = json.load(f)
    except Exception:  # noqa: BLE001
        return
    pat = re.compile(r"F-\d{4}")
    honorific = ("作废", "已废除", "已证伪", "更正", "取代", "替代",
                 "superseded", "历史", "已废弃", "已推翻")
    n_checked = n_missing = 0
    for e in vd.get("entries", []):
        consumes = e.get("consumes")
        path = e.get("path", "")
        if not consumes or not path.endswith(".md"):
            continue
        p = os.path.join(root, path)
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except Exception:  # noqa: BLE001
            continue
        declared = set(consumes)
        n_checked += 1
        for m in pat.finditer(text):
            fid = m.group(0)
            if fid in declared:
                continue
            ctx = text[max(0, m.start() - 24):m.end() + 24]
            if any(k in ctx for k in honorific):
                continue  # 历史沿革式提及，非依赖
            n_missing += 1
            kind = e.get("kind", "")
            if kind in ("strategy_guide", "strategy"):
                rep.err(
                    f"下游声明完整性: {path} 正文引用了 {fid} 但未登记 consumes"
                    f"（kind={kind}）—— 该结论被推翻时此文档会静默过期；请补登记"
                )
            else:
                rep.warn(
                    f"下游声明完整性: {path} 正文引用了 {fid} 但未登记 consumes"
                    f"（kind={kind}）—— 若属依赖请补登记，若属历史沿革请在上下文标注"
                )
    if n_missing == 0:
        rep.ok(
            f"下游声明完整性: {n_checked} 个声明 consumes 的文档，"
            f"正文引用均已在声明内（0 项遗漏）"
        )


def _check_readme_tree_versions(root: str, rep: "ValidationReport") -> None:
    """★ 目录树手写版本标注 vs versions.json —— 堵住『目录树手写标注』盲区。

    背景：README 的 `## 目录结构` 代码块里，嵌套文件（含 / 的路径）手写了
    `vX.Y` 版本标注。此前这些标注没有任何校验，过期了也没人发现
    （r03 就漏过一次：目录树写 v1.0，实际已是 v1.1）。

    做法：用栈式解析目录树的连接线（├──/└──/│），重建每个条目的完整相对路径，
    把行内**紧跟在文件名后**的 `vX.Y` 与 versions.json 中该路径的 content_version 比对。

    只比对「含 / 的路径」（嵌套文件）；顶层文件已由文件头版本行机制覆盖。
    要点：同名嵌套 README.md（如 framework/README.md）的版本号写在箭头说明里，
    不是『文件名后紧跟 v』，本检查自然不会误匹配到顶层 README.md。
    未在 versions.json 登记的路径（如未登记的 README.md）跳过，不误报。
    """
    import json as _json
    import re as _re

    rp = os.path.join(root, "README.md")
    if not os.path.exists(rp):
        return

    # 版本索引的 by_path（只取有 content_version 的条目）
    by_path: dict[str, str] = {}
    vp = os.path.join(root, "versions.json")
    if os.path.exists(vp):
        try:
            with open(vp, encoding="utf-8") as f:
                vd = _json.load(f)
            for e in vd.get("entries") or []:
                p = e.get("path")
                cv = e.get("content_version")
                if p and cv:
                    by_path[p] = cv
        except Exception:  # noqa: BLE001
            pass

    # 定位代码块
    try:
        text = open(rp, encoding="utf-8").read()
    except Exception:  # noqa: BLE001
        return
    lines = text.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## 目录结构":
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "```":
                    start = j
                    break
            break
    if start is None:
        return
    end = None
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == "```":
            end = j
            break
    if end is None:
        return

    tree_chars = set("│├└─ ")
    stack: list[tuple[int, str]] = []  # (depth, path_prefix_with_slash_or_empty)
    checked = 0
    mismatches = 0
    for ln in lines[start + 1:end]:
        if not ln.strip():
            continue
        width = 0
        for ch in ln:
            if ch in tree_chars:
                width += 1
            else:
                break
        depth = width // 4
        content = ln[width:]
        m = _re.match(r"\S+", content)
        if not m:
            continue
        token = m.group(0)
        rest = content[m.end():]
        vm = _re.match(r"\s+v(\d+\.\d+)", rest)
        is_dir = token.endswith("/")
        name = token.rstrip("/")
        while stack and stack[-1][0] >= depth:
            stack.pop()
        parent = stack[-1][1] if stack else ""
        if is_dir:
            stack.append((depth, parent + name + "/"))
            continue
        cur = parent + name
        if "/" not in cur:
            continue  # 顶层文件，已由文件头版本行机制覆盖
        if vm is None:
            continue  # 该嵌套文件在树里没写版本标注，不强制
        declared = vm.group(1)
        actual = by_path.get(cur)
        if actual is None:
            continue  # 未在 versions.json 登记，无法比对，跳过
        checked += 1
        if declared != actual:
            mismatches += 1
            rep.err(
                f"目录树标注不一致: {cur} 树内写 v{declared}，"
                f"versions.json 为 v{actual}"
            )

    if mismatches == 0:
        suffix = "" if checked else "（树内嵌套文件均无版本标注，跳过）"
        rep.ok(
            f"目录树版本标注: {checked} 处嵌套文件标注均与 versions.json 一致{suffix}"
        )


# ★ 速览表计数一致性：手工维护的「N 条结论」必须等于 FACTS.jsonl 实际条数。
#
#   背景（r03 发现的第二类下游漏洞）：consumes 管得住「引用某条结论」，
#   却管不住「表格里写的结论**总数**」—— games/INDEX.md 写「15」、
#   AI_CONTEXT.md 写「FACTS.jsonl（15 条）」，而实盘已是 18 条，
#   两种情况下校验依然全绿。
#
#   判据：在这些「速览类」文件里，凡出现「N 条结论」字样，N 必须等于
#   台账实际条数（只统计 status != superseded 的活跃结论数 + 全部条数，
#   两个口径都接受，因为不同文档可能选用不同口径，但**数字必须真实存在**）。
_COUNT_LABEL_FILES = (
    "games/INDEX.md",
    "AI_CONTEXT.md",
    "README.md",
    "memory/INDEX.md",
)

_COUNT_PATTERNS = (
    re.compile(r"(?P<n>\d+)\s*条结论"),
    re.compile(r"FACTS\.jsonl[^）)]{0,8}?(?P<n>\d+)\s*条"),
)


def _check_summary_counts(root: str, rep: ValidationReport) -> None:
    """校验速览表里的「N 条结论」是否与台账实际条数一致。"""
    fp = os.path.join(root, "memory", "facts", "FACTS.jsonl")
    if not os.path.exists(fp):
        return
    total = 0
    active = 0
    seen_f0 = False
    with open(fp, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:  # noqa: BLE001, S112
                continue
            total += 1
            if d.get("id") == "F-0001":
                seen_f0 = True
            if d.get("status") != "superseded":
                active += 1
    if not seen_f0:
        return
    allowed = {total, active}

    checked = 0
    bad: list[str] = []
    for rel in _COUNT_LABEL_FILES:
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        for lineno, line in enumerate(open(p, encoding="utf-8"), 1):
            for pat in _COUNT_PATTERNS:
                for m in pat.finditer(line):
                    n = int(m.group("n"))
                    # 过滤明显非结论数的数字（如「2933 期」不会命中；「18 条结论」会）
                    if n < 1 or n > 500:
                        continue
                    checked += 1
                    if n not in allowed:
                        bad.append(f"{rel}:{lineno} 写「{n} 条结论」，台账实为 {total} 条")

    if bad:
        for b in bad:
            rep.err(f"速览计数: {b}")
    elif checked:
        rep.ok(f"速览计数: {checked} 处「N 条结论」与台账一致（台账 {total} 条）")


# ---------------------------------------------------------------- 概率口径标注（T-050 r10 根治）

_PROB_CALIBRATION_FILES = [
    "README.md",
    "AI_CONTEXT.md",
    "AGENTS.md",
    "docs/METHODOLOGY.md",
    "docs/CONSUMING.md",
    "docs/ARCHITECTURE.md",
    "cli/main.py",
    "framework/core/generate.py",
    "framework/core/judge.py",
    "framework/core/portfolio.py",
    "games/dlt/strategy/strategy.json",
]
_PROB_DIGITS = re.compile(r"(4\.66?7e-08|1\s*/\s*T|21,425,712|21425712)")
_PROB_QUALIFIER = re.compile(r"(一等奖|任一奖级|全奖级|各奖级|任意奖级|头奖)")
_PROB_BAD_PATTERN = re.compile(
    r"(中奖概率[^\n]{0,40}(?:4\.66?7e-08|1\s*/\s*T|21,425,712|21425712)"
    r"|(?:4\.66?7e-08|1\s*/\s*T|21,425,712|21425712)[^\n]{0,40}中奖概率)")


def _check_probability_calibration(root: str, rep: ValidationReport) -> None:
    """T-050：概率数字必须带奖级限定。

    检查对外产物中「中奖概率」与具体数字（1/T、4.667e-08、21,425,712）绑定出现、
    但附近 40 字符内无奖级限定词（一等奖/任一奖级/各奖级等）的表述。
    中奖概率是集合概念（任一奖级约 1/15），4.667e-08 仅指一等奖——两者不得混用。
    """
    bad: list[str] = []
    checked_files = 0
    for rel in _PROB_CALIBRATION_FILES:
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        checked_files += 1
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:  # noqa: BLE001, S112
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if not _PROB_DIGITS.search(line) or "中奖概率" not in line:
                continue
            m = _PROB_BAD_PATTERN.search(line)
            if m and not _PROB_QUALIFIER.search(line):
                bad.append(f"{rel}:{lineno} 「中奖概率」与具体数字绑定但缺奖级限定: {line.strip()[:80]}")
    if bad:
        for b in bad:
            rep.err(f"概率口径: {b}")
    else:
        rep.ok(f"概率口径: 检查 {checked_files} 个对外产物，无「中奖概率=具体数字」缺限定表述")


# ---------------------------------------------------------------- 开放问题一致性（Q 状态根治）

_QUESTION_ID_RE = re.compile(r"^##\s+(Q-\d{3})\s+—\s+(.+)$", re.M)
_QUESTION_STATUS_RE = re.compile(r"\|\s*\*\*状态\*\*\s*\|\s*([^|\n]+?)\s*\|")
_HEADER_ANSWERED_RE = re.compile(r"\*\*(\d+)\s*answered\*\*")


def _question_sections(txt: str) -> list[tuple[str, str, str]]:
    """解析 OPEN_QUESTIONS.md，返回 [(qid, status, title)]，status 归一化。"""
    out = []
    for m in _QUESTION_ID_RE.finditer(txt):
        qid, title = m.group(1), m.group(2)
        seg = txt[m.end(): m.end() + 2000]
        status = "unknown"
        sm = _QUESTION_STATUS_RE.search(seg)
        if sm:
            w = re.search(r"[A-Za-z]+", sm.group(1))
            if w:
                status = w.group(0).lower()
        out.append((qid, status, title))
    return out


def _check_open_questions_consistency(root: str, rep: ValidationReport) -> None:
    """★ Q 状态一致性：状态字段 ↔ 标题 ✅ ↔ 头部统计 ↔ 优先级总览。

    根治目标：Q 的 answered 标记需 4 处手动同步，漏一处即滞后
    （曾发生：Q-012/013/014 内容状态已 answered，但头部统计、标题 ✅、
    优先级总览未同步 → CLI 显示错误）。任一不一致 → error（FAIL）。
    """
    p = os.path.join(root, "memory", "workbench", "OPEN_QUESTIONS.md")
    if not os.path.exists(p):
        rep.err("开放问题一致性: OPEN_QUESTIONS.md 缺失")
        return
    txt = open(p, encoding="utf-8").read()

    qs = _question_sections(txt)
    if not qs:
        rep.err("开放问题一致性: 未解析到任何 Q-xxx 节")
        return

    qids = [qid for qid, _, _ in qs]
    status_of = {qid: st for qid, st, _ in qs}
    answered_ids = {qid for qid, st in status_of.items() if st == "answered"}

    problems: list[str] = []

    # 规则 0：Q 编号唯一（重复定义会掩盖滞后）
    if len(qids) != len(set(qids)):
        dup = sorted({q for q in qids if qids.count(q) > 1})
        problems.append(f"Q 编号重复定义 {dup}")

    # 规则 1：状态字段词合法
    for qid, st, _t in qs:
        if st not in ("answered", "open", "blocked"):
            problems.append(f"{qid} 状态字段无法解析（值 {st!r}）——应为 answered/open/blocked")

    # 规则 2：标题 ✅ 标记 ↔ 状态字段
    for m in _QUESTION_ID_RE.finditer(txt):
        qid, title = m.group(1), m.group(2)
        has_mark = "✅ answered" in title
        st = status_of.get(qid, "unknown")
        if st == "answered" and not has_mark:
            problems.append(f"{qid} 状态=answered 但标题缺『✅ answered』标记")
        elif st != "answered" and has_mark:
            problems.append(f"{qid} 标题含『✅ answered』但状态字段={st}")

    # 规则 3：头部 answered 计数 ↔ 实际
    hm = _HEADER_ANSWERED_RE.search(txt)
    if hm:
        declared = int(hm.group(1))
        if declared != len(answered_ids):
            problems.append(
                f"头部 answered 计数 {declared} ≠ 实际 {len(answered_ids)} "
                f"（{sorted(answered_ids)}）——头部统计未同步"
            )
    else:
        problems.append("头部缺少『N answered』统计行")

    # 规则 4：优先级总览 active 行（未 ~~ 划掉）不得含 answered 的 Q
    prio_start = txt.find("## 优先级总览")
    if prio_start >= 0:
        prio_txt = txt[prio_start:]
        for line in prio_txt.splitlines():
            if "|" not in line or "~~" in line:
                continue  # 跳过非表格行与已划掉（~~）行
            ids_in_line = set(re.findall(r"Q-\d{3}", line))
            overlap = ids_in_line & answered_ids
            if overlap:
                problems.append(
                    f"优先级总览 active 行仍列出已清偿问题 {sorted(overlap)}——应划掉（~~）"
                )
    else:
        problems.append("缺少『优先级总览』段")

    # 汇总
    if problems:
        for msg in problems:
            rep.err(f"开放问题一致性: {msg}")
    else:
        rep.ok(
            f"开放问题一致性: {len(qs)} 个 Q，状态字段/标题✅/头部统计/优先级表 4 处一致"
        )


# ---------------------------------------------------------------- 结构完整性（P1-2 根治）

# 受管目录：这些目录下的**每个**文件都必须登记进 versions.json。
# 排除（不要求登记）：数据（*/data/**，走 SHA256 清单）、夹具（tests/fixtures）、
# 模板（framework/protocol/templates）、运行残留（__pycache__/.git/.idea 等）。
_MANAGED_PREFIXES = (
    "",               # 根层文件
    "src/",
    "framework/core/",
    "framework/tools/",
    "framework/protocol/",
    "framework/methodology/",
    "spec/",
    "tools/",
    "cli/",
    "memory/",
    "tests/",
    "docs/",
    "games/dlt/",
)
_STRUCT_EXCLUDE_DIRS = {
    ".git", "__pycache__", ".idea", ".workbuddy", ".github",
    "data", "fixtures", "templates", "legacy_findings",
}
_STRUCT_EXCLUDE_FILES = {".gitignore"}


def _check_structure_completeness(root: str, rep: ValidationReport) -> None:
    """★ 双向登记完整性：受管目录实际文件 ↔ versions.json。

    根因（2026-10-11）：目录树是手写静态文本，校验只做一致性（标注 vs 索引），
    不做完整性（实际文件 vs 登记）——v2.0 新增 8 文件/目录全部漏登记/漏进树，
    validate 67 项全绿仍漏 13 处。

    本检查扫受管目录的**实际文件**，凡未登记进 versions.json 即报错；
    已登记但文件缺失由 validate_versions 的 missing_files 覆盖（不重复）。
    方向相反的两道闸合并，任何新增文件未登记 → validate 红字。
    """
    vp = os.path.join(root, "versions.json")
    if not os.path.exists(vp):
        return
    with open(vp, encoding="utf-8") as f:
        vd = json.load(f)
    registered = {e.get("path") for e in vd.get("entries") or []}

    unregistered: list[str] = []
    seen: set[str] = set()
    for pfx in _MANAGED_PREFIXES:
        base = os.path.join(root, pfx)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [
                d for d in dirnames
                if d not in _STRUCT_EXCLUDE_DIRS
            ]
            for fn in filenames:
                if fn in _STRUCT_EXCLUDE_FILES:
                    continue
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, root).replace("\\", "/")
                if rel not in registered and rel not in seen:
                    seen.add(rel)
                    unregistered.append(rel)

    if unregistered:
        shown = sorted(unregistered)[:8]
        more = f" 等 {len(unregistered)} 个" if len(unregistered) > 8 else ""
        rep.err(
            "结构完整性: 以下受管文件未登记进 versions.json（新增文件必须登记，"
            f"目录树才同步）：{', '.join(shown)}{more}"
        )
    else:
        rep.ok("结构完整性: 受管目录全部文件均已登记进 versions.json")


def _check_readme_tree_rendered(root: str, rep: ValidationReport) -> None:
    """★ README 目录树 = 派生物：必须与 render_tree(versions.json) 逐字一致。

    根因：目录树曾是手写文本，更新面不全导致整片遗漏。生成式后：
    任何手改 / 未跑 render_readme_tree --write → 本检查红字。
    """
    rp = os.path.join(root, "README.md")
    if not os.path.exists(rp):
        rep.err("README.md 缺失，无法核对目录树")
        return
    text = open(rp, encoding="utf-8").read()
    lines = text.split("\n")
    start = end = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## 目录结构":
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "```":
                    start = j
                    break
            break
    if start is None:
        rep.err("README 未找到「## 目录结构」区块")
        return
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == "```":
            end = j
            break
    if end is None:
        rep.err("目录结构代码块未闭合")
        return

    try:
        vd = load_versions(root)
        expected = render_tree(vd["entries"]).strip()
    except Exception as e:  # noqa: BLE001
        rep.err(f"目录树渲染失败: {e}")
        return
    actual = "\n".join(lines[start + 1:end]).strip()
    if actual == expected:
        rep.ok("目录树: 为派生物且与 versions.json 一致（render_readme_tree --write 生成）")
    else:
        rep.err(
            "目录树: 与 versions.json 派生物不一致——请运行 "
            "`python tools/render_readme_tree.py --write` 重新生成，勿手改"
        )


# ---------------------------------------------------------------- 全局升级（r06 批量实施）

# P2 —— AI 入口完整性锚表（AI_CONTEXT 必须包含的静态锚点）
_AI_ENTRY_STATIC_ANCHORS = [
    ("AI_CONTEXT.md", "expected_bonus_given_win", "唯一可优化量（红线 3）"),
    ("AI_CONTEXT.md", "21,425,712", "单注组合总数（§3）"),
    ("AI_CONTEXT.md", "4.667289469773513e-08", "一等奖概率（§3）"),
    ("AI_CONTEXT.md", "三条红线", "红线章节（§1）"),
    ("AI_CONTEXT.md", "judge_portfolio", "跨注层入口（§8）"),
    ("AI_CONTEXT.md", "LESSONS.md", "方法论纪律入口（§4）"),
    ("AI_CONTEXT.md", "五个版本号并存", "版本意识（头部）"),
    ("AI_CONTEXT.md", "caveats", "结论减损项纪律（§6）"),
]


def _check_ai_entry_completeness(root: str, rep: ValidationReport) -> None:
    """★ P2：AI 入口完整性 —— 关键问题锚点必须存在于入口文档。

    依据：DocAgent（ACL 2025）文档质量按 Completeness/Helpfulness/Truthfulness
    可测；Wright 禁止自欺 —— 入口与实现脱节是系统自欺，应被校验拦截。
    设计：静态锚表 + 动态锚（从 strategy/game.yaml 读当前值，对照入口文档，
    防"实现变了文档没改"）。
    """
    cp = os.path.join(root, "AI_CONTEXT.md")
    if not os.path.exists(cp):
        rep.err("AI 入口完整性: AI_CONTEXT.md 缺失（P2 检查无法执行）")
        return
    ctx = open(cp, encoding="utf-8").read()

    anchors: list[tuple[str, str]] = [  # (text, label)
        (txt, label) for _f, txt, label in _AI_ENTRY_STATIC_ANCHORS
    ]
    # 动态锚：strategy 的唯一可优化量（彩种目录动态发现，不硬编码）
    gd = os.path.join(root, "games")
    first_game = None
    if os.path.isdir(gd):
        for _n in sorted(os.listdir(gd)):
            if os.path.isfile(os.path.join(gd, _n, "game.yaml")):
                first_game = _n
                break
    if first_game:
        sp = os.path.join(root, "games", first_game, "strategy", "strategy.json")
        if os.path.exists(sp):
            try:
                with open(sp, encoding="utf-8") as f:
                    st = json.load(f)
                bd = st.get("boundary") or {}
                target = bd.get("optimizable_target")
                if target:
                    anchors.append((target, "strategy.boundary.optimizable_target（动态）"))
            except Exception:  # noqa: BLE001
                pass
        # 动态锚：game.yaml 的数据版本字面量
        gp = os.path.join(root, "games", first_game, "game.yaml")
        if os.path.exists(gp):
            try:
                gtxt = open(gp, encoding="utf-8").read()
                for dv in re.findall(r"[a-z]{2,4}_full_\d{3,4}", gtxt):
                    anchors.append((dv, "game.yaml 数据版本（动态）"))
            except Exception:  # noqa: BLE001
                pass

    missing = [(t, label) for t, label in anchors if t not in ctx]
    if missing:
        for t, label in missing[:8]:
            rep.err(
                f"AI 入口完整性: AI_CONTEXT.md 缺少关键锚 `{t}`"
                f"（{label}）—— 入口与实现脱节，须同步后重渲染"
            )
    else:
        rep.ok(
            f"AI 入口完整性: {len(anchors)} 个关键锚（含 {len(anchors) - 8} 个动态锚）"
            f"全部存在于 AI_CONTEXT.md"
        )


def _check_ai_map_rendered(root: str, rep: ValidationReport) -> None:
    """★ P1：AI_MAP.md = 派生物，必须与 render_ai_map(versions.json) 逐字一致。"""
    rp = os.path.join(root, "AI_MAP.md")
    if not os.path.exists(rp):
        rep.err("AI_MAP.md 缺失——运行 `python tools/render_ai_map.py --write`")
        return
    try:
        from .ai_map import load_versions as av_load, render_ai_map
        expected = render_ai_map(av_load(root)["entries"], root).strip()
    except Exception as e:  # noqa: BLE001
        rep.err(f"AI_MAP 渲染失败: {e}")
        return
    actual = open(rp, encoding="utf-8").read().strip()
    if actual == expected:
        rep.ok("AI_MAP: 为派生物且与 versions.json 一致（render_ai_map --write 生成）")
    else:
        rep.err(
            "AI_MAP: 与 versions.json 派生物不一致——请运行 "
            "`python tools/render_ai_map.py --write` 重新生成，勿手改"
        )


def _check_handoff_structure(root: str, rep: ValidationReport) -> None:
    """★ H：HANDOFF 模板化 —— 已收尾轮（有 manifest.json）必须含结构化交接。

    依据：Anthropic Effective Harnesses —— 为下一会话留下 clear artifacts；
    DOLPHIN —— 反馈闭环需要结构化的交接物。
    """
    it_dir = os.path.join(root, "games")
    if not os.path.isdir(it_dir):
        return
    it_dirs: list[str] = []
    for g in sorted(os.listdir(it_dir)):
        d = os.path.join(it_dir, g, "iterations")
        if os.path.isdir(d):
            it_dirs.append(d)
    checked = 0
    for d in it_dirs:
        for name in sorted(os.listdir(d)):
            mf = os.path.join(d, name, "manifest.json")
            if not os.path.isfile(mf):
                continue  # 未收尾轮（当前轮）跳过
            checked += 1
            hp = os.path.join(d, name, "HANDOFF.md")
            if not os.path.exists(hp):
                rep.err(f"HANDOFF 模板: {name} 有 manifest.json 但缺 HANDOFF.md（收尾不完整）")
                continue
            text = open(hp, encoding="utf-8").read()
            n_h2 = sum(1 for ln in text.split("\n") if ln.startswith("## "))
            keywords = ("结论", "遗留", "未决", "下轮", "建议", "风险")
            hits = [k for k in keywords if k in text]
            if n_h2 < 4 or len(hits) < 3:
                rep.err(
                    f"HANDOFF 模板: {name} 未结构化（{n_h2} 个 ## 段，命中 {len(hits)}/6 关键词）"
                    f"—— 应含结论/遗留/下轮建议等固定段，供下轮 AI 直接解析"
                )
    if checked:
        rep.ok(f"HANDOFF 模板: {checked} 个已收尾轮 HANDOFF 均结构化")


def _check_compression_freshness(root: str, rep: ValidationReport) -> None:
    """★ I：记忆压缩到期提醒 —— 距上次压缩超过 5 轮 → warning。

    依据：战略遗忘（IterResearch/MEM1）、SAGE（Ebbinghaus 遗忘曲线）——
    记忆膨胀降信噪比，到期不压缩必须被看见。
    """
    ap = os.path.join(root, "memory", "facts", "ACTIVE.md")
    if not os.path.exists(ap):
        return
    text = open(ap, encoding="utf-8").read()
    m = re.search(r"当前轮 round(\d{2})", text)
    if not m:
        return
    compressed_round = int(m.group(1))
    cur = current_iteration_round(root)
    gap = cur - compressed_round
    if gap > 5:
        rep.warn(
            f"记忆压缩: 距上次压缩已 {gap} 轮（round{compressed_round:02d} → round{cur:02d}）"
            f"—— 运行 `python framework/tools/compress_memory.py --write`"
        )
    else:
        rep.ok(f"记忆压缩: 距上次压缩 {gap} 轮（≤5，正常）")


def _check_flywheel_health(root: str, rep: ValidationReport) -> None:
    """★ K：飞轮仪表盘 = 派生物，与 collect_metrics 渲染结果一致。"""
    rp = os.path.join(root, "FLYWHEEL_HEALTH.md")
    if not os.path.exists(rp):
        rep.err("FLYWHEEL_HEALTH.md 缺失——运行 `python tools/render_flywheel_health.py --write`")
        return
    try:
        from .flywheel import collect_metrics, render_health
        expected = render_health(collect_metrics(root), root=root).strip()
    except Exception as e:  # noqa: BLE001
        rep.err(f"FLYWHEEL_HEALTH 渲染失败: {e}")
        return
    actual = open(rp, encoding="utf-8").read().strip()
    if actual == expected:
        rep.ok("FLYWHEEL_HEALTH: 为派生物且与 FACTS 台账一致")
    else:
        rep.err(
            "FLYWHEEL_HEALTH: 与台账派生物不一致——请运行 "
            "`python tools/render_flywheel_health.py --write` 重新生成"
        )


def _check_calibration(root: str, rep: ValidationReport) -> None:
    """★ D1：置信度校准 —— 高置信度（4-5★）推翻率高于低置信度（1-2★）→ warning。

    依据：confidence calibration；AIDE²（reward hacking 55%→32% 可测）——
    置信度与存活率系统性失配 = 置信度虚高，须被看见。样本 <3 跳过（避免误报）。
    """
    try:
        from .flywheel import collect_metrics
        m = collect_metrics(root)
    except Exception as e:  # noqa: BLE001
        rep.warn(f"置信度校准: 统计失败（{e}）")
        return
    hi = sum(c["dead"] for c, c2 in m["by_confidence"].items() for c2 in ())
    bc = m["by_confidence"]
    hi_t = sum(cell["total"] for c, cell in bc.items() if c >= 4)
    lo_t = sum(cell["total"] for c, cell in bc.items() if c <= 2)
    if hi_t < 3 or lo_t < 3:
        rep.ok(f"置信度校准: 高{hi_t}/低{lo_t} 置信度样本不足（<3），不做失配判定")
        return
    hi_d = sum(cell["dead"] for c, cell in bc.items() if c >= 4)
    lo_d = sum(cell["dead"] for c, cell in bc.items() if c <= 2)
    hi_r, lo_r = hi_d / hi_t, lo_d / lo_t
    if hi_r > lo_r:
        rep.warn(
            f"置信度校准: 高置信度（4-5★）推翻率 {hi_r:.0%} > 低置信度（1-2★）{lo_r:.0%}"
            f"—— 置信度可能系统性虚高；运行 `python tools/report_calibration.py` 查看分层"
        )
    else:
        rep.ok(
            f"置信度校准: 高置信度推翻率 {hi_r:.0%} ≤ 低置信度 {lo_r:.0%}（匹配）"
        )


def _check_dependency_map(root: str, rep: ValidationReport) -> None:
    """★ C：DEPENDENCY_MAP = 派生物，与显式引用关系渲染结果一致。"""
    rp = os.path.join(root, "DEPENDENCY_MAP.md")
    if not os.path.exists(rp):
        rep.err("DEPENDENCY_MAP.md 缺失——运行 `python tools/render_dependency_map.py --write`")
        return
    try:
        from .depmap import render_dependency_map
        expected = render_dependency_map(root).strip()
    except Exception as e:  # noqa: BLE001
        rep.err(f"DEPENDENCY_MAP 渲染失败: {e}")
        return
    actual = open(rp, encoding="utf-8").read().strip()
    if actual == expected:
        rep.ok("DEPENDENCY_MAP: 为派生物且与显式引用一致")
    else:
        rep.err(
            "DEPENDENCY_MAP: 与引用关系派生物不一致——请运行 "
            "`python tools/render_dependency_map.py --write` 重新生成"
        )


def _check_critical_numbers(root: str, rep: ValidationReport) -> None:
    """★ C2：关键数字跨文件一致 —— 解析事实（组合数/一等奖概率）必须在
    台账与速览文档中一致出现。

    依据：tests/README「结论数字与 game.yaml 重算结果一致」暂缓项 ——
    4.667e-08 出现在 FACTS/文档多处，一处改错现有校验不报警。
    """
    fp = os.path.join(root, "memory", "facts", "FACTS.jsonl")
    if not os.path.exists(fp):
        return
    claim = ""
    with open(fp, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if d.get("id") == "F-0001" and d.get("status") != "superseded":
                claim = d.get("claim") or ""
                break
    if not claim:
        return
    m_int = re.search(r"\d{1,3}(?:,\d{3})+", claim)      # 21,425,712
    m_float = re.search(r"\d\.\d+e-\d+", claim)           # 4.667289469773513e-08
    numbers = [m.group(0) for m in (m_int, m_float) if m]
    if not numbers:
        rep.ok("关键数字: F-0001 无可提取的解析数字，跳过")
        return
    bad: list[str] = []
    for rel in ("AI_CONTEXT.md", "README.md"):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        text = open(p, encoding="utf-8").read()
        for n in numbers:
            if n not in text:
                bad.append(f"{rel} 缺少 `{n}`（F-0001 有）")
    if bad:
        for b in bad:
            rep.err(f"关键数字一致性: {b}")
    else:
        rep.ok(f"关键数字一致性: F-0001 的 {len(numbers)} 个解析数字"
               f"在 AI_CONTEXT/README 一致出现")


def validate_incremental(root: str | None = None) -> ValidationReport:
    """★ F：增量校验 —— 只跑结构与派生物检查（新增文件场景最快路径）。

    依据：IncrConsist —— 原子操作 + 分层不变量，校验范围收敛到受编辑邻域；
    规模增长后全量 validate 不再是每步必跑项。
    """
    root = root or _ROOT
    rep = ValidationReport()
    _check_structure_completeness(root, rep)
    _check_readme_tree_rendered(root, rep)
    _check_ai_map_rendered(root, rep)
    _check_flywheel_health(root, rep)
    _check_dependency_map(root, rep)
    validate_versions(root, rep)
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

    # 版本索引一致性
    validate_versions(root, rep)

    # 结构完整性（P1-2 根治）：受管文件双向登记 + README 目录树为派生物
    _check_structure_completeness(root, rep)
    _check_readme_tree_rendered(root, rep)

    # 全局升级 r06 新增（P0-P4 批次落地后的机械护栏）
    _check_ai_map_rendered(root, rep)           # P1 机器地图派生物
    _check_ai_entry_completeness(root, rep)     # P2 入口完整性
    _check_handoff_structure(root, rep)         # H 交接模板化
    _check_compression_freshness(root, rep)     # I 压缩到期
    _check_flywheel_health(root, rep)           # K 飞轮仪表盘
    _check_calibration(root, rep)               # D1 置信度校准
    _check_dependency_map(root, rep)            # C 依赖图
    _check_critical_numbers(root, rep)          # C2 关键数字一致性
    _check_open_questions_consistency(root, rep)  # Q 状态一致性（4 处手动同步根治）
    _check_probability_calibration(root, rep)   # T-050 概率口径标注（r10）

    # 协议文档存在性（软检查）
    docs = [
        "AI_CONTEXT.md",
        "VERSION_INDEX.md",
        "versions.json",
        "memory/lessons/LESSONS.md",
        "memory/INDEX.md",
        "docs/VERSIONING_DOCS.md",
        "framework/protocol/ITERATION_PROTOCOL.md",
        "framework/protocol/MEMORY_PROTOCOL.md",
        "framework/methodology/MATH_BOUNDARY.md",
        "framework/methodology/STATISTICAL_DISCIPLINE.md",
        "spec/README.md",
        "spec/VERSIONING.md",
        "spec/version_index.schema.json",
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
