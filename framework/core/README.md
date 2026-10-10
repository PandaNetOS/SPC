# framework/core/ — 框架核心（已实现）

> **本目录存放彩种无关的计算核心。** 它从 `games/<id>/game.yaml` 读取参数，
> 不硬编码任何具体彩种的数值。
>
> **状态：已实现（config_version 2.0 起）。** 共 6 个模块，21 个原语。

## 模块清单

| 模块 | 职责 | 关键接口 |
|---|---|---|
| `features.py` | **特征原语库**。纯数学函数，签名统一为 `(zone, **args) -> int\|bool` | `PRIMITIVES`（21 个）、`apply_primitive(name, zone_values, args)`、`list_primitives()`、`resolve_primitive()` |
| `game_util.py` | 由 `machine` / `features` 段驱动的**纯计算** | `total_combinations(cfg)`、`first_prize_probability(cfg)`、`zones_of(cfg)`、`validate_feature_declarations(cfg)` |
| `ticket.py` | **`Ticket` 一等公民** —— 一注号码 | `Ticket(zones)`、`from_any()`、`validate(cfg)`、`replace_zone()`、`render()`、可哈希可比较 |
| `evaluate.py` | 按 `features[]` 声明**机械求值** | `evaluate(cfg, ticket)`、`evaluate_one(cfg, ticket, key)`、`evaluable_features(cfg)` |
| `judge.py` | **受限 DSL 解析 + 规则判定 + 作用域切分** | `parse_predicate(text)`、`eval_predicate()`、`judge(cfg, ticket, rules)`、`split_by_scope()`、`apply_scope()`、`score()` |
| `generate.py` | **通用生成器**（拒绝采样 + 结构分散） | `sample_batch(cfg, rules, n, seed)`、`sample_filtered()`、`SampleResult.stats`、`spread_penalty()` |
| `__init__.py` | 汇总 re-export | 上述全部接口 + `__all__` |

## 三层架构

```
L1 Ticket 层      Ticket(zones)                        一注号码。区名来自 machine.zones，不硬编码 front/back
L2 Scoring 层     evaluate → judge → score             求值 / 判定 / 计分。全部为单注可判定
L3 Portfolio 层   generate（只留接口）                  多注组合。跨注规则在此层，本版本仅提供 spread_penalty
```

**关键设计：`Ticket` 不含 `front` / `back` 字段。** 区名是可变长的数组，
来自 `machine.zones`。这是"加入第二个彩种不改 `framework/`"的前提。

## 特征声明形式（config_version 2.0）

`game.yaml` 的 `features[]` **从 `formula` 字符串改为 `primitive` + `args`**：

```yaml
- key: front_sum
  primitive: sum
  args: {zone: front}
  formula: "sum(front)"     # 仅注释，不参与求值
  range: [15, 165]

- key: has_run_ge2
  primitive: adjacent_pair_count_ge
  args: {zone: front, threshold: 2}
```

**为什么不用 `formula` 字符串求值**：`eval` 不可静态验证、可执行任意代码、
且让"声明"与"实现"脱钩。改为原语注册表后，`validate_feature_declarations()`
可以在**不运行任何号码**的情况下判定一份声明是否可执行。

## 受限 DSL（`machine_rule.predicate`）

`spec/strategy.schema.json` 用 `pattern` **结构性拒收**非法表达式：

```
<feature_key> <op> <literal>   （单个比较项）
term1 and term2 and term3      （同连接词，可多个）
term1 or term2                 （不可与 and 混用）
```

| 允许 | 拒绝 |
|---|---|
| `has_run_ge2 == true` | `(a == 1 or b == 2) and c == 3`（括号 + 混用） |
| `front_sum >= 100 and front_sum <= 120` | `front_sum >= back_sum`（右侧非字面量） |
| `count_odd <= 3` | `not has_run_ge2`（不支持取反） |

拒绝的语义是**明确报错**（`PredicateError`），不是"返回 False"。

## 作用域切分（本框架解决的核心缺陷）

**问题**：`R-002` 的 predicate 是 `duplicated_structure_across_tickets == true`
—— 这是**跨注特征**，一注号码**不可能**算出它。若求值时简单 `try/except` 吞掉，
会连带使同一批规则里的 `R-001` 一起失效（静默降级）。

**解决**：`split_by_scope(rules, declared)` 把规则按作用域切开：

| 类别 | 判定 | 处理 |
|---|---|---|
| `single` | 全部特征已在 `game.yaml` 声明 | 单注层正常判定 |
| `cross` | 引用了未声明的特征 | **显式上报**，不被静默忽略 |

`SmartPick.judge()` 自动只跑 `single` 层。
`sample_filtered()` 把跳过的跨注规则写进 `stats["cross_scope_skipped"]`。
`validate_strategy()` 对未声明特征给 **warning**（区分"跨注"与"拼错"）。

> **本仓库原则：跨注规则宁可被显式上报，不可被静默忽略。**

## 关键约束

```
framework/core/ 里禁止出现：
  ✗ 数字 35 / 12 / 5 / 2（号码池参数）
  ✗ 字符串 "dlt" / "大乐透"
  ✗ 特征名如 "adjacent_pairs"（应从 game.yaml 读）
  ✗ 硬编码的概率值（应从 game.yaml 算）

framework/core/ 里应当出现：
  ✓ 从配置读取 machine.zones 并计算 T
  ✓ 按 features 段的 primitive + args 求值
  ✓ 通用的枚举 / 置换检验 / 分散度工具
```

自检命令：

```bash
python cli/main.py validate --all -v     # 含 features 声明可执行性检查
python tests/test_core.py                # 92 项核心测试
```

## 与 `games/<id>/data/tools/` 的关系

| | `framework/core/` | `games/<id>/data/tools/` |
|---|---|---|
| 范围 | 彩种无关通用 | 该彩种专用（含字段口径） |
| 状态 | **已实现** | 已实现 |
| 内容 | 原语 / Ticket / 求值 / 判定 / 生成 | 数据加载、字段口径、该彩种专用分析 |

判定标准：**这段代码换一个彩种能否直接用？**
- 能（只需换配置）→ 属于 `framework/core/`
- 不能（依赖特定字段名/口径）→ 留在彩种目录

## 已知边界

| 项 | 状态 |
|---|---|
| `spread_penalty()` | **未量化**。只返回一个启发式惩罚值，不是统计结论 |
| 撞号权重模型（α = 13.9405） | **未收入 framework**。属于彩种层观测校准，`F-0004` 有记录 |
| L3 组合优化 | **未实现**。仅有 `spread_penalty` 占位 + 跨注规则上报 |
| 奖金封顶（1 亿） | **未纳入** +121.48% 的计算（Q-004，P0 开放） |
