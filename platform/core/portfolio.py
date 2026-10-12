# -*- coding: utf-8 -*-
"""spc.core.portfolio — 一组注（**跨注层一等公民**）

## 为什么需要这个模块

`platform/core/` 此前只有 L1 `Ticket`（一注）与 L2（求值 / 判定）。
L3 Portfolio 层**只有接口没有实现** —— 后果是真实且外溢的：

```
strategy.json 的 R-002: predicate = "duplicated_structure_across_tickets == true"
                        ↓
  该特征从未在 game.yaml 声明（它描述的是「注与注之间」的关系）
                        ↓
  split_by_scope() 把它归为 cross → 单注层执行不了 → 显式上报跳过
                        ↓
  消费者拿到 strategy.json，却**没有任何办法执行 R-002**
```

也就是说：仓库对外输出了一条**消费者根本执行不了**的规则。
这不是"规则没量化"（`magnitude_pct: null` 是另一回事），
而是**契约层面缺了一整层**。本模块补的就是这一层。

## 与 Ticket 的关系

```
Ticket      一注号码          evaluate()        → 单注特征
Portfolio   一组 Ticket       evaluate_cross()  → 跨注特征（注与注之间）
```

`Portfolio` 与 `Ticket` 一样**不写死区名**：区名来自 `machine.zones`。
这是"加入第二个彩种不改 platform/" 的前提。

## 铁律（与 core/ 其它模块一致）

```
✗ 禁止出现 35 / 12 / 5 / 2
✗ 禁止出现 "dlt" / "大乐透"
✗ 禁止出现 "front" / "back"
✓ 一切从 cfg 读
```

## ⚠️ 跨注层能影响什么

**期望中奖注数恒为 N/T，与组合分散度无关（线性）。**
跨注规则只影响**方差**（多注同时撞号的风险），不影响期望。
本模块提供的判定结果不得被解读为"提高中奖概率"或"提高期望回报"。
"""
from __future__ import annotations

from typing import Any, Iterable, Iterator, Mapping, Sequence

from .features import PrimitiveError, apply_cross_primitive
from .game_util import (
    GameUtilError,
    cross_feature_keys,
    declared_cross_features,
    feature_scope,
    validate_feature_declarations,
    zone_keys,
)
from .judge import (
    ACTION_EXCLUDE,
    ACTION_PENALIZE,
    ACTION_PREFER,
    ACTION_REQUIRE,
    JudgeResult,
    PredicateError,
    VALID_ACTIONS,
    eval_predicate,
)
from .ticket import Ticket, TicketError

__all__ = [
    "Portfolio",
    "PortfolioError",
    "portfolio_from_any",
    "evaluable_cross_features",
    "evaluate_cross_one",
    "evaluate_cross",
    "judge_cross",
    "score_cross",
]


class PortfolioError(Exception):
    """一组注的结构或取值不合法。"""


class Portfolio:
    """一组注（`Ticket` 的有序集合）。

    内部存 `tuple[Ticket, ...]`，保持传入顺序（跨注判定不依赖顺序，
    但保持顺序让输出可复现）。
    """

    __slots__ = ("_tickets",)

    def __init__(self, tickets: Iterable[Any]):
        if isinstance(tickets, (Ticket, Mapping)):
            raise PortfolioError(
                f"Portfolio 需要**一组**注，收到单个 {type(tickets).__name__}。"
                f"传一注请用 [ticket] 包一层。"
            )
        try:
            raw = list(tickets)
        except TypeError as e:
            raise PortfolioError(f"无法把 {type(tickets).__name__} 当作注的序列") from e
        if not raw:
            raise PortfolioError("Portfolio 不能为空（跨注特征至少需要一注）")
        norm: list[Ticket] = []
        for i, t in enumerate(raw):
            if isinstance(t, Ticket):
                norm.append(t)
            elif isinstance(t, Mapping):
                norm.append(Ticket(t))
            else:
                raise PortfolioError(
                    f"第 {i} 项不是 Ticket 或 {{区名: 号码}}，得到 {type(t).__name__}"
                )
        self._tickets = tuple(norm)

    # -------------------------------------------------- 构造

    @classmethod
    def from_any(cls, obj: Any) -> "Portfolio":
        """接受 Portfolio / Ticket 列表 / dict 列表。"""
        if isinstance(obj, Portfolio):
            return obj
        if isinstance(obj, (Ticket, Mapping)):
            return cls([obj])
        return cls(obj)

    def append(self, ticket: Any) -> "Portfolio":
        """返回追加一注后的新 Portfolio（不修改自身）。"""
        return Portfolio(list(self._tickets) + [ticket])

    # -------------------------------------------------- 访问

    @property
    def tickets(self) -> tuple[Ticket, ...]:
        return self._tickets

    def zone_values(self, key: str) -> list[list[int]]:
        """取每注在某区的号码（供跨注原语消费）。"""
        out: list[list[int]] = []
        for i, t in enumerate(self._tickets):
            try:
                out.append(list(t.zone(key)))
            except TicketError as e:
                raise PortfolioError(f"第 {i} 注缺少区 {key!r}: {e}") from e
        return out

    def zone_keys(self) -> list[str]:
        """全部注共有的区名（按第一注）。"""
        return self._tickets[0].zone_keys()

    def as_list(self) -> list[Ticket]:
        return list(self._tickets)

    # -------------------------------------------------- 校验

    def validate(self, cfg: dict[str, Any]) -> list[str]:
        """逐注校验 + 全区名一致性。返回错误列表（空=合法）。"""
        errs: list[str] = []
        want = set(zone_keys(cfg))
        for i, t in enumerate(self._tickets):
            for e in t.validate(cfg):
                errs.append(f"第 {i} 注: {e}")
            got = set(t.zone_keys())
            if got != want:
                errs.append(
                    f"第 {i} 注的区名集合 {sorted(got)} 与配置声明 "
                    f"{sorted(want)} 不一致"
                )
        return errs

    def is_valid(self, cfg: dict[str, Any]) -> bool:
        return not self.validate(cfg)

    def check(self, cfg: dict[str, Any]) -> "Portfolio":
        errs = self.validate(cfg)
        if errs:
            raise PortfolioError("；".join(errs))
        return self

    # -------------------------------------------------- 协议方法

    def __len__(self) -> int:
        return len(self._tickets)

    def __iter__(self) -> Iterator[Ticket]:
        return iter(self._tickets)

    def __getitem__(self, i: int) -> Ticket:
        return self._tickets[i]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Portfolio):
            return self._tickets == other._tickets
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._tickets)

    def __repr__(self) -> str:
        return f"Portfolio({len(self._tickets)} 注)"

    def render(self, **kw) -> str:
        return "\n".join(t.render(**kw) for t in self._tickets)

    def to_json(self) -> list[dict[str, list[int]]]:
        return [t.to_json() for t in self._tickets]


def portfolio_from_any(obj: Any, cfg: dict[str, Any] | None = None) -> Portfolio:
    """宽松构造 + 可选校验。"""
    p = Portfolio.from_any(obj)
    if cfg is not None:
        p.check(cfg)
    return p


# ---------------------------------------------------------------- 跨注求值

def evaluable_cross_features(cfg: dict[str, Any]) -> list[str]:
    """列出可执行的**跨注**特征 key（声明了 primitive 且 scope=cross）。"""
    return [f["key"] for f in declared_cross_features(cfg) if f.get("primitive")]


def evaluate_cross_one(cfg: dict[str, Any], portfolio: Portfolio, key: str) -> Any:
    """求单个跨注特征的值。

    若该特征声明为 `scope: single`，**报错** —— 单注特征请走 `evaluate_one()`。
    这条边界是刻意的：让"拿错层的特征"变成显式错误，而不是静默给出无意义值。
    """
    decl = None
    for f in declared_cross_features(cfg):
        if f.get("key") == key:
            decl = f
            break
    if decl is None:
        raise PortfolioError(
            f"特征 {key!r} 不是跨注特征（未声明或 scope != cross）。"
            f"跨注特征：{', '.join(evaluable_cross_features(cfg)) or '（无）'}"
        )
    prim = decl.get("primitive")
    if not prim:
        raise PortfolioError(
            f"特征 {key!r} 只有 formula（人类注释），没有 primitive，框架无法求值。"
        )

    args = dict(decl.get("args") or {})
    zone_name = args.get("zone")
    if zone_name is None:
        zs = zone_keys(cfg)
        if len(zs) != 1:
            raise PortfolioError(
                f"特征 {key!r} 的 args 未指定 `zone`，但配置有多个区 {zs}；"
                f"无法推断应对哪个区求值。"
            )
        zone_name = zs[0]

    groups = portfolio.zone_values(zone_name)
    try:
        return apply_cross_primitive(prim, groups, args)
    except PrimitiveError as e:
        raise PortfolioError(
            f"特征 {key!r} 求值失败（原语 {prim!r}）: {e}"
        ) from e


def evaluate_cross(cfg: dict[str, Any], portfolio: Portfolio) -> dict[str, Any]:
    """对**一组注**求出全部可执行跨注特征。

    · 先静态检查声明，再逐注校验号码
    · 结构错误直接抛错，不静默跳过
    """
    decl_errs = validate_feature_declarations(cfg)
    if decl_errs:
        raise PortfolioError(
            "game.yaml 的 features 声明有问题，无法求值：\n  - "
            + "\n  - ".join(decl_errs)
        )
    perrs = portfolio.validate(cfg)
    if perrs:
        raise PortfolioError("号码不合法：" + "；".join(perrs))

    return {k: evaluate_cross_one(cfg, portfolio, k)
            for k in evaluable_cross_features(cfg)}


# ---------------------------------------------------------------- 跨注判定

def judge_cross(
    cfg: dict[str, Any],
    portfolio: Portfolio,
    rules: list[dict[str, Any]],
) -> JudgeResult:
    """按规则集判定**一组注**（只处理跨注层规则）。

    与 `judge()` 的差别：特征来自 `evaluate_cross()`（注与注之间），
    因此 `declared` 只含 `scope: cross` 的特征。

    ⚠️ 判定结果只反映「这组注与跨注规则的契合度」。
    **跨注规则不影响期望中奖注数（恒为 N/T），只影响方差。**
    """
    declared = cross_feature_keys(cfg)

    try:
        feats = evaluate_cross(cfg, portfolio)
    except PortfolioError as e:
        raise PredicateError(f"跨注特征求值失败: {e}") from e

    excluded = False
    required_failed = False
    weight = 1.0
    matched: list[str] = []
    actions: dict[str, str] = {}

    for r in rules:
        rid = r.get("id", "<无 id>")
        mr = r.get("machine_rule")
        if not mr:
            continue
        action = mr.get("action")
        if action not in VALID_ACTIONS:
            raise PredicateError(
                f"规则 {rid} 的 action={action!r} 非法，只允许 {sorted(VALID_ACTIONS)}"
            )
        pred = mr.get("predicate")
        if not pred:
            raise PredicateError(f"规则 {rid} 的 machine_rule 缺少 predicate")

        hit = eval_predicate(pred, feats, declared=declared)
        actions[rid] = action

        if action == ACTION_EXCLUDE:
            if hit:
                excluded = True
                matched.append(rid)
        elif action == ACTION_REQUIRE:
            if not hit:
                required_failed = True
                matched.append(rid)
        elif action == ACTION_PENALIZE:
            if hit:
                w = mr.get("weight")
                w = 0.5 if w is None else float(w)
                if not (0.0 < w <= 1.0):
                    raise PredicateError(
                        f"规则 {rid} 的 penalize 权重必须在 (0,1]，得到 {w}"
                    )
                weight *= w
                matched.append(rid)
        elif action == ACTION_PREFER:
            if hit:
                w = mr.get("weight")
                w = 0.5 if w is None else float(w)
                if not (0.0 < w <= 1.0):
                    raise PredicateError(
                        f"规则 {rid} 的 prefer 权重必须在 (0,1]，得到 {w}"
                    )
                weight *= (1.0 / w)
                matched.append(rid)

    return JudgeResult(
        excluded=excluded,
        required_failed=required_failed,
        weight=weight,
        matched=matched,
        actions=actions,
        features=feats,
    )


def score_cross(
    cfg: dict[str, Any],
    portfolio: Portfolio,
    rules: list[dict[str, Any]],
) -> float:
    """给一组注打跨注层分数（越高越好）。被 penalize 命中则降权。

    ⚠️ 与 `score()` 同理：这个分数**不代表中奖概率，也不代表期望回报**。
    """
    r = judge_cross(cfg, portfolio, rules)
    if not r.passes:
        return 0.0
    return r.weight
