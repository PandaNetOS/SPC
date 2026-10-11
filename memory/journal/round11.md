# round11 执行日志（效应与代理轮）

> 轮次：round11 ｜ 日期：2026-10-11 ｜ 状态：completed

## 任务书

`render_task_brief.py --round 11 --top 3 --write` → T-023（60 分，Q-011 效应弱化复验）/
T-024（60 分，Q-015 机选代理）/ T-048（60 分，hold-out 评测设计）。T-025/T-032 资源缺口备选未列入。

## 执行

### T-023（t023_roll_decay.py）
- 后段 1973 期滚动窗口 W=300/500 步长 50 → R_run 窗口序列（34/30 窗）
- OLS 趋势 + Kendall tau + 头尾 1/3 Mann-Whitney：全部不显著 → 平台期
- 节假日春节精确映射 ±14 天分三时段：0.385 / 1.217 / 0.888（n=65/47/52）
- 踩坑：±7 天窗口样本太少（n=23）→ 放宽 ±14 天；结论措辞修正（"未检测到显著持续弱化"→"平台期"）

### T-024（t024_proxy.py）
- 3 代理（R_low / R_run / gini_w1）后段滚动 W=300，数据驱动变点扫描（置换 B=2000）
- P2/P3 显著（p=0.0005），P1 边缘（p=0.055）；P2 与 F-0021 同窗（±24 月容差）
- 踩坑：pandas int 列不能当布尔掩码（low 列 0/1 → 改 bool）；变点对齐判定从"字面区间"改"窗口级 ±24 月"

### T-048（T048_HOLDOUT_DESIGN.md）
- 时序 hold-out 设计：训练 60% / 验证 20% / 测试 20%（测试只评估一次）
- 指标、防泄漏（L6）、组合搜索边界、验收护栏、引用陷阱全含

## 入库（apply_r11_facts.py + 手动修正）

- F-0042（平台期）/ F-0043（代理可观测）新增；F-0021 caveats 更新（代理证据 + 口径限定）
- Q-011/Q-015 → answered；open 5→3；TODO T-023/T-024/T-048 → done
- **schema 踩坑序列**：缺 supersedes/superseded_by/created_at/confidence_grade/change_type →
  根级 noop_count 不允许（应在 evidence）→ claim 超长 → source 必填（None 致 rehash join 崩溃）→
  evidence.noop_count/data_version/rules_epoch/script/source_sha256/n_observations 补齐
- F-0021 变更 → strategy evidence_hash 漂移 → `rehash --strategy` 重基线

## 顺带根治

1. **validate .jsonl 盲区**：FACTS.jsonl 不在检查范围（后缀 .jsonl 被 .endswith 漏掉）→ 纳入 +
   按 claim 字段检查（跨字段误报 6 处清零）
2. **渲染脚本 BOM 叠加**：render_*.py 用 utf-8 读 BOM 文件 → 每次 --write 叠一个 U+FEFF
   （README 累计 15 个）→ 版本行注入失效。修 4 个脚本读为 utf-8-sig + README 压缩单 BOM

## 收尾

- 四件套：FINDINGS（3 研究 + 2 根治 + 遗留）/ HANDOFF（r12 候选）/ manifest / 本日志
- versions.json：+7 新增（round11 任务书/设计/2 脚本/2 报告/apply）+6 刷新（FACTS/OQ/TODO/validate/README/AI_CONTEXT）
- validate 96 项全绿；count_tests 463（待确认）；合规（待跑）
- git：待用户 push 指令
