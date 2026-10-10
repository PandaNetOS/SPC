# -*- coding: utf-8 -*-
"""smartpickcore.core.game_util — 由 game.yaml 的 machine 段驱动的基础计算

**彩种无关**：不出现任何号码池常量、区名、特征名。
一切从传入的 cfg 读取。

与 `src/smartpickcore/game.py` 的区别：

| | `src/smartpickcore/game.py` | 本模块 |
|---|---|---|
| 职责 | **装载** `game.yaml` + 最小结构校验 + schema 校验入口 | **纯计算**：区定义解析、编号空间、特征声明解析 |
| 依赖 | 需要 PyYAML 读文件 | 只吃 dict，可用性更广 |
| 位置 | 库层（面向消费方） | 框架层（面向框架内部与其他彩种接入） |

依赖方向：`src/` → `framework/core/`，不可逆。
"""
from __future__ import annotations

from math import comb
from typing import Any

from .features import PrimitiveError, arity_of, list_primitives

__all__ = [
    "GameUtilError",
    "zones_of",
    "zone_by_key",
    "zone_keys",
    "max_value_of_zone",
    "total_combinations",
    "first_prize_probability",
    "declared_features",
    "feature_by_key",
    "feature_keys",
    "validate_feature_declarations",
]


class GameUtilError(Exception):
    """配置结构不满足框架要求。"""


# ---------------------------------------------------------------- 区（zone）

def zones_of(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """取 machine.zones（原样返回，不做默认填充）。"""
    try:
        zones = cfg["machine"]["zones"]
    except (KeyError, TypeError) as e:
        raise GameUtilError("配置缺少 machine.zones") from e
    if not isinstance(zones, list) or not zones:
        raise GameUtilError("machine.zones 必须是非空列表")
    return zones


def zone_keys(cfg: dict[str, Any]) -> list[str]:
    """全部区名，按配置顺序（如 ['front', 'back']）。"""
    return [z["key"] for z in zones_of(cfg)]


def zone_by_key(cfg: dict[str, Any], key: str) -> dict[str, Any]:
    """按 key 取区定义。不存在时报错并列出可用区。"""
    for z in zones_of(cfg):
        if z.get("key") == key:
            return z
    raise GameUtilError(
        f"区 {key!r} 不存在。可用区：{', '.join(zone_keys(cfg))}"
    )


def max_value_of_zone(cfg: dict[str, Any], key: str) -> int:
    """某区的最大号 = min_value + pool_size - 1。

    ⚠️ 这是从配置算出来的，**不是硬编码的 35 / 12**。
    """
    z = zone_by_key(cfg, key)
    mv = z.get("min_value", 1)
    if not isinstance(mv, int):
        raise GameUtilError(f"zone {key!r} 的 min_value 必须是整数")
    return mv + int(z["pool_size"]) - 1


# ---------------------------------------------------------------- 号码空间

def total_combinations(cfg: dict[str, Any]) -> int:
    """单注组合总数 T = ∏ C(pool_size_i, pick_i)。解析计算，非模拟。"""
    total = 1
    for z in zones_of(cfg):
        total *= comb(int(z["pool_size"]), int(z["pick"]))
    return total


def first_prize_probability(cfg: dict[str, Any]) -> float:
    """一等奖概率 = 1 / T。"""
    t = total_combinations(cfg)
    if t <= 0:
        raise GameUtilError("组合总数为非正，检查 machine.zones")
    return 1.0 / t


# ---------------------------------------------------------------- 特征声明

def declared_features(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """取 features[] 声明（原样）。"""
    feats = cfg.get("features")
    if not isinstance(feats, list) or not feats:
        raise GameUtilError("features 必须是非空列表")
    return feats


def feature_by_key(cfg: dict[str, Any], key: str) -> dict[str, Any]:
    for f in declared_features(cfg):
        if f.get("key") == key:
            return f
    raise GameUtilError(
        f"特征 {key!r} 未在 game.yaml 声明。已声明："
        f"{', '.join(feature_keys(cfg))}"
    )


def feature_keys(cfg: dict[str, Any]) -> list[str]:
    return [f["key"] for f in declared_features(cfg)]


def validate_feature_declarations(cfg: dict[str, Any]) -> list[str]:
    """静态检查 features[] 的声明是否可被框架执行。

    检查项：
      · key 唯一且非空
      · 每个特征要么给 `primitive`（新格式，可执行），要么给 `formula`（旧格式，仅注释）
      · `primitive` 必须在 features.PRIMITIVES 里存在
      · `primitive` 的必需参数必须齐备
      · `args.zone`（若有）必须在 machine.zones 的区名里
      · feature 的 `type` 若是 boolean，primitive 必须返回布尔（无法静态判定时只警告）

    返回错误信息列表（空表示通过）。
    """
    errs: list[str] = []
    known_zones = set(zone_keys(cfg))
    seen: set[str] = set()

    for i, f in enumerate(declared_features(cfg)):
        where = f"features[{i}]"
        key = f.get("key")
        if not key or not isinstance(key, str):
            errs.append(f"{where}: key 缺失或非字符串")
            continue
        where = f"features[{i}] ({key})"
        if key in seen:
            errs.append(f"{where}: key 重复")
        seen.add(key)

        prim = f.get("primitive")
        if prim is None:
            # 旧格式：只有 formula（人类注释）。允许存在，但标记为不可执行。
            if not f.get("formula"):
                errs.append(
                    f"{where}: 既没有 primitive（可执行）也没有 formula（注释）。"
                    f"要么给 primitive 使其可被框架求值，要么给 formula 作为人类可读说明。"
                )
            continue

        if not isinstance(prim, str):
            errs.append(f"{where}: primitive 必须是字符串")
            continue
        try:
            need = arity_of(prim)
        except PrimitiveError as e:
            errs.append(f"{where}: {e}")
            continue

        args = f.get("args") or {}
        if not isinstance(args, dict):
            errs.append(f"{where}: args 必须是映射")
            continue

        for req in need:
            if req not in args:
                errs.append(
                    f"{where}: 原语 {prim!r} 需要参数 {req!r}，"
                    f"args 里没有（当前 args={args}）"
                )

        zk = args.get("zone")
        if zk is not None:
            if zk not in known_zones:
                errs.append(
                    f"{where}: args.zone={zk!r} 不是已声明的区。"
                    f"可用区：{', '.join(sorted(known_zones))}"
                )

        extra = set(args) - set(need) - {"zone"}
        if extra:
            errs.append(
                f"{where}: args 含未使用参数 {sorted(extra)}"
                f"（原语 {prim!r} 只接受 {list(need)} + zone）"
            )

    if not seen and not errs:
        errs.append("features[] 为空，框架至少要有一个可求值的特征")
    return errs
