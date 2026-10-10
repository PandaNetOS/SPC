# -*- coding: utf-8 -*-
"""smartpickcore.core.features — 特征原语库（彩种无关）

## 这是什么

一注号码的「派生特征」（和值、跨度、连号对数…）由 `games/<id>/game.yaml`
的 `features[]` 段**声明**。本模块提供**可被声明的原语**。

## 铁律：这里只许出现纯数学

```
✗ 禁止出现 35 / 12 / 5 / 2（号码池参数）
✗ 禁止出现 "dlt" / "大乐透"
✗ 禁止出现 "front" / "back"（区名是彩种字段名）
✗ 禁止出现 "has_run_ge2" / "adjacent_pairs"（特征名是彩种声明的）
✓ 只接受一个整数序列，返回一个数或布尔
```

原语通过 `args` 收参（如 `zone` / `threshold`），参数值由 `game.yaml` 给。
**原语的签名里不含任何具体彩种的常量。**

## 为什么不用 eval(formula)

`game.yaml` 里的 `formula` 字段是**给人看的注释**（如 `"sum(front)"`），
**不参与求值**。若真的解析执行它，会有两类问题：

1. 安全：`eval` 任意表达式
2. 不可静态验证：校验器无法确认 `formula` 引用的特征是否存在

改为「原语名 + 参数」后，校验器可以**静态确认**每个 `primitive` 都在本表里，
每个 `args.zone` 都在 `machine.zones` 里。这是结构性保障，不靠自觉。

## 新增彩种时怎么办

若某彩种的特征现有原语表达不了 → **往 PRIMITIVES 加一个纯数学函数**。
加的是彩种无关的通用原语，不是彩种分支 —— 这不违反「唯一硬标准」。

## 单注原语与跨注原语（scope）

`config_version 2.1` 起，`game.yaml` 的 `features[]` 可声明 `scope`：

| scope | 输入 | 例子 | 求值入口 |
|---|---|---|---|
| `single`（默认） | 一注的**一个区** `[3,11,17,24,32]` | sum / adjacent_pair_count | `evaluate()` |
| `cross` | **一组注**的同一个区 `[[3,11,...],[5,9,...],...]` | duplicate_structure_count | `evaluate_cross()` |

两套原语**分表注册**（`PRIMITIVES` / `CROSS_PRIMITIVES`），
`validate_feature_declarations()` 会**结构性拒绝**把单注原语用在
`scope: cross` 的特征上（反之亦然）——
与四条红线同一思路：靠 `const`/分表拒收，不靠自觉。

**为什么必须分表**：跨注特征（如"这组注里有多少注结构重复"）
从一注号码**在数学上算不出来**。若允许混用，调用方会把
`sum` 之类的单注原语喂进一组注里，得到毫无意义却**不报错**的结果 ——
静默错误正是本仓库要防的那类。
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

__all__ = [
    "PrimitiveError",
    "PRIMITIVES",
    "CROSS_PRIMITIVES",
    "PRIMITIVE_SCOPES",
    "SCOPE_SINGLE",
    "SCOPE_CROSS",
    "list_primitives",
    "resolve_primitive",
    "resolve_cross_primitive",
    "arity_of",
    "scope_of",
    "apply_primitive",
    "apply_cross_primitive",
]

SCOPE_SINGLE = "single"
SCOPE_CROSS = "cross"

Numbers = Sequence[int]


class PrimitiveError(Exception):
    """原语使用错误（名字不存在、参数不合法、输入不是整数序列）。"""


# ---------------------------------------------------------------- 内部工具

def _sorted_zone(zone: Any, name: str) -> list[int]:
    """把输入规范成「去重排序后的整数列表」，不顺从就报错。

    为什么强制排序：连号对、跨度这类原语依赖顺序。
    若调用方传来未排序的列表，结果会静默错误 —— 这里选择**报错而非猜测**。
    """
    if zone is None:
        raise PrimitiveError(f"args.zone={name!r} 指向的区不存在")
    try:
        vals = list(zone)
    except TypeError as e:
        raise PrimitiveError(f"args.zone={name!r} 的值不是可迭代对象") from e
    for v in vals:
        if not isinstance(v, int) or isinstance(v, bool):
            raise PrimitiveError(f"args.zone={name!r} 含非整数元素: {v!r}")
    if not vals:
        raise PrimitiveError(f"args.zone={name!r} 为空")
    if len(set(vals)) != len(vals):
        raise PrimitiveError(f"args.zone={name!r} 含重复元素: {vals}")
    return sorted(vals)


def _need(args: dict, key: str, prim: str) -> Any:
    if key not in args:
        raise PrimitiveError(f"原语 {prim!r} 缺少必需参数 {key!r}")
    return args[key]


def _int_arg(args: dict, key: str, prim: str) -> int:
    v = _need(args, key, prim)
    if not isinstance(v, int) or isinstance(v, bool):
        raise PrimitiveError(f"原语 {prim!r} 的参数 {key!r} 必须是整数，得到 {v!r}")
    return v


# ---------------------------------------------------------------- 原语实现
# 约定：签名 (zone, **args) -> int | bool
#   zone  正被求值的区的号码（已排序去重）
#   args  来自 game.yaml 的 args 段

def _p_sum(zone: Numbers, **_: Any) -> int:
    """和值。"""
    return sum(zone)


def _p_span(zone: Numbers, **_: Any) -> int:
    """跨度 = max - min。"""
    s = sorted(zone)
    return s[-1] - s[0]


def _p_min(zone: Numbers, **_: Any) -> int:
    return min(zone)


def _p_max(zone: Numbers, **_: Any) -> int:
    return max(zone)


def _p_count(zone: Numbers, **_: Any) -> int:
    """元素个数。"""
    return len(zone)


def _p_count_odd(zone: Numbers, **_: Any) -> int:
    """奇数个数。"""
    return sum(1 for x in zone if x % 2 == 1)


def _p_count_even(zone: Numbers, **_: Any) -> int:
    """偶数个数。"""
    return sum(1 for x in zone if x % 2 == 0)


def _p_count_ge(zone: Numbers, **args: Any) -> int:
    """>= threshold 的个数。args: threshold。"""
    t = _int_arg(args, "threshold", "count_ge")
    return sum(1 for x in zone if x >= t)


def _p_count_le(zone: Numbers, **args: Any) -> int:
    """<= threshold 的个数。args: threshold。"""
    t = _int_arg(args, "threshold", "count_le")
    return sum(1 for x in zone if x <= t)


def _p_adjacent_pair_count(zone: Numbers, **_: Any) -> int:
    """相邻号对数量（如 12-13 算 1 对；12-13-14 算 2 对）。

    ⚠️ 纯数学定义，不含任何彩种常量。
    """
    s = sorted(zone)
    return sum(1 for a, b in zip(s, s[1:]) if b - a == 1)


def _p_adjacent_pair_count_ge(zone: Numbers, **args: Any) -> bool:
    """>= threshold 个相邻号对。args: threshold。

    这是本仓库策略核心判定量 `has_run_ge2` 的原语载体 ——
    但原语本身不知道「run」「连号」这些彩种概念，它只数相邻对。
    """
    t = _int_arg(args, "threshold", "adjacent_pair_count_ge")
    return _p_adjacent_pair_count(zone) >= t


def _p_max_gap(zone: Numbers, **_: Any) -> int:
    """最大间隔（相邻差的 max）。"""
    s = sorted(zone)
    if len(s) < 2:
        return 0
    return max(b - a for a, b in zip(s, s[1:]))


def _p_min_gap(zone: Numbers, **_: Any) -> int:
    """最小间隔（相邻差的 min）。"""
    s = sorted(zone)
    if len(s) < 2:
        return 0
    return min(b - a for a, b in zip(s, s[1:]))


def _p_all_le(zone: Numbers, **args: Any) -> bool:
    """全部 <= threshold。args: threshold。"""
    t = _int_arg(args, "threshold", "all_le")
    return all(x <= t for x in zone)


def _p_all_ge(zone: Numbers, **args: Any) -> bool:
    """全部 >= threshold。args: threshold。"""
    t = _int_arg(args, "threshold", "all_ge")
    return all(x >= t for x in zone)


def _p_any_le(zone: Numbers, **args: Any) -> bool:
    """存在 <= threshold。args: threshold。"""
    t = _int_arg(args, "threshold", "any_le")
    return any(x <= t for x in zone)


def _p_any_ge(zone: Numbers, **args: Any) -> bool:
    """存在 >= threshold。args: threshold。"""
    t = _int_arg(args, "threshold", "any_ge")
    return any(x >= t for x in zone)


def _p_has_consecutive(zone: Numbers, **_: Any) -> bool:
    """是否存在相邻号对（>=1 对）。"""
    return _p_adjacent_pair_count(zone) >= 1


def _p_count_in_range(zone: Numbers, **args: Any) -> int:
    """落在 [lo, hi] 闭区间内的个数。args: lo, hi。"""
    lo = _int_arg(args, "lo", "count_in_range")
    hi = _int_arg(args, "hi", "count_in_range")
    if lo > hi:
        raise PrimitiveError(f"count_in_range: lo={lo} > hi={hi}")
    return sum(1 for x in zone if lo <= x <= hi)


def _p_max_in_range(zone: Numbers, **args: Any) -> int:
    """区间 [lo,hi] 内的最大号；区间内无号时返回 0。

    用途举例：判断「是否含生日号区（<=31）的号」这类特征。
    返回 0 而非 None，是为了让特征可被 DSL 直接比较（弱 DSL 不支持 null）。
    args: lo, hi。
    """
    lo = _int_arg(args, "lo", "max_in_range")
    hi = _int_arg(args, "hi", "max_in_range")
    hit = [x for x in zone if lo <= x <= hi]
    return max(hit) if hit else 0


def _p_sum_mod(zone: Numbers, **args: Any) -> int:
    """和值对 modulus 取余。args: modulus。"""
    m = _int_arg(args, "modulus", "sum_mod")
    if m <= 0:
        raise PrimitiveError(f"sum_mod: modulus 必须为正，得到 {m}")
    return sum(zone) % m


# ---------------------------------------------------------------- 跨注原语
# 约定：签名 (groups, **args) -> int | bool
#   groups  list[list[int]] —— **一组注**在同一区的号码（每注已排序去重）
#
# 这些量在数学上无法由单注算出：它们描述的是「注与注之间」的关系。

def _sorted_groups(groups: Any, name: str) -> list[list[int]]:
    """把输入规范成「若干组已排序去重的整数列表」。"""
    if groups is None:
        raise PrimitiveError(f"{name} 为空（跨注原语需要一组注）")
    try:
        raw = list(groups)
    except TypeError as e:
        raise PrimitiveError(f"{name} 不是可迭代对象") from e
    if not raw:
        raise PrimitiveError(f"{name} 为空列表（跨注原语至少需要一注）")
    return [_sorted_zone(g, f"{name}[{i}]") for i, g in enumerate(raw)]


def _gap_signature(vals: Sequence[int]) -> tuple[int, ...]:
    """结构签名 = 相邻间隔向量。

    例：(1,3,5) 与 (2,4,6) 的签名都是 (2,2) —— 号码不同但**结构相同**。
    这正是 R-002「多注集中在同一结构形态」要刻画的量。
    用间隔向量而非号码本身，是刻意的：否则两注号码不同就永远判不出「同构」。
    """
    return tuple(b - a for a, b in zip(vals, vals[1:]))


def _c_duplicate_structure_count(groups: Any, **_: Any) -> int:
    """结构签名在组内出现 >= 2 次的**注数**（不是"重复了几对"）。

    例：3 注的签名若为 [(2,2), (2,2), (1,3)] → 返回 2（前两注互相同构）。
    """
    gs = _sorted_groups(groups, "groups")
    sigs = [_gap_signature(g) for g in gs]
    counts: dict[tuple[int, ...], int] = {}
    for s in sigs:
        counts[s] = counts.get(s, 0) + 1
    return sum(1 for s in sigs if counts[s] >= 2)


def _c_duplicate_structure_count_ge(groups: Any, **args: Any) -> bool:
    """>= threshold 注与他人结构同构。args: threshold。

    这是 `strategy.json` R-002 的判定量载体 —— 但原语本身不知道
    「分散」「撞号」这些概念，它只数同构的注数。
    """
    t = _int_arg(args, "threshold", "duplicate_structure_count_ge")
    return _c_duplicate_structure_count(groups) >= t


def _c_distinct_structure_count(groups: Any, **_: Any) -> int:
    """组内不同结构签名的个数（1 = 全同构，len(groups) = 全异）。"""
    gs = _sorted_groups(groups, "groups")
    return len({_gap_signature(g) for g in gs})


def _c_coverage_unique_count(groups: Any, **_: Any) -> int:
    """全组去重后覆盖到的不同号码总数（衡量号码空间的铺开程度）。"""
    gs = _sorted_groups(groups, "groups")
    return len({x for g in gs for x in g})


def _c_max_shared_count(groups: Any, **_: Any) -> int:
    """任意两注之间共享号码数的**最大值**（衡量注间重叠程度）。"""
    gs = _sorted_groups(groups, "groups")
    best = 0
    for i in range(len(gs)):
        si = set(gs[i])
        for j in range(i + 1, len(gs)):
            best = max(best, len(si & set(gs[j])))
    return best


# ---------------------------------------------------------------- 注册表

PRIMITIVES: dict[str, Callable[..., Any]] = {
    # 基础统计
    "sum": _p_sum,
    "span": _p_span,
    "min": _p_min,
    "max": _p_max,
    "count": _p_count,
    # 奇偶
    "count_odd": _p_count_odd,
    "count_even": _p_count_even,
    # 阈值计数
    "count_ge": _p_count_ge,
    "count_le": _p_count_le,
    "count_in_range": _p_count_in_range,
    # 相邻 / 间隔
    "adjacent_pair_count": _p_adjacent_pair_count,
    "adjacent_pair_count_ge": _p_adjacent_pair_count_ge,
    "has_consecutive": _p_has_consecutive,
    "max_gap": _p_max_gap,
    "min_gap": _p_min_gap,
    # 全称 / 存在量词
    "all_le": _p_all_le,
    "all_ge": _p_all_ge,
    "any_le": _p_any_le,
    "any_ge": _p_any_ge,
    # 区间
    "max_in_range": _p_max_in_range,
    # 其他
    "sum_mod": _p_sum_mod,
}

#: 跨注原语（scope: cross）。输入是一组注，不是一注。
CROSS_PRIMITIVES: dict[str, Callable[..., Any]] = {
    "duplicate_structure_count": _c_duplicate_structure_count,
    "duplicate_structure_count_ge": _c_duplicate_structure_count_ge,
    "distinct_structure_count": _c_distinct_structure_count,
    "coverage_unique_count": _c_coverage_unique_count,
    "max_shared_count": _c_max_shared_count,
}

#: 原语名 → 作用域。供 game_util 静态校验「原语与 scope 是否匹配」。
PRIMITIVE_SCOPES: dict[str, str] = {
    **{n: SCOPE_SINGLE for n in PRIMITIVES},
    **{n: SCOPE_CROSS for n in CROSS_PRIMITIVES},
}

#: 需要 args 的原语 → 必需参数名（供校验器静态检查 game.yaml 是否给全参数）
_REQUIRED_ARGS: dict[str, tuple[str, ...]] = {
    "count_ge": ("threshold",),
    "count_le": ("threshold",),
    "count_in_range": ("lo", "hi"),
    "adjacent_pair_count_ge": ("threshold",),
    "all_le": ("threshold",),
    "all_ge": ("threshold",),
    "any_le": ("threshold",),
    "any_ge": ("threshold",),
    "max_in_range": ("lo", "hi"),
    "sum_mod": ("modulus",),
    "duplicate_structure_count_ge": ("threshold",),
}

#: 声明为 `zone` 的原语（需要 zone 参数）
_ZONE_PRIMITIVES = frozenset(PRIMITIVES)


def list_primitives(scope: str | None = None) -> list[str]:
    """列出可用原语名（供文档与校验器）。

    scope=None  → 全部；"single" → 仅单注；"cross" → 仅跨注。
    """
    if scope is None:
        return sorted(PRIMITIVE_SCOPES)
    if scope == SCOPE_SINGLE:
        return sorted(PRIMITIVES)
    if scope == SCOPE_CROSS:
        return sorted(CROSS_PRIMITIVES)
    raise PrimitiveError(
        f"未知 scope {scope!r}，只能是 {SCOPE_SINGLE!r} 或 {SCOPE_CROSS!r}"
    )


def scope_of(name: str) -> str:
    """原语所属作用域。未知原语报错并列出可用项。"""
    if name not in PRIMITIVE_SCOPES:
        raise PrimitiveError(
            f"未知原语 {name!r}。可用原语：{', '.join(list_primitives())}"
        )
    return PRIMITIVE_SCOPES[name]


def arity_of(name: str) -> tuple[str, ...]:
    """返回原语必需的 args 名（空元组表示无必需参数）。"""
    if name not in PRIMITIVE_SCOPES:
        raise PrimitiveError(
            f"未知原语 {name!r}。可用原语：{', '.join(list_primitives())}"
        )
    return _REQUIRED_ARGS.get(name, ())


def resolve_primitive(name: str) -> Callable[..., Any]:
    """按名字取**单注**原语函数。名字不存在时报错并列出可用项。"""
    if name not in PRIMITIVES:
        extra = ""
        if name in CROSS_PRIMITIVES:
            extra = (
                f" —— 注意 {name!r} 是**跨注**原语，只能在 scope: cross 的"
                f"特征上使用（用 resolve_cross_primitive 取它）"
            )
        raise PrimitiveError(
            f"未知单注原语 {name!r}。可用单注原语："
            f"{', '.join(list_primitives(SCOPE_SINGLE))}{extra}"
        )
    return PRIMITIVES[name]


def resolve_cross_primitive(name: str) -> Callable[..., Any]:
    """按名字取**跨注**原语函数。名字不存在时报错并列出可用项。"""
    if name not in CROSS_PRIMITIVES:
        extra = ""
        if name in PRIMITIVES:
            extra = (
                f" —— 注意 {name!r} 是**单注**原语，不能用在 scope: cross 的"
                f"特征上（用 resolve_primitive 取它）"
            )
        raise PrimitiveError(
            f"未知跨注原语 {name!r}。可用跨注原语："
            f"{', '.join(list_primitives(SCOPE_CROSS))}{extra}"
        )
    return CROSS_PRIMITIVES[name]


def apply_primitive(
    name: str,
    zone_values: Iterable[int],
    args: dict[str, Any] | None = None,
) -> Any:
    """对一组号码值执行**单注**原语。args 中的 `zone` 键会被忽略（由调用方传入）。"""
    fn = resolve_primitive(name)
    a = dict(args or {})
    a.pop("zone", None)
    zone_key = a.pop("_zone_name", "zone")
    ordered = _sorted_zone(list(zone_values), zone_key)
    return fn(ordered, **a)


def apply_cross_primitive(
    name: str,
    groups: Iterable[Iterable[int]],
    args: dict[str, Any] | None = None,
) -> Any:
    """对**一组注**执行跨注原语。args 中的 `zone` 键会被忽略（由调用方传入）。"""
    fn = resolve_cross_primitive(name)
    a = dict(args or {})
    a.pop("zone", None)
    a.pop("_zone_name", None)
    return fn(list(groups), **a)
