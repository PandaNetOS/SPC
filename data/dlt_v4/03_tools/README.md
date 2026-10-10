# 03_tools — 可复用检验工具

这些脚本从历史复核中抽取，**展示正确的方法论**。请把它们当模板，而非答案。

| 脚本 | 用途 | 演示的正确做法 |
|---|---|---|
| `_load.py` | **统一数据装载器**（其余脚本共用） | 从包内 CSV 重建派生列；`draw_num` 强制 str |
| `validate_data.py` | 数据完整性校验 | 全字段一致性 + 期号连续性 + 周分布 |
| `changepoint_scan.py` | 切点全扫描 | **不用自然年硬切**（避开 E3） |
| `changepoint_refine.py` | 变点精细定位 | ruptures 多模型 + Power analysis |
| `acf_permutation_test.py` | 自相关置换检验 | **置换检验替代 FDR**（避开 E4） |
| `overdispersion_and_hac.py` | 过度离散与稳健标准误 | **QuasiPoisson/NegBin/HAC**（避开 E1） |
| `exact_tests.py` | 精确检验 | **蒙特卡洛替代渐近卡方**（避开 E2） |
| `consecutive_exact_check.py` | 连号精确理论 | **枚举组合空间**（避开 E7） |

## 运行方式（自包含）

所有脚本已改造为**从包内 CSV 读取**，可在本目录直接运行：

```bash
cd 03_tools
python validate_data.py          # 或任意脚本
```

脚本通过 `_load.py` 统一装载数据，并从原始列重建派生列
（`log_sale` / `run` / `run_ge2` / `sum_z` / `span_z` / `heat` / `back_span`），
保证口径一致。若需换数据源，改 `_load.py` 的 `_CSV` 路径即可。

> **v4 变更**：`_load.py` 的数据源已指向 `01_data/dlt_full_2933.csv`（2933 期）。

## 注意事项

- 这些脚本**不含任何结论**，只产出统计量。结论由你基于输出自行判断。
- **`heat` 为全样本口径**（含前视偏差，见 `05_known_errors.md` E6），
  仅为复现历史讨论；做预测性分析时须改为滚动（仅用历史）口径。
- **`exact_tests.py` / `changepoint_scan.py` 计算量大**（蒙特卡洛/全切点扫描），
  单次运行可能需 1~2 分钟。
- 运行输出（`*_v4.log` / `s*_output.txt`）在 `output/` 下，可删。
- 依赖：`numpy pandas scipy statsmodels ruptures`。

## 与 T7 模拟验证的关系

`03_tools/` 处理的是**历史数据检验**（数据层）；
`07_strategy_simulation/` 处理的是**策略主张验证**（决策层）。
两者的方法论纪律一致：精确方法优先、给出 CI、区分解析与估计。
