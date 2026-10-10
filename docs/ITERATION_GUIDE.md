# ITERATION_GUIDE —— 如何做一轮分析

> **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

面向"下一轮的执行者"（人或 AI）。目标是：**任何有能力的执行者，照本文件就能正确完成一轮。**

## 0. 动手前的固定顺序（不许跳）

```bash
# 1) 读单一入口
cat AI_CONTEXT.md

# 2) 读教训库（这一步最容易被跳过，也最容易导致返工）
cat memory/lessons/LESSONS.md

# 3) 读本轮任务书
cat games/<id>/iterations/roundNN/TASK_BRIEF.md

# 4) 读待办与开放问题，只挑与本轮 TASK_BRIEF 相关的
python cli/main.py questions
python cli/main.py todo

# 5) 确认基线干净
python cli/main.py validate --all
```

第 2 步为什么必须在第 3 步之前：**先知道坑在哪，再读任务。**
反过来读会产生锚定——看到任务描述就觉得"这方案可行"，而忽略了任务书本身
可能已经踩了 L1–L9 中的某一条。

## 1. 一轮的四件套

| 文件 | 何时写 | 作用 |
|---|---|---|
| `TASK_BRIEF.md` | **开轮前** | 反锚定：只写问题与判据，不写答案 |
| `FINDINGS.md` | 分析过程中/结束 | 结论 + 引用类别 + 主动证伪 |
| `HANDOFF.md` | **收轮时** | 交接 + 框架改进建议 |
| `manifest.json` | **收轮时** | 结构化登记（机器可读） |
| `round(N+1)/TASK_BRIEF.md` | **收轮时必生成** | 迭代链不断的关键 |

模板在 `framework/protocol/templates/`。

## 2. 开轮：写 TASK_BRIEF

8 节（见模板）。关键：

- **§5 陷阱提醒**：逐条对照 LESSONS，说明本轮场景为什么/为什么不适用。
  跳过这一节 = 主动放弃教训库的保护。
- **§8 反锚定声明**：明写"不要预设某个结论成立"。

## 3. 做分析

### 3.1 数据口径先钉死

在写任何检验代码之前，在 `FINDINGS.md` 里先写一段**数据与口径声明**：

- 用的是哪个文件（含 SHA256）
- 期号范围、行数
- 每个用到的列，含义是什么
- 有没有缺失/重复/口径变更

**教训 L7 的全部代价**：拿"开出率"当"被选中率"，整轮作废。
口径没钉死之前，任何数字都不可信。

### 3.2 结果必须落盘

脚本输出 JSON/CSV 到 `data/derived/`，不要只 print。
结论里 `evidence.script` 必须指向**存在的**文件（校验器会检查）。

### 3.3 给结论标注引用类别（最重要的一步）

每条结论必须落在下列**四类之一**，且**不可混淆**：

| 类别 | 定义 | 可否用模拟验证 |
|---|---|---|
| 解析可证 | 由定义/数学直接推出 | ❌ 禁止（教训 L8） |
| 精确枚举 | 可穷举真值（如 C(35,5)=324632） | ❌ 禁止 |
| 观测+CI | 历史数据估计，带置信区间 | ✅ 可以 |
| 模型估计 | 依赖假设的推算 | ✅ 可以，且必须列假设 |

**判据**：如果你能用"对所有可能情况求和"算出真值，那它就是解析/枚举，
**不允许**用模拟去"验证"它。反过来，如果你在用一个模型推一个观测不到的量
（如"若避开连号，奖金会是多少"），必须写明模型假设与减损项。

### 3.4 主动证伪

在 `FINDINGS.md` 里显式写三小节：

1. **我尝试推翻了什么**（做了哪些证伪性检验）
2. **什么结果会让我改变结论**（预先声明）
3. **我没有做的检验及原因**（诚实边界）

第 3 节尤其重要 —— **不要假装做全了**。没做的写出来，下一轮的人会补。

### 3.5 置信度怎么给（1–5）

| 值 | 判据 |
|---|---|
| 5 | 解析可证 / 精确枚举真值 |
| 4 | 强观测 + 多源交叉验证 |
| 3 | 依赖模型的估计 |
| 2 | 弱迹象，样本不足或方法有争议 |
| 1 | 猜测，或已被推翻 |

**状态与置信度是两个独立维度**：

- `status`（established/tentative/refuted/superseded）回答"证据是否成立"
- `confidence`（1–5）回答"证据有多强"

`established` + ★★★☆☆ 是**合法**的（如 F-0004：效应方向确定，但幅度依赖模型）。

## 4. 收轮

### 4.1 更新记忆（四项，缺一不可）

```bash
# 1) 追加新结论到 memory/facts/FACTS.jsonl
#    用 Memory.add_fact()，它会强制红线检查与 source 存在性
# 2) 重生成 INDEX（派生物，不要手改）
python cli/main.py index
# 3) 写 memory/journal/roundNN.md（本轮的完整叙事）
# 4) 更新 memory/workbench/（caveats → OPEN_QUESTIONS → TODO）
```

### 4.2 结论演化的写法

取代旧结论时**必须双向一致**：

```jsonc
// 新结论
{ "id": "F-0006", "supersedes": "F-0007", ... }
// 旧结论
{ "id": "F-0007", "superseded_by": "F-0006", "status": "superseded", ... }
```

校验器会检查一致性。**被取代/被推翻的结论不要删除** ——
保留演化链，否则后人会重复踩同一个坑（见 `MEMORY_PROTOCOL.md` §1.4）。

### 4.3 若影响对外策略

```bash
python cli/main.py strategy --game <id> --dry-run    # 先看
python cli/main.py strategy --game <id>              # 再写
```

注意：CLI 只重算 `boundary` 与重建 `evidence_index`，
**`rules` 与 `avoid_list` 不由代码生成** —— 那是需要人/ AI 判断的产物。
写完后校验会自动跑。

### 4.4 提框架改进建议

在 `manifest.json` 的 `framework_revision.proposed` 里写。
格式：`R-1: <问题> → <建议>`。被采纳的进 `accepted`。

这是"框架自身进化"的机制 —— 每轮都要提，哪怕只是"这轮没发现问题"。

### 4.5 生成下一轮 TASK_BRIEF（最重要）

**不生成 = 迭代链断裂。** 从本轮 HANDOFF 的 §3「下轮建议」转写，
保持 8 节结构，特别是：

- 逐条点名本轮相关的 LESSONS 陷阱
- 写明验收判据
- 写反锚定声明

## 5. 校验

```bash
python cli/main.py validate --all -v          # 全量
python cli/main.py validate --game <id>       # 单彩种（含 strategy + iterations）
python cli/main.py validate --facts           # 只查台账
```

校验项目（40 项）包括：

- 5 份 schema 的 jsonschema 校验（含 `version_index.schema.json`）
- 四条红线（`const` 级）
- 外键（`evidence_refs` / `upstream_fact_ids` 指向存在）
- 双向取代一致性
- `caveats` 非空
- `evidence.script` / `source` 文件存在性
- **数据 SHA256 实算比对**
- **`features[]` 声明可执行性**（每个声明能否被框架原语执行）
- **`predicate` 引用完整性与作用域**（单注层 / 跨注层分类）
- **版本一致性**：文件内版本行 ↔ `versions.json` ↔ `VERSION_INDEX.md`

**全绿才收轮。** 另需跑 `python tests/test_core.py`（105 项）。

## 6. 规模建议

一轮不要太大。经验值：

| 项 | 建议 |
|---|---|
| 新增结论 | 3–8 条 |
| 每轮脚本 | 1–3 个 |
| 单个脚本 | < 300 行 |
| 单轮时长 | 一个完整的工作会话内可完成 |

轮次太大 → 中途上下文丢失 → 结论质量下降。宁可多轮小步快跑。

## 7. 禁止事项总表

| 禁止 | 依据 |
|---|---|
| 用模拟验证解析事实 | L8 |
| 跨规则断点比奖金 | L9 |
| 用自然年硬切变点 | L3 |
| 重尾数据比均值 | L5 |
| 混用开出率与被选中率 | L7 |
| 删除被推翻的结论 | MEMORY_PROTOCOL §1.4 |
| 手改 `INDEX.md` | 它是派生物 |
| 在 `framework/` 写彩种分支 | ARCHITECTURE 唯一硬标准 |
| 跳过 TASK_BRIEF 直接给结论 | 反锚定协议 |
| 静默跳过数据缺口 | MEMORY_PROTOCOL / data/raw/README |
| 收轮不生成下轮 TASK_BRIEF | 迭代协议 §4.3 |

## 8. 自查清单（收轮前逐条打勾）

- [ ] TASK_BRIEF 的每一项验收判据都有明确结论（做到/没做到/部分）
- [ ] 每条新结论都标了引用类别（四选一）
- [ ] 每条新结论的 `caveats` 非空
- [ ] 做了主动证伪，并诚实声明"没做的检验"
- [ ] `FACTS.jsonl` 无双向取代不一致
- [ ] `INDEX.md` 已重生成
- [ ] `memory/journal/roundNN.md` 已写
- [ ] `workbench` 已更新（caveats → 新问题）
- [ ] `manifest.json` 合规于 `iteration.schema.json`
- [ ] `framework_revision.proposed` 已写
- [ ] **`round(N+1)/TASK_BRIEF.md` 已生成**
- [ ] `python cli/main.py validate --all` 全绿
