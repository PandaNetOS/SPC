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
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

__all__ = [
    "PrimitiveError",
    "PRIMITIVES",
    "list_primitives",
    "resolve_primitive",
    "arity_of",
]

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
}

#: 声明为 `zone` 的原语（需要 zone 参数）
_ZONE_PRIMITIVES = frozenset(PRIMITIVES)


def list_primitives() -> list[str]:
    """列出全部可用原语名（供文档与校验器）。"""
    return sorted(PRIMITIVES)


def arity_of(name: str) -> tuple[str, ...]:
    """返回原语必需的 args 名（空元组表示无必需参数）。"""
    if name not in PRIMITIVES:
        raise PrimitiveError(
            f"未知原语 {name!r}。可用原语：{', '.join(list_primitives())}"
        )
    return _REQUIRED_ARGS.get(name, ())


def resolve_primitive(name: str) -> Callable[..., Any]:
    """按名字取原语函数。名字不存在时报错并列出可用项。"""
    if name not in PRIMITIVES:
        raise PrimitiveError(
            f"未知原语 {name!r}。可用原语：{', '.join(list_primitives())}"
        )
    return PRIMITIVES[name]


def apply_primitive(
    name: str,
    zone_values: Iterable[int],
    args: dict[str, Any] | None = None,
) -> Any:
    """对一组号码值执行原语。args 中的 `zone` 键会被忽略（由调用方传入）。"""
    fn = resolve_primitive(name)
    a = dict(args or {})
    a.pop("zone", None)
    zone_key = a.pop("_zone_name", "zone")
    ordered = _sorted_zone(list(zone_values), zone_key)
    return fn(ordered, **a)
