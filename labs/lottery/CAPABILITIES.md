# CAPABILITIES.md — 实验室层（彩票域）能力里程碑台账

> **版本**：`1.0` ｜ 轮次 `r19` ｜ 更新 2026-10-13 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本台账是 `CHANGE_PROTOCOL.md §3.3` 规定的「实验室层能力里程碑文档」。
> 它登记 `labs/lottery/` 下**跨研究组复用、且不绑定单一彩种**的能力。
> 晋级判据（§3.2）：**一个能力只有被第二个研究组/彩种用上，才够格进实验室层。**
> 状态：`candidate`（单研究组沉淀）/ `shared`（≥2 研究组复用，晋升实验室级）/ `deprecated`。

## 当前 `domain_version`：`0.1`

> 初始值：r19 建立实验室层版本轴，尚未有跨研究组复用达成，故能力均处 `candidate`。

---

## 能力清单

### C-001 `payout_analyzer` — 奖池 / 封顶 / 派发通用分析器

| 字段 | 值 |
|---|---|
| 提供方 | DLT `labs/lottery/studies/dlt/iterations/round04/`（T-030/T-049 等） |
| 复用方 | 仅 DLT（截至 r19） |
| 状态 | `candidate` |
| 沉淀位置 | `labs/lottery/studies/dlt/strategy/`、round04 脚本（`prize_mechanism_tobit.py` 等） |
| `domain_version` 触发点 | 第二个彩种接入并复用该分析器时 → 升 `0.1 → 0.2`，状态转 `shared` |
| 契约测试 | 被引用时需回归：奖级口径按 `rules_epoch` 分段、封顶 Tobit 建模（见 `E8`） |

> 注：该能力目前写在 DLT study 内部 / `research_lib/`，尚未抽到 `labs/lottery/` 顶层。
> 达到 `shared` 时应将其抽到 `labs/lottery/payout/` 并登记为实验室级能力。

### C-002 `shape_library` — 形态库（和值 / 跨度 / 连号 / 奇偶 / 大小 / 三区）

| 字段 | 值 |
|---|---|
| 提供方 | DLT `labs/lottery/studies/dlt/iterations/round05/`（T-053）、round14 |
| 复用方 | 仅 DLT（截至 r19） |
| 状态 | `candidate` |
| 沉淀位置 | `research_lib/` 原语 + DLT 派生集 `02_derived/04_structure_distribution_exact.json` |
| `domain_version` 触发点 | 第二个彩种复用形态统计（精确枚举理论分布）时 → 升 `0.2`，状态转 `shared` |
| 契约测试 | 被引用时需回归：号码结构理论分布（精确枚举）与各彩种实际分布比对 |

---

## 晋级流程（从 `candidate` 到 `shared`）

1. 第二个研究组/彩种在其实例中需要该能力（证明「跨研究组通用」非臆测）。
2. 将代码从 study 内部 / `research_lib/` 抽到 `labs/lottery/<capability>/`。
3. 在 `versions.json` 提升 `domain_version`（并记录 history），本台账该条状态转 `shared`。
4. 在 `proposals/PROPOSALS.md` 的「实验室层能力里程碑」表增补一行登记。
5. 跑 `tests/test_shadow_game.py` 铁律扫描，确认抽离不泄漏进 `platform/`。
