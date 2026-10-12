# HANDOFF —— round16（还债 + 重校准 + 任务源机制轮）

> **版本**：`1.0` ｜ 轮次 `r16` ｜ 更新 2026-10-12 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 1. 本轮结论清单

| 项 | 内容 | 证据 |
|---|---|---|
| T-066 | 7 条动态锚点重校准**全部维持** → NOOP 重记 + 刷新 `established_in` | 清 7 条重校准告警 |
| T-067 | `evidence_index` 补 F-0044~47（25 条）+ STRATEGY_GUIDE `consumes` 补 4 项（28 项） | 清 7 条结构性告警 |
| T-064 | **F-0048 新增**：H-002 三段检验 → 端点显著、序型不显著（`partial`） | bootstrap CI + 置换检验 p=0.2103 |
| T-068 | 新增 `tools/derive_tasks.py`（任务源派生），池子不再靠人工现想 | 新增 4 条派生候选 |
| T-069 | 修正 r15 对 T-020 的误判：产出一直是 F-0038，缺的是完成记录 | Q-006 → answered（15/15） |

数字：validate **106 → 110 项**，错误 0、**警告 0**（首次清零）；
测试 **467 → 496**（`test_derive_tasks.py` +11，`test_research_lib.py` 由 ERR 恢复 +18）；
FACTS **47 → 48 条**。

> 顺带修掉三处「写死计数」的测试：`test_claim_type` / `test_evidence_anchor` /
> `test_flywheel` 各自把 `len(FACTS) == 47` 写死，F-0048 一入库就红了 4 项。
> 已改为「台账只增不删 → 用下界」与「总数由 `FACTS.jsonl` 实读推导」。

## 2. 遗留

- **告警已清零** —— 这是本轮最实在的收尾：validate 现在 0 警告，
  意味着「告警清单即任务源」这条通道暂时为空（不是没有事做，是**欠账还完了**）。
- Q-016 / T-062 仍挂在 `external-data`；H-003 / T-065 为 `unverifiable` —— 都不可自行推进。
- H-001（T-063）是本轮**唯一**可自行推进的派生候选。

## 3. 下轮建议

1. **T-063（H-001 补剩余判据）**：唯一可自行推进项，且它是唯一可能
   **系统性枚举**高撞号形态的路径（比逐条试形态高效）。
2. 若要继续还债：告警已清零，需从别处找任务源 —— `labs/lottery/studies/dlt/memory/lessons/LESSONS.md`
   与 `platform/methodology/` 的待办项尚未纳入 `derive_tasks` 的扫描源。
3. 若想扩研究：Q-006 虽已答，但 F-0038/F-0048 都指出**逐号权重与连号形态可能共线**
   （未做 VIF 诊断）—— 这是把 F-0004 从 3★ 往上推的前置问题。

## 4. 未决

- **F-0048 的端点显著性很脆**（CI 下界 +0.0045，32-35 段仅 4 个号）。
  是否据此调整策略的生日号分段（例如从 `max≤31` 改为加权），**属策略变更，需用户批准**。
  本轮只做了结论入库，未动任何规则。
- `derive_tasks` 目前只扫 Q / H / validate 告警三处，是否扩展到 LESSONS 与
  methodology 待办，待定。

## 5. 风险

- **重校准的钥匙是 `established_in` 而不是 `recalibrated_roundNN`**。
  下一轮若只写重校准记录不刷新确立轮，告警会立刻回来。已写进 FINDINGS，
  但未写进 SOP 文档（本轮范围外）。
- 本轮装了 numpy/pandas/scipy/statsmodels（隔离环境）。若换环境跑，
  `test_research_lib.py` 与重校准脚本会再次 `ERR`。
