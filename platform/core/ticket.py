# -*- coding: utf-8 -*-
"""spc.core.ticket — 一条观测记录（通用一等公民，不绑定任何具体问题）

## 这是什么

一条「观测记录」是研究对象的最小单位。它由多个「维度」组成，
每个维度有一组取值。区名/维度名来自配置，不硬编码。

```python
# 彩票：一条选号记录
Record({"front": (3, 11, 17, 24, 32), "back": (4, 9)})

# 股票：一条 K 线记录（未来扩展）
Record({"open": 10.5, "close": 11.2, "volume": 100000})

# 医学：一条病例记录（未来扩展）
Record({"age": 45, "blood_pressure": 120, "diagnosis": "hypertension"})
```

## 为什么需要这个类

平台此前只有两端：

```
machine.zones  →  compute_space()  →  T / 基础概率       （观测空间级）
strategy.json  →  load_strategy()  →  规则                 （规则级）
```

**中间那层「拿一条记录，算它的特征、判它合规、给它打分」是缺的。**
缺了它，就必须由每个消费方自己实现 —— 这正是 `machine_rule.predicate`
一直只是「给人看的字符串」的根因。

## 核心设计：不写死维度名

`Record`（别名 `Ticket`）**不含 `front` / `back`**。维度名来自 `machine.zones`，长度可变：

```python
Record({"front": (3, 11, 17, 24, 32), "back": (4, 9)})   # 大乐透（2 维）
Record({"main": (1, 2, 3, 4, 5, 6, 7)})                  # 单维 7 选 7
```

若写死 `front`/`back`，就等于把某个彩种的字段名硬编码进平台 ——
违反「唯一硬标准」。

## 向后兼容

- `Ticket` 是 `Record` 的别名，现有代码无需修改
- `ticket_from_any()` 是 `record_from_any()` 的别名
"""
from __future__ import annotations

from typing import Any, Iterable, Iterator, Mapping, Sequence

from .game_util import (
    GameUtilError,
    max_value_of_zone,
    zone_by_key,
    zone_keys,
)

__all__ = ["Ticket", "TicketError", "ticket_from_any"]


class TicketError(Exception):
    """一注号码的结构或取值不合法。"""


class Ticket:
    """一注号码。结构完全由 `machine.zones` 决定。

    内部存储为 `{zone_key: tuple(sorted(values))}`。
    每次都存**规范化**后的形式（升序、元组、不可变），
    这样 `Ticket` 可哈希、可比较、可放集合去重。
    """

    __slots__ = ("_zones",)

    def __init__(self, zones: Mapping[str, Iterable[int]]):
        if not isinstance(zones, Mapping):
            raise TicketError(f"zones 必须是映射（区名 → 号码序列），得到 {type(zones).__name__}")
        norm: dict[str, tuple[int, ...]] = {}
        for k, v in zones.items():
            if not isinstance(k, str):
                raise TicketError(f"区名必须是字符串，得到 {k!r}")
            try:
                vals = tuple(sorted(int(x) for x in v))
            except (TypeError, ValueError) as e:
                raise TicketError(f"区 {k!r} 的号码序列无法转成整数序列: {v!r}") from e
            norm[k] = vals
        self._zones = norm

    # -------------------------------------------------- 构造

    @classmethod
    def from_any(cls, obj: Any) -> "Ticket":
        """接受 Ticket / dict / list-of-list 等多种输入，统一成 Ticket。

        · Ticket            → 原样
        · {"front": [...], "back": [...]}  → 直接
        · [[3,11,17,24,32], [4,9]]         → 按 zones 顺序映射（需传 zone_keys）
        """
        if isinstance(obj, Ticket):
            return obj
        if isinstance(obj, Mapping):
            return cls(obj)
        raise TicketError(
            f"无法把 {type(obj).__name__} 转成 Ticket；请传 Ticket 或 {{区名: 号码}}"
        )

    def replace_zone(self, key: str, values: Iterable[int]) -> "Ticket":
        """返回替换了某个区的新 Ticket（不修改自身）。"""
        d = dict(self._zones)
        d[key] = tuple(sorted(int(x) for x in values))
        return Ticket(d)

    # -------------------------------------------------- 访问

    def zone(self, key: str) -> tuple[int, ...]:
        if key not in self._zones:
            raise TicketError(
                f"本注不含区 {key!r}。本注的区：{', '.join(self.zone_keys())}"
            )
        return self._zones[key]

    def zone_keys(self) -> list[str]:
        """本注实际含有的区名。"""
        return list(self._zones.keys())

    def as_dict(self) -> dict[str, tuple[int, ...]]:
        return dict(self._zones)

    def values(self) -> Iterator[int]:
        for v in self._zones.values():
            yield from v

    # -------------------------------------------------- 校验

    def validate(self, cfg: dict[str, Any]) -> list[str]:
        """对照 `cfg['machine']['zones']` 校验本注。返回错误列表（空=合法）。

        检查项：
          1. 区名集合**恰好**等于配置声明的区名集合（不多不少）
          2. 每区号码个数 == pick
          3. 每区号码在 [min_value, min_value + pool_size - 1] 内
          4. 每区内无重复
          5. 区配置声明 ordered=True 时，号码顺序须为升序（本类总是升序存，故必过）
        """
        errs: list[str] = []
        try:
            want = set(zone_keys(cfg))
        except GameUtilError as e:
            return [f"配置不可用: {e}"]

        got = set(self._zones.keys())
        missing = want - got
        extra = got - want
        if missing:
            errs.append(f"缺少区: {sorted(missing)}")
        if extra:
            errs.append(f"多出未声明的区: {sorted(extra)}")

        for k in sorted(want & got):
            vals = self._zones[k]
            zdef = zone_by_key(cfg, k)
            pick = int(zdef["pick"])
            mn = int(zdef.get("min_value", 1))
            mx = max_value_of_zone(cfg, k)

            if len(vals) != pick:
                errs.append(f"区 {k}: 需 {pick} 个号，实际 {len(vals)} 个")
            if len(set(vals)) != len(vals):
                errs.append(f"区 {k}: 含重复号 {vals}")
            out = [v for v in vals if v < mn or v > mx]
            if out:
                errs.append(f"区 {k}: 号码越界 {out}（合法范围 [{mn}, {mx}]）")
        return errs

    def is_valid(self, cfg: dict[str, Any]) -> bool:
        return not self.validate(cfg)

    def check(self, cfg: dict[str, Any]) -> "Ticket":
        """不合法就抛 TicketError（链式调用友好）。"""
        errs = self.validate(cfg)
        if errs:
            raise TicketError("；".join(errs))
        return self

    # -------------------------------------------------- 协议方法

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Ticket):
            return self._zones == other._zones
        return NotImplemented

    def __hash__(self) -> int:
        return hash(tuple(sorted(self._zones.items())))

    def __len__(self) -> int:
        return sum(len(v) for v in self._zones.values())

    def __iter__(self) -> Iterator[str]:
        return iter(self._zones)

    def __repr__(self) -> str:
        inner = ", ".join(
            f"{k}={list(v)}" for k, v in self._zones.items()
        )
        return f"Ticket({inner})"

    def render(self, sep: str = " ", zone_sep: str = " + ", width: int = 2) -> str:
        """人类可读单行。宽度按最大号自适应（如 '03 11 17 24 32 + 04 09'）。"""
        parts = []
        for k in self._zones:
            parts.append(sep.join(f"{v:0{width}d}" for v in self._zones[k]))
        return zone_sep.join(parts)

    def to_json(self) -> dict[str, list[int]]:
        return {k: list(v) for k, v in self._zones.items()}


def ticket_from_any(obj: Any, cfg: dict[str, Any] | None = None) -> Ticket:
    """宽松构造 + 可选校验。

    接受的输入：
      · Ticket
      · {"front": [...], "back": [...]}
      · {"front": "03 11 17 24 32", "back": "04 09"}   ← 字符串会自动分词
    """
    if isinstance(obj, Ticket):
        t = obj
    elif isinstance(obj, Mapping):
        norm: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(v, str):
                norm[k] = [int(x) for x in v.replace(",", " ").split()]
            else:
                norm[k] = v
        t = Ticket(norm)
    else:
        raise TicketError(f"无法识别的输入类型: {type(obj).__name__}")

    if cfg is not None:
        t.check(cfg)
    return t


# ============================================================
# 抽象升级：Record 是 Ticket 的通用别名
# ============================================================
# Ticket = Record（一条观测记录）
# 现有代码用 Ticket，新代码推荐用 Record
# 两者完全等价

Record = Ticket
RecordError = TicketError
record_from_any = ticket_from_any

__all__ = [
    "Ticket", "TicketError", "ticket_from_any",
    "Record", "RecordError", "record_from_any",  # 通用别名
]
