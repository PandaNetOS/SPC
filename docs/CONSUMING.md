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

**`predicate` 是给人看的字符串，不是可执行表达式。**
消费方必须自己实现求值逻辑 —— 本仓库**故意不提供**求值器，
因为求值语义应属于消费方，而本仓库只能承诺"规则是什么"。

`features` 数组列出该规则引用了哪些特征，特征定义见
`games/<id>/game.yaml` 的 `features[]`（`formula` 字段说明怎么算）。

## 7. 绝对不要做的事

| 禁止 | 原因 |
|---|---|
| 把 `avoid_list` 说成"提高中奖率的技巧" | 事实相反（红线 4） |
| 用 `rules` 生成"必中号码" | 中奖概率恒 4.667e-08，不可改变 |
| 忽略 `caveats` 直接展示 `magnitude_pct` | 数字有减损项，单看会误导 |
| 跨 `rules_epoch` 比较奖金数字 | 规则变更过 6 次（教训 L9） |
| 用 `generated_at` 做缓存键 | 每次重建都变 |

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
