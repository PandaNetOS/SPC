# SPC 迭代飞轮全局升级计划（整体链路）

> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 状态：**已实施**（active）｜ 批次 r06 收尾 A / r07 B/G/H/I/K/D1 / r08 C / 远期 D2/F 全部落地（D2 矛盾增强与 F 增量校验按设计并入本批）。

## 0. 飞轮是什么（现状闭环）

```
[入口认知] AI_CONTEXT 读取（10 分钟）
    ↓
[任务生成] TASK_BRIEF 从 workbench TODO/OPEN_QUESTIONS 挑 P0
    ↓
[研究执行] 分析 + 可复现脚本（LESSONS 纪律）
    ↓
[结论入库] 三闸门（filter/judge/manager）→ FACTS.jsonl
    ↓
[证据锚定] source_sha256 + rehash + recalibrate_every
    ↓
[一致性校验] validate 69 项（契约/红线/结构/版本）
    ↓
[收轮四件套] FINDINGS / HANDOFF / manifest / journal + 下轮 TASK_BRIEF
    ↓
[记忆演化] caveats → OPEN_QUESTIONS → TODO（机械传导）
    ↓
[记忆压缩] 每 5 轮 compress_memory
    ↓
[发布门] 合规 26 项 → 用户确认 → 直连推送（仅 main）
    ↓
（下一轮 AI 读新 TASK_BRIEF + 新记忆，飞轮转一圈）
```

## 1. 各环节升级链路总表

| 环节 | 现状（已实测） | 缺口 | 升级动作 | 依据 | 批次 |
|---|---|---|---|---|---|
| A 入口认知 | AI_CONTEXT 468 行；无 AGENTS.md；目录树已生成式 | 无标准入口 / 过长 / 入口手写 / 不可测 | **P0** AGENTS.md 极简入口；**P1** AI_MAP.md 生成式地图；**P2** validate「AI 入口完整性」 | Context Engineering 2026；llms.txt；Anthropic；DocAgent；SACL；FastCode | **r06 收尾** |
| B 任务生成 | TASK_BRIEF 由 AI 手选 TODO 条目 | 问题选择无客观排序（"AI 恰好想到"） | **TASK_BRIEF 生成器**（render_task_brief.py：TODO 按价值评分 → 候选 TOP3 → 生成任务书；validate 检查任务书必须引用 TODO 且带验收判据） | DOLPHIN（idea→反馈闭环）；IterResearch；主动学习不确定性采样 | r07 |
| C 研究执行 | 脚本可复现；关键数字散落多文件 | 跨文件依赖无图；数字无单一事实源 | **DEPENDENCY_MAP.md**（evidence_refs→FACTS；game.yaml 特征→原语；schema→数据）；**关键数字一致性检查**（validate 对比 p1/T 等跨文件数字） | REPOGRAPH；SWE-QA；tests/README「数字重算一致」暂缓项 | r08 |
| D 结论入库 | 三闸门 v2.0（关键词互斥 + 结构约束） | 置信度 1-5 星无校准；矛盾检测仅关键词 | **D1 置信度校准**（每 N 轮统计推翻率按置信度分层 → 校准报告，系统性失配 validate 警告）；**D2 语义矛盾检测**（相似结论自动提示核验） | confidence calibration；AIDE²（reward hacking 55%→32% 可测）；contradiction detection | D1 r07；D2 远期 |
| E 证据锚定 | sha256 + rehash + recalibrate ✓ | — | **已闭环**，不再升级 | — | — |
| F 一致性校验 | validate 69 项全量 | 规模增长后全量校验慢 | **增量校验**（validate --incremental 受编辑邻域，IncrConsist 1660×）；本轮附带 P2 入口完整性 | IncrConsist | 远期 |
| G 记忆演化 | caveats→问题传导 ✓ | TODO 条目无价值字段 | **TODO 加 value 字段**（影响面/置信度缺口/可证伪性）→ 供 B 评分 | IterResearch；AIDE² | r07 |
| H 收轮四件套 | SOP 要求四件套 | HANDOFF 自由文本，下轮 AI 重新解析 | **HANDOFF 模板化**（结论变更/未决/风险/下轮建议四段 + validate 检查非空） | Anthropic Effective Harnesses（clear artifacts for next session）；DOLPHIN | r07 |
| I 记忆压缩 | 每 5 轮手动纪律 | 到期不压缩 validate 不拦 | **压缩到期提醒**（距上次 >5 轮 → validate warning） | 战略遗忘（IterResearch/MEM1）；SAGE Ebbinghaus | r07 |
| J 发布门 | 合规 26 + 确认门 + 直连推送 ✓ | — | **已闭环**，不再升级 | — | — |
| K 飞轮健康度 | "正向升级"靠人工论证 | 无机械指标 | **飞轮仪表盘**（每轮 journal 自动统计：新增/推翻结论、问题转化率、校验通过率、框架改进采纳 → FLYWHEEL_HEALTH.md 派生物） | AIDE²（连续改进可测）；IterResearch 自我评估；Self-Rewarding（自评信号） | r07 |

## 2. 关键学术锚（本轮新增）

| 论文 | 结论 | 锚定环节 |
|---|---|---|
| Recursive self-improvement of AI research agents（AIDE²，arXiv 2609.26457） | AI 研究 agent 提出改动→基准→保留最优，8 天 7 个连续改进；reward hacking 55%→32%（未优化的属性也被改善） | K 飞轮健康度、D1 校准 |
| DOLPHIN（arXiv 2501.03916，复旦/上海AI实验室） | 闭环开放式自动研究：idea 生成→实验→结果反馈→更高质量 idea | B 任务生成、H 收轮 |
| Gödel Agent（arXiv 2410.04444） | 自引用框架递归自我改进，无需预定义例程 | 全局（远期：框架自改） |
| METAREFLECTION（Microsoft，EMNLP 2024） | 用过去试错增强语义记忆，agent 提升 4%~16.8% | G 记忆演化 |
| Self-Rewarding LM（Meta，arXiv 2401.10020） | 模型自评奖励，双向提升 | K 自评信号 |
| Mirror / REFINER（ACL 2024） | 多视角自反思避免困于单一反思回路 | D2 矛盾检测（远期） |

## 3. 分批执行计划

### r06 收尾（本批，待批准）
A：P0 AGENTS.md（六域 ≤120 行）+ P1 render_ai_map.py（AI_MAP 派生物 + validate 检查）+ P2 AI 入口完整性校验（Q&A 锚表）
→ 测试 + validate 69+ + 合规 + 提交

### r07（下一轮）
B 任务书生成器（render_task_brief.py + validate 引用检查）→ G TODO value 字段 → H HANDOFF 模板化 → I 压缩到期提醒 → K 飞轮仪表盘（FLYWHEEL_HEALTH.md 派生物）→ D1 置信度校准初版
→ 每项：写代码 + 登记 + 测试 + 合规 + 提交（逐项确认门）

### r08
C DEPENDENCY_MAP.md 生成器 + 关键数字单一事实源检查
→ 同上流程

### 远期
D2 语义矛盾检测（embedding）→ F 增量校验（validate --incremental）→ 框架自改（Gödel Agent 式，需谨慎评估）

## 4. 依赖关系

- P1/P2 复用 P1-2 目录树机制（派生物 + validate 对照）——已有框架直接扩展
- B 依赖 G（TODO 先有价值字段才能评分）
- K 依赖 journal 结构化（已有 round 日志格式）
- C 依赖 versions.json 引用关系（已有 evidence_refs / provenance）
- 每批独立可交付，可随时中止（用户确认门逐项生效）

## 5. 判定成功（怎么知道升级有用）

- P2：故意改错 AI_CONTEXT 一个数字 → validate 必须红（防回归测试）
- B：任务书必须引用 TODO 条目且带验收判据 → 无引用 validate 红
- K：飞轮仪表盘连续 3 轮指标不退化（结论存活率、问题转化率、校验通过率）
- D1：置信度 5★ 结论的存活率应 > 3★；违反 → 校准警告
