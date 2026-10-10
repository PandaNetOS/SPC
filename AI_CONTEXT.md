# AI_CONTEXT.md — 单一入口

> **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **如果你是一个 AI（或人），要在这个仓库里做分析 —— 从本文件开始，读完本文件再动手。**
>
> 本文件约 10 分钟可读完。读完你能知道：这个仓库是干什么的、东西在哪、
> 三条不能违反的红线、以及**动手前必须知道的方法论纪律**。
>
> 最后更新：2026-10-11 | 当前轮次：`round02`（已交付）| 下一轮：`round03`（待启动）
>
> **★ 版本意识**：本仓库有五个版本号并存（`schema_version` / `config_version` /
> `data_version` / **`content_version`** / **`framework_version`**）。
> **引用任何内容前，先确认它的版本** → 读 [`VERSION_INDEX.md`](VERSION_INDEX.md)。
> 规则见 `docs/VERSIONING_DOCS.md`。

---

## 0. 三十秒版本

**这是一个「彩票投注策略研究框架」**，不是彩票工具、不是预测器。

它做两件事：

1. **自我迭代地研究**：每轮 AI 读上轮结论 → 提出更好的研究框架 → 产出新结论。
   记忆层让结论**带着血统演化**，而不是每轮重来。
2. **输出可被机器消费的策略规则**：`games/<id>/strategy/strategy.json`
   遵守 `spec/strategy.schema.json`，供其他工具直接调用。

**它明确知道的真相**：
> **没有任何选号方法能提高中奖概率。** 唯一可优化的量是
> 「**中奖时的期望奖金**」—— 通过减少与他人撞号（避开热门形态）实现。

这不是免责声明式的谦辞，是**解析可证的数学事实**（分母固定 = 全部组合数）。
任何声称能提高中奖概率的结论，在本仓库**结构性拒收**。

---

## 1. 三条红线（违反即校验失败）

| # | 红线 | 编码位置 |
|---|---|---|
| 1 | **`affects_win_probability` 恒为 `false`** —— 任何结论都不能声称改变中奖概率 | `spec/fact.schema.json` 的 `const` |
| 2 | **`strategy.disclaimer.changes_win_probability` 恒为 `false`** —— 对外输出必须声明不提高中奖概率 | `spec/strategy.schema.json` 的 `const` |
| 3 | **`optimizable_target` 只能是 `expected_bonus_given_win`** —— 唯一可优化量是"中奖时奖金" | 枚举里**故意不放** `win_probability` |

第 3 条的设计意图：**让写错变成校验期错误，而不是报告期错误**。
一个把"提高奖金"写成"提高中奖率"的前端，比一个报错的前端危险得多。

补充红线：`game_config.prize_model.epochs[].sum_affects_numbers` 恒 `false`
（奖金规则变更不影响号码分布）。

---

## 2. 目录地图

```
smartpickcore/
├── AI_CONTEXT.md          ← 你在这里（单一入口）
├── VERSION_INDEX.md       ★ 版本索引（先读 §0，知道「我读的是哪一版」）
├── versions.json             版本索引的机器可读镜像
├── README.md                  仓库总览（给人看）
├── spec/                  ★ 契约层：5 个 JSON Schema + VERSIONING.md
│   └── version_index.schema.json   版本索引的契约
├── framework/             框架层（彩种无关）｜ framework_version = 1.0
│   ├── protocol/          迭代协议、记忆协议 ★ 动手前必读
│   ├── methodology/       方法论（数学底线、统计纪律）
│   ├── tools/             通用工具（记忆读写库）
│   └── core/              ★ 框架核心（已实现，6 模块 / 21 原语）
│       ├── features.py     特征原语库（纯数学，zone 已排序去重）
│       ├── game_util.py    由 machine/features 段驱动的纯计算（T / p1 / 声明检查）
│       ├── ticket.py       Ticket 一等公民（区名可变长，不硬编码 front/back）
│       ├── evaluate.py     按声明机械求值
│       ├── judge.py        受限 DSL + 判定 + ★ 作用域切分
│       └── generate.py     通用生成器（拒绝采样 + 结构分散）
├── memory/                ★ 记忆层（本仓库的核心差异）
│   ├── INDEX.md           ← 记忆层说明，建议读
│   ├── facts/             FACTS.jsonl（权威源）+ INDEX.md（速览）
│   ├── journal/           每轮迭代日志
│   ├── lessons/           ★ LESSONS.md（L1–L9，动手前必读）
│   └── workbench/         OPEN_QUESTIONS / HYPOTHESES / TODO
├── games/                 彩种层（插件）
│   ├── _template/         新彩种模板
│   └── dlt/               超级大乐透（当前唯一实现的彩种）
│       ├── game.yaml      彩种声明式配置（config_version 2.0）
│       ├── rules_history.md   规则变更史（决定奖金类分析口径）
│       ├── data/          raw/（原始，不可变）+ derived/ + tools/ + build_scripts/
│       ├── iterations/    round01/ round02/ round03/
│       └── strategy/      strategy.json（对外输出）+ 模拟脚本与结果
├── src/smartpickcore/     库代码（api / memory / strategy / validate）
├── cli/main.py            命令行入口（13 个命令）
├── tools/                 仓库维护脚本（版本索引生成器）
├── tests/                 test_core.py（92 项，无需 pytest）
└── docs/                  ARCHITECTURE.md / CONSUMING.md / ITERATION_GUIDE.md
                           VERSIONING_DOCS.md（★ 文档版本规则）
```

---

## 3. 数据现状（当前彩种：dlt）

| 项 | 值 |
|---|---|
| 彩种 | 超级大乐透：前区 **35 选 5** + 后区 **12 选 2** |
| 单注组合总数 | **21,425,712** |
| 一等奖概率 | **4.667289469773513e-08** |
| 数据版本 | `dlt_full_2933` |
| 期数 | **2933**（`07001` ~ `26115`） |
| 时间范围 | 2007-05-30 ~ 2026-10-10 |
| 原始数据 | `games/dlt/data/raw/dlt_full_2933.csv`（SHA256 `9e92848e...706bb7`） |
| 现行规则 | **E6**，2026-02-02（26014 期）起：7 奖级、一/二等奖单期总额封顶 1 亿元、返奖率 51% |

### 读数据的两个必踩坑

```python
import pandas as pd
df = pd.read_csv("games/dlt/data/raw/dlt_full_2933.csv",
                 encoding="utf-8-sig",        # ← 漏掉会让首列名变成 '\ufeffdraw_num'
                 dtype={"draw_num": str})     # ← 漏掉会让 '07001' 变成整数 7001
```

`draw_num` 是**字符串**（带前导零），`prize1_amount_yuan` 是**右删失**数据
（81.4% 封顶 500 万），`prize1_winners` 是**重尾**分布（var/mean=8.46）。
详见 `games/dlt/game.yaml` 的 `data.caveats`。

---

## 4. 动手前必读：方法论纪律

**先读 `memory/lessons/LESSONS.md`** —— 它记录了 9 条已付学费的错误。
对照速查：

| id | 一句话禁令 | 检查方式 |
|---|---|---|
| L1 | 过度离散计数**禁用** Poisson | `var/mean` > 1.5 ? |
| L2 | 小期望格**禁用**渐近卡方 | 最小期望频数 < 5 ? |
| L3 | 变点**禁用**自然年硬切 | 报告里有"某年之前/之后" ? |
| L4 | 多重比较**禁用** FDR 替代置换 | 有样本外 R² 吗 ? |
| L5 | 重尾变量**禁止**比均值 | 分布斜度多大 ? |
| L6 | **禁用**全样本统计量做预测 | 特征在第 t 期怎么算的 ? |
| L7 | **严禁**混用开出率与被选中率 | 同段是否同时出现两个说法 ? |
| L8 | **禁用**模拟验证解析事实 | 循环里有"是否中一等奖" ? |
| L9 | **禁止**跨规则断点比奖金 | 有 `rules_epoch` 吗 ? |

### 三条最容易越界的

1. **L7 —— 开出率 ≠ 被选中率**
   "连号更容易被摇出"（1.120，仅早期，**不可用**）
   ≠ "连号更容易被人买"（1.360，**强，可用**）。
   **策略价值只来自后者。** 混淆会产生完全错误的因果解释。

2. **L8 —— 不要用模拟验证解析事实**
   一等奖概率 4.67e-08。写循环模拟"技巧 vs 随机"的命中，
   结论**完全由噪声主导**。概率不变性用**解析**给出；
   只有"撞号/奖金"这类**必须估计**的量才用模拟，且必须报 CI 与假设。

3. **"统计显著" ≠ "可用"**
   ACF lag 6/10/18/23 置换检验家族 p=0.0004（**信号是真的**），
   但样本外 R²=−0.083（**信号没用**）。这两件事不矛盾。

### 归因边界

本仓库**只有数据**，没有摇奖设备、球组、场地记录。
任何"为什么"的因果断言都超出证据范围（见 `HYPOTHESES.md` H-003）。
**"能排除什么"比"能证明什么"更常是有效产出。**

---

## 5. 已经确定的结论（速览）

**权威源是 `memory/facts/FACTS.jsonl`（15 条）**，此处只列最重要的几条。
引用前**必读该条的 `caveats`**。

| id | 结论 | 置信度 |
|---|---|---|
| **F-0001** | 任何选号方式都不能改变单注中奖概率（**解析可证**） | ★★★★★ |
| **F-0002** | 彩票是负期望游戏（返奖率 51%，净期望 −0.98 元/注） | ★★★★★ |
| **F-0003** | 连号形态人群更密（一等奖注数比 **1.3603** [1.1298, 1.6292]） | ★★★★☆ |
| **F-0004** | 避开连号提高"中奖时期望奖金" **+121.48%**（条件模拟） | ★★★☆☆ |
| F-0005 | 连号**开出率**优势仅早期、不可用（与 F-0003 严格区分） | ★★★★☆ |
| F-0006 | 结构切点 **2013-08**（χ²=185.0, 1/234），渐变 | ★★★★☆ |
| F-0008 | 开奖序列**不可预测**（样本外 R² 全负） | ★★★★☆ |
| F-0014 | 规则变更 6 次，**号码结构从未改变**（号码类分析可跨全期） | ★★★★★ |
| F-0015 | 现行 **1 亿封顶已实测触发**（26113 期 37 注 → 239 万/注） | ★★★★★ |
| ~~F-0007~~ | ~~2015 年断点~~ **已推翻**，禁引用 | — |

### 三个引用陷阱

1. **F-0004 的 +121% 不是中奖概率提升**，是"中奖时奖金"提升。
   写成"提高中奖率"是本仓库最严重的表述错误。
2. **F-0004 被 F-0015 削弱**。26113 期已实测触发封顶 ——
   触发后减少同号人数**不再**提高单注奖金。给 E6 规则的建议必须带此减损。
3. **F-0004 是模型估计（★★★☆☆），不是数学事实。**
   不要把它当 F-0001 使用。

---

## 6. 一条结论长什么样

```jsonc
{
  "id": "F-0004", "game": "dlt",
  "claim": "在固定预算下避开连号形态，可提高『中奖时的期望奖金』约 121%",
  "status": "established",
  "confidence": 3,
  "confidence_basis": "条件份额模拟（必须估计的量，无法解析给出）...",
  "category": "prize_mechanism",
  "affects_win_probability": false,          // ← 红线，恒 false
  "evidence": {
    "method": "条件份额模拟（100 注 × 300000 次抽样）",
    "result_summary": "撞号系数 1.0028 → 0.4528；比值 0.4515，95%CI [0.4487, 0.4543]",
    "effect": { "collision_factor_from": 1.0028, "collision_factor_to": 0.4528,
                "prize_uplift_pct": 121.48, "calibrated_alpha": 13.9405 },
    "ci95": [0.4487, 0.4543],
    "rules_epoch": "E6",
    "script": "games/dlt/strategy/strategy_simulation.py"
  },
  "caveats": [                               // ← 必读！每条 caveat 都是一个任务
    "模型依赖：α 由历史注数近似校准，是估计非真值。",
    "封顶稀释：现行 1 亿总额封顶触发后，减少同号人数不再增加单注奖金。",
    "只在中奖时兑现：中奖概率不变，期望回报提升被极小概率大幅折现。",
    "长期期望回报仍为负（约 −0.98 元/注），本结论不改变这一事实。"
  ],
  "established_in": "round02",
  "supersedes": null, "superseded_by": null,
  "source": "games/dlt/strategy/simulation_results.json"
}
```

**注意 `caveats` 的长度**：本仓库要求它非空。
一条没有减损项的结论，要么是数学定理，要么是作者没想清楚边界。

---

## 7. 工作流程（AI 按此顺序）

```
【开始一轮】
1. 读本文件（AI_CONTEXT.md）
2. 读 VERSION_INDEX.md §0 + §2-A               ← ★ 先知道「我读的是哪一版」
3. 读 memory/lessons/LESSONS.md               ← ★ 最重要的一步
4. 读 games/<game>/iterations/roundNN/TASK_BRIEF.md   ← 这轮要做什么
5. 读 memory/facts/INDEX.md                   ← 已有结论速览
6. 读 memory/workbench/{OPEN_QUESTIONS,HYPOTHESES,TODO}.md ← 从哪继续
7. 需要精确数字时读 memory/facts/FACTS.jsonl（注意 caveats）

【做分析】
8. 严格套用 LESSONS 的检测方法；每个结论写可复现脚本
9. 遵守 games/<game>/game.yaml 的字段口径与数据警告

【结束一轮】
10. 新结论 → 追加 FACTS.jsonl（含 caveats 与真实存在的 source）
11. 新教训 → 追加 LESSONS.md（含检测方法）
12. 新问题 → 更新 workbench/（**caveats 条条变问题**）
13. 写 iterations/roundNN/HANDOFF.md
14. 生成下一轮 TASK_BRIEF.md（否则这条链就断了）
15. 写 journal/roundNN.md
16. **升版本** ← ★ 改了哪些内容就升哪些文件的 content_version，
    并在 VERSION_INDEX 里留一行演化记录
17. 跑 python cli/main.py versions      ← 版本一致性
18. 跑 python cli/main.py validate --all
```

**第 16 步是本次新增的**。**改了内容不升版本 = 索引记录的是错的，比没有索引更坏。**

详细协议见 `framework/protocol/ITERATION_PROTOCOL.md` 与 `MEMORY_PROTOCOL.md`。

---

## 8. 校验与命令

```bash
# 全量校验（schema + 外键 + 红线恒值 + 双向取代 + features 声明可执行性
#           + predicate 作用域 + ★ 版本一致性）
python cli/main.py validate --all -v

# ★ 版本一致性检查（文件内版本行 ↔ versions.json ↔ VERSION_INDEX.md）
python cli/main.py versions

# ★ 重生版本索引（改完 versions.json 后）
python tools/render_version_index.py --write

# 只校验结论台账
python cli/main.py validate --facts

# 从 FACTS.jsonl 重新生成 INDEX.md
python cli/main.py index

# 生成策略输出
python cli/main.py strategy --game dlt

# 列出现有彩种
python cli/main.py games

# ★ 生成号码（只执行单注层规则；跨注规则数在 stats 里显式上报）
python cli/main.py pick --game dlt -n 10 --seed 20261011

# ★ 对一注号码求值 + 判定
python cli/main.py eval --game dlt --ticket "03 11 17 24 32 + 04 09"
```

### 库接口（`from smartpickcore.api import SmartPick`）

```python
sp = SmartPick("dlt")

sp.evaluate(ticket)        # 求值全部声明特征 → dict
sp.judge(ticket)           # 判定（自动只跑单注层）→ JudgeResult
sp.rule_scopes()           # {"single": [...], "cross": [...], "cross_reasons": {...}}
sp.pick(n=10, seed=...)    # 生成 n 注
```

> 若命令未实现，`cli/main.py` 会打印清晰的"未实现"提示而非静默成功
> —— 静默成功比报错危险。

### ★ 作用域：本仓库最容易误用的地方

`strategy.json` 的 `R-002` predicate 是 `duplicated_structure_across_tickets == true`
—— **跨注特征，一注号码算不出来**。

| 层 | 规则 | 能否单注判定 |
|---|---|---|
| 单注层 | R-001（`has_run_ge2 == true` → exclude） | ✅ |
| 跨注层 | R-002（结构分散度 → penalize 0.5） | ❌ 需要整组号码上下文 |

`sp.judge(ticket)` **自动只跑单注层**，跨注规则在 `rule_scopes()` 里可见。
`pick` 命令会把跳过的跨注规则数写进 `stats["cross_scope_skipped"]`。

> **禁止静默忽略跨注规则** —— 那会让调用方以为"全部规则已生效"。

---

## 9. 自我迭代机制（本仓库的立身之本）

**迭代不靠"AI 灵光一现"，靠一条机械的传导链：**

```
每条结论必须写 caveats（减损项）
        ↓ 自动（不是可选）
每条 caveat 变成一个 OPEN_QUESTION
        ↓
问题进入 workbench/TODO.md，带脚本路径与验收判据
        ↓
下一轮 TASK_BRIEF.md 从中挑 P0 项
        ↓
答出 → 新 FACTS 条目（或更新旧条）
        ↓
新的 caveats …… 循环
```

**框架本身也被迭代**：每轮 `journal/` 的最后要有「对框架本身的改进建议」
（见 `round02.md` §5 的 R-1 ~ R-5）。这些建议进入 `TODO.md` 的 P4 段，
由后续轮次评审采纳。

> **这就是"每轮 AI 给出更好的研究框架"的具体落地方式** ——
> 不是让 AI 自由发挥，而是让框架带着**已识别的缺陷**进入下一轮。
> 缺陷是显式记录的（caveats），不是靠 AI 恰好想到。

---

## 10. 明确不做的事

- ❌ **不做号码预测**。序列不可预测（F-0008），任何预测都是噪声。
- ❌ **不声称提高中奖概率**（红线）。
- ❌ **不给"推荐号码"**。策略是**约束**（避开什么、偏好什么），
  不是具体号码 —— 具体号码无信息量，且容易被误读为"更可能中"。
- ❌ **不鼓励投注**。长期期望恒为负（F-0002）。
- ❌ **不在完成独立分析前读 `games/dlt/iterations/round02/legacy_findings/`**
  —— 那是历史产出的归档，设了使用门槛（防锚定）。

---

## 11. 风险与责任

本仓库的所有输出都遵守以下立场（对消费者同样有效）：

1. 彩票是**负期望游戏**，长期投注**必然亏损**（F-0002）。
2. 本仓库的一切结论**不提高中奖概率**（红线，数学事实）。
3. 唯一可优化量是"中奖时的期望奖金"，且幅度有限、受封顶稀释、
   只在极小概率的中奖事件上兑现。
4. 任何分析结果**不得用于借贷投注**或其他超出承受能力的支出。
5. **理性购彩，量力而行。**

> 这一立场不写在附录里，写在**入口**里。
> 因为它不是免责声明，它是**结论的一部分**。
