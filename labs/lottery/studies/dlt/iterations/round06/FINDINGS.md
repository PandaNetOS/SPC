# FINDINGS.md — round06 · 策略落地 + 迭代飞轮全局升级（元层轮）

> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

| 项 | 内容 |
|---|---|
| **轮次** | `round06` |
| **彩种** | `dlt` |
| **数据版本** | `dlt_full_2933`（2933 期，07001 ~ 26115） |
| **基准规则 epoch** | `E6`（现行） |
| **日期** | 2026-10-11 |
| **执行者** | AI（MainAgent 直接执行；用户逐轮明确批准：T-210 三项策略落地 → AI 可读性升级 → 飞轮升级「一次性全部实施」） |
| **性质** | **元层轮**：策略规则落地（用户批准三项）+ 框架/流程自我升级（AI 可读性 + 迭代飞轮），无新数据结论（FACTS 维持 32 条） |

---

## 0. 摘要

| 任务 | 对应问题 | 结果 |
|---|---|---|
| T-210 策略落地（三项批准变更） | r05 遗留的 R-002 处置 | R-001/R-002/R-003 语义与 evidence_refs 更新，策略 1.1 生效 |
| AI 可读性升级（P0–P3） | 「AI 可读性友好方面有没有升级空间，结合学术研究」 | P0 AGENTS.md / P1 AI_MAP 派生物 / P2 入口完整性校验 / P3 依赖图，全部落地 |
| 迭代飞轮全局升级（A–K） | 「从全局迭代飞轮视角列出各环节需升级的链路」 | 11 环节盘点 → 批次规划 → 一次性实施 12 项机制 |
| 机制验证（自举/铁律/派生物） | 新机制真的会拦吗 | 铁律拦硬编码彩种名、结构完整性拦漏登记、派生物一致拦手改 |

## 1. 策略落地（T-210，用户批准三项）

| 规则 | 落地内容 | 依据 |
|---|---|---|
| R-001 | 避开相邻号对 ≥2 的形态（未变，evidence 链确认） | F-0003/F-0004/F-0017/F-0019 |
| R-002 | 语义重构为「禁止完全相同号码」；结构同构不在此列（F-0028 not_established） | F-0027/F-0028 |
| R-003 | 新增「避开生日号区」（max ≥ 32），与 R-001 叠加 +136.2%（未计封顶） | F-0029 |

> 策略 `schema_version 1.1`；`rules[]` 均已带 `scope`；R-002 为 `cross` 层（跨注原语 `has_identical_tickets`）。

## 2. AI 可读性升级（P0–P3）

学术锚（详见 `research/ai_readability_proposal.md`）：llms.txt（Answer.AI）、AGENTS.md（Linux Foundation）、
Anthropic CLAUDE.md best practices、Context Engineering for AI Agents in OSS、SACL（EMNLP 2025）、
FastCode、REPOGRAPH（ICLR 2025）、SWE-QA、DocAgent（ACL 2025）、ML-Bench。

| 机制 | 产物 | 校验 |
|---|---|---|
| P0 AGENTS.md 极简入口 | `AGENTS.md`（六域 ≤120 行） | 结构完整性登记 |
| P1 机器地图（生成式） | `AI_MAP.md` + `src/spc/ai_map.py` + `tools/render_ai_map.py` | validate 派生物逐字比对 |
| P2 入口完整性 | AI_CONTEXT 关键锚（8 静态 + 动态对照 strategy/game.yaml） | validate `_check_ai_entry_completeness` |
| P3 依赖图 | `DEPENDENCY_MAP.md` + `src/spc/depmap.py` | validate 派生物一致 |

## 3. 迭代飞轮全局升级（一次性实施）

学术锚（详见 `research/flywheel_upgrade_plan.md`）：AIDE²（递归自改可测）、DOLPHIN、Gödel Agent、
METAREFLECTION、Self-Rewarding、Mirror/REFINER、Wright 禁止自欺。

| 环节 | 升级 | 产物 |
|---|---|---|
| A 入口认知 | AGENTS.md 六域 | `AGENTS.md` |
| B 任务生成 | TODO 价值评分 → TOP3 任务书 | `tools/render_task_brief.py` |
| G TODO 价值 | value 字段 + P 级基分 + ★首推加权 | 同上 |
| H 交接模板 | 收尾轮 HANDOFF 结构化校验（缺段报错） | validate `_check_handoff_structure` |
| I 记忆压缩 | 距上次压缩 >5 轮 warning | validate `_check_compression_freshness` |
| K 飞轮仪表盘 | `FLYWHEEL_HEALTH.md` 派生物（存活率/产出/置信度分层） | `src/spc/flywheel.py` |
| D1 置信度校准 | ★分层存活率失配警告 + 报告 | `tools/report_calibration.py` |
| C 依赖图 | strategy→FACTS→证据 跨文件依赖图 | `DEPENDENCY_MAP.md` |
| C2 关键数字 | F-0001 解析数字跨文件一致 | validate `_check_critical_numbers` |
| D2 矛盾增强 | 方向对 + 主题词典 + 范畴红线三维（不引 embedding） | `platform/tools/ingate.py` |
| F 增量校验 | `validate --incremental` 最快路径 | `cli/main.py` |

## 4. 机制验证（新机制真的会拦）

| 事件 | 机制 | 结果 |
|---|---|---|
| 库代码硬编码 `dlt` 路径 | 影子彩种铁律（AST 剥 docstring 扫描） | 拦截 → 参数化为动态发现彩种目录 → shadow 69 恢复全绿 |
| 派生物缺版本行 | A 级文档版本行校验 | 拦截 → render 函数内置版本行 |
| 重定向文件滞留仓库根 | 结构完整性双向登记 | 拦截 → 删除（教训：临时文件禁止落仓库根） |
| 新文件漏登记 | 结构完整性双向登记 | 拦截（登记脚本自身也被拦）→ 15 文件全部登记 |

## 5. 结论

本轮为元层升级轮：**FACTS 无新增/无推翻（32 条维持）**；策略 1.1 生效；
validate 69 → **77 项**（+8 新检查）；测试 333 → **378 项**（+45）；合规 26 项 PASS；
提交 `9802e0f`（feat(r06) 一次性实施）已推送。
