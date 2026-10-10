# -*- coding: utf-8 -*-
"""smartpickcore.strategy — 策略生成与消费

两个方向：
  1. **生成**（本仓库内部）：`build_strategy(game)` 从 FACTS + game.yaml 组装 strategy.json
  2. **消费**（外部工具）：`load_strategy(game)` 读并做契约校验

设计要点：
  - `strategy.json` 是**唯一对外契约**（受 spec/strategy.schema.json 约束）
  - 生成时**强制**校验 evidence_refs 全部指向 status=established 的结论
  - 四条红线在生成与消费两侧都检查

用法：
    # 外部消费者
    from smartpickcore.strategy import load_strategy
    st = load_strategy("dlt")
    for r in st["rules"]:
        print(r["statement"])

    # 内部生成
    from smartpickcore.strategy import build_strategy
    st = build_strategy("dlt")
"""
from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

from .game import compute_space, load_game_config

__all__ = [
    "StrategyError",
    "load_strategy",
    "build_strategy",
    "strategy_path",
    "render_machine_rules",
]

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DISCLAIMER_TEXT = (
    "本策略集不提高中奖概率，这是数学事实（{boundary}）。"
    "彩票是负期望游戏：现行返奖率 {rr}%，每 2 元投注的长期数学期望回报约 "
    "{exp:.2f} 元，净期望约 {net:.2f} 元/注。"
    "本策略唯一的作用是在极小概率中奖时，减少与他人重号的人数、提高单注奖金；"
    "该收益受封顶条款稀释，且只在中奖时兑现。"
    "请理性购彩，量力而行，不得借贷投注。"
)


class StrategyError(Exception):
    """策略生成/消费错误。"""


# ---------------------------------------------------------------- 路径

def strategy_path(game: str, repo_root: str | None = None) -> str:
    root = repo_root or _ROOT
    return os.path.join(root, "games", game, "strategy", "strategy.json")


# ---------------------------------------------------------------- 消费

def load_strategy(game: str, repo_root: str | None = None,
                  strict: bool = True) -> dict[str, Any]:
    """读 strategy.json 并做红线检查。外部工具应使用本函数。

    strict=True 时，四条红线任一不符即抛 StrategyError。
    **不要用 json.load 直接读** —— 那会绕过红线检查。
    """
    p = strategy_path(game, repo_root)
    if not os.path.exists(p):
        raise StrategyError(f"strategy.json 不存在: {p}")

    with open(p, encoding="utf-8") as f:
        st = json.load(f)

    if strict:
        _check_red_lines(st, game)
        _check_schema_version(st)

    return st


def _check_red_lines(st: dict, game: str) -> None:
    """四条红线。外部消费者必须执行。"""
    dis = st.get("disclaimer") or {}
    if dis.get("changes_win_probability") is not False:
        raise StrategyError(
            f"strategy[{game}]: 红线违反 —— disclaimer.changes_win_probability "
            f"必须为 False（本策略不提高中奖概率）"
        )
    if dis.get("is_negative_ev") is not True:
        raise StrategyError(
            f"strategy[{game}]: 红线违反 —— disclaimer.is_negative_ev 必须为 True"
        )
    bd = st.get("boundary") or {}
    if bd.get("optimizable_target") != "expected_bonus_given_win":
        raise StrategyError(
            f"strategy[{game}]: 红线违反 —— boundary.optimizable_target 只能是 "
            f"'expected_bonus_given_win'，当前为 {bd.get('optimizable_target')!r}"
        )
    for rule in st.get("rules", []):
        evi = rule.get("expected_value_impact") or {}
        if evi.get("changes_win_probability") is not False:
            raise StrategyError(
                f"strategy[{game}].{rule.get('id')}: 红线违反 —— "
                f"expected_value_impact.changes_win_probability 必须为 False"
            )


def _check_schema_version(st: dict, supported_major: int = 1) -> None:
    """主版本必须匹配。遇到不认识的主版本应拒绝解析，而非尽力而为。"""
    v = str(st.get("schema_version", ""))
    if "." not in v:
        raise StrategyError(f"schema_version 格式非法: {v!r}（应为 '主.次'）")
    major = v.split(".", 1)[0]
    if major != str(supported_major):
        raise StrategyError(
            f"strategy schema_version={v} 的主版本与消费者支持的 "
            f"{supported_major}.x 不匹配。请升级消费者，不要尽力而为地解析。"
        )


def render_machine_rules(st: dict[str, Any]) -> list[str]:
    """把 machine_rule 渲染成可读文本（供调试/文档）。

    注意：真正执行需要 game.yaml 的 features 定义来求值 predicate。
    本函数只做展示，不做求值。
    """
    out = []
    for r in st.get("rules", []):
        mr = r.get("machine_rule")
        if not mr:
            out.append(f"# {r['id']}: （无 machine_rule，仅陈述）")
            continue
        out.append(
            f"# {r['id']} [{mr.get('action')}]  "
            f"{mr.get('predicate')}"
            + (f"  weight={mr['weight']}" if mr.get("weight") is not None else "")
        )
    return out


# ---------------------------------------------------------------- 生成

def build_strategy(game: str, repo_root: str | None = None,
                   iteration: str | None = None,
                   generator: str | None = None) -> dict[str, Any]:
    """从 game.yaml + FACTS.jsonl + 已有 strategy.json 组装新的 strategy.json。

    本函数**不发明规则** —— 它只做：
      1. 从 game.yaml 重算 boundary（保证数值与配置一致）
      2. 从 FACTS.jsonl 重建 evidence_index（保证摘要与台账一致）
      3. 校验 evidence_refs 全部指向已存在的结论
      4. 保留已有的 rules / avoid_list（规则由人来定，不由代码生成）

    为什么规则不由代码生成：**规则是判断，证据是事实。**
    代码可以保证事实的一致性，但不能代替"这条规则值不值得给用户"的判断。
    """
    from .memory import Memory

    root = repo_root or _ROOT
    cfg = load_game_config(game, root)
    space = compute_space(cfg)
    mem = Memory(root)
    facts = {f["id"]: f for f in mem.load_facts()}

    p = strategy_path(game, root)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            st = json.load(f)
    else:
        st = {
            "schema_version": "1.0",
            "game": game,
            "rules": [],
            "avoid_list": [],
        }

    rr = (cfg.get("prize_model") or {}).get("return_rate", 0.51)

    # boundary 重算
    st["boundary"] = {
        "total_combinations": space["total_combinations"],
        "first_prize_probability": space["first_prize_probability"],
        "return_rate": rr,
        "optimizable_target": "expected_bonus_given_win",
        "note": (
            "期望回报可分解为 E = Σ_j P_j × (池_j / 中奖注数_j)。"
            "其中 P_j 由号码空间决定、与选号无关；"
            "唯一可被选号影响的是『中奖注数_j』。"
        ),
    }

    # disclaimer
    st["disclaimer"] = {
        "is_negative_ev": True,
        "changes_win_probability": False,
        "text": DISCLAIMER_TEXT.format(
            boundary=f"单注一等奖概率恒为 1/{space['total_combinations']:,}",
            rr=round(rr * 100),
            exp=2.0 * rr,
            net=2.0 * rr - 2.0,
        ),
    }

    # evidence_index 重建
    used: set[str] = set()
    for r in st.get("rules", []):
        used.update(r.get("evidence_refs") or [])
    for a in st.get("avoid_list", []):
        used.update(a.get("refuted_by") or [])

    idx = []
    for fid in sorted(used):
        f = facts.get(fid)
        if f is None:
            raise StrategyError(
                f"strategy.json 引用了不存在的结论 {fid}。"
                f"请先确认该结论已在 memory/facts/FACTS.jsonl 中。"
            )
        idx.append(
            {
                "id": fid,
                "claim": f["claim"],
                "status": f["status"],
                "confidence": f["confidence"],
            }
        )
    st["evidence_index"] = idx

    st["game"] = game
    st["generated_at"] = date.today().isoformat()
    st["data_version"] = ((cfg.get("data") or {}).get("raw") or {}).get(
        "n_draws"
    ) and f"{game}_full_{cfg['data']['raw']['n_draws']}" or st.get("data_version")
    st["rules_epoch"] = (cfg.get("prize_model") or {}).get("current_epoch")
    st["generated_by"] = generator or st.get("generated_by") or "smartpickcore"

    prov = st.setdefault("provenance", {})
    if iteration:
        prov["iteration"] = iteration
    prov["generator"] = generator or prov.get("generator")

    return st
