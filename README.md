# smartpickcore

> PandaNetOS 智能选号核心（Smart Pick Core）

**通用的彩票投注策略研究框架** —— 带自我迭代能力，并把研究结论输出成
其他工具可直接消费的策略规则。

---

## 这个仓库做什么

| 用途 | 说明 |
|---|---|
| ① **研究框架** | 与彩种无关的研究骨架：契约、协议、方法论、记忆系统。带**自我迭代**：每轮分析产出的 `caveats` 机械地转成下一轮的开放问题与任务，收轮时必须生成下轮任务书，迭代链不断。 |
| ② **策略输出** | 产出 `games/<id>/strategy/strategy.json` —— 机器可读的规则（`exclude`/`penalize`/`prefer`/`require`），供选号器、App、机器人消费。 |

## 核心立场（先看这个）

> **选号不改变中奖概率。**

大乐透单注组合总数 `C(35,5) × C(12,2) = 324,632 × 66 = 21,425,712`，
一等奖概率 `≈ 4.667e-08`。这是**解析结论**，不依赖任何数据——
分子（是否命中）由开奖结果决定，选号无法影响。

选号**唯一**能影响的是**分母**：中奖时是否与他人共享奖金。
这就是本仓库全部策略的立足点。

因此：

- ✅ 可以做的：避开高人群密度形态（连号、生日号），降低撞号，提高**中奖时的期望奖金**
- ❌ 不能做的：提高中奖率、预测号码、追冷热号、按周期选号

## 快速开始

```bash
# 依赖
pip install pyyaml jsonschema numpy pandas

# 仓库概览
python cli/main.py info

# 全量校验（28 项：schema / 红线 / 外键 / 双向取代 / SHA256 实算）
python cli/main.py validate --all -v

# 列彩种、列结论、看某条结论的减损项
python cli/main.py games
python cli/main.py facts --game dlt --min-confidence 4
python cli/main.py caveats F-0004

# 重生成对外策略（只重算 boundary 与 evidence_index；rules 不由代码生成）
python cli/main.py strategy --game dlt --dry-run

# 新彩种
python cli/main.py new-game <game_id>
```

## 目录结构

```
AI_CONTEXT.md          ← 单一入口。AI 与人都从这里进
spec/                  ← 契约层：4 份 JSON Schema + 版本规则 + 四条红线
framework/
  readme.md            ← 框架层说明（框架/彩种分离判定标准）
  INDEX.md             ← 按需求找文件
  protocol/            ← 迭代协议 + 记忆协议 + 3 个模板
  methodology/         ← 数学边界 + 统计纪律
  tools/memory.py      ← 记忆读写库（彩种无关）
  core/                ← 待实现（不为可能的复用做抽象）
memory/
  facts/FACTS.jsonl    ← 结论台账（权威源，JSONL 追加式）
  facts/INDEX.md       ← 速览（派生物，CLI 生成，勿手改）
  journal/roundNN.md   ← 迭代日志
  lessons/LESSONS.md   ← 教训库 L1–L9（只增不删）
  workbench/           ← 工作记忆（OPEN_QUESTIONS / HYPOTHESES / TODO）
games/
  _template/           ← 新彩种骨架
  dlt/                 ← 超级大乐透（数据 + 轮次 + 策略）
  INDEX.md             ← 彩种索引
src/smartpickcore/     ← 库代码（game / memory / validate / strategy / api）
cli/main.py            ← 命令行入口（10 个命令）
docs/                  ← ARCHITECTURE / CONSUMING / ITERATION_GUIDE / METHODOLOGY
tests/                 ← 测试说明（应测什么）
```

详见 `docs/ARCHITECTURE.md`。

## 四条红线

不是"文档里写不要"，而是**schema 里用 `const` / 枚举结构性拒收**：

| # | 红线 | 实现 |
|---|---|---|
| 1 | 任何结论都不得声称影响中奖概率 | `fact.schema.json`：`affects_win_probability` 为 `{"const": false}` |
| 2 | 策略声明不得声称改变中奖概率 | `strategy.schema.json`：`disclaimer.changes_win_probability` 为 `{"const": false}` |
| 3 | 可优化目标只能是"中奖时的期望奖金" | `boundary.optimizable_target` 枚举**故意不含** `win_probability` |
| 4 | 奖金规则变更不得声称影响号码分布 | `game_config.schema.json`：`epochs[].sum_affects_numbers` 为 `{"const": false}` |

违反红线的数据**根本存不进去**，不靠自觉。

## 自我迭代怎么运转

三条**机械式传导**（不依赖 AI 记得要做）：

```
每条结论的 caveats 非空（校验器强制）
        │
        ▼  每条 caveat → 一个开放问题 → 进 TODO（带脚本路径与验收判据）
             → 成为下轮 TASK_BRIEF 的选题

收轮时必须生成 iterations/round(N+1)/TASK_BRIEF.md
        │
        ▼  不生成 = 迭代链断裂

每轮在 manifest.json 提 framework_revision.proposed
        │
        ▼  被采纳的进 accepted —— 框架自身的进化留痕
```

## 接入新彩种

```bash
python cli/main.py new-game <game_id>
```

**唯一硬标准**：

> 加入第二个彩种时，是否需要改 `framework/` 或 `src/` 的任何一行？

不需要 = 框架分离成立。需要 = 框架缺了抽象，必须补进框架而不是打补丁。

## 当前状态

| 项 | 状态 |
|---|---|
| 契约层 | ✅ 4 schema + VERSIONING |
| 框架层 | ✅ 2 协议 + 3 模板 + 2 方法论 + memory.py |
| 记忆层 | ✅ 15 条结论 / L1–L9 / 8 开放问题 / 5 假设 / 42 待办 |
| 库与 CLI | ✅ 6 模块 + 10 命令，`validate --all` 28 项全绿 |
| 彩种 `dlt` | ✅ `game.yaml` + `strategy.json`（2 规则 + 8 条 avoid_list）+ round02 收轮 + round03 任务书 |
| `framework/core/` | ⬜ 待实现 |
| `tests/` | ⬜ 说明已写，用例待写 |

## 免责声明

本仓库**不提供中奖保证**，不改变中奖概率，不构成投注建议。
所有分析结论均附带减损项（`caveats`）与置信度分级，引用前请阅读。
**理性购彩，量力而行。**
