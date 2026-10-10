# -*- coding: utf-8 -*-
"""smartpickcore.core — 框架计算核心（**彩种无关**）

## 本包的铁律

```
✗ 禁止出现号码池常量（35 / 12 / 5 / 2…）
✗ 禁止出现彩种标识（"dlt" / "大乐透"）
✗ 禁止出现区名字符串（"front" / "back"）
✗ 禁止出现该彩种特有的特征名（"has_run_ge2" / "adjacent_pairs"）
✓ 只从传入的 cfg（= game.yaml 解析结果）读取参数
```

`src/smartpickcore/game.py` 已在做「由 `machine.zones` 机械算 T」。
本包把同一思路**从号码空间级下沉到单注级**：

```
号码空间级    machine.zones  →  compute_space()  →  T, 一等奖概率
单注级        machine.zones  →  Ticket           →  一注号码是否合法
              features[]     →  evaluate()       →  这注的特征值
              rules[].machine_rule               →  judge() 判定
```

## 模块

| 模块 | 职责 |
|---|---|
| `features`   | 特征**原语库**（纯数学函数：sum / span / adjacent_pair_count …） |
| `game_util`  | 由 `machine` 与 `features` 段驱动的**基础计算与静态检查** |
| `ticket`     | `Ticket` —— 一注号码（**不写死区名**） |
| `evaluate`   | 按 `features[]` 声明**机械求值**一注号码的全部特征 |
| `judge`      | `machine_rule.predicate` 的**受限 DSL** 解析与求值 + 规则判定 |
| `generate`   | **通用号码生成器**（均匀 / 拒绝采样 / 结构分散） |

## 依赖方向

```
cli/  →  src/smartpickcore/  →  framework/core/  →  (stdlib)
                                      ↑
                          games/<id>/game.yaml（仅作数据输入）
```

`framework/core/` **不得 import `games/` 下的任何 Python 代码**。
"""
from __future__ import annotations

__all__ = [
    # features
    "PrimitiveError",
    "PRIMITIVES",
    "list_primitives",
    "resolve_primitive",
    "arity_of",
    "apply_primitive",
    # game_util
    "GameUtilError",
    "zones_of",
    "zone_keys",
    "zone_by_key",
    "max_value_of_zone",
    "total_combinations",
    "first_prize_probability",
    "declared_features",
    "feature_by_key",
    "feature_keys",
    "validate_feature_declarations",
    # ticket
    "Ticket",
    "TicketError",
    "ticket_from_any",
    # evaluate
    "EvaluateError",
    "evaluate",
    "evaluate_one",
    "evaluable_features",
    # judge
    "PredicateError",
    "Comparison",
    "ParsedPredicate",
    "parse_predicate",
    "eval_predicate",
    "JudgeResult",
    "judge",
    "score",
    "VALID_ACTIONS",
    # generate
    "GenerateError",
    "GenerateResult",
    "sample_uniform",
    "sample_filtered",
    "sample_batch",
    "spread_penalty",
]

from .evaluate import (  # noqa: E402
    EvaluateError,
    evaluate,
    evaluate_one,
    evaluable_features,
)
from .features import (  # noqa: E402
    PRIMITIVES,
    PrimitiveError,
    apply_primitive,
    arity_of,
    list_primitives,
    resolve_primitive,
)
from .game_util import (  # noqa: E402
    GameUtilError,
    declared_features,
    feature_by_key,
    feature_keys,
    first_prize_probability,
    max_value_of_zone,
    total_combinations,
    validate_feature_declarations,
    zone_by_key,
    zone_keys,
    zones_of,
)
from .generate import (  # noqa: E402
    GenerateError,
    GenerateResult,
    sample_batch,
    sample_filtered,
    sample_uniform,
    spread_penalty,
)
from .judge import (  # noqa: E402
    VALID_ACTIONS,
    Comparison,
    JudgeResult,
    ParsedPredicate,
    PredicateError,
    eval_predicate,
    judge,
    parse_predicate,
    score,
)
from .ticket import Ticket, TicketError, ticket_from_any  # noqa: E402
