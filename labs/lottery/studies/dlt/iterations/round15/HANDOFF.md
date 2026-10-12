# HANDOFF —— round15（轮次号与待办状态双源治理轮）

> **版本**：`1.0` ｜ 轮次 `r15` ｜ 更新 2026-10-12 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 1. 本轮结论清单

| 项 | 内容 | 证据 |
|---|---|---|
| T-057 | dry-run 不再建目录（`makedirs` 移入 `--write`） | `tools/render_task_brief.py`；回归测试已守 |
| T-058 | 轮次号只认已收尾轮（新增 `delivered_round_dirs`） | 重校准警告 7 轮 → **真实的 5 轮**；轮号 round16 → **round14** |
| T-059 | ★R 轮次号双源对账（`current_iteration` == 最新已收尾轮） | `src/spc/validate.py` |
| T-060 | ★T 已落地任务必须勾选 + T-052 对齐 | 新增检查项**当场抓出 T-052** |
| T-061 | 无可执行候选时不得把资源缺口型提升为必做 | `_render_brief` 降级路径 |

数字变化：validate **104 → 106 项检查**（新增 ★R/★T 两条 OK），错误 0；
测试 **456 → 464**（新增 `tests/test_round_counter_sync.py` 11 项），
并连带修好 `test_ai_readability` 2 项、还原 `test_flywheel` 1 项。

## 2. 遗留问题

- **待办池枯竭（结构性）**：可执行候选 = 0，剩余 T-025（`external-data`）/
  T-032（`unverifiable`）均不可自行推进。**这不再是记账问题，是任务源问题**。
- **validate 15 条警告未清**：8 条 FACT 超期重校准 + `evidence_index` 未覆盖
  F-0044~F-0047 + 6 条 STRATEGY_GUIDE `consumes` 未登记（本轮范围外）。
- **T-020 存疑未裁定**（见下）。

## 3. 下轮建议

按「不依赖外部数据」优先排序：

1. **B2 还债**：补 `evidence_index` 的 F-0044~F-0047 + STRATEGY_GUIDE 的
   `consumes` 登记 → 清 7 条结构性警告。零外部依赖，纯机械。
2. **B1 重校准**：8 条超期 FACT 走 `update` 通道核验奖池/封顶/锚点。
   需回读开奖数据，量中等。
3. **B3 新研究**：Q-006 逐号偏好向量（`prize2_winners` 全量回归）——
   唯一能提升 F-0004 置信度的路径，但工作量大。
4. **任务源机制**：待办池需要一个「从 OPEN_QUESTIONS / HYPOTHESES / validate 警告
   派生新任务」的通道，否则每轮都要靠开轮侦察现想。

## 4. 未决

- **T-020 状态矛盾（需用户裁定）**：`TODO.md` 标 `[x]`，但
  ① round08 manifest `actual_updates` 记「T-020 → done」、**同一轮 HANDOFF 却把
  T-020 列在下轮 TODO**；② 本条无 `✅ rXX 完成 → F-xxxx` 记录（与其余已完成项格式不符）；
  ③ Q-006 至今 `open`，F-0004 置信度仍 ★★★☆☆。
  即「已勾选」与「产出落地」不一致。本轮**只在 TODO 加标注、未改勾选状态** ——
  需判定是「r08 提前勾错（应回退 `- [ ]`）」还是「做了但未入库（应补 F-xxxx 与 Q-006 → answered）」。

## 5. 风险

- ★R 引入了新的**顺序约束**：`bump_iteration` 必须在 `roundNN/manifest.json`
  写完之后跑，否则 `current_iteration` 会领先最新已收尾轮而报错。
  本轮已按此顺序执行（先四件套、后 bump）。SOP 文档待同步此约束。
- `tests/test_research_lib.py` 因环境缺 `numpy` 无法运行（与本项目改动无关），
  `count_tests` 记为 `ERR`。
