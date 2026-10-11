# TASK_BRIEF —— round14 任务书

> **版本**：`1.0` ｜ 轮次 `r14` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本任务书由 `tools/render_task_brief.py` 从 TODO 待办池按价值评分生成
> （派生物草稿，人工确认后可改）。本轮必做 **3** 个（`--top 3` 可调）。
> 评分依据：TODO 条目 value / P 级 / ★首推。

## 本轮候选（按评分排序 TOP-N）

| 排序 | 任务 | 优先级 | 评分 | 说明 |
|---|---|---|---|---|
| 1 | T-052 value: 40 | P2 | 40 | r14 候选：R_new（R001_norun_high_mirror）正式落地为 R-004 —— **需用户批准**（策略变更红线） |
| 2 | T-053 value: 30 P4：F-0041 补强——三连号之外形态复验（CI 宽） | P2 | 30 |  |
| 3 | T-054 value: 30 P4：walk-forward 每步 bootstrap CI（当前单步仅点估计） | P2 | 30 |  |

## 本轮必做任务（引用 TODO 原条目）

- [ ] **T-052** —— 来源：`memory/workbench/TODO.md` 的 `P2` 段（评分 40）。
- [ ] **T-053** —— 来源：`memory/workbench/TODO.md` 的 `P2` 段（评分 30）。
- [ ] **T-054** —— 来源：`memory/workbench/TODO.md` 的 `P2` 段（评分 30）。

## ⚠ 资源缺口型备选（不占本批预算，数据就绪后自动进入候选）

- **T-025** E6 固定奖加成是否真实发生（Q-016）（评分 60）—— 需 `external-data`，当前未就绪，不列为必做。
- **T-032** 摇奖设备数据的获取评估（H-003）`resource: unverifiable`（评分 40）—— 需 `unverifiable`，当前未就绪，不列为必做。

## 验收判据

1. 本批 3 个任务全部完成后更新 FACTS.jsonl（新结论必须过三闸门，带 caveats）；
2. `python cli/main.py validate --all` 全绿；
3. 收轮四件套 + 版本登记 + 下轮任务书。

## 并行研究建议（X 协议，见 ITERATION_SOP_v2 §9）

本批有 **3** 个可执行任务（无资源缺口）互不依赖，可并行研究：

- T-052 value: 40
- T-053 value: 30 P4：F-0041 补强——三连号之外形态复验（CI 宽）
- T-054 value: 30 P4：walk-forward 每步 bootstrap CI（当前单步仅点估计）

约束：① 各任务独立研究、各自出草案；② **入库必须串行过三闸门**（INV1/2/3 不豁免）；
③ 共享文档（FACTS/STRATEGY_GUIDE/strategy.json）在汇合后统一串行更新，避免并发写冲突；
④ 收尾统一跑 `tools/finish_round.py`。
