# HANDOFF —— round12 → round13 交接

> **版本**：`1.0` ｜ 轮次 `r12` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 轮次：round12（L3 hold-out 落地轮）｜ 状态：delivered ｜ 日期：2026-10-11

## 结论（本轮要点）

- **T-049 验收通过（F-0044）**：时序 hold-out（后段 1973 期 60/20/20，测试窗 396 期只评估一次）
  实测撞号避让规则组合的**中奖时期望奖金**样本外提升：随机 708.7 万 → R-001 743.5 万（+4.9%）→
  R-003 812.6 万（+14.7%）→ **R001_norun_high_mirror 906.4 万（+27.9%）**（bootstrap CI
  [725.6 万, 1000 万]，下界高于随机，方向一致）。R-001/R-003 获 B 档（统计确立）样本外确认。
- **T-030（Q-008）落地**：策略有效性三档（A 数学恒真 / B 统计确立 / C 模型估计）写入
  strategy.schema.json 1.4（`effectiveness_grade` 必填），三规则档位回填（R-001=B、R-002=A、
  R-003=B），STRATEGY_GUIDE v1.8/r12 新增三档表。Q-008 → answered。
- **T-040**：ITERATION_PROTOCOL 回写 5 条机械护栏（BOM 编码、策略同步 ★S、任务 id 纯数字、
  渲染五件套、deliverables 对象数组）。
- **F-0004/F-0005 重校准**：E6 锚点精确复现（w1 中位 6.0 / 派发额 0.4252 亿 / 触发 0 次）→ 维持。

## 遗留（未决项）

- **R_new（R001_norun_high_mirror：避连号+避生日号区+避镜像对）尚未入策略**——落地需用户批准
  （策略变更红线）。批准后：strategy.json 新增规则（含镜像对 machine_rule）+ STRATEGY_GUIDE +
  validate 机器规则同步。
- T-025（external-data）、T-032（unverifiable）仍 blocked；F-0041 补强仍可选。
- 开放问题：Q-006（H-003 摇奖设备相关性）、Q-016（E6 固定奖加成真实性）。

## 下轮建议（round13 候选）

1. **T-049b / L3 扩展**：walk-forward 滚动再训练（训练窗前滚，每步只评估紧邻窗）+ 扩大候选池
   （gap 结构、和值区间、冷热号类形态）——或直接处理 R_new 批准落地（若用户批准）。
2. **记忆维护**：记忆压缩已 6 轮到期（round06→round12），下轮须跑 `compress_memory.py --write`。
3. F-0041 补强：三连号之外形态复验（CI 宽）。
4. 等待数据就绪：T-025（E6 固定奖加成，external-data）。

## 建议与风险

- **建议**：R_new 镜像对规则在测试窗 13.13% 池占比（约 52 期）样本中等，若批准入策略，建议
  保持 C 档（探索性）或 B-，不急于升档；下轮 walk-forward 可再确认。
- **风险**：① 测试窗只评估一次，本轮 winner 未经二次样本外；② 池占比继续收缩（R-003 后
  22.98% → +镜像对 13.13%），选号空间越窄，后续叠加规则的边际收益与实操便利性需权衡；
  ③ 概率口径红线：任何文案不得出现"提高中奖率/概率"（validate 自动拦截）。
- 记忆开环（用户长期关切）：Q-008 关闭后 open 仅剩 Q-006/Q-016，均为资源依赖型，无记忆污染风险。

## 交接给 round13 的机械清单

- [ ] 若用户批准 R_new：strategy.json（schema 1.4 已就绪）+ STRATEGY_GUIDE + validate 同步
- [ ] 记忆压缩（6 轮到期）
- [ ] render_task_brief --round 13 --top 3 --write（T-049b / 压缩 / F-0041 候选）
- [ ] 收尾四件套 + versions.json 登记 + 5 render + inject + validate/count_tests/合规
