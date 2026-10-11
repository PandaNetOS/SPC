# SPC

> **版本**：`1.16` ｜ 轮次 `r12` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
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

> **选号不改变中奖概率（各奖级概率恒定）。**

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

### 👉 [**超级大乐透 · 策略说明书（人话版）**](games/dlt/strategy/STRATEGY_GUIDE.md) &nbsp;`v1.9`

> 路径：`games/dlt/strategy/STRATEGY_GUIDE.md` — 版本 `v1.9`（轮次 `r14`，更新 2026-10-11）— 不需要任何背景知识

它讲清了四件事：策略说了什么、为什么可能有用、
**什么时候它没用（四个减损项，其中 1 亿封顶已真实触发过）**、以及绝对不要做的事。

> 一句话预告：**本策略不提高中奖概率，只在中奖时可能让你少跟别人分钱；
> 买单注的人基本用不上，买多注的人别把号码挤在一起。**

下面开始是给**开发者与研究者**的内容。

---

## 快速开始

```bash
# 依赖

> **版本**：`1.16` ｜ 轮次 `r11` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

pip install pyyaml jsonschema numpy pandas

# 仓库概览
python cli/main.py info

# 全量校验（94 项：schema / 红线 / 外键 / 双向取代 / SHA256 实算 / 证据锚定漂移 / 版本一致性 / 跨注规则冒烟 / 概率口径）
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
├── pyproject.toml  v0.1.0    ← 包版本
├── AI_CONTEXT.md  v1.5      ← FACTS 计数 38→43
├── VERSION_INDEX.md  v1.0      ← 版本索引（人读），权威源是 versions.json
├── versions.json  v1.0
├── README.md  v1.16     ← ← 速览区 47 条结论 / open 2 / r12 彩种行
├── AGENTS.md  v1.0      ← 给 AI 的操作规则极简入口（六域，指向 AI_CONTEXT）
├── AI_MAP.md  v1.0      ← 机器地图（派生物，render_ai_map 生成）
├── DEPENDENCY_MAP.md  v1.0      ← 跨文件依赖图（派生物，render_dependency_map 生成）
├── FLYWHEEL_HEALTH.md  v1.0      ← 飞轮健康度仪表盘（派生物，render_flywheel_health…
├── cli/
│   └── main.py  —         ← 代码文件：不写文件内版本行（用 git blame）
├── docs/
│   ├── ARCHITECTURE.md  v1.1
│   ├── CONSUMING.md  v1.1
│   ├── ITERATION_GUIDE.md  v1.0
│   ├── METHODOLOGY.md  v1.0
│   ├── PROPOSAL_SINGLE_TICKET_CORE.md  v1.1
│   └── VERSIONING_DOCS.md  v1.3
├── framework/
│   ├── INDEX.md  v1.1
│   ├── README.md  v1.0
│   ├── core/
│   │   ├── README.md  v1.1
│   │   ├── __init__.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│   │   ├── evaluate.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│   │   ├── features.py  —         ← 新增跨注原语 duplicate_ticket_count / dup…
│   │   ├── game_util.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│   │   ├── generate.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│   │   ├── judge.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│   │   ├── portfolio.py  —         ← ★ 跨注层（L3）核心：Portfolio 一等公民 + 跨注求值 +…
│   │   └── ticket.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│   ├── methodology/
│   │   ├── MATH_BOUNDARY.md  v1.1      ← r10.1：红线表格 P=1/T 加一等奖限定（各奖级恒定）
│   │   └── STATISTICAL_DISCIPLINE.md  v1.0
│   ├── protocol/
│   │   ├── ITERATION_PROTOCOL.md  v1.2      ← r12: T-040 回写 §6 校验扩展 + §7 禁止事项 5 条…
│   │   ├── MEMORY_PROTOCOL.md  v1.2      ← r03 框架迭代：新增 §1.7 claim_type 证据类型 + …
│   │   └── README.md  v1.0
│   └── tools/
│       ├── compress_memory.py  v1.0      ← 记忆压缩（每 5 轮）：ACTIVE.md + merge 候选 + …
│       ├── ingate.py  v1.1      ← 新增 _evidence_tier 分档校验
│       └── memory.py  —         ← 代码文件：不写文件内版本行（用 git blame）；open_que…
├── games/
│   ├── INDEX.md  v1.2      ← 彩种索引（r04：结论数 18 → 25；轮次 round04 ✅ /…
│   ├── _template/
│   │   ├── README.md  —
│   │   ├── game.yaml  v2.0      ← 2026-10-11 与 dlt 同步升至 2.0（features …
│   │   ├── iterations/
│   │   │   └── round01/
│   │   │       └── TASK_BRIEF.md  —
│   │   └── strategy/
│   │       └── strategy.json  v2.0      ← 模板策略，2026-10-11 随 game.yaml 同步至 2.0
│   └── dlt/
│       ├── game.yaml  v2.2      ← r14.1: +has_mirror_pair 特征（R-004 判定…
│       ├── iterations/
│       │   ├── round02/
│       │   │   ├── FINDINGS.md  v1.0      ← 整理入库轮发现
│       │   │   ├── HANDOFF.md  v1.0      ← r02→r03 交接
│       │   │   ├── PRIORITY_TASKS.md  v1.0
│       │   │   ├── TASK_BRIEF.md  v1.0      ← 已交付
│       │   │   ├── known_errors.md  v1.0      ← E1~E9 避坑手册
│       │   │   ├── legacy_findings/
│       │   │   │   ├── README.md  v1.0      ← 归档，设使用门槛
│       │   │   │   ├── _round3_reference/
│       │   │   │   │   └── round3_independent_review.html  v1.0      ← 历史归档，设使用门槛（防锚定）
│       │   │   │   ├── round2_deep_analysis.txt  v1.0      ← 历史归档，设使用门槛（防锚定）
│       │   │   │   ├── round2_glm_analysis.txt  v1.0      ← 历史归档，设使用门槛（防锚定）
│       │   │   │   ├── round2_main_report.md  v1.0      ← 历史归档，设使用门槛（防锚定）
│       │   │   │   └── round2_verify_analysis.txt  v1.0      ← 历史归档，设使用门槛（防锚定）
│       │   │   └── manifest.json  vdlt_full_2933
│       │   ├── round03/
│       │   │   ├── FINDINGS.md  v1.0      ← 复核轮发现（含自我纠错）
│       │   │   ├── HANDOFF.md  v1.0      ← r03→r04 交接
│       │   │   ├── TASK_BRIEF.md  v1.0      ← 已交付
│       │   │   ├── manifest.json  vdlt_full_2933
│       │   │   └── scripts/  ← 轮次脚本（8 个）
│       │   ├── round04/
│       │   │   ├── FINDINGS.md  v1.0
│       │   │   ├── HANDOFF.md  v1.0
│       │   │   ├── TASK_BRIEF.md  v1.0      ← 已交付（round04 执行完毕）
│       │   │   ├── manifest.json  —
│       │   │   └── scripts/  ← 轮次脚本（8 个）
│       │   ├── round05/
│       │   │   ├── FINDINGS.md  v1.0      ← 投注方式数学层 + R-002 量化 + 时间因素证伪
│       │   │   ├── HANDOFF.md  v1.0      ← r05→r06 交接；策略变更待用户批准
│       │   │   ├── TASK_BRIEF.md  v1.0      ← 已交付（round05 执行完毕；用户点名方向优先，T-201 顺延 …
│       │   │   ├── manifest.json  v1.0
│       │   │   └── scripts/  ← 轮次脚本（7 个）
│       │   ├── round06/
│       │   │   ├── FINDINGS.md  v1.0      ← r06 元层轮发现（策略落地+飞轮升级）
│       │   │   ├── HANDOFF.md  v1.0      ← r06→r07 交接（结论/遗留/下轮建议）
│       │   │   ├── TASK_BRIEF.md  v1.0      ← 由 round05 HANDOFF 转写（planned；T-201 …
│       │   │   ├── manifest.json  v1.0      ← r06 机器登记
│       │   │   ├── research/
│       │   │   │   ├── ai_readability_proposal.md  v1.0      ← AI 可读性升级方案稿（P0/P1/P2，待批准）
│       │   │   │   └── flywheel_upgrade_plan.md  v1.0      ← 迭代飞轮全局升级计划（A-K 环节链路 + 分批）
│       │   │   └── scripts/  ← 轮次脚本（13 个）
│       │   ├── round07/
│       │   │   ├── FINDINGS.md  v1.0      ← 前段取证+外部核对+节假日验证+锚点重校准
│       │   │   ├── HANDOFF.md  v1.0      ← r07→r08 交接
│       │   │   ├── TASK_BRIEF.md  v1.0      ← r07 任务书（render_task_brief 生成，T-014 …
│       │   │   ├── manifest.json  vdlt_full_2933  ← r07 机器登记
│       │   │   └── scripts/  ← 轮次脚本（9 个）
│       │   ├── round08/
│       │   │   ├── FINDINGS.md  v1.0      ← 体系升级轮发现（C1 注入器自愈 / Y 方法库 / X 协议 / 四…
│       │   │   ├── HANDOFF.md  v1.0      ← r08→r09 交接（P0：动态锚点重校准 + T-046/T-047…
│       │   │   ├── manifest.json  —         ← 体系升级批清单（C+X+Y+Z）
│       │   │   └── scripts/  ← 轮次脚本（2 个）
│       │   ├── round09/
│       │   │   ├── FINDINGS.md  v1.0      ← 策略量化轮发现（R-002 量化 / NOOP 实战 / 逐号偏好 /…
│       │   │   ├── HANDOFF.md  v1.0      ← r09→r10 交接（F-0037/38；遗留 T-021/22/23…
│       │   │   ├── TASK_BRIEF.md  v1.0      ← 任务书：T-046/T-047/T-020 + 并行建议（X）
│       │   │   ├── manifest.json  —         ← 策略量化轮清单
│       │   │   └── scripts/  ← 轮次脚本（7 个）
│       │   ├── round10/
│       │   │   ├── FINDINGS.md  v1.1      ← r10 结论 + r10.1 漏网根治补记（自动派生挖出 STRATE…
│       │   │   ├── HANDOFF.md  v1.1      ← r10→r11 交接 + r10.1 概率口径护栏升级（扫描范围自动派…
│       │   │   ├── TASK_BRIEF.md  v1.0      ← 任务书：T-050/T-021/T-022（T-050 概率口径根治，…
│       │   │   ├── manifest.json  v1.0      ← r10 轮清单
│       │   │   └── scripts/  ← 轮次脚本（9 个）
│       │   ├── round11/
│       │   │   ├── FINDINGS.md  v1.0      ← r11 结论：F-0042 平台期 / F-0043 代理可观测 / …
│       │   │   ├── HANDOFF.md  v1.0      ← r11→r12 交接：T-048b 首推 + T-025 仍 bloc…
│       │   │   ├── T048_HOLDOUT_DESIGN.md  v1.0      ← T-048 L3 组合优化预备：时序 hold-out 评测设计（切分…
│       │   │   ├── TASK_BRIEF.md  v1.0      ← r11 任务书：T-023/T-024/T-048（render_ta…
│       │   │   ├── manifest.json  —         ← r11 deliverables（根级）
│       │   │   └── scripts/  ← 轮次脚本（5 个）
│       │   ├── round12/
│       │   │   ├── FINDINGS.md  v1.0      ← r12 研究结论
│       │   │   ├── HANDOFF.md  v1.0      ← r12→r13 交接
│       │   │   ├── TASK_BRIEF.md  v1.0      ← r12 任务书（T-049/T-030/T-040）
│       │   │   ├── manifest.json  —         ← r12 manifest
│       │   │   └── scripts/  ← 轮次脚本（3 个）
│       │   ├── round13/
│       │   │   ├── FINDINGS.md  v1.0      ← r13 研究结论
│       │   │   ├── HANDOFF.md  v1.0      ← r13 交接
│       │   │   ├── TASK_BRIEF.md  v1.0      ← r13 任务书（T-051/T-044/T-045）
│       │   │   ├── manifest.json  —         ← r13 manifest
│       │   │   └── scripts/  ← 轮次脚本（2 个）
│       │   └── round14/
│       │       ├── FINDINGS.md  v1.0      ← r14 研究结论
│       │       ├── HANDOFF.md  v1.0      ← r14 交接
│       │       ├── TASK_BRIEF.md  v1.0      ← r14 任务书（T-052 待批准/T-053/T-054）
│       │       ├── manifest.json  —         ← r14 manifest
│       │       └── scripts/  ← 轮次脚本（4 个）
│       ├── manifest_v4_source.json  —
│       ├── rules_history.md  v1.1      ← E0~E6 共 7 段（§3.3 措辞存疑；第 6 次实证已加 r03…
│       └── strategy/
│           ├── STRATEGY_GUIDE.md  v1.9      ← r14.1: R-004 小节 + 三档表 B 档行（v1.8→1.9）
│           ├── simulation_results.json  —
│           ├── strategy.json  v1.5      ← r14.1: R-004 落地（用户批准 T-052）；schema …
│           └── strategy_simulation.py  —         ← r10.1：docstring 一等奖概率口径
├── memory/
│   ├── INDEX.md  v1.0      ← 记忆层说明
│   ├── facts/
│   │   ├── ACTIVE.md  —         ← 当前有效结论清单（与台账分离，compress_memory 生成）
│   │   ├── FACTS.jsonl  v1.5      ← r14: +F-0046（高区撞号<1）/F-0047（单步显著 1/…
│   │   └── INDEX.md  v1.5      ← 派生物，由 cli index 生成（32 条）
│   ├── journal/
│   │   ├── round02.md  v1.0      ← 整理入库轮
│   │   ├── round03.md  v1.0      ← 复核轮（含 1 次自我纠错）
│   │   ├── round04.md  v1.0
│   │   ├── round05.md  v1.0      ← 叙事：R-002 量化不成立 + H-005 证伪
│   │   ├── round06.md  v1.0      ← r06 叙事（元层轮）
│   │   ├── round07.md  v1.0      ← r07 叙事（研究轮）
│   │   ├── round08.md  v1.0      ← 体系升级批执行日志
│   │   ├── round09.md  v1.0      ← 策略量化轮执行日志
│   │   ├── round10.md  v1.0      ← r10 执行日志
│   │   ├── round11.md  v1.0      ← r11 执行日志（含 schema 踩坑序列与 BOM 根治）
│   │   ├── round12.md  v1.0      ← r12 执行日志
│   │   ├── round13.md  v1.0      ← r13 执行日志
│   │   └── round14.md  v1.0      ← r14 执行日志
│   ├── lessons/
│   │   └── LESSONS.md  v1.3      ← L1–L15，只增不删（r10.1 新增 L15：命中清单全量核对 +…
│   ├── spec/
│   │   └── ITERATION_SOP_v2.md  v1.3      ← 证据门控式迭代规范 v2（C+X 协议已并入）：收尾清单第10步引 f…
│   └── workbench/
│       ├── HYPOTHESES.md  v1.2      ← H-001~H-006（H-006 refuted）
│       ├── OPEN_QUESTIONS.md  v1.7      ← r12: Q-008 → answered（open 3→2：Q-00…
│       └── TODO.md  v2.1      ← r14: T-053/T-054 → done，T-052 证据闭合待…
├── research_lib/
│   ├── README.md  —         ← 原语→来源脚本→历史结论映射表 + 使用纪律
│   ├── __init__.py  —         ← 研究资本化（Y）：彩种无关统计原语出口
│   ├── stability.py  —         ← split_ratio_stability / ci_overlap（…
│   └── stats.py  —         ← bootstrap_ci / ratio_and_boot / wil…
├── spec/
│   ├── README.md  v1.0
│   ├── VERSIONING.md  v1.2
│   ├── fact.schema.json  —         ← evidence 新增 noop_count
│   ├── game_config.schema.json  —         ← schema 自身无版本；约束 game_config.config_…
│   ├── iteration.schema.json  —         ← schema 自身无版本；约束 iteration 结构
│   ├── strategy.schema.json  —         ← metric enum 同步为 expected_bonus_give…
│   └── version_index.schema.json  —         ← schema 自身无版本；约束 versions.index_vers…
├── src/
│   ├── __init__.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│   └── spc/
│       ├── __init__.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│       ├── ai_map.py  —         ← AI_MAP 生成源（llms.txt 式机器地图）
│       ├── api.py  —         ← r10.1：generate 概率口径限定（各奖级恒定；一等奖恒为 1…
│       ├── depmap.py  —         ← 跨文件依赖图生成源（C）
│       ├── evidence.py  —         ← ★ 证据锚定：sha256_file / fact_anchor / …
│       ├── flywheel.py  —         ← 飞轮健康度统计 + 置信度校准（K/D1）
│       ├── game.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│       ├── memory.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│       ├── strategy.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│       ├── tree.py  —         ← 目录树生成源（P1-2）：README 树 = 派生物
│       ├── validate.py  —         ← r12: 策略同步 ★S 已内置（r11 起），登记轮次同步
│       └── versions.py  —         ← 代码文件：不写文件内版本行（用 git blame）
├── tests/
│   ├── README.md  v1.5      ← 测试说明（自举计数：合计 333，含 test_structure 8）
│   ├── test_ai_readability.py  —         ← P1/P2/B/H/I 测试
│   ├── test_claim_type.py  —         ← ★ 结论证据类型测试（五类约束真的会拦 / schema 与 Pyth…
│   ├── test_consumes_completeness.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│   ├── test_core.py  —         ← 代码文件：不写文件内版本行（用 git blame）
│   ├── test_cross_scope.py  —         ← ★ 跨注层测试（scope 三分 / 跨注判定 / 结构性拒收）；无需…
│   ├── test_evidence_anchor.py  —         ← ★ 证据锚定测试（漂移真能检出 / 该敏感的要敏感、该迟钝的要迟钝 /…
│   ├── test_flywheel.py  —         ← K/D1/D2/C/F 测试（无需 pytest）
│   ├── test_meta_variables.py  —         ← schema 1.3 元数据（convenience/experien…
│   ├── test_open_questions_consistency.py  —         ← Q 状态一致性回归：解析归一化/头部计数滞后/标题缺✅/优先级表act…
│   ├── test_research_lib.py  —         ← research_lib 原语测试（已知分布验证可复现/正确性/样本不…
│   ├── test_shadow_game.py  v1.0
│   └── test_structure.py  —         ← 结构完整性回归测试（P1-2 三道防线）
└── tools/
    ├── build_versions.py  —         ← 代码文件：不写文件内版本行（用 git blame）；r13 T-04…
    ├── count_tests.py  —         ← 登记测试文件 + --inject（T-045：tests/READM…
    ├── finish_round.py  —         ← 收尾自动化（C1）：rehash→count_tests--injec…
    ├── inject_version_lines.py  —         ← 代码文件：不写文件内版本行（用 git blame）
    ├── register_r06_upgrade.py  —         ← r06 批量实施登记脚本（一次性，登记含自身）
    ├── render_ai_map.py  —         ← r11：读取改 utf-8-sig（修 BOM 叠加 bug）
    ├── render_dependency_map.py  —         ← r11：读取改 utf-8-sig（修 BOM 叠加 bug）
    ├── render_flywheel_health.py  —         ← r11：读取改 utf-8-sig（修 BOM 叠加 bug）
    ├── render_readme_tree.py  —         ← r11：读取改 utf-8-sig（修 BOM 叠加 bug）
    ├── render_task_brief.py  —         ← 任务书生成器（B+G/X）：--top N 控制必做数；resourc…
    ├── render_version_index.py  —         ← 代码文件：不写文件内版本行（用 git blame）
    └── report_calibration.py  —         ← 置信度校准报告（D1）
```

> **目录树为派生物**：由 `tools/render_readme_tree.py` 从 versions.json 生成；新增文件登记 versions.json 后运行 `--write` 同步，勿手改。

> **版本号标注规则**：`vX.Y` = 该文件当前 `content_version`；`—` = 该文件不单独版本化
> （B 级 `.py` 只登记索引）。例外：`pyproject.toml` 的 `v0.1.0` 标的是 **SPC 整体 release 版本**（`project_version`），不是 `content_version`。完整清单见 [`VERSION_INDEX.md`](VERSION_INDEX.md)。
>
> **文件名本身不带版本号** —— 版本号在**文件头部版本行**与**本索引**里维护。
> 原因：改名会让所有指向它的链接失效、`git log` 追不到历史。详见
> [`docs/VERSIONING_DOCS.md`](docs/VERSIONING_DOCS.md) §2。
>
> **⚠ `tools/build_versions.py --write` 已禁用（T-044，r13）**：该生成器内嵌版本表停留在 r03，
> 运行会**回退** versions.json。权威维护流程 = **手工登记 + `render_readme_tree /
> render_version_index / render_ai_map / render_dependency_map / render_flywheel_health --write` +
> `inject_version_lines.py --write`**，勿跑 build_versions --write。

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
| **框架核心** | ✅ **`framework/core/` 7 模块 / 21 单注原语 + 7 跨注原语**（Ticket / Portfolio / 求值 / 受限 DSL 判定 / 作用域三路切分 / 生成器） |
| 记忆层 | ✅ **47 条结论**（每条带 `claim_type` 证据类型 + `source_sha256` 证据锚定 + **v2.0** `confidence_grade`/`change_type`/重校准周期 + **r08 起 `noop_count`**）/ L1–L15 / 15 开放问题（**2 open**，r11 清偿 Q-011/Q-015，r12 清偿 Q-008）/ 6 假设（H-001 部分支持，2 已推翻）/ 待办（P0 已清空，P1/P2 见 TODO） |
| 库与 CLI | ✅ 9 模块 + 14 命令，`validate --all` **98 项全绿**（含 v2.0：INV2 引用链 / INV3 取代链环检测 / 动态锚点重校准 / 策略-证据一致性 / 速览计数 / **r10 概率口径检查项**，r11 覆盖 .jsonl 事实库 + **★S 策略文档随轮同步**） |
| 彩种 `dlt` | ✅ `game.yaml`（config **2.1**，11 单注 + **5 跨注**特征全原语化）+ `strategy.json`（schema **1.4**，**3 规则** + 9 条 avoid_list，规则含有效性三档 `effectiveness_grade`）+ [**策略说明书（人话版）**](games/dlt/strategy/STRATEGY_GUIDE.md) + **r07**（前段取证/外部核对/节假日验证）+ **r08 体系升级**（C+X+Y+Z：任务书参数化/研究资本化/收尾自动化/并行研究池）+ **r09 策略量化轮**（R-002 `magnitude_pct`=65.49 量化、F-0037/F-0038 新增、P0 四锚点重校准维持）+ **r10 口径根治轮**（F-0039 全奖级概率表 / F-0040 销量外生 / F-0041 形态撞号、概率口径检查项落地）+ **r11 效应与代理轮**（F-0042 效应平台期 / F-0043 机选代理可观测、T-048 hold-out 评测设计）+ **r12 L3 hold-out 落地轮**（T-049 时序评测验收通过 F-0044、T-030 策略有效性三档 schema 1.4、Q-008 answered、F-0004/F-0005 锚点重校准） |
| `tests/` | ✅ 12 文件 **463/463 全绿**（core 117 / cross_scope 64 / claim_type 42 / evidence_anchor 31 / shadow_game 69 / structure 8 / flywheel 17 / ai_readability 30 / consumes_completeness 6 / meta_variables 44 / open_questions_consistency 12 / research_lib 18；无需 pytest） |
| 版本体系 | ✅ A/B/C/D 四级分区，**252 条**登记（A=125 B=82 C=16 D=29），版本行全部一致 |

### r04 归因要点（口径已复核）

| 项 | 结果 |
|---|---|
| **前段数据能不能用？** | **不能当基线**：2013-08 之前那段在「号码分布—中出注数—销售额」三者间不自洽（`F-0019`） |
| **"衰减过半"对不对？** | **口径依赖**：均值比口径 0.59/0.50；稳健口径（中位数/截尾/剔极端期）只有 **0.65~0.83**（`F-0020`） |
| **衰减的成因** | 与 F-0006 的 2013-08 号码结构变点**同期**；**销量稀释已排除**（NB2 交互 IRR 0.596）（`F-0021`） |
| **F-0004 该按哪个口径？** | **后段 1.2472**：未计封顶上界 **109.4%**、含封顶实测锚点 **40.6%**（`F-0022`） |
| **高奖池期该不该加注？** | **不存在稳健高期望期** → 不新增规则，反而新增 `A-009` 驳回择时（`F-0023` / `F-0024`） |
| **后区能不能用？** | 撞号结构**存在但不可靠可利用**（交叉验证 uplift 1~3%、CI 含 0）；F-0011 的口径混淆已修正（`F-0025`） |

### r03 复核要点（历史留档）

| 项 | 结果 |
|---|---|
| **封顶是否触发过？** | **从未**（E6 102 期一等奖总额最大 0.9788 亿）→ `F-0015` 被推翻，新增 `F-0016` |
| **计入封顶后的收益** | 未计封顶上界 **121%** → 实测锚点净值 **41.4%**（`F-0017`）；r04 按后段口径重算为 **109.4% / 40.6%**（`F-0022`） |
| **撞号效应稳健性** | 仍成立；"幅度衰减过半"经 r04 复核为**口径依赖**（`F-0020`） |
| **L5 技术债** | **已清偿**：中位数比 1.5 + 截尾检验仅变化 1.72%（`F-0018`） |

### 已知未闭合

| 项 | 说明 |
|---|---|
| `R-002` 跨注规则 | ✅ **执行层已闭合**（2.1）：已声明 `scope: cross` 特征 `has_duplicated_structure`，`judge_cross()` 可真正判定。✅ **r09 已量化**：`magnitude_pct` = **65.49%** [64.86, 66.16]（K=10 修复增益，后段口径，`F-0037`） |
| `spread_penalty` | 启发式，**未量化**（不是统计结论）。有跨注特征时应优先用跨注特征 |
| L3 组合**优化** | **未实现**。跨注层只补齐了"执行"，"在候选集上求解最优组合"仍未做 |
| 奖金封顶 | ✅ **已闭合**（r03 T-003 + r04 F-0022）：封顶已纳入模拟，口径改为后段 109.4% / 含封顶 40.6% |
| 前段数据可信度 | ⚠️ `F-0019`：2013-08 之前那段**不自洽**，含前段的全样本数字只是"历史口径"（`Q-013`/`Q-014`，r05 首推） |
| Q-009 | 组合分散度研究**未获用户批准**，保持不动 |

## 免责声明

本仓库**不提供中奖保证**，不改变中奖概率（各奖级恒定），不构成投注建议。
所有分析结论均附带减损项（`caveats`）与置信度分级，引用前请阅读。
**理性购彩，量力而行。**
