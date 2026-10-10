# -*- coding: utf-8 -*-
"""smartpickcore.core.generate — 通用号码生成器（彩种无关）

## 为什么在这里（而不是交给消费方）

`docs/CONSUMING.md` 曾经的立场是「求值语义属于消费方，本仓库只承诺规则是什么」。
实践暴露了问题：**每个消费方都要自己实现 predicate 求值 + 拒绝采样，
就都有实现错的概率** —— 历史最严重的误读（把"避开连号"读成"提高中奖率"，
见 `avoid_list` 的 A-008）正是这类语义漂移的产物。

因此本仓库提供**参考实现**。消费方仍可自实现，但不再必须。
求值语义由 `judge.py` 单一来源定义。

## 生成策略

```
batch：本模块
  ├─ 均匀采样：从每个区独立采 pick 个号（等价于随机购票）
  └─ 按 rules 过滤：
       exclude  命中 → 丢弃
       require  未命中 → 丢弃
       penalize/prefer → 记权重，用于加权选择
```

**本模块不改变中奖概率**（恒为 1/T）。它只保证产出的号码满足规则。
"""
from __future__ import annotations

import random
from typing import Any, Iterable, Sequence

from .game_util import GameUtilError, max_value_of_zone, zone_by_key, zone_keys
from .judge import (
    ACTION_EXCLUDE,
    ACTION_REQUIRE,
    PredicateError,
    apply_scope,
    judge,
)
from .ticket import Ticket

__all__ = [
    "GenerateError",
    "sample_uniform",
    "sample_filtered",
    "sample_batch",
    "spread_penalty",
    "GenerateResult",
]


class GenerateError(Exception):
    """生成失败（预算不足、规则不可满足等）。"""


# ---------------------------------------------------------------- 均匀采样

def sample_uniform(cfg: dict[str, Any], rng: random.Random) -> Ticket:
    """均匀采一注：每个区独立地从 [min_value, max_value] 无放回抽 pick 个号。

    这是「等价于随机购票」的基线。
    """
    zones: dict[str, tuple[int, ...]] = {}
    for z in cfg["machine"]["zones"]:
        k = z["key"]
        mn = int(z.get("min_value", 1))
        mx = max_value_of_zone(cfg, k)
        pick = int(z["pick"])
        ordered = bool(z.get("ordered", False))
        picked = rng.sample(range(mn, mx + 1), pick)
        if not ordered:
            picked = sorted(picked)
        zones[k] = tuple(picked)
    return Ticket(zones)


# ---------------------------------------------------------------- 过滤采样

class GenerateResult:
    """一次批量生成的结果 + 统计。"""

    def __init__(self, tickets: list[Ticket], attempts: int, stats: dict[str, Any]):
        self.tickets = tickets
        self.attempts = attempts
        self.stats = stats

    def __len__(self) -> int:
        return len(self.tickets)

    def __iter__(self):
        return iter(self.tickets)

    def __getitem__(self, i):
        return self.tickets[i]

    def render(self, **kw) -> str:
        return "\n".join(t.render(**kw) for t in self.tickets)


def _rule_is_satisfiable(rules: list[dict[str, Any]]) -> tuple[bool, str]:
    """粗查规则集是否有明显自相矛盾（仅查同一 predicate 同时 exclude+require）。"""
    excl: set[str] = set()
    req: set[str] = set()
    for r in rules:
        mr = r.get("machine_rule") or {}
        p = mr.get("predicate")
        if not p:
            continue
        a = mr.get("action")
        if a == ACTION_EXCLUDE:
            excl.add(p)
        elif a == ACTION_REQUIRE:
            req.add(p)
    both = excl & req
    if both:
        return False, f"同一 predicate 同时被 exclude 与 require: {sorted(both)}"
    return True, ""


def sample_filtered(
    cfg: dict[str, Any],
    rules: list[dict[str, Any]],
    rng: random.Random,
    *,
    n: int = 1,
    max_attempts: int = 200_000,
    min_weight: float = 0.0,
) -> GenerateResult:
    """拒绝采样：反复均匀采样直到得到 n 注通过全部规则的号码。

    参数：
        n             需要的注数
        max_attempts  最多尝试次数（防死循环 —— 规则不可满足时会触顶报错）
        min_weight    只接受权重 >= min_weight 的注（默认 0 = 只要通过即可）

    ⚠️ **只执行单注层规则。** 跨注规则（如 R-002 的
    `duplicated_structure_across_tickets`）无法由一注号码判定，
    会被自动跳过并在 `stats["cross_scope_skipped"]` 里**显式上报**
    （不静默忽略）。跨注层的分散度由 `sample_batch(spread=True)` 的
    `spread_penalty` 事后评估。

    产出保证：
        · 每注都通过单注层的全部规则
        · 组合互不重复（用 Ticket 的哈希去重）
        · 按权重降序排列

    若规则不可满足（如 require 一个概率极低的条件），触顶后**明确报错**，
    不静默返回空列表。
    """
    single, cross = apply_scope(cfg, rules)
    ok, why = _rule_is_satisfiable(single)
    if not ok:
        raise GenerateError(f"规则集自相矛盾，无法生成: {why}")

    picked: dict[Ticket, float] = {}
    attempts = 0
    n_excluded = 0
    n_required_failed = 0

    while len(picked) < n and attempts < max_attempts:
        attempts += 1
        t = sample_uniform(cfg, rng)
        if t in picked:
            continue
        try:
            r = judge(cfg, t, single)
        except PredicateError as e:
            raise GenerateError(f"规则求值失败: {e}") from e
        if r.excluded:
            n_excluded += 1
            continue
        if r.required_failed:
            n_required_failed += 1
            continue
        if r.weight < min_weight:
            continue
        picked[t] = r.weight

    if len(picked) < n:
        raise GenerateError(
            f"在 {max_attempts} 次尝试内只生成 {len(picked)}/{n} 注。"
            f"（被 exclude 拒绝 {n_excluded} 次，require 未满足 {n_required_failed} 次）。"
            f"规则可能过严或不可满足。请检查 rules 或调大 max_attempts。"
        )

    ordered = sorted(picked.items(), key=lambda kv: (-kv[1], kv[0].render()))
    stats = {
        "attempts": attempts,
        "acceptance_rate": (len(picked) / attempts) if attempts else 0.0,
        "excluded": n_excluded,
        "required_failed": n_required_failed,
        "unique": len(picked),
        "single_scope_rules": [r["id"] for r in single],
        "cross_scope_skipped": [r.get("id") for r in cross],
    }
    return GenerateResult([t for t, _ in ordered], attempts, stats)


# ---------------------------------------------------------------- 批量

def sample_batch(
    cfg: dict[str, Any],
    rules: list[dict[str, Any]] | None = None,
    *,
    n: int = 1,
    seed: int | None = None,
    spread: bool = True,
    max_attempts: int = 200_000,
) -> GenerateResult:
    """对外主入口。

    参数：
        rules   空/None 时退化为均匀随机（不做规则过滤 —— 用于对照）
        seed    固定种子 → 可复现
        spread  是否启用「注间结构去重」（R-002 的精神；**未量化**，见 spread_penalty）

    返回 GenerateResult（含 tickets / attempts / stats）。
    """
    rng = random.Random(seed)

    if not rules:
        tickets = []
        seen: set[Ticket] = set()
        attempts = 0
        while len(tickets) < n and attempts < max_attempts:
            attempts += 1
            t = sample_uniform(cfg, rng)
            if t in seen:
                continue
            seen.add(t)
            tickets.append(t)
        return GenerateResult(tickets, attempts, {"mode": "uniform", "unique": len(seen)})

    if not spread:
        return sample_filtered(cfg, rules, rng, n=n, max_attempts=max_attempts)

    # 带结构分散：在通过规则的基础上，尽量让注间结构不同
    res = sample_filtered(cfg, rules, rng, n=n, max_attempts=max_attempts)
    res.stats["mode"] = "filtered+spread"
    res.stats["spread_penalty"] = spread_penalty(cfg, res.tickets)
    return res


# ---------------------------------------------------------------- 多注层（未量化）

def spread_penalty(cfg: dict[str, Any], tickets: Sequence[Ticket]) -> float:
    """一组注的「结构重复度」惩罚（0 = 完全分散，1 = 完全同构）。

    ⚠️ **本函数未被量化验证。** 它实现了 `strategy.json` 的 R-002 的精神，
    但 R-002 的 `magnitude_pct` 是 `null` —— 本仓库**从未做过**组合优化的
    模拟实验（见 `memory/workbench/OPEN_QUESTIONS.md` 的 Q-009 提案）。

    ⚠️ 更重要：**本函数的结果与期望中奖注数无关。**
    期望中奖注数恒为 `N / T`（线性），与结构分散度无关。
    分散只影响**方差**。

    定义（可替换，接口先定下）：
        对每个可求值的整数特征，计算各注取值的「重复集中度」，
        取平均。这里用「众数占比 - 均匀基线」的归一化形式。
    """
    if len(tickets) <= 1:
        return 0.0

    from .evaluate import evaluable_features, evaluate

    try:
        keys = evaluable_features(cfg)
    except GameUtilError:
        return 0.0
    if not keys:
        return 0.0

    # 只看整数型特征（布尔型天然只有 2 个取值，众数占比无意义）
    int_keys = [
        f["key"]
        for f in cfg["features"]
        if f.get("key") in keys and f.get("type") == "integer"
    ]
    if not int_keys:
        return 0.0

    feats = [evaluate(cfg, t) for t in tickets]
    n = len(tickets)
    penalties: list[float] = []
    for k in int_keys:
        vals = [f[k] for f in feats]
        counts: dict[Any, int] = {}
        for v in vals:
            counts[v] = counts.get(v, 0) + 1
        mode_share = max(counts.values()) / n
        # 归一化：1/n 是完全分散（基线），1.0 是完全同构
        if n > 1:
            pen = (mode_share - 1.0 / n) / (1.0 - 1.0 / n)
        else:
            pen = 0.0
        penalties.append(max(0.0, min(1.0, pen)))
    return sum(penalties) / len(penalties)
