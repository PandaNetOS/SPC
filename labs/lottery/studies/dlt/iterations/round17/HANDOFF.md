# HANDOFF —— round17（全形态穷举筛选轮）

> **版本**：`1.0` ｜ 轮次 `r17` ｜ 更新 2026-10-12

## 1. 本轮结论清单

| 项 | 内容 | 证据 |
|---|---|---|
| T-070 | 40 个 boolean 形态撞号比穷举，5 个显著（1 高 4 低），29 个不显著 | `t070_feature_screen.py` + JSON |
| 新原语 | features.py 新增 6 个原语（count_same_tail/max_run_length/arithmetic_triplet_count/count_in_set/center_deviation/has_tail_cluster） | features.py |
| game.yaml | 新增 23 个特征声明，config_version 2.2→2.3 | game.yaml |
| F-0049 | 全形态宽筛总览（tentative，未过多重比较校正） | FACTS.jsonl |

数字：40 形态筛选，B=2000 bootstrap，后段 1973 期。

## 2. 关键发现

**显著低（冷门，可利用）4 个：**
- `front_mingap_eq2`（最小间隔=2）ratio=0.794，CI=[0.722, 0.877] — 与 R-001 互补
- `front_max_ge31`（含35）ratio=0.795，CI=[0.715, 0.886] — 与 F-0038/F-0048 一致
- `back_all_even`（后区全偶）ratio=0.815，CI=[0.721, 0.919]
- `back_same_tail`（后区同尾）ratio=0.619，CI=[0.485, 0.762]（n=50，功效有限）

**显著高（拥挤）1 个：**
- `front_run_and_birthday` ratio=1.129 — R-001×R-003 叠加效应，非新形态

**证伪 29 个：** 同尾聚集/吉祥号/忌讳号/全奇全偶/镜像对/等差三元组等均不显著。

## 3. 遗留

- **多重比较未校正**：40 个检验预期 ~2 个假阳性，5 个显著形态需置换检验 max|r| 校正。
- **重尾未复核**：撞号比是均值比，var/mean=8.46，需 NB2/中位数比复核。
- **候选规则未落地**：4 个冷门形态是 R-005 候选，但未过 walk-forward hold-out 验证。
- **未跑 validate --all**：PyYAML/jsonschema 缺失，且按用户红线不立即部署。

## 4. 下轮建议

1. **置换检验 max|r| 校正**：对 5 个显著形态做全排列检验，确认假阳性率。
2. **NB2 重尾复核**：用负二项模型替代均值比，确认效应稳健。
3. **walk-forward 验证 R-005 候选**：优先验证 front_mingap_eq2（与 R-001 互补，效应最强且前后段一致）。
4. **连续变量补充筛选**：本轮只筛 boolean 形态，sum/span/min/center_dev 等连续变量未做分桶分析。

## 5. 风险

- **back_same_tail n=50**：样本量小，即使 CI 不跨 1 也可能是假阳性。
- **front_max_ge31 前半段 CI 边缘**：[0.684, 1.001]，效应在后半段更强，可能是时变效应。
- **29 个"不显著"不等于"无效应"**：可能是效应小但存在，只是 CI 太宽。
