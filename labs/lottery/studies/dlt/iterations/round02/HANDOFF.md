# HANDOFF.md — round02 → round03

> **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

| 项 | 内容 |
|---|---|
| **完成轮次** | `round02` |
| **彩种** | `dlt` |
| **日期** | 2026-10-10 |
| **状态** | `delivered` |
| **数据版本** | `dlt_full_2933` |

---

## 1. 本轮结论清单

### 1.1 新增

15 条，全部为 v4 素材的编号化（`F-0001` ~ `F-0015`）。

| id | 结论 | 状态 | 置信度 | 引用类别 |
|---|---|---|---|---|
| F-0001 | 任何选号方式都不能改变单注中奖概率 | established | ★★★★★ | 解析可证 |
| F-0002 | 彩票是负期望游戏（返奖率 51%） | established | ★★★★★ | 解析可证 |
| F-0003 | 连号形态人群更密（1.3603） | established | ★★★★☆ | 观测 |
| **F-0004** | **避开连号提高中奖时奖金 +121%** | established | **★★★☆☆** | **模型估计** |
| F-0005 | 开出率 ≠ 被选中率 | established | ★★★★☆ | 精确枚举 |
| F-0006 | 结构切点 2013-08（渐变） | established | ★★★★☆ | 观测+多方法 |
| F-0007 | ~~2015 年断点~~ | **superseded** | ★☆☆☆☆ | — |
| F-0008 | 序列不可预测 | established | ★★★★☆ | 观测+样本外 |
| F-0009 | heat 伪显著 | established | ★★★★☆ | 观测(HAC) |
| F-0010 | 奇偶偏离不显著 | established | ★★★★★ | 精确检验 |
| F-0011 | 后区独立 | established | ★★★★☆ | 观测 |
| F-0012 | 销量有星期效应，号码没有 | established | ★★★★☆ | 观测 |
| F-0013 | 18 组重复正常 | established | ★★★★☆ | 精确枚举 |
| F-0014 | 规则 6 次变更；号码结构从未变 | established | ★★★★★ | 解析可证 |
| F-0015 | 1 亿封顶已实测触发 | established | ★★★★★ | 观测 |

### 1.2 更新

无（首次编号化）。

### 1.3 取代 / 推翻

| 旧 id | 新 id | 原因 |
|---|---|---|
| `F-0007` | `F-0006` | "2015 年断点"是自然年硬切的产物，实为 2013-08 |

双向已填：`F-0007.superseded_by = F-0006`、`F-0006.supersedes = F-0007`。

---

## 2. 遗留问题（按优先级）

| 优先级 | 问题 | 关联 | 建议脚本 | 为什么重要 |
|---|---|---|---|---|
| **P0** | `Q-004` +121% 未纳入现行 1 亿封顶 | `F-0004` caveat #2 · `F-0015` | 扩展 `strategy_simulation.py` | **现有对外输出偏乐观** —— 封顶已实测触发，触发后减少同号人数不再提高单注奖金 |
| **P0** | `Q-001` 撞号效应分期稳健性 | `F-0003` caveat #2 | `round03/scripts/b2_split_stability.py` | 若只在 2013-08 前成立，`F-0004` 需大幅降级 |
| **P0** | `Q-002` 均值比 → 中位数比 / NegBin IRR | `F-0003` caveat #1（偿 L5） | `round03/scripts/b2_robust_estimators.py` | 纪律性欠账；重尾变量用均值比有实质风险 |
| **P1** | `Q-007` 奖金瓜分机制与择时 | v4 的 T4.3（从未做） | `round03/scripts/prize_mechanism_tobit.py` | 可能产出**第二条独立可用规则** |
| **P1** | `Q-003` 后区撞号建模 | `F-0011` caveat | `round03/scripts/back_collision.py` | 后区仅 66 组合，撞号集中度可能更高 |
| P2 | `Q-006` 逐号偏好权重 | `F-0004` caveat #1 | `round03/scripts/weight_calibration.py` | 可把 `F-0004` 从 ★★★☆☆ 提升 |
| P2 | `Q-005` 销量内生性 | `F-0012` caveat | — | 影响 `F-0003` 的稳健性论证 |
| P2 | `Q-008` "策略有效性"标准 | 元问题 | 文档工作 | 影响对外表达可信度 |

**P0 的定义**：不做会**导致现有对外输出错误**，或**阻塞后续工作**。

---

## 3. 下轮建议（明确推荐）

**建议 round03 优先攻**：

1. **`Q-004`**（P0，最高优先）
   理由：**现在 `strategy.json` 给用户的 +121% 是未计封顶的上界**。
   `F-0015` 已证明封顶实测触发（26113 期 37 注 → 单注 239 万）。
   这是一个**已知偏差的对外输出**，应最先修正。
   预计产出：更新 `F-0004` 的 `magnitude_pct` + `strategy.json` 的 `expected_value_impact`

2. **`Q-001` + `Q-002`**（P0，合并执行）
   理由：两者都是 `F-0003` 的稳健性检验，可共用同一份数据切片。
   若撞号效应只在早期成立，`F-0004` 的整个策略价值需要重新评估。
   预计产出：新增 1–2 条复核结论；可能更新 `F-0003` 的 `caveats`

3. **`Q-007`**（P1）
   理由：**可能产出第二条独立可用的策略规则**。当前策略集只有 `R-001` 一条，
   若存在"高期望期"（奖池累积），可加 `R-003`（择时）。
   预计产出：新增 `F-00xx`（瓜分机制 / 择时）

**不建议本轮做的**：

| 项 | 为什么现在不做 |
|---|---|
| `T-031` 第二个彩种接入 | 先把 dlt 的策略质量做扎实；框架通用性检验可延后 |
| `H-003` 摇奖设备假设 | 需要外部数据源，不在本轮能力范围 |
| 框架重构（`R-1`/`R-2` 的 schema 变更） | 应等 round03 的分析实践暴露真实需求后再改，避免臆测 |

---

## 4. 框架改进建议（自我迭代的元层面产出）

| # | 建议 | 理由 | 影响面 |
|---|---|---|---|
| **R-1** | `fact.schema.json` 增加 `evidence.verification_class` 枚举<br>（`analytic` / `exact_enumeration` / `observational` / `simulated`） | 当前"解析可证 vs 模拟估计"只存在 `evidence.method` 的自由文本里，**机器不可判**。这是本仓库最重要的区分（L8），应结构化 | schema 次版本 + 15 条结论需回填 |
| **R-2** | `fact.schema.json` 增加 `depends_on` 字段（结论间依赖边） | 当前只知道"谁取代谁"（演化），不知道"谁依赖谁"。`F-0004` 依赖 `F-0003` 的 α 校准 —— 若 `F-0003` 被推翻，`F-0004` 应自动降级。现在这个传导靠人记 | schema 次版本 |
| **R-3** | 校验器增加"证据哈希" | `source` 文件被改后无法检出结论失效。呼应 `spec/VERSIONING.md` 的数据静默修改风险 | `validate.py` |
| **R-4** | `INDEX.md` 自动生成 ✅ **本轮已实现** | 手写必然漂移 | — |
| **R-5** | `strategy.schema.json` 增加 `validity_window` | 策略规则会因规则变更（如封顶条款）失效，需显式有效期 | schema 次版本 |

**评审状态**：R-4 已实现；R-1 ~ R-3、R-5 待 round03 评审。

> **R-1 应最优先** —— 它是本轮实践暴露的最直接痛点：
> 分类信息存在但机器不可判，导致"引用 `F-0004` 时误当 `F-0001` 用"这类错误无法被程序阻止。

---

## 5. 本轮踩的坑（→ LESSONS）

| 新教训 | 症状 | 检测方法 | 已追加 LESSONS？ |
|---|---|---|---|
| 无新增 | — | — | — |

**说明**：本轮未产生新的方法论教训（性质为整理入库）。
但**发现了一条技术债**：`F-0003` 用均值比触及 `L5`。
这不是新教训，是**已知教训未被充分执行** —— 已记入 `Q-002` / `T-002`（P0）。

> 本条记录本身有价值：它说明**教训库里已有的条目仍可能被违反**。
> 未来的 `R-1`（结构化 `verification_class`）正是为了让这类违反可被程序检出。

---

## 6. 给下轮执行者的提醒

### 6.1 最容易被误用的结论

| 结论 | 误用方式 | 正确用法 |
|---|---|---|
| **`F-0004`** | 当成 `F-0001` 那样的定理引用（"避开连号能提高收益 121%"） | 它是**模型估计**（★★★☆☆）。必须带 caveats：封顶稀释、只在中奖时兑现、长期期望仍为负 |
| **`F-0004`** | 表述为"提高中奖率" | **提高的是"中奖时奖金"**。写成提高中奖率是本仓库最严重的表述错误 |
| **`F-0003`** | 与 `F-0005` 混用 | `F-0003` 是"人更爱买连号"（可用）；`F-0005` 是"连号被摇出的频率"（不可用） |
| `F-0006` | 当成精确日期 | 是**渐变**，切点有 **±6 个月**不确定性 |
| `F-0007` | 引用 | **已推翻，禁止引用** |

### 6.2 最不该信的推断

**`F-0004` 的 +121% 的精度被高估了。**

它是条件份额模拟的结果，依赖：
- 人群权重模型（只有"连号"和"生日号（≤31）"两个特征）
- 校准参数 `α = 13.9405`（由单一比值锁定）
- 假设 H2/H3（彩民非均匀、注数 ∝ 购买量）

这三者都是**估计**。真实数字可能显著偏离。
**并且**它还**未纳入封顶**（`Q-004`）—— 所以方向上也是偏乐观的。

**给用户输出时必须把这两个减损明确写出。**

### 6.3 环境/路径注意事项

| 项 | 注意 |
|---|---|
| 数据读取 | `encoding="utf-8-sig"` + `dtype={"draw_num": str}`，缺一即错 |
| Python | 用 `C:/Users/panda/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（含 numpy/pandas/pyyaml/jsonschema）；系统 python 无这些依赖 |
| 脚本路径 | v4 脚本已修正为 `raw/` 与 `derived/`，但 `strategy_simulation.py` 的路径**尚未修正**（它读 `../01_data/`）—— 需修 |
| 校验 | 收轮前必须跑 `python cli/main.py validate --all` |
| `source` 路径 | 以**仓库根**为基准的相对路径（`labs/lottery/studies/dlt/...`），不是 `../../` |

### 6.4 若时间/精力有限，只做这一件事

> **做 `Q-004`（把 1 亿封顶加进条件份额模拟，重算 uplift）。**

理由：这是**唯一一个"当前对外输出已知有偏"的问题**。
其它问题（`Q-001`/`Q-002`）是"可能有问题"，而 `Q-004` 是"确定有问题、只是不知幅度"。

---

## 7. 本轮工作记忆变化

| 文件 | 变化 |
|---|---|
| `memory/facts/FACTS.jsonl` | **新建**，15 条 |
| `memory/facts/INDEX.md` | **新建**（由 `cli/main.py index` 生成） |
| `memory/lessons/LESSONS.md` | **新建**，L1–L9（从 v4 的 E1–E9 提炼 + 补「检测方法」） |
| `memory/workbench/OPEN_QUESTIONS.md` | **新建**，Q-001 ~ Q-008 |
| `memory/workbench/HYPOTHESES.md` | **新建**，H-001 ~ H-005 |
| `memory/workbench/TODO.md` | **新建**，T-001 ~ T-042 |
| `memory/journal/round02.md` | **新建** |
| `memory/INDEX.md` | **新建**（记忆层说明） |

---

## 8. 校验状态

```bash
python cli/main.py validate --all -v
```

结果：**✅ 全部通过（28 项检查；r03 起校验项扩展为 40 项）**

包含：
- `game.yaml` 合规 + SHA256 一致
- `strategy.json` 合规 + 红线恒值
- 15 条 FACTS 全部合规 + 红线 + 外键 + 双向取代 + `caveats` 非空
- 9 个协议/文档存在

---

## 9. 下一轮 TASK_BRIEF 已生成

- [x] 已创建 `labs/lottery/studies/dlt/iterations/round03/TASK_BRIEF.md`
- [x] 已填入：目标 + 验收判据 + 陷阱提醒（从本文件第 2、3、6 节转写）
- [x] 已创建 `labs/lottery/studies/dlt/iterations/round03/manifest.json`（`status: planned`）

---

## 10. 交付物清单

| 路径 | 说明 |
|---|---|
| `spec/*.schema.json` ×4 + `README.md` + `VERSIONING.md` | 契约层 |
| `AI_CONTEXT.md` | 单一入口 |
| `platform/protocol/{ITERATION,MEMORY}_PROTOCOL.md` + 3 模板 | 协议层 |
| `platform/methodology/{MATH_BOUNDARY,STATISTICAL_DISCIPLINE}.md` | 方法论 |
| `platform/tools/memory.py` | 记忆读写库 |
| `memory/facts/FACTS.jsonl` + `INDEX.md` | 结论台账（15 条） |
| `memory/lessons/LESSONS.md` | 教训库（L1–L9） |
| `memory/workbench/*` | 工作记忆（8 问 + 5 假设 + 42 待办） |
| `memory/journal/round02.md` | 本轮日志 |
| `labs/lottery/studies/dlt/game.yaml` | 彩种配置（7 epoch / 11 特征） |
| `labs/lottery/studies/dlt/rules_history.md` | 规则变更史 |
| `labs/lottery/studies/dlt/data/**` | 数据（raw/derived/tools/build_scripts） |
| `labs/lottery/studies/dlt/strategy/strategy.json` | **对外策略输出** |
| `labs/lottery/studies/dlt/strategy/simulation_results.json` | 模拟证据 |
| `labs/lottery/studies/dlt/iterations/round02/*` | 本文件 + FINDINGS + PRIORITY_TASKS + known_errors + legacy_findings |
| `labs/lottery/studies/dlt/iterations/round03/{TASK_BRIEF,manifest}.json` | 下一轮 |
| `src/spc/*` | 库代码（validate / memory / strategy / game / api） |
| `cli/main.py` | CLI（9 命令） |
| `tests/README.md` | 测试规划 |
| `docs/{ARCHITECTURE,CONSUMING,ITERATION_GUIDE}.md` | 文档 |

---

*交接的本质：让下一轮执行者**不需要读 FINDINGS 全文**就能知道从哪开始。*
*若做不到，说明遗留问题记录得不够具体。*
