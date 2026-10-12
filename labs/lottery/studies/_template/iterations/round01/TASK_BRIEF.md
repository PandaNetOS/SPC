# TASK_BRIEF —— <彩种名> round01（占位）

> **反锚定声明**：本任务书写在分析之前。若你已看到任何结论，请先放下，
> 只按下面的数据事实与检验清单工作。

## 1. 目标

占位。真实轮次需要写清：这一轮要回答什么可证伪的问题。

首次接入一个彩种时，最小目标通常是：

- 核实数据完整性（期数、期号连续性、字段口径）
- 核实当前奖金规则与规则变更史
- 建立"概率不可变"这一解析基线（机械计算，不依赖数据）
- 列出 2–3 个**可证伪**的高优先级问题

## 2. 验收判据

- [ ] `python cli/main.py validate --game PLACEHOLDER_ID` 全部通过
- [ ] `data/raw/` 的 SHA256 实算一致
- [ ] 每一条结论都有 `evidence.script` 指向可复现脚本
- [ ] 每一条结论的 `caveats` 非空（否则写"无已知减损项"并说明理由）

## 3. 输入

| 输入 | 路径 | 说明 |
|---|---|---|
| 原始数据 | `games/PLACEHOLDER_ID/data/raw/` | 占位 |
| 既有结论 | `memory/facts/FACTS.jsonl` | 新彩种通常为空 |
| 教训库 | `memory/lessons/LESSONS.md` | **动手前必读 L1–L9** |

## 4. 方法

占位。参考 `platform/methodology/MATH_BOUNDARY.md` 与
`platform/methodology/STATISTICAL_DISCIPLINE.md` 的检查清单。

## 5. 陷阱提醒（逐条对照 LESSONS）

| 教训 | 本彩种场景 | 注意 |
|---|---|---|
| L1 过度离散禁 Poisson | 占位 | — |
| L3 变点禁自然年硬切 | 占位 | — |
| L5 重尾禁止比均值 | 占位 | — |
| L7 严禁混用开出率与被选中率 | 占位 | — |
| L8 禁用模拟验证解析事实 | 占位 | — |
| L9 禁止跨规则断点比奖金 | 占位 | — |

## 6. 预期产出

- `iterations/round01/FINDINGS.md`
- `iterations/round01/HANDOFF.md`
- `iterations/round01/manifest.json`
- `iterations/round02/TASK_BRIEF.md` ← **收轮时必须生成，否则迭代链断裂**
- 新增 `memory/facts/FACTS.jsonl` 条目（如有）

## 7. 明确不做

- 占位。写明本轮明确不碰的边界。

## 8. 反锚定提醒

- 不要预设任何结论成立。数据说什么就是什么。
- 不要因为"别人都这么说"就跳过检验。
