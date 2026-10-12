# TASK_BRIEF —— round15 任务书

> **版本**：`1.0` ｜ 轮次 `r15` ｜ 更新 2026-10-12 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本任务书由 `tools/render_task_brief.py` 从 TODO 待办池按价值评分生成
> （派生物草稿，人工确认后可改）。本轮必做 **0** 个（`--top 3` 可调）。
> 评分依据：TODO 条目 value / P 级 / ★首推。

## 本轮候选（按评分排序 TOP-N）

| 排序 | 任务 | 优先级 | 评分 | 说明 |
|---|---|---|---|---|
| — | （无可执行候选） | — | — | 待办池已无非资源缺口型条目 |

## 本轮必做任务（引用 TODO 原条目）

**本轮无可执行的非资源缺口任务。** 待办池剩余条目全部挂在`external-data` / `unverifiable` 上（见下方备选段）——按 Z 协议，资源缺口型不得占用轮次预算，因此本轮不派发研究任务。

处置建议：① 从 `OPEN_QUESTIONS.md` / `HYPOTHESES.md` 派新任务入池；② 或做不依赖外部数据的治理/还债项（validate 警告清单即任务源）。


## ⚠ 资源缺口型备选（不占本批预算，数据就绪后自动进入候选）

- **T-025** E6 固定奖加成是否真实发生（Q-016）（评分 60）—— 需 `external-data`，当前未就绪，不列为必做。
- **T-032** 摇奖设备数据的获取评估（H-003）`resource: unverifiable`（评分 40）—— 需 `unverifiable`，当前未就绪，不列为必做。

## 验收判据

1. 本批 0 个任务全部完成后更新 FACTS.jsonl（新结论必须过三闸门，带 caveats）；
2. `python cli/main.py validate --all` 全绿；
3. 收轮四件套 + 版本登记 + 下轮任务书。
