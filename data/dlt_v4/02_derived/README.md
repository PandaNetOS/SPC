# 02_derived — 派生数据集

> 本目录所有文件由 `05_build_scripts/build_derived_v4.py` 从 `01_data/dlt_full_2933.csv`
> **机械生成，无人工编辑**。所有文件名均为纯 ASCII，UTF-8 with BOM 输出。
>
> 复现：`cd 05_build_scripts && python build_derived_v4.py`

## 文件清单

| 文件 | 内容 | 关键口径 |
|---|---|---|
| `01_yearly_stats.csv` | 逐年统计（20 年 × 17 指标） | 含逐年前区卡方与 p、销量/奖池均值、和值/奇偶/大小/跨度均值、高区占比、连号占比 |
| `02_front_number_frequency.csv` | 35 号频率 | 全期 / **2013-08 前后分段**，含 z 值 |
| `03_back_number_frequency.csv` | 12 号频率与均匀性检验 | 含卡方 p |
| `04_structure_distribution_exact.json` | ★ **精确枚举理论分布** | 和值/连号/奇偶/大小/跨度/三区：观测 vs 理论 vs 差 |
| `05_back_combo_66.csv` | 66 种后区组合频次 | 含期望与比值 |
| `06_acf_lag1to60.csv` | 5 指标 × lag1-60 的 ACF | 含朴素 z 与 p（**未做多重比较校正，勿直接判定**） |
| `07_data_quality_report.json` | 数据质量断言 + SHA256 | 2933 期全部校验结果 |
| `08_rules_epoch_summary.json` | ★ **按规则变更断点分段统计**（v4 新增） | 7 个 epoch，见 `06_RULES_HISTORY.md` |

## 08_rules_epoch_summary.json 详解（v4 新增）

按 `06_RULES_HISTORY.md` 的 6 次规则变更断点，把 2933 期切成 7 个 epoch：

| epoch | 区间 | 奖级 | 期数 | 关键说明 |
|---|---|---|---|---|
| E0 | 2007-05-30 ~ 2009-10-17 | 8 | 367 | 原始规则 |
| E1 | 2009-10-17 ~ 2013-12-09 | 8 | 637 | 奖池过亿单注最高 1000 万 |
| E2 | 2013-12-09 ~ 2014-05-05 | 8 | 60 | 资金 50/15/35 → 51/14/35 |
| E3 | 2014-05-05 ~ 2019-02-18 | 6 | 735 | 奖级 8 → 6 |
| E4 | 2019-02-18 ~ 2023-01-01 | 9 | 567 | 奖级 6 → 9，追加 80% |
| E5 | 2023-01-01 ~ 2026-02-02 | 9 | 465 | 开奖时间改 21:25 |
| E6 | 2026-02-02 ~ 今 | **7** | **102** | **现行规则**，一二等单期总额封顶 1 亿 |

> ⚠️ **跨 epoch 比较奖金金额会产生无意义结论**（见 `05_known_errors.md` E8）。
> 号码类分析（前区/后区分布）不受规则变更影响，**可跨全期合并**。

## 重要提示

- `04_structure_distribution_exact.json` 的 `theoretical_*` 字段是**精确枚举真值**
  （枚举全部 324,632 个前区组合），不是近似或模拟。分析结构分布时应以此为基准。
- `06_acf_lag1to60.csv` 的 `p_naive` **未做多重比较校正**，直接看会得到大量假阳性。
  正确做法见 `03_tools/acf_permutation_test.py`（置换检验 + 家族错误率）。
- 所有派生文件的 SHA256 见 `07_data_quality_report.json`。
