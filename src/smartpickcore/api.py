# -*- coding: utf-8 -*-
"""smartpickcore.api — 高层门面

面向两类用户的统一入口：

  外部消费者（选号器 / 前端 / 其他 Agent）：
      sp = SmartPick.for_game("dlt")
      sp.boundary()          # 数学边界（可校验的定量框架）
      sp.strategy()          # 策略规则集（受 schema 约束）
      sp.disclaimer()        # 免责声明（必须原样展示）

  本仓库的 AI 分析者：
      sp = SmartPick.for_game("dlt")
      sp.facts()             # 结论台账
      sp.open_questions()    # 待解问题
      sp.lessons()           # 教训（动手前必读）
      sp.validate()          # 校验全部契约
"""
from __future__ import annotations

import os
from typing import Any

from .game import compute_space, feature_keys, list_games, load_game_config
from .memory import Memory
from .strategy import load_strategy
from .validate import validate_all

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
