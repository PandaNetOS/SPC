# r06 附加研究 —— SPC AI 可读性升级空间（方案稿）

> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 0. 结论

SPC 的 AI 可读性底子扎实（单一入口 AI_CONTEXT、机器可读 versions.json / FACTS、
派生物目录树），但对照 2024–2026 学术研究与业界标准，有三个明确缺口：

| # | 缺口 | 现状（实测） | 依据 |
|---|---|---|---|
| 1 | 无 AGENTS.md 标准入口 | SPC 根目录无 AGENTS.md；AI_CONTEXT.md 468 行 | Context Engineering for AI Agents in OSS（466 项目实证）；Anthropic"过长上下文被忽略一半" |
| 2 | 入口文档仍是手写维护 | 目录树已生成式，但 AI_CONTEXT 的目录地图/结论速览仍手写 | llms.txt v2；Spatial Context Theory（文档=生成输出）；FastCode scouting-first |
| 3 | AI 可读性不可测 | validate 69 项全查结构一致性，无一项查"入口能否答对关键问题" | DocAgent 三维评估；SACL 文档偏置；Wright 禁止自欺 |

## 1. 学术与业界依据（可溯源）

### 1.1 业界标准

- **llms.txt**（Jeremy Howard / Answer.AI，2024-09；2026-08 v2）：根目录单
  Markdown 机器地图（H1 + blockquote 摘要 + H2 分区链接列表）。设计要点：
  用 Markdown 而非 JSON，因为**消费者是 LLM**；llms-full.txt 提供全文伴侣。
  https://llmstxt.org/
- **AGENTS.md**：开放标准，由 Linux Foundation Agentic AI Foundation 治理；
  六域（命令/测试/结构/风格/git/边界）；建议 ≤150 行、分层（monorepo）。
  https://ai-tldr.dev/learn/ai-coding-tools/coding-agents-assistants/agents-md-claude-md/
- **CLAUDE.md（Anthropic）**：每次会话自动拉入上下文；**"过长则被忽略一半"**
  —— 必须激进删减。
  https://code.claude.com/docs/en/best-practices

### 1.2 学术

| 论文 | 结论 | 对本仓库的含义 |
|---|---|---|
| Context Engineering for AI Agents in OSS（Mohsenimofidi et al. 2026） | 466 个开源项目实证：AGENTS.md 内容结构尚无共识，呈现方式（描述/规定/禁止/解释/条件）差异大；上下文文件质量直接影响生成质量 | 仓库应主动提供**结构化**上下文文件，抢占"给 AI 的第一印象" |
| SACL（EMNLP 2025 Findings，CMU） | 代码检索器**强依赖表面文本特征**（docstring、标识符名），对"文档化良好的代码"有偏置，即使文档与功能无关 | 入口文档质量直接决定 AI 能否定位正确实现 |
| FastCode（arXiv 2603.01012） | scouting-first：用轻量**结构-语义地图**导航仓库，避免全文摄取；同等精度下显著省 token | 生成式目录树/地图降低 AI 导航成本 |
| REPOGRAPH（ICLR 2025） | 仓库级代码图插件，四方法接入后 SWE-bench 全部提升 | 结构导航层是 AI 理解仓库的通用增益点 |
| SWE-QA（arXiv 2509.14635） | 仓库级 QA 基准：意图理解/跨文件推理/多跳依赖是瓶颈 | 需要**跨文件关系视图**（P3 依赖图） |
| DocAgent（ACL 2025 demo，Apple/Meta/Google） | 文档质量按 Completeness / Helpfulness / Truthfulness 三维可测 | 入口完整性可以**机械校验**（P2） |
| ML-Bench（OpenReview） | GPT-4 凭 README 完成开源库任务仅 39.73% | 单 README 不够，需多级入口 |
| Onboarding Information Overload（Adejumo & Johnson） | 信息过载是 onboarding 主障碍 | 入口必须分层渐进披露，控制单文件长度 |
| Wright 禁止自欺（arXiv 2506.17331） | 系统不得断言内部自相矛盾 | 入口与实现脱节 = 自欺，应被 validate 拦截 |

## 2. 升级机制（P0 / P1 / P2）

### P0 — AGENTS.md 极简入口（新增根文件）

- 六域：常用命令 / 测试方式 / 目录结构一句话 / 边界（红线） / 版本纪律 / git 流程
- ≤120 行；开头一行指向 AI_CONTEXT.md（深度入口）
- 给**任何** AI 工具标准入口；登记 versions.json（A 级 doc）
- 依据：Context Engineering（格式影响生成质量）+ Anthropic 减删原则 + AGENTS.md 标准

### P1 — AI_MAP.md 生成式机器地图（llms.txt 式）

- `tools/render_ai_map.py`：从 versions.json 派生 AI_MAP.md
  （H1 + 摘要 + 分区链接：契约/框架/记忆/彩种/工具/测试/版本，每区带一行说明）
- `--write` 写回；validate 校验 AI_MAP 为派生物（复用 P1-2 目录树机制）
- 与 AI_CONTEXT 分工：AI_CONTEXT = 人/AI 深度入口；AI_MAP = 机器快速地图
- 依据：llms.txt + Spatial Context Theory（生成输出非维护输入）+ FastCode

### P2 — validate 新增「AI 入口完整性」检查

- 维护 N 个关键问题锚（Q&A 对，如"唯一可优化量是？→ expected_bonus_given_win 在 AI_CONTEXT §1"）
- validate 检查：入口文档包含答案锚 + 答案锚指向的实现存在
- 防"入口与实现脱节"（如改了 game.yaml 却忘了 AI_CONTEXT 的数字）
- 依据：DocAgent 三维评估（机械子集）+ Wright 禁止自欺 + 本仓 validate 传统

### P3 — DEPENDENCY_MAP.md（后续轮）

- 跨文件引用关系自动生成：strategy evidence_refs → FACTS；game.yaml 特征 → features.py 原语；
  schema → 数据文件；versions.json → 文件
- 依据：REPOGRAPH + SWE-QA（跨文件/多跳依赖）

## 3. 实施与验证（批准后）

1. P0：写 AGENTS.md → 登记 → render tree + vindex → validate
2. P1：写 render_ai_map.py + AI_MAP 模板 → validate 加派生物检查 → 测试
3. P2：validate 加 AI 入口完整性检查（Q&A 锚表）→ 测试
4. 全量：validate 69+ → count_tests → 合规 → 提交（等批准）
