# VERSION_INDEX.md — 仓库版本索引

> **本文件由 `python tools/render_version_index.py --write` 从 `versions.json` 自动生成。请勿手工编辑。**
> 权威源是 `versions.json`（受 `spec/version_index.schema.json` 约束）。

**索引版本**：`2.0` ｜ **框架版本**：`1.1` ｜ **顶层版本（release）**：`0.1.0` ｜ **当前轮次**：`r07` ｜ **生成日期**：2026-10-11

---

## 0. AI 一分钟版（先读这里）

**这套版本号要回答的问题是：**

> 我手里这份内容，是**哪个版本**、**哪一轮产出的**、**改过几次**？

**四个版本号并存，各答不同问题 —— 不可互相替代：**

| 版本号 | 答什么问题 | 谁拥有 | 位置 |
|---|---|---|---|
| `schema_version` | 契约**结构**长什么样 | `spec/` | `strategy.json` |
| `config_version` | 彩种**参数**是什么版本 | `games/<id>/` | `game.yaml` |
| `data_version` | 用了**哪份数据** | `data/raw/` | `game.yaml` / manifest |
| **`content_version`** ★ | **这份内容改过几版** | **每份内容自己** | **文件内版本行 + 本索引** |
| **`framework_version`** ★ | **框架层改过几版** | **`framework/`** | **本索引** |
| **`project_version`** ★ | **SPC 整体 release 版本** | **整个包** | **本索引 + pyproject.toml** |

★ = 本次（2026-10-11）新引入。此前全仓库**没有**「内容版本」与「框架版本」的概念。

**实例（说明为何不冲突）**：`strategy.json` 的 `schema_version` 可以一直是 `1.0`，
而 `content_version` 从 `1.0` 升到 `1.1` —— 因为**契约结构没动，但规则幅度改了**。

**版本号格式**：`<主>.<次>`，如 `1.1`。

- **主** +1：结构变更 / 立场变更 / 破坏性变更（须单独评审）
- **次** +1：内容增补、结论新增、幅度修正

> 与 `spec/VERSIONING.md` 的三段式（`x.y`）规则一致。
> 轮次归属记在 `iteration` 字段（`r01`/`r02`/…），**不塞进版本号** ——
> 因为同一版本可能跨多轮才定稿，把轮次编码进版本号会造成 `1.0.r02` → `1.0.r03` 的假升级。

---

## 1. 四级分区

**不是所有文件都需要版本号。** 分级依据是「这份内容重复写错的代价有多高」。

| 级别 | 名称 | 版本化 | 字段 | 判定理由 | 数量 |
|---|---|---|---|---|---|
| **A** | 结论性内容 | ✅ | `content_version` | 随轮次演化、重复写错代价最高。文件内版本行 + 索引登记。 | 95 |
| **B** | 结构性文档 / 框架与库代码 | ✅ | `content_version` | 随框架演进但无『结论』性质。.md 加版本行；.py 只登记索引。 | 75 |
| **C** | 机器契约 | ❌ | — | 已有 schema_version / config_version / data_version / version 字段，各答不同问题。索引镜像其值，不重复加版本。 | 14 |
| **D** | 纯数据 / 分析脚本 | ❌ | — | raw 数据用 SHA256（比版本号更强的保证）；分析脚本随结论归档，不单独版本化。 | 28 |

**为什么 D 级（数据）不版本化**：`data/raw/` 已有 **SHA256**，
那是**比版本号更强的完整性保证** —— 版本号只能告诉你「变了」，
SHA256 能告诉你「**具体哪里**变了」。给数据加版本号是双重记账。

**为什么 B 级的 `.py` 不写文件内版本行**：代码的版本信息由 `git blame` 提供，
且远比手写版本行精确。在代码里加注释版本行是纯噪音。

---

## 2. 全量文件版本表

### A 级 · 结论性内容

| 路径 | 版本 | 轮次 | 更新日 | 状态 | 备注 |
|---|---|---|---|---|---|
| `AGENTS.md` | `1.0` | `r06` | 2026-10-11 | active | 给 AI 的操作规则极简入口（六域，指向 AI_CONTEXT） |
| `AI_MAP.md` | `1.0` | `r06` | 2026-10-11 | generated | 机器地图（派生物，render_ai_map 生成） |
| `DEPENDENCY_MAP.md` | `1.0` | `r06` | 2026-10-11 | generated | 跨文件依赖图（派生物，render_dependency_map 生成） |
| `FLYWHEEL_HEALTH.md` | `1.0` | `r06` | 2026-10-11 | generated | 飞轮健康度仪表盘（派生物，render_flywheel_health 生成） |
| `framework/tools/compress_memory.py` | `1.0` | `r06` | 2026-10-11 | active | 记忆压缩（每 5 轮）：ACTIVE.md + merge 候选 + 到期清单（IterResearch 依据） |
| `framework/tools/ingate.py` | `1.0` | `r06` | 2026-10-11 | active | 入库三闸门（filter/judge/manager，LSTM-MAS 依据） |
| `games/dlt/iterations/round02/FINDINGS.md` | `1.0` | `r02` | 2026-10-11 | active | 整理入库轮发现 |
| `games/dlt/iterations/round02/HANDOFF.md` | `1.0` | `r02` | 2026-10-11 | active | r02→r03 交接 |
| `games/dlt/iterations/round02/PRIORITY_TASKS.md` | `1.0` | `r02` | 2026-10-11 | active |  |
| `games/dlt/iterations/round02/TASK_BRIEF.md` | `1.0` | `r02` | 2026-10-11 | active | 已交付 |
| `games/dlt/iterations/round02/known_errors.md` | `1.0` | `r02` | 2026-10-11 | active | E1~E9 避坑手册 |
| `games/dlt/iterations/round02/legacy_findings/README.md` | `1.0` | `r02` | 2026-10-11 | active | 归档，设使用门槛 |
| `games/dlt/iterations/round02/legacy_findings/_round3_reference/round3_independent_review.html` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `games/dlt/iterations/round02/legacy_findings/round2_deep_analysis.txt` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `games/dlt/iterations/round02/legacy_findings/round2_glm_analysis.txt` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `games/dlt/iterations/round02/legacy_findings/round2_main_report.md` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `games/dlt/iterations/round02/legacy_findings/round2_verify_analysis.txt` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `games/dlt/iterations/round03/FINDINGS.md` | `1.0` | `r03` | 2026-10-11 | active | 复核轮发现（含自我纠错） |
| `games/dlt/iterations/round03/HANDOFF.md` | `1.0` | `r03` | 2026-10-11 | active | r03→r04 交接 |
| `games/dlt/iterations/round03/TASK_BRIEF.md` | `1.0` | `r03` | 2026-10-11 | active | 已交付 |
| `games/dlt/iterations/round03/scripts/apply_r03_facts.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/apply_r03_strategy.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/b2_robust_estimators.json` | `1.0` | `r03` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/b2_robust_estimators.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/b2_split_stability.json` | `1.0` | `r03` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/b2_split_stability.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.json` | `1.0` | `r03` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/FINDINGS.md` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/HANDOFF.md` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/TASK_BRIEF.md` | `1.0` | `r04` | 2026-10-11 | active | 已交付（round04 执行完毕） |
| `games/dlt/iterations/round04/scripts/apply_r04_facts.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/scripts/apply_r04_strategy.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/scripts/back_collision.json` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/scripts/back_collision.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/scripts/decay_cause.json` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/scripts/decay_cause.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/scripts/prize_mechanism_tobit.json` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/scripts/prize_mechanism_tobit.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `games/dlt/iterations/round05/FINDINGS.md` | `1.0` | `r05` | 2026-10-11 | active | 投注方式数学层 + R-002 量化 + 时间因素证伪 |
| `games/dlt/iterations/round05/HANDOFF.md` | `1.0` | `r05` | 2026-10-11 | active | r05→r06 交接；策略变更待用户批准 |
| `games/dlt/iterations/round05/TASK_BRIEF.md` | `1.0` | `r05` | 2026-10-11 | active | 已交付（round05 执行完毕；用户点名方向优先，T-201 顺延 r06） |
| `games/dlt/iterations/round05/scripts/apply_r05_facts.py` | `1.0` | `r05` | 2026-10-11 | active | F-0026~F-0032 落地 |
| `games/dlt/iterations/round05/scripts/bet_structure.json` | `1.0` | `r05` | 2026-10-11 | active |  |
| `games/dlt/iterations/round05/scripts/bet_structure.py` | `1.0` | `r05` | 2026-10-11 | active | 投注方式 + R-002 量化 + R-003 候选模拟 |
| `games/dlt/iterations/round05/scripts/fix_r05_housekeeping.py` | `1.0` | `r05` | 2026-10-11 | active | 收轮维护（tags/versions/计数） |
| `games/dlt/iterations/round05/scripts/sync_r05_versions.py` | `1.0` | `r05` | 2026-10-11 | active |  |
| `games/dlt/iterations/round05/scripts/timing_weekday.json` | `1.0` | `r05` | 2026-10-11 | active |  |
| `games/dlt/iterations/round05/scripts/timing_weekday.py` | `1.0` | `r05` | 2026-10-11 | active | 星期/奖池时序/节假日窗口 |
| `games/dlt/iterations/round06/FINDINGS.md` | `1.0` | `r06` | 2026-10-11 | active | r06 元层轮发现（策略落地+飞轮升级） |
| `games/dlt/iterations/round06/HANDOFF.md` | `1.0` | `r06` | 2026-10-11 | active | r06→r07 交接（结论/遗留/下轮建议） |
| `games/dlt/iterations/round06/TASK_BRIEF.md` | `1.0` | `r06` | 2026-10-11 | active | 由 round05 HANDOFF 转写（planned；T-201 前段取证首推） |
| `games/dlt/iterations/round06/manifest.json` | `1.0` | `r06` | 2026-10-11 | active | r06 机器登记 |
| `games/dlt/iterations/round06/research/ai_readability_proposal.md` | `1.0` | `r06` | 2026-10-11 | active | AI 可读性升级方案稿（P0/P1/P2，待批准） |
| `games/dlt/iterations/round06/research/flywheel_upgrade_plan.md` | `1.0` | `r06` | 2026-10-11 | active | 迭代飞轮全局升级计划（A-K 环节链路 + 分批） |
| `games/dlt/iterations/round06/scripts/add_v2_fields.py` | `1.0` | `r06` | 2026-10-11 | active | FACTS v2.0 字段迁移（grade/change_type/有效期） |
| `games/dlt/iterations/round06/scripts/apply_r06_strategy.py` | `1.0` | `r06` | 2026-10-11 | active | 用户批准三项策略变更落地 |
| `games/dlt/iterations/round06/scripts/fix_rename_remainder.py` | `1.0` | `r06` | 2026-10-11 | active | 改名残余引用修正（路径/import/标识） |
| `games/dlt/iterations/round06/scripts/probe_r06.py` | `1.0` | `r06` | 2026-10-11 | active | 探查原语与结论原文 |
| `games/dlt/iterations/round06/scripts/probe_v2.py` | `1.0` | `r06` | 2026-10-11 | active | v2.0 实施前的 FACTS/结构探查 |
| `games/dlt/iterations/round06/scripts/rename_spc.py` | `1.0` | `r06` | 2026-10-11 | active | 全链路改名：git mv src→spc + 包/品牌替换 |
| `games/dlt/iterations/round06/scripts/smoke_ingate.py` | `1.0` | `r06` | 2026-10-11 | active | 三闸门自测（缺陷→拒绝 / 合法→入库） |
| `games/dlt/iterations/round06/scripts/smoke_r06.py` | `1.0` | `r06` | 2026-10-11 | active | 新原语 + R-002/R-003 可执行性冒烟 |
| `games/dlt/iterations/round06/scripts/sync_guide_v14.py` | `1.0` | `r06` | 2026-10-11 | active | STRATEGY_GUIDE v1.4 同步 |
| `games/dlt/iterations/round06/scripts/sync_structure_registration.py` | `1.0` | `r06` | 2026-10-11 | active | 结构完整性补登记 + 目录树写回（P1-2） |
| `games/dlt/iterations/round06/scripts/sync_v2_final.py` | `1.0` | `r06` | 2026-10-11 | active | v2.0 收尾：版本登记 + README 计数同步 |
| `games/dlt/iterations/round06/scripts/sync_v2_versions.py` | `1.0` | `r06` | 2026-10-11 | active | v2.0 版本登记与 README 同步 |
| `games/dlt/iterations/round06/scripts/versions_r06_strategy.py` | `1.0` | `r06` | 2026-10-11 | active | r06 策略落地的版本登记 |
| `games/dlt/iterations/round07/FINDINGS.md` | `1.0` | `r07` | 2026-10-11 | active | 前段取证+外部核对+节假日验证+锚点重校准 |
| `games/dlt/iterations/round07/HANDOFF.md` | `1.0` | `r07` | 2026-10-11 | active | r07→r08 交接 |
| `games/dlt/iterations/round07/TASK_BRIEF.md` | `1.0` | `r07` | 2026-10-11 | active | r07 任务书（render_task_brief 生成，T-014 评分居首） |
| `games/dlt/iterations/round07/scripts/apply_r07_facts.py` | `1.0` | `r07` | 2026-10-11 | active | r07 结论入库 |
| `games/dlt/iterations/round07/scripts/t013_recalibrate.json` | `1.0` | `r07` | 2026-10-11 | active | 重校准结果 |
| `games/dlt/iterations/round07/scripts/t013_recalibrate.py` | `1.0` | `r07` | 2026-10-11 | active | F-0004/F-0005 重校准 |
| `games/dlt/iterations/round07/scripts/t014_forensics.json` | `1.0` | `r07` | 2026-10-11 | active | T-014 结果 |
| `games/dlt/iterations/round07/scripts/t014_forensics.py` | `1.0` | `r07` | 2026-10-11 | active | T-014 前段取证（F-0033） |
| `games/dlt/iterations/round07/scripts/t015_external.json` | `1.0` | `r07` | 2026-10-11 | active | T-015 结果 |
| `games/dlt/iterations/round07/scripts/t015_external.py` | `1.0` | `r07` | 2026-10-11 | active | T-015 外部核对（F-0034） |
| `games/dlt/iterations/round07/scripts/t016_holiday.json` | `1.0` | `r07` | 2026-10-11 | active | T-016 结果 |
| `games/dlt/iterations/round07/scripts/t016_holiday.py` | `1.0` | `r07` | 2026-10-11 | active | T-016 节假日验证（F-0035） |
| `games/dlt/rules_history.md` | `1.1` | `r03` | 2026-10-11 | active | E0~E6 共 7 段（§3.3 措辞存疑；第 6 次实证已加 r03 更正标记） |
| `games/dlt/strategy/STRATEGY_GUIDE.md` | `1.5` | `r07` | 2026-10-11 | active | r07：数据可靠性段升级（F-0033/F-0034 根因定位）；consumes 补齐 F-0002/F-0026~F-0029 |
| `memory/INDEX.md` | `1.0` | `r02` | 2026-10-11 | active | 记忆层说明 |
| `memory/facts/FACTS.jsonl` | `1.2` | `r07` | 2026-10-11 | active | 35 条结论（F-0001~F-0035；F-0032 superseded；F-0004/F-0005 重校准维持） |
| `memory/facts/INDEX.md` | `1.5` | `r04` | 2026-10-11 | active | 派生物，由 cli index 生成（32 条） |
| `memory/journal/round02.md` | `1.0` | `r02` | 2026-10-11 | active | 整理入库轮 |
| `memory/journal/round03.md` | `1.0` | `r03` | 2026-10-11 | active | 复核轮（含 1 次自我纠错） |
| `memory/journal/round04.md` | `1.0` | `r04` | 2026-10-11 | active |  |
| `memory/journal/round06.md` | `1.0` | `r06` | 2026-10-11 | active | r06 叙事（元层轮） |
| `memory/journal/round07.md` | `1.0` | `r07` | 2026-10-11 | active | r07 叙事（研究轮） |
| `memory/lessons/LESSONS.md` | `1.2` | `r04` | 2026-10-11 | active | L1–L14，只增不删（r04 新增 L13 口径自由度 / L14 分段自洽性前置检查；L7 追加第二实例） |
| `memory/spec/ITERATION_SOP_v2.md` | `1.3` | `r07` | 2026-10-11 | active | r07：收尾清单新增第 9 步『统一注入版本行』（版本行单一来源：inject/生成器，禁止手写） |
| `memory/workbench/HYPOTHESES.md` | `1.2` | `r07` | 2026-10-11 | active | H-001~H-006（H-006 refuted） |
| `memory/workbench/OPEN_QUESTIONS.md` | `1.4` | `r07` | 2026-10-11 | active | 11 问，5 answered（Q-001/002/004/013/014） |
| `memory/workbench/TODO.md` | `1.6` | `r07` | 2026-10-11 | active | T-014/T-015/T-016 已交付 |

### B 级 · 结构性文档 / 框架与库代码

| 路径 | 版本 | 轮次 | 状态 | 备注 |
|---|---|---|---|---|
| `AI_CONTEXT.md` | `1.5` | `r05` | active | 单一入口；r05 同步投注方式等价性、R-002 量化不成立、H-005 证伪、32 条结论 |
| `README.md` | `1.15` | `r07` | active | 仓库总览；r05 研究要点 + r06 策略落地（R-002 重构 / R-003 新增，用户批准）+ r07 修复轮（下游声明完整性）；35 条结论、212 条登记 |
| `VERSION_INDEX.md` | `1.0` | `r02` | active | 版本索引（人读），权威源是 versions.json |
| `cli/main.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `docs/ARCHITECTURE.md` | `1.1` | `r03` | active |  |
| `docs/CONSUMING.md` | `1.1` | `r02` | active |  |
| `docs/ITERATION_GUIDE.md` | `1.0` | `r02` | active |  |
| `docs/METHODOLOGY.md` | `1.0` | `r02` | active |  |
| `docs/PROPOSAL_SINGLE_TICKET_CORE.md` | `1.1` | `r03` | active |  |
| `docs/VERSIONING_DOCS.md` | `1.3` | `r03` | active |  |
| `framework/INDEX.md` | `1.1` | `r03` | active |  |
| `framework/README.md` | `1.0` | `r02` | active |  |
| `framework/core/README.md` | `1.1` | `r03` | active |  |
| `framework/core/__init__.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/evaluate.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/features.py` | —（见备注） | `r06` | active | 新增跨注原语 duplicate_ticket_count / duplicate_ticket_count_ge（F-0027 判定量） |
| `framework/core/game_util.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/generate.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/judge.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/portfolio.py` | —（见备注） | `—` | active | ★ 跨注层（L3）核心：Portfolio 一等公民 + 跨注求值 + judge_cross |
| `framework/core/ticket.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/methodology/MATH_BOUNDARY.md` | `1.0` | `r02` | active |  |
| `framework/methodology/STATISTICAL_DISCIPLINE.md` | `1.0` | `r02` | active |  |
| `framework/protocol/ITERATION_PROTOCOL.md` | `1.1` | `r03` | active |  |
| `framework/protocol/MEMORY_PROTOCOL.md` | `1.2` | `r03` | active | r03 框架迭代：新增 §1.7 claim_type 证据类型 + §1.8 证据锚定 |
| `framework/protocol/README.md` | `1.0` | `r02` | active |  |
| `framework/protocol/templates/FINDINGS.template.md` | `1.0` | `r02` | active |  |
| `framework/protocol/templates/HANDOFF.template.md` | `1.0` | `r02` | active |  |
| `framework/protocol/templates/TASK_BRIEF.template.md` | `1.0` | `r02` | active |  |
| `framework/tools/memory.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `games/INDEX.md` | `1.2` | `r04` | active | 彩种索引（r04：结论数 18 → 25；轮次 round04 ✅ / round05 计划中） |
| `games/_template/README.md` | —（见备注） | `—` | active |  |
| `games/_template/data/build_scripts/README.md` | —（见备注） | `—` | active |  |
| `games/_template/data/derived/README.md` | —（见备注） | `—` | active |  |
| `games/_template/data/raw/README.md` | —（见备注） | `—` | active |  |
| `games/_template/data/tools/README.md` | —（见备注） | `—` | active |  |
| `games/_template/iterations/round01/TASK_BRIEF.md` | —（见备注） | `—` | active |  |
| `games/dlt/iterations/round05/manifest.json` | `1.0` | `r05` | active |  |
| `memory/journal/round05.md` | `1.0` | `r05` | active | 叙事：R-002 量化不成立 + H-005 证伪 |
| `spec/README.md` | `1.0` | `r02` | active |  |
| `spec/VERSIONING.md` | `1.2` | `r03` | active |  |
| `src/__init__.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/__init__.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/ai_map.py` | —（见备注） | `—` | active | AI_MAP 生成源（llms.txt 式机器地图） |
| `src/spc/api.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/depmap.py` | —（见备注） | `—` | active | 跨文件依赖图生成源（C） |
| `src/spc/evidence.py` | —（见备注） | `r03` | active | ★ 证据锚定：sha256_file / fact_anchor / evidence_digest（结论与策略的哈希锚） |
| `src/spc/flywheel.py` | —（见备注） | `—` | active | 飞轮健康度统计 + 置信度校准（K/D1） |
| `src/spc/game.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/memory.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/strategy.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/tree.py` | —（见备注） | `r06` | active | 目录树生成源（P1-2）：README 树 = 派生物 |
| `src/spc/validate.py` | —（见备注） | `r06` | active | r07：新增 _check_consumes_completeness 逆向声明完整性检查 |
| `src/spc/versions.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tests/README.md` | `1.5` | `r06` | active | 测试说明（自举计数：合计 333，含 test_structure 8） |
| `tests/test_ai_readability.py` | —（见备注） | `—` | active | P1/P2/B/H/I 测试 |
| `tests/test_claim_type.py` | —（见备注） | `r03` | active | ★ 结论证据类型测试（五类约束真的会拦 / schema 与 Python 双通道一致）；无需 pytest |
| `tests/test_consumes_completeness.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tests/test_core.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tests/test_cross_scope.py` | —（见备注） | `—` | active | ★ 跨注层测试（scope 三分 / 跨注判定 / 结构性拒收）；无需 pytest |
| `tests/test_evidence_anchor.py` | —（见备注） | `r03` | active | ★ 证据锚定测试（漂移真能检出 / 该敏感的要敏感、该迟钝的要迟钝 / 重基线幂等）；无需 pytest |
| `tests/test_flywheel.py` | —（见备注） | `—` | active | K/D1/D2/C/F 测试（无需 pytest） |
| `tests/test_shadow_game.py` | `1.0` | `r03` | active |  |
| `tests/test_structure.py` | —（见备注） | `r06` | active | 结构完整性回归测试（P1-2 三道防线） |
| `tools/build_versions.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tools/inject_version_lines.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tools/register_r06_upgrade.py` | —（见备注） | `—` | active | r06 批量实施登记脚本（一次性，登记含自身） |
| `tools/render_ai_map.py` | —（见备注） | `—` | active | AI_MAP.md 渲染器（--write 写回） |
| `tools/render_dependency_map.py` | —（见备注） | `—` | active | DEPENDENCY_MAP.md 渲染器 |
| `tools/render_flywheel_health.py` | —（见备注） | `—` | active | FLYWHEEL_HEALTH.md 渲染器 |
| `tools/render_readme_tree.py` | —（见备注） | `r06` | active | 目录树渲染 CLI（--write 写回 README） |
| `tools/render_task_brief.py` | —（见备注） | `—` | active | 下轮任务书生成器（B+G 价值评分） |
| `tools/render_version_index.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tools/report_calibration.py` | —（见备注） | `—` | active | 置信度校准报告（D1） |
| `versions.json` | `1.0` | `r02` | generated |  |

### C 级 · 机器契约（用自身既有版本字段）

| 路径 | 版本字段 | 值 | 备注 |
|---|---|---|---|
| `games/_template/game.yaml` | `config_version` | `2.0` | 2026-10-11 与 dlt 同步升至 2.0（features 原语化） |
| `games/_template/strategy/strategy.json` | `config_version` | `2.0` | 模板策略，2026-10-11 随 game.yaml 同步至 2.0 |
| `games/dlt/game.yaml` | `config_version` | `2.1` | 跨注特征 3→5（新增 identical_ticket_count / has_identical_tickets）；has_duplicated_structure 改为无规则引用（R-002 已重构） |
| `games/dlt/iterations/round02/manifest.json` | `inputs.data_version` | `dlt_full_2933` |  |
| `games/dlt/iterations/round03/manifest.json` | `inputs.data_version` | `dlt_full_2933` |  |
| `games/dlt/iterations/round04/manifest.json` | `—` | `—` |  |
| `games/dlt/iterations/round07/manifest.json` | `inputs.data_version` | `dlt_full_2933` | r07 机器登记 |
| `games/dlt/strategy/strategy.json` | `schema_version` | `1.1` | r06（用户批准）：R-002 → exclude + 禁止完全相同号码；新增 R-003（F-0029）；provenance round06 |
| `pyproject.toml` | `project.version` | `0.1.0` | 包版本 |
| `spec/fact.schema.json` | `—` | `—` | v2.0：新增 confidence_grade（GRADE）/ change_type（update-revision）/ valid_until / recalibrate_every |
| `spec/game_config.schema.json` | `—` | `—` | schema 自身无版本；约束 game_config.config_version |
| `spec/iteration.schema.json` | `—` | `—` | schema 自身无版本；约束 iteration 结构 |
| `spec/strategy.schema.json` | `—` | `—` | schema 自身无版本；约束 strategy.schema_version |
| `spec/version_index.schema.json` | `—` | `—` | schema 自身无版本；约束 versions.index_version |

### D 级 · 纯数据 / 分析脚本（不版本化）

| 路径 | 类型 | SHA256（raw） | 备注 |
|---|---|---|---|
| `.gitignore` | `meta` | — |  |
| `games/dlt/data/build_scripts/build_derived_v4.py` | `build_script` | — |  |
| `games/dlt/data/build_scripts/hash_and_list.py` | `build_script` | — |  |
| `games/dlt/data/build_scripts/validate_package_v4.py` | `build_script` | — |  |
| `games/dlt/data/derived/01_yearly_stats.csv` | `derived_data` | — |  |
| `games/dlt/data/derived/02_front_number_frequency.csv` | `derived_data` | — |  |
| `games/dlt/data/derived/03_back_number_frequency.csv` | `derived_data` | — |  |
| `games/dlt/data/derived/04_structure_distribution_exact.json` | `derived_data` | — |  |
| `games/dlt/data/derived/05_back_combo_66.csv` | `derived_data` | — |  |
| `games/dlt/data/derived/06_acf_lag1to60.csv` | `derived_data` | — |  |
| `games/dlt/data/derived/07_data_quality_report.json` | `derived_data` | — |  |
| `games/dlt/data/derived/08_rules_epoch_summary.json` | `derived_data` | — |  |
| `games/dlt/data/raw/dlt_full_2933.csv` | `raw_data` | `9e92848e184c7715…` | SHA256 为准，不做内容版本 |
| `games/dlt/data/raw/dlt_full_2933.jsonl` | `raw_data` | `11a1714e9c850a7d…` | SHA256 为准，不做内容版本 |
| `games/dlt/data/tools/_load.py` | `analysis_script` | — |  |
| `games/dlt/data/tools/acf_permutation_test.py` | `analysis_script` | — |  |
| `games/dlt/data/tools/changepoint_refine.py` | `analysis_script` | — |  |
| `games/dlt/data/tools/changepoint_scan.py` | `analysis_script` | — |  |
| `games/dlt/data/tools/consecutive_exact_check.py` | `analysis_script` | — |  |
| `games/dlt/data/tools/exact_tests.py` | `analysis_script` | — |  |
| `games/dlt/data/tools/overdispersion_and_hac.py` | `analysis_script` | — |  |
| `games/dlt/data/tools/validate_data.py` | `analysis_script` | — |  |
| `games/dlt/manifest_v4_source.json` | `source_manifest` | — |  |
| `games/dlt/strategy/simulation_results.json` | `analysis_output` | — |  |
| `games/dlt/strategy/strategy_simulation.py` | `analysis_script` | — |  |
| `memory/facts/ACTIVE.md` | `report` | — | 当前有效结论清单（与台账分离，compress_memory 生成） |
| `tests/fixtures/shadow/game.yaml` | `test_fixture` | — |  |
| `tools/count_tests.py` | `test_tool` | — |  |

---

## 3. 按内容类型检索

| 类型 | 数量 | 级别 | 文件 |
|---|---|---|---|
| `iteration_artifact` | 44 | A | `games/dlt/iterations/round02/FINDINGS.md`<br>`games/dlt/iterations/round02/HANDOFF.md`<br>`games/dlt/iterations/round02/PRIORITY_TASKS.md`<br>`games/dlt/iterations/round02/TASK_BRIEF.md`<br>`games/dlt/iterations/round02/known_errors.md`<br>`games/dlt/iterations/round02/legacy_findings/README.md`<br>`games/dlt/iterations/round02/legacy_findings/_round3_reference/round3_independent_review.html`<br>`games/dlt/iterations/round02/legacy_findings/round2_deep_analysis.txt`<br>`games/dlt/iterations/round02/legacy_findings/round2_glm_analysis.txt`<br>`games/dlt/iterations/round02/legacy_findings/round2_main_report.md`<br>`games/dlt/iterations/round02/legacy_findings/round2_verify_analysis.txt`<br>`games/dlt/iterations/round03/FINDINGS.md`<br>`games/dlt/iterations/round03/HANDOFF.md`<br>`games/dlt/iterations/round03/TASK_BRIEF.md`<br>`games/dlt/iterations/round03/scripts/apply_r03_facts.py`<br>`games/dlt/iterations/round03/scripts/apply_r03_strategy.py`<br>`games/dlt/iterations/round03/scripts/b2_robust_estimators.json`<br>`games/dlt/iterations/round03/scripts/b2_robust_estimators.py`<br>`games/dlt/iterations/round03/scripts/b2_split_stability.json`<br>`games/dlt/iterations/round03/scripts/b2_split_stability.py`<br>`games/dlt/iterations/round03/scripts/cap_adjusted_uplift.json`<br>`games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`<br>`games/dlt/iterations/round04/FINDINGS.md`<br>`games/dlt/iterations/round04/HANDOFF.md`<br>`games/dlt/iterations/round04/TASK_BRIEF.md`<br>`games/dlt/iterations/round04/scripts/apply_r04_facts.py`<br>`games/dlt/iterations/round04/scripts/apply_r04_strategy.py`<br>`games/dlt/iterations/round04/scripts/back_collision.json`<br>`games/dlt/iterations/round04/scripts/back_collision.py`<br>`games/dlt/iterations/round04/scripts/decay_cause.json`<br>`games/dlt/iterations/round04/scripts/decay_cause.py`<br>`games/dlt/iterations/round04/scripts/prize_mechanism_tobit.json`<br>`games/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`<br>`games/dlt/iterations/round05/FINDINGS.md`<br>`games/dlt/iterations/round05/HANDOFF.md`<br>`games/dlt/iterations/round05/TASK_BRIEF.md`<br>`games/dlt/iterations/round06/FINDINGS.md`<br>`games/dlt/iterations/round06/HANDOFF.md`<br>`games/dlt/iterations/round06/TASK_BRIEF.md`<br>`games/dlt/iterations/round06/manifest.json`<br>`games/dlt/iterations/round07/FINDINGS.md`<br>`games/dlt/iterations/round07/HANDOFF.md`<br>`games/dlt/iterations/round07/TASK_BRIEF.md`<br>`memory/journal/round04.md` |
| `script` | 25 | A | `framework/tools/compress_memory.py`<br>`framework/tools/ingate.py`<br>`games/dlt/iterations/round05/scripts/apply_r05_facts.py`<br>`games/dlt/iterations/round05/scripts/bet_structure.py`<br>`games/dlt/iterations/round05/scripts/fix_r05_housekeeping.py`<br>`games/dlt/iterations/round05/scripts/sync_r05_versions.py`<br>`games/dlt/iterations/round05/scripts/timing_weekday.py`<br>`games/dlt/iterations/round06/scripts/add_v2_fields.py`<br>`games/dlt/iterations/round06/scripts/apply_r06_strategy.py`<br>`games/dlt/iterations/round06/scripts/fix_rename_remainder.py`<br>`games/dlt/iterations/round06/scripts/probe_r06.py`<br>`games/dlt/iterations/round06/scripts/probe_v2.py`<br>`games/dlt/iterations/round06/scripts/rename_spc.py`<br>`games/dlt/iterations/round06/scripts/smoke_ingate.py`<br>`games/dlt/iterations/round06/scripts/smoke_r06.py`<br>`games/dlt/iterations/round06/scripts/sync_guide_v14.py`<br>`games/dlt/iterations/round06/scripts/sync_structure_registration.py`<br>`games/dlt/iterations/round06/scripts/sync_v2_final.py`<br>`games/dlt/iterations/round06/scripts/sync_v2_versions.py`<br>`games/dlt/iterations/round06/scripts/versions_r06_strategy.py`<br>`games/dlt/iterations/round07/scripts/apply_r07_facts.py`<br>`games/dlt/iterations/round07/scripts/t013_recalibrate.py`<br>`games/dlt/iterations/round07/scripts/t014_forensics.py`<br>`games/dlt/iterations/round07/scripts/t015_external.py`<br>`games/dlt/iterations/round07/scripts/t016_holiday.py` |
| `doc` | 19 | A/B | `AGENTS.md`<br>`AI_MAP.md`<br>`DEPENDENCY_MAP.md`<br>`FLYWHEEL_HEALTH.md`<br>`games/dlt/iterations/round06/research/ai_readability_proposal.md`<br>`games/dlt/iterations/round06/research/flywheel_upgrade_plan.md`<br>`memory/spec/ITERATION_SOP_v2.md`<br>`README.md`<br>`docs/ARCHITECTURE.md`<br>`docs/CONSUMING.md`<br>`docs/ITERATION_GUIDE.md`<br>`docs/METHODOLOGY.md`<br>`docs/PROPOSAL_SINGLE_TICKET_CORE.md`<br>`docs/VERSIONING_DOCS.md`<br>`framework/README.md`<br>`framework/core/README.md`<br>`spec/README.md`<br>`spec/VERSIONING.md`<br>`tests/README.md` |
| `code` | 12 | B | `src/spc/ai_map.py`<br>`src/spc/depmap.py`<br>`src/spc/flywheel.py`<br>`src/spc/tree.py`<br>`tests/test_structure.py`<br>`tools/register_r06_upgrade.py`<br>`tools/render_ai_map.py`<br>`tools/render_dependency_map.py`<br>`tools/render_flywheel_health.py`<br>`tools/render_readme_tree.py`<br>`tools/render_task_brief.py`<br>`tools/report_calibration.py` |
| `analysis_script` | 9 | D | `games/dlt/data/tools/_load.py`<br>`games/dlt/data/tools/acf_permutation_test.py`<br>`games/dlt/data/tools/changepoint_refine.py`<br>`games/dlt/data/tools/changepoint_scan.py`<br>`games/dlt/data/tools/consecutive_exact_check.py`<br>`games/dlt/data/tools/exact_tests.py`<br>`games/dlt/data/tools/overdispersion_and_hac.py`<br>`games/dlt/data/tools/validate_data.py`<br>`games/dlt/strategy/strategy_simulation.py` |
| `library` | 9 | B | `src/__init__.py`<br>`src/spc/__init__.py`<br>`src/spc/api.py`<br>`src/spc/evidence.py`<br>`src/spc/game.py`<br>`src/spc/memory.py`<br>`src/spc/strategy.py`<br>`src/spc/validate.py`<br>`src/spc/versions.py` |
| `derived_data` | 8 | D | `games/dlt/data/derived/01_yearly_stats.csv`<br>`games/dlt/data/derived/02_front_number_frequency.csv`<br>`games/dlt/data/derived/03_back_number_frequency.csv`<br>`games/dlt/data/derived/04_structure_distribution_exact.json`<br>`games/dlt/data/derived/05_back_combo_66.csv`<br>`games/dlt/data/derived/06_acf_lag1to60.csv`<br>`games/dlt/data/derived/07_data_quality_report.json`<br>`games/dlt/data/derived/08_rules_epoch_summary.json` |
| `framework_core` | 8 | B | `framework/core/__init__.py`<br>`framework/core/evaluate.py`<br>`framework/core/features.py`<br>`framework/core/game_util.py`<br>`framework/core/generate.py`<br>`framework/core/judge.py`<br>`framework/core/portfolio.py`<br>`framework/core/ticket.py` |
| `test` | 8 | B | `tests/test_ai_readability.py`<br>`tests/test_claim_type.py`<br>`tests/test_consumes_completeness.py`<br>`tests/test_core.py`<br>`tests/test_cross_scope.py`<br>`tests/test_evidence_anchor.py`<br>`tests/test_flywheel.py`<br>`tests/test_shadow_game.py` |
| `report` | 7 | A/D | `games/dlt/iterations/round05/scripts/bet_structure.json`<br>`games/dlt/iterations/round05/scripts/timing_weekday.json`<br>`games/dlt/iterations/round07/scripts/t013_recalibrate.json`<br>`games/dlt/iterations/round07/scripts/t014_forensics.json`<br>`games/dlt/iterations/round07/scripts/t015_external.json`<br>`games/dlt/iterations/round07/scripts/t016_holiday.json`<br>`memory/facts/ACTIVE.md` |
| `template_game` | 6 | B | `games/_template/README.md`<br>`games/_template/data/build_scripts/README.md`<br>`games/_template/data/derived/README.md`<br>`games/_template/data/raw/README.md`<br>`games/_template/data/tools/README.md`<br>`games/_template/iterations/round01/TASK_BRIEF.md` |
| `journal` | 5 | A/B | `memory/journal/round02.md`<br>`memory/journal/round03.md`<br>`memory/journal/round06.md`<br>`memory/journal/round07.md`<br>`memory/journal/round05.md` |
| `schema` | 5 | C | `spec/fact.schema.json`<br>`spec/game_config.schema.json`<br>`spec/iteration.schema.json`<br>`spec/strategy.schema.json`<br>`spec/version_index.schema.json` |
| `iteration_manifest` | 4 | C | `games/dlt/iterations/round02/manifest.json`<br>`games/dlt/iterations/round03/manifest.json`<br>`games/dlt/iterations/round04/manifest.json`<br>`games/dlt/iterations/round07/manifest.json` |
| `build_script` | 3 | D | `games/dlt/data/build_scripts/build_derived_v4.py`<br>`games/dlt/data/build_scripts/hash_and_list.py`<br>`games/dlt/data/build_scripts/validate_package_v4.py` |
| `index` | 3 | A/B | `memory/INDEX.md`<br>`framework/INDEX.md`<br>`games/INDEX.md` |
| `protocol` | 3 | B | `framework/protocol/ITERATION_PROTOCOL.md`<br>`framework/protocol/MEMORY_PROTOCOL.md`<br>`framework/protocol/README.md` |
| `repo_tool` | 3 | B | `tools/build_versions.py`<br>`tools/inject_version_lines.py`<br>`tools/render_version_index.py` |
| `template` | 3 | B | `framework/protocol/templates/FINDINGS.template.md`<br>`framework/protocol/templates/HANDOFF.template.md`<br>`framework/protocol/templates/TASK_BRIEF.template.md` |
| `workbench` | 3 | A | `memory/workbench/HYPOTHESES.md`<br>`memory/workbench/OPEN_QUESTIONS.md`<br>`memory/workbench/TODO.md` |
| `game_config` | 2 | C | `games/_template/game.yaml`<br>`games/dlt/game.yaml` |
| `methodology` | 2 | B | `framework/methodology/MATH_BOUNDARY.md`<br>`framework/methodology/STATISTICAL_DISCIPLINE.md` |
| `raw_data` | 2 | D | `games/dlt/data/raw/dlt_full_2933.csv`<br>`games/dlt/data/raw/dlt_full_2933.jsonl` |
| `strategy` | 2 | C | `games/_template/strategy/strategy.json`<br>`games/dlt/strategy/strategy.json` |
| `analysis_output` | 1 | D | `games/dlt/strategy/simulation_results.json` |
| `cli` | 1 | B | `cli/main.py` |
| `entry_point` | 1 | B | `AI_CONTEXT.md` |
| `fact_index` | 1 | A | `memory/facts/INDEX.md` |
| `fact_ledger` | 1 | A | `memory/facts/FACTS.jsonl` |
| `framework_tool` | 1 | B | `framework/tools/memory.py` |
| `lesson_library` | 1 | A | `memory/lessons/LESSONS.md` |
| `manifest` | 1 | B | `games/dlt/iterations/round05/manifest.json` |
| `meta` | 1 | D | `.gitignore` |
| `package_manifest` | 1 | C | `pyproject.toml` |
| `rules_history` | 1 | A | `games/dlt/rules_history.md` |
| `source_manifest` | 1 | D | `games/dlt/manifest_v4_source.json` |
| `strategy_guide` | 1 | A | `games/dlt/strategy/STRATEGY_GUIDE.md` |
| `test_fixture` | 1 | D | `tests/fixtures/shadow/game.yaml` |
| `test_tool` | 1 | D | `tools/count_tests.py` |
| `version_index` | 1 | B | `versions.json` |
| `version_index_doc` | 1 | B | `VERSION_INDEX.md` |

---

## 4. 版本演化史

> 追加式，**不删历史行**。

| 版本 | 日期 | 范围 | 变更 |
|---|---|---|---|
| `1.7` | 2026-10-11 | r07 修复（续） | STRATEGY_GUIDE consumes 补 F-0033/F-0034；登记 tests/test_consumes_completeness.py。 |
| `1.6` | 2026-10-11 | r07 修复 | 下游声明完整性修复：STRATEGY_GUIDE consumes 补齐 F-0002/F-0026~F-0029 并升 1.5；validate 新增逆向检查（正文引用未声明即拦截）；SOP 收尾清单新增第 8 步。 |
| `1.5` | 2026-10-11 | round07 | 登记 r07 研究轮 13 个产物；FACTS 32→35（+F-0033/34/35，F-0032 superseded）；F-0004/F-0005 重校准维持。 |
| `1.1` | 2026-10-11 | framework/ | 跨注层（L3）从『只上报』升级为『可执行』，记为 framework_version 1.1。新增 framework/core/portfolio.py（Portfolio 一等公民 + evaluate_cross + judge_cross）；features.py 新增 CROSS_PRIMITIVES 独立注册表（5 个跨注原语），与单注原语分开注册、混用结构性拒收；game.yaml 与 strategy.json 新增 scope: single/cross 声明（config 2.0→2.1 / schema 1.0→1.1）；judge.classify_rules() 三路切分（single / cross / undeclared），'跨注'与'拼错'不再混为一谈；validate_strategy() 对未声明特征由 warning 升为 error，并对跨注规则做真样本冒烟执行。修复 1.0 的契约缺口：R-002 引用了从未声明、且全仓库无执行入口的跨注特征。登记文件 124 → 126。 |
| `1.0` | 2026-10-11 | 全仓库 | 建立版本体系：引入 content_version（内容版本）与 framework_version（框架版本），与既有 schema_version / config_version / data_version 并存分区；登记 A/B/C/D 四级共 124 个文件。 |
| `1.0` | 2026-10-10 | framework/ | 单注层通用架构落地（framework/core/ 6 模块 / 21 原语），记为 framework_version 1.0。 |
| `1.2` | 2026-10-11 | A/B 级内容（结论层与文档层） | r04 轮次更新：结论台账 18 → 25 条（新增 F-0019~F-0025，更新 F-0003/F-0004/F-0011）；LESSONS 1.1 → 1.2（新增 L13/L14）；OPEN_QUESTIONS 1.2 → 1.3；TODO 1.4 → 1.5；HYPOTHESES 1.0 → 1.1；STRATEGY_GUIDE 1.1 → 1.2（口径同步）；strategy.json content 1.1 → 1.2；AI_CONTEXT 1.3 → 1.4；README 1.11 → 1.12。framework_version 保持 1.1（本轮未改框架代码）。 |

---

## 5. 维护规则

### 5.1 改内容时（谁改谁升）

| 你做了什么 | 版本怎么动 |
|---|---|
| 新增一条结论 / 新增一条教训 | `memory/facts/FACTS.jsonl` 次版本 +1 |
| 改了策略规则的幅度 | `strategy.json` 的 `content_version` 次版本 +1（`schema_version` **不动**） |
| 改了 `game.yaml` 的玩法/特征 | `config_version` 次版本 +1 |
| 改了框架协议 / 方法论 / core | `framework_version` 视情况 +1（结构变更升主版本） |
| 新增一轮迭代 | 新目录，各文件 `content_version` 从 `1.0` 起，`iteration` 记新轮次 |
| 改了某份文档的表述 | 该文档次版本 +1（**禁止静默改**） |

### 5.2 禁止事项

| 禁止 | 后果 |
|---|---|
| 手改 `VERSION_INDEX.md` | 会被下次生成覆盖（它是派生物） |
| 手改 `versions.json` 而不改对应文件 | `cli/main.py versions` 会报不一致 |
| 改内容但不升版本 | 索引记录的是**错的**，比没有索引更坏 |
| 把轮次编码进版本号 | 造成假升级（见 §0） |
| 给 D 级数据加版本号 | 与 SHA256 双重记账 |

### 5.3 三条自检命令

```bash
# 1) 版本一致性（文件内版本行 ↔ versions.json ↔ VERSION_INDEX.md）
python cli/main.py versions

# 2) 重新生成本索引（改完 versions.json 后）
python tools/render_version_index.py --write

# 3) 全量校验（含版本检查）
python cli/main.py validate --all -v
```

---

## 6. AI 读取顺序（带版本意识）

```
1. AI_CONTEXT.md                       ← 单一入口
2. VERSION_INDEX.md §0 + §2-A          ← ★ 先知道『我读的是哪一版』
3. memory/lessons/LESSONS.md           ← 禁令（记 L1–L9）
4. games/<g>/iterations/roundNN/TASK_BRIEF.md  ← 这轮做什么
5. memory/facts/INDEX.md               ← 结论速览
6. memory/workbench/{OPEN_QUESTIONS,HYPOTHESES,TODO}.md
7. memory/facts/FACTS.jsonl            ← 精确数字（引用前必读 caveats）
```

**第 2 步是本次新增的**。它的价值：

- 如果 `FACTS.jsonl` 的 `content_version` 与你在别处看到的引用不符 → **别处的引用已过期**
- 如果 `framework_version` 是别处未记录的版本 → 框架已变，**旧结论的适用条件可能已失效**
- `iteration` 告诉你这份内容最后一次动是哪一轮 → **判断新鲜度**

---

## 7. 一句话

> **版本号不是给文件贴标签，是给「引用」定锚点。**
>
> 一份内容若无法被引用者确认「我读的是哪一版」，
> 它就已经在无人察觉的情况下开始漂移 —— 这正是本索引要防的事。
