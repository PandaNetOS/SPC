# INDEX.md — 框架层索引

> **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> 本文件是 `framework/` 的导航。**AI 读这一页就能知道该读哪个文件。**

## 按需求找文件

| 我想…… | 读这个 |
|---|---|
| 知道这一轮研究该怎么进行（开轮/收轮/四件套） | `protocol/ITERATION_PROTOCOL.md` |
| 知道结论/教训/问题该写在哪、怎么写 | `protocol/MEMORY_PROTOCOL.md` |
| 开轮时写任务书 | `protocol/templates/TASK_BRIEF.template.md` |
| 记录发现 | `protocol/templates/FINDINGS.template.md` |
| 收轮时写交接 | `protocol/templates/HANDOFF.template.md` |
| 搞清"选号能/不能影响什么" | `methodology/MATH_BOUNDARY.md` ★ |
| 动手前过一遍检查清单 | `methodology/STATISTICAL_DISCIPLINE.md` ★ |
| 读写记忆（程序化） | `tools/memory.py` |
| **拿一注号码算特征 / 判定是否合规 / 打分** | `core/README.md` → `core/ticket.py` + `core/evaluate.py` + `core/judge.py` ★ |
| **生成号码（遵守策略规则）** | `core/generate.py`，或 `python cli/main.py pick --game <id>` |
| **知道框架有哪些原语可用来声明特征** | `core/features.py` 的 `PRIMITIVES`（21 个） |
| **知道某个 predicate 该不该在单注层判定** | `core/judge.py` 的 `split_by_scope()` ★ |
| 知道该彩种有哪些特征可算 | `games/<id>/game.yaml` 的 `features` 段（**不在本目录**） |

## 动手前的固定顺序

```
1. protocol/ITERATION_PROTOCOL.md     ← 知道流程
2. methodology/STATISTICAL_DISCIPLINE.md  ← ★ 过一遍检查清单
3. methodology/MATH_BOUNDARY.md       ← 知道边界在哪
4. memory/lessons/LESSONS.md          ← ★ 知道哪些坑踩过
5. games/<id>/iterations/roundNN/TASK_BRIEF.md  ← 知道这轮做什么
```

第 2、4 步最省时间。它们是"读一次省几小时"的文档。

## 一句话记忆

| 文件 | 一句话 |
|---|---|
| `MATH_BOUNDARY.md` | `E[回报] = Σ P_j × (池_j / 中奖注数_j)`；只有最后一项可被选号影响 |
| `STATISTICAL_DISCIPLINE.md` | 9 条检查清单，逐项打勾才能标 `established` |
| `ITERATION_PROTOCOL.md` | 四件套（BRIEF/FINDINGS/HANDOFF/manifest）+ 收轮必生成下轮 BRIEF |
| `MEMORY_PROTOCOL.md` | 四类记忆、状态机、演化链、`caveats` 非空 |
| `core/README.md` | 三层（Ticket / Scoring / Portfolio）+ 原语注册表 + 受限 DSL + **作用域切分** ★ |

## 彩种无关性自检

本目录**任何文件都不应出现**：具体彩种 id、号码池大小、具体特征名。

若发现违反，这是技术债（见 `README.md` 的"唯一的硬标准"）。
