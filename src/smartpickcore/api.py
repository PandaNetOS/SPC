# -*- coding: utf-8 -*-
"""smartpickcore.api — 高层门面

面向两类用户的统一入口：

  外部消费者（选号器 / 前端 / 其他 Agent）：
      sp = SmartPick.for_game("dlt")
      sp.boundary()          # 数学边界（可校验的定量框架）
      sp.strategy()          # 策略规则集（受 schema 约束）
      sp.disclaimer()        # 免责声明（必须原样展示）

      # 单注层（framework/core）
      sp.evaluate({"front": [...], "back": [...]})   # 求一注的特征
      sp.judge(ticket)                               # 按规则判定（单注层）
      sp.pick(n=5)                                   # 生成合规号码
      sp.spread(tickets)                             # 多注分散度（未量化，启发式）

      # 跨注层（L3，需整组号码）
      sp.rule_scopes()                               # 哪些规则是单注、哪些是跨注
      sp.evaluate_portfolio([t1, t2, ...])           # 求注与注之间的特征
      sp.judge_portfolio([t1, t2, ...])              # 执行跨注规则（如 R-002）

  本仓库的 AI 分析者：
      sp = SmartPick.for_game("dlt")
      sp.facts()             # 结论台账
      sp.open_questions()    # 待解问题
      sp.lessons()           # 教训（动手前必读）
      sp.validate()          # 校验全部契约
"""
from __future__ import annotations

import os
import sys
from typing import Any

from .game import compute_space, feature_keys, list_games, load_game_config
from .memory import Memory
from .strategy import load_strategy
from .validate import validate_all

# framework/core 是彩种无关的计算核心，不在 src/ 包内 —— 补进 import 路径
_FRAMEWORK = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "framework")
)
if _FRAMEWORK not in sys.path:
    sys.path.insert(0, _FRAMEWORK)

from core import (  # noqa: E402
    EvaluateError,
    GenerateError,
    JudgeResult,
    Portfolio,
    PredicateError,
    Ticket,
    TicketError,
    evaluable_cross_features,
    evaluable_features,
    evaluate,
    evaluate_cross,
    judge,
    judge_cross,
    portfolio_from_any,
    sample_batch,
    spread_penalty,
    ticket_from_any,
)
from core.judge import apply_scope, classify_rules  # noqa: E402

__all__ = ["SmartPick"]

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SmartPick:
    """某彩种的统一访问门面。"""

    def __init__(self, game: str, repo_root: str | None = None):
        self.game = game
        self.root = repo_root or _ROOT
        self._cfg: dict | None = None
        self._mem: Memory | None = None

    # -------------------------------------------------- 构造

    @classmethod
    def for_game(cls, game: str, repo_root: str | None = None) -> "SmartPick":
        root = repo_root or _ROOT
        if game not in list_games(root):
            raise ValueError(
                f"彩种 {game!r} 不存在。可用: {list_games(root)}"
            )
        return cls(game, root)

    @classmethod
    def games(cls, repo_root: str | None = None) -> list[str]:
        return list_games(repo_root or _ROOT)

    # -------------------------------------------------- 配置

    @property
    def config(self) -> dict[str, Any]:
        if self._cfg is None:
            self._cfg = load_game_config(self.game, self.root)
        return self._cfg

    @property
    def memory(self) -> Memory:
        if self._mem is None:
            self._mem = Memory(self.root)
        return self._mem

    # -------------------------------------------------- 外部消费者接口

    def boundary(self) -> dict[str, Any]:
        """数学边界：单注组合总数、一等奖概率、返奖率、唯一可优化量。

        ★ 这是消费者必须读取的第一项 —— 用可校验的数字告诉它
          "本策略能影响什么、不能影响什么"。
        """
        sp = compute_space(self.config)
        rr = (self.config.get("prize_model") or {}).get("return_rate", 0.51)
        return {
            "game": self.game,
            "total_combinations": sp["total_combinations"],
            "first_prize_probability": sp["first_prize_probability"],
            "return_rate": rr,
            "net_expected_per_2yuan": round(2.0 * rr - 2.0, 4),
            "optimizable_target": "expected_bonus_given_win",
            "zones": sp["zones"],
            "note": (
                "E[回报] = Σ_j P(命中奖级 j) × 该奖级总奖金池 / 中奖注数。"
                "P_j 由号码空间决定、与选号无关；只有『中奖注数』可被选号影响。"
                "因此策略只作用于中奖时的奖金，不作用于中奖概率。"
            ),
        }

    def strategy(self, strict: bool = True) -> dict[str, Any]:
        """读策略规则集。**已通过红线检查**。"""
        return load_strategy(self.game, self.root, strict=strict)

    def disclaimer(self) -> dict[str, Any]:
        """免责声明。消费者**必须原样展示** text 字段。"""
        return self.strategy()["disclaimer"]

    def rules(self) -> list[dict]:
        return self.strategy().get("rules", [])

    def avoid_list(self) -> list[dict]:
        return self.strategy().get("avoid_list", [])

    def features(self) -> list[str]:
        """可算特征 key（machine_rule.predicate 只能引用这些）。"""
        return feature_keys(self.config)

    # -------------------------------------------------- 单注层（framework/core）

    def evaluable_features(self) -> list[str]:
        """**可执行**的特征 key（声明了 primitive 的那些）。"""
        return evaluable_features(self.config)

    def evaluate(self, ticket: Any) -> dict[str, Any]:
        """求一注号码的全部可执行特征。

        接受 Ticket / {"front": [...], "back": [...]} / {"front": "03 11 ..."}
        """
        t = ticket_from_any(ticket)
        return evaluate(self.config, t)

    def judge(self, ticket: Any) -> JudgeResult:
        """按**单注层**规则判定一注号码。

        ⚠️ 跨注层规则（scope=cross，如 R-002 的组合分散度）不在此判定 ——
        它们需要一整组注。**用 `judge_portfolio()` 执行它们**，
        用 `rule_scopes()` 查哪些是跨注规则。
        """
        t = ticket_from_any(ticket)
        single, _ = apply_scope(self.config, self.rules())
        return judge(self.config, t, single)

    def judge_scoped(
        self, ticket: Any, rules: list[dict] | None = None
    ) -> JudgeResult:
        """按**给定规则集**判定（不做作用域切分）。

        传混合规则集会明确报错（而不是静默忽略）—— 这是刻意的。
        """
        t = ticket_from_any(ticket)
        return judge(self.config, t, rules if rules is not None else self.rules())

    def rule_scopes(self) -> dict[str, Any]:
        """规则的**作用域三分**。

        {
          "single":     ["R-001"],   # 单注可判 → sp.judge(ticket)
          "cross":      ["R-002"],   # 需整组   → sp.judge_portfolio([tickets])
          "undeclared": [],          # ★ 谁都执行不了（拼错/漏声明）= 配置缺陷
          "cross_reasons": {...}
        }

        ★ 契约 1.1 起 `cross` 与 `undeclared` 分开：
        1.0 时代二者混为一谈，于是 R-002 被归到"跨注"后**没有任何入口能执行它**
        —— 消费者拿到策略却用不了。`undeclared` 现在是明确的错误信号。
        """
        scopes = classify_rules(self.config, self.rules())
        reasons: dict[str, str] = {}
        for r in scopes.cross:
            p = (r.get("machine_rule") or {}).get("predicate", "")
            reasons[r.get("id", "?")] = (
                f"predicate `{p}` 引用了跨注特征；"
                f"整组号码上用 judge_portfolio() 执行"
            )
        for r in scopes.undeclared:
            p = (r.get("machine_rule") or {}).get("predicate", "")
            reasons[r.get("id", "?")] = f"predicate `{p}` 引用了未声明特征"
        return {
            "single": [r["id"] for r in scopes.single],
            "cross": [r["id"] for r in scopes.cross],
            "undeclared": [r["id"] for r in scopes.undeclared],
            "cross_reasons": reasons,
        }

    # -------------------------------------------------- 跨注层（framework/core/portfolio）

    def evaluable_cross_features(self) -> list[str]:
        """可执行的**跨注**特征 key（scope=cross 且声明了 primitive）。"""
        return evaluable_cross_features(self.config)

    def evaluate_portfolio(self, tickets: Any) -> dict[str, Any]:
        """求**一组注**的全部跨注特征。

        接受 Ticket 列表 / dict 列表 / Portfolio。
        ⚠️ 这些量描述的是注与注之间的关系，**一注号码算不出来**。
        """
        pf = portfolio_from_any(tickets, self.config)
        return evaluate_cross(self.config, pf)

    def judge_portfolio(self, tickets: Any) -> JudgeResult:
        """按**跨注层**规则判定一组注（如 R-002 的组合分散度）。

        这是契约 1.1 补上的一层：1.0 时代跨注规则只能被"上报跳过"，
        消费者**没有任何办法执行 R-002**。

        ⚠️ 判定结果只反映"这组注与跨注规则的契合度"。
        跨注规则**不影响期望中奖注数**（恒为 N/T），只影响方差。
        """
        pf = portfolio_from_any(tickets, self.config)
        scopes = classify_rules(self.config, self.rules())
        if not scopes.cross:
            return judge_cross(self.config, pf, [])
        return judge_cross(self.config, pf, scopes.cross)

    def pick(
        self,
        n: int = 1,
        *,
        seed: int | None = None,
        use_rules: bool = True,
        spread: bool = True,
    ) -> Any:
        """生成 n 注合规号码。

        ⚠️ **本方法不改变中奖概率**（恒为 1/T）。它只保证产出的号码
        满足单注层规则（如避开连号）。

        返回 core.generate.GenerateResult（含 tickets / attempts / stats）。
        """
        rules = self.rules() if use_rules else []
        return sample_batch(
            self.config, rules, n=n, seed=seed, spread=spread
        )

    def spread(self, tickets: list[Any]) -> float:
        """一组注的**结构分散度惩罚**（0 = 完全分散，1 = 完全同构）。

        ⚠️ **未量化**（R-002 的 magnitude_pct 是 null）。
        ⚠️ 与期望中奖注数**无关**（恒为 N/T，线性）。
        """
        ts = [ticket_from_any(t) for t in tickets]
        return spread_penalty(self.config, ts)

    # -------------------------------------------------- 分析者接口

    def facts(self, **kw) -> list[dict]:
        return self.memory.facts_by(**kw) if kw else self.memory.load_facts()

    def fact(self, fact_id: str) -> dict | None:
        return self.memory.fact(fact_id)

    def open_questions(self) -> list[tuple]:
        return self.memory.open_questions()

    def lessons_header(self) -> str:
        """返回教训库的相对路径（AI 应自行读取 —— 本库不解析 markdown）。"""
        return "memory/lessons/LESSONS.md"

    def best_reference(self) -> str:
        """给 AI 的单一入口提示。"""
        return "AI_CONTEXT.md"

    # -------------------------------------------------- 校验

    def validate(self) -> Any:
        return validate_all(self.root)

    # -------------------------------------------------- 展示

    def __repr__(self) -> str:
        return f"<SmartPick game={self.game!r} root={self.root!r}>"

    def summary(self) -> str:
        """一行摘要，便于 CLI 打印。"""
        sp = compute_space(self.config)
        rr = (self.config.get("prize_model") or {}).get("return_rate", 0.51)
        st_path = os.path.join(
            self.root, "games", self.game, "strategy", "strategy.json"
        )
        has_st = os.path.exists(st_path)
        n_rules = 0
        if has_st:
            try:
                n_rules = len(self.strategy(strict=False).get("rules", []))
            except Exception:
                n_rules = -1
        n_facts = len(
            [f for f in self.facts() if f.get("game") in (self.game, "global")]
        )
        return (
            f"{self.game:8s}  T={sp['total_combinations']:>11,}  "
            f"p1={sp['first_prize_probability']:.3e}  rr={rr:.2f}  "
            f"facts={n_facts:>3}  rules={n_rules}"
        )
