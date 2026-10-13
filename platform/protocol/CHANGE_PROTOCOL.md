# CHANGE_PROTOCOL.md — 框架层与实验室层迭代协议

> **版本**：`1.0` ｜ 轮次 `r19` ｜ 更新 2026-10-13 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本文件定义**框架层（`platform/`）**与**实验室层（`labs/<domain>/`）**的变更生命周期。
> 它与 `ITERATION_PROTOCOL.md` 互补：后者定义**研究组层**的一轮（`studies/<game>/iterations/roundNN/`），
> 本文件定义**跨研究组的供给方**如何演进。
>
> **一句话**：研究组是「消费方」，框架/实验室是「供给方」。消费方发现不够用就**提需求单**，
> 不能自己改供给；供给方改动必须经过「对全部已有研究组零破坏」的契约测试才放行。

---

## 0. 三层定位（与 ITERATION_PROTOCOL 的分工）

| 层 | 仓库位置 | 通用性 | 迭代制度 | 节奏由什么决定 |
|---|---|---|---|---|
| **框架** | `platform/` | 彩种无关 | **变更提案制**（本文 §2） | 事件驱动，破坏性变更升 major |
| **实验室** | `labs/<domain>/`（如 `labs/lottery/`） | 跨彩种通用 | **能力里程碑制**（本文 §3） | 领域里程碑 |
| **研究组** | `studies/<game>/` | 单一彩种 | **轮次制** `roundNN`（ITERATION_PROTOCOL） | 快，几天一轮 |

**依赖方向（单向，能力向下流）**：研究组 → 实验室 → 框架。
**提案方向（向上提）**：研究组/实验室发现上层缺口 → 提 Change Proposal / Capability Proposal。

> ⚠️ 研究组轮次**不得**直接修改 `platform/` 或 `labs/<domain>/` 的契约/代码。
> 其 `manifest.json` 的 `framework_revision` 字段**只许引用、不许实现**上层提案
> （见 §5 与研究组 manifest 升级）。

---

## 1. 版本坐标（三轴解耦，已在 `versions.json` 落地）

| 轴 | 字段 | 含义 | 谁升 |
|---|---|---|---|
| `project_version` | `pyproject.toml` 的 `project.version` | 发布给用户用的整体版本 | 发布时 |
| `framework_version` | `versions.json.framework_version` | **框架层**演进（platform/） | 框架提案实现后 |
| `domain_version` | `versions.json.domain_version` | **实验室层**演进（labs/<domain>/） | 能力里程碑达成后 |
| `current_iteration` | `versions.json.current_iteration` | 研究组当前轮次 | 研究组收尾后 |

校验器在 `validate --versions` 中核对 `project_version == pyproject`；
**新增**校验（§4）：研究组 manifest 引用的 `framework_version` / `domain_version`
必须 ≤ `versions.json` 中已发布的值，否则 FAIL（跨层版本契约）。

---

## 2. 框架层 = 变更提案制（Change Proposal）

### 2.1 生命周期

```
proposals/CP-XXX.md          # 提案（不进 roundNN/）
   ↓ RFC + 影响面分析
评审（破坏性 → 升 framework_version major + 写迁移说明）
   ↓ 实现（在 platform/ 落地）
跨研究组契约测试（§4 闸门口）   # 全绿才放行
   ↓
framework_version 提升 + versions.json 登记 + PROPOSALS.md 记状态
   ↓
对所有研究组开放引用
```

### 2.2 提案文档形状（`proposals/CP-XXX.md`）

| 节 | 内容 |
|---|---|
| 动机 | 哪个研究组/实验室的哪次实践暴露了缺口 |
| 影响面 | 破坏哪些契约（schema / strategy / 跨研究组 API） |
| 破坏性判定 | 是 → 升 major；否 → 升 minor |
| 迁移说明 | 破坏性变更必须写：旧消费者怎么改 |
| 契约测试清单 | 要在 §4 闸门口跑哪些测试（含影子彩种反泄漏） |

### 2.3 闸门：跨研究组契约测试

框架改动**放行前**必须全绿：

1. `tests/test_shadow_game.py` 铁律扫描：`platform/` 与 `src/` **无**研究组痕迹（AST 剥 docstring 防误报），且扫描器自检确认非「永远全绿」。
2. 全部 `validate --all` 通过（含 `validate --versions` 的框架版本对账）。
3. 若改了 schema：既有研究组 manifest 仍能被新 schema 接受（向后兼容）或已在迁移说明中列清。

> 这是框架层的「硬标准」：**改动不得让任何已有研究组悄悄挂掉**。

---

## 3. 实验室层 = 能力里程碑制（Capability Milestone）

### 3.1 什么算「实验室能力」

`labs/<domain>/` 中**跨研究组复用**、且**不绑定单一彩种**的能力
（如彩票域的「奖池/封顶/派发通用分析器」「形态库」）。
写在某个 study 内部、只被它自己用的，不算——那是研究组的私货。

### 3.2 晋级判据（复用现有「影子彩种验证通用性」硬标准）

> **一个能力只有被第二个研究组/彩种用上，才够格进实验室层。**

单 study 自用的通用代码，留在 `research_lib/` 或 study 内部；
一旦第二个 study 需要它，就抽到 `labs/<domain>/` 并记一个能力里程碑。

### 3.3 里程碑文档（`labs/<domain>/CAPABILITIES.md`）

| 字段 | 说明 |
|---|---|
| 能力名 | 如 `payout_analyzer` |
| 提供方 | 哪个 study 首次沉淀 |
| 复用方 | 哪些 study 已引用（≥2 才登「实验室级」） |
| `domain_version` 触发点 | 达成复用时提升 `domain_version` |
| 契约测试 | 该能力被引用时的回归测试 |

---

## 4. 跨层契约闸门（新增校验，接 `validate --all`）

落点：`src/spc/validate.py` 新增 `_check_cross_layer_contract(root, rep)`。

检查项：

1. **研究组 manifest 只引用、不实现上层提案**
   若 `studies/<game>/iterations/roundNN/manifest.json` 的 `framework_revision.proposed`
   指向 `platform/` 代码改动（而非引用某个已 `accepted` 的 `CP-XXX`），FAIL。
2. **版本上限契约**
   研究组 round 若声明 `uses_framework_version` / `uses_domain_version`，
   其值必须 ≤ `versions.json.framework_version` / `domain_version`，否则 FAIL。
3. **影子彩种零交集**（框架/实验室改动后跑）
   `tests/test_shadow_game.py` 铁律扫描必须绿；扫描器自检必须表明它真能报错（非空绿）。
4. **schema 向后兼容**
   改了 `spec/*.schema.json` 时，既有研究组 manifest 仍被接受，或迁移说明已列清。

> 判据同 ★R 风格：**不是「有没有 warning」，而是「每个跨层引用都有契约背书」**。

---

## 5. 与研究组迭代的衔接

- 研究组收尾（`ITERATION_PROTOCOL` §4）时，`manifest.framework_revision` **只填引用**：
  `proposed/accepted/rejected` 列表填 `CP-XXX` / 能力名，**不得**内含对 `platform/` 的具体代码 diff。
- 上层提案**实现并提升版本后**，研究组下一轮才能把 `uses_framework_version` 升到该值。
- 这把「研究组顺手改框架」的 P4 黑盒，变成了一条**可评审、可回滚、有契约测试**的供给链。

---

## 6. 禁止事项

| 禁止 | 理由 |
|---|---|
| 研究组 round 直接改 `platform/` 或 `labs/<domain>/` | 破坏性变更不该挂在某个彩种的 roundNN 上 |
| 框架破坏性变更不升 `framework_version` major | 消费者无法感知契约断裂 |
| 框架/实验室改动未经 §2.3 / §4 闸门就合并 | 可能让已有研究组静默挂掉 |
| 单 study 私货冒充实验室能力 | 污染「跨研究组通用」的语义 |
| 提案文档写进 `roundNN/` | 框架/实验室的演进不属于任何单一研究组 |

---

## 7. 最后一条

> **三层迭代的节奏，应该跟着「变更的影响半径」走，而不是都按研究组的快节奏跑。**
> 影响半径越大，闸门越硬、版本越重、回滚越慎。
> 跨层契约测试，是三层之间唯一的硬闸门。
