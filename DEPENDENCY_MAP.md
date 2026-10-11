# DEPENDENCY_MAP —— 跨文件依赖图


> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **本文件是派生物**：由 `tools/render_dependency_map.py` 从 strategy.json /
> FACTS.jsonl / game.yaml / versions.json 显式引用关系生成；改动后运行
> `--write` 同步，勿手改。

> 改动任何文件前，先看它被谁依赖（反向引用）；跨文件/多跳依赖是
> AI 理解仓库的主要瓶颈（SWE-QA / REPOGRAPH）。

## FACTS:F-0001
- script→ `games/dlt/strategy/strategy_simulation.py`
- sha256锚→ `games/dlt/strategy/simulation_results.json`
- source→ `games/dlt/strategy/simulation_results.json`

## FACTS:F-0002
- sha256锚→ `games/dlt/rules_history.md`
- source→ `games/dlt/rules_history.md`

## FACTS:F-0003
- script→ `games/dlt/iterations/round03/scripts/b2_split_stability.py`
- sha256锚→ `games/dlt/strategy/simulation_results.json`
- source→ `games/dlt/strategy/simulation_results.json`

## FACTS:F-0004
- script→ `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- sha256锚→ `games/dlt/strategy/simulation_results.json`
- source→ `games/dlt/strategy/simulation_results.json`

## FACTS:F-0005
- script→ `games/dlt/data/tools/consecutive_exact_check.py`
- sha256锚→ `games/dlt/data/tools/consecutive_exact_check.py`
- source→ `games/dlt/data/tools/consecutive_exact_check.py`

## FACTS:F-0006
- script→ `games/dlt/data/tools/changepoint_scan.py`
- sha256锚→ `games/dlt/data/tools/changepoint_scan.py`
- source→ `games/dlt/data/tools/changepoint_scan.py`

## FACTS:F-0007
- script→ `games/dlt/iterations/round02/known_errors.md`
- sha256锚→ `games/dlt/iterations/round02/known_errors.md`
- source→ `games/dlt/iterations/round02/known_errors.md`

## FACTS:F-0008
- script→ `games/dlt/data/tools/acf_permutation_test.py`
- sha256锚→ `games/dlt/data/tools/acf_permutation_test.py`
- source→ `games/dlt/data/tools/acf_permutation_test.py`

## FACTS:F-0009
- script→ `games/dlt/data/tools/overdispersion_and_hac.py`
- sha256锚→ `games/dlt/data/tools/overdispersion_and_hac.py`
- source→ `games/dlt/data/tools/overdispersion_and_hac.py`

## FACTS:F-0010
- script→ `games/dlt/data/tools/exact_tests.py`
- sha256锚→ `games/dlt/data/tools/exact_tests.py`
- source→ `games/dlt/data/tools/exact_tests.py`

## FACTS:F-0011
- script→ `games/dlt/data/tools/exact_tests.py`
- sha256锚→ `games/dlt/data/tools/exact_tests.py`
- source→ `games/dlt/data/tools/exact_tests.py`

## FACTS:F-0012
- script→ `games/dlt/data/tools/validate_data.py`
- sha256锚→ `games/dlt/data/tools/validate_data.py`
- source→ `games/dlt/data/tools/validate_data.py`

## FACTS:F-0013
- script→ `games/dlt/data/tools/validate_data.py`
- sha256锚→ `games/dlt/data/tools/validate_data.py`
- source→ `games/dlt/data/tools/validate_data.py`

## FACTS:F-0014
- sha256锚→ `games/dlt/rules_history.md`
- source→ `games/dlt/rules_history.md`

## FACTS:F-0015
- script→ `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- sha256锚→ `games/dlt/rules_history.md`
- source→ `games/dlt/rules_history.md`

## FACTS:F-0016
- script→ `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- sha256锚→ `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- source→ `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`

## FACTS:F-0017
- script→ `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- sha256锚→ `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- source→ `games/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`

## FACTS:F-0018
- script→ `games/dlt/iterations/round03/scripts/b2_robust_estimators.py`
- sha256锚→ `games/dlt/iterations/round03/scripts/b2_robust_estimators.py`
- source→ `games/dlt/iterations/round03/scripts/b2_robust_estimators.py`

## FACTS:F-0019
- script→ `games/dlt/iterations/round04/scripts/decay_cause.py`
- sha256锚→ `games/dlt/iterations/round04/scripts/decay_cause.py`
- source→ `games/dlt/iterations/round04/scripts/decay_cause.py`

## FACTS:F-0020
- script→ `games/dlt/iterations/round04/scripts/decay_cause.py`
- sha256锚→ `games/dlt/iterations/round04/scripts/decay_cause.py`
- source→ `games/dlt/iterations/round04/scripts/decay_cause.py`

## FACTS:F-0021
- script→ `games/dlt/iterations/round04/scripts/decay_cause.py`
- sha256锚→ `games/dlt/iterations/round04/scripts/decay_cause.py`
- source→ `games/dlt/iterations/round04/scripts/decay_cause.py`

## FACTS:F-0022
- script→ `games/dlt/iterations/round04/scripts/decay_cause.py`
- sha256锚→ `games/dlt/iterations/round04/scripts/decay_cause.py`
- source→ `games/dlt/iterations/round04/scripts/decay_cause.py`

## FACTS:F-0023
- script→ `games/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`
- sha256锚→ `games/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`
- source→ `games/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`

## FACTS:F-0024
- script→ `games/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`
- sha256锚→ `games/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`
- source→ `games/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`

## FACTS:F-0025
- script→ `games/dlt/iterations/round04/scripts/back_collision.py`
- sha256锚→ `games/dlt/iterations/round04/scripts/back_collision.py`
- source→ `games/dlt/iterations/round04/scripts/back_collision.py`

## FACTS:F-0026
- script→ `games/dlt/iterations/round05/scripts/bet_structure.py`
- sha256锚→ `games/dlt/iterations/round05/scripts/bet_structure.py`
- source→ `games/dlt/iterations/round05/scripts/bet_structure.py`

## FACTS:F-0027
- script→ `games/dlt/iterations/round05/scripts/bet_structure.py`
- sha256锚→ `games/dlt/iterations/round05/scripts/bet_structure.py`
- source→ `games/dlt/iterations/round05/scripts/bet_structure.py`

## FACTS:F-0028
- script→ `games/dlt/iterations/round05/scripts/bet_structure.py`
- sha256锚→ `games/dlt/iterations/round05/scripts/bet_structure.py`
- source→ `games/dlt/iterations/round05/scripts/bet_structure.py`

## FACTS:F-0029
- script→ `games/dlt/iterations/round05/scripts/bet_structure.py`
- sha256锚→ `games/dlt/iterations/round05/scripts/bet_structure.py`
- source→ `games/dlt/iterations/round05/scripts/bet_structure.py`

## FACTS:F-0030
- script→ `games/dlt/iterations/round05/scripts/timing_weekday.py`
- sha256锚→ `games/dlt/iterations/round05/scripts/timing_weekday.py`
- source→ `games/dlt/iterations/round05/scripts/timing_weekday.py`

## FACTS:F-0031
- script→ `games/dlt/iterations/round05/scripts/timing_weekday.py`
- sha256锚→ `games/dlt/iterations/round05/scripts/timing_weekday.py`
- source→ `games/dlt/iterations/round05/scripts/timing_weekday.py`

## FACTS:F-0032
- script→ `games/dlt/iterations/round05/scripts/timing_weekday.py`
- sha256锚→ `games/dlt/iterations/round05/scripts/timing_weekday.py`
- source→ `games/dlt/iterations/round05/scripts/timing_weekday.py`

## FACTS:F-0033
- script→ `games/dlt/iterations/round07/scripts/t014_forensics.py`
- sha256锚→ `games/dlt/iterations/round07/scripts/t014_forensics.py`
- source→ `games/dlt/iterations/round07/scripts/t014_forensics.py`

## FACTS:F-0034
- script→ `games/dlt/iterations/round07/scripts/t015_external.py`
- sha256锚→ `games/dlt/iterations/round07/scripts/t015_external.py`
- source→ `games/dlt/iterations/round07/scripts/t015_external.py`

## FACTS:F-0035
- script→ `games/dlt/iterations/round07/scripts/t016_holiday.py`
- sha256锚→ `games/dlt/iterations/round07/scripts/t016_holiday.py`
- source→ `games/dlt/iterations/round07/scripts/t016_holiday.py`

## FACTS:F-0036
- script→ `games/dlt/iterations/round08/scripts/all_tiers_expectation.py`
- sha256锚→ `games/dlt/iterations/round08/scripts/all_tiers_expectation.py`
- source→ `games/dlt/iterations/round08/scripts/all_tiers_expectation.py`

## game.yaml:?
- primitive→ `features.py:sum`

## game.yaml:prize_model
- epoch→ `epochs:E0`
