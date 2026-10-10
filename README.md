# smartpickcore

> **版本**：`1.10` ｜ 轮次 `r03` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

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

---

## 👤 普通用户从这里看

**你不想读代码、不想看统计术语，只想知道"这个策略到底该怎么用"** —— 直接点这里：

### 👉 [**超级大乐透 · 策略说明书（人话版）**](games/dlt/strategy/STRATEGY_GUIDE.md) &nbsp;`v1.1`

> 路径：`games/dlt/strategy/STRATEGY_GUIDE.md` — 版本 `v1.1`（轮次 `r03`，更新 2026-10-11）— 不需要任何背景知识

它讲清了四件事：策略说了什么、为什么可能有用、
**什么时候它没用（四个减损项，其中 1 亿封顶已真实触发过）**、以及绝对不要做的事。

> 一句话预告：**本策略不提高中奖概率，只在中奖时可能让你少跟别人分钱；
> 买单注的人基本用不上，买多注的人别把号码挤在一起。**

下面开始是给**开发者与研究者**的内容。

---

## 快速开始

```bash
# 依赖
pip install pyyaml jsonschema numpy pandas

# 仓库概览
python cli/main.py info

# 全量校验（48 项：schema / 红线 / 外键 / 双向取代 / SHA256 实算 / 证据锚定漂移 / 版本一致性 / 跨注规则冒烟）
python cli/main.py validate --all -v

# 重算证据锚定哈希（改完结论或证据文件后重新基线）
python cli/main.py rehash --strategy --dry-run

# 版本一致性（文件内版本行 ↔ versions.json ↔ VERSION_INDEX.md）
python cli/main.py versions --summary

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
├── pyproject.toml          v0.1.0   ← 顶层版本（release）= smartpickcore 整体版本，源自 project.version
├── AI_CONTEXT.md          v1.3   ← 单一入口。AI 与人都从这里进
├── VERSION_INDEX.md       v1.0   ← 版本总索引（派生物，AI 先读这里）
├── versions.json          v1.0   ← 版本权威源（所有版本字段的唯一事实来源）
├── README.md              v1.10  ← 本文件
├── spec/                         ← 契约层：5 份 JSON Schema + 版本规则 + 四条红线
│   ├── fact.schema.json            ← 结论契约（claim_type / source_sha256 / 红线）
│   ├── game_config.schema.json     ← 彩种配置契约（sum_affects_numbers 红线）
│   ├── strategy.schema.json        ← 策略契约（changes_win_probability 红线）
│   ├── iteration.schema.json       ← 迭代契约
│   ├── version_index.schema.json   ← 版本索引契约（index_version 1.1）
│   ├── README.md
│   └── VERSIONING.md               ← 版本规则 + config 2.0→2.1 迁移指南
├── framework/                    ← 框架层（framework_version = 1.1）
│   ├── README.md                   ← 框架层说明（v1.0，框架/彩种分离判定标准）
│   ├── INDEX.md             v1.1   ← 按需求找文件
│   ├── core/                       ← ★ 框架核心（7 模块）
│   │   ├── __init__.py
│   │   ├── ticket.py                 ← L1 Ticket
│   │   ├── features.py               ← 21 单注 + 5 跨注原语表
│   │   ├── evaluate.py               ← 求值（单注）
│   │   ├── judge.py                  ← 判定（受限 DSL）
│   │   ├── portfolio.py              ← L3 Portfolio（跨注求值 / 判定）
│   │   ├── generate.py               ← 候选生成
│   │   ├── game_util.py              ← 彩种无关工具
│   │   └── README.md
│   ├── protocol/                   ← 迭代协议 + 记忆协议 + 3 模板
│   │   ├── ITERATION_PROTOCOL.md
│   │   ├── MEMORY_PROTOCOL.md        ← 含 claim_type / 证据锚定章节
│   │   ├── README.md
│   │   └── templates/
│   │       ├── FINDINGS.template.md
│   │       ├── HANDOFF.template.md
│   │       └── TASK_BRIEF.template.md
│   ├── methodology/                ← 数学边界 + 统计纪律
│   │   ├── MATH_BOUNDARY.md
│   │   └── STATISTICAL_DISCIPLINE.md
│   └── tools/
│       └── memory.py                 ← 记忆读写库（彩种无关）
├── src/smartpickcore/            ← 库代码（8 模块）
│   ├── __init__.py
│   ├── game.py                     ← 彩种加载
│   ├── memory.py                   ← 结论 / FACTS 读写
│   ├── validate.py                 ← 校验器（49 项）
│   ├── strategy.py                 ← 策略构建
│   ├── evidence.py                 ← ★ 证据锚定（C 新增：sha256 / 漂移）
│   ├── api.py                      ← 对外 API
│   └── versions.py                 ← 版本索引读写
├── cli/
│   └── main.py              —      ← 命令行入口（14 个命令）
├── memory/                        ← 记忆层
│   ├── facts/
│   │   ├── FACTS.jsonl        v1.3   ← 结论台账（18 条，JSONL 追加式；每条带 claim_type + source_sha256）
│   │   └── INDEX.md           v1.3   ← 速览（派生物，CLI 生成，勿手改）
│   ├── journal/
│   │   ├── round02.md
│   │   └── round03.md
│   ├── lessons/
│   │   └── LESSONS.md         v1.1   ← 教训库 L1–L12（只增不删）
│   ├── workbench/
│   │   ├── TODO.md            v1.4   ← 任务台账（P0 已清空）
│   │   ├── OPEN_QUESTIONS.md          ← 开放问题（11，3 answered）
│   │   └── HYPOTHESES.md              ← 假设（5）
│   └── INDEX.md
├── games/                         ← 彩种（数据 + 轮次 + 策略）
│   ├── _template/                   ← 新彩种骨架
│   │   ├── game.yaml
│   │   ├── README.md
│   │   ├── strategy/strategy.json
│   │   ├── data/{raw,derived,build_scripts,tools}/  ← 工具生成，各含 README
│   │   └── iterations/round01/TASK_BRIEF.md
│   ├── dlt/                         ← 超级大乐透（实际数据）
│   │   ├── game.yaml                  ← config 2.1（11 单注 + 3 跨注特征）
│   │   ├── manifest_v4_source.json
│   │   ├── rules_history.md           ← 规则沿革（F-0015 历史引用）
│   │   ├── data/
│   │   │   ├── raw/                     ← dlt_full_2933.{csv,jsonl}（原始开奖，2933 期）
│   │   │   ├── derived/                 ← 8 份派生统计（CSV/JSON，工具生成）
│   │   │   ├── build_scripts/           ← 3 个构建脚本
│   │   │   └── tools/                   ← 8 个分析工具（acf / changepoint / exact / 等）
│   │   ├── iterations/
│   │   │   ├── round01/                 ← 空占位
│   │   │   ├── round02/                 ← FINDINGS / HANDOFF / TASK_BRIEF / manifest + legacy_findings/
│   │   │   ├── round03/                 ← FINDINGS / HANDOFF / TASK_BRIEF / manifest + scripts/
│   │   │   └── round04/                 ← TASK_BRIEF / manifest（待测）
│   │   └── strategy/
│   │       ├── strategy.json            ← schema 1.1（2 规则 + 8 avoid_list）
│   │       ├── STRATEGY_GUIDE.md        ← 人话版 v1.1
│   │       ├── simulation_results.json
│   │       └── strategy_simulation.py
│   └── INDEX.md             v1.1   ← 彩种索引
├── tools/                         ← 版本索引生成 / 注入脚本
│   ├── build_versions.py
│   ├── render_version_index.py
│   ├── inject_version_lines.py
│   └── count_tests.py        —      ← 测试计数自举（E 新增）
├── docs/                          ← 设计 / 消费 / 迭代 / 方法 / 版本文档
│   ├── ARCHITECTURE.md
│   ├── CONSUMING.md
│   ├── ITERATION_GUIDE.md
│   ├── METHODOLOGY.md
│   ├── PROPOSAL_SINGLE_TICKET_CORE.md
│   └── VERSIONING_DOCS.md
└── tests/                         ← 5 个测试（共 319 项，无需 pytest）
    ├── README.md                   ← 测试说明（v1.3，tests/README.md）
    ├── test_core.py                 ← 113 项
    ├── test_cross_scope.py          ← 62 项
    ├── test_claim_type.py           ← 43 项
    ├── test_evidence_anchor.py      ← 32 项
    ├── test_shadow_game.py          ← 69 项（D 新增）
    └── fixtures/shadow/             ← 影子彩种夹具（T-031 实测，与 dlt 零交集）
        ├── game.yaml
        ├── data/raw/shadow.csv
        └── strategy/strategy.json
```

> **版本号标注规则**：`vX.Y` = 该文件当前 `content_version`；`—` = 该文件不单独版本化
> （B 级 `.py` 只登记索引）。例外：`pyproject.toml` 的 `v0.1.0` 标的是 **smartpickcore 整体 release 版本**（`project_version`），不是 `content_version`。完整清单见 [`VERSION_INDEX.md`](VERSION_INDEX.md)。
>
> **文件名本身不带版本号** —— 版本号在**文件头部版本行**与**本索引**里维护。
> 原因：改名会让所有指向它的链接失效、`git log` 追不到历史。详见
> [`docs/VERSIONING_DOCS.md`](docs/VERSIONING_DOCS.md) §2。

详见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)。

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
| 契约层 | ✅ 5 schema + VERSIONING（含 config 2.0 迁移指南） |
| 版本体系 | ✅ A/B/C/D 四级分区 + `versions.json` 权威源 + `content_version` / `framework_version` |
| 框架层 | ✅ 2 协议 + 3 模板 + 2 方法论 + memory.py |
| **框架核心** | ✅ **`framework/core/` 7 模块 / 21 单注原语 + 5 跨注原语**（Ticket / Portfolio / 求值 / 受限 DSL 判定 / 作用域三路切分 / 生成器） |
| 记忆层 | ✅ **18 条结论**（每条带 `claim_type` 证据类型 + `source_sha256` 证据锚定）/ L1–L12 / 11 开放问题（3 answered）/ 5 假设 / 待办（P0 已清空） |
| 库与 CLI | ✅ 9 模块 + 14 命令，`validate --all` **48 项全绿** |
| 彩种 `dlt` | ✅ `game.yaml`（config **2.1**，11 单注 + **3 跨注**特征全原语化）+ `strategy.json`（schema **1.1**，2 规则 + 8 条 avoid_list）+ [**策略说明书（人话版）**](games/dlt/strategy/STRATEGY_GUIDE.md) + **round03 复核完成** + round04 任务书 |
| `tests/` | ✅ `test_core.py` **113** + `test_cross_scope.py` **62** + `test_claim_type.py` **43** + `test_evidence_anchor.py` **32** + `test_shadow_game.py` **69** 全绿（无需 pytest，共 **319** 项） |
| 版本体系 | ✅ A/B/C/D 四级分区，**132 条**登记（A=34 B=58 C=13 D=27），版本行全部一致 |

### r03 复核要点（结论已修正）

| 项 | 结果 |
|---|---|
| **封顶是否触发过？** | **从未**（E6 102 期一等奖总额最大 0.9788 亿）→ `F-0015` 被推翻，新增 `F-0016` |
| **计入封顶后的收益** | 未计封顶上界 **121%** → 实测锚点净值 **41.4%**（`F-0017`） |
| **撞号效应稳健性** | 仍成立但**幅度衰减过半**（前段 2.11 → 后段 1.25），`F-0003` 已更新 |
| **L5 技术债** | **已清偿**：中位数比 1.5 + 截尾检验仅变化 1.72%（`F-0018`） |

### 已知未闭合

| 项 | 说明 |
|---|---|
| `R-002` 跨注规则 | ✅ **执行层已闭合**（2.1）：已声明 `scope: cross` 特征 `has_duplicated_structure`，`judge_cross()` 可真正判定。⚠️ 但 `magnitude_pct` 仍为 **null** —— **可执行 ≠ 已量化** |
| `spread_penalty` | 启发式，**未量化**（不是统计结论）。有跨注特征时应优先用跨注特征 |
| L3 组合**优化** | **未实现**。跨注层只补齐了"执行"，"在候选集上求解最优组合"仍未做 |
| 奖金封顶 | +121.48% 的计算**未纳入** 1 亿封顶（Q-004，P0） |
| Q-009 | 组合分散度研究**尚未写入**开放问题清单 |

## 免责声明

本仓库**不提供中奖保证**，不改变中奖概率，不构成投注建议。
所有分析结论均附带减损项（`caveats`）与置信度分级，引用前请阅读。
**理性购彩，量力而行。**
