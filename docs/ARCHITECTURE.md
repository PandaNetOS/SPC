# ARCHITECTURE —— 仓库架构

> **版本**：`1.1` ｜ 轮次 `r03` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 一句话

**框架是骨架与协议，彩种是数据与插件。** 新增彩种 = 加一个 `games/<id>/` 目录，不改一行框架代码。

## 分层图

```
┌──────────────────────────────────────────────────────────────┐
│  AI_CONTEXT.md          单一入口（AI 与人都从这里进）           │
└──────────────────────────────────────────────────────────────┘
                            │
     ┌──────────────────────┼──────────────────────┐
     ▼                      ▼                      ▼
┌──────────┐        ┌──────────────┐        ┌──────────────┐
│  spec/   │        │  platform/  │        │   memory/    │
│  契约层   │        │   框架层      │        │   记忆层      │
│          │        │              │        │              │
│ 4 schema │        │ protocol     │        │ facts (台账)  │
│ 红线     │        │ methodology  │        │ journal      │
│ 版本号    │        │ tools        │        │ lessons      │
│          │        │ core(已实现)  │        │ workbench    │
└──────────┘        └──────────────┘        └──────────────┘
     │                      │                      │
     └──────────────────────┼──────────────────────┘
                            ▼
     ┌──────────────────────────────────────────┐
     │  src/spc/  +  cli/               │
     │  库代码与命令行（消费上述三者）               │
     └──────────────────────────────────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────┐
     │  games/<id>/   彩种层（数据 + 插件）        │
     │  game.yaml → data/ → iterations/ → strategy/│
     └──────────────────────────────────────────┘
```

## 各层职责与边界

| 层 | 职责 | 允许写的内容 | 禁止写的内容 |
|---|---|---|---|
| `spec/` | 定义**数据结构与红线** | JSON Schema、版本规则 | 具体彩种参数、具体结论 |
| `platform/` | 定义**怎么做研究** | 协议、方法论、通用工具、**号码空间计算与判定核心** | 彩种专属分支、彩种数值 |
| `memory/` | 存**结论与教训** | 结论台账、日志、教训、待办 | 原始数据、脚本 |
| `src/` + `cli/` | **机械执行**契约与协议 | 校验、计算、生成 | 判断"哪条结论对" |
| `games/<id>/` | **具体彩种的**数据与产出 | 数据、脚本、策略、轮次 | 修改上面任何一层 |

## 依赖方向（单向，不可逆）

```
games/  →  src/  →  spec/
   │        │
   └────────┴──→  platform/（文档与工具，被引用）
                     │
memory/ ←── 由 games/ 的轮次产出写入
```

**反向依赖 = 架构破坏。** 具体说：

- `platform/` 里出现 `if game_id == "dlt"` → 破坏
- `src/` 里硬编码 `35`、`12`、`21425712` → 破坏
- `spec/` 里出现"大乐透"三个字 → 破坏

## 四条核心设计

### 1. 契约优先（schema-first）

先有 `spec/*.schema.json`，后有内容。五份契约：

| 契约 | 约束对象 | 关键红线 |
|---|---|---|
| `fact.schema.json` | 结论台账 | `affects_win_probability` 恒 false |
| `strategy.schema.json` | 对外策略输出 | `boundary.optimizable_target` 枚举里**没有** `win_probability`；`predicate` 受限 DSL |
| `game_config.schema.json` | 彩种配置 | `epochs[].sum_affects_numbers` 恒 false |
| `iteration.schema.json` | 轮次登记 | `upstream_fact_ids` 形成演化链 |
| `version_index.schema.json` | 版本索引 | `levels` 必须 A/B/C/D 齐全；`content_version` / `iteration` 格式 |

红线的实现方式不是"文档里写不要"，而是 **schema 里的 `const` / 枚举 / `pattern`**——
写错的值**根本存不进去**。结构性拒收，不靠自觉。

### 2. 配置驱动（config-driven）

`game.yaml` 是唯一彩种参数来源。`T = ∏ C(pool_size_i, pick_i)` 由
`platform/core/game_util.py` 从 `machine.zones` **机械算出**，代码里没有任何 `35` 或 `12`。

**同一思路已从「号码空间级」下沉到「单注级」**：
`platform/core/` 的 21 个特征原语由 `game.yaml` 的 `features[]`
以 `primitive` + `args` 形式声明驱动 —— 框架不知道"连号"是什么，只执行声明。

验证方式：把 `game.yaml` 的 `pool_size` 从 35 改成 36，`T` 必须自动变；
把 `has_run_ge2` 的 `threshold` 从 2 改成 3，判定结果必须自动变。

### 3. 单注层一等公民（single-ticket core）

`platform/core/` 七个模块，构成 `Ticket → 求值 → 判定 → 生成` 与
`Portfolio → 跨注求值 → 跨注判定` 两条链路：

```
L1 Ticket      ticket.py      一注号码。区名来自 machine.zones，不硬编码 front/back
L2 Scoring     evaluate.py    按声明机械求值（仅 scope: single 特征）
               judge.py       受限 DSL 解析 + 判定 + ★ 作用域切分
               features.py    21 个单注原语 + 5 个跨注原语（两张表分开注册）
L3 Portfolio   portfolio.py   ★ 2.1 起已实现：整组一等公民 + 跨注求值/判定
               generate.py    拒绝采样 + 结构分散（跨注规则在批次上下文执行）
```

**为什么 `Ticket` 不含 `front`/`back`**：区名是可变长数组。这是"加入第二个彩种
不改 `platform/`"的唯一硬标准的前提。`Portfolio` 同理 —— 只持有 `tuple[Ticket]`。

**★ 作用域是本层的核心机制**，且 2.1 起从"二路切分"升级为"三路切分"：

| 类别 | 判定 | 处理 |
|---|---|---|
| `single` | 特征已声明且 `scope: single` | 单注层正常判定 |
| `cross` | 引用了 `scope: cross` 的已声明特征 | `judge_cross()` 在整组上下文**真正执行** |
| `undeclared` | 引用了根本没声明的特征（拼错 / 遗漏） | **报错**，不是警告 |

`classify_rules()` 负责三路切分（"跨注"与"拼错"不再混为一谈）。
绝不用 `try/except` 静默吞掉 —— 那会连带使同批的 `R-001` 一起失效
（静默降级比报错危险）。

> **1.0 的病根**：`R-002` 引用 `duplicated_structure_across_tickets`，
> 该特征**从未在 `game.yaml` 声明，且全仓库没有任何执行入口** ——
> 策略被发布，消费者却无法执行它，**契约缺了整整一层**。
> 2.1 已正式声明为 `scope: cross`（改名为 `has_duplicated_structure`）并补上 L3 执行层。

> 详见 `platform/core/README.md` 与 `docs/PROPOSAL_SINGLE_TICKET_CORE.md`。

### 4. 记忆四层（memory tiers）

不同寿命的信息分开存，避免"长寿命的被短寿命的污染"：

| 记忆 | 半衰期 | 存储 | 权威性 |
|---|---|---|---|
| 结论台账 | 长期（有状态机） | `memory/facts/FACTS.jsonl` | **权威源** |
| 教训库 | 永久（只增不删） | `memory/lessons/LESSONS.md` | **最高** |
| 迭代日志 | 中（一轮一份） | `memory/journal/roundNN.md` | 过程记录 |
| 工作记忆 | 短（每轮清空重构） | `memory/workbench/` | 待验证 |

`memory/facts/INDEX.md` 是**派生物**，由 CLI 从 JSONL 生成，**不要手改**。

## 自我迭代的三个机械传导

"AI 每轮给出更好的框架"不能靠自觉，靠三条**结构性传导**：

1. **caveats → 开放问题**
   每条结论的 `caveats` 非空被校验器强制。每条 caveat 转成一个
   `memory/workbench/OPEN_QUESTIONS.md` 条目，进 `TODO.md`，带脚本路径与验收判据。

2. **HANDOFF → 下轮 TASK_BRIEF**
   协议 §4.3 要求：收轮时必须生成 `iterations/round(N+1)/TASK_BRIEF.md`。
   **不生成 = 迭代链断裂**，下轮无从开始。

3. **manifest.framework_revision**
   每轮在 `manifest.json` 里提框架改进建议（`proposed`），
   被采纳的进 `accepted`。这是"框架自身进化"的留痕。

## 数据流（一轮的完整路径）

```
iterations/roundNN/TASK_BRIEF.md      ← 上一轮 HANDOFF 生成（反锚定）
         │
         ▼
data/tools/*.py  →  data/derived/*    ← 分析，结果落盘
         │
         ▼
iterations/roundNN/FINDINGS.md        ← 结论（含引用类别标注）
         │
         ├──→  memory/facts/FACTS.jsonl   ← 新结论/取代/推翻
         ├──→  memory/workbench/          ← caveats 转的开放问题
         └──→  strategy/strategy.json     ← 若影响对外策略（CLI 重建）
         │
         ▼
iterations/roundNN/manifest.json      ← 轮次登记 + 框架改进建议
iterations/roundNN/HANDOFF.md         ← 交接 + 生成下轮 TASK_BRIEF
```

## 为什么这样分

见 `platform/methodology/` 与 `memory/lessons/LESSONS.md`。核心动机：

- **框架与彩种分离** → 第二个彩种不需要复制粘贴 5000 行分析代码
- **契约优先** → 红线不可能被"不小心"违反，也不可能被后来的 AI 悄悄改掉
- **记忆分层** → 3 个月后回来看，能分清"当时知道的"和"当时猜的"
- **机械传导** → 自我迭代不依赖某个 AI 记得要做，靠文件依赖强制

## 唯一硬标准（再强调一次）

> **加入第二个彩种时，是否需要改 `platform/` 或 `src/` 的任何一行？**

不需要 = 架构成立。需要 = 这不是"新彩种的问题"，是框架缺了抽象，必须补进框架。
