# platform/core/ — 框架核心（已实现）

> **版本**：`1.1` ｜ 轮次 `r03` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **本目录存放彩种无关的计算核心。** 它从 `games/<id>/game.yaml` 读取参数，
> 不硬编码任何具体彩种的数值。
>
> **状态：已实现（config_version 2.0 起）。** 共 7 个模块，**21 个单注原语 + 5 个跨注原语**。

## 模块清单

| 模块 | 职责 | 关键接口 |
|---|---|---|
| `features.py` | **特征原语库**。纯数学函数，签名统一为 `(zone, **args) -> int\|bool` | `PRIMITIVES`（21 个单注）、`CROSS_PRIMITIVES`（5 个跨注，签名 `(groups, **args)`）、`apply_primitive()`、`apply_cross_primitive()`、`list_primitives(scope)`、`resolve_primitive()`、`scope_of()` |
| `game_util.py` | 由 `machine` / `features` 段驱动的**纯计算** | `total_combinations(cfg)`、`first_prize_probability(cfg)`、`zones_of(cfg)`、`validate_feature_declarations(cfg)`、`feature_scope()`、`single_feature_keys()`、`cross_feature_keys()` |
| `ticket.py` | **`Ticket` 一等公民** —— 一注号码 | `Ticket(zones)`、`from_any()`、`validate(cfg)`、`replace_zone()`、`render()`、可哈希可比较 |
| `evaluate.py` | 按 `features[]` 声明**机械求值**（仅单注） | `evaluate(cfg, ticket)`、`evaluate_one(cfg, ticket, key)`、`evaluable_features(cfg)` |
| `judge.py` | **受限 DSL 解析 + 规则判定 + 作用域切分** | `parse_predicate(text)`、`eval_predicate()`、`judge(cfg, ticket, rules)`、`classify_rules()`、`split_by_scope()`、`apply_scope()`、`score()` |
| `portfolio.py` | **`Portfolio` 一等公民 + 跨注层执行路径**（2.1 新增） | `Portfolio(tickets)`、`from_any()`、`evaluate_cross()`、`evaluate_cross_one()`、`judge_cross()`、`score_cross()` |
| `generate.py` | **通用生成器**（拒绝采样 + 结构分散 + 跨注判定） | `sample_batch(cfg, rules, n, seed)`、`sample_filtered()`、`SampleResult.stats`、`spread_penalty()` |
| `__init__.py` | 汇总 re-export | 上述全部接口 + `__all__` |

## 三层架构

```
L1 Ticket 层      Ticket(zones)                        一注号码。区名来自 machine.zones，不硬编码 front/back
L2 Scoring 层     evaluate → judge → score             求值 / 判定 / 计分。全部为单注可判定
L3 Portfolio 层   Portfolio → evaluate_cross            多注组合 ★ 2.1 起已实现
                  → judge_cross → score_cross           跨注规则在此层真正执行
```

**关键设计：`Ticket` 不含 `front` / `back` 字段。** 区名是可变长的数组，
来自 `machine.zones`。这是"加入第二个彩种不改 `platform/`"的前提。
`Portfolio` 同理 —— 它只持有 `tuple[Ticket]`，不认识任何区名。

> **为什么 2.1 必须补 L3**：`config_version 2.0` 里 L3 是空壳，只有 `spread_penalty`
> 一个占位。而 `strategy.json` 的 `R-002` 已引用了一个**从未在任何地方声明**的跨注特征
> `duplicated_structure_across_tickets` —— 消费者拿到策略，却没有任何接口能执行它，
> **契约缺了整整一层**。2.1 补上 `portfolio.py` 后，`R-002` 可在整组上下文里真正判定。

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

## 特征作用域声明（config_version 2.1 新增）

每个特征必须（或默认）声明 `scope`，决定它**在哪一层可算**：

```yaml
- key: front_sum
  primitive: sum
  args: {zone: front}
  # scope 省略 → 默认 "single"

- key: has_duplicated_structure
  type: boolean
  scope: cross                          # ★ 跨注：整组号码才能算
  primitive: duplicate_structure_count_ge
  args: {zone: front, threshold: 1}
```

| `scope` | 输入 | 求值入口 | 原语表 |
|---|---|---|---|
| `single`（默认） | 一注 `Ticket` | `evaluate_one()` / `evaluate()` | `PRIMITIVES`（21 个） |
| `cross` | 整组 `Portfolio` | `evaluate_cross_one()` / `evaluate_cross()` | `CROSS_PRIMITIVES`（5 个） |

**两张原语表分开注册是刻意的**：单注原语签名 `(zone_values, **args)`，
跨注原语签名 `(groups, **args)`，二者**不可互换**。
`validate_feature_declarations()` 会结构性拒收混用 ——
声明 `scope: cross` 却挂单注原语（或反之）直接报错，
错误信息里给出该原语的**真实**作用域。

跨注原语清单（全部为纯结构度量，不含任何彩种数值）：

| 原语 | 返回 | 含义 |
|---|---|---|
| `duplicate_structure_count` | int | 结构签名出现 ≥2 次的注数 |
| `duplicate_structure_count_ge` | bool | 上述计数是否 ≥ `threshold` |
| `distinct_structure_count` | int | 不同结构签名的个数 |
| `coverage_unique_count` | int | 至少被覆盖一次的号码个数 |
| `max_shared_count` | int | 任意两注共享号码数的最大值 |

结构签名取**间隔向量**（gap vector）：`gaps(1,3,5) == gaps(2,4,6) == (2,2)`。
这是刻意设计 —— 号码不同但结构同构的两注，应当被判定为重复结构。

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

**问题**：`R-002` 的 predicate 引用跨注特征，一注号码**不可能**算出它。
2.0 里它既未声明、也无执行入口；若求值时简单 `try/except` 吞掉，
会连带使同一批规则里的 `R-001` 一起失效（静默降级）。

**解决（2.1）**：`classify_rules(cfg, rules)` 把规则**三路**切开，
不再把"已知跨注"与"配置缺陷"混为一谈：

| 类别 | 判定 | 处理 |
|---|---|---|
| `single` | 全部特征已声明且 `scope: single` | 单注层正常判定 |
| `cross` | 引用了 `scope: cross` 的**已声明**特征 | 交给 `judge_cross()` 在整组上下文执行 |
| `undeclared` | 引用了**根本没声明**的特征（拼错 / 遗漏） | **报错**，不是警告 |

`split_by_scope()` / `apply_scope()` 保留为二路切分的兼容入口，内部委托给
`classify_rules()`（`single` vs `cross + undeclared`）。

各消费者的分工：

| 消费者 | 行为 |
|---|---|
| `SmartPick.rule_scopes()` | 返回 `single` / `cross` / `undeclared` / `cross_reasons` |
| `SmartPick.judge(ticket)` | 只跑单注层（一注没有组上下文） |
| `SmartPick.judge_portfolio(tickets)` | 跑跨注层 |
| `sample_filtered()` | 统计写入 `stats["cross_scope_pending"]` 与 `stats["undeclared_skipped"]` |
| `sample_batch()` | 若存在 `cross` 规则，构造 `Portfolio` 并真正执行，写入 `stats["cross_scope_evaluated"]` |
| `validate_strategy()` | `undeclared` = **error**；missing `scope` = warning；跨注规则**用 3 注随机样本冒烟执行**，跑不通即报错 |

> **本仓库原则：跨注规则要么被真正执行，要么被显式报错，不可被静默忽略。**
> `validate_strategy()` 的冒烟测试理由：一条跨注规则执行不了，等于契约缺了一层
> —— 1.0 的 `R-002` 正是此病。

## 关键约束

```
platform/core/ 里禁止出现：
  ✗ 数字 35 / 12 / 5 / 2（号码池参数）
  ✗ 字符串 "dlt" / "大乐透"
  ✗ 特征名如 "adjacent_pairs"（应从 game.yaml 读）
  ✗ 硬编码的概率值（应从 game.yaml 算）

platform/core/ 里应当出现：
  ✓ 从配置读取 machine.zones 并计算 T
  ✓ 按 features 段的 primitive + args 求值
  ✓ 通用的枚举 / 置换检验 / 分散度工具
  ✓ 跨注原语只做纯结构度量（间隔向量 / 覆盖 / 共享计数），不含号码池数值
```

> **关于自检**：`tests/test_cross_scope.py` 有一条"铁律扫描"，
> 用 AST 剥掉 docstring 与注释后再扫源码里的彩种常量。
> 原因：本 README 与 `portfolio.py` 的 docstring 里**正列举着被禁止的字符串**，
> 朴素的全文本扫描会把这些"禁令清单"本身当成违规 —— **会误报的检查比没有检查更坏**。

自检命令：

```bash
python cli/main.py validate --all -v     # 含 features 声明可执行性 + 跨注规则冒烟
python tests/test_core.py                # 113 项核心测试
python tests/test_cross_scope.py         # 62 项跨注层测试
```

## 与 `games/<id>/data/tools/` 的关系

| | `platform/core/` | `games/<id>/data/tools/` |
|---|---|---|
| 范围 | 彩种无关通用 | 该彩种专用（含字段口径） |
| 状态 | **已实现** | 已实现 |
| 内容 | 原语（单注 + 跨注）/ Ticket / Portfolio / 求值 / 判定 / 生成 | 数据加载、字段口径、该彩种专用分析 |

判定标准：**这段代码换一个彩种能否直接用？**
- 能（只需换配置）→ 属于 `platform/core/`
- 不能（依赖特定字段名/口径）→ 留在彩种目录

## 已知边界

| 项 | 状态 |
|---|---|
| `spread_penalty()` | **未量化**。只返回一个启发式惩罚值，不是统计结论。跨注特征已声明时应优先用跨注特征，此启发式仅作向后兼容保留 |
| 撞号权重模型（α = 13.9405） | **未收入 framework**。属于彩种层观测校准，`F-0004` 有记录 |
| L3 组合**优化** | **未实现**。2.1 已补齐 L3 的**执行层**（`Portfolio` / `judge_cross`），但"在候选集上求解最优组合"仍未做 |
| `R-002` 的 `magnitude_pct` | **仍为 null**。可执行 ≠ 已量化：`R-002` 现在能判定命中与否，但"重复结构到底改变多少收益"没有证据 |
| 奖金封顶（1 亿） | **未纳入** +121.48% 的计算（Q-004，P0 开放） |
