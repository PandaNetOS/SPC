# VERSIONING.md — 版本与兼容策略

> **版本**：`1.2` ｜ 轮次 `r03` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 三个独立版本号

本仓库有**三个互不相同的版本号**，混淆它们是常见错误：

| 版本号 | 位置 | 语义 | 何时提升 |
|---|---|---|---|
| **schema_version** | `strategy.json` | 对外契约版本 | 结构变更时 |
| **config_version** | `games/<id>/game.yaml` | 单彩种配置版本 | 玩法/特征变更时 |
| **data_version** | `game.yaml` 的 `data.raw` | 数据集版本（如 `dlt_full_2933`） | 新增开奖期时 |

**轮次号**（`round01`、`round02`…）不是版本号，是迭代序号，两者不可互相替代。

## strategy.schema.json 的兼容规则

采用**主版本.次版本**两段式。

### 次版本提升（向后兼容）

允许的操作：

- 新增**可选**字段
- 放宽校验（扩大枚举、放宽 pattern、降低 minLength）
- 补充 `description`
- 新增 `rules[]` 条目、新增 `avoid_list[]` 条目

消费者行为：**直接使用**。旧字段语义不变。

### 主版本提升（破坏性）

触发条件（任一）：

- 删除或重命名字段
- 把可选字段改为必填
- 收紧校验（缩小枚举、收窄 pattern）
- 改变已有字段的语义
- 改变红线段落的恒值

消费者行为：**必须显式声明支持的版本**，遇到不认识的主版本应拒绝解析而非"尽力而为"。

> **"尽力而为"解析是本仓库明确禁止的。** 一个把 `changes_win_probability`
> 读错方向的前端，会向用户展示"本策略提高中奖率"—— 这是比报错严重得多的失败。

### 红线段落的版本政策

`affects_win_probability` / `changes_win_probability` / `optimizable_target` /
`sum_affects_numbers` 这四处**无论版本如何变化，恒值不变**。
若某次变更试图修改它们，那不是版本升级，那是**立场变化** —— 需要单独的评审记录，不能混在版本升级里。

## 数据版本（data_version）

命名约定：`<game>_full_<期数>`

例：`dlt_full_2933` = 超级大乐透，2933 期全量。

### 数据更新规则

1. **raw 层只增不改**。新增开奖期 → 新文件（或追加，但须重算 SHA256）。
2. **`data_version` 变更后，必须重跑全部结论的复现脚本**。
   依赖了旧数据的结论若无法复现，须将其 `status` 降级或标注失效。
3. `sha256` 必须与文件实际内容一致 —— 这是"数据没被悄悄改过"的唯一保证。

### 为什么这么严

`games/dlt/iterations/round02/known_errors.md` 记录了 E6（前视偏差）：
用全样本统计量做"预测"会得出看似显著、实则无用的结论。
数据层一旦被静默修改，所有建立在它之上的结论都会**在无人察觉的情况下失效**。
SHA256 是这个链条上唯一廉价的断点探测器。

## 迭代轮次与结论演化

轮次之间用**结论 id 的取代链**而非覆盖来演化：

```
F-0007 (round02, status=superseded, superseded_by=F-0019)
   └─→ F-0019 (round03, status=established, supersedes=F-0007)
```

规则：

- **已发布的结论 id 永不复用**。推翻它，就新增一条并填 `superseded_by`。
- `supersedes` 与 `superseded_by` **必须双向一致**，校验器会检查。
- 被推翻的结论**保留在台账里**，`status=refuted`。
  **不要删除** —— 它是"这个方向已试过"的记忆，删掉会导致下一轮重复劳动。

> 这是本仓库"自我迭代"记忆的底座：结论不是被替换，而是**带着血统被取代**。

## 变更日志

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-10-10 | 初始契约：`fact` / `strategy` / `game_config` / `iteration` 四个 schema，均 v1.0 / 1.0 | 建立仓库基线 |
| 2026-10-10 | **`game_config` 主版本 1.0 → 2.0**：`features[]` 新增 `primitive`（枚举于框架原语注册表）、`args`（含 `zone` / `threshold` / `lo` / `hi` / `modulus`）、`note`；`formula` 降级为纯注释字段（不参与求值） | **破坏性**（若消费方曾按 `formula` 字符串求值，须改为按 `primitive` + `args` 求值）。**旧 config 仍可读**，`framework/core/evaluate.py` 会跳过无 `primitive` 的特征并显式提示 |
| 2026-10-10 | **`strategy.schema.json` 次版本提升**：`machine_rule.predicate` 新增受限 DSL `pattern`（`<feature_key> <op> <literal>`，同连接词 `and`/`or`，禁括号/嵌套/混用/右侧非字面量） | **收紧校验**。原为自由字符串，现非法表达式在校验阶段被拒收。已发布的 `dlt` 策略两条 predicate 均合规 |
| 2026-10-10 | **`iteration.schema.json` 次版本提升**：`started_at` 放宽为可空；`new_lesson_ids` pattern 由 `^L-[0-9]{2}$` 放宽为 `^L-?[0-9]{1,2}$`（仓内实际写法为 `L1`..`L9` 无补零）；新增可选字段 `planned_tasks`（下轮任务计划）与 `outputs_planned` | 向后兼容 |
| 2026-10-10 | **`fact.schema.json` 次版本提升**：`evidence.effect` 放宽为 `["object","null"]` | 向后兼容（部分结论无效应量） |
| 2026-10-11 | **`game_config` 次版本 2.0 → 2.1**：`features[]` 新增可选 `scope`（`single` / `cross`，默认 `single`）；新增 5 个跨注原语，注册在**独立**的 `CROSS_PRIMITIVES` 表 | 向后兼容（`scope` 有默认值）。**收紧校验**：`scope` 与原语真实作用域不一致时结构性拒收 |
| 2026-10-11 | **`strategy.schema.json` 次版本 1.0 → 1.1**：`rules[]` 新增**必填** `scope`（`single` / `cross`） | **破坏性**（存量 `strategy.json` 的每条 rule 必须补 `scope`）。理由见下节 —— 缺这个字段时，消费者无法知道该走哪个执行入口 |
| 2026-10-11 | **`fact.schema.json` 次版本提升**：新增**必填** `claim_type`（枚举 `analytic` / `empirical` / `simulation` / `documentary` / `methodological`），并在 `allOf` 中按类型施加结构性约束 | **破坏性**（存量 18 条结论全部须回填）。此前"这个数字靠什么立住"只写在 `confidence_basis` 里当**建议**，属文档层约束；现升为结构层约束，填错即拒收 |
| 2026-10-11 | **`fact.schema.json` 次版本提升**：`evidence` 新增可选 `source_sha256`（`^[0-9a-f]{64}$`） | 向后兼容（允许 null，但 null 时校验给 warning）。**新增检测能力**：source 文件被改而结论未更新时，"结论可能失效"变成可检出的错误 |

> 新增记录请追加到表末，**不要删除历史行**。

## config_version 2.0 迁移指南

**唯一变化**：`features[]` 每项从"只有 `formula` 注释"改为"`primitive` + `args` 声明"。

| 旧（1.0，仍可读） | 新（2.0） |
|---|---|
| `key: front_sum`<br>`formula: "sum(front)"`<br>`range: [15, 165]` | `key: front_sum`<br>`primitive: sum`<br>`args: {zone: front}`<br>`formula: "sum(front)"`（保留为注释）<br>`range: [15, 165]` |

**升级检查清单**：

1. 每个 `formula` 对应的计算能否由框架 21 个原语之一表达？
   `python cli/main.py games` 后查 `framework/core/README.md` 的原语表
2. 参数落在 `args` 里，**不要**写进 `formula`
3. 多区彩种必须显式写 `args.zone`；单区彩种可省略
4. 升级后跑 `python cli/main.py validate --game <id> -v`，
   应看到 `features 声明可执行 (N/N 个含 primitive)`

## config_version 2.1 → 与 schema_version 1.1 迁移指南（跨注层）

**为什么必须加 `scope`**：`config_version 2.0` 时，`strategy.json` 的 `R-002` 引用了一个
跨注特征 —— 而该特征**既未在 `game.yaml` 声明，全仓库也没有任何执行入口**。
策略被发布出去，消费者拿到却**无法执行**：契约缺了整整一层。

`scope` 就是补上这层：**它告诉消费者该走哪个执行入口**。

| 位置 | 字段 | 值 | 作用 |
|---|---|---|---|
| `game.yaml` `features[]` | `scope` | `single`（默认）/ `cross` | 声明该特征在哪一层可算 |
| `strategy.json` `rules[]` | `scope` | `single` / `cross`（**必填**） | 声明该规则走哪个入口 |

| 规则 `scope` | 执行入口 |
|---|---|
| `single` | `judge(cfg, ticket, rules)` / `SmartPick.judge(ticket)` |
| `cross` | `judge_cross(cfg, portfolio, rules)` / `SmartPick.judge_portfolio(tickets)` |

**升级检查清单**：

1. `strategy.json` 每条 rule 补 `scope`（缺即 warning，`validate --all` 会报）
2. 引用的跨注特征必须在 `game.yaml` 里以 `scope: cross` 声明 ——
   否则进 `undeclared`，`validate` 报 **error**（1.0 是 warning，正是这个宽松让缺口活了下来）
3. `scope: cross` 的特征只能挂 `CROSS_PRIMITIVES` 里的原语，反之亦然 —— 混用被结构性拒收
4. `validate --all` 会对每条跨注规则做**真样本冒烟执行**，跑不通即 error

> **可执行 ≠ 已量化**：`R-002` 现在能判定命中与否，但 `magnitude_pct` 仍是 `null`。
> 把这两件事分开，避免"能跑"被误读成"有效"。

**为什么 `rules[].scope` 是必填（而非默认 `single`）**：
默认 `single` 会让一条跨注规则**静默地在单注层被跳过** ——
而"静默跳过"正是 1.0 的病根。宁可让升级时报错，也不给一个会骗人的默认值。

## 关于 config_version 2.0 那次

**为什么是破坏性而不仅是"新增可选字段"**：
`formula` 从"参与求值的语义载体"退回"注释"，这是**语义变更**（第 33 行"改变已有字段的语义"）。
任何曾把 `formula` 当可执行规范的消费方，行为会静默改变 —— 这类变更必须提升主版本，
强制消费方显式确认。

**与红线的交互**：本次变更**未触碰任何红线段落**
（`affects_win_probability` / `changes_win_probability` / `optimizable_target` /
`sum_affects_numbers`）。若未来有变更触碰它们，按第 45–49 行处理 —— 那是立场变化，
需单独评审记录，不能混在版本升级里。
