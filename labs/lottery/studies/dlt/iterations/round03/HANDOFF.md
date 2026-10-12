# HANDOFF.md — round03 → round04

> **版本**：`1.0` ｜ 轮次 `r03` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

| 项 | 内容 |
|---|---|
| **完成轮次** | `round03` |
| **彩种** | `dlt` |
| **日期** | 2026-10-11 |
| **状态** | `delivered` |
| **数据版本** | `dlt_full_2933` |
| **性质** | 复核轮（清偿 3 项 P0 技术债 + 1 次自我纠错） |

---

## 1. 本轮结论清单

### 1.1 新增（3 条）

| id | 结论 | 状态 | 置信度 | 引用类别 |
|---|---|---|---|---|
| **F-0016** | 封顶条款在 E6 102 期中**从未触发**（总额最大 0.9788 亿） | established | ★★★★★ | 解析可证 |
| **F-0017** | 计入 1 亿封顶后，避开连号的期望奖金提升由 121% 降至实测锚点下约 41% | established | ★★★☆☆ | 模型估计 |
| **F-0018** | F-0003 的撞号效应不依赖均值比（中位数比 1.5 + 截尾 1.72%） | established | ★★★★☆ | 观测+Bootstrap |

### 1.2 更新（2 条）

| id | 变化 |
|---|---|
| **F-0003** | 补分期稳健性：效应仍成立但**幅度衰减过半**（前段一等奖比 2.11 → 后段 1.25）；新增 `split_2013_08` 结构化字段；caveats 重写（L5 已清偿 + 强度衰减） |
| **F-0004** | claim 改为"未计封顶上界 121% / 计入封顶实测锚点约 41%"；`effect` 新增 `prize_uplift_pct_with_cap_anchor = 41.42`；caveats 重写（封顶稀释已量化） |

### 1.3 取代 / 推翻（1 条）

| 旧 id | 新 id | 原因 |
|---|---|---|
| **F-0015** | **F-0016** | 原称"26113 期触发 1 亿封顶" → **实测未触发**（归因错误） |

双向已填：`F-0015.superseded_by = F-0016`、`F-0016.supersedes = F-0015`。

---

## 2. 本轮最重要的事：一次自我纠错

`F-0015` 在 round02 被标为 `confidence: 5`（理由："直接观测到官方公告记录的实际事件"）。

**问题在于：观测到的是"事件"，归因却错了。**

| 项 | F-0015 原说法 | 实测 |
|---|---|---|
| 26113 期 37 注一等奖 | "触发封顶" | 总额 0.8852 亿 < 1 亿 → **未触发** |
| 单注 239 万 | "因封顶被压低" | 是 **0.8852亿/37 的自然摊薄** |
| 263 万 vs 1000 万上限 | — | 1000 万上限**从未触及**（实测最大 1000.0 万出现在 w1≤4 的少数期） |

**教训（拟追加 LESSONS）**：

> **高置信度不豁免归因错误。** "我亲眼看到"只能支撑"事件发生了"，
> 不能支撑"事件由 X 引起"。归因需要**独立的证据**（本轮用全期扫描）。
> 所有 `confidence: 5` 的观测类结论都应检查：它证的是"发生"还是"原因"？

---

## 3. 遗留问题（按优先级）

| 优先级 | 问题 | 关联 | 建议脚本 | 为什么重要 |
|---|---|---|---|---|
| **P1** | `Q-010` 撞号效应**为何衰减**？（人群结构变化 / 数据质量 / 真实弱化） | `F-0003` 分期 | `round04/scripts/decay_cause.py` | 衰减原因决定 `F-0004` 应否按后段 1.25 而非全样本 1.36 校准 |
| **P1** | `Q-007` 奖金瓜分机制与择时 | v4 的 T4.3（从未做） | `round04/scripts/prize_mechanism_tobit.py` | 可能产出**第二条独立可用规则** |
| **P1** | `Q-003` 后区撞号建模 | `F-0011` caveat | `round04/scripts/back_collision.py` | 后区仅 66 组合，撞号集中度可能更高 |
| P2 | `Q-011` 后段 CI 下界逼近 1（1.03），E6 内会否弱化至不显著 | `F-0003` 后段 | 随数据增长滚动复验 | 决定 F-0004 的时效性 |
| P2 | `Q-006` 逐号偏好权重 | `F-0004` caveat | `round04/scripts/weight_calibration.py` | 可把 `F-0004` 从 ★★★☆☆ 提升 |
| P2 | `Q-005` 销量内生性 | `F-0012` caveat | — | 影响 `F-0003` 的稳健性论证 |
| P2 | `Q-008` "策略有效性"标准 | 元问题 | 文档工作 | 影响对外表达可信度 |
| P2 | `Q-009` 组合分散度 | **仍为提案** | — | **未获用户批准，勿动** |

**P0 已全部清偿** —— 本轮无 P0 遗留。

---

## 4. 下轮建议（明确推荐）

**建议 round04 优先攻**：

1. **`Q-010`**（P1，最高优先）
   理由：这是本轮暴露的**新问题**，且直接决定 `F-0004` 的校准口径。
   若衰减源于"人群结构真实变化"，则新一轮应把 α 按后段 1.25 重算；
   若源于"数据质量/口径变化"，则应修正数据而非模型。
   **两种结论导向完全相反的动作**，必须先分清。
   预计产出：更新 `F-0003` / `F-0004` 的幅度口径；可能新增 1 条结论

2. **`Q-007`**（P1）
   理由：**可能产出第二条独立可用的策略规则**。当前 `strategy.json` 只有
   `R-001`（避连号）+ `R-002`（分散度，predicate 待修）。若存在"高期望期"（奖池累积），
   可加 `R-003`（择时）。
   预计产出：新增 `F-00xx`（瓜分机制 / 择时）

3. **`Q-003`**（P1）
   理由：后区仅 66 组合，撞号集中度可能**高于前区**。`R-001` 目前只约束前区，
   若后区也存在撞号效应，`R-001` 应扩展。
   预计产出：新增后区撞号结论；可能更新 `R-001`

**不建议下轮做的**：

| 项 | 为什么现在不做 |
|---|---|
| `Q-006` 逐号偏好权重 | 需要逐号建模（67 个参数），成本高、收益仅"提升一档置信度"；应先做 P1 |
| `T-031` 第二个彩种接入 | 先把 dlt 做扎实；框架通用性检验可延后 |
| `H-003` 摇奖设备假设 | 需要外部数据源，不在能力范围 |
| `Q-009` 组合分散度 | **未获用户批准** |

---

## 5. 框架改进建议（自我迭代的元层面产出）

| # | 建议 | 理由 | 状态 |
|---|---|---|---|
| **R-1** | `fact.schema.json` 增加 `evidence.verification_class` 枚举（`analytic`/`exact_enumeration`/`observational`/`simulated`） | "解析可证 vs 模拟估计"仍是自由文本，机器不可判 | **待评审**（round02 已提） |
| **R-2** | `fact.schema.json` 增加 `depends_on`（结论间依赖边） | `F-0004` 依赖 `F-0003` 的 α 校准；`F-0003` 已更新，`F-0004` 应自动降级 —— 现在靠人记 | **待评审** |
| **R-6** | **`evidence.effect` 增加"观测事件 vs 归因"两分** | ★ **本轮新增**：`F-0015` 的教训 —— 高置信度观测不能外推为归因。schema 应逼作者显式区分 | **新增建议** |
| **R-3** | 校验器增加"证据哈希" | `source` 被改后无法检出结论失效 | **待评审** |
| **R-5** | `strategy.schema.json` 增加 `validity_window` | 策略规则会因规则变更失效（F-0003 的衰减也是时效问题） | **待评审** |

> **R-6 本轮最值得做** —— 它是本轮唯一一次实质纠错的直接产物。
> `F-0015` 的 `confidence_basis` 写的是"直接观测到官方公告记录的实际事件"，
> 这是**真的**；但 claim 说的是"触发了封顶"，这是**归因**，需要另一类证据。
> schema 若不区分，同类错误会重演。

---

## 6. 本轮踩的坑（→ LESSONS）

| 新教训 | 症状 | 检测方法 | 已追加 LESSONS？ |
|---|---|---|---|
| **归因错误的伪装** | 高 confidence（5）+ 真实观测 → 掩盖了错误归因 | 区分"事件发生"与"事件原因"两类 claim；归因须有独立证据（全期扫描） | ⏳ 建议追加为 **L10**，待用户确认 |
| **锚点口径反了** | 用 `pool_yuan`（奖池余额）/单注金额 → 得到 1.7 注的荒谬锚点 | 锚点必须取**实测可观测统计量**（w1 中位 6 注），不得由不相关量反推 | ⏳ 建议追加为 **L11** |
| **估计量不独立** | NB2 IRR 与均值比数值等价 → 误当"两个独立证据" | 用 log 链接的计数模型，IRR ≡ 均值比；须检查估计量是否真独立 | ⏳ 建议追加为 **L12** |

> **本轮产生了 3 条真实的新教训**（不同于 round02 的"无新增"）。
> 是否写入 `LESSONS.md`（L10–L12）**待用户确认** —— 已列入下轮建议。

---

## 7. 给下轮执行者的提醒

### 7.1 最容易被误用的结论

| 结论 | 误用方式 | 正确用法 |
|---|---|---|
| **`F-0004`** | 引用"121%" | 121% 是**未计封顶上界**；净值约 41%（F-0017）；低注数情形为 0% |
| **`F-0004`** | 引用全样本 1.36 校准 | 效应**幅度衰减过半**（F-0003），后段仅 1.25；**不应按 1.36 恒定外推** |
| **`F-0015`** | 引用 | **已推翻（superseded），禁止引用** |
| **`F-0016`** | 外推为"永不触发封顶" | 是**样本内（102 期）**结论；40+ 注一等奖的期次仍可能触发 |
| **`F-0017`** | 当成精确值 41% | 是**模型估计**（★★★☆☆）；锚点取中位数，±50% 是敏感性而非 CI |

### 7.2 最不该信的推断

**`F-0004` 的绝对值精度仍被高估。** 本轮虽已量化封顶，但它仍依赖：
- 人群权重模型（仅"连号"+"生日号≤31"两个特征）
- 单一校准参数 `α = 13.9405`
- 假设 H2/H3

**并且**本轮发现效应**幅度随时间衰减** —— 所以按全样本校准本身就有偏差。
**给用户输出时必须写出"这是上界、且幅度在衰减"。**

### 7.3 环境/路径注意事项

| 项 | 注意 |
|---|---|
| 数据读取 | `encoding="utf-8-sig"`，否则列名带 BOM |
| Python | `C:/Users/panda/.workbuddy/binaries/python/envs/default/Scripts/python.exe` |
| 新增依赖 | `statsmodels 0.15.0`（T-002 的 NB2 用）；已在环境中 |
| 脚本路径锚点 | `round03/scripts/` 上溯 **5 级**才到仓库根（`scripts→round03→iterations→dlt→games→root`）—— 本轮踩过，`apply_r03_facts.py` 一度算成 4 级 |
| 校验 | 收轮前必须跑 `python cli/main.py validate --all`（本轮 43 项通过） |
| BOM/内联脚本 | Bash 工具里 `python -c` 偶发 exit 127，改用**脚本文件**最稳 |
| 沙箱 | 不能写 `D:\` 根；临时脚本放仓库内 |

### 7.4 若时间/精力有限，只做这一件事

> **做 `Q-010`（查清撞号效应为何衰减）。**

理由：这是**唯一一个"决定其它结论怎么用"**的问题。
`F-0004` 该按 1.36 还是 1.25 校准，完全取决于衰减的性质。
其它问题（`Q-007`/`Q-003`）是"新增价值"，而 `Q-010` 是"修正现有价值"。

---

## 8. 本轮工作记忆变化

| 文件 | 变化 |
|---|---|
| `labs/lottery/studies/dlt/memory/facts/FACTS.jsonl` | 15 → **18 条**（+F-0016/F-0017/F-0018；F-0015 标 superseded） |
| `labs/lottery/studies/dlt/strategy/strategy.json` | R-001 `expected_value_impact` 同步；`evidence_index` 9 → **12 条**；`provenance.iteration = round03` |
| `labs/lottery/studies/dlt/iterations/round03/scripts/` | **新建**，6 个脚本 + 3 个 JSON 产出 |
| `labs/lottery/studies/dlt/memory/workbench/OPEN_QUESTIONS.md` | 待更新（Q-001/Q-002/Q-004 标 answered；新增 Q-010/Q-011） |
| `labs/lottery/studies/dlt/memory/workbench/TODO.md` | 待更新（清算 T-001/T-002/T-003） |
| `labs/lottery/studies/dlt/iterations/round03/FINDINGS.md` | **新建** |
| `labs/lottery/studies/dlt/iterations/round03/HANDOFF.md` | 本文件 |
| `labs/lottery/studies/dlt/memory/journal/round03.md` | 待更新 |

---

## 9. 校验状态

```bash
python cli/main.py validate --all
```

结果：**✅ 全部通过（43 项检查；1 项预期内警告）**

警告内容（**已知待决策，非本轮引入**）：

```
! strategy[dlt].R-002: predicate 引用了未声明的特征
  ['duplicated_structure_across_tickets']
  —— 该规则单注层无法判定，若这是跨注特征（如组合分散度）应属 L3；
     若是拼写错误则须修正。
```

---

## 10. 下一轮 TASK_BRIEF

- [x] 已创建 `labs/lottery/studies/dlt/iterations/round04/TASK_BRIEF.md`
- [x] 已填入：目标 + 验收判据 + 陷阱提醒（从本文件第 3、4、7 节转写）
- [x] 已更新 `labs/lottery/studies/dlt/iterations/round03/manifest.json` → `status: delivered`

---

## 11. 交付物清单（本轮新增/修改）

| 路径 | 说明 |
|---|---|
| `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py` + `.json` | T-003 封顶修正 |
| `labs/lottery/studies/dlt/iterations/round03/scripts/b2_split_stability.py` + `.json` | T-001 分期稳健性 |
| `labs/lottery/studies/dlt/iterations/round03/scripts/b2_robust_estimators.py` + `.json` | T-002 稳健估计量 |
| `labs/lottery/studies/dlt/iterations/round03/scripts/apply_r03_facts.py` | 事实落地（幂等） |
| `labs/lottery/studies/dlt/iterations/round03/scripts/apply_r03_strategy.py` | 策略落地 |
| `labs/lottery/studies/dlt/iterations/round03/FINDINGS.md` | 本轮证据层 |
| `labs/lottery/studies/dlt/iterations/round03/HANDOFF.md` | 本文件 |
| `labs/lottery/studies/dlt/memory/facts/FACTS.jsonl` | 18 条（+3，1 条 superseded） |
| `labs/lottery/studies/dlt/strategy/strategy.json` | R-001 同步 + evidence_index 扩充 |

---

*交接的本质：让下一轮执行者**不需要读 FINDINGS 全文**就能知道从哪开始。*
*本轮的特殊之处：最重要的一课是"我错了，错在哪"。*
