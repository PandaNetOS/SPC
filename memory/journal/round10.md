# journal — round10（口径根治与稳健性轮）

> **版本**：`1.0` ｜ 轮次 `r10` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本文件是执行日志，记录 round10 的执行过程事实。

## 2026-10-11 · 口径根治与稳健性轮执行

- 用户「下一轮 + 开工」→ 任务书（T-050 100 分 + T-021 + T-022）批准执行；P0 三锚点重校准（F-0028/29/31，HANDOFF 交接 + validate 到期警告）并入。
- **任务书修正过程**：render_task_brief 首轮生成 T-021/T-022/T-023（T-050 未进——缺 value 字段只 60 分被挤出 top3）→ `--score` 发现 T-050 缺 value → 补 `value: 90 ★ r10 首推` 后重新生成，T-050/T-021/T-022 入选。
- **T-050（F-0039 + validate 检查项）**：`t050_calibration.py` 解析全奖级概率（C(35,5)×C(12,2)=21,425,712；1-9 等累计 1,429,197 → 任一奖级 ≈1/15）；检索 184 处绑定，数字型错误 4 处 + 结论缺限定 6 处 → 7 份文档 + strategy.json:224 逐处修正；**validate 新增 `_check_probability_calibration` 检查项，首跑即抓到 strategy.json:224 漏网**。
- **T-021（F-0040，Q-005 → answered）**：ADF + Granger（滞后 1-3）+ 含/不含销量模型对照——销量内生但不驱动注数；pool 系数 −0.00111 稳定。踩坑：statsmodels ndarray 无 `.iloc` → `m.params[i]`。
- **T-022（F-0041，H-001 → partial）**：9 形态 bootstrap——仅等差 1 三连显著（1.1287 CI [1.0351,1.2243]）；judge/summary 措辞两次修正（『获得支持』→『部分支持』）。
- **P0 重校准（t028_recalibrate_r10）**：F-0031 AR(1) 0.9994/SE 0.00064/ACF≈0.999 精确复现；F-0028/29 E6 锚点 6 复现、模拟参数无机制变化 → 全部 maintain（noop_count=1，established_in=round10）。踩坑：与 T-021 同源的 ndarray `.iloc`。
- **入库（apply_r10_facts）**：FACTS 38→41；F-0001 表述校正（奖级限定，rehash 基线）；H-001 partial；Q-005/Q-017 answered；TODO T-050/21/22 → done。
- **收尾修复**：F-0039 claim_type=analytic（n_observations 不适用）、category 枚举校正（robustness/collision 非法 → sales_external/structure_preference）、data_version "E6"；OQ 标题 ✅ 标记 + 计数 9→11 + 优先级总览划线；TASK_BRIEF 版本行补写；apply_r10_facts.py 登记。
- **登记**：versions.json 248 条（round10 新增 11 条：任务书 + t021/t022/t050/t028 脚本与报告 + apply）。
- **validate**：93 项全绿（含概率口径检查项）；**四件套 + finish_round 完成，待用户批准后提交推送**。
