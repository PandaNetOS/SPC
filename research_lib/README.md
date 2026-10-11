# research_lib —— 研究资本化方法库（Y 方向）

> 把历史轮次脚本里反复使用的统计原语提炼为**彩种无关**的可复用模块。
> 新任务的研发出「重写脚本」变成「组合原语」—— 每轮不仅产出结论，还产出方法资产（研究复利）。

## 使用纪律（必须遵守）

1. **彩种无关**：本库禁止 import dlt 数据、`games/` 任何路径、具体彩种常量。数据由调用方传入。
2. **种子显式**：所有重抽样函数默认 `seed=20261011`（L0 统一种子），调用方可覆盖，结果必须可复现。
3. **CI 用分位数**：percentile bootstrap，不用 CLT 正态近似（重尾分布下不可靠，见 STATISTICAL_DISCIPLINE.md）。
4. **样本不足不硬报**：任一段为空 / 分母为 0 → 返回 None / `unknown`，禁止勉强报显著（T-046 三态判定精神）。
5. **来源可追溯**：新结论引用本库原语时，结论的 `evidence.script` 可指向调用脚本，`caveats` 里注明原语来源（见下映射表）。

## 原语清单与来源映射

| 原语 | 位置 | 来源脚本 | 历史验证结论 |
|---|---|---|---|
| `ratio_and_boot` | `stats.py` | `round03/scripts/b2_split_stability.py`（F-0003 同口径估计器） | F-0003：一等奖注数比 1.3603 [1.1298, 1.6292] |
| `bootstrap_ci` | `stats.py` | `b2_split_stability.py` / `cap_adjusted_uplift.py`（通用重采样） | 与 ratio_and_boot 同源 |
| `wilson_interval` | `stats.py` | T-046 方法纪律（文献 27/28/29，比例类首选） | 用于 R-002 量化的比例判据 |
| `split_ratio_stability` | `stability.py` | `b2_split_stability.py`（分期稳健性，Q-001 清偿） | F-0003 分期：前段 2.1072 / 后段 1.2472，符号一致但衰减（0.592） |
| `ci_overlap` | `stability.py` | `b2_split_stability.py::ci_overlap`（幅度差异显著性） | 两段 CI 不重叠 → 衰减统计显著 |

## 为什么不把「条件份额模拟」也提炼进来

`simulate_conditional_share`（F-0004 核心）依赖 dlt 专用模型参数（人群权重 α、生日号权重、
E6 池锚点、封顶逻辑）—— 参数化后即是几个公式的排列，抽象收益低且易引入口径偏差。
处置：作为 dlt 专用流程保留在轮次脚本（`round05/scripts/bet_structure.py`），
其公式已文档化于 `F-0004` / `strategy.json` / `STRATEGY_GUIDE.md`。本库只提炼**真正跨任务复用**的统计骨架。

## 新增原语的流程（研究资本化的闭环）

1. 新轮次脚本里出现「第二次复用」的统计逻辑 → 提炼进本库并补测试；
2. 本 README 映射表登记：原语 → 来源脚本 → 历史验证结论；
3. 原语经 `tests/test_research_lib.py` 守住（构造已知分布验证，不依赖真实数据）。
