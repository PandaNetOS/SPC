# ARCHITECTURE —— 仓库架构

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
│  spec/   │        │  framework/  │        │   memory/    │
│  契约层   │        │   框架层      │        │   记忆层      │
│          │        │              │        │              │
│ 4 schema │        │ protocol     │        │ facts (台账)  │
│ 红线     │        │ methodology  │        │ journal      │
│ 版本号    │        │ tools        │        │ lessons      │
│          │        │ core(待实现)  │        │ workbench    │
└──────────┘        └──────────────┘        └──────────────┘
     │                      │                      │
     └──────────────────────┼──────────────────────┘
                            ▼
     ┌──────────────────────────────────────────┐
     │  src/smartpickcore/  +  cli/               │
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
| `framework/` | 定义**怎么做研究** | 协议、方法论、通用工具 | 彩种专属分支、彩种数值 |
| `memory/` | 存**结论与教训** | 结论台账、日志、教训、待办 | 原始数据、脚本 |
| `src/` + `cli/` | **机械执行**契约与协议 | 校验、计算、生成 | 判断"哪条结论对" |
| `games/<id>/` | **具体彩种的**数据与产出 | 数据、脚本、策略、轮次 | 修改上面任何一层 |

## 依赖方向（单向，不可逆）

```
games/  →  src/  →  spec/
   │        │
   └────────┴──→  framework/（文档与工具，被引用）
                     │
memory/ ←── 由 games/ 的轮次产出写入
```

**反向依赖 = 架构破坏。** 具体说：

- `framework/` 里出现 `if game_id == "dlt"` → 破坏
- `src/` 里硬编码 `35`、`12`、`21425712` → 破坏
- `spec/` 里出现"大乐透"三个字 → 破坏

## 三条核心设计

### 1. 契约优先（schema-first）

先有 `spec/*.schema.json`，后有内容。四份契约：

| 契约 | 约束对象 | 关键红线 |
|---|---|---|
| `fact.schema.json` | 结论台账 | `affects_win_probability` 恒 false |
| `strategy.schema.json` | 对外策略输出 | `boundary.optimizable_target` 枚举里**没有** `win_probability` |
| `game_config.schema.json` | 彩种配置 | `epochs[].sum_affects_numbers` 恒 false |
| `iteration.schema.json` | 轮次登记 | `upstream_fact_ids` 形成演化链 |

红线的实现方式不是"文档里写不要"，而是 **schema 里的 `const` / 枚举**——
写错的值**根本存不进去**。结构性拒收，不靠自觉。

### 2. 配置驱动（config-driven）

`game.yaml` 是唯一彩种参数来源。`T = ∏ C(pool_size_i, pick_i)` 由
`src/smartpickcore/game.py` 从 `machine.zones` **机械算出**，代码里没有任何 `35` 或 `12`。

验证方式：把 `game.yaml` 的 `pool_size` 从 35 改成 36，`T` 必须自动变。

### 3. 记忆四层（memory tiers）

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

见 `framework/methodology/` 与 `memory/lessons/LESSONS.md`。核心动机：

- **框架与彩种分离** → 第二个彩种不需要复制粘贴 5000 行分析代码
- **契约优先** → 红线不可能被"不小心"违反，也不可能被后来的 AI 悄悄改掉
- **记忆分层** → 3 个月后回来看，能分清"当时知道的"和"当时猜的"
- **机械传导** → 自我迭代不依赖某个 AI 记得要做，靠文件依赖强制

## 唯一硬标准（再强调一次）

> **加入第二个彩种时，是否需要改 `framework/` 或 `src/` 的任何一行？**

不需要 = 架构成立。需要 = 这不是"新彩种的问题"，是框架缺了抽象，必须补进框架。
