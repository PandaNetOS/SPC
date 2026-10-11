# FINDINGS —— round12 研究结论

> **版本**：`1.0` ｜ 轮次 `r12` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 轮次：round12（L3 hold-out 落地轮）｜ 版本：1.0｜ 权威源 `VERSION_INDEX.md`
> 任务书：T-049（L3 组合优化时序 hold-out 评测实现 + 规则搜索 v1）/ T-030（策略有效性三档标准写入
> schema，Q-008）/ T-040（框架改进回写 framework/protocol/）

## 一、T-049 时序 Hold-Out 评测落地（→ F-0044，验收通过）

**问题**：r11 只做了 hold-out 评测设计（T-048），需要按设计落地实现评测脚本 + L3 规则搜索 v1
（T-048b → 更名 T-049，规避任务书生成器正则 `T-\d{3}` 对字母后缀 id 的漏解析）。

**方法**（严格按 `round11/T048_HOLDOUT_DESIGN.md` §2/§3/§4）：
- 后段 1973 期按时序切：训练 1183 / 验证 394 / 测试 396（切点 2021-07-10 / 2024-02-28）
- 规则池：随机 / R-001（run=0）/ R-003（run=0 且 max>=32）+ 候选形态（镜像对、等差、单开生日号区）
- 组合搜索 v1：验证窗枚举 6 个候选组合（均以 run=0 为基底）→ 选 expected_bonus_given_win 最高者；
  测试窗**只评估一次**
- cf = mean(w1|开出∈池)/mean(w1|全部)（实证口径，分母为全池均值）；expected_bonus_given_win 含
  1 亿封顶（口径同 F-0017：n0=6.0、派发额 0.4252 亿）；bootstrap B=2000 按期重抽样

**结果**（测试窗）：
| 规则 | 池占比 | cf | 预期奖金（封顶） |
|---|---|---|---|
| 随机 | 100% | 1.0000 | 708.7 万 |
| R-001（避连号） | 48.99% | 0.9531 | 743.5 万（+4.9%） |
| R-003（避连号+避生日号） | 22.98% | 0.8721 | 812.6 万（+14.7%） |
| **R001_norun_high_mirror（验证窗最优）** | 13.13% | 0.7819 | **906.4 万（+27.9%）** |

- bootstrap CI：R-001 [679.3, 822.4] 万、R-003 [701.6, 960.3] 万、R001_norun_high_mirror
  **[725.6, 1000.0] 万**（下界高于随机基线 708.7 万）
- 方向一致：验证窗 799.7 万 vs R-003 729.3 万；测试窗 906.4 vs 812.6 万 → 同向
- **验收 met=True**（测试窗提升 > R-003 基线 + CI 下界高于随机 + 方向一致）

**结论（F-0044）**：撞号避让规则组合的中奖时期望奖金存在样本外提升——R-001/R-003 获 **B 档
（统计确立）** 样本外确认；**镜像对为新的候选组合（R_new），尚未进入 strategy.json**（落地需
用户批准，策略变更红线）。概率红线不变：任何规则不改变各奖级中奖概率（一等奖恒 1/21,425,712）。

**踩坑序列**（r11 journal 的 schema 教训延续到本脚本）：
1. `_ROOT` 路径层级少一层（FileNotFoundError）→ 修正 `..`×5
2. CSV 列名是 `front_1..front_5 / back_1..back_2`（不是 n1/b1）→ KeyError
3. numpy bool 不可 JSON 序列化 → `bool()` 包裹
4. bootstrap_ci 初版只对两个基线算 CI，winner 无 CI → 泛化为全规则

## 二、T-030 策略有效性三档标准（Q-008 → answered）

**问题**：负期望游戏里什么算"有效策略"？标准不清会暗示不存在的价值（Q-008）。

**落地**（schema 1.4）：
- `strategy.schema.json` rules 条目新增必填 `effectiveness_grade`（A/B/C）+ `effectiveness_basis`：
  - **A 数学恒真**：解析可证无模型假设 → R-002（(1+m)/(K+m)）
  - **B 统计确立**：观测 + 样本外/测试窗验证 + 方向一致 → R-001、R-003（T-049 测试窗确认）
  - **C 模型估计/探索性**：依赖模型假设或样本有限 → 暂无规则落入
- `strategy.json` → schema_version 1.4，三规则档位回填
- `STRATEGY_GUIDE.md` → v1.8/r12，§2 新增三档表 + T-049 测试窗证据

## 三、T-040 框架改进回写 framework/protocol/

从 r11/r12 实践提炼回写 `ITERATION_PROTOCOL.md`：
- §6 校验清单扩展：概率口径自动派生扫描（.jsonl 逐条 JSON 只查 claim）、★S 策略文档随轮同步、
  deliverables 对象数组、schema 全字段必填
- §7 禁止事项新增 5 条：BOM 编码护栏（读/写统一 utf-8-sig）、策略文档版本落后策略更新轮、
  任务 id 用非纯数字（T-048b 教训）、versions.json 变更后必须跑 5 render + inject、
  deliverables 字符串列表

## 四、顺带根治与维护

1. **F-0004/F-0005 动态锚点重校准（r12 到期）**：E6 段（draw_num 26014-26115，102 期）重验
   ——一等奖中出注数中位数 **6.0**、总派发额中位数 **0.4252 亿**、max 0.9788 亿、触发 1 亿封顶
   **0 次** → F-0016/F-0017 锚点精确复现，F-0004/F-0005 **维持**（established_in → round12）。
2. **FACTS 44 条**（+F-0044）；Q-008 → answered（open 3→2：Q-006/Q-016）；TODO 三任务 → done。
3. **T-049 规则搜索框架可复用**：后续 L3 轮可直接扩展候选池/滚动 walk-forward。

## 五、遗留与下一轮入口

- **R_new（R001_norun_high_mirror）落地待用户批准**：若批准，入 strategy.json（新规则 R-004 +
  镜像对避让），并同步 STRATEGY_GUIDE/validate 机器规则
- T-025（E6 固定奖加成）仍 blocked（external-data）；T-032（摇奖设备）unverifiable
- F-0041 补强（三连号之外形态复验）仍可选
- 开放问题：Q-006 / Q-016（2 个）
