# FLYWHEEL_HEALTH —— 迭代飞轮健康度

> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`

> **本文件是派生物**：由 `tools/render_flywheel_health.py` 从 FACTS.jsonl 统计生成；
> 结论变更后运行 `--write` 同步，勿手改。｜ 统计轮 r06

> 飞轮是否正向升级的可量化观测（AIDE² 式：连续改进 + 自评信号）。
> 连续 3 轮指标不退化（存活率、产出、通过率）视为飞轮正常。

## 结论演化

| 指标 | 值 |
|---|---|
| 总结论数 | **32** |
| 有效结论（established+tentative） | **30** |
| 被推翻（superseded+refuted） | **2** |
| 结论存活率 | **93.8%** |

## 每轮新增结论（产出是否持续）

| 轮 | 新增 |
|---|---|
| round02 | 15 |
| round03 | 3 |
| round04 | 7 |
| round05 | 7 |

## 置信度分层存活率（D1 校准信号）

| 置信度 | 总数 | 已推翻 | 推翻率 |
|---|---|---|---|
| 1★ | 1 | 1 | 100% |
| 2★ | 1 | 0 | 0% |
| 3★ | 7 | 0 | 0% |
| 4★ | 15 | 0 | 0% |
| 5★ | 8 | 1 | 12% |

## 证据类型分布

| claim_type | 条数 |
|---|---|
| analytic | 3 |
| documentary | 2 |
| empirical | 18 |
| methodological | 4 |
| simulation | 5 |
