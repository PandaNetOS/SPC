# framework/ — 框架层

> **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **框架 = 骨架 + 协议。彩种 = 数据 + 插件。**
>
> 本目录的一切内容**不含任何具体彩种的参数**。
> 换一个彩种，本目录不需要改动一行 —— 这是"框架/彩种分离"的判定标准。

## 目录

| 目录 | 内容 | 彩种无关？ |
|---|---|---|
| `protocol/` | 迭代协议、记忆协议、三个交接模板 | ✅ |
| `methodology/` | 数学边界推导、统计纪律检查清单 | ✅（数值从 `game.yaml` 读） |
| `tools/` | 通用工具（记忆读写库） | ✅ |
| `core/` | **框架核心（已实现）**：21 个特征原语 / `Ticket` / 求值 / 受限 DSL 判定 / 作用域切分 / 生成器 | ✅（`game.yaml` 只提供声明） |

## 怎么判断某段代码属于框架还是彩种

| 问题 | 属于框架 | 属于彩种 |
|---|---|---|
| 代码里出现了 `35`、`12`、`dlt`、`连号`？ | ❌ 不该出现 | ✅ 正常 |
| 代码从 `game.yaml` 读 `machine.zones`？ | ✅ 正确 | — |
| 代码从 `features` 段读特征定义？ | ✅ 正确 | — |
| 代码硬编码某个特征的公式？ | ❌ 违反分离 | ✅ 应在 `game.yaml` 的 `features` 里 |
| 代码里出现 `if zone_key == "front"`？ | ❌ 违反分离 | ✅ 只在 `game.yaml` 里作为数据出现 |

**唯一的硬标准**：加入第二个彩种时，是否需要修改 `framework/`？
- 需要 → 分离没做好，是技术债
- 不需要 → 分离成立

> 这个标准目前**尚未被检验** —— 因为仓库里只有 `games/dlt/` 一个彩种。
> 见 `memory/workbench/TODO.md` 的 `T-031`。
>
> **但结构已经为它准备好了**：`Ticket` 的区名来自 `machine.zones`（可变长，
> 不硬编码 `front`/`back`）；特征求值走 `primitive` + `args` 注册表
> （框架不知道"连号"是什么）。这两条是"不改 `framework/`"的前提条件。

## 框架核心（`core/`）速览

| 模块 | 一行说明 |
|---|---|
| `features.py` | 21 个纯数学原语，签名 `(zone, **args) -> int\|bool`。输入**强制去重排序**，不规范就报错 |
| `game_util.py` | `T = ∏ C(pool_size_i, pick_i)`、`p1 = 1/T`、`validate_feature_declarations()` |
| `ticket.py` | `Ticket` 一等公民。可哈希、可比较、可渲染。**不含 `front`/`back`** |
| `evaluate.py` | 按 `features[]` 声明机械求值（跳过纯 `formula` 的） |
| `judge.py` | 受限 DSL 解析 + 判定 + **作用域切分**（`split_by_scope`） |
| `generate.py` | 拒绝采样 + 结构分散。触顶**明确报错**，不返回空 |

## 两条核心设计

### 1. 契约优先

`spec/` 定义了 5 个 schema。框架的所有输入输出都必须合规：

```
game.yaml        ← 彩种声明，框架据此驱动
FACTS.jsonl      ← 结论台账，策略生成器的证据来源
manifest.json    ← 轮次元数据，协议的机器可读骨架
strategy.json    ← 对外输出
```

**为什么要契约**：分析过程可以随轮次大改，但**对外结构不变**。
这让内部自由演进与外部稳定消费得以共存（见 `spec/README.md`）。

### 2. 配置驱动

框架不"知道"大乐透是什么。它只读 `game.yaml`：

```yaml
machine:
  zones:
    - {key: front, pool_size: 35, pick: 5}
    - {key: back,  pool_size: 12, pick: 2}
features:
  - {key: adjacent_pairs, type: integer, formula: "count(adjacent_pairs)"}
prize_model:
  epochs: [...]
```

框架据此计算 `T = ∏ C(pool_size_i, pick_i)`、枚举组合、计算特征。

**新增彩种的正确流程**：

```
1. cp -r games/_template games/<new_id>
2. 填 game.yaml（machine / features / prize_model / data）
3. 准备 data/raw/ 并算 SHA256
4. 建 iterations/round01/TASK_BRIEF.md
5. 跑 python cli/main.py validate --game <new_id>
```

**不修改 `framework/` 与 `src/` 的任何一行。**

> 如果做不到这一点，说明框架里藏了彩种假设 ——
> 这是**必须修的技术债**，不是"以后再说"。

## 本目录与 `memory/` 的关系

| | `framework/` | `memory/` |
|---|---|---|
| 内容 | **怎么做**（方法、协议、纪律） | **已经知道什么**（结论、教训、待办） |
| 变化频率 | 低（只在框架改进时改） | 高（每轮迭代都更新） |
| 彩种相关 | ❌ 无关 | ⚠️ 台账含 `game` 字段区分 |

简单说：`framework/` 是**方法论文档**，`memory/` 是**研究记录**。
