# FINDINGS.md — round18 · 置换检验校正 + 稳健复核

> **版本**：`1.0` ｜ 轮次 `r18` ｜ 更新 2026-10-12 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **日期**：2026-10-12 ｜ **数据**：dlt_full_2933 后段 1973 期
> **脚本**：`scripts/t071_permutation_test.py`、`scripts/t072_robust_check.py`
> **输出**：`scripts/t071_permutation_test.json`、`scripts/t072_robust_check.json`

---

## 1. 本轮做了什么

对 round17 筛出的 5 个显著形态做两步复核：
1. **置换检验 max|r| 多重比较校正**：B=2000，随机打乱 w1 标签，看 40 个形态的 max|ratio-1| 零分布
2. **重尾稳健复核**：中位数比 + 10% 截尾均值，替代均值比（一等奖注数 var/mean=8.46）

---

## 2. 置换检验结果

| 指标 | 值 |
|---|---|
| 观测 max\|r-1\| | 0.381 |
| 零分布 95% 分位数 | 0.573 |
| **p 值** | **0.2235** |
| B（置换次数） | 2000 |

**结论：整体不显著。** 40 个形态中筛出的 5 个"显著"形态，在多重比较校正后可能含假阳性。观测到的最大偏差 0.381，在随机打乱 w1 标签后有 22.35% 概率出现更大偏差。

---

## 3. 稳健复核结果

| 形态 | 均值比 | 中位数比 | 截尾均值比 | 三口径一致 |
|---|---|---|---|---|
| front_max_ge31 | 0.795 | 0.750 | 0.825 | ✅ |
| front_mingap_eq2 | 0.794 | 0.750 | 0.883 | ✅ |
| back_same_tail | 0.619 | 0.667 | 0.713 | ✅（n=50） |
| back_all_even | 0.815 | **1.000** | 0.879 | ❌ 中位数口径消失 |
| front_run_and_birthday | 1.129 | 1.333 | 1.121 | ✅ |

**back_all_even 已从 R-005 移除**：中位数口径 ratio=1.0，说明均值比 0.815 是被低注数期拉低的，效应不稳健。

---

## 4. R-005 修正

| 字段 | 修正前 | 修正后 |
|---|---|---|
| predicate | front_has_35 OR front_min_gap==2 OR **back_even_count==2** OR back_same_tail>=1 | front_has_35 OR front_min_gap==2 OR back_same_tail>=1 |
| evidence_refs | F-0049 | F-0038, F-0041, F-0048, F-0049 |
| caveats | r17 宽筛结果 | 加入置换检验 p=0.22、稳健复核三口径结果 |

---

## 5. FACTS 更新

- **F-0049**（tentative）：claim/caveats 更新，加入置换检验和稳健复核结论
- 未升级为 established——置换检验整体不显著，保持探索性

---

## 6. 结论

1. round17 宽筛的 5 个"显著"形态，在多重比较校正后整体不显著（p=0.22）
2. 3 个冷门形态（front_max_ge31 / front_mingap_eq2 / back_same_tail）在三种估计量下方向一致，效应方向可信但统计显著性不足
3. R-005 保持 C 档探索性，未经 walk-forward 验证
4. 后续需要：连续变量（sum/span/min/center_dev）补充筛选、walk-forward hold-out 验证 R-005
