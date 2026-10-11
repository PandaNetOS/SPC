# -*- coding: utf-8 -*-
"""spc.core.judge — `machine_rule.predicate` 的受限 DSL 求值器

## 这个模块存在的理由

`strategy.json` 里每条规则都有：

```json
"machine_rule": {
  "predicate": "has_run_ge2 == true",
  "action": "exclude"
}
```

在此模块出现之前，`predicate` **只是一串给人看的字符串** ——
校验器无法确认它引用的是否是已声明的特征，消费方必须各自实现求值，
而各自实现就可能各自实现错（历史最严重误读见 `avoid_list` 的 A-008）。

## DSL 故意做弱（这是设计，不是限制）

只允许：

```
<feature_key> <op> <literal>
op      ∈ { ==, !=, <, <=, >, >= }
literal ∈ { true, false, 整数, 浮点 }
连接词  ： and / or  （不能混用，不支持括号、不支持嵌套）
```

**为什么不支持完整表达式**：校验器要能**静态确认**每个 `feature_key`
都在 `game.yaml` 的 `features[]` 里存在。DSL 越弱，静态可验证性越强。

格式错误的 predicate **在 schema 层就被拒收**（见 `spec/strategy.schema.json`
的 `machine_rule.predicate.pattern`），根本存不进仓库 ——
与四条红线同一思路：**结构性拒收优于文档劝告**。
"""
from __future__ import annotations

import re
from typing import Any, NamedTuple

from .evaluate import EvaluateError, evaluate
from .ticket import Ticket

__all__ = [
    "PredicateError",
    "Comparison",
    "parse_predicate",
    "eval_predicate",
    "JudgeResult",
    "judge",
    "score",
    "apply_scope",
    "split_by_scope",
    "classify_rules",
    "RuleScopes",
    "ACTION_EXCLUDE",
    "ACTION_PENALIZE",
    "ACTION_PREFER",
    "ACTION_REQUIRE",
    "VALID_ACTIONS",
]

ACTION_EXCLUDE = "exclude"
ACTION_PENALIZE = "penalize"
ACTION_PREFER = "prefer"
ACTION_REQUIRE = "require"
VALID_ACTIONS = frozenset(
    {ACTION_EXCLUDE, ACTION_PENALIZE, ACTION_PREFER, ACTION_REQUIRE}
)


class PredicateError(Exception):
    """predicate 语法错误、引用未声明特征、或求值失败。"""


# ---------------------------------------------------------------- DSL

_OPS = ("==", "!=", "<=", ">=", "<", ">")

_TERM_RE = re.compile(
    r"^\s*([a-z_][a-z0-9_]*)\s*(==|!=|<=|>=|<|>)\s*"
    r"(-?[0-9]+(?:\.[0-9]+)?|true|false)\s*$"
)


class Comparison(NamedTuple):
    """单个比较项。"""
    feature: str
    op: str
    literal: Any


class ParsedPredicate(NamedTuple):
    """解析结果：若干比较项 + 连接方式。"""

    terms: tuple[Comparison, ...]
    connector: str | None      # None（单项） / "and" / "or"

    def features(self) -> list[str]:
        return [t.feature for t in self.terms]


def _parse_literal(raw: str) -> Any:
    if raw == "true":
        return True
    if raw == "false":
        return False
    if "." in raw:
        return float(raw)
    return int(raw)


def parse_predicate(text: str) -> ParsedPredicate:
    """把 predicate 文本解析成比较项列表。

    支持：
      "has_run_ge2 == true"
      "front_sum > 100"
      "a == true and b < 3"
      "a == true or b == false"

    不支持（明确报错，不猜测）：
      "a == true and b < 3 or c == 1"   ← 混用连接词
      "(a == true or b == false) and c == 1"  ← 括号
      "a > b"                            ← 右侧不是字面量
    """
    if not isinstance(text, str) or not text.strip():
        raise PredicateError("predicate 必须是非空字符串")

    s = text.strip()

    if "(" in s or ")" in s:
        raise PredicateError(
            f"predicate 不支持括号（DSL 故意做弱以保静态可验证性）：{text!r}"
        )

    has_and = re.search(r"\s+and\s+", s) is not None
    has_or = re.search(r"\s+or\s+", s) is not None
    if has_and and has_or:
        raise PredicateError(
            f"predicate 不允许混用 and / or（无法静态判定优先级）：{text!r}"
        )

    if has_and:
        parts = re.split(r"\s+and\s+", s)
        connector = "and"
    elif has_or:
        parts = re.split(r"\s+or\s+", s)
        connector = "or"
    else:
        parts = [s]
        connector = None

    terms: list[Comparison] = []
    for p in parts:
        m = _TERM_RE.match(p)
        if not m:
            raise PredicateError(
                f"predicate 片段格式非法: {p!r}。"
                f"允许的形式是 `<feature> <op> <literal>`；"
                f"op ∈ {list(_OPS)}，literal ∈ true/false/数字，"
                f"连接词只允许 and 或 or（不可混用、不可加括号）。"
            )
        feat, op, raw = m.group(1), m.group(2), m.group(3)
        terms.append(Comparison(feat, op, _parse_literal(raw)))

    if not terms:
        raise PredicateError(f"predicate 未解析出任何比较项: {text!r}")
    return ParsedPredicate(tuple(terms), connector)


def _compare(left: Any, op: str, right: Any) -> bool:
    # 类型不匹配时给清晰错误，而不是让 Python 抛 TypeError
    if isinstance(right, bool):
        if not isinstance(left, bool):
            raise PredicateError(
                f"布尔字面量 {right!r} 只能与布尔特征比较，"
                f"但特征值是 {left!r}（{type(left).__name__}）"
            )
    else:
        if isinstance(left, bool):
            raise PredicateError(
                f"数值字面量 {right!r} 不能与布尔特征值 {left!r} 比较"
            )
        if not isinstance(left, (int, float)):
            raise PredicateError(
                f"特征值 {left!r}（{type(left).__name__}）不是数值，无法与 {right!r} 比较"
            )

    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    raise PredicateError(f"未知运算符 {op!r}")


def eval_predicate(
    text: str,
    features: dict[str, Any],
    *,
    declared: list[str] | None = None,
) -> bool:
    """在已求出的特征字典上求值 predicate。

    `declared` 非空时，会先检查 predicate 引用的每个特征都在其中 ——
    这是**引用完整性检查**，把「引用了不存在的特征」变成显式错误。
    """
    parsed = parse_predicate(text)

    if declared is not None:
        unknown = [f for f in parsed.features() if f not in declared]
        if unknown:
            raise PredicateError(
                f"predicate 引用了未声明的特征 {unknown}。"
                f"已声明：{', '.join(declared)}。"
                f"（若该特征描述的是**跨注**性质如组合分散度，"
                f"那它不属于单注层 —— 见 apply_scope）"
            )

    results: list[bool] = []
    for t in parsed.terms:
        if t.feature not in features:
            raise PredicateError(
                f"特征 {t.feature!r} 没有值（可能只有 formula、没有 primitive，"
                f"或求值时被跳过）。已求出的特征：{', '.join(sorted(features))}"
            )
        results.append(_compare(features[t.feature], t.op, t.literal))

    if parsed.connector == "and":
        return all(results)
    if parsed.connector == "or":
        return any(results)
    return results[0]


# ---------------------------------------------------------------- 判定

class JudgeResult(NamedTuple):
    """对一注号码、一组规则的判定结果。"""

    excluded: bool
    required_failed: bool
    weight: float
    matched: list[str]          # 命中的规则 id
    actions: dict[str, str]     # rule_id → action
    features: dict[str, Any]    # 已求出的特征（便于调试）

    @property
    def passes(self) -> bool:
        """是否通过全部规则（未被 exclude、无 require 未满足）。"""
        return not self.excluded and not self.required_failed

    def explain(self) -> str:
        if self.passes:
            return f"通过（命中权重 {self.weight:.3f}，命中规则 {self.matched or '无'}）"
        reasons = []
        if self.excluded:
            hit = [m for m in self.matched if self.actions.get(m) == ACTION_EXCLUDE]
            reasons.append(f"被排除（规则 {hit}）")
        if self.required_failed:
            hit = [m for m in self.matched if self.actions.get(m) == ACTION_REQUIRE]
            reasons.append(f"未满足必需条件（规则 {hit}）")
        return "；".join(reasons)


def judge(
    cfg: dict[str, Any],
    ticket: Ticket,
    rules: list[dict[str, Any]],
) -> JudgeResult:
    """按规则集判定一注号码。

    规则来自 `strategy.json` 的 `rules[]`，每条含：
        {id, machine_rule: {predicate, action, weight}}

    action 语义：
        exclude   命中 predicate → 直接排除
        require   未命中 predicate → 判定不通过
        penalize  命中 predicate → 权重乘 weight（默认 0.5）
        prefer    命中 predicate → 权重乘 1/weight（默认 0.5 → ×2）

    权重从 1.0 起算，按命中顺序累乘。
    """
    declared = [f["key"] for f in (cfg.get("features") or [])]

    try:
        feats = evaluate(cfg, ticket)
    except EvaluateError as e:
        raise PredicateError(f"特征求值失败: {e}") from e

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
                f"规则 {rid} 的 action={action!r} 非法，"
                f"只允许 {sorted(VALID_ACTIONS)}"
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


# ---------------------------------------------------------------- 作用域

def split_by_scope(
    rules: list[dict[str, Any]],
    declared: list[str],
    cross_declared: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """把规则按**作用域**分成两组：

        (single, cross) = split_by_scope(rules, declared, cross_declared)

    · `single` —— predicate 引用的特征**全部**在 `declared`（单注声明）里
                   → 单注层可判定（`judge()`）
    · `cross`  —— 引用了 `cross_declared` 里的特征（**已知跨注**）、
                  或引用了两边都没声明的特征（**未声明**，可能是拼错）
                   → 单注层判定不了

    `cross_declared` 为 `None` 时退化为旧行为（未声明即 cross），
    以保持 config_version 2.0 的兼容。

    ## 为什么需要这个函数

    真实案例：`strategy.json` 的 R-002 用的是
        `duplicated_structure_across_tickets == true`
    这个特征**不可能**从一注号码算出来 —— 它需要一"组"注。

    若无本函数，`judge()` 会在遇到 R-002 时抛错，**连带 R-001 也用不了**。
    有了它，单注层可以只执行自己管得着的那部分，并把管不着的
    **显式上报**（而非静默忽略 —— 静默忽略正是本仓库要防的那类错误）。

    ## ★ 从 2.0 到 2.1 的变化

    2.0 里 `cross` 只意味着"单注层管不着"，**没有任何地方能执行它** ——
    于是 R-002 成了"对外输出了却执行不了"的规则。
    2.1 起，`game.yaml` 可以显式声明 `scope: cross` 的特征，
    跨注规则由 `portfolio.judge_cross()` 在**整组上下文**里真正执行。
    用 `classify_rules()` 可以把"已知跨注"与"未声明"分开。
    """
    known_single = set(declared or [])
    known_cross = set(cross_declared or [])
    single: list[dict[str, Any]] = []
    cross: list[dict[str, Any]] = []
    for r in rules:
        mr = r.get("machine_rule") or {}
        p = mr.get("predicate")
        if not p:
            continue
        try:
            feats = parse_predicate(p).features()
        except PredicateError:
            cross.append(r)       # 无法解析 → 不归单注层
            continue
        if any(f in known_cross for f in feats):
            cross.append(r)       # 显式声明的跨注特征 → 需整组上下文
        elif all(f in known_single for f in feats):
            single.append(r)
        else:
            cross.append(r)       # 两边都没声明 → 拼错或漏声明
    return single, cross


class RuleScopes(NamedTuple):
    """规则的三分：`single` / `cross`（已声明跨注）/ `undeclared`（未声明）。

    ★ `cross` 与 `undeclared` 的区分是本层的关键：
      · `cross`      → 可以用 `judge_cross()` 在整组上**真正执行**
      · `undeclared` → 谁都执行不了，是配置缺陷（拼错 / 漏声明）
    二者混在一起时，前者会被后者的"执行不了"掩盖。
    """

    single: list[dict[str, Any]]
    cross: list[dict[str, Any]]
    undeclared: list[dict[str, Any]]


def classify_rules(cfg: dict[str, Any], rules: list[dict[str, Any]]) -> RuleScopes:
    """按 `game.yaml` 的 `scope` 声明把规则**三分**。"""
    single_keys = [f["key"] for f in (cfg.get("features") or [])
                   if (f.get("scope") or "single") == "single"]
    cross_keys = [f["key"] for f in (cfg.get("features") or [])
                  if f.get("scope") == "cross"]
    ks, kc = set(single_keys), set(cross_keys)

    single: list[dict[str, Any]] = []
    cross: list[dict[str, Any]] = []
    undeclared: list[dict[str, Any]] = []
    for r in rules:
        mr = r.get("machine_rule") or {}
        p = mr.get("predicate")
        if not p:
            continue
        try:
            feats = parse_predicate(p).features()
        except PredicateError:
            undeclared.append(r)
            continue
        if any(f in kc for f in feats):
            cross.append(r)
        elif all(f in ks for f in feats):
            single.append(r)
        else:
            undeclared.append(r)
    return RuleScopes(single, cross, undeclared)


def apply_scope(
    cfg: dict[str, Any],
    rules: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """`split_by_scope` 的便捷版：自动取 cfg 的声明特征。

    ★ 2.1 起会传 `cross_declared`：已知跨注特征不再被当成"未声明"。
    """
    s = classify_rules(cfg, rules)
    return s.single, (s.cross + s.undeclared)


def score(cfg: dict[str, Any], ticket: Ticket, rules: list[dict[str, Any]]) -> float:
    """给一注号码打分（越高越好）。

    ⚠️ 这个分数**不代表中奖概率**，也不代表期望回报。
    它只反映「这注号码与规则集的契合度」：
      · 被 exclude 命中 → 0.0
      · require 未满足   → 0.0
      · 否则             → 权重（penalize/prefer 的累乘结果）

    ⚠️ 只对**单注层**规则计分；跨注规则（如 R-002）自动跳过。
    """
    single, _ = apply_scope(cfg, rules)
    r = judge(cfg, ticket, single)
    if not r.passes:
        return 0.0
    return r.weight
