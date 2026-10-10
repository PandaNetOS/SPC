# VERSION_INDEX.md — 仓库版本索引

> **本文件由 `python tools/render_version_index.py --write` 从 `versions.json` 自动生成。请勿手工编辑。**
> 权威源是 `versions.json`（受 `spec/version_index.schema.json` 约束）。

**索引版本**：`1.0` ｜ **框架版本**：`1.1` ｜ **当前轮次**：`r03` ｜ **生成日期**：2026-10-11

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
| **A** | 结论性内容 | ✅ | `content_version` | 随轮次演化、重复写错代价最高。文件内版本行 + 索引登记。 | 34 |
| **B** | 结构性文档 / 框架与库代码 | ✅ | `content_version` | 随框架演进但无『结论』性质。.md 加版本行；.py 只登记索引。 | 54 |
| **C** | 机器契约 | ❌ | — | 已有 schema_version / config_version / data_version / version 字段，各答不同问题。索引镜像其值，不重复加版本。 | 13 |
| **D** | 纯数据 / 分析脚本 | ❌ | — | raw 数据用 SHA256（比版本号更强的保证）；分析脚本随结论归档，不单独版本化。 | 25 |

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
| `games/dlt/iterations/round03/scripts/apply_r03_facts.py` | `1.0` | `r02` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/apply_r03_strategy.py` | `1.0` | `r02` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/b2_robust_estimators.json` | `1.0` | `r02` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/b2_robust_estimators.py` | `1.0` | `r02` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/b2_split_stability.json` | `1.0` | `r02` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/b2_split_stability.py` | `1.0` | `r02` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.json` | `1.0` | `r02` | 2026-10-11 | active |  |
| `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py` | `1.0` | `r02` | 2026-10-11 | active |  |
| `games/dlt/iterations/round04/TASK_BRIEF.md` | `1.0` | `r04` | 2026-10-11 | active | planned |
| `games/dlt/rules_history.md` | `1.1` | `r03` | 2026-10-11 | active | E0~E6 共 7 段（§3.3 措辞存疑；第 6 次实证已加 r03 更正标记） |
| `games/dlt/strategy/STRATEGY_GUIDE.md` | `1.1` | `r03` | 2026-10-11 | active | 面向普通读者的策略说明书（人话版）；r03 同步封顶修正 |
| `memory/INDEX.md` | `1.0` | `r02` | 2026-10-11 | active | 记忆层说明 |
| `memory/facts/FACTS.jsonl` | `1.1` | `r03` | 2026-10-11 | active | 18 条结论（F-0001~F-0018；F-0015 superseded） |
| `memory/facts/INDEX.md` | `1.1` | `r03` | 2026-10-11 | active | 派生物，由 cli index 生成 |
| `memory/journal/round02.md` | `1.0` | `r02` | 2026-10-11 | active | 整理入库轮 |
| `memory/journal/round03.md` | `1.0` | `r03` | 2026-10-11 | active | 复核轮（含 1 次自我纠错） |
| `memory/lessons/LESSONS.md` | `1.1` | `r03` | 2026-10-11 | active | L1–L12，只增不删（r03 新增 L10–L12） |
| `memory/workbench/HYPOTHESES.md` | `1.0` | `r02` | 2026-10-11 | active | H-001~H-005 |
| `memory/workbench/OPEN_QUESTIONS.md` | `1.2` | `r03` | 2026-10-11 | active | 11 问，3 answered（Q-001/Q-002/Q-004）；r03 框架迭代新增 Q-012（跨注规则量化） |
| `memory/workbench/TODO.md` | `1.3` | `r03` | 2026-10-11 | active | P0 已清空；T-043 已销账；**T-033 已销账**（R-002 跨注层，选 ②） |

### B 级 · 结构性文档 / 框架与库代码

| 路径 | 版本 | 轮次 | 状态 | 备注 |
|---|---|---|---|---|
| `AI_CONTEXT.md` | `1.2` | `r03` | active |  |
| `README.md` | `1.2` | `r03` | active |  |
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
| `framework/core/features.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/game_util.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/generate.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/judge.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/ticket.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `framework/core/portfolio.py` | —（见备注） | `—` | active | ★ 跨注层（L3）核心：Portfolio 一等公民 + 跨注求值 + judge_cross |
| `framework/methodology/MATH_BOUNDARY.md` | `1.0` | `r02` | active |  |
| `framework/methodology/STATISTICAL_DISCIPLINE.md` | `1.0` | `r02` | active |  |
| `framework/protocol/ITERATION_PROTOCOL.md` | `1.1` | `r03` | active |  |
| `framework/protocol/MEMORY_PROTOCOL.md` | `1.0` | `r02` | active |  |
| `framework/protocol/README.md` | `1.0` | `r02` | active |  |
| `framework/protocol/templates/FINDINGS.template.md` | `1.0` | `r02` | active |  |
| `framework/protocol/templates/HANDOFF.template.md` | `1.0` | `r02` | active |  |
| `framework/protocol/templates/TASK_BRIEF.template.md` | `1.0` | `r02` | active |  |
| `framework/tools/memory.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `games/INDEX.md` | `1.1` | `r03` | active |  |
| `games/_template/README.md` | —（见备注） | `—` | active |  |
| `games/_template/data/build_scripts/README.md` | —（见备注） | `—` | active |  |
| `games/_template/data/derived/README.md` | —（见备注） | `—` | active |  |
| `games/_template/data/raw/README.md` | —（见备注） | `—` | active |  |
| `games/_template/data/tools/README.md` | —（见备注） | `—` | active |  |
| `games/_template/iterations/round01/TASK_BRIEF.md` | —（见备注） | `—` | active |  |
| `spec/README.md` | `1.0` | `r02` | active |  |
| `spec/VERSIONING.md` | `1.1` | `r03` | active |  |
| `src/__init__.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/smartpickcore/__init__.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/smartpickcore/api.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/smartpickcore/game.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/smartpickcore/memory.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/smartpickcore/strategy.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/smartpickcore/validate.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `src/smartpickcore/versions.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tests/README.md` | `1.1` | `r03` | active |  |
| `tests/test_core.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tests/test_cross_scope.py` | —（见备注） | `—` | active | ★ 跨注层测试（scope 三分 / 跨注判定 / 结构性拒收）；无需 pytest |
| `tools/build_versions.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tools/inject_version_lines.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `tools/render_version_index.py` | —（见备注） | `r02` | active | 代码文件：不写文件内版本行（用 git blame） |
| `versions.json` | `1.0` | `r02` | generated |  |

### C 级 · 机器契约（用自身既有版本字段）

| 路径 | 版本字段 | 值 | 备注 |
|---|---|---|---|
| `games/_template/game.yaml` | `config_version` | `2.0` | 2026-10-11 与 dlt 同步升至 2.0（features 原语化） |
| `games/_template/strategy/strategy.json` | `config_version` | `2.0` | 模板策略，2026-10-11 随 game.yaml 同步至 2.0 |
| `games/dlt/game.yaml` | `config_version` | `2.1` | ★ 2026-10-11 由 1.0 升 2.0（features 原语化）；2.0 → 2.1（新增 scope: single/cross，声明 3 个跨注特征） |
| `games/dlt/iterations/round02/manifest.json` | `inputs.data_version` | `dlt_full_2933` |  |
| `games/dlt/iterations/round03/manifest.json` | `inputs.data_version` | `dlt_full_2933` |  |
| `games/dlt/iterations/round04/manifest.json` | `—` | `—` |  |
| `games/dlt/strategy/strategy.json` | `schema_version` | `1.1` | 契约版本；1.0 → 1.1（rules[] 新增必填 scope 字段；R-002 的 predicate 改为引用已声明的跨注特征 has_duplicated_structure，从此可真正执行） |
| `pyproject.toml` | `project.version` | `0.1.0` | 包版本 |
| `spec/fact.schema.json` | `—` | `—` | schema 自身无版本；约束 fact.schema_version |
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

---

## 3. 按内容类型检索

| 类型 | 数量 | 级别 | 文件 |
|---|---|---|---|
| `iteration_artifact` | 23 | A | `games/dlt/iterations/round02/FINDINGS.md`<br>`games/dlt/iterations/round02/HANDOFF.md`<br>`games/dlt/iterations/round02/PRIORITY_TASKS.md`<br>`games/dlt/iterations/round02/TASK_BRIEF.md`<br>`games/dlt/iterations/round02/known_errors.md`<br>`games/dlt/iterations/round02/legacy_findings/README.md`<br>`games/dlt/iterations/round02/legacy_findings/_round3_reference/round3_independent_review.html`<br>`games/dlt/iterations/round02/legacy_findings/round2_deep_analysis.txt`<br>`games/dlt/iterations/round02/legacy_findings/round2_glm_analysis.txt`<br>`games/dlt/iterations/round02/legacy_findings/round2_main_report.md`<br>`games/dlt/iterations/round02/legacy_findings/round2_verify_analysis.txt`<br>`games/dlt/iterations/round03/FINDINGS.md`<br>`games/dlt/iterations/round03/HANDOFF.md`<br>`games/dlt/iterations/round03/TASK_BRIEF.md`<br>`games/dlt/iterations/round03/scripts/apply_r03_facts.py`<br>`games/dlt/iterations/round03/scripts/apply_r03_strategy.py`<br>`games/dlt/iterations/round03/scripts/b2_robust_estimators.json`<br>`games/dlt/iterations/round03/scripts/b2_robust_estimators.py`<br>`games/dlt/iterations/round03/scripts/b2_split_stability.json`<br>`games/dlt/iterations/round03/scripts/b2_split_stability.py`<br>`games/dlt/iterations/round03/scripts/cap_adjusted_uplift.json`<br>`games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`<br>`games/dlt/iterations/round04/TASK_BRIEF.md` |
| `doc` | 12 | B | `README.md`<br>`docs/ARCHITECTURE.md`<br>`docs/CONSUMING.md`<br>`docs/ITERATION_GUIDE.md`<br>`docs/METHODOLOGY.md`<br>`docs/PROPOSAL_SINGLE_TICKET_CORE.md`<br>`docs/VERSIONING_DOCS.md`<br>`framework/README.md`<br>`framework/core/README.md`<br>`spec/README.md`<br>`spec/VERSIONING.md`<br>`tests/README.md` |
| `analysis_script` | 9 | D | `games/dlt/data/tools/_load.py`<br>`games/dlt/data/tools/acf_permutation_test.py`<br>`games/dlt/data/tools/changepoint_refine.py`<br>`games/dlt/data/tools/changepoint_scan.py`<br>`games/dlt/data/tools/consecutive_exact_check.py`<br>`games/dlt/data/tools/exact_tests.py`<br>`games/dlt/data/tools/overdispersion_and_hac.py`<br>`games/dlt/data/tools/validate_data.py`<br>`games/dlt/strategy/strategy_simulation.py` |
| `derived_data` | 8 | D | `games/dlt/data/derived/01_yearly_stats.csv`<br>`games/dlt/data/derived/02_front_number_frequency.csv`<br>`games/dlt/data/derived/03_back_number_frequency.csv`<br>`games/dlt/data/derived/04_structure_distribution_exact.json`<br>`games/dlt/data/derived/05_back_combo_66.csv`<br>`games/dlt/data/derived/06_acf_lag1to60.csv`<br>`games/dlt/data/derived/07_data_quality_report.json`<br>`games/dlt/data/derived/08_rules_epoch_summary.json` |
| `framework_core` | 8 | B | `framework/core/__init__.py`<br>`framework/core/evaluate.py`<br>`framework/core/features.py`<br>`framework/core/game_util.py`<br>`framework/core/generate.py`<br>`framework/core/judge.py`<br>`framework/core/ticket.py`<br>`framework/core/portfolio.py` |
| `library` | 8 | B | `src/__init__.py`<br>`src/smartpickcore/__init__.py`<br>`src/smartpickcore/api.py`<br>`src/smartpickcore/game.py`<br>`src/smartpickcore/memory.py`<br>`src/smartpickcore/strategy.py`<br>`src/smartpickcore/validate.py`<br>`src/smartpickcore/versions.py` |
| `template_game` | 6 | B | `games/_template/README.md`<br>`games/_template/data/build_scripts/README.md`<br>`games/_template/data/derived/README.md`<br>`games/_template/data/raw/README.md`<br>`games/_template/data/tools/README.md`<br>`games/_template/iterations/round01/TASK_BRIEF.md` |
| `schema` | 5 | C | `spec/fact.schema.json`<br>`spec/game_config.schema.json`<br>`spec/iteration.schema.json`<br>`spec/strategy.schema.json`<br>`spec/version_index.schema.json` |
| `build_script` | 3 | D | `games/dlt/data/build_scripts/build_derived_v4.py`<br>`games/dlt/data/build_scripts/hash_and_list.py`<br>`games/dlt/data/build_scripts/validate_package_v4.py` |
| `index` | 3 | A/B | `memory/INDEX.md`<br>`framework/INDEX.md`<br>`games/INDEX.md` |
| `iteration_manifest` | 3 | C | `games/dlt/iterations/round02/manifest.json`<br>`games/dlt/iterations/round03/manifest.json`<br>`games/dlt/iterations/round04/manifest.json` |
| `protocol` | 3 | B | `framework/protocol/ITERATION_PROTOCOL.md`<br>`framework/protocol/MEMORY_PROTOCOL.md`<br>`framework/protocol/README.md` |
| `repo_tool` | 3 | B | `tools/build_versions.py`<br>`tools/inject_version_lines.py`<br>`tools/render_version_index.py` |
| `template` | 3 | B | `framework/protocol/templates/FINDINGS.template.md`<br>`framework/protocol/templates/HANDOFF.template.md`<br>`framework/protocol/templates/TASK_BRIEF.template.md` |
| `workbench` | 3 | A | `memory/workbench/HYPOTHESES.md`<br>`memory/workbench/OPEN_QUESTIONS.md`<br>`memory/workbench/TODO.md` |
| `game_config` | 2 | C | `games/_template/game.yaml`<br>`games/dlt/game.yaml` |
| `journal` | 2 | A | `memory/journal/round02.md`<br>`memory/journal/round03.md` |
| `methodology` | 2 | B | `framework/methodology/MATH_BOUNDARY.md`<br>`framework/methodology/STATISTICAL_DISCIPLINE.md` |
| `raw_data` | 2 | D | `games/dlt/data/raw/dlt_full_2933.csv`<br>`games/dlt/data/raw/dlt_full_2933.jsonl` |
| `strategy` | 2 | C | `games/_template/strategy/strategy.json`<br>`games/dlt/strategy/strategy.json` |
| `test` | 2 | B | `tests/test_core.py`<br>`tests/test_cross_scope.py` |
| `analysis_output` | 1 | D | `games/dlt/strategy/simulation_results.json` |
| `cli` | 1 | B | `cli/main.py` |
| `entry_point` | 1 | B | `AI_CONTEXT.md` |
| `fact_index` | 1 | A | `memory/facts/INDEX.md` |
| `fact_ledger` | 1 | A | `memory/facts/FACTS.jsonl` |
| `framework_tool` | 1 | B | `framework/tools/memory.py` |
| `lesson_library` | 1 | A | `memory/lessons/LESSONS.md` |
| `meta` | 1 | D | `.gitignore` |
| `package_manifest` | 1 | C | `pyproject.toml` |
| `rules_history` | 1 | A | `games/dlt/rules_history.md` |
| `source_manifest` | 1 | D | `games/dlt/manifest_v4_source.json` |
| `strategy_guide` | 1 | A | `games/dlt/strategy/STRATEGY_GUIDE.md` |
| `version_index` | 1 | B | `versions.json` |
| `version_index_doc` | 1 | B | `VERSION_INDEX.md` |

---

## 4. 版本演化史

> 追加式，**不删历史行**。

| 版本 | 日期 | 范围 | 变更 |
|---|---|---|---|
| `1.1` | 2026-10-11 | framework/ | 跨注层（L3）从『只上报』升级为『可执行』，记为 framework_version 1.1。新增 framework/core/portfolio.py（Portfolio 一等公民 + evaluate_cross + judge_cross）；features.py 新增 CROSS_PRIMITIVES 独立注册表（5 个跨注原语），与单注原语分开注册、混用结构性拒收；game.yaml 与 strategy.json 新增 scope: single/cross 声明（config 2.0→2.1 / schema 1.0→1.1）；judge.classify_rules() 三路切分（single / cross / undeclared），'跨注'与'拼错'不再混为一谈；validate_strategy() 对未声明特征由 warning 升为 error，并对跨注规则做真样本冒烟执行。修复 1.0 的契约缺口：R-002 引用了从未声明、且全仓库无执行入口的跨注特征。登记文件 124 → 126。 |
| `1.0` | 2026-10-11 | 全仓库 | 建立版本体系：引入 content_version（内容版本）与 framework_version（框架版本），与既有 schema_version / config_version / data_version 并存分区；登记 A/B/C/D 四级共 124 个文件。 |
| `1.0` | 2026-10-10 | framework/ | 单注层通用架构落地（framework/core/ 6 模块 / 21 原语），记为 framework_version 1.0。 |

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
