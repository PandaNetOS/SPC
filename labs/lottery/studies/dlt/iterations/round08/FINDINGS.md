# FINDINGS.md — round08 · 体系升级轮（C+X+Y+Z 四方向实施）

> **版本**：`1.0` ｜ 轮次 `r08` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

| 项 | 内容 |
|---|---|
| **轮次** | `round08`（r08 研究收尾后追加的体系升级批） |
| **彩种** | `dlt` |
| **性质** | **基础设施/方法体系升级轮**：无新 FACTS 结论入库（不产出研究结论），交付 A+Z / Y / C1 / X 四项机制升级 |
| **日期** | 2026-10-11 |
| **执行者** | AI（MainAgent 直接执行；用户「开工全部实施」批准 C+X+Y+Z 组合方案） |

---

## 0. 摘要

| 方向 | 交付 | 验证 |
|---|---|---|
| A+Z | 任务书生成器 `--top N`（一轮完成量可指定）+ `resource:` 字段（资源缺口型任务前置降备选，不做废活） | test_ai_readability 30/30；dry-run round09 top4 正确 |
| Y | `research_lib/` 研究资本化方法库（bootstrap_ci / ratio_and_boot / wilson_interval / split_ratio_stability，彩种无关） | tests/test_research_lib.py 18/18 |
| C1 | 收尾自动化 `tools/finish_round.py` 六步 + `count_tests --inject`（测试计数自举注入 tests/README） | 463/463 全绿；validate 85 项全绿 |
| X | ITERATION_SOP_v2 §9 并行研究池协议 + 任务书「并行研究建议」段 | dry-run round09 top4 输出并行段 |

## 1. C1：收尾自动化的关键发现（注入器自愈）

`count_tests --inject` 首版注入存在丢头 bug（`new` 未含 `txt[:m.start()]`，重写后文件头丢失），
validate 的版本一致性检查立刻拦截（tests/README.md 版本行缺失报错）→ 修复后头部恢复。
**验证了机制闭环**：注入器是派生物生成方，validate 是独立校验方，二者互为防线——
这正是"手写滞后根治"的设计意图：任何一处生成/登记漏跑，独立校验立刻红。

## 2. Y：研究资本化（方法复利）

`research_lib/` 把历史轮次反复使用的统计原语提炼为彩种无关模块（来源映射见 research_lib/README.md）：
- `ratio_and_boot` ← round03/b2_split_stability.py（F-0003 同口径）
- `wilson_interval` ← T-046 方法纪律（文献 27/28/29）
- `split_ratio_stability` ← b2_split_stability.py（Q-001 分期稳健性）
- 纪律：种子显式（默认 20261011）、CI 用分位数、样本不足不硬报（返回 None/unknown）

## 3. X：并行研究池协议

SOP §9：研究阶段可并行（互不依赖的 Q），**入库必须串行过三闸门（INV1/2/3 不豁免）**；
共享文档（FACTS/STRATEGY_GUIDE/strategy.json）在汇合后统一串行更新；收尾照跑 finish_round.py。

## 4. 历史遗留处置（机制防漏生效实例）

`finish_round.py` 检查出 **round08 原收尾缺四件套**（仅 scripts/）——r08 研究批（T-049，98d3c0b）
未按 SOP 落四件套。本轮补齐 FINDINGS / HANDOFF / manifest / journal，
并登记进 versions.json（此后 finish_round 全绿路径可通）。

## 5. 未做的事（如实声明）

- 无新 FACTS 结论入库（本轮是方法/机制升级，不是研究轮）；
- F-0016/F-0017/F-0022/F-0023 动态锚点重校准警告仍挂起（validate 显示当前轮已至 r09）——
  **下一轮开 r09 时的 P0**，见 HANDOFF §3。
