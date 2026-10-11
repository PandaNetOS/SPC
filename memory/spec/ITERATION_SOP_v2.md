# ITERATION_SOP_v2 —— 证据门控式迭代规范（v2.0）

> **版本**：`1.3` ｜ 轮次 `r07` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本文件是 SPC 自我迭代的 v2.0 操作规范：**记忆分层、入库门控、
> 矛盾双通道、一致性不变量、重校准与记忆压缩**。由 v1（`framework/protocol/ITERATION_PROTOCOL.md`）
> 按学术研究综合升级而来。最后更新：2026-10-11（round06）。

## 0. 设计依据（学术）

| 组件 | 学术来源 | 对应问题 |
|---|---|---|
| 三层信念基 | Reason Maintenance Systems（foundations-based：信念必须有有效 justification） | 派生结论无支撑自动失效 |
| 入库三闸门 | LSTM-MAS（arXiv 2601.11913）：filter / judge / manager 门控 | 错误累积与幻觉传播 |
| merge 操作 | TiM（arXiv 2311.08719）：insert / forget / merge | 同主题结论合并 |
| 矛盾双通道 | Katsuno & Mendelzon（1991）：Update ≠ Revision | 世界变了 vs 信念错了 |
| 证据置信度 | GRADE（Balshem 2011）+ AHRQ EPC 四域 | 结论需要置信度而非只有类型 |
| 增量一致性 | IncrConsist：原子操作 + 分层不变量（INV1/2/3） | 校验范围收敛到受编辑邻域 |
| 战略遗忘 | IterResearch（arXiv 2511.07327）、MEM1（arXiv 2506.15841） | 记忆无限膨胀 → 信噪比下降 |
| 禁止自欺 | Wright（arXiv 2506.17331）：不得断言内部自相矛盾 | 策略与证据脱节不可见 |

## 1. 三层信念基（L0 / L1 / L2）

| 层 | 内容 | 生命周期 | 引用规则 |
|---|---|---|---|
| **L0 锚点** | 数据文件哈希、后段切点（F-0006）、统一种子 20261011、规则 epoch | 不可变（变更即新版本） | 任何人不得修改 |
| **L1 观测结论** | FACTS.jsonl（claim + claim_type + confidence + source_sha256） | 可被 superseded / refuted（保留台账） | L2 只能引用 active 的 L1 |
| **L2 策略规则** | strategy.json R-001~003 + avoid_list | 需用户批准门 | 无有效 L1 支撑 → validate 报错 |

**核心纪律**：L2 不得引用 status ∈ {superseded, refuted} 的 L1（INV2）；L1 的
`source` 必须被 SHA256 锚定（内容漂移可检出）。

## 2. 原子操作（IncrConsist 五操作 → 本仓库四操作）

FACTS.jsonl 的一切变更必须通过以下**原子操作**之一，禁止整段重写：

| 操作 | 语义 | 触发的检查 |
|---|---|---|
| **Add** | 新增一条 F（新编号 F-XXXX，永不复用） | 三闸门（ingate.py）+ schema + claim_type |
| **Modify** | 修订一条 active F 的字段（口径/数字） | 证据摘要变化 → 下游 rehash 联动 |
| **Supersede** | 旧 F 标 superseded + superseded_by；新 F 立 | 双向一致 + 取代链无环（INV3） |
| **Merge** | 多条同主题 F 合成一条（TiM merge），被并入条标 superseded | 保留被并入 F 的 id（审计留痕） |

**禁止**：删除 F 条目；重用 F 编号；跳过 supersedes/superseded_by 双向声明。

## 3. 入库三闸门（`framework/tools/ingate.py`）

新结论进 FACTS 前逐闸过检（任一硬错误 → 拒绝；相似/疑似矛盾 → 降 tentative）：

1. **Filter 闸（冗余）**：与 active F 的 claim 关键词 Jaccard ≥ 0.6 → 提示重复或 merge。
2. **Judge 闸（检错）**：
   - claim_type 结构性约束（analytic 禁带 p/CI；empirical 必带 data_version + n_observations；
     simulation 必带 n_sim/rng_seed + ≥2 caveats；documentary 必带 rules_epoch；methodological 必带 caveats）
   - 数据口径：涉及数据一律后段口径（dlt_full_2933，F-0019）
   - 统计判据：empirical/simulation 必须有效应量（effect）+ CI/p
   - 矛盾检测：与同主题 active F 的互斥关键词 → 人工核验或走 revision
3. **Manager 闸（全局）**：新结论是否影响策略规则 evidence_refs；提示联动
   （rehash --strategy → validate --all → 版本 bump）。

退出码：0=入库；1=建议 tentative；2=建议拒绝。

## 4. 矛盾双通道（Katsuno & Mendelzon）

| 情形 | 通道 | 操作 | 记录 |
|---|---|---|---|
| 奖池 / E6 锚点 / 封顶 / n0 变化（世界变了） | **update** | 新结论标 `change_type: update`，旧结论**保留为历史**（不标错） | 触发重校准流程 |
| 新证据证伪旧结论（信念错了） | **revision** | 旧结论 superseded/refuted + superseded_by | 走取代链（INV3） |

`change_type` 枚举：`initial`（首立）/ `update`（世界变了）/ `revision`（信念错了）。
revision 必须落到 status ∈ {superseded, refuted}（validate 强制）。

## 5. 一致性不变量（INV1 / INV2 / INV3）

| 不变量 | 含义 | 落地 |
|---|---|---|
| **INV1 局部模式** | 每条 F 字段合法（schema + claim_type + grade/change_type 枚举） | validate_facts（check_v2_fields） |
| **INV2 引用链** | 引用的 F 必须存在且 active（策略不得建立在被推翻结论上） | validate_strategy（evidence_refs 升级） |
| **INV3 全局互斥** | 取代链无环；superseded 双向一致 | validate_facts（check_supersede_cycles） |

规模增长后，校验可从全量 `validate --all` 收敛为**增量**（只检查受编辑影响
的 provenance 邻域，IncrConsist 的 1660× 加速思路）；当前 32 条规模全量即足够。

## 6. 动态锚点重校准（update 通道）

- 动态锚点类结论（F-0004/0005/0016/0017/0022/0023/0028/0029/0031）标
  `recalibrate_every: 5`（每 5 轮重验奖池/封顶/锚点数值）。
- validate 按 `established_in + N` vs 当前轮报 warning；`compress_memory.py` 也列出到期项。
- 到期处理：① 数值仍成立 → 维持并重记；② 变了 → 走 update（change_type=update，旧记录保留）。

## 7. 记忆压缩（每 5 轮一次，`framework/tools/compress_memory.py --write`）

- 只读 + 生成视图，**不移动/不删除数据**（审计留痕优先）。
- 产物：`memory/facts/ACTIVE.md`（当前有效结论清单，与台账分离解决信噪比）
  + merge 候选（同 category+claim_type ≥3 条）+ 到期清单。

## 8. 收尾清单（每轮必过）

1. 三闸门通过的新结论才允许 Add；
2. `python cli/main.py rehash --strategy`（FACTS 变更后证据摘要重算）；
3. `python cli/main.py validate --all` —— **全部通过**（含结构完整性两项）；
4. 四件套（FINDINGS / HANDOFF / manifest / journal）落地；
5. versions.json 登记 + VERSION_INDEX 重渲染 + README 计数同步；
6. **结构完整性（P1-2 根治）**：新增文件必须登记 versions.json
   （validate `check_structure` 双向比对强制）；README 目录树为**派生物**——
   先 `python tools/render_readme_tree.py --write` 再提交，**禁止手改目录树**；
7. 涉及代码/配置/策略 → 用户批准门后才提交推送（仅 main 单分支）。
8. **下游增强性更新检查**：本轮 FACTS 新增结论后，检查被引用的下游文档
   （STRATEGY_GUIDE / strategy.json / AI_CONTEXT 等）是否需要**增强性更新**
   （证据升级、口径注记、表述精确化）—— 增强型证据不会自动触发版本 bump，
   需要人工确认并同步 bump；正文新增 `F-xxxx` 引用时，同步登记 consumes
   （validate 逆向检查会拦截遗漏，见 `src/spc/validate.py::_check_consumes_completeness`）。
9. **统一注入版本行**：所有渲染（render_readme_tree / render_version_index /
   render_ai_map / render_flywheel_health / render_dependency_map --write）之后，
   运行 `python tools/inject_version_lines.py --write` 把登记版本统一写进各文档头部。
   **版本行一律由注入器/生成器从 versions.json 写，禁止手写**；改了登记就重跑注入，
   validate 的版本一致性检查会拦截漏跑（`src/spc/versions.py`）。
