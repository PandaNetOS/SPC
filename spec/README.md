# spec/ — 契约层

> **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

本目录是仓库的**稳定接口**。框架代码、AI 协议、外部消费者都必须遵守这里定义的结构。

## 为什么先有契约

这个仓库的两种用户是完全不同的：

| 用户 | 需要什么 | 不关心什么 |
|---|---|---|
| **AI 分析者**（每轮迭代） | 数据在哪、结论记在哪、上轮遗留什么 | 消费者怎么用 |
| **外部工具**（选号器 / 前端 / Agent） | 一个稳定的策略 JSON | 内部怎么分析出来的 |

契约层把两者**解耦**：分析过程可以随轮次大改，输出结构保持不变。

## 文件清单

| 文件 | 约束什么 | 权威消费者 |
|---|---|---|
| `fact.schema.json` | 一条研究结论（`labs/lottery/studies/dlt/memory/facts/FACTS.jsonl` 每行） | 记忆层、策略生成器 |
| `strategy.schema.json` | 对外输出的彩种策略规则集 | **所有外部工具** |
| `game_config.schema.json` | 彩种声明式配置（`games/<id>/game.yaml`） | 框架核心 |
| `iteration.schema.json` | 一轮迭代的元数据（`iterations/roundNN/manifest.json`） | AI 协议、自我迭代 |
| `version_index.schema.json` | 版本总索引（`versions.json`） | 版本校验、AI 读取版本 |

版本规则见 `VERSIONING.md`；文档与内容的版本分级见 `../docs/VERSIONING_DOCS.md`。

## 三条不可违反的红线

以下字段在 schema 中被编码为 `const`，任何生成器违反即校验失败：

1. **`fact.affects_win_probability` 恒为 `false`**
   选号方式在数学上不可能改变中奖概率（分母 = 全部组合数，固定）。
   任何声称能提高中奖概率的结论**拒收**，不是"待商榷"，是结构性拒绝。

2. **`strategy.disclaimer.changes_win_probability` 恒为 `false`**
   对外输出必须明确告诉消费者：本策略不提高中奖概率。

3. **`strategy.boundary.optimizable_target` 只能是 `expected_bonus_given_win`**
   唯一可优化的量是"中奖时的期望奖金"。枚举里**故意不放** `win_probability`
   —— 让写错变成编译期/校验期错误，而不是报告期错误。

4. **`game_config.prize_model.epochs[].sum_affects_numbers` 恒为 `false`**
   奖金规则的变更不影响号码分布。跨 epoch 比较奖金金额是无意义的。

> 这四条来自 `labs/lottery/studies/dlt/iterations/round02/known_errors.md` 的 E1–E9 实证教训。
> 契约不是装饰 —— 它是把已付出的学费固化成机器可检的约束。

## 校验

```bash
python cli/main.py validate --all
```

或直接：

```bash
python -c "from src.SPC.validate import validate_all; validate_all()"
```

校验器会检查：schema 合规、外键引用存在（`evidence_refs` → `FACTS.jsonl`）、
`source` 文件真实存在、`superseded`/`superseded_by` 双向一致、红线段落恒为期望值。

## 变更流程

1. 改 schema → 2. 跑 `validate --all` 找出所有受影响文件 → 3. 同步更新数据 →
4. 更新 `VERSIONING.md` 的变更日志 → 5. 提交。

**新增字段一律可选（不加入 `required`）**，保证旧消费者不破。
