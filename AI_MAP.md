# AI_MAP —— SPC 机器可读地图


> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **本文件是派生物**：由 `tools/render_ai_map.py` 从 versions.json 生成；
> 新增文件登记 versions.json 后运行 `--write` 同步，勿手改。

> SPC：彩票投注策略研究框架（自我迭代）—— 研究结论输出为机器可读
> 策略规则。AI 快速了解本项目：先读本地图定分区，再读 AI_CONTEXT.md
> （深度入口）与 AGENTS.md（操作规则）。

## 入口（先读）
- `AI_CONTEXT.md` — 单一入口；r05 同步投注方式等价性、R-002 量化不成立、H-005 证伪、32 条结论
- `AGENTS.md` — 给 AI 的操作规则极简入口（六域，指向 AI_CONTEXT）
- `README.md` — 仓库总览；r05 研究要点 + r06 策略落地（R-002 重构 / R-003 新增，用户批准）+ r07 修复轮…
- `VERSION_INDEX.md` — 版本索引（人读），权威源是 versions.json
- `versions.json`
- `pyproject.toml` — 包版本
- `AI_MAP.md` — 机器地图（派生物，render_ai_map 生成）
- `DEPENDENCY_MAP.md` — 跨文件依赖图（派生物，render_dependency_map 生成）
- `FLYWHEEL_HEALTH.md` — 飞轮健康度仪表盘（派生物，render_flywheel_health 生成）

## 契约
- `spec/README.md`
- `spec/VERSIONING.md`
- `spec/fact.schema.json` — evidence 新增 noop_count
- `spec/game_config.schema.json` — schema 自身无版本；约束 game_config.config_version
- `spec/iteration.schema.json` — schema 自身无版本；约束 iteration 结构
- `spec/strategy.schema.json` — metric enum 同步为 expected_bonus_given_win
- `spec/version_index.schema.json` — schema 自身无版本；约束 versions.index_version

## 框架
- `framework/INDEX.md`
- `framework/README.md`
- `framework/core/README.md`
- `framework/core/__init__.py` — 代码文件：不写文件内版本行（用 git blame）
- `framework/core/evaluate.py` — 代码文件：不写文件内版本行（用 git blame）
- `framework/core/features.py` — 新增跨注原语 duplicate_ticket_count / duplicate_ticket_count_ge（F…
- `framework/core/game_util.py` — 代码文件：不写文件内版本行（用 git blame）
- `framework/core/generate.py` — 代码文件：不写文件内版本行（用 git blame）
- `framework/core/judge.py` — 代码文件：不写文件内版本行（用 git blame）
- `framework/core/portfolio.py` — ★ 跨注层（L3）核心：Portfolio 一等公民 + 跨注求值 + judge_cross
- `framework/core/ticket.py` — 代码文件：不写文件内版本行（用 git blame）
- `framework/methodology/MATH_BOUNDARY.md`
- `framework/methodology/STATISTICAL_DISCIPLINE.md`
- `framework/protocol/ITERATION_PROTOCOL.md`
- `framework/protocol/MEMORY_PROTOCOL.md` — r03 框架迭代：新增 §1.7 claim_type 证据类型 + §1.8 证据锚定
- `framework/protocol/README.md`
- `framework/tools/compress_memory.py` — 记忆压缩（每 5 轮）：ACTIVE.md + merge 候选 + 到期清单（IterResearch 依据）
- `framework/tools/ingate.py` — 新增 _evidence_tier 分档校验
- `framework/tools/memory.py` — 代码文件：不写文件内版本行（用 git blame）；open_questions() 状态解析归一化（容忍 →/（）…

## 记忆
- `memory/INDEX.md` — 记忆层说明
- `memory/facts/ACTIVE.md` — 当前有效结论清单（与台账分离，compress_memory 生成）
- `memory/facts/FACTS.jsonl` — 新增 F-0036 全奖级口径
- `memory/facts/INDEX.md` — 派生物，由 cli index 生成（32 条）
- `memory/journal/round02.md` — 整理入库轮
- `memory/journal/round03.md` — 复核轮（含 1 次自我纠错）
- `memory/journal/round04.md`
- `memory/journal/round05.md` — 叙事：R-002 量化不成立 + H-005 证伪
- `memory/journal/round06.md` — r06 叙事（元层轮）
- `memory/journal/round07.md` — r07 叙事（研究轮）
- `memory/journal/round08.md` — 体系升级批执行日志
- `memory/lessons/LESSONS.md` — L1–L14，只增不删（r04 新增 L13 口径自由度 / L14 分段自洽性前置检查；L7 追加第二实例）
- `memory/spec/ITERATION_SOP_v2.md` — 证据门控式迭代规范 v2（C+X 协议已并入）：收尾清单第10步引 finish_round.py；新增§9 并行研究…
- `memory/workbench/HYPOTHESES.md` — H-001~H-006（H-006 refuted）
- `memory/workbench/OPEN_QUESTIONS.md` — 11 问，5 answered（Q-001/002/004/013/014）
- `memory/workbench/TODO.md` — 新增 T-046/047/048

## 策略输出
- `games/_template/strategy/strategy.json` — 模板策略，2026-10-11 随 game.yaml 同步至 2.0

## 彩种
- `games/_template/README.md`
- `games/_template/game.yaml` — 2026-10-11 与 dlt 同步升至 2.0（features 原语化）
- `games/_template/iterations/round01/TASK_BRIEF.md`

## 工具与 CLI
- `cli/main.py` — 代码文件：不写文件内版本行（用 git blame）
- `tools/build_versions.py` — 代码文件：不写文件内版本行（用 git blame）
- `tools/count_tests.py` — 登记测试文件 + --inject（T-045：tests/README 计数自举注入）
- `tools/finish_round.py` — 收尾自动化（C1）：rehash→count_tests--inject→validate→渲染→四件套检查→批准门提示
- `tools/inject_version_lines.py` — 代码文件：不写文件内版本行（用 git blame）
- `tools/register_r06_upgrade.py` — r06 批量实施登记脚本（一次性，登记含自身）
- `tools/render_ai_map.py` — AI_MAP.md 渲染器（--write 写回）
- `tools/render_dependency_map.py` — DEPENDENCY_MAP.md 渲染器
- `tools/render_flywheel_health.py` — FLYWHEEL_HEALTH.md 渲染器
- `tools/render_readme_tree.py` — 目录树渲染 CLI（--write 写回 README）
- `tools/render_task_brief.py` — 任务书生成器（B+G/X）：--top N 控制必做数；resource 资源前置（Z）；必做≥2 输出并行研究建议段…
- `tools/render_version_index.py` — 代码文件：不写文件内版本行（用 git blame）
- `tools/report_calibration.py` — 置信度校准报告（D1）

## 工具与 CLI
- `cli/main.py` — 代码文件：不写文件内版本行（用 git blame）
- `tools/build_versions.py` — 代码文件：不写文件内版本行（用 git blame）
- `tools/count_tests.py` — 登记测试文件 + --inject（T-045：tests/README 计数自举注入）
- `tools/finish_round.py` — 收尾自动化（C1）：rehash→count_tests--inject→validate→渲染→四件套检查→批准门提示
- `tools/inject_version_lines.py` — 代码文件：不写文件内版本行（用 git blame）
- `tools/register_r06_upgrade.py` — r06 批量实施登记脚本（一次性，登记含自身）
- `tools/render_ai_map.py` — AI_MAP.md 渲染器（--write 写回）
- `tools/render_dependency_map.py` — DEPENDENCY_MAP.md 渲染器
- `tools/render_flywheel_health.py` — FLYWHEEL_HEALTH.md 渲染器
- `tools/render_readme_tree.py` — 目录树渲染 CLI（--write 写回 README）
- `tools/render_task_brief.py` — 任务书生成器（B+G/X）：--top N 控制必做数；resource 资源前置（Z）；必做≥2 输出并行研究建议段…
- `tools/render_version_index.py` — 代码文件：不写文件内版本行（用 git blame）
- `tools/report_calibration.py` — 置信度校准报告（D1）

## 测试
- `tests/README.md` — 测试说明（自举计数：合计 333，含 test_structure 8）
- `tests/test_ai_readability.py` — P1/P2/B/H/I 测试
- `tests/test_claim_type.py` — ★ 结论证据类型测试（五类约束真的会拦 / schema 与 Python 双通道一致）；无需 pytest
- `tests/test_consumes_completeness.py` — 代码文件：不写文件内版本行（用 git blame）
- `tests/test_core.py` — 代码文件：不写文件内版本行（用 git blame）
- `tests/test_cross_scope.py` — ★ 跨注层测试（scope 三分 / 跨注判定 / 结构性拒收）；无需 pytest
- `tests/test_evidence_anchor.py` — ★ 证据锚定测试（漂移真能检出 / 该敏感的要敏感、该迟钝的要迟钝 / 重基线幂等）；无需 pytest
- `tests/test_flywheel.py` — K/D1/D2/C/F 测试（无需 pytest）
- `tests/test_meta_variables.py` — schema 1.3 元数据（convenience/experience/psychology）结构+红线+CLI …
- `tests/test_open_questions_consistency.py` — Q 状态一致性回归：解析归一化/头部计数滞后/标题缺✅/优先级表active含已清偿/状态词非法
- `tests/test_research_lib.py` — research_lib 原语测试（已知分布验证可复现/正确性/样本不足不硬报）
- `tests/test_shadow_game.py`
- `tests/test_structure.py` — 结构完整性回归测试（P1-2 三道防线）

## 库代码
- `src/__init__.py` — 代码文件：不写文件内版本行（用 git blame）
- `src/spc/__init__.py` — 代码文件：不写文件内版本行（用 git blame）
- `src/spc/ai_map.py` — AI_MAP 生成源（llms.txt 式机器地图）
- `src/spc/api.py` — 代码文件：不写文件内版本行（用 git blame）
- `src/spc/depmap.py` — 跨文件依赖图生成源（C）
- `src/spc/evidence.py` — ★ 证据锚定：sha256_file / fact_anchor / evidence_digest（结论与策略的哈希…
- `src/spc/flywheel.py` — 飞轮健康度统计 + 置信度校准（K/D1）
- `src/spc/game.py` — 代码文件：不写文件内版本行（用 git blame）
- `src/spc/memory.py` — 代码文件：不写文件内版本行（用 git blame）
- `src/spc/strategy.py` — 代码文件：不写文件内版本行（用 git blame）
- `src/spc/tree.py` — 目录树生成源（P1-2）：README 树 = 派生物
- `src/spc/validate.py` — r07：新增 _check_consumes_completeness 逆向声明完整性检查；r08：新增 _check…
- `src/spc/versions.py` — 代码文件：不写文件内版本行（用 git blame）

## 文档
- `docs/ARCHITECTURE.md`
- `docs/CONSUMING.md`
- `docs/ITERATION_GUIDE.md`
- `docs/METHODOLOGY.md`
- `docs/PROPOSAL_SINGLE_TICKET_CORE.md`
- `docs/VERSIONING_DOCS.md`
