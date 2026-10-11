# -*- coding: utf-8 -*-
"""spc.core.evaluate — 按声明机械求值一注号码的特征

**纯机械，无判断。** 本模块不知道哪个特征"重要"，也不判断"哪条结论对"。
它只做一件事：读 `cfg['features']` 的声明，对一注号码求出每个特征的**值**。

```
game.yaml features[] 声明          本模块
─────────────────────────          ─────────────────────
- key: front_sum                    evaluate(cfg, ticket) →
  primitive: sum                      {"front_sum": 135,
  args: {zone: front}                  "has_run_ge2": False, ...}
```
"""
from __future__ import annotations

from typing import Any

from .features import PrimitiveError, apply_primitive, resolve_primitive
from .game_util import (
    GameUtilError,
    declared_features,
    declared_single_features,
    validate_feature_declarations,
    zone_keys,
)
from .ticket import Ticket

__all__ = ["EvaluateError", "evaluate", "evaluate_one", "evaluable_features"]


class EvaluateError(Exception):
    """特征求值失败。"""


def evaluable_features(cfg: dict[str, Any]) -> list[str]:
    """列出**可执行**的**单注**特征 key（声明了 primitive 且 scope != cross）。

    两类特征被排除：
      · 只有 `formula` 的旧格式特征 —— 它们是人类注释
      · `scope: cross` 的跨注特征 —— 它们需要一组注，走 `evaluate_cross()`

    ★ 2.1 起必须排除 cross：否则 `evaluate()` 会把跨注原语喂进单注求值，
    得到"毫无意义却可能不报错"的结果。
    """
    out = []
    for f in declared_single_features(cfg):
        if f.get("primitive"):
            out.append(f["key"])
    return out


def evaluate_one(cfg: dict[str, Any], ticket: Ticket, key: str) -> Any:
    """求单个特征。特征未声明或不可执行时报错。"""
    decl = None
    for f in declared_features(cfg):
        if f.get("key") == key:
            decl = f
            break
    if decl is None:
        raise EvaluateError(
            f"特征 {key!r} 未声明。可求值特征：{', '.join(evaluable_features(cfg))}"
        )
    if decl.get("scope") == "cross":
        raise EvaluateError(
            f"特征 {key!r} 是**跨注**特征（scope: cross），一注号码算不出来 —— "
            f"请用 portfolio.evaluate_cross_one(cfg, portfolio, {key!r})，"
            f"它需要一整组注作为输入。"
        )
    prim = decl.get("primitive")
    if not prim:
        raise EvaluateError(
            f"特征 {key!r} 只有 formula（人类注释），没有 primitive，框架无法求值。"
            f"请在该特征上补 `primitive` 与 `args`。"
        )

    args = dict(decl.get("args") or {})
    zone_name = args.get("zone")
    if zone_name is None:
        # 未指定区时：单区彩种可用唯一区；多区彩种必须显式给
        zs = zone_keys(cfg)
        if len(zs) != 1:
            raise EvaluateError(
                f"特征 {key!r} 的 args 未指定 `zone`，但配置有多个区 {zs}；"
                f"无法推断应对哪个区求值。"
            )
        zone_name = zs[0]

    try:
        vals = ticket.zone(zone_name)
    except Exception as e:
        raise EvaluateError(f"特征 {key!r} 引用区 {zone_name!r} 失败: {e}") from e

    args_with_name = dict(args)
    args_with_name["_zone_name"] = zone_name
    try:
        return apply_primitive(prim, vals, args_with_name)
    except PrimitiveError as e:
        raise EvaluateError(f"特征 {key!r} 求值失败（原语 {prim!r}）: {e}") from e


def evaluate(cfg: dict[str, Any], ticket: Ticket) -> dict[str, Any]:
    """对一注号码求出**全部可执行特征**。

    · 不可执行的特征（只有 formula）**被跳过**，不出现在结果里
    · 结构错误（区缺失等）**直接抛错**，不静默跳过

    返回：{feature_key: value}
    """
    # 先静态检查声明本身
    decl_errs = validate_feature_declarations(cfg)
    if decl_errs:
        raise EvaluateError(
            "game.yaml 的 features 声明有问题，无法求值：\n  - "
            + "\n  - ".join(decl_errs)
        )

    # 号码本身必须合法
    terr = ticket.validate(cfg)
    if terr:
        raise EvaluateError("号码不合法：" + "；".join(terr))

    out: dict[str, Any] = {}
    for key in evaluable_features(cfg):
        out[key] = evaluate_one(cfg, ticket, key)
    return out
