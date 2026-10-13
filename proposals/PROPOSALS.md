# PROPOSALS.md — 框架层 / 实验室层 变更提案台账

> **版本**：`1.1` ｜ 轮次 `r19` ｜ 更新 2026-10-13 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本台账登记所有 `proposals/CP-XXX.md`（框架层变更提案）与 `labs/<domain>/CAPABILITIES.md`
> 中的能力里程碑（实验室层）。它是 `CHANGE_PROTOCOL.md §2.1` 规定的「状态登记处」。
> 提案范本见 `proposals/CP-001.md`（即本轮三层迭代架构迁移的回写）。

## 框架层变更提案（Change Proposals）

| 编号 | 标题 | 类别 | 破坏性 | 状态 | 版本影响 | 落地轮次 |
|---|---|---|---|---|---|---|
| [CP-001](CP-001.md) | 三层迭代架构迁移纳入提案制 | 框架层（protocol + schema + 闸门） | 否（纯增量） | `implemented` | `framework_version` 维持 1.1；`domain_version` 0.1 初建 | r19 |
| [CP-002](CP-002.md) | 数据自备能力：数据需求前置 + 自取数据接入管道 | 框架层（protocol + 管道 + schema） | 否（纯增量） | `accepted` | `framework_version` 计划 1.1→1.2；新增 §2.4 数据需求契约 | r19 |

> 状态取值（与 `versions.json` status 风格一致）：`proposed` / `accepted` / `implemented` / `rejected` / `superseded`。
> 破坏性提案实现时须升 `framework_version` major（实验室层能力里程碑达成时升 `domain_version`）。

## 实验室层能力里程碑（Capability Milestones）

> 实验室能力的「晋级判据」见 `CHANGE_PROTOCOL.md §3.2`：**一个能力只有被第二个研究组/彩种用上，才够格进实验室层**。
> 当前彩票域只有一个已接入研究组（DLT），故下表「是否已晋级实验室级」均暂为「否（待第二研究组复用）」。
> 详细字段台账见 `labs/lottery/CAPABILITIES.md`。

| 能力 | 提供方 | 复用方 | 是否已晋级实验室级 | 备注 |
|---|---|---|---|---|
| `payout_analyzer`（奖池/封顶/派发通用分析器） | DLT r04 | 仅 DLT | 否（待第二彩种） | 候选；达成复用即升 `domain_version` |
| `shape_library`（形态库） | DLT r05/r14 | 仅 DLT | 否（待第二彩种） | 候选；见 `labs/lottery/CAPABILITIES.md` |
