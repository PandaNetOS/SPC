# HANDOFF —— round13（L3 规则搜索 v2 轮）

> **版本**：`1.0` ｜ 轮次 `r13` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 结论

- **F-0045（T-051）**：R_new（R001_norun_high_mirror）walk-forward 二次样本外确认通过——5 步中 4 步正增益（80%），中位增益约 +150 万元，累计约 +604 万元，3/5 步为本步最优；与 v1 固定切分测试窗（+27.9%）方向一致，**B 档证据链闭合**。
- **T-044**：`build_versions.py --write` 已禁用（防 versions.json 回退），降级为参考实现。
- **T-045**：count_tests --inject 已落地，销账。
- 红线遵守：R_new 仍为**新候选**，不改变任一奖级中奖概率；正式入策略需用户批准（T-052）。

## 遗留

- **T-052（待用户批准）**：R_new 落地为 R-004（strategy.json + STRATEGY_GUIDE + validate 同步）。批准前 F-0044/F-0045 证据链保留，候选状态不升级。
- **F-0041 补强**：三连号之外形态复验（CI 宽），仍开放。
- **walk-forward 单步 CI**：当前单步仅点估计（第 5 步样本不足），下轮可加每步 bootstrap CI。

## 未决

- R_new 是否入策略 → **等用户批准**（策略变更红线，不自动执行）。
- Q-006（摇奖设备，H-003）/ Q-016（E6 固定奖加成，T-025）仍开放，均需 external-data / unverifiable 资源。

## 下轮

- round14 建议：任务书自动生成（T-052 待批准 / F-0041 补强 / walk-forward CI 强化）；记忆压缩（本轮已执行 compress_memory --write，下轮到期检查）。
- 每轮 push 已预授权至 round14。

## 风险

- 短窗 walk-forward（150 期）cf 估计噪声大（第 5 步命中不足 20 期即不估）——统计上如实记录，不作为强证据单独使用，须与 v1 全窗联合解读。
- 冷热号避让依赖训练窗频率，跨期稳定性未单独检验（本轮结果未显示其超越 R_new）。
