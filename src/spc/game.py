# -*- coding: utf-8 -*-
"""spc.game — 彩种配置装载与号码空间计算

**本模块不含任何具体彩种参数。** 一切从 games/<id>/game.yaml 读取。

核心职责：
  1. `load_game_config()` —— 读并做最小结构校验
  2. `compute_space()`     —— 由 machine.zones 算出单注组合总数 T 与一等奖概率
  3. `feature_keys()`      —— 列出可用的特征 key（供 machine_rule 的 predicate 引用）
"""
from __future__ import annotations

import os
from math import comb
from typing import Any

__all__ = [
    "GameConfigError",
    "load_game_config",
    "compute_space",
    "feature_keys",
    "list_games",
]

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class GameConfigError(Exception):
    """彩种配置错误。"""


# ---------------------------------------------------------------- 装载

def load_game_config(game: str, repo_root: str | None = None) -> dict[str, Any]:
    """读 games/<game>/game.yaml 并做最小校验。

    ⚠️ 本函数**不替代** schema 校验（见 validate.py）。
    它只做"能不能用"的结构检查，给出更易读的错误信息。
    """
    root = repo_root or _ROOT
    path = os.path.join(root, "games", game, "game.yaml")
    if not os.path.exists(path):
        raise GameConfigError(
            f"彩种配置不存在: {path}\n"
            f"  可用彩种: {list_games(root)}"
        )

    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise GameConfigError(
            "读取 game.yaml 需要 PyYAML。\n"
            "  安装: pip install pyyaml"
        ) from e

    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise GameConfigError(f"{path}: 顶层必须是映射")

    # 最小结构校验
    for key in ("id", "name", "machine", "features", "prize_model", "data"):
        if key not in cfg:
            raise GameConfigError(f"{path}: 缺少顶层字段 {key!r}")

    if cfg["id"] != game:
        raise GameConfigError(
            f"{path}: id={cfg['id']!r} 与目录名 {game!r} 不一致"
        )

    zones = cfg["machine"].get("zones")
    if not zones:
        raise GameConfigError(f"{path}: machine.zones 为空")

    for i, z in enumerate(zones):
        for k in ("key", "pool_size", "pick"):
            if k not in z:
                raise GameConfigError(f"{path}: machine.zones[{i}] 缺少 {k!r}")
        if z["pick"] > z["pool_size"]:
            raise GameConfigError(
                f"{path}: zones[{i}] ({z['key']}) pick={z['pick']} > pool_size={z['pool_size']}"
            )

    feats = cfg["features"]
    if not isinstance(feats, list) or not feats:
        raise GameConfigError(f"{path}: features 必须是非空列表")
    seen: set[str] = set()
    for i, ft in enumerate(feats):
        for k in ("key", "type", "formula"):
            if k not in ft:
                raise GameConfigError(f"{path}: features[{i}] 缺少 {k!r}")
        if ft["key"] in seen:
            raise GameConfigError(f"{path}: features[{i}] key {ft['key']!r} 重复")
        seen.add(ft["key"])

    pe = cfg["prize_model"]
    if "current_epoch" not in pe or "epochs" not in pe:
        raise GameConfigError(f"{path}: prize_model 缺少 current_epoch / epochs")
    ep_ids = [e.get("id") for e in pe["epochs"]]
    if pe["current_epoch"] not in ep_ids:
        raise GameConfigError(
            f"{path}: current_epoch={pe['current_epoch']!r} 不在 epochs {ep_ids} 中"
        )
    # 红线：奖金规则不影响号码分布
    for e in pe["epochs"]:
        if e.get("sum_affects_numbers") is not False:
            raise GameConfigError(
                f"{path}: epoch {e.get('id')} 的 sum_affects_numbers "
                f"必须为 False（红线：奖金规则变更不影响号码分布）"
            )

    return cfg


def list_games(repo_root: str | None = None) -> list[str]:
    """列出 games/ 下含 game.yaml 的彩种 id（排除 _template 与隐藏目录）。"""
    root = repo_root or _ROOT
    d = os.path.join(root, "games")
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if name.startswith("_") or name.startswith("."):
            continue
        if os.path.isfile(os.path.join(d, name, "game.yaml")):
            out.append(name)
    return out


# ---------------------------------------------------------------- 号码空间

def compute_space(cfg: dict[str, Any]) -> dict[str, Any]:
    """由 machine.zones 算出号码空间。

    返回：
        {
          "total_combinations": int,      # T = ∏ C(pool_size_i, pick_i)
          "first_prize_probability": float,   # 1 / T
          "zones": [{"key", "label", "pool_size", "pick", "sub_combinations"}, ...]
        }

    ⚠️ 这是**解析计算**，不是模拟。是"概率不可变"结论的分母来源。
    """
    zones_out = []
    total = 1
    for z in cfg["machine"]["zones"]:
        sub = comb(z["pool_size"], z["pick"])
        total *= sub
        zones_out.append(
            {
                "key": z["key"],
                "label": z.get("label", z["key"]),
                "pool_size": z["pool_size"],
                "pick": z["pick"],
                "sub_combinations": sub,
            }
        )
    if total <= 0:
        raise GameConfigError("号码空间计算结果非正，检查 machine.zones")
    return {
        "total_combinations": total,
        "first_prize_probability": 1.0 / total,
        "zones": zones_out,
    }


def feature_keys(cfg: dict[str, Any]) -> list[str]:
    """列出可用特征 key。strategy.json 的 machine_rule.predicate 只能引用这些。"""
    return [f["key"] for f in cfg["features"]]


def feature_map(cfg: dict[str, Any]) -> dict[str, dict]:
    """key → 特征定义。"""
    return {f["key"]: f for f in cfg["features"]}
