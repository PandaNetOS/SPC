# CONSUMING —— 其他工具如何消费本仓库的输出

本仓库对外的**唯一稳定契约**是 `games/<id>/strategy/strategy.json`。
其他工具（选号器、App、机器人、插件）只读这一个文件，不读本仓库其他任何内容。

## 1. 契约位置

```
games/<id>/strategy/strategy.json     受 spec/strategy.schema.json 约束
```

- `spec/strategy.schema.json` —— 结构定义
- `spec/VERSIONING.md` —— 版本兼容规则

## 2. 稳定性承诺

| 版本字段 | 变更影响 | 消费方应对 |
|---|---|---|
| `schema_version` 主版本 | **破坏性** | 必须同步升级；主版本不匹配应拒绝加载 |
| `schema_version` 次版本 | 向后兼容（新增可选字段） | 忽略未知字段即可 |
| `config_version` | 彩种参数变更 | 一般不影响消费逻辑 |
| `generated_at` | 每次重建都变 | 不要用它做缓存键（用 `schema_version` + `game`） |

**主版本不匹配时的行为**：库的 `load_strategy(strict=True)` 会抛错。
消费方应当**拒绝**而不是猜测。

## 3. 文件结构概要

```jsonc
{
  "schema_version": "1.0",
  "game": "dlt",

  "disclaimer": {
    "affects_win_probability": false,     // 恒 false（红线）
    "changes_win_probability": false,     // 恒 false（红线）
    "text": "...",
    "responsibility": "..."
  },

  "boundary": {
    "total_combinations": 21425712,
    "first_prize_probability": 4.667289469773513e-08,
    "return_rate": 0.51,
    "net_expectation_per_yuan": -0.98,
    "optimizable_target": "expected_bonus_given_win"   // 枚举里没有 win_probability
  },

  "rules": [
    {
      "id": "R-001",
      "kind": "avoid",
      "description": "...",
      "machine_rule": {
        "action": "exclude",              // exclude|penalize|prefer|require
        "predicate": "has_run_ge2 == true",
        "features": ["has_run_ge2"],
        "params": { "weight": 0.5 }
      },
      "expected_effect": {
        "metric": "bonus_multiplier_given_win",
        "magnitude_pct": 121.48,
        "ci95": [0.4487, 0.4543],
        "confidence": 3,
        "evidence_refs": ["F-0003", "F-0004"]
      },
      "caveats": ["..."]
    }
  ],

  "avoid_list": [
    { "id": "A-001", "practice": "...", "reason": "...", "evidence_refs": [] }
  ],

  "evidence_index": {
    "F-0003": { "claim": "...", "category": "...", "confidence": 4, "status": "established" }
  }
}
```

## 4. 四条红线（消费方必须自己再检查一次）

即使本仓库已经强制过，消费方**也应独立校验**，因为文件可能被手工改过：

1. `disclaimer.affects_win_probability` **必须** 是 `false`
2. `disclaimer.changes_win_probability` **必须** 是 `false`
3. `boundary.optimizable_target` **必须** 是 `"expected_bonus_given_win"`
4. 若要展示 `avoid_list`，其中的"reason"不得被改写成"能提高中奖率"

第 4 条特别重要：`avoid_list` 里的 A-008 明确写着
**"误读为提高中奖率"** — 这是历史高频误读，必须原样传递。

## 5. 消费示例（Python）

```python
import json, sys

def load(games_root: str, game: str, strict: bool = True) -> dict:
    with open(f"{games_root}/{game}/strategy/strategy.json", encoding="utf-8") as f:
        s = json.load(f)

    # 1) 主版本匹配
    major = s["schema_version"].split(".")[0]
    if strict and major != "1":
        raise RuntimeError(f"不支持的 schema 主版本: {s['schema_version']}")

    # 2) 红线自检
    assert s["disclaimer"]["affects_win_probability"] is False, "红线违反：①"
    assert s["disclaimer"]["changes_win_probability"] is False, "红线违反：②"
    assert s["boundary"]["optimizable_target"] == "expected_bonus_given_win", "红线违反：③"

    return s
```

本仓库提供等价实现：`from smartpickcore.strategy import load_strategy`。

## 6. 如何用规则做选号

`machine_rule.action` 的四种取值：

| action | 含义 | 消费方应做 |
|---|---|---|
| `exclude` | 命中 predicate 的组合**直接排除** | 从候选池删除 |
| `penalize` | 降权（`params.weight`） | 在打分里乘权重 |
| `prefer` | 加权 | 在打分里乘权重 |
| `require` | 必须满足 | 只保留命中的 |

### 6.1 求值器：本仓库提供参考实现

`predicate` 采用**受限 DSL**，语法在 `spec/strategy.schema.json` 里用 `pattern`
**结构性约束**（非法表达式在校验阶段就被拒收）：

```
<feature_key> <op> <literal>          例：has_run_ge2 == true
term1 and term2 and term3             同连接词，可多个
term1 or term2                        不可与 and 混用
```

不支持：括号、嵌套、`not`、右侧非字面量。

**本仓库提供参考求值器**（`framework/core/judge.py`）：

```python
from core.judge import judge, split_by_scope, apply_scope

result = judge(cfg, ticket, rules)     # 自动只跑单注层规则
result.passes                          # bool
result.excluded                        # 被 exclude 命中的规则 id
result.weight                          # penalize/prefer 累计权重
result.explain()                       # 人类可读的判定解释
```

消费方**可以**自实现（DSL 语法简单，且 schema 已约束），
但**不再必须** —— 这是相对早期版本（"不提供求值器"）的立场变更。

> **变更原因**：受限 DSL 使求值语义**可被唯一确定**。既然语法只有 6 种比较算子、
> 不支持嵌套，那么"求值语义属于消费方"这一理由就不再成立。
> 提供参考实现反而能减少各消费方的口径漂移。

### 6.2 ★ 作用域：单注层 vs 跨注层

部分规则的 `predicate` 引用了**跨注特征**（例如 R-002 的
`duplicated_structure_across_tickets`）—— 这类特征**一注号码算不出来**。

消费方必须显式区分：

```python
single, cross = apply_scope(cfg, rules)
# single: 全部特征已声明 —— 单注层可正常判定
# cross:  引用了未声明特征 —— 必须显式处理，不可静默忽略
```

| 处理 | 说明 |
|---|---|
| `single` 层 | 逐注判定，用于筛号 / 打分 |
| `cross` 层 | 需要**多注上下文**（如整组号码的结构分散度）。若你的工具只处理单注，应**明确告知用户"该规则未生效"**，而不是假装它通过了 |

**这是本仓库明确禁止的失败模式**：静默忽略跨注规则，会让用户以为
"已按全部规则选号"，实际只应用了一部分。

### 6.3 特征定义

`features` 数组列出该规则引用了哪些特征。特征定义见
`games/<id>/game.yaml` 的 `features[]`，**从 `config_version: "2.0"` 起为
`primitive` + `args` 形式**（而非早期只有注释意义的 `formula` 字符串）：

```yaml
- key: has_run_ge2
  primitive: adjacent_pair_count_ge
  args: {zone: front, threshold: 2}
```

`primitive` 是框架注册表中的纯数学函数（21 个，见
`framework/core/README.md`），消费方可直接调用 `apply_primitive()`，
无需自己复现数学。

## 7. 绝对不要做的事

| 禁止 | 原因 |
|---|---|
| 把 `avoid_list` 说成"提高中奖率的技巧" | 事实相反（红线 4） |
| 用 `rules` 生成"必中号码" | 中奖概率恒 4.667e-08，不可改变 |
| 忽略 `caveats` 直接展示 `magnitude_pct` | 数字有减损项，单看会误导 |
| 跨 `rules_epoch` 比较奖金数字 | 规则变更过 6 次（教训 L9） |
| 用 `generated_at` 做缓存键 | 每次重建都变 |
| **静默忽略跨注层规则** | 会让用户以为"全部规则已生效"（见 §6.2） |
| **只展示单注层规则却不说 R-002 未生效** | R-002 是跨注规则，必须显式告知 |

## 8. 减损项（caveats）的处理

`expected_effect.caveats` **非空是强制的**。消费方展示 `magnitude_pct` 时：

- **必须**同时可让用户看到 caveats（至少提供入口）
- 若界面空间实在不足，**不要展示 `magnitude_pct`**，只展示规则本身与免责声明

这是"宁可少说，不可误导"。

## 9. 版本升级流程（消费方视角）

1. 读 `spec/VERSIONING.md` 的变更日志
2. 主版本变了 → 检查自己解析的每个字段
3. 跑 `python cli/main.py validate --game <id>` 确认仓库侧无误
4. 用 `tests/` 里的契约测试样例做回归（若有）
