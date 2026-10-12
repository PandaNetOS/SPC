# DEPENDENCY_MAP —— 跨文件依赖图


> **版本**：`1.0` ｜ 轮次 `r16` ｜ 更新 2026-10-12 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **本文件是派生物**：由 `tools/render_dependency_map.py` 从 strategy.json /
> FACTS.jsonl / game.yaml / versions.json 显式引用关系生成；改动后运行
> `--write` 同步，勿手改。

> 改动任何文件前，先看它被谁依赖（反向引用）；跨文件/多跳依赖是
> AI 理解仓库的主要瓶颈（SWE-QA / REPOGRAPH）。

## FACTS:F-0001
- script→ `labs/lottery/studies/dlt/strategy/strategy_simulation.py`
- sha256锚→ `labs/lottery/studies/dlt/strategy/simulation_results.json`
- source→ `labs/lottery/studies/dlt/strategy/simulation_results.json`

## FACTS:F-0002
- sha256锚→ `labs/lottery/studies/dlt/rules_history.md`
- source→ `labs/lottery/studies/dlt/rules_history.md`

## FACTS:F-0003
- script→ `labs/lottery/studies/dlt/iterations/round03/scripts/b2_split_stability.py`
- sha256锚→ `labs/lottery/studies/dlt/strategy/simulation_results.json`
- source→ `labs/lottery/studies/dlt/strategy/simulation_results.json`

## FACTS:F-0004
- script→ `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- sha256锚→ `labs/lottery/studies/dlt/strategy/simulation_results.json`
- source→ `labs/lottery/studies/dlt/strategy/simulation_results.json`

## FACTS:F-0005
- script→ `labs/lottery/studies/dlt/data/tools/consecutive_exact_check.py`
- sha256锚→ `labs/lottery/studies/dlt/data/tools/consecutive_exact_check.py`
- source→ `labs/lottery/studies/dlt/data/tools/consecutive_exact_check.py`

## FACTS:F-0006
- script→ `labs/lottery/studies/dlt/data/tools/changepoint_scan.py`
- sha256锚→ `labs/lottery/studies/dlt/data/tools/changepoint_scan.py`
- source→ `labs/lottery/studies/dlt/data/tools/changepoint_scan.py`

## FACTS:F-0007
- script→ `labs/lottery/studies/dlt/iterations/round02/known_errors.md`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round02/known_errors.md`
- source→ `labs/lottery/studies/dlt/iterations/round02/known_errors.md`

## FACTS:F-0008
- script→ `labs/lottery/studies/dlt/data/tools/acf_permutation_test.py`
- sha256锚→ `labs/lottery/studies/dlt/data/tools/acf_permutation_test.py`
- source→ `labs/lottery/studies/dlt/data/tools/acf_permutation_test.py`

## FACTS:F-0009
- script→ `labs/lottery/studies/dlt/data/tools/overdispersion_and_hac.py`
- sha256锚→ `labs/lottery/studies/dlt/data/tools/overdispersion_and_hac.py`
- source→ `labs/lottery/studies/dlt/data/tools/overdispersion_and_hac.py`

## FACTS:F-0010
- script→ `labs/lottery/studies/dlt/data/tools/exact_tests.py`
- sha256锚→ `labs/lottery/studies/dlt/data/tools/exact_tests.py`
- source→ `labs/lottery/studies/dlt/data/tools/exact_tests.py`

## FACTS:F-0011
- script→ `labs/lottery/studies/dlt/data/tools/exact_tests.py`
- sha256锚→ `labs/lottery/studies/dlt/data/tools/exact_tests.py`
- source→ `labs/lottery/studies/dlt/data/tools/exact_tests.py`

## FACTS:F-0012
- script→ `labs/lottery/studies/dlt/data/tools/validate_data.py`
- sha256锚→ `labs/lottery/studies/dlt/data/tools/validate_data.py`
- source→ `labs/lottery/studies/dlt/data/tools/validate_data.py`

## FACTS:F-0013
- script→ `labs/lottery/studies/dlt/data/tools/validate_data.py`
- sha256锚→ `labs/lottery/studies/dlt/data/tools/validate_data.py`
- source→ `labs/lottery/studies/dlt/data/tools/validate_data.py`

## FACTS:F-0014
- sha256锚→ `labs/lottery/studies/dlt/rules_history.md`
- source→ `labs/lottery/studies/dlt/rules_history.md`

## FACTS:F-0015
- script→ `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- sha256锚→ `labs/lottery/studies/dlt/rules_history.md`
- source→ `labs/lottery/studies/dlt/rules_history.md`

## FACTS:F-0016
- script→ `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- source→ `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`

## FACTS:F-0017
- script→ `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`
- source→ `labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py`

## FACTS:F-0018
- script→ `labs/lottery/studies/dlt/iterations/round03/scripts/b2_robust_estimators.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round03/scripts/b2_robust_estimators.py`
- source→ `labs/lottery/studies/dlt/iterations/round03/scripts/b2_robust_estimators.py`

## FACTS:F-0019
- script→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`
- source→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`

## FACTS:F-0020
- script→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`
- source→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`

## FACTS:F-0021
- script→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`
- source→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`

## FACTS:F-0022
- script→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`
- source→ `labs/lottery/studies/dlt/iterations/round04/scripts/decay_cause.py`

## FACTS:F-0023
- script→ `labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`
- source→ `labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`

## FACTS:F-0024
- script→ `labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`
- source→ `labs/lottery/studies/dlt/iterations/round04/scripts/prize_mechanism_tobit.py`

## FACTS:F-0025
- script→ `labs/lottery/studies/dlt/iterations/round04/scripts/back_collision.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round04/scripts/back_collision.py`
- source→ `labs/lottery/studies/dlt/iterations/round04/scripts/back_collision.py`

## FACTS:F-0026
- script→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`
- source→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`

## FACTS:F-0027
- script→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`
- source→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`

## FACTS:F-0028
- script→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`
- source→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`

## FACTS:F-0029
- script→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`
- source→ `labs/lottery/studies/dlt/iterations/round05/scripts/bet_structure.py`

## FACTS:F-0030
- script→ `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`
- source→ `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`

## FACTS:F-0031
- script→ `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`
- source→ `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`

## FACTS:F-0032
- script→ `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`
- source→ `labs/lottery/studies/dlt/iterations/round05/scripts/timing_weekday.py`

## FACTS:F-0033
- script→ `labs/lottery/studies/dlt/iterations/round07/scripts/t014_forensics.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round07/scripts/t014_forensics.py`
- source→ `labs/lottery/studies/dlt/iterations/round07/scripts/t014_forensics.py`

## FACTS:F-0034
- script→ `labs/lottery/studies/dlt/iterations/round07/scripts/t015_external.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round07/scripts/t015_external.py`
- source→ `labs/lottery/studies/dlt/iterations/round07/scripts/t015_external.py`

## FACTS:F-0035
- script→ `labs/lottery/studies/dlt/iterations/round07/scripts/t016_holiday.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round07/scripts/t016_holiday.py`
- source→ `labs/lottery/studies/dlt/iterations/round07/scripts/t016_holiday.py`

## FACTS:F-0036
- script→ `labs/lottery/studies/dlt/iterations/round08/scripts/all_tiers_expectation.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round08/scripts/all_tiers_expectation.py`
- source→ `labs/lottery/studies/dlt/iterations/round08/scripts/all_tiers_expectation.py`

## FACTS:F-0037
- script→ `labs/lottery/studies/dlt/iterations/round09/scripts/t046_r002_quantify.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round09/scripts/t046_r002_quantify.py`
- source→ `labs/lottery/studies/dlt/iterations/round09/scripts/t046_r002_quantify.py`

## FACTS:F-0038
- script→ `labs/lottery/studies/dlt/iterations/round09/scripts/t020_number_weight.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round09/scripts/t020_number_weight.py`
- source→ `labs/lottery/studies/dlt/iterations/round09/scripts/t020_number_weight.py`

## FACTS:F-0039
- script→ `labs/lottery/studies/dlt/iterations/round10/scripts/t050_calibration.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round10/scripts/t050_calibration.py`
- source→ `labs/lottery/studies/dlt/iterations/round10/scripts/t050_calibration.py`

## FACTS:F-0040
- script→ `labs/lottery/studies/dlt/iterations/round10/scripts/t021_sales_endogeneity.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round10/scripts/t021_sales_endogeneity.py`
- source→ `labs/lottery/studies/dlt/iterations/round10/scripts/t021_sales_endogeneity.py`

## FACTS:F-0041
- script→ `labs/lottery/studies/dlt/iterations/round10/scripts/t022_illusion.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round10/scripts/t022_illusion.py`
- source→ `labs/lottery/studies/dlt/iterations/round10/scripts/t022_illusion.py`

## FACTS:F-0042
- script→ `labs/lottery/studies/dlt/iterations/round11/scripts/t023_roll_decay.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round11/scripts/t023_roll_decay.py`
- source→ `labs/lottery/studies/dlt/iterations/round11/scripts/t023_roll_decay.py`

## FACTS:F-0043
- script→ `labs/lottery/studies/dlt/iterations/round11/scripts/t024_proxy.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round11/scripts/t024_proxy.py`
- source→ `labs/lottery/studies/dlt/iterations/round11/scripts/t024_proxy.py`

## FACTS:F-0044
- script→ `labs/lottery/studies/dlt/iterations/round12/scripts/t049_holdout.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round12/scripts/t049_holdout.py`
- source→ `labs/lottery/studies/dlt/iterations/round12/scripts/t049_holdout.py`

## FACTS:F-0045
- script→ `labs/lottery/studies/dlt/iterations/round13/scripts/t051_walkforward.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round13/scripts/t051_walkforward.py`
- source→ `labs/lottery/studies/dlt/iterations/round13/scripts/t051_walkforward.py`

## FACTS:F-0046
- script→ `labs/lottery/studies/dlt/iterations/round14/scripts/t053_shape_ratios.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round14/scripts/t053_shape_ratios.py`
- source→ `labs/lottery/studies/dlt/iterations/round14/scripts/t053_shape_ratios.py`

## FACTS:F-0047
- script→ `labs/lottery/studies/dlt/iterations/round14/scripts/t054_walkforward_ci.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round14/scripts/t054_walkforward_ci.py`
- source→ `labs/lottery/studies/dlt/iterations/round14/scripts/t054_walkforward_ci.py`

## FACTS:F-0048
- script→ `labs/lottery/studies/dlt/iterations/round16/scripts/t064_h002_segment.py`
- sha256锚→ `labs/lottery/studies/dlt/iterations/round16/scripts/t064_h002_segment.py`
- source→ `labs/lottery/studies/dlt/iterations/round16/scripts/t064_h002_segment.py`

## game.yaml:?
- primitive→ `features.py:sum`

## game.yaml:prize_model
- epoch→ `epochs:E0`
