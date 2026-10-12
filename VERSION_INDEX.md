# VERSION_INDEX.md — 仓库版本索引

> **本文件由 `python tools/render_version_index.py --write` 从 `versions.json` 自动生成。请勿手工编辑。**
> 权威源是 `versions.json`（受 `spec/version_index.schema.json` 约束）。

**索引版本**：`2.1` ｜ **框架版本**：`1.1` ｜ **顶层版本（release）**：`0.1.0` ｜ **当前轮次**：`r17` ｜ **生成日期**：2026-10-12

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
| **`framework_version`** ★ | **框架层改过几版** | **`platform/`** | **本索引** |
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
| **A** | 结论性内容 | ✅ | `content_version` | 随轮次演化、重复写错代价最高。文件内版本行 + 索引登记。 | 125 |
| **B** | 结构性文档 / 框架与库代码 | ✅ | `content_version` | 随框架演进但无『结论』性质。.md 加版本行；.py 只登记索引。 | 106 |
| **C** | 机器契约 | ❌ | — | 已有 schema_version / config_version / data_version / version 字段，各答不同问题。索引镜像其值，不重复加版本。 | 36 |
| **D** | 纯数据 / 分析脚本 | ❌ | — | raw 数据用 SHA256（比版本号更强的保证）；分析脚本随结论归档，不单独版本化。 | 44 |

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
| `AI_MAP.md` | `1.0` | `r16` | 2026-10-12 | generated | 机器地图（派生物，render_ai_map 生成） |
| `DEPENDENCY_MAP.md` | `1.0` | `r16` | 2026-10-12 | generated | 跨文件依赖图（派生物，render_dependency_map 生成） |
| `FLYWHEEL_HEALTH.md` | `1.0` | `r16` | 2026-10-12 | generated | 飞轮健康度仪表盘（派生物，render_flywheel_health 生成） |
| `platform/tools/compress_memory.py` | `1.0` | `r06` | 2026-10-11 | active | 记忆压缩（每 5 轮）：ACTIVE.md + merge 候选 + 到期清单（IterResearch 依据） |
| `platform/tools/ingate.py` | `1.1` | `r08` | 2026-10-11 | active | 新增 _evidence_tier 分档校验 |
| `labs/lottery/studies/dlt/iterations/round02/FINDINGS.md` | `1.0` | `r02` | 2026-10-11 | active | 整理入库轮发现 |
| `labs/lottery/studies/dlt/iterations/round02/HANDOFF.md` | `1.0` | `r02` | 2026-10-11 | active | r02→r03 交接 |
| `labs/lottery/studies/dlt/iterations/round02/PRIORITY_TASKS.md` | `1.0` | `r02` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round02/TASK_BRIEF.md` | `1.0` | `r02` | 2026-10-11 | active | 已交付 |
| `labs/lottery/studies/dlt/iterations/round02/known_errors.md` | `1.0` | `r02` | 2026-10-11 | active | E1~E9 避坑手册 |
| `labs/lottery/studies/dlt/iterations/round02/legacy_findings/README.md` | `1.0` | `r02` | 2026-10-11 | active | 归档，设使用门槛 |
| `labs/lottery/studies/dlt/iterations/round02/legacy_findings/_round3_reference/round3_independent_review.html` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `labs/lottery/studies/dlt/iterations/round02/legacy_findings/round2_deep_analysis.txt` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `labs/lottery/studies/dlt/iterations/round02/legacy_findings/round2_glm_analysis.txt` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `labs/lottery/studies/dlt/iterations/round02/legacy_findings/round2_main_report.md` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `labs/lottery/studies/dlt/iterations/round02/legacy_findings/round2_verify_analysis.txt` | `1.0` | `r02` | 2026-10-11 | archived | 历史归档，设使用门槛（防锚定） |
| `labs/lottery/studies/dlt/iterations/round03/FINDINGS.md` | `1.0` | `r03` | 2026-10-11 | active | 复核轮发现（含自我纠错） |
| `labs/lottery/studies/dlt/iterations/round03/HANDOFF.md` | `1.0` | `r03` | 2026-10-11 | active | r03→r04 交接 |
| `labs/lottery/studies/dlt/iterations/round03/TASK_BRIEF.md` | `1.0` | `r03` | 2026-10-11 | active | 已交付 |
| `labs/lottery/studies/dlt/iterations/round03/scripts/apply_r03_facts.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round03/scripts/apply_r03_strategy.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round03/scripts/b2_robust_estimators.json` | `1.0` | `r03` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round03/scripts/b2_robust_estimators.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round03/scripts/b2_split_stability.json` | `1.0` | `r03` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round03/scripts/b2_split_stability.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.json` | `1.0` | `r03` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py` | `1.0` | `r03` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/FINDINGS.md` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/HANDOFF.md` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/TASK_BRIEF.md` | `1.0` | `r04` | 2026-10-11 | active | 已交付（round04 执行完毕） |
| `labs/lottery/studies/dlt/iterations/round04/scripts/apply_r04_facts.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/scripts/apply_r04_strategy.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/scripts/back_collision.json` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/scripts/back_collision.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.json` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.json` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.py` | `1.0` | `r04` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round05/FINDINGS.md` | `1.0` | `r05` | 2026-10-11 | active | 投注方式数学层 + R-002 量化 + 时间因素证伪 |
| `labs/lottery/studies/dlt/iterations/round05/HANDOFF.md` | `1.0` | `r05` | 2026-10-11 | active | r05→r06 交接；策略变更待用户批准 |
| `labs/lottery/studies/dlt/iterations/round05/TASK_BRIEF.md` | `1.0` | `r05` | 2026-10-11 | active | 已交付（round05 执行完毕；用户点名方向优先，T-201 顺延 r06） |
| `labs/lottery/studies/dlt/iterations/round05/scripts/apply_r05_facts.py` | `1.0` | `r05` | 2026-10-11 | active | F-0026~F-0032 落地 |
| `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.json` | `1.0` | `r05` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py` | `1.0` | `r05` | 2026-10-11 | active | 投注方式 + R-002 量化 + R-003 候选模拟 |
| `labs/lottery/studies/dlt/iterations/round05/scripts/fix_r05_housekeeping.py` | `1.0` | `r05` | 2026-10-11 | active | 收轮维护（tags/versions/计数） |
| `labs/lottery/studies/dlt/iterations/round05/scripts/sync_r05_versions.py` | `1.0` | `r05` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.json` | `1.0` | `r05` | 2026-10-11 | active |  |
| `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py` | `1.0` | `r05` | 2026-10-11 | active | 星期/奖池时序/节假日窗口 |
| `labs/lottery/studies/dlt/iterations/round06/FINDINGS.md` | `1.0` | `r06` | 2026-10-11 | active | r06 元层轮发现（策略落地+飞轮升级） |
| `labs/lottery/studies/dlt/iterations/round06/HANDOFF.md` | `1.0` | `r06` | 2026-10-11 | active | r06→r07 交接（结论/遗留/下轮建议） |
| `labs/lottery/studies/dlt/iterations/round06/TASK_BRIEF.md` | `1.0` | `r06` | 2026-10-11 | active | 由 round05 HANDOFF 转写（planned；T-201 前段取证首推） |
| `labs/lottery/studies/dlt/iterations/round06/manifest.json` | `1.0` | `r06` | 2026-10-11 | active | r06 机器登记 |
| `labs/lottery/studies/dlt/iterations/round06/research/ai_readability_proposal.md` | `1.0` | `r06` | 2026-10-11 | active | AI 可读性升级方案稿（P0/P1/P2，待批准） |
| `labs/lottery/studies/dlt/iterations/round06/research/flywheel_upgrade_plan.md` | `1.0` | `r06` | 2026-10-11 | active | 迭代飞轮全局升级计划（A-K 环节链路 + 分批） |
| `labs/lottery/studies/dlt/iterations/round06/scripts/add_v2_fields.py` | `1.0` | `r06` | 2026-10-11 | active | FACTS v2.0 字段迁移（grade/change_type/有效期） |
| `labs/lottery/studies/dlt/iterations/round06/scripts/apply_r06_strategy.py` | `1.0` | `r06` | 2026-10-11 | active | 用户批准三项策略变更落地 |
| `labs/lottery/studies/dlt/iterations/round06/scripts/fix_rename_remainder.py` | `1.0` | `r06` | 2026-10-11 | active | 改名残余引用修正（路径/import/标识） |
| `labs/lottery/studies/dlt/iterations/round06/scripts/probe_r06.py` | `1.0` | `r06` | 2026-10-11 | active | 探查原语与结论原文 |
| `labs/lottery/studies/dlt/iterations/round06/scripts/probe_v2.py` | `1.0` | `r06` | 2026-10-11 | active | v2.0 实施前的 FACTS/结构探查 |
| `labs/lottery/studies/dlt/iterations/round06/scripts/rename_spc.py` | `1.0` | `r06` | 2026-10-11 | active | 全链路改名：git mv src→spc + 包/品牌替换 |
| `labs/lottery/studies/dlt/iterations/round06/scripts/smoke_ingate.py` | `1.0` | `r06` | 2026-10-11 | active | 三闸门自测（缺陷→拒绝 / 合法→入库） |
| `labs/lottery/studies/dlt/iterations/round06/scripts/smoke_r06.py` | `1.0` | `r06` | 2026-10-11 | active | 新原语 + R-002/R-003 可执行性冒烟 |
| `labs/lottery/studies/dlt/iterations/round06/scripts/sync_guide_v14.py` | `1.0` | `r06` | 2026-10-11 | active | STRATEGY_GUIDE v1.4 同步 |
| `labs/lottery/studies/dlt/iterations/round06/scripts/sync_structure_registration.py` | `1.0` | `r06` | 2026-10-11 | active | 结构完整性补登记 + 目录树写回（P1-2） |
| `labs/lottery/studies/dlt/iterations/round06/scripts/sync_v2_final.py` | `1.0` | `r06` | 2026-10-11 | active | v2.0 收尾：版本登记 + README 计数同步 |
| `labs/lottery/studies/dlt/iterations/round06/scripts/sync_v2_versions.py` | `1.0` | `r06` | 2026-10-11 | active | v2.0 版本登记与 README 同步 |
| `labs/lottery/studies/dlt/iterations/round06/scripts/versions_r06_strategy.py` | `1.0` | `r06` | 2026-10-11 | active | r06 策略落地的版本登记 |
| `labs/lottery/studies/dlt/iterations/round07/FINDINGS.md` | `1.0` | `r07` | 2026-10-11 | active | 前段取证+外部核对+节假日验证+锚点重校准 |
| `labs/lottery/studies/dlt/iterations/round07/HANDOFF.md` | `1.0` | `r07` | 2026-10-11 | active | r07→r08 交接 |
| `labs/lottery/studies/dlt/iterations/round07/TASK_BRIEF.md` | `1.0` | `r07` | 2026-10-11 | active | r07 任务书（render_task_brief 生成，T-014 评分居首） |
| `labs/lottery/studies/dlt/iterations/round07/scripts/apply_r07_facts.py` | `1.0` | `r07` | 2026-10-11 | active | r07 结论入库 |
| `labs/lottery/studies/dlt/iterations/round07/scripts/t013_recalibrate.json` | `1.0` | `r07` | 2026-10-11 | active | 重校准结果 |
| `labs/lottery/studies/dlt/iterations/round07/scripts/t013_recalibrate.py` | `1.0` | `r07` | 2026-10-11 | active | F-0004/F-0005 重校准 |
| `labs/lottery/studies/dlt/iterations/round07/scripts/t014_forensics.json` | `1.0` | `r07` | 2026-10-11 | active | T-014 结果 |
| `labs/lottery/studies/dlt/iterations/round07/scripts/t014_forensics.py` | `1.0` | `r07` | 2026-10-11 | active | T-014 前段取证（F-0033） |
| `labs/lottery/studies/dlt/iterations/round07/scripts/t015_external.json` | `1.0` | `r07` | 2026-10-11 | active | T-015 结果 |
| `labs/lottery/studies/dlt/iterations/round07/scripts/t015_external.py` | `1.0` | `r07` | 2026-10-11 | active | T-015 外部核对（F-0034） |
| `labs/lottery/studies/dlt/iterations/round07/scripts/t016_holiday.json` | `1.0` | `r07` | 2026-10-11 | active | T-016 结果 |
| `labs/lottery/studies/dlt/iterations/round07/scripts/t016_holiday.py` | `1.0` | `r07` | 2026-10-11 | active | T-016 节假日验证（F-0035） |
| `labs/lottery/studies/dlt/iterations/round08/FINDINGS.md` | `1.0` | `r08` | 2026-10-11 | active | 体系升级轮发现（C1 注入器自愈 / Y 方法库 / X 协议 / 四件套补齐） |
| `labs/lottery/studies/dlt/iterations/round08/HANDOFF.md` | `1.0` | `r08` | 2026-10-11 | active | r08→r09 交接（P0：动态锚点重校准 + T-046/T-047；新工具用法） |
| `labs/lottery/studies/dlt/iterations/round08/scripts/all_tiers_expectation.json` | `1.0` | `r08` | 2026-10-11 | active | 全奖级口径输出（F-0036 的派生产物） |
| `labs/lottery/studies/dlt/iterations/round08/scripts/all_tiers_expectation.py` | `1.0` | `r08` | 2026-10-11 | active | 全奖级口径期望分解（r08 T-049，各奖级精确枚举 + 封顶饱和 L5 双口径） |
| `labs/lottery/studies/dlt/iterations/round09/FINDINGS.md` | `1.0` | `r09` | 2026-10-11 | active | 策略量化轮发现（R-002 量化 / NOOP 实战 / 逐号偏好 / 四锚点维持） |
| `labs/lottery/studies/dlt/iterations/round09/HANDOFF.md` | `1.0` | `r09` | 2026-10-11 | active | r09→r10 交接（F-0037/38；遗留 T-021/22/23/48 + F-0004 系数细化） |
| `labs/lottery/studies/dlt/iterations/round09/TASK_BRIEF.md` | `1.0` | `r09` | 2026-10-11 | active | 任务书：T-046/T-047/T-020 + 并行建议（X） |
| `labs/lottery/studies/dlt/iterations/round09/scripts/apply_r09_facts.py` | `1.0` | `r09` | 2026-10-11 | active | r09 入库：F-0037/F-0038 + NOOP + R-002 magnitude_pct |
| `labs/lottery/studies/dlt/iterations/round09/scripts/t013_recalibrate_r09.json` | `1.0` | `r09` | 2026-10-11 | active | 全部维持（recalibrated） |
| `labs/lottery/studies/dlt/iterations/round09/scripts/t013_recalibrate_r09.py` | `1.0` | `r09` | 2026-10-11 | active | 四锚点重校准（F-0016/17/22/23）+ NOOP |
| `labs/lottery/studies/dlt/iterations/round09/scripts/t020_number_weight.json` | `1.0` | `r09` | 2026-10-11 | active | 逐号结构存在；生日段不显著 |
| `labs/lottery/studies/dlt/iterations/round09/scripts/t020_number_weight.py` | `1.0` | `r09` | 2026-10-11 | active | 逐号偏好权重建模（Q-006/H-002） |
| `labs/lottery/studies/dlt/iterations/round09/scripts/t046_r002_quantify.json` | `1.0` | `r09` | 2026-10-11 | active | R-002 量化结果：K2/5/10 增益 PASS |
| `labs/lottery/studies/dlt/iterations/round09/scripts/t046_r002_quantify.py` | `1.0` | `r09` | 2026-10-11 | active | R-002 magnitude_pct 实证量化（m 经验分布 + bootstrap） |
| `labs/lottery/studies/dlt/iterations/round10/FINDINGS.md` | `1.1` | `r10` | 2026-10-11 | active | r10 结论 + r10.1 漏网根治补记（自动派生挖出 STRATEGY_GUIDE/api.py/MATH_BOUNDARY） |
| `labs/lottery/studies/dlt/iterations/round10/HANDOFF.md` | `1.1` | `r10` | 2026-10-11 | active | r10→r11 交接 + r10.1 概率口径护栏升级（扫描范围自动派生） |
| `labs/lottery/studies/dlt/iterations/round10/TASK_BRIEF.md` | `1.0` | `r10` | 2026-10-11 | active | 任务书：T-050/T-021/T-022（T-050 概率口径根治，用户指出） |
| `labs/lottery/studies/dlt/iterations/round10/manifest.json` | `1.0` | `r10` | 2026-10-11 | active | r10 轮清单 |
| `labs/lottery/studies/dlt/iterations/round10/scripts/apply_r10_facts.py` | `1.0` | `r10` | 2026-10-11 | active | r10 结论入库（F-0039/40/41 + 锚点重校准 + 工作台同步） |
| `labs/lottery/studies/dlt/iterations/round10/scripts/t021_sales_endogeneity.json` | `1.0` | `r10` | 2026-10-11 | active | 销量不驱动注数（pool→sale 显著、sale→w1 无） |
| `labs/lottery/studies/dlt/iterations/round10/scripts/t021_sales_endogeneity.py` | `1.0` | `r10` | 2026-10-11 | active | T-021 销量内生性（Granger+VAR+模型对比） |
| `labs/lottery/studies/dlt/iterations/round10/scripts/t022_illusion.json` | `1.0` | `r10` | 2026-10-11 | active | 仅等差1三连显著；H-001 部分支持 |
| `labs/lottery/studies/dlt/iterations/round10/scripts/t022_illusion.py` | `1.0` | `r10` | 2026-10-11 | active | T-022 随机性错觉形态撞号（H-001） |
| `labs/lottery/studies/dlt/iterations/round10/scripts/t028_recalibrate_r10.json` | `1.0` | `r10` | 2026-10-11 | active | 3 条锚点复现/复核成立 |
| `labs/lottery/studies/dlt/iterations/round10/scripts/t028_recalibrate_r10.py` | `1.0` | `r10` | 2026-10-11 | active | F-0028/29/31 重校准（维持+NOOP） |
| `labs/lottery/studies/dlt/iterations/round10/scripts/t050_calibration.json` | `1.0` | `r10` | 2026-10-11 | active | 一等奖 1/21425712；任一奖级 1/15；命中清单 |
| `labs/lottery/studies/dlt/iterations/round10/scripts/t050_calibration.py` | `1.0` | `r10` | 2026-10-11 | active | T-050 各奖级概率表 + 口径检索 |
| `labs/lottery/studies/dlt/rules_history.md` | `1.1` | `r03` | 2026-10-11 | active | E0~E6 共 7 段（§3.3 措辞存疑；第 6 次实证已加 r03 更正标记） |
| `labs/lottery/studies/dlt/strategy/STRATEGY_GUIDE.md` | `1.9` | `r16` | 2026-10-12 | active | r14.1: R-004 小节 + 三档表 B 档行（v1.8→1.9） |
| `memory/INDEX.md` | `1.0` | `r02` | 2026-10-11 | active | 记忆层说明 |
| `memory/facts/FACTS.jsonl` | `1.5` | `r16` | 2026-10-12 | active | r14: +F-0046（高区撞号<1）/F-0047（单步显著 1/5）；FACTS 45→47 |
| `memory/facts/INDEX.md` | `1.5` | `r04` | 2026-10-11 | active | 派生物，由 cli index 生成（32 条） |
| `memory/journal/round02.md` | `1.0` | `r02` | 2026-10-11 | active | 整理入库轮 |
| `memory/journal/round03.md` | `1.0` | `r03` | 2026-10-11 | active | 复核轮（含 1 次自我纠错） |
| `memory/journal/round04.md` | `1.0` | `r04` | 2026-10-11 | active |  |
| `memory/journal/round06.md` | `1.0` | `r06` | 2026-10-11 | active | r06 叙事（元层轮） |
| `memory/journal/round07.md` | `1.0` | `r07` | 2026-10-11 | active | r07 叙事（研究轮） |
| `memory/journal/round08.md` | `1.0` | `r08` | 2026-10-11 | active | 体系升级批执行日志 |
| `memory/journal/round09.md` | `1.0` | `r09` | 2026-10-11 | active | 策略量化轮执行日志 |
| `memory/journal/round10.md` | `1.0` | `r10` | 2026-10-11 | active | r10 执行日志 |
| `memory/lessons/LESSONS.md` | `1.3` | `r10` | 2026-10-11 | active | L1–L15，只增不删（r10.1 新增 L15：命中清单全量核对 + 校验器禁手写白名单） |
| `memory/spec/ITERATION_SOP_v2.md` | `1.3` | `r07` | 2026-10-11 | active | 证据门控式迭代规范 v2（C+X 协议已并入）：收尾清单第10步引 finish_round.py；新增§9 并行研究池（研究可并行、入库串行过三闸门） |
| `memory/workbench/HYPOTHESES.md` | `1.2` | `r07` | 2026-10-11 | active | H-001~H-006（H-006 refuted） |
| `memory/workbench/OPEN_QUESTIONS.md` | `1.7` | `r16` | 2026-10-12 | active | r12: Q-008 → answered（open 3→2：Q-006/Q-016） |
| `memory/workbench/TODO.md` | `2.2` | `r16` | 2026-10-12 | active | r15: T-052 → done（r14.1 已落地，此前漏勾；新增 ★T 护栏捕获）；T-020 标注存疑（r08 记 done 但无产出记录、Q-006 仍 open），勾选状态未改待裁定 |

### B 级 · 结构性文档 / 框架与库代码

| 路径 | 版本 | 轮次 | 状态 | 备注 |
|---|---|---|---|---|
| `AI_CONTEXT.md` | `1.5` | `r16` | active | FACTS 计数 38→43 |
| `README.md` | `1.16` | `r16` | active | ← 速览区 48 条结论 / open 1 / r12 彩种行 |
| `VERSION_INDEX.md` | `1.0` | `r16` | active | 版本索引（人读），权威源是 versions.json |
| `cli/main.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `docs/ARCHITECTURE.md` | `1.1` | `r03` | active |  |
| `docs/CONSUMING.md` | `1.1` | `r02` | active |  |
| `docs/ITERATION_GUIDE.md` | `1.0` | `r02` | active |  |
| `docs/METHODOLOGY.md` | `1.0` | `r02` | active |  |
| `docs/PROPOSAL_SINGLE_TICKET_CORE.md` | `1.1` | `r03` | active |  |
| `docs/VERSIONING_DOCS.md` | `1.5` | `r15` | active | r15: §6.2 追加『manifest 先于 bump』顺序约束；新增 §6.7 轮次号唯一判据 |
| `platform/INDEX.md` | `1.1` | `r03` | active |  |
| `platform/README.md` | `1.0` | `r02` | active |  |
| `platform/core/README.md` | `1.1` | `r03` | active |  |
| `platform/core/__init__.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `platform/core/evaluate.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `platform/core/features.py` | —（见备注） | `r06` | active | 新增跨注原语 duplicate_ticket_count / duplicate_ticket_count_ge（F-0027 判定量） |
| `platform/core/game_util.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `platform/core/generate.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `platform/core/judge.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `platform/core/portfolio.py` | —（见备注） | `—` | active | ★ 跨注层（L3）核心：Portfolio 一等公民 + 跨注求值 + judge_cross |
| `platform/core/ticket.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `platform/methodology/MATH_BOUNDARY.md` | `1.1` | `r10` | active | r10.1：红线表格 P=1/T 加一等奖限定（各奖级恒定） |
| `platform/methodology/STATISTICAL_DISCIPLINE.md` | `1.0` | `r02` | active |  |
| `platform/protocol/ITERATION_PROTOCOL.md` | `1.2` | `r12` | active | r12: T-040 回写 §6 校验扩展 + §7 禁止事项 5 条护栏 |
| `platform/protocol/MEMORY_PROTOCOL.md` | `1.2` | `r03` | active | r03 框架迭代：新增 §1.7 claim_type 证据类型 + §1.8 证据锚定 |
| `platform/protocol/README.md` | `1.0` | `r02` | active |  |
| `platform/protocol/templates/FINDINGS.template.md` | `1.0` | `r02` | active |  |
| `platform/protocol/templates/HANDOFF.template.md` | `1.0` | `r02` | active |  |
| `platform/protocol/templates/TASK_BRIEF.template.md` | `1.0` | `r02` | active |  |
| `platform/tools/memory.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame）；open_questions() 状态解析归一化（容忍 →/（）/+ 说明字符） |
| `labs/lottery/INDEX.md` | `1.2` | `r04` | active | 彩种索引（r04：结论数 18 → 25；轮次 round04 ✅ / round05 计划中） |
| `labs/lottery/studies/_template/README.md` | —（见备注） | `—` | active |  |
| `labs/lottery/studies/_template/data/build_scripts/README.md` | —（见备注） | `—` | active |  |
| `labs/lottery/studies/_template/data/derived/README.md` | —（见备注） | `—` | active |  |
| `labs/lottery/studies/_template/data/raw/README.md` | —（见备注） | `—` | active |  |
| `labs/lottery/studies/_template/data/tools/README.md` | —（见备注） | `—` | active |  |
| `labs/lottery/studies/_template/iterations/round01/TASK_BRIEF.md` | —（见备注） | `—` | active |  |
| `labs/lottery/studies/dlt/iterations/round05/manifest.json` | `1.0` | `r05` | active |  |
| `labs/lottery/studies/dlt/iterations/round11/FINDINGS.md` | `1.0` | `r11` | active | r11 结论：F-0042 平台期 / F-0043 代理可观测 / T-048 设计 + 2 项顺带根治 |
| `labs/lottery/studies/dlt/iterations/round11/HANDOFF.md` | `1.0` | `r11` | active | r11→r12 交接：T-048b 首推 + T-025 仍 blocked + 编码护栏建议 |
| `labs/lottery/studies/dlt/iterations/round11/T048_HOLDOUT_DESIGN.md` | `1.0` | `r11` | active | T-048 L3 组合优化预备：时序 hold-out 评测设计（切分/指标/防泄漏/组合搜索边界/验收护栏，不落 L2） |
| `labs/lottery/studies/dlt/iterations/round11/TASK_BRIEF.md` | `1.0` | `r11` | active | r11 任务书：T-023/T-024/T-048（render_task_brief --round 11 --top 3） |
| `labs/lottery/studies/dlt/iterations/round12/FINDINGS.md` | `1.0` | `r12` | active | r12 研究结论 |
| `labs/lottery/studies/dlt/iterations/round12/HANDOFF.md` | `1.0` | `r12` | active | r12→r13 交接 |
| `labs/lottery/studies/dlt/iterations/round12/TASK_BRIEF.md` | `1.0` | `r12` | active | r12 任务书（T-049/T-030/T-040） |
| `labs/lottery/studies/dlt/iterations/round13/FINDINGS.md` | `1.0` | `r13` | active | r13 研究结论 |
| `labs/lottery/studies/dlt/iterations/round13/HANDOFF.md` | `1.0` | `r13` | active | r13 交接 |
| `labs/lottery/studies/dlt/iterations/round13/TASK_BRIEF.md` | `1.0` | `r13` | active | r13 任务书（T-051/T-044/T-045） |
| `labs/lottery/studies/dlt/iterations/round14/FINDINGS.md` | `1.0` | `r14` | active | r14 研究结论 |
| `labs/lottery/studies/dlt/iterations/round14/HANDOFF.md` | `1.0` | `r14` | active | r14 交接 |
| `labs/lottery/studies/dlt/iterations/round14/TASK_BRIEF.md` | `1.0` | `r14` | active | r14 任务书（T-052 待批准/T-053/T-054） |
| `labs/lottery/studies/dlt/iterations/round15/FINDINGS.md` | `1.0` | `r15` | active | r15 治理结论（D1~D5 五处缺陷及其与 r11.1/r14.2 的同源关系） |
| `labs/lottery/studies/dlt/iterations/round15/HANDOFF.md` | `1.0` | `r15` | active | r15 交接（含 T-020 未决裁定项） |
| `labs/lottery/studies/dlt/iterations/round15/TASK_BRIEF.md` | `1.0` | `r15` | active | r15 任务书（必做 0 个：待办池仅剩资源缺口型；T-052 已落地漏勾） |
| `labs/lottery/studies/dlt/iterations/round16/TASK_BRIEF.md` | `1.0` | `r16` | active | r16 任务书（首次含派生候选：必做 1 个 = T-063 [derive:H-001]） |
| `labs/lottery/studies/dlt/iterations/round16/FINDINGS.md` | `1.0` | `r16` | active | r16 结论（B1 重校准钥匙=established_in；B2 证据索引还债；F-0048 H-002 partial；★源自救） |
| `labs/lottery/studies/dlt/iterations/round16/HANDOFF.md` | `1.0` | `r16` | active | r16 交接（validate 首次 0 警告；F-0048 策略用途待用户批准） |
| `memory/journal/round05.md` | `1.0` | `r05` | active | 叙事：R-002 量化不成立 + H-005 证伪 |
| `research_lib/README.md` | —（见备注） | `r08` | active | 原语→来源脚本→历史结论映射表 + 使用纪律 |
| `research_lib/__init__.py` | —（见备注） | `r08` | active | 研究资本化（Y）：彩种无关统计原语出口 |
| `research_lib/stability.py` | —（见备注） | `r08` | active | split_ratio_stability / ci_overlap（分期稳健性，Q-001 原语化） |
| `research_lib/stats.py` | —（见备注） | `r08` | active | bootstrap_ci / ratio_and_boot / wilson_interval（来源 round03 b2_split_stability） |
| `spec/README.md` | `1.0` | `r02` | active |  |
| `spec/VERSIONING.md` | `1.2` | `r03` | active |  |
| `src/__init__.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/__init__.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/ai_map.py` | —（见备注） | `—` | active | AI_MAP 生成源（llms.txt 式机器地图） |
| `src/spc/api.py` | —（见备注） | `r10` | active | r10.1：generate 概率口径限定（各奖级恒定；一等奖恒为 1/T） |
| `src/spc/depmap.py` | —（见备注） | `—` | active | 跨文件依赖图生成源（C） |
| `src/spc/evidence.py` | —（见备注） | `r03` | active | ★ 证据锚定：sha256_file / fact_anchor / evidence_digest（结论与策略的哈希锚） |
| `src/spc/flywheel.py` | —（见备注） | `—` | active | 飞轮健康度统计 + 置信度校准（K/D1） |
| `src/spc/game.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/memory.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/strategy.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/spc/tree.py` | —（见备注） | `r06` | active | 目录树生成源（P1-2）：README 树 = 派生物 |
| `src/spc/validate.py` | —（见备注） | `r15` | active | r12: 策略同步 ★S 已内置（r11 起）。r15: 新增 ★R 轮次号双源对账（current_iteration vs 最新已收尾轮）+ ★T 已落地任务必须勾选；轮号推导改由 delivered_round_dirs（判据=含 manifest.json） |
| `src/spc/versions.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tests/README.md` | `1.5` | `r06` | active | 测试说明（自举计数：合计 333，含 test_structure 8） |
| `tests/test_ai_readability.py` | —（见备注） | `r15` | active | P1/P2/B/H/I 测试；★r15: 压缩到期夹具改为真收尾轮（含 manifest.json），对齐『轮号判据=已收尾』 |
| `tests/test_claim_type.py` | —（见备注） | `r03` | active | ★ 结论证据类型测试（五类约束真的会拦 / schema 与 Python 双通道一致）；无需 pytest |
| `tests/test_consumes_completeness.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tests/test_core.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tests/test_cross_scope.py` | —（见备注） | `—` | active | ★ 跨注层测试（scope 三分 / 跨注判定 / 结构性拒收）；无需 pytest |
| `tests/test_evidence_anchor.py` | —（见备注） | `r03` | active | ★ 证据锚定测试（漂移真能检出 / 该敏感的要敏感、该迟钝的要迟钝 / 重基线幂等）；无需 pytest |
| `tests/test_flywheel.py` | —（见备注） | `—` | active | K/D1/D2/C/F 测试（无需 pytest） |
| `tests/test_meta_variables.py` | —（见备注） | `r08` | active | schema 1.3 元数据（convenience/experience/psychology）结构+红线+CLI 展示测试 |
| `tests/test_open_questions_consistency.py` | —（见备注） | `r08` | active | Q 状态一致性回归：解析归一化/头部计数滞后/标题缺✅/优先级表active含已清偿/状态词非法 |
| `tests/test_research_lib.py` | —（见备注） | `r08` | active | research_lib 原语测试（已知分布验证可复现/正确性/样本不足不硬报） |
| `tests/test_round_counter_sync.py` | `1.0` | `r15` | active | ★ 轮次号与待办双源对账（r15）：dry-run 无副作用 / 轮次号只认已收尾轮 / 双源不一致必报 / 已落地未勾选必报且提及不误报；无需 pytest |
| `tests/test_derive_tasks.py` | `1.0` | `r16` | active | ★ 任务源派生（r16 ★源自救）：open Q 必派生 / 已答不派生；H unverified+partial 派生、refuted 不派生；resource 标记保留；幂等（跑两次不重复）；dry-run 不落盘；派生条目可被 render_task_brief 解析；无需 pytest |
| `tests/test_round_stall.py` | —（见备注） | `r14` | active | 轮次停滞检查（r14.2）：同源自洽陷阱必须被识破 / 未声明活文档不误伤 / bump_iteration 能修复；无需 pytest |
| `tests/test_shadow_game.py` | `1.0` | `r03` | active |  |
| `tests/test_structure.py` | —（见备注） | `r06` | active | 结构完整性回归测试（P1-2 三道防线） |
| `tools/build_versions.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame）；r13 T-044 降级为参考实现，--write 禁用 |
| `tools/bump_iteration.py` | —（见备注） | `r14` | active | 代码文件：不写文件内版本行（用 git blame）；r14.2 新增：活文档轮次对齐（防登记停滞），必须在 render_* 与 inject_version_lines 之前执行 |
| `tools/inject_version_lines.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tools/register_r06_upgrade.py` | —（见备注） | `—` | active | r06 批量实施登记脚本（一次性，登记含自身） |
| `tools/render_ai_map.py` | —（见备注） | `r11` | active | r11：读取改 utf-8-sig（修 BOM 叠加 bug） |
| `tools/render_dependency_map.py` | —（见备注） | `r11` | active | r11：读取改 utf-8-sig（修 BOM 叠加 bug） |
| `tools/render_flywheel_health.py` | —（见备注） | `r11` | active | r11：读取改 utf-8-sig（修 BOM 叠加 bug） |
| `tools/render_readme_tree.py` | —（见备注） | `r11` | active | r11：读取改 utf-8-sig（修 BOM 叠加 bug） |
| `tools/render_task_brief.py` | —（见备注） | `r15` | active | 任务书生成器（B+G/X）：--top N 控制必做数；resource 资源前置（Z）；★r15: dry-run 不再建目录（makedirs 移入 --write）；轮号只认已收尾轮；无可执行候选时如实输出 0 个，不再把资源缺口型提升为必做 |
| `tools/derive_tasks.py` | —（见备注） | `r16` | active | ★ 任务源派生（r16 ★源自救）：从 OPEN_QUESTIONS(open) / HYPOTHESES(unverified,partial) / validate 告警 三处存量派生 T-nnn 写入 TODO；[derive:…] 源标记保证幂等；资源缺口如实标记不占轮次预算（Z 协议） |
| `tools/render_version_index.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tools/report_calibration.py` | —（见备注） | `—` | active | 置信度校准报告（D1） |
| `versions.json` | `1.0` | `r16` | generated |  |

### C 级 · 机器契约（用自身既有版本字段）

| 路径 | 版本字段 | 值 | 备注 |
|---|---|---|---|
| `labs/lottery/studies/_template/game.yaml` | `config_version` | `2.0` | 2026-10-11 与 dlt 同步升至 2.0（features 原语化） |
| `labs/lottery/studies/_template/strategy/strategy.json` | `config_version` | `2.0` | 模板策略，2026-10-11 随 game.yaml 同步至 2.0 |
| `labs/lottery/studies/dlt/game.yaml` | `config_version` | `2.2` | r14.1: +has_mirror_pair 特征（R-004 判定量）；config_version 2.1→2.2 |
| `labs/lottery/studies/dlt/iterations/round02/manifest.json` | `inputs.data_version` | `dlt_full_2933` |  |
| `labs/lottery/studies/dlt/iterations/round03/manifest.json` | `inputs.data_version` | `dlt_full_2933` |  |
| `labs/lottery/studies/dlt/iterations/round04/manifest.json` | `—` | `—` |  |
| `labs/lottery/studies/dlt/iterations/round07/manifest.json` | `inputs.data_version` | `dlt_full_2933` | r07 机器登记 |
| `labs/lottery/studies/dlt/iterations/round08/manifest.json` | `—` | `—` | 体系升级批清单（C+X+Y+Z） |
| `labs/lottery/studies/dlt/iterations/round09/manifest.json` | `—` | `—` | 策略量化轮清单 |
| `labs/lottery/studies/dlt/iterations/round11/scripts/apply_r11_facts.py` | `—` | `—` | r11 入库：F-0042/F-0043 新增 + F-0021 caveats 更新 + Q-011/Q-015 answered + TODO done |
| `labs/lottery/studies/dlt/iterations/round11/scripts/t023_roll_decay.py` | `—` | `—` | T-023 效应弱化滚动复验（W=300/500 滚动窗口 + 节假日分时段；→ F-0042） |
| `labs/lottery/studies/dlt/iterations/round11/scripts/t024_proxy.py` | `—` | `—` | T-024 机选占比代理变量（P1 低号注数比 / P2 连号注数比 / P3 偏好基尼 + 变点扫描；→ F-0043） |
| `labs/lottery/studies/dlt/iterations/round12/scripts/t030_effectiveness.py` | `—` | `—` | T-030 三档标准写入 |
| `labs/lottery/studies/dlt/iterations/round12/scripts/t049_holdout.py` | `—` | `—` | T-049 hold-out 评测 |
| `labs/lottery/studies/dlt/iterations/round13/scripts/t051_walkforward.py` | `—` | `—` | T-051 walk-forward 评测 |
| `labs/lottery/studies/dlt/iterations/round14/scripts/t053_shape_ratios.py` | `—` | `—` | T-053 形态撞号比复验 |
| `labs/lottery/studies/dlt/iterations/round14/scripts/t054_walkforward_ci.py` | `—` | `—` | T-054 walk-forward 每步 CI |
| `labs/lottery/studies/dlt/iterations/round16/scripts/apply_r16_facts.py` | `—` | `—` | T-066/T-069：7 条动态锚点 NOOP 重记 + established_in→round16；Q-006→answered；H-002→partial |
| `labs/lottery/studies/dlt/iterations/round16/scripts/b2_fill_evidence_index.py` | `—` | `—` | T-067：补 strategy.json evidence_index（F-0044~47）与 STRATEGY_GUIDE consumes（F-0041/44/45/46） |
| `labs/lottery/studies/dlt/iterations/round16/scripts/t064_h002_segment.py` | `—` | `—` | T-064：H-002 三段单调 bootstrap CI + 序型置换检验（p=0.2103）→ F-0048 |
| `labs/lottery/studies/dlt/iterations/round16/scripts/t013_recalibrate_r09.py` | `—` | `—` | T-066 复现副本（不覆盖 r09 历史产物）：F-0016/17/22/23 重校准 |
| `labs/lottery/studies/dlt/iterations/round16/scripts/t028_recalibrate_r10.py` | `—` | `—` | T-066 复现副本（不覆盖 r10 历史产物）：F-0028/29/31 重校准 |
| `labs/lottery/studies/dlt/iterations/round16/scripts/t020_number_weight.py` | `—` | `—` | T-069 复算副本：逐号相对撞号强度 S_j（F-0038 原始脚本，用于核实 T-020 产出确实存在） |
| `labs/lottery/studies/dlt/strategy/strategy.json` | `schema_version` | `1.4` | r14.1: R-004 落地（用户批准 T-052）；schema 仍 1.4，内容 1.4→1.5 |
| `memory/journal/round11.md` | `—` | `—` | r11 执行日志（含 schema 踩坑序列与 BOM 根治） |
| `memory/journal/round12.md` | `—` | `—` | r12 执行日志 |
| `memory/journal/round13.md` | `—` | `—` | r13 执行日志 |
| `memory/journal/round14.md` | `—` | `—` | r14 执行日志 |
| `memory/journal/round15.md` | `—` | `—` | r15 执行日志（治理轮） |
| `memory/journal/round16.md` | `—` | `—` | r16 执行日志（告警清零 + 任务源机制轮） |
| `pyproject.toml` | `project.version` | `0.1.0` | 包版本 |
| `spec/fact.schema.json` | `—` | `—` | evidence 新增 noop_count |
| `spec/game_config.schema.json` | `—` | `—` | schema 自身无版本；约束 game_config.config_version |
| `spec/iteration.schema.json` | `—` | `—` | schema 自身无版本；约束 iteration 结构 |
| `spec/strategy.schema.json` | `—` | `—` | metric enum 同步为 expected_bonus_given_win |
| `spec/version_index.schema.json` | `—` | `—` | schema 自身无版本；约束 versions.index_version |

### D 级 · 纯数据 / 分析脚本（不版本化）

| 路径 | 类型 | SHA256（raw） | 备注 |
|---|---|---|---|
| `.gitignore` | `meta` | — |  |
| `labs/lottery/studies/dlt/data/build_scripts/build_derived_v4.py` | `build_script` | — |  |
| `labs/lottery/studies/dlt/data/build_scripts/hash_and_list.py` | `build_script` | — |  |
| `labs/lottery/studies/dlt/data/build_scripts/validate_package_v4.py` | `build_script` | — |  |
| `labs/lottery/studies/dlt/data/derived/01_yearly_stats.csv` | `derived_data` | — |  |
| `labs/lottery/studies/dlt/data/derived/02_front_number_frequency.csv` | `derived_data` | — |  |
| `labs/lottery/studies/dlt/data/derived/03_back_number_frequency.csv` | `derived_data` | — |  |
| `labs/lottery/studies/dlt/data/derived/04_structure_distribution_exact.json` | `derived_data` | — |  |
| `labs/lottery/studies/dlt/data/derived/05_back_combo_66.csv` | `derived_data` | — |  |
| `labs/lottery/studies/dlt/data/derived/06_acf_lag1to60.csv` | `derived_data` | — |  |
| `labs/lottery/studies/dlt/data/derived/07_data_quality_report.json` | `derived_data` | — |  |
| `labs/lottery/studies/dlt/data/derived/08_rules_epoch_summary.json` | `derived_data` | — |  |
| `labs/lottery/studies/dlt/data/raw/dlt_full_2933.csv` | `raw_data` | `9e92848e184c7715…` | SHA256 为准，不做内容版本 |
| `labs/lottery/studies/dlt/data/raw/dlt_full_2933.jsonl` | `raw_data` | `11a1714e9c850a7d…` | SHA256 为准，不做内容版本 |
| `labs/lottery/studies/dlt/data/tools/_load.py` | `analysis_script` | — |  |
| `labs/lottery/studies/dlt/data/tools/acf_permutation_test.py` | `analysis_script` | — |  |
| `labs/lottery/studies/dlt/data/tools/changepoint_refine.py` | `analysis_script` | — |  |
| `labs/lottery/studies/dlt/data/tools/changepoint_scan.py` | `analysis_script` | — |  |
| `labs/lottery/studies/dlt/data/tools/consecutive_exact_check.py` | `analysis_script` | — |  |
| `labs/lottery/studies/dlt/data/tools/exact_tests.py` | `analysis_script` | — |  |
| `labs/lottery/studies/dlt/data/tools/overdispersion_and_hac.py` | `analysis_script` | — |  |
| `labs/lottery/studies/dlt/data/tools/validate_data.py` | `analysis_script` | — |  |
| `labs/lottery/studies/dlt/iterations/round11/manifest.json` | `manifest` | — | r11 deliverables（根级） |
| `labs/lottery/studies/dlt/iterations/round11/scripts/t023_roll_decay.json` | `research_output` | — | T-023 复验结果（34/30 窗序列 + 趋势检验 + 节假日分段） |
| `labs/lottery/studies/dlt/iterations/round11/scripts/t024_proxy.json` | `research_output` | — | T-024 代理序列 + 变点 + 相关结果 |
| `labs/lottery/studies/dlt/iterations/round12/manifest.json` | `manifest` | — | r12 manifest |
| `labs/lottery/studies/dlt/iterations/round12/scripts/t049_holdout.json` | `data` | — | T-049 结果 |
| `labs/lottery/studies/dlt/iterations/round13/manifest.json` | `manifest` | — | r13 manifest |
| `labs/lottery/studies/dlt/iterations/round13/scripts/t051_walkforward.json` | `data` | — | T-051 结果 |
| `labs/lottery/studies/dlt/iterations/round14/manifest.json` | `manifest` | — | r14 manifest |
| `labs/lottery/studies/dlt/iterations/round14/scripts/t053_shape_ratios.json` | `data` | — | T-053 结果 |
| `labs/lottery/studies/dlt/iterations/round14/scripts/t054_walkforward_ci.json` | `data` | — | T-054 结果 |
| `labs/lottery/studies/dlt/iterations/round15/manifest.json` | `manifest` | — | r15 manifest |
| `labs/lottery/studies/dlt/iterations/round16/manifest.json` | `manifest` | — | r16 manifest |
| `labs/lottery/studies/dlt/iterations/round16/scripts/t013_recalibrate_r09.json` | `data` | — | T-066 复现产物：F-0016/17/22/23 重校准数值快照 |
| `labs/lottery/studies/dlt/iterations/round16/scripts/t028_recalibrate_r10.json` | `data` | — | T-066 复现产物：F-0028/29/31 重校准数值快照 |
| `labs/lottery/studies/dlt/iterations/round16/scripts/t064_h002_segment.json` | `data` | — | T-064 产物：三段均值/sd、bootstrap CI、置换检验 p 值（F-0048 证据） |
| `labs/lottery/studies/dlt/manifest_v4_source.json` | `source_manifest` | — |  |
| `labs/lottery/studies/dlt/strategy/simulation_results.json` | `analysis_output` | — |  |
| `labs/lottery/studies/dlt/strategy/strategy_simulation.py` | `analysis_script` | — | r10.1：docstring 一等奖概率口径 |
| `memory/facts/ACTIVE.md` | `report` | — | 当前有效结论清单（与台账分离，compress_memory 生成） |
| `tests/fixtures/shadow/game.yaml` | `test_fixture` | — |  |
| `tools/count_tests.py` | `test_tool` | — | 登记测试文件 + --inject（T-045：tests/README 计数自举注入）；r15: 新增 test_round_counter_sync |
| `tools/finish_round.py` | `utility` | — | 收尾自动化（C1）：rehash→count_tests--inject→bump_iteration→渲染+inject→validate（渲染后终检）→四件套检查→批准门提示 |

---

## 3. 按内容类型检索

| 类型 | 数量 | 级别 | 文件 |
|---|---|---|---|
| `iteration_artifact` | 52 | A | `labs/lottery/studies/dlt/iterations/round02/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round02/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round02/PRIORITY_TASKS.md`<br>`labs/lottery/studies/dlt/iterations/round02/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round02/known_errors.md`<br>`labs/lottery/studies/dlt/iterations/round02/legacy_findings/README.md`<br>`labs/lottery/studies/dlt/iterations/round02/legacy_findings/_round3_reference/round3_independent_review.html`<br>`labs/lottery/studies/dlt/iterations/round02/legacy_findings/round2_deep_analysis.txt`<br>`labs/lottery/studies/dlt/iterations/round02/legacy_findings/round2_glm_analysis.txt`<br>`labs/lottery/studies/dlt/iterations/round02/legacy_findings/round2_main_report.md`<br>`labs/lottery/studies/dlt/iterations/round02/legacy_findings/round2_verify_analysis.txt`<br>`labs/lottery/studies/dlt/iterations/round03/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round03/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round03/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round03/scripts/apply_r03_facts.py`<br>`labs/lottery/studies/dlt/iterations/round03/scripts/apply_r03_strategy.py`<br>`labs/lottery/studies/dlt/iterations/round03/scripts/b2_robust_estimators.json`<br>`labs/lottery/studies/dlt/iterations/round03/scripts/b2_robust_estimators.py`<br>`labs/lottery/studies/dlt/iterations/round03/scripts/b2_split_stability.json`<br>`labs/lottery/studies/dlt/iterations/round03/scripts/b2_split_stability.py`<br>`labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.json`<br>`labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`<br>`labs/lottery/studies/dlt/iterations/round04/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round04/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round04/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round04/scripts/apply_r04_facts.py`<br>`labs/lottery/studies/dlt/iterations/round04/scripts/apply_r04_strategy.py`<br>`labs/lottery/studies/dlt/iterations/round04/scripts/back_collision.json`<br>`labs/lottery/studies/dlt/iterations/round04/scripts/back_collision.py`<br>`labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.json`<br>`labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`<br>`labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.json`<br>`labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`<br>`labs/lottery/studies/dlt/iterations/round05/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round05/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round05/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round06/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round06/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round06/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round06/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round07/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round07/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round07/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round08/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round08/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round08/scripts/all_tiers_expectation.json`<br>`labs/lottery/studies/dlt/iterations/round08/scripts/all_tiers_expectation.py`<br>`labs/lottery/studies/dlt/iterations/round09/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round09/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round09/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round10/TASK_BRIEF.md`<br>`memory/journal/round04.md` |
| `script` | 45 | A/C | `platform/tools/compress_memory.py`<br>`platform/tools/ingate.py`<br>`labs/lottery/studies/dlt/iterations/round05/scripts/apply_r05_facts.py`<br>`labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`<br>`labs/lottery/studies/dlt/iterations/round05/scripts/fix_r05_housekeeping.py`<br>`labs/lottery/studies/dlt/iterations/round05/scripts/sync_r05_versions.py`<br>`labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/add_v2_fields.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/apply_r06_strategy.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/fix_rename_remainder.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/probe_r06.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/probe_v2.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/rename_spc.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/smoke_ingate.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/smoke_r06.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/sync_guide_v14.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/sync_structure_registration.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/sync_v2_final.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/sync_v2_versions.py`<br>`labs/lottery/studies/dlt/iterations/round06/scripts/versions_r06_strategy.py`<br>`labs/lottery/studies/dlt/iterations/round07/scripts/apply_r07_facts.py`<br>`labs/lottery/studies/dlt/iterations/round07/scripts/t013_recalibrate.py`<br>`labs/lottery/studies/dlt/iterations/round07/scripts/t014_forensics.py`<br>`labs/lottery/studies/dlt/iterations/round07/scripts/t015_external.py`<br>`labs/lottery/studies/dlt/iterations/round07/scripts/t016_holiday.py`<br>`labs/lottery/studies/dlt/iterations/round09/scripts/apply_r09_facts.py`<br>`labs/lottery/studies/dlt/iterations/round09/scripts/t013_recalibrate_r09.py`<br>`labs/lottery/studies/dlt/iterations/round09/scripts/t020_number_weight.py`<br>`labs/lottery/studies/dlt/iterations/round09/scripts/t046_r002_quantify.py`<br>`labs/lottery/studies/dlt/iterations/round10/scripts/apply_r10_facts.py`<br>`labs/lottery/studies/dlt/iterations/round10/scripts/t021_sales_endogeneity.py`<br>`labs/lottery/studies/dlt/iterations/round10/scripts/t022_illusion.py`<br>`labs/lottery/studies/dlt/iterations/round10/scripts/t028_recalibrate_r10.py`<br>`labs/lottery/studies/dlt/iterations/round10/scripts/t050_calibration.py`<br>`labs/lottery/studies/dlt/iterations/round12/scripts/t030_effectiveness.py`<br>`labs/lottery/studies/dlt/iterations/round12/scripts/t049_holdout.py`<br>`labs/lottery/studies/dlt/iterations/round13/scripts/t051_walkforward.py`<br>`labs/lottery/studies/dlt/iterations/round14/scripts/t053_shape_ratios.py`<br>`labs/lottery/studies/dlt/iterations/round14/scripts/t054_walkforward_ci.py`<br>`labs/lottery/studies/dlt/iterations/round16/scripts/apply_r16_facts.py`<br>`labs/lottery/studies/dlt/iterations/round16/scripts/b2_fill_evidence_index.py`<br>`labs/lottery/studies/dlt/iterations/round16/scripts/t064_h002_segment.py`<br>`labs/lottery/studies/dlt/iterations/round16/scripts/t013_recalibrate_r09.py`<br>`labs/lottery/studies/dlt/iterations/round16/scripts/t028_recalibrate_r10.py`<br>`labs/lottery/studies/dlt/iterations/round16/scripts/t020_number_weight.py` |
| `doc` | 43 | A/B/C | `AGENTS.md`<br>`AI_MAP.md`<br>`DEPENDENCY_MAP.md`<br>`FLYWHEEL_HEALTH.md`<br>`README.md`<br>`docs/ARCHITECTURE.md`<br>`docs/CONSUMING.md`<br>`docs/ITERATION_GUIDE.md`<br>`docs/METHODOLOGY.md`<br>`docs/PROPOSAL_SINGLE_TICKET_CORE.md`<br>`docs/VERSIONING_DOCS.md`<br>`platform/README.md`<br>`platform/core/README.md`<br>`platform/protocol/ITERATION_PROTOCOL.md`<br>`labs/lottery/studies/dlt/iterations/round06/research/ai_readability_proposal.md`<br>`labs/lottery/studies/dlt/iterations/round06/research/flywheel_upgrade_plan.md`<br>`labs/lottery/studies/dlt/iterations/round12/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round12/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round12/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round13/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round13/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round13/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round14/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round14/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round14/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round15/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round15/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round15/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round16/TASK_BRIEF.md`<br>`labs/lottery/studies/dlt/iterations/round16/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round16/HANDOFF.md`<br>`labs/lottery/studies/dlt/strategy/STRATEGY_GUIDE.md`<br>`memory/journal/round12.md`<br>`memory/journal/round13.md`<br>`memory/journal/round14.md`<br>`memory/journal/round15.md`<br>`memory/journal/round16.md`<br>`memory/spec/ITERATION_SOP_v2.md`<br>`memory/workbench/OPEN_QUESTIONS.md`<br>`memory/workbench/TODO.md`<br>`spec/README.md`<br>`spec/VERSIONING.md`<br>`tests/README.md` |
| `code` | 14 | B | `src/spc/ai_map.py`<br>`src/spc/depmap.py`<br>`src/spc/flywheel.py`<br>`src/spc/tree.py`<br>`src/spc/validate.py`<br>`tests/test_structure.py`<br>`tools/register_r06_upgrade.py`<br>`tools/render_ai_map.py`<br>`tools/render_dependency_map.py`<br>`tools/render_flywheel_health.py`<br>`tools/render_readme_tree.py`<br>`tools/render_task_brief.py`<br>`tools/derive_tasks.py`<br>`tools/report_calibration.py` |
| `report` | 14 | A/D | `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.json`<br>`labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.json`<br>`labs/lottery/studies/dlt/iterations/round07/scripts/t013_recalibrate.json`<br>`labs/lottery/studies/dlt/iterations/round07/scripts/t014_forensics.json`<br>`labs/lottery/studies/dlt/iterations/round07/scripts/t015_external.json`<br>`labs/lottery/studies/dlt/iterations/round07/scripts/t016_holiday.json`<br>`labs/lottery/studies/dlt/iterations/round09/scripts/t013_recalibrate_r09.json`<br>`labs/lottery/studies/dlt/iterations/round09/scripts/t020_number_weight.json`<br>`labs/lottery/studies/dlt/iterations/round09/scripts/t046_r002_quantify.json`<br>`labs/lottery/studies/dlt/iterations/round10/scripts/t021_sales_endogeneity.json`<br>`labs/lottery/studies/dlt/iterations/round10/scripts/t022_illusion.json`<br>`labs/lottery/studies/dlt/iterations/round10/scripts/t028_recalibrate_r10.json`<br>`labs/lottery/studies/dlt/iterations/round10/scripts/t050_calibration.json`<br>`memory/facts/ACTIVE.md` |
| `test` | 14 | B | `tests/test_ai_readability.py`<br>`tests/test_claim_type.py`<br>`tests/test_consumes_completeness.py`<br>`tests/test_core.py`<br>`tests/test_cross_scope.py`<br>`tests/test_evidence_anchor.py`<br>`tests/test_flywheel.py`<br>`tests/test_meta_variables.py`<br>`tests/test_open_questions_consistency.py`<br>`tests/test_research_lib.py`<br>`tests/test_round_counter_sync.py`<br>`tests/test_derive_tasks.py`<br>`tests/test_round_stall.py`<br>`tests/test_shadow_game.py` |
| `library` | 11 | B | `research_lib/__init__.py`<br>`research_lib/stability.py`<br>`research_lib/stats.py`<br>`src/__init__.py`<br>`src/spc/__init__.py`<br>`src/spc/api.py`<br>`src/spc/evidence.py`<br>`src/spc/game.py`<br>`src/spc/memory.py`<br>`src/spc/strategy.py`<br>`src/spc/versions.py` |
| `analysis_script` | 9 | D | `labs/lottery/studies/dlt/data/tools/_load.py`<br>`labs/lottery/studies/dlt/data/tools/acf_permutation_test.py`<br>`labs/lottery/studies/dlt/data/tools/changepoint_refine.py`<br>`labs/lottery/studies/dlt/data/tools/changepoint_scan.py`<br>`labs/lottery/studies/dlt/data/tools/consecutive_exact_check.py`<br>`labs/lottery/studies/dlt/data/tools/exact_tests.py`<br>`labs/lottery/studies/dlt/data/tools/overdispersion_and_hac.py`<br>`labs/lottery/studies/dlt/data/tools/validate_data.py`<br>`labs/lottery/studies/dlt/strategy/strategy_simulation.py` |
| `journal` | 9 | A/B/C | `memory/journal/round02.md`<br>`memory/journal/round03.md`<br>`memory/journal/round05.md`<br>`memory/journal/round06.md`<br>`memory/journal/round07.md`<br>`memory/journal/round08.md`<br>`memory/journal/round09.md`<br>`memory/journal/round10.md`<br>`memory/journal/round11.md` |
| `derived_data` | 8 | D | `labs/lottery/studies/dlt/data/derived/01_yearly_stats.csv`<br>`labs/lottery/studies/dlt/data/derived/02_front_number_frequency.csv`<br>`labs/lottery/studies/dlt/data/derived/03_back_number_frequency.csv`<br>`labs/lottery/studies/dlt/data/derived/04_structure_distribution_exact.json`<br>`labs/lottery/studies/dlt/data/derived/05_back_combo_66.csv`<br>`labs/lottery/studies/dlt/data/derived/06_acf_lag1to60.csv`<br>`labs/lottery/studies/dlt/data/derived/07_data_quality_report.json`<br>`labs/lottery/studies/dlt/data/derived/08_rules_epoch_summary.json` |
| `framework_core` | 8 | B | `platform/core/__init__.py`<br>`platform/core/evaluate.py`<br>`platform/core/features.py`<br>`platform/core/game_util.py`<br>`platform/core/generate.py`<br>`platform/core/judge.py`<br>`platform/core/portfolio.py`<br>`platform/core/ticket.py` |
| `manifest` | 8 | A/B/D | `labs/lottery/studies/dlt/iterations/round05/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round10/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round11/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round12/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round13/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round14/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round15/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round16/manifest.json` |
| `data` | 7 | D | `labs/lottery/studies/dlt/iterations/round12/scripts/t049_holdout.json`<br>`labs/lottery/studies/dlt/iterations/round13/scripts/t051_walkforward.json`<br>`labs/lottery/studies/dlt/iterations/round14/scripts/t053_shape_ratios.json`<br>`labs/lottery/studies/dlt/iterations/round14/scripts/t054_walkforward_ci.json`<br>`labs/lottery/studies/dlt/iterations/round16/scripts/t013_recalibrate_r09.json`<br>`labs/lottery/studies/dlt/iterations/round16/scripts/t028_recalibrate_r10.json`<br>`labs/lottery/studies/dlt/iterations/round16/scripts/t064_h002_segment.json` |
| `iteration_manifest` | 6 | C | `labs/lottery/studies/dlt/iterations/round02/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round03/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round04/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round07/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round08/manifest.json`<br>`labs/lottery/studies/dlt/iterations/round09/manifest.json` |
| `template_game` | 6 | B | `labs/lottery/studies/_template/README.md`<br>`labs/lottery/studies/_template/data/build_scripts/README.md`<br>`labs/lottery/studies/_template/data/derived/README.md`<br>`labs/lottery/studies/_template/data/raw/README.md`<br>`labs/lottery/studies/_template/data/tools/README.md`<br>`labs/lottery/studies/_template/iterations/round01/TASK_BRIEF.md` |
| `schema` | 5 | C | `spec/fact.schema.json`<br>`spec/game_config.schema.json`<br>`spec/iteration.schema.json`<br>`spec/strategy.schema.json`<br>`spec/version_index.schema.json` |
| `repo_tool` | 4 | B | `tools/build_versions.py`<br>`tools/bump_iteration.py`<br>`tools/inject_version_lines.py`<br>`tools/render_version_index.py` |
| `build_script` | 3 | D | `labs/lottery/studies/dlt/data/build_scripts/build_derived_v4.py`<br>`labs/lottery/studies/dlt/data/build_scripts/hash_and_list.py`<br>`labs/lottery/studies/dlt/data/build_scripts/validate_package_v4.py` |
| `index` | 3 | A/B | `platform/INDEX.md`<br>`labs/lottery/INDEX.md`<br>`memory/INDEX.md` |
| `template` | 3 | B | `platform/protocol/templates/FINDINGS.template.md`<br>`platform/protocol/templates/HANDOFF.template.md`<br>`platform/protocol/templates/TASK_BRIEF.template.md` |
| `findings` | 2 | A/B | `labs/lottery/studies/dlt/iterations/round10/FINDINGS.md`<br>`labs/lottery/studies/dlt/iterations/round11/FINDINGS.md` |
| `game_config` | 2 | C | `labs/lottery/studies/_template/game.yaml`<br>`labs/lottery/studies/dlt/game.yaml` |
| `handoff` | 2 | A/B | `labs/lottery/studies/dlt/iterations/round10/HANDOFF.md`<br>`labs/lottery/studies/dlt/iterations/round11/HANDOFF.md` |
| `methodology` | 2 | B | `platform/methodology/MATH_BOUNDARY.md`<br>`platform/methodology/STATISTICAL_DISCIPLINE.md` |
| `protocol` | 2 | B | `platform/protocol/MEMORY_PROTOCOL.md`<br>`platform/protocol/README.md` |
| `raw_data` | 2 | D | `labs/lottery/studies/dlt/data/raw/dlt_full_2933.csv`<br>`labs/lottery/studies/dlt/data/raw/dlt_full_2933.jsonl` |
| `research_output` | 2 | D | `labs/lottery/studies/dlt/iterations/round11/scripts/t023_roll_decay.json`<br>`labs/lottery/studies/dlt/iterations/round11/scripts/t024_proxy.json` |
| `research_script` | 2 | C | `labs/lottery/studies/dlt/iterations/round11/scripts/t023_roll_decay.py`<br>`labs/lottery/studies/dlt/iterations/round11/scripts/t024_proxy.py` |
| `analysis_output` | 1 | D | `labs/lottery/studies/dlt/strategy/simulation_results.json` |
| `apply_script` | 1 | C | `labs/lottery/studies/dlt/iterations/round11/scripts/apply_r11_facts.py` |
| `cli` | 1 | B | `cli/main.py` |
| `contract` | 1 | C | `labs/lottery/studies/dlt/strategy/strategy.json` |
| `design` | 1 | B | `labs/lottery/studies/dlt/iterations/round11/T048_HOLDOUT_DESIGN.md` |
| `entry_point` | 1 | B | `AI_CONTEXT.md` |
| `fact_index` | 1 | A | `memory/facts/INDEX.md` |
| `facts` | 1 | A | `memory/facts/FACTS.jsonl` |
| `framework_tool` | 1 | B | `platform/tools/memory.py` |
| `lesson_library` | 1 | A | `memory/lessons/LESSONS.md` |
| `library_doc` | 1 | B | `research_lib/README.md` |
| `meta` | 1 | D | `.gitignore` |
| `package_manifest` | 1 | C | `pyproject.toml` |
| `rules_history` | 1 | A | `labs/lottery/studies/dlt/rules_history.md` |
| `source_manifest` | 1 | D | `labs/lottery/studies/dlt/manifest_v4_source.json` |
| `strategy` | 1 | C | `labs/lottery/studies/_template/strategy/strategy.json` |
| `task_brief` | 1 | B | `labs/lottery/studies/dlt/iterations/round11/TASK_BRIEF.md` |
| `test_fixture` | 1 | D | `tests/fixtures/shadow/game.yaml` |
| `test_tool` | 1 | D | `tools/count_tests.py` |
| `utility` | 1 | D | `tools/finish_round.py` |
| `version_index` | 1 | B | `versions.json` |
| `version_index_doc` | 1 | B | `VERSION_INDEX.md` |
| `workbench` | 1 | A | `memory/workbench/HYPOTHESES.md` |

---

## 4. 版本演化史

> 追加式，**不删历史行**。

| 版本 | 日期 | 范围 | 变更 |
|---|---|---|---|
| `1.7` | 2026-10-11 | r07 修复（续） | STRATEGY_GUIDE consumes 补 F-0033/F-0034；登记 tests/test_consumes_completeness.py。 |
| `1.6` | 2026-10-11 | r07 修复 | 下游声明完整性修复：STRATEGY_GUIDE consumes 补齐 F-0002/F-0026~F-0029 并升 1.5；validate 新增逆向检查（正文引用未声明即拦截）；SOP 收尾清单新增第 8 步。 |
| `1.5` | 2026-10-11 | round07 | 登记 r07 研究轮 13 个产物；FACTS 32→35（+F-0033/34/35，F-0032 superseded）；F-0004/F-0005 重校准维持。 |
| `1.1` | 2026-10-11 | platform/ | 跨注层（L3）从『只上报』升级为『可执行』，记为 framework_version 1.1。新增 platform/core/portfolio.py（Portfolio 一等公民 + evaluate_cross + judge_cross）；features.py 新增 CROSS_PRIMITIVES 独立注册表（5 个跨注原语），与单注原语分开注册、混用结构性拒收；game.yaml 与 strategy.json 新增 scope: single/cross 声明（config 2.0→2.1 / schema 1.0→1.1）；judge.classify_rules() 三路切分（single / cross / undeclared），'跨注'与'拼错'不再混为一谈；validate_strategy() 对未声明特征由 warning 升为 error，并对跨注规则做真样本冒烟执行。修复 1.0 的契约缺口：R-002 引用了从未声明、且全仓库无执行入口的跨注特征。登记文件 124 → 126。 |
| `1.0` | 2026-10-11 | 全仓库 | 建立版本体系：引入 content_version（内容版本）与 framework_version（框架版本），与既有 schema_version / config_version / data_version 并存分区；登记 A/B/C/D 四级共 124 个文件。 |
| `1.0` | 2026-10-10 | platform/ | 单注层通用架构落地（platform/core/ 6 模块 / 21 原语），记为 framework_version 1.0。 |
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
