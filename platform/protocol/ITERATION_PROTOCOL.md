# ITERATION_PROTOCOL.md — 迭代协议

> **版本**：`1.2` ｜ 轮次 `r12` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **本文件定义"一轮研究"的完整生命周期。**
> 任何 AI 或人在本仓库里做分析，都必须按本协议执行。
>
> 协议的**目的不是限制**，而是让每轮工作**可被下一轮接续**。
> 一轮研究若没按协议留痕，它产出的结论就只是"一份文档"，
> 不是这个系统的一部分。

---

## 0. 一轮的定义

**一轮 = 一个 `games/<game>/iterations/roundNN/` 目录的完整生命周期。**

一轮可以做的事：

| 类型 | 例 | 是否可接受 |
|---|---|---|
| 新的分析证据 | 检验一个新假设 | ✅ |
| 复核已有结论 | 补做分期稳健性 | ✅ |
| 整理/重构（无新证据） | 如 `round02`（v4 素材结构化入库） | ✅ 但必须标明 `性质：整理入库轮` |
| 只写文档不跑数据 | | ⚠️ 需在 HANDOFF 说明为何 |
| 修改框架本身 | 改 schema / 协议 | ✅ 属 P4，**必须单独记录评审** |

---

## 1. 四件套（强制）

每轮**必须**产出四个文件，缺一不可：

| 文件 | 何时写 | 给谁看 | 核心内容 |
|---|---|---|---|
| `TASK_BRIEF.md` | **开轮前** | 本轮执行者 | 要做什么、验收判据、陷阱提醒 |
| `FINDINGS.md` | **做分析时** | 本轮执行者自己 + 评审 | 每条结论的证据、数字、CI |
| `HANDOFF.md` | **收轮时** | 下一轮执行者 | 遗留什么、下轮从哪开始 |
| `manifest.json` | **收轮时** | 机器 | 结构化索引（受 `spec/iteration.schema.json` 约束） |

**为什么是四件而不是一件**：它们的**读者不同**。
`TASK_BRIEF` 写给"还没开始的我"，`HANDOFF` 写给"下一轮的别人"，
`FINDINGS` 写给"要复核证据的人"，`manifest` 写给"程序"。
合成一份，就必然有一方拿不到需要的信息。

---

## 2. 开轮：写 TASK_BRIEF.md

模板见 `templates/TASK_BRIEF.template.md`。必含：

### 2.1 必填项

| 项 | 要求 |
|---|---|
| **目标** | 一句可判断"做到没有"的话。禁止"深入研究 X" |
| **验收判据** | **客观标准** —— 满足什么条件算完成 |
| **输入** | 数据版本、引用的既有结论 id、上轮 HANDOFF |
| **方法** | 具体做什么，含脚本路径 |
| **陷阱提醒** | 本轮易犯的 LESSONS 条目（**逐条点名 L<sub>id</sub>**） |
| **预期产出** | 文件路径 + 结论 id 范围 |

### 2.2 反锚定纪律

若本轮是**独立复核**，`TASK_BRIEF` **不得给出期望的结论**，
只给数据事实、方法、陷阱。这是继承自 v4 任务书的设计（"反锚定"）。

原因：若任务书写"预期发现 X 显著"，执行者（尤其是 AI）会不自觉地
朝这个方向找证据。**任务书应当中立。**

### 2.3 从哪来

`TASK_BRIEF` 的内容**必须来自**：

1. 上一轮的 `HANDOFF.md`（首选）
2. `labs/lottery/studies/dlt/memory/workbench/TODO.md` 的 P0/P1 项
3. `labs/lottery/studies/dlt/memory/workbench/OPEN_QUESTIONS.md` 的高优先级问题
4. `FACTS.jsonl` 某条的 `caveats`

**禁止**凭空提出与本仓库记忆无关的任务。

---

## 3. 做分析：写 FINDINGS.md

### 3.1 每条结论的格式

按 `spec/fact.schema.json` 的字段思考，但用 markdown 表叙述：

```markdown
### 发现 N：〈一句话结论〉

| 项 | 内容 |
|---|---|
| **结论 id** | F-00xx（或"暂不分配，待复核"） |
| **方法** | 精确枚举 / 置换检验 / 观测+Bootstrap / 条件模拟 ... |
| **数字** | 效应量 + 95%CI + p 值 + n |
| **脚本** | `scripts/xxx.py`（必须能独立跑出上面的数字） |
| **减损项** | ★ 必填，非空 |
| **状态建议** | established / tentative / refuted |
| **置信度建议** | 1–5 及理由 |
```

### 3.2 三条硬要求

1. **可复现**：每个数字对应一个能独立运行的脚本。
   跑不出来的数字**不得标 `established`**。
2. **`caveats` 非空**：没有减损项的结论，要么是数学定理（写明"解析可证，无减损"），
   要么是没想清楚边界。
3. **区分「解析/枚举/观测/模拟」**：
   这四类证据的强度差异巨大（见 `L8`）。
   **`F-0001`（解析）和 `F-0004`（模拟）绝不可同等对待。**

### 3.3 主动证伪义务

`FINDINGS.md` **必须有一节**说明：

- 本轮**推翻或修正**了哪些既有结论（引用 id）
- 本轮**试图验证但失败**的假设（这也算产出）
- 本轮**未能验证**的假设（转入 workbench）

> "什么都没发现"是一个合法且重要的结果。
> 但必须**具体地**说清"试了什么、为什么没成"，而非空泛地说"无显著结果"。

---

## 4. 收轮：写 HANDOFF.md + manifest.json

模板见 `templates/HANDOFF.template.md`。

### 4.1 HANDOFF.md 必含

| 节 | 内容 |
|---|---|
| **本轮结论清单** | 新增/更新的 `F-xxxx` |
| **遗留问题** | 按优先级列出，每条附 `Q-xxxx` 与建议脚本路径 |
| **下轮建议** | 明确推荐先攻哪 2–3 项，**并说明理由** |
| **框架改进建议** | 对研究框架本身的改进（自我迭代的元层面产出） |
| **本轮踩的坑** | 新的方法论教训 → 应追加到 `LESSONS.md` |
| **给下轮执行者的提醒** | 最容易被误用的结论、最不该信的推断 |

### 4.2 manifest.json

受 `spec/iteration.schema.json` 约束。关键字段：

- `inputs.upstream_fact_ids` —— 本轮消费了哪些既有结论
- `outputs.new_fact_ids` / `superseded_fact_ids` / `refuted_fact_ids`
- `open_questions` —— 遗留问题 id
- `framework_revision` —— 对框架的改进提案

### 4.3 必须自动生成下一轮 TASK_BRIEF

**这是本协议最重要的一条：**

> 收轮时，`HANDOFF.md` 的「遗留问题」+「下轮建议」
> **必须转写为下一轮的 `TASK_BRIEF.md`**。
>
> 不做这一步，迭代链就断了 —— 下一轮会从零开始问"我们该做什么"。

可以只写占位（目标 + 验收判据 + 陷阱提醒），细节由下轮执行者补。
但**不能留空**。

---

## 5. 记忆更新（与上一步并行）

| 产出 | 更新到 |
|---|---|
| 新结论 | **追加** `labs/lottery/studies/dlt/memory/facts/FACTS.jsonl` → 重生成 `INDEX.md` |
| 被取代的结论 | 改 `status` + 填**双向** `supersedes`/`superseded_by` |
| 新教训 | **追加** `labs/lottery/studies/dlt/memory/lessons/LESSONS.md`（含**检测方法**） |
| 新问题 | 更新 `workbench/OPEN_QUESTIONS.md` |
| 假设变化 | 更新 `workbench/HYPOTHESES.md` |
| 待办清算 | 更新 `workbench/TODO.md`（完成的移到「已完成」节） |
| 本轮过程 | 新写 `labs/lottery/studies/dlt/memory/journal/roundNN.md` |
| **★ 下游同步** | **结论被 superseded 时**，检查所有 `consumes` 引用它的下游文档（`versions.json` 的 `consumes` 字段），同步内容 + 升 `content_version` |

### ★ 下游同步（r03 血的教训）

**根因**：r03 推翻了 `F-0015`（「1 亿封顶已触发」），但给普通用户看的
`STRATEGY_GUIDE.md` 仍在传播这个错误结论 —— 而当时**测试全绿、校验全绿**，
因为旧校验只看版本号自洽，看不见"内容没跟上"。

**协议要求**（每轮收轮时执行）：

1. 列出本轮 `status` 从 `established` 变为 `superseded` 的结论
2. 查 `versions.json` 里哪些条目的 `consumes` 引用了它们
3. 对每一个：**要么同步内容并升版本，要么在文档内加显式存疑标记**
4. 跑 `validate` 确认 warning 只剩"已确认的沿革式引用"

**判据不是"有没有 warning"，而是"每个 warning 都有解释"。**

### 关键传导（本仓库的自我迭代机制）

```
每条新结论的 caveats
    ↓ 逐条
转化为 OPEN_QUESTIONS 条目
    ↓
进入 TODO.md 并分配优先级
    ↓
下一轮 TASK_BRIEF 从中选题
```

**这一步不能省。** 省掉它，`caveats` 就变成装饰；
留下它，系统就有了**自我驱动的下一轮任务**。

---

## 6. 校验（收轮前必做）

```bash
python cli/main.py validate --all
```

校验内容：

- 全部 JSON 合规于对应 schema
- `FACTS.jsonl` 的红线字段恒为期望值
- `evidence_refs` 的外键在 `FACTS.jsonl` 中存在
- `source` / `evidence.script` 指向**真实存在**的文件
- `supersedes` ↔ `superseded_by` **双向一致**
- `manifest.json` 的 id 引用存在

r11/r12 新增的机械护栏（validate --all 已内置，勿手写白名单）：

- 概率口径扫描**自动派生**：versions.json 全部 active .md/.py/.json/.jsonl 均在检查范围
  （FACTS.jsonl 按**逐条 JSON 的 claim 字段**检查，避免跨字段误报；L15）
- ★S 策略文档随轮同步：最近 `strategy_updated=true` 的收尾轮 → STRATEGY_GUIDE.md 与
  strategy.json 登记轮次必须 >= 该轮，落后即 FAIL（防「策略文档漏更新」复发）
- 迭代 manifest 的 deliverables 必须是 `{path, kind}` 对象数组（非字符串列表）；
  status 用 schema 枚举（delivered），顶层不得出现 schema 外字段
- 新增 fact 必填 schema 全字段：supersedes/superseded_by/created_at/updated_at/
  confidence_grade/change_type/source（source=None 会崩 rehash）+ evidence 内
  n_observations/data_version/rules_epoch/script/source_sha256/noop_count

**校验不过 = 本轮未完成。** 不得标记 `status: delivered`。

---

## 7. 禁止事项

| 禁止 | 理由 |
|---|---|
| 修改已发布结论的 `id` | id 是永久的引用锚点 |
| 删除已推翻的结论 | 会导致下轮重走弯路（见 `MEMORY_PROTOCOL.md`） |
| 不写 `caveats` | 下游无法判断失效边界 |
| 跳过分期稳健性（当结论支持时段性判断时） | L3 教训 |
| 用模拟"验证"解析事实 | L8 教训 |
| 跨规则 epoch 比较奖金 | L9 教训 |
| 声称提高中奖概率 | 红线 |
| 在 `TASK_BRIEF` 里写期望结论（独立复核场景） | 反锚定失效 |
| 收轮不生成下轮 `TASK_BRIEF` | **迭代链断裂** |
| 读改写脚本用 `utf-8` 读带 BOM 文件 | 每次运行叠加一个 U+FEFF → 版本行注入失效（r11 BOM 教训）；读/写统一 `utf-8-sig` |
| 策略文档版本落后于最新策略更新轮 | ★S 拦截：轮次收尾前必须同步证据并 bump 登记（r10/r11.1 教训） |
| 新任务 id 用非纯数字（如 T-048b） | 任务书生成器正则只匹配 `T-\d{3}`，用 `T-\d{3}[a-z]?` 会被静默漏掉（r12 教训） |
| 变更 versions.json 后不跑 5 个 render + inject | README 目录树/版本行/派生图为派生物，validate 结构完整性会红 |
| manifest 的 deliverables 写成字符串列表 | schema 要求 `{path, kind}` 对象数组（r11 教训） |

---

## 8. 一轮的标准时长（按工作量而非时间）

| 规模 | 典型内容 | 产出 |
|---|---|---|
| **小** | 复核 1 条结论的分期稳健性 | 1–2 条更新结论 |
| **中** | 检验 2–3 个假设 | 3–5 条新结论 |
| **大** | 新彩种接入 / 框架重构 | 多个结论 + 框架版本更新 |

**不要在单轮里塞太多。** 结论之间的证据链越短，可追溯性越强。
宁可多轮推进，也不要一轮产出 20 条互相纠缠的结论。

---

## 9. 给执行者的最后提醒

> 本仓库的价值**不在结论的数量，而在结论的可追溯性**。
>
> 一条标着 `tentative` 且 `caveats` 写得很清楚的结论，
> 比一条标着 `established` 但边界模糊的结论**有用得多**。
>
> 如果你不确定某条结论该标 `established` 还是 `tentative` ——
> **标 `tentative`**。本仓库宁可保守。
