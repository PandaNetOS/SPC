# journal — round09（策略量化轮）

> **版本**：`1.0` ｜ 轮次 `r09` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本文件是执行日志，记录 round09 的执行过程事实。

## 2026-10-11 · 策略量化轮执行

- 用户「下一轮」「开工」→ 任务书（T-046 110 / T-047 80 / T-020 60）批准执行；P0 四锚点重校准（HANDOFF 交接）并入。
- **T-046（F-0037）**：R-002 magnitude_pct 实证量化——m 升级为经验分布（一等奖中出注数），K=2/5/10 修复增益 20.72%/47.82%/65.49%（CI 均不含 0，PASS）；strategy.json R-002.magnitude_pct 填入。
- **T-047**：核验 ingate `_evidence_tier` + schema `noop_count` 已落地（r08 登记确认）；NOOP 实战——4 条重校准维持 `evidence.noop_count=1`。
- **T-020（F-0038）**：逐号相对强度 S_j + OLS 对照——逐号结构存在（ΔR² 0.0366）但生日段 1-31 vs 32-35 不显著（+0.047 CI 含 0）。
- **P0 重校准（t013_recalibrate_r09）**：F-0016 max 0.9788 亿 0 触发 / F-0017/22 锚点 6+0.4252 / F-0023 +0.017 p=0.311——全部维持（NOOP）。
- **入库（apply_r09_facts）**：FACTS 36→38；R-002 magnitude_pct 填入；TODO T-046/47/20 → done。
- **登记**：versions.json 234 条（+8：round09 任务书 + 7 脚本/报告；strategy.json note 更新）。
- **踩坑**：t013 json.dump 遇 np.bool_ 序列化失败（文件截断）→ `p_two` 转 float 修复。
