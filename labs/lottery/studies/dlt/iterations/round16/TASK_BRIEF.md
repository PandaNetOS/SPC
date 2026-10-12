# TASK_BRIEF —— round16 任务书

> **版本**：`1.0` ｜ 轮次 `r16` ｜ 更新 2026-10-12 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本任务书由 `tools/render_task_brief.py` 从 TODO 待办池按价值评分生成
> （派生物草稿，人工确认后可改）。本轮必做 **1** 个（`--top 3` 可调）。
> 评分依据：TODO 条目 value / P 级 / ★首推。

## 本轮候选（按评分排序 TOP-N）

| 排序 | 任务 | 优先级 | 评分 | 说明 |
|---|---|---|---|---|
| 1 | T-063 value: 30 | P4 | 30 | 派生 H-001 连号偏好源于"随机性错觉"（已部分验证，补剩余判据）  [derive:H-001] |

## 本轮必做任务（引用 TODO 原条目）

- [ ] **T-063** —— 来源：`memory/workbench/TODO.md` 的 `P4` 段（评分 30）。

## ⚠ 资源缺口型备选（不占本批预算，数据就绪后自动进入候选）

- **T-025** E6 固定奖加成是否真实发生（Q-016）（评分 60）—— 需 `external-data`，当前未就绪，不列为必做。
- **T-032** 摇奖设备数据的获取评估（H-003）`resource: unverifiable`（评分 40）—— 需 `unverifiable`，当前未就绪，不列为必做。
- **T-062** value: 40（评分 40）—— 需 `external-data`，当前未就绪，不列为必做。
- **T-065** value: 30（评分 30）—— 需 `unverifiable`，当前未就绪，不列为必做。

## 验收判据

1. 本批 1 个任务全部完成后更新 FACTS.jsonl（新结论必须过三闸门，带 caveats）；
2. `python cli/main.py validate --all` 全绿；
3. 收轮四件套 + 版本登记 + 下轮任务书。
