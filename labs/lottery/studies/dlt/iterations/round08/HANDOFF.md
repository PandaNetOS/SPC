# HANDOFF.md — round08 → round09 交接

> **版本**：`1.0` ｜ 轮次 `r08` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 1. 本轮结论清单

- **无新 FACTS 结论入库**（本轮为体系升级轮：A+Z / Y / C1 / X 四项机制升级）。
- **机制交付**：
  - `tools/finish_round.py --round NN`：收尾六步一键化（rehash → count_tests --inject → validate --all → 渲染流水线 → 四件套检查 → 批准门提示）；
  - `count_tests.py --inject`：tests/README.md 测试计数自举注入（12 个测试文件，合计 463）；
  - `research_lib/`：彩种无关统计原语库（bootstrap_ci / ratio_and_boot / wilson_interval / split_ratio_stability）+ 18 项原语测试；
  - `render_task_brief.py --top N`：一轮完成量可指定；`resource:` 字段资源缺口前置；必做 ≥2 输出并行建议段；
  - ITERATION_SOP_v2.md §9：并行研究池协议（研究可并行、入库串行过三闸门）。

## 2. 最重要的事

1. **收尾不再手写**：本轮起，收尾清单第 2–6 步用 `python tools/finish_round.py --round NN` 一键执行；
   测试计数由 `count_tests --inject` 自举注入，版本行由 `inject_version_lines --write` 统一注入，均禁手写。
2. **新增/修改文件必须登记 versions.json**：validate 结构完整性会双向拦截（本轮 research_lib/*、tools/finish_round.py、
   tests/test_research_lib.py 未登记时 count_tests 即红——机制预期生效）。
3. **研究产出可复用**：新轮次研究的统计逻辑若第二次复用，先提炼进 `research_lib/` 再组合（研究资本化闭环，见 research_lib/README.md）。
4. **并行研究纪律**：研究可并行，入库必须串行过三闸门；共享文档汇合后统一更新（SOP §9）。

## 3. 遗留问题（按优先级）

| 优先级 | 问题 | 来源 | 状态 |
|---|---|---|---|
| **P0** | **F-0016/F-0017/F-0022/F-0023 动态锚点重校准**（validate 警告：6/6/5/5 轮到期，当前轮已至 r09） | 机制到期 | 开 r09 时必须重校准（维持或 update 通道） |
| P0 | T-046 R-002 `magnitude_pct` 量化补齐（评分 110） | TODO | 任务书已生成（round09 top1） |
| P1 | T-047 F-0032 教训制度化 + FACTS 新增 NOOP（评分 80） | TODO | 任务书已生成（round09 top2） |
| P2 | T-020 逐号偏好权重建模（Q-006 / H-002）、T-021 销量内生性检验（Q-005） | TODO | 可并行研究 |
| P2 | T-025 E6 固定奖加成（Q-016） | TODO | 需 `external-data`，资源就绪后自动入候选 |
| P2 | T-032 摇奖设备数据获取评估（H-003） | TODO | 需 `unverifiable`，资源前置 |
| — | round08 四件套缺失（历史遗留） | 机制检查 | 本轮已补齐并登记 |

## 4. 给下一轮的执行提示

- 开轮：`python tools/render_task_brief.py --round 09 --top N --write` → 你确认任务书 → 开工；
- 每轮收尾：`python tools/finish_round.py --round 09`（全绿路径：validate 85 项 + count_tests 463 全绿）；
- 涉及代码/配置/策略的变更：先给你确认方案，得到明确开工指令后才动手；push 等你的明确指令（仅 main 单分支）。
