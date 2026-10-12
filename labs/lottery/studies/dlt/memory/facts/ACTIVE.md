# 当前有效结论清单（ACTIVE VIEW）

> 由 `platform/tools/compress_memory.py --write` 生成 ｜ 当前轮 round12 ｜ 权威源 `labs/lottery/studies/dlt/memory/facts/FACTS.jsonl`（台账保留全部历史，本视图只列可用结论）

| F-id | 结论 | 类型 | 置信度 | 变更通道 | 重校准 | 确立轮 |
|---|---|---|---|---|---|---|
| F-0001 | 任何选号方式都不能改变单注各奖级的中奖概率（一等奖 1/21,425,712；任一奖级合计约 1/15；均解析可证） | analytic | high | initial | - | round02 |
| F-0002 | 彩票是负期望游戏：现行返奖率 51%，每 2 元投注的长期数学期望回报约 1.02 元 | documentary | high | initial | - | round02 |
| F-0003 | 连号形态（run>=2）的投注人群密度更高，撞号效应真实存在 | empirical | high | initial | - | round02 |
| F-0004 | 在固定预算下避开连号形态，可提高『中奖时的期望奖金』—— 未计封顶的上界为 109%（后段口径）/121%（全样本口径），计入封 | simulation | moderate | initial | 5 轮 | round12 |
| F-0005 | 『开出率』与『被选中率』是两个不同的量，连号的开出率优势仅存在于早期且不可用 | empirical | high | initial | 5 轮 | round12 |
| F-0006 | 前区号码分布存在结构变化，最优切点为 2013-08（χ²=185.0，在 234 个候选中排名第 1），且为渐变过程 | empirical | high | initial | - | round02 |
| F-0008 | 开奖序列不可预测：所有 ML/时序模型在严格时间序列外推下 R² 均为负 | empirical | high | initial | - | round02 |
| F-0009 | 『组合冷热（heat）』对中奖注数没有稳健效应，历史报告的显著性为伪显著 | empirical | high | initial | - | round02 |
| F-0010 | 奇偶分布的偏离不显著：渐近卡方的 p<1e-6 是伪显著 | empirical | high | initial | - | round02 |
| F-0011 | 后区与前统计独立（互信息 0.203 < 置换基准 0.209），后区号码的『开出率』均匀；但这**不等于**后区人群偏好均匀  | empirical | high | initial | - | round02 |
| F-0012 | 销量存在星期效应（周六 > 周一/周三），但号码不存在星期效应 | empirical | high | initial | - | round02 |
| F-0013 | 数据集的 18 组前区组合重复在随机碰撞的合理范围内，不是数据错误 | empirical | high | initial | - | round02 |
| F-0014 | 奖金规则已变更 6 次，跨 epoch 直接比较奖金金额会产生无意义结论；但号码结构（前区35选5+后区12选2）自 2007  | documentary | high | initial | - | round02 |
| F-0016 | 现行规则（E6，>=26014 期）下『一等奖单期总额封顶 1 亿元』条款从未触发：102 期一等奖总额最大值仅 0.9788  | empirical | high | initial | 5 轮 | round09 |
| F-0017 | 把 1 亿封顶纳入条件份额模拟后，避开连号的期望奖金提升由 121.48%（未计封顶）降为实测锚点下约 41.4%，且低注数情形 | simulation | moderate | initial | 5 轮 | round09 |
| F-0018 | F-0003 的撞号效应不依赖均值比：中位数比 1.5 [1.5, 2.0] 与均值比同向，且截尾检验显示重尾仅贡献 1.72% | methodological | high | initial | - | round03 |
| F-0019 | 2013-08 之前那段数据在『号码分布—中出注数—销售额』三者间不自洽：前区号码分布严重偏高端（χ²=251.5，P(前区全部 | empirical | high | initial | - | round04 |
| F-0020 | F-0003 的分期『衰减过半』是估计量依赖的：均值比口径给出 post/pre = 0.592（w1）/ 0.498（w2）， | methodological | high | initial | - | round04 |
| F-0021 | 撞号效应的弱化与 F-0006 的 2013-08 号码结构变点同期（滚动窗口 W=300/400/500 的数据驱动最优切点落 | empirical | moderate | initial | - | round04 |
| F-0022 | 把 F-0004 的校准口径从全样本 1.3603 改为后段 1.2472 后，未计封顶的收益上界由 121.5% 降为 109 | simulation | moderate | initial | 5 轮 | round09 |
| F-0023 | 在可观测的一/二等奖派发口径下不存在稳健的『高期望期』：全局期初奖池分位 top−bottom 的每元期望派发差 +0.090  | empirical | high | initial | 5 轮 | round09 |
| F-0024 | 用『派发额/销售额』(r_t) 衡量择时价值会误判：E4 段剔除 2019 后 r_t 仍随奖池显著上升（+0.067）而每元期 | methodological | high | initial | - | round04 |
| F-0025 | 后区撞号结构存在但不可靠可利用：后区 66 对的『被选中率』强烈非均匀（过散布 8.72×，MC p<1e-4；最热对/最冷对密 | empirical | high | initial | - | round04 |
| F-0026 | 单注、复式、胆拖、倍投、追加五种投注方式在『每元期望回报率』上数学等价（都落在 51% 返奖率内）：复式=组合展开、胆拖=拖码组 | analytic | high | initial | - | round05 |
| F-0027 | 『买 K 注完全相同的号码』会自我摊薄：若中奖，K 注同时命中一等奖、总奖金被 K 份瓜分，每元期望回报比 = (1+m)/(K | analytic | high | initial | - | round05 |
| F-0028 | R-002 判定的『结构同构』（gap 向量相同但号码不同）不改变期望奖金：10 注同构 vs 10 注分散的期望撞号差 +0. | simulation | moderate | initial | 5 轮 | round10 |
| F-0029 | 同时避开连号（run>=2）与生日号区（max<=31）的覆盖，条件撞号系数由随机基线 1.005 降至 0.425（仅避开连号 | simulation | moderate | initial | 5 轮 | round10 |
| F-0030 | 撞号效应的星期交互方向与 H-005 假设相反：后段控制销量后 run×周六 交互显著为负（w1 −0.268，p=0.039； | empirical | moderate | initial | - | round05 |
| F-0031 | 期初奖池序列高度可预测：后段 AR(1) 斜率 0.9994（SE 0.0006）、ACF lag1-3 均 ≈ 1.0（奖池几 | empirical | high | initial | 5 轮 | round10 |
| F-0033 | 前段（<2013-08）数据不自洽的根因进一步定位：注数-销售额异常区间为 2008-01~2013-08（2007 全年正常， | empirical | moderate | initial | - | round07 |
| F-0034 | 本地 CSV 前段数据与外部独立公开源（500.com 历史库，转载自官方开奖公告）102/102 期完全一致（2008 年 4 | empirical | moderate | initial | - | round07 |
| F-0035 | 节假日窗口无『连号撞号减弱』证据：春节（农历精确映射正月初一±7天）后段连号注数比 1.005、国庆 1.010、元旦 1.00 | empirical | moderate | initial | - | round07 |
| F-0036 | 全奖级口径下 P(任中)=0.019572（1/51.1，419335/21425712），比现行口径隐含的 4.6673e-0 | analytic | high | initial | - | round08 |
| F-0037 | R-002（禁止完全相同号码）的期望修复增益完成实证量化：m（外部同号注数）取后段一等奖中出注数经验分布（中位 3、均值 4.8 | empirical | high | initial | - | round09 |
| F-0038 | 逐号偏好结构真实存在但精细度高于『生日段』假设：后段逐号相对撞号强度 S_j（1.0=无偏好）在号码间有明显分异（如 9/11/ | empirical | moderate | initial | - | round09 |
| F-0039 | 大乐透现行（E6）9 个奖级的中奖概率精确值：一等奖 5+2 为 1/21,425,712（≈4.67e-08）；任一奖级（1- | analytic | high | initial | - | round10 |
| F-0040 | 销量是内生变量但**不驱动一等奖中出注数**：Granger 检验（后段 1973 期，一阶差分口径）奖池→销量显著（滞后 1- | empirical | moderate | initial | - | round10 |
| F-0041 | 『随机性错觉』形态的撞号溢价仅存在于三连号（等差 1）：期含三连号撞号比 1.1287（CI [1.0351, 1.2243]） | empirical | moderate | initial | - | round10 |
| F-0042 | 后段内部（2013-08-28 起）连号撞号效应进入平台期：滚动窗口 W=300/500 下 R_run 趋势均不显著（slop | empirical | moderate | initial | - | round11 |
| F-0043 | 机选占比的可观测代理成立：连号一等奖注数比 R_run 显著变点（p=0.0005，切点 2015-04，1.231→1.009 | empirical | moderate | initial | - | round11 |
| F-0044 | 时序 hold-out（后段 1973 期 60/20/20，测试窗 396 期只评估一次）实测撞号避让组合的中奖时期望奖金样本 | empirical | moderate | initial | - | round12 |

## 动态锚点待重校准（update 通道）
- 无到期项。
