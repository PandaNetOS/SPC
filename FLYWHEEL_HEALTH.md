# FLYWHEEL_HEALTH —— 迭代飞轮健康度


> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **本文件是派生物**：由 `tools/render_flywheel_health.py` 从 FACTS.jsonl 统计生成；
> 结论变更后运行 `--write` 同步，勿手改。｜ 统计轮 r06

> 飞轮是否正向升级的可量化观测（AIDE² 式：连续改进 + 自评信号）。
> 连续 3 轮指标不退化（存活率、产出、通过率）视为飞轮正常。

## 结论演化

| 指标 | 值 |
|---|---|
| 总结论数 | **43** |
| 有效结论（established+tentative） | **40** |
| 被推翻（superseded+refuted） | **3** |
| 结论存活率 | **93.0%** |

## 每轮新增结论（产出是否持续）

| 轮 | 新增 |
|---|---|
| round02 | 13 |
| round03 | 1 |
| round04 | 5 |
| round05 | 4 |
| round07 | 5 |
| round08 | 1 |
| round09 | 6 |
| round10 | 6 |
| round11 | 2 |

## 置信度分层存活率（D1 校准信号）

| 置信度 | 总数 | 已推翻 | 推翻率 |
|---|---|---|---|
| 1★ | 1 | 1 | 100% |
| 2★ | 1 | 1 | 100% |
| 3★ | 12 | 0 | 0% |
| 4★ | 18 | 0 | 0% |
| 5★ | 11 | 1 | 9% |

## 证据类型分布

| claim_type | 条数 |
|---|---|
| analytic | 5 |
| documentary | 2 |
| empirical | 27 |
| methodological | 4 |
| simulation | 5 |
