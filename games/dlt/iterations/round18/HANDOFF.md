# HANDOFF.md — round18 交接

> **日期**：2026-10-12 ｜ **下轮**：round19

---

## 本轮完成

1. **置换检验 max|r| 校正**：40 个形态多重比较，p=0.2235，整体不显著
2. **稳健复核**：中位数比 + 截尾均值，3/4 冷门形态三口径一致，back_all_even 移除
3. **R-005 修正**：predicate 去掉 back_even_count==2，evidence_refs 加入 F-0038/F-0041/F-0048（established 支撑）
4. **F-0049 更新**：claim/caveats 加入置换检验和稳健复核结果，保持 tentative

---

## 当前规则集（5 条）

| 规则 | 档位 | 动作 | 内容 |
|---|---|---|---|
| R-001 | B | exclude | 避连号 |
| R-002 | A | exclude | 禁完全相同号码 |
| R-003 | B | exclude | 避生日号区（全号≤31） |
| R-004 | B | exclude | R-001+R-003+镜像对叠加 |
| R-005 | C | prefer | 偏好冷门形态：含35/最小间隔=2/后区同尾 |

---

## 下轮候选任务

### 必做（TODO 池）
- **T-063** H-001 连号偏好源于"随机性错觉"补剩余判据（评分 30）

### 建议（本轮遗留）
1. **连续变量补充筛选**：sum/span/min/center_dev 等连续值的撞号比，而非 boolean 形态
2. **R-005 walk-forward 验证**：用时间序列 hold-out 验证 R-005 的样本外有效性
3. **R-005 权重优化**：当前权重 1.2 是拍定值，需组合搜索优化

---

## 文件清单

| 文件 | 说明 |
|---|---|
| `TASK_BRIEF.md` | 本轮任务书 |
| `FINDINGS.md` | 本轮发现 |
| `HANDOFF.md` | 本文件 |
| `manifest.json` | 本轮清单 |
| `scripts/t071_permutation_test.py` | 置换检验脚本 |
| `scripts/t071_permutation_test.json` | 置换检验结果 |
| `scripts/t072_robust_check.py` | 稳健复核脚本 |
| `scripts/t072_robust_check.json` | 稳健复核结果 |
