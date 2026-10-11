# round12 执行日志（L3 hold-out 落地轮）

> 轮次：round12 ｜ 日期：2026-10-11 ｜ 状态：completed

## 任务书

`render_task_brief.py --round 12 --top 3 --write` → T-049（90 分，★r12 首推，hold-out 评测实现 +
规则搜索 v1）/ T-030（40 分，策略有效性三档，Q-008）/ T-040（20 分，框架改进回写）。
T-025/T-032 资源缺口备选未列入。

## 执行

### T-049（t049_holdout.py）
- 后段 1973 期切 训练 1183 / 验证 394 / 测试 396（切点 2021-07-10 / 2024-02-28）
- 候选池 6 组合验证窗选型 → 验证窗最优 R001_norun_high_mirror（799.7 万 vs R-003 729.3 万）
- 测试窗单次评估：随机 708.7 万 / R-001 743.5 万 / R-003 812.6 万 / winner 906.4 万
- bootstrap B=2000：winner CI [725.6, 1000.0] 万，下界高于随机 → **验收 met=True**
- 踩坑：① `_ROOT` 层级少一层（..×4→×5）② CSV 列名 front_1..front_5/back_1..back_2（非 n1/b1）
  ③ numpy bool 不可 JSON 序列化 → bool() ④ bootstrap 初版漏 winner CI → 泛化全规则

### T-030（t030_effectiveness.py）
- strategy.schema.json 1.4：rules 必填 effectiveness_grade（A/B/C）+ effectiveness_basis
- strategy.json：schema_version 1.4 + R-001=B / R-002=A / R-003=B 档位回填
- STRATEGY_GUIDE v1.8/r12：§2 三档表 + T-049 测试窗证据

### T-040（框架回写）
- ITERATION_PROTOCOL §6 校验清单扩展（概率口径派生扫描/★S 策略同步/deliverables 对象数组/schema 全字段）
- §7 禁止事项 +5：BOM 编码、策略版本落后、任务 id 纯数字、渲染五件套、deliverables 字符串

## 入库（_tmp_facts12.py）

- F-0044 新增（T-049 hold-out 结论，met=True）；FACTS 43→44
- F-0004/F-0005 重校准：E6 锚点精确复现（w1 中位 6.0 / 派发额 0.4252 亿 / max 0.9788 亿 / 触发 0 次）
  → 维持，established_in → round12
- Q-008 → answered（open 3→2）；TODO T-030/T-040/T-049 → done

## 收尾

- 四件套：FINDINGS（3 研究 + 重校准 + 遗留）/ HANDOFF（R_new 待批准 + 下轮建议）/ manifest / 本日志
- versions.json 登记 + 5 render + inject；validate --all / count_tests / 合规
- git：每轮结束即推送（用户预授权）
