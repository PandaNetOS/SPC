# memory/facts/INDEX.md — 结论台账速览

> **本文件由 `cli/main.py index` 从 `FACTS.jsonl` 自动生成。请勿手工编辑。**
> 权威源是 `FACTS.jsonl`（每行一条，受 `spec/fact.schema.json` 约束）。

**当前状态**：15 条结论 | 14 established / 1 superseded | 生成日期 2026-10-10

---

## 全部结论

| id | 彩种 | 结论 | 状态 | 置信度 | 类别 | 轮次 |
|---|---|---|---|---|---|---|
| F-0001 | global | 任何选号方式都不能改变单注的中奖概率 | established | ★★★★★ | `probability` | round02 |
| F-0002 | dlt | 彩票是负期望游戏：现行返奖率 51%，每 2 元投注的长期数学期望回报约 1.02 元 | established | ★★★★★ | `prize_mechanism` | round02 |
| F-0003 | dlt | 连号形态（run>=2）的投注人群密度更高，撞号效应真实存在 | established | ★★★★☆ | `structure_preference` | round02 |
| F-0004 | dlt | 在固定预算下避开连号形态，可提高『中奖时的期望奖金』约 121% | established | ★★★☆☆ | `prize_mechanism` | round02 |
| F-0005 | dlt | 『开出率』与『被选中率』是两个不同的量，连号的开出率优势仅存在于早期且不可用 | established | ★★★★☆ | `fairness` | round02 |
| F-0006 | dlt | 前区号码分布存在结构变化，最优切点为 2013-08（χ²=185.0，在 234 个候… | established | ★★★★☆ | `fairness` | round02 |
| F-0007 | dlt | 历史『2015 年断点』的结论是错的，正确切点为 2013-08 | superseded | ★☆☆☆☆ | `methodology` | round02 |
| F-0008 | global | 开奖序列不可预测：所有 ML/时序模型在严格时间序列外推下 R² 均为负 | established | ★★★★☆ | `predictability` | round02 |
| F-0009 | dlt | 『组合冷热（heat）』对中奖注数没有稳健效应，历史报告的显著性为伪显著 | established | ★★★★☆ | `methodology` | round02 |
| F-0010 | dlt | 奇偶分布的偏离不显著：渐近卡方的 p<1e-6 是伪显著 | established | ★★★★★ | `fairness` | round02 |
| F-0011 | dlt | 后区与前区统计独立，后区号码不存在可利用的偏好结构 | established | ★★★★☆ | `fairness` | round02 |
| F-0012 | dlt | 销量存在星期效应（周六 > 周一/周三），但号码不存在星期效应 | established | ★★★★☆ | `sales_external` | round02 |
| F-0013 | dlt | 数据集的 18 组前区组合重复在随机碰撞的合理范围内，不是数据错误 | established | ★★★★☆ | `methodology` | round02 |
| F-0014 | dlt | 奖金规则已变更 6 次，跨 epoch 直接比较奖金金额会产生无意义结论；但号码结构（前… | established | ★★★★★ | `rules_scope` | round02 |
| F-0015 | dlt | 现行规则（2026-02-02 起）已实测触发『一/二等奖单期总额封顶 1 亿元』，单注… | established | ★★★★★ | `prize_mechanism` | round02 |

## 按类别

| 类别 | 结论 |
|---|---|
| `fairness` | F-0005 · F-0006 · F-0010 · F-0011 |
| `methodology` | F-0007 · F-0009 · F-0013 |
| `predictability` | F-0008 |
| `prize_mechanism` | F-0002 · F-0004 · F-0015 |
| `probability` | F-0001 |
| `rules_scope` | F-0014 |
| `sales_external` | F-0012 |
| `structure_preference` | F-0003 |

## 按置信度（引用时必看）

**★★★★★ 解析可证 / 精确枚举真值** — 可直接作为不变量依赖

`F-0001` `F-0002` `F-0010` `F-0014` `F-0015`

**★★★★☆ 强观测 + 多源交叉确认** — 可用，但须声明适用条件

`F-0003` `F-0005` `F-0006` `F-0008` `F-0009` `F-0011` `F-0012` `F-0013`

**★★★☆☆ 依赖模型的估计** — 可用作方向判断，**禁止当作真值引用**

`F-0004`

**★★☆☆☆ 弱迹象** — 不可引用

`（无）`

**★☆☆☆☆ 已推翻** — 禁止引用，仅作历史记录

`F-0007`

## 结论演化链

- `F-0007` ──被取代──> `F-0006`  （`F-0006.supersedes = F-0007`）

> **演化链是本仓库记忆的核心机制**：结论不被删除，而是带着血统被取代。
> 删除被推翻的结论会导致下一轮重复走同一条弯路。

## 自动提醒

以下结论**引用前必读 caveats**：

- **F-0004**（置信度仅 3/5）：在固定预算下避开连号形态，可提高『中奖时的期望奖金』约 121%
- **F-0007**（status=superseded; 置信度仅 1/5）：历史『2015 年断点』的结论是错的，正确切点为 2013-08

---

## 新增结论的操作步骤

1. 在 `FACTS.jsonl` **末尾追加**（不要插在中间，便于 diff）
2. id 取当前最大编号 +1（**永不复用**）
3. `affects_win_probability` 必须为 `false`（红线，`validate` 会检查）
4. 若推翻旧结论：旧条 `status=superseded` + 填 `superseded_by`；新条填 `supersedes`。**双向必须一致**
5. `source` 必须是真实存在的文件路径；`evidence.script` 能复现
6. 跑 `python cli/main.py validate --facts` 确认无报错
7. 跑 `python cli/main.py index` 重新生成本文件
