# round02.md — 迭代日志（round02：v4 素材结构化入库）

| 项 | 内容 |
|---|---|
| **轮次** | `round02` |
| **彩种** | `dlt`（超级大乐透） |
| **性质** | **整理入库轮** —— 不产生新的分析证据，把 v4 分析包的成果按框架结构固化 |
| **日期** | 2026-10-10 |
| **状态** | delivered |
| **执行者** | AI（WorkBuddy） |
| **数据版本** | `dlt_full_2933`（2933 期，07001 ~ 26115，2007-05-30 ~ 2026-10-10） |

---

## 1. 本轮要解决什么问题

`round01` 之前的分析（历史"第 2/3/4 轮"）产出了 `dlt_2933_package_v4` 分析包：
数据 + 派生集 + 规则变更史 + 策略模拟验证 + 防污染任务书 + 已知错误清单。

问题在于：它是**一份文档包**，不是**可迭代系统**。具体缺陷：

| 缺陷 | 后果 |
|---|---|
| 结论散在 5 个 markdown 里 | AI 无法机器检索，每轮要重读全文 |
| 没有"结论 id" | 无法追踪"哪条结论被哪轮推翻了" |
| 没有状态机 | `established` 与 `refuted` 混在一起，读的人不知道信哪个 |
| 教训与方法论混在错误清单里 | 无法独立复用 |
| 没有开放问题池 | 减损项（"未做分期稳健性"）写完就丢了，下一轮想不起来 |
| 输出契约缺失 | 外部工具无法安全消费 |

**本轮的任务**：把包内容**拆解、编号、状态化**，并建立让它可持续迭代的骨架。

---

## 2. 做了什么

### 2.1 建立结构

```
spec/          4 个 JSON Schema + VERSIONING.md   ← 契约层（稳定接口）
framework/     protocol/ methodology/ tools/ core/ ← 框架层（彩种无关）
memory/        facts/ journal/ lessons/ workbench/ ← 记忆层（本仓库的核心差异）
games/dlt/     game.yaml data/ iterations/ strategy/ ← 彩种层（插件）
src/ cli/      校验器与生成器
```

### 2.2 拆解 v4 包 → 新结构

| v4 原位置 | 新位置 | 处理 |
|---|---|---|
| `01_data/*.csv` `*.jsonl` | `games/dlt/data/raw/` | 原样搬迁，SHA256 校验一致 |
| `02_derived/*` | `games/dlt/data/derived/` | 原样搬迁 |
| `03_tools/*.py` | `games/dlt/data/tools/` | 搬迁 + 修正路径（`01_data/` → `raw/`）|
| `05_build_scripts/*` | `games/dlt/data/build_scripts/` | 搬迁 + 修正路径 |
| `06_RULES_HISTORY.md` | `games/dlt/rules_history.md` | 原位保留（彩种级口径） |
| `07_strategy_simulation/*` | `games/dlt/strategy/` | 搬迁（`*_results.json` 即策略证据） |
| `00_TASK_BRIEF.md` | `games/dlt/iterations/round02/TASK_BRIEF.md` | 归入轮次 |
| `04_priority_tasks.md` | `games/dlt/iterations/round02/PRIORITY_TASKS.md` | 归入轮次 |
| `05_known_errors.md` | `games/dlt/iterations/round02/known_errors.md`（留档）<br>+ **`memory/lessons/LESSONS.md`（提炼，主用）** | **拆成两份**：教训独立成库 |
| `03_findings/_legacy/*` | `games/dlt/iterations/round02/legacy_findings/` | 归档，带使用门槛 |
| `manifest.json` | `games/dlt/manifest_v4_source.json` | 保留为溯源 |

### 2.3 提炼记忆层

**`memory/facts/FACTS.jsonl`（15 条）** —— 每条含 id / 状态 / 置信度 1–5 /
结构化证据（效应量 + CI）/ **减损项** / 演化链（`supersedes` ↔ `superseded_by`）。

来源映射：

| 来源 | 提炼出的结论 |
|---|---|
| 模拟结果 A 层 | F-0001（概率不可变，解析） |
| 现行规则文档 | F-0002（负期望）、F-0014（规则口径）、F-0015（1 亿封顶实测） |
| 模拟结果 B2 层 | F-0003（撞号效应 1.360） |
| 模拟结果 C 层 | F-0004（+121%，条件模拟） |
| 精确枚举 check | F-0005（开出率 vs 被选中率） |
| 变点扫描 | F-0006（2013-08 渐进切点）、F-0007（被推翻的 2015） |
| ACF 置换检验 | F-0008（不可预测） |
| 过度离散 + HAC | F-0009（heat 伪显著） |
| 精确检验 | F-0010（奇偶不显著） |
| 独立性检验 | F-0011（后区独立） |
| 校验脚本输出 | F-0012（销量星期效应）、F-0013（重复组合正常） |

**`memory/lessons/LESSONS.md`（L1–L9）** —— 每条含
**症状 / 后果 / 正确做法 / 检测方法** 四段。相比 v4 的错误清单，
补了「**检测方法**」一栏（"下次怎么早发现"），这是从"记录错误"升级为"防止错误"。

**`memory/workbench/`** —— 8 个开放问题（**全部来自 FACTS 的 caveats**）、
5 个假设、42 项待办。

> 关键洞察：**每条 caveat 都是一个下一代任务**。
> 这是本仓库自我迭代真正的动力机制 —— 不是靠"AI 灵光一现"，而是靠
> 结论自带减损项，减损项自动进入问题池，问题池驱动下一轮。

---

## 3. 本轮确认的核心事实（供后续轮次引用）

| 量 | 值 | 来源 |
|---|---|---|
| 单注组合总数 | **21,425,712** = C(35,5)×C(12,2) | 解析 |
| 一等奖概率 | **4.667289469773513e-08** | 解析 |
| 撞号系数（随机 → 避连号） | **1.0028 → 0.4528**（比值 0.4515 [0.4487, 0.4543]） | 条件模拟 |
| 中奖时奖金提升 | **+121.48%**（★★★☆☆，封顶前上界） | 条件模拟 |
| 连号撞号比（一等奖） | **1.3603 [1.1298, 1.6292]** | 观测 + Bootstrap |
| 连号撞号比（二等奖） | **1.3520 [1.1679, 1.5793]** | 观测 + Bootstrap |
| 结构切点 | **2013-08-28**（χ²=185.0，排名 1/234，渐变，±6 月） | 切点扫描 |
| 现行规则 epoch | **E6**（2026-02-02 起，7 奖级，返奖率 51%） | 规则文档 |
| 抽稀系数 α | **13.9405**（由 B2 观测锁定） | 模型校准 |

---

## 4. 本轮**没有**做的事（明确记录）

| 未做 | 影响 | 记录位置 |
|---|---|---|
| 撞号效应的分期稳健性 | F-0003 可能只在早期成立 | `Q-001` / `T-001` |
| 中位数比 / NegBin 对照 | F-0003 触及 L5（重尾比均值），有技术债 | `Q-002` / `T-002` |
| 条件模拟纳入 1 亿封顶 | **F-0004 的 +121% 偏乐观**，属对外输出风险 | `Q-004` / `T-003` |
| 后区撞号建模 | 后区 66 组合撞号可能比前区更集中 | `Q-003` / `T-010` |
| 奖金瓜分机制 / 择时 | 错失可能存在的第二条策略 | `Q-007` / `T-012` |
| 逐号偏好权重 | F-0004 可信度被限制在 ★★★☆☆ | `Q-006` / `T-020` |
| 第二个彩种接入 | **框架通用性未经检验** | `T-031` |

> 记录"没做什么"与记录"做了什么"同等重要 —— 它防止下一轮误以为这些都做过了。
> 这也是 `spec/fact.schema.json` 强制 `caveats` 不为空的用意。

---

## 5. 本轮对**框架本身**的改进建议

（自我迭代的元层面产出，待 round03 评审）

| # | 建议 | 理由 |
|---|---|---|
| R-1 | `fact.schema.json` 增加 `evidence.verification_class` 枚举字段<br>（`analytic` / `exact_enumeration` / `observational` / `simulated`） | 当前"解析可证 vs 模拟估计"的信息只存在 `evidence.method` 的自由文本里，机器不可判。这是本仓库最重要的区分（L8），应该结构化成字段 |
| R-2 | 增加 `fact.schema.json` 的 `depends_on` 字段（结论间的依赖边） | 当前只知道"谁取代谁"，不知道"谁依赖谁"。`F-0004` 依赖 `F-0003` 的 α 校准 —— 若 `F-0003` 被推翻，`F-0004` 应自动降级。现在这个传导靠人记 |
| R-3 | 校验器增加"证据哈希" | `source` 文件被改后无法检出。呼应 `spec/VERSIONING.md` 的数据静默修改风险 |
| R-4 | `INDEX.md` 由 `FACTS.jsonl` 自动生成 | 当前手写 → 必然漂移 |
| R-5 | 增加 `strategy.schema.json` 的 `validity_window` 字段 | 策略规则会因规则变更（如封顶条款）而失效，需要显式的有效期 |

---

## 6. 下一步（交给 round03）

**round03 的优先攻击顺序**（详见 `games/dlt/iterations/round03/TASK_BRIEF.md`）：

1. `T-001` `T-002` `T-003` — P0 三项，**直接关乎现有对外输出的正确性**
   T-003 尤其重要：现在给用户的 +121% 是**未计封顶的上界**，而封顶已被实测触发（F-0015）
2. `T-010` `T-011` — P1 两项，可能新增独立可用规则（后区撞号、星期交互）
3. `R-1` `R-2` — 框架改进中优先级最高，影响后续所有轮次

**给 round03 执行者的提醒**：

- 先读 `AI_CONTEXT.md`（单一入口），再读 `games/dlt/iterations/round03/TASK_BRIEF.md`
- 本轮结论**不是 ground truth**。`F-0004` 是模型估计（★★★☆☆），请独立复核
- 引用任何结论前**必读其 `caveats`** —— 本仓库把减损项写进台账就是为了这个
- **不要引用 F-0007**（已推翻）
- 涉及奖金的任何分析**必须声明 `rules_epoch`**

---

## 7. 本轮交付物清单

| 路径 | 说明 |
|---|---|
| `spec/*.schema.json` ×4 + `README.md` + `VERSIONING.md` | 契约层 |
| `memory/facts/FACTS.jsonl` + `INDEX.md` | 结论台账（15 条） |
| `memory/lessons/LESSONS.md` | 教训库（L1–L9） |
| `memory/workbench/{OPEN_QUESTIONS,HYPOTHESES,TODO}.md` | 工作记忆（8 问 + 5 假设 + 42 待办） |
| `memory/journal/round02.md` | 本文件 |
| `games/dlt/` 全部内容 | 拆解重排后的彩种数据与产出 |
| `games/dlt/iterations/round02/` | 轮次归档（任务书/优先级/已知错误/legacy findings） |
| `games/dlt/strategy/strategy.json` | 对外策略输出（首版） |
| `games/dlt/iterations/round03/TASK_BRIEF.md` | 下一轮任务书（占位，由 HANDOFF 生成） |
