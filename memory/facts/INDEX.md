# memory/facts/INDEX.md — 结论台账速览

> **本文件由 `cli/main.py index` 从 `FACTS.jsonl` 自动生成。请勿手工编辑。**
> 权威源是 `FACTS.jsonl`（每行一条，受 `spec/fact.schema.json` 约束）。

> **版本**：`1.4` ｜ 轮次 `r04` ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

**当前状态**：25 条结论 | 23 established / 2 superseded | 生成日期 2026-10-11

---

## 全部结论

| id | 彩种 | 结论 | 状态 | 置信度 | 类别 | ★证据类型 | 轮次 |
|---|---|---|---|---|---|---|---|
| F-0001 | global | 任何选号方式都不能改变单注的中奖概率 | established | ★★★★★ | `probability` | `analytic` | round02 |
| F-0002 | dlt | 彩票是负期望游戏：现行返奖率 51%，每 2 元投注的长期数学期望回报约 1.02 元 | established | ★★★★★ | `prize_mechanism` | `documentary` | round02 |
| F-0003 | dlt | 连号形态（run>=2）的投注人群密度更高，撞号效应真实存在 | established | ★★★★☆ | `structure_preference` | `empirical` | round02 |
| F-0004 | dlt | 在固定预算下避开连号形态，可提高『中奖时的期望奖金』—— 未计封顶的上界为 109%（后… | established | ★★★☆☆ | `prize_mechanism` | `simulation` | round02 |
| F-0005 | dlt | 『开出率』与『被选中率』是两个不同的量，连号的开出率优势仅存在于早期且不可用 | established | ★★★★☆ | `fairness` | `empirical` | round02 |
| F-0006 | dlt | 前区号码分布存在结构变化，最优切点为 2013-08（χ²=185.0，在 234 个候… | established | ★★★★☆ | `fairness` | `empirical` | round02 |
| F-0007 | dlt | 历史『2015 年断点』的结论是错的，正确切点为 2013-08 | superseded | ★☆☆☆☆ | `methodology` | `methodological` | round02 |
| F-0008 | global | 开奖序列不可预测：所有 ML/时序模型在严格时间序列外推下 R² 均为负 | established | ★★★★☆ | `predictability` | `empirical` | round02 |
| F-0009 | dlt | 『组合冷热（heat）』对中奖注数没有稳健效应，历史报告的显著性为伪显著 | established | ★★★★☆ | `methodology` | `empirical` | round02 |
| F-0010 | dlt | 奇偶分布的偏离不显著：渐近卡方的 p<1e-6 是伪显著 | established | ★★★★★ | `fairness` | `empirical` | round02 |
| F-0011 | dlt | 后区与前统计独立（互信息 0.203 < 置换基准 0.209），后区号码的『开出率』均… | established | ★★★★☆ | `fairness` | `empirical` | round02 |
| F-0012 | dlt | 销量存在星期效应（周六 > 周一/周三），但号码不存在星期效应 | established | ★★★★☆ | `sales_external` | `empirical` | round02 |
| F-0013 | dlt | 数据集的 18 组前区组合重复在随机碰撞的合理范围内，不是数据错误 | established | ★★★★☆ | `methodology` | `empirical` | round02 |
| F-0014 | dlt | 奖金规则已变更 6 次，跨 epoch 直接比较奖金金额会产生无意义结论；但号码结构（前… | established | ★★★★★ | `rules_scope` | `documentary` | round02 |
| F-0015 | dlt | 【已修正】第 26113 期（2026-10-05）37 注一等奖的单注 239 万元，… | superseded | ★★★★★ | `prize_mechanism` | `empirical` | round02 |
| F-0016 | dlt | 现行规则（E6，>=26014 期）下『一等奖单期总额封顶 1 亿元』条款从未触发：10… | established | ★★★★★ | `prize_mechanism` | `empirical` | round03 |
| F-0017 | dlt | 把 1 亿封顶纳入条件份额模拟后，避开连号的期望奖金提升由 121.48%（未计封顶）降… | established | ★★★☆☆ | `prize_mechanism` | `simulation` | round03 |
| F-0018 | dlt | F-0003 的撞号效应不依赖均值比：中位数比 1.5 [1.5, 2.0] 与均值比同… | established | ★★★★☆ | `methodology` | `methodological` | round03 |
| F-0019 | dlt | 2013-08 之前那段数据在『号码分布—中出注数—销售额』三者间不自洽：前区号码分布严… | established | ★★★★☆ | `methodology` | `empirical` | round04 |
| F-0020 | dlt | F-0003 的分期『衰减过半』是估计量依赖的：均值比口径给出 post/pre = 0… | established | ★★★★☆ | `methodology` | `methodological` | round04 |
| F-0021 | dlt | 撞号效应的弱化与 F-0006 的 2013-08 号码结构变点同期（滚动窗口 W=30… | established | ★★★☆☆ | `structure_preference` | `empirical` | round04 |
| F-0022 | dlt | 把 F-0004 的校准口径从全样本 1.3603 改为后段 1.2472 后，未计封顶… | established | ★★★☆☆ | `prize_mechanism` | `simulation` | round04 |
| F-0023 | dlt | 在可观测的一/二等奖派发口径下不存在稳健的『高期望期』：全局期初奖池分位 top−bot… | established | ★★★★☆ | `prize_mechanism` | `empirical` | round04 |
| F-0024 | dlt | 用『派发额/销售额』(r_t) 衡量择时价值会误判：E4 段剔除 2019 后 r_t … | established | ★★★★☆ | `methodology` | `methodological` | round04 |
| F-0025 | dlt | 后区撞号结构存在但不可靠可利用：后区 66 对的『被选中率』强烈非均匀（过散布 8.72… | established | ★★★★☆ | `structure_preference` | `empirical` | round04 |

## 按类别

| 类别 | 结论 |
|---|---|
| `fairness` | F-0005 · F-0006 · F-0010 · F-0011 |
| `methodology` | F-0007 · F-0009 · F-0013 · F-0018 · F-0019 · F-0020 · F-0024 |
| `predictability` | F-0008 |
| `prize_mechanism` | F-0002 · F-0004 · F-0015 · F-0016 · F-0017 · F-0022 · F-0023 |
| `probability` | F-0001 |
| `rules_scope` | F-0014 |
| `sales_external` | F-0012 |
| `structure_preference` | F-0003 · F-0021 · F-0025 |

## 按证据类型（引用时必看）

> `claim_type` 的判据不是『用了什么方法』，而是『**它会在什么情况下变错**』。与『类别』正交：类别说这结论属于哪一层，证据类型说它靠什么立住。

| 证据类型 | 失效方式 | 引用须知 | 结论 |
|---|---|---|---|
| `analytic` | 只有**模型定义**错了才会错 | 可当不变量用；但不可拿来『验证』统计结论（L8） | F-0001 |
| `empirical` | **数据换了 / 时段移位**就会错 | 引用前必看 `data_version` 与 `n_observations` | F-0003 · F-0005 · F-0006 · F-0008 · F-0009 · F-0010 · F-0011 · F-0012 · F-0013 · F-0015 · F-0016 · F-0019 · F-0021 · F-0023 · F-0025 |
| `simulation` | **模型假设**变了就会错 | 依赖输入参数；**禁止当作真值引用** | F-0004 · F-0017 · F-0022 |
| `documentary` | **官方规则文本**变了就会错 | 必须带 `rules_epoch`，脱离 epoch 无意义 | F-0002 · F-0014 |
| `methodological` | 关于**方法本身**的判断 | 不产效应量；价值全在 caveats 的失效边界 | F-0007 · F-0018 · F-0020 · F-0024 |

## 按置信度（引用时必看）

**★★★★★ 解析可证 / 精确枚举真值** — 可直接作为不变量依赖

`F-0001` `F-0002` `F-0010` `F-0014` `F-0015` `F-0016`

**★★★★☆ 强观测 + 多源交叉确认** — 可用，但须声明适用条件

`F-0003` `F-0005` `F-0006` `F-0008` `F-0009` `F-0011` `F-0012` `F-0013` `F-0018` `F-0019` `F-0020` `F-0023` `F-0024` `F-0025`

**★★★☆☆ 依赖模型的估计** — 可用作方向判断，**禁止当作真值引用**

`F-0004` `F-0017` `F-0021` `F-0022`

**★★☆☆☆ 弱迹象** — 不可引用

`（无）`

**★☆☆☆☆ 已推翻** — 禁止引用，仅作历史记录

`F-0007`

## 结论演化链

- `F-0007` ──被取代──> `F-0006`  （`F-0006.supersedes = F-0007`）
- `F-0015` ──被取代──> `F-0016`  （`F-0016.supersedes = F-0015`）

> **演化链是本仓库记忆的核心机制**：结论不被删除，而是带着血统被取代。
> 删除被推翻的结论会导致下一轮重复走同一条弯路。

## 自动提醒

以下结论**引用前必读 caveats**：

- **F-0004**（置信度仅 3/5）：在固定预算下避开连号形态，可提高『中奖时的期望奖金』—— 未计封顶的上界为 109%（后段口径）/121%（全样本口径），计入封顶后实测锚点
- **F-0007**（status=superseded; 置信度仅 1/5）：历史『2015 年断点』的结论是错的，正确切点为 2013-08
- **F-0015**（status=superseded）：【已修正】第 26113 期（2026-10-05）37 注一等奖的单注 239 万元，是自然摊薄结果，**并未触发** 1 亿元封顶（当期
- **F-0017**（置信度仅 3/5）：把 1 亿封顶纳入条件份额模拟后，避开连号的期望奖金提升由 121.48%（未计封顶）降为实测锚点下约 41.4%，且低注数情形下会被单注上
- **F-0021**（置信度仅 3/5）：撞号效应的弱化与 F-0006 的 2013-08 号码结构变点同期（滚动窗口 W=300/400/500 的数据驱动最优切点落在 2013
- **F-0022**（置信度仅 3/5）：把 F-0004 的校准口径从全样本 1.3603 改为后段 1.2472 后，未计封顶的收益上界由 121.5% 降为 109.4%，而含

---

## 新增结论的操作步骤

1. 在 `FACTS.jsonl` **末尾追加**（不要插在中间，便于 diff）
2. id 取当前最大编号 +1（**永不复用**）
3. `affects_win_probability` 必须为 `false`（红线，`validate` 会检查）
4. 若推翻旧结论：旧条 `status=superseded` + 填 `superseded_by`；新条填 `supersedes`。**双向必须一致**
5. `source` 必须是真实存在的文件路径；`evidence.script` 能复现
6. ★ 填 `claim_type` —— 判据是『**它会在什么情况下变错**』，不是『用了什么方法』。五选一：`analytic`（模型定义错才错）/ `empirical`（数据或时段变了就错） / `simulation`（模型假设变了就错）/ `documentary`（规则文本变了就错） / `methodological`（方法本身的判断）。填错会被 `validate` 按类型拒收
7. 跑 `python cli/main.py validate --facts` 确认无报错
8. 跑 `python cli/main.py index` 重新生成本文件
