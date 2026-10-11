# AI_CONTEXT.md — 单一入口

> **版本**：`1.5` ｜ 轮次 `r11` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **如果你是一个 AI（或人），要在这个仓库里做分析 —— 从本文件开始，读完本文件再动手。**
>
> 本文件约 10 分钟可读完。读完你能知道：这个仓库是干什么的、东西在哪、
> 三条不能违反的红线、以及**动手前必须知道的方法论纪律**。
>
> 最后更新：2026-10-11 | 当前轮次：`round04`（已交付）| 下一轮：`round05`（待启动）
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
SPC/
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
│   ├── lessons/           ★ LESSONS.md（L1–L14，动手前必读）
│   └── workbench/         OPEN_QUESTIONS / HYPOTHESES / TODO
├── games/                 彩种层（插件）
│   ├── _template/         新彩种模板
│   └── dlt/               超级大乐透（当前唯一实现的彩种）
│       ├── game.yaml      彩种声明式配置（config_version 2.0）
│       ├── rules_history.md   规则变更史（决定奖金类分析口径）
│       ├── data/          raw/（原始，不可变）+ derived/ + tools/ + build_scripts/
│       ├── iterations/    round01/ round02/ round03/ round04/ round05/
│       └── strategy/      strategy.json（对外输出）+ STRATEGY_GUIDE.md（★ 人话版）
│                           + 模拟脚本与结果
├── src/SPC/     库代码（api / memory / strategy / validate / versions）
├── cli/main.py            命令行入口（13 个命令）
├── tools/                 仓库维护脚本（版本索引：build / render / inject）
├── tests/                 test_core.py（117 项，无需 pytest）
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

> ⚠️ **r04 新增的口径警告（F-0019）**：**2013-08 之前那一段数据不能当基线** —— 它在
> 「号码分布—中出注数—销售额」三者间不自洽（前区号码分布 χ²=251.5；由中出注数反推的投注量
> 超出售额允许上限，每注均价 1.75~1.87 元 < 最低票价 2 元）。后段两项自洽。
> 凡是**含前段的全样本数字**，引用时必须声明为「历史口径」。

---

## 4. 动手前必读：方法论纪律

**先读 `memory/lessons/LESSONS.md`** —— 它记录了 14 条已付学费的错误。
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
| L10 | 条款写了 ≠ 现实触发过 | 触发次数是多少 ? |
| L11 | 锚点口径不可反推 | A 与 B 是同一口径吗 ? |
| L12 | 换名字不算换人证 | 新旧估计量点估计数值相同 ? |
| **L13** | **数字对 ≠ 口径唯一** | **换成中位数/截尾，还是这个数吗 ?** |
| **L14** | **先验段内自洽，再跨段比** | **反推量落在允许区间吗 ?** |

### 四条最容易越界的

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

**权威源是 `memory/facts/FACTS.jsonl`（45 条）**，此处只列最重要的几条。
引用前**必读该条的 `caveats`**。

| id | 结论 | 置信度 |
|---|---|---|
| **F-0001** | 任何选号方式都不能改变单注各奖级中奖概率（一等奖 1/21,425,712；任一奖级合计约 1/15，**解析可证**） | ★★★★★ |
| **F-0002** | 彩票是负期望游戏（返奖率 51%，净期望 −0.98 元/注） | ★★★★★ |
| **F-0003** | 连号形态人群更密（全样本注数比 **1.3603**；**后段 1.2472**，策略用后段口径） | ★★★★☆ |
| **F-0004** | 避开连号提高"中奖时期望奖金"：**后段口径上界 +109.4%**、含封顶 **+40.6%**（全样本上界 121%） | ★★★☆☆ |
| F-0005 | 连号**开出率**优势仅早期、不可用（与 F-0003 严格区分） | ★★★★☆ |
| F-0006 | 结构切点 **2013-08**（χ²=185.0, 1/234），渐变 | ★★★★☆ |
| F-0008 | 开奖序列**不可预测**（样本外 R² 全负） | ★★★★☆ |
| F-0014 | 规则变更 6 次，**号码结构从未改变**（号码类分析可跨全期） | ★★★★★ |
| F-0016 | 现行 **1 亿总额封顶从未触发**（E6 102 期最大 0.9788 亿） | ★★★★★ |
| F-0017 | 含封顶后 uplift 由 121% 降到实测锚点 41.4%（r04 后段口径 40.6%） | ★★★☆☆ |
| **F-0019** | **2013-08 之前那段数据三者不自洽**（号码分布 / 中出注数 / 销售额）→ 不能当基线 | ★★★★☆ |
| **F-0020** | "衰减过半"是**均值比口径**；稳健口径 0.65~0.83 | ★★★★☆ |
| **F-0021** | 弱化与 2013-08 号码结构变点**同期**；**销量稀释已排除** | ★★★☆☆ |
| **F-0022** | 后段口径重算：上界 **109.4%** / 含封顶 **40.6%** | ★★★☆☆ |
| **F-0023** | **不存在稳健的"高期望期"**（择时） | ★★★★☆ |
| **F-0024** | 用"派发额/销售额"衡量择时会误判（组成效应） | ★★★★☆ |
| **F-0025** | 后区撞号**存在但不可靠可利用**（交叉验证 CI 含 0） | ★★★★☆ |
| ~~F-0007~~ · ~~F-0015~~ | ~~2015 年断点~~ / ~~封顶已触发~~ **均已推翻**，禁引用 | — |

### 四个引用陷阱

1. **F-0004 的 +109%（全样本口径 +121%）不是中奖概率提升**，是"中奖时奖金"提升。
   写成"提高中奖率"是本仓库最严重的表述错误。
2. **口径必须写清**：全样本 1.3603 / 后段 1.2472；未计封顶 109% / 含封顶 40.6%。
   只写"121%"或"41%"而不写口径，等于把上界当承诺（F-0020 / F-0022）。
3. **含前段的全样本数字只是"历史口径"**：那段数据三者不自洽（F-0019）。
4. **F-0004 是模型估计（★★★☆☆），不是数学事实。** 不要把它当 F-0001 使用。

> ⚠️ **F-0015 已作废**（原称"26113 期触发封顶"）：F-0016 证明 E6 102 期**从未触发**，
> 单注 239 万是 37 注的自然摊薄。**任何把 F-0015 当作事实引用的文档都是过期的。**

---

## 6. 一条结论长什么样

```jsonc
{
  "id": "F-0004", "game": "dlt",
  "claim": "在固定预算下避开连号形态，可提高『中奖时的期望奖金』—— 后段口径上界约 109%，含封顶约 40.6%",
  "status": "established",
  "confidence": 3,
  "confidence_basis": "条件份额模拟（必须估计的量，无法解析给出）...",
  "category": "prize_mechanism",
  "claim_type": "simulation",                // ← ★ 证据类型：这个数字靠什么立住
  "affects_win_probability": false,          // ← 红线，恒 false
  "evidence": {
    "method": "条件份额模拟（100 注 × 300000 次抽样）",
    "result_summary": "撞号系数 1.0028 → 0.4528；比值 0.4515，95%CI [0.4487, 0.4543]",
    "effect": { "collision_factor_from": 1.0028, "collision_factor_to": 0.4528,
                "prize_uplift_pct_nocap_post": 109.39, "prize_uplift_pct_with_cap_anchor_post": 40.64,
                "calibrated_alpha_post_segment": 12.7815 },
    "ci95": [0.4487, 0.4543],
    "rules_epoch": "E6",
    "script": "games/dlt/strategy/strategy_simulation.py"
  },
  "caveats": [                               // ← 必读！每条 caveat 都是一个任务
    "模型依赖：α 由历史注数近似校准，是估计非真值。",
    "封顶稀释：单注 1000 万上限会把低注数情形的收益抹平为 0；1 亿总额封顶样本内从未触发（F-0016）。",
    "口径依赖：上界 121% 是全样本口径，后段口径为 109%（F-0020 / F-0022）。",
    "只在中奖时兑现：中奖概率不变，期望回报提升被极小概率大幅折现。",
    "长期期望回报仍为负（约 −0.98 元/注），本结论不改变这一事实。"
  ],
  "established_in": "round02（r04 复核口径）",
  "supersedes": null, "superseded_by": null,
  "source": "games/dlt/strategy/simulation_results.json"
}
```

**注意 `caveats` 的长度**：本仓库要求它非空。
一条没有减损项的结论，要么是数学定理，要么是作者没想清楚边界。

### ★ `claim_type`：引用一条结论前先看它靠什么立住

置信度（`confidence`）答「**有多可信**」；`claim_type` 答「**靠什么立住**」。
判据不是「用了什么方法」，而是「**它会在什么情况下变错**」：

| `claim_type` | 失效方式 | 强制项 | 本仓例 |
|---|---|---|---|
| `analytic` | 只有模型定义错了才会错 | 不得带 `p_value` / `ci95` | F-0001（组合数恒等式） |
| `empirical` | 数据换了、时段移位就会错 | 声明 `data_version` + `n_observations` | F-0003（2.11 → 1.25）· F-0019（前段不自洽） |
| `simulation` | 模型假设变了就会错 | `n_sim` 或 `rng_seed` 可复现；`caveats` ≥ 2 | F-0004 / F-0017 |
| `documentary` | 官方规则文本变了就会错 | 声明 `rules_epoch` | F-0002 / F-0014 |
| `methodological` | 关于方法本身的判断 | `caveats` 非空 | F-0007 / F-0018 / F-0020 / F-0024 |

填错会被 `validate --facts` **按类型拒收**（不是警告）。
最典型的坑：把模拟结论标成 `empirical` —— 那等于暗示"换个数据集就能解决"，
而 F-0004 的 109% 与 F-0017 的 40.6% 的差距恰恰来自**假设**（封顶与锚点），不是数据。

> 详见 `framework/protocol/MEMORY_PROTOCOL.md` §1.7。

### ★ 证据锚定：改了证据文件要能被发现

结论只存 `source` 路径是不够的 —— **路径还在 ≠ 内容没变**。

| 锚 | 位置 | 漂移时的含义 |
|---|---|---|
| `evidence.source_sha256` | 每条结论 | 证据文件被改 → 结论可能失效（`validate` 报 **error**） |
| `provenance.evidence_hash` | `strategy.json` | 被引结论被改 → 策略可能建立在旧结论上（报 **error**） |

摘要只取结论的**规范视图**（`claim` / `status` / `confidence` / `claim_type` /
`superseded_by` / `evidence.effect` / `caveats`），
**不含** `tags` / `updated_at` —— 无关编辑不该触发报警
（**会误报的检查比没有检查更坏**）。

**漂移了怎么办**（顺序不能反）：
① 确认结论是否仍成立 → ② 仍成立则 `python cli/main.py rehash --id F-xxxx`
（策略侧加 `--strategy`）重算基线 → ③ 不成立则改 status 并写新结论，旧条不得删。

> `rehash` 不是"消掉报警"的按钮，它只是把"重算基线"机械化，
> 避免手填哈希 —— 手填就又变成一次无人担保的断言。

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

### 库接口（`from SPC.api import SmartPick`）

```python
sp = SmartPick("dlt")

# —— 单注层 ——
sp.evaluate(ticket)        # 求值全部「单注」声明特征 → dict
sp.judge(ticket)           # 判定（自动只跑单注层）→ JudgeResult

# —— 跨注层（config_version 2.1 起） ——
sp.rule_scopes()           # {"single": [...], "cross": [...], "undeclared": [...], "cross_reasons": {...}}
sp.evaluate_portfolio([t1, t2, t3])   # 整组上下文求值跨注特征 → dict
sp.judge_portfolio([t1, t2, t3])      # 在整组上下文判定跨注规则 → JudgeResult

sp.pick(n=10, seed=...)    # 生成 n 注（若有 cross 规则会自动执行跨注层）
```

> 若命令未实现，`cli/main.py` 会打印清晰的"未实现"提示而非静默成功
> —— 静默成功比报错危险。

### ★ 作用域：本仓库最容易误用的地方

`strategy.json` 的 `R-002` 是**跨注规则**，一注号码算不出来，
必须拿到整组号码（`Portfolio`）才能判定。

| 层 | 规则 | 判定入口 |
|---|---|---|
| 单注层 | R-001（`has_run_ge2 == true` → exclude） | `sp.judge(ticket)` ✅ |
| 跨注层 | R-002（`has_duplicated_structure == true` → penalize 0.5） | `sp.judge_portfolio([...])` ✅ |

`sp.judge(ticket)` **自动只跑单注层**；跨注层必须显式传一组号码。
`rule_scopes()` 三路返回 `single` / `cross` / `undeclared` ——
其中 `undeclared` 表示"引用了根本没声明的特征"（拼错或遗漏），是**配置缺陷**，不是跨注。

`pick` 命令：存在 `cross` 规则时会构造 `Portfolio` **真正执行**跨注层，
结果写进 `stats["cross_scope_evaluated"]`；`undeclared` 的部分写进 `stats["undeclared_skipped"]`。

> **跨注规则要么被真正执行，要么被显式报错，禁止静默忽略**
> —— 那会让调用方以为"全部规则已生效"。

> **历史病（已在 2.1 修复）**：1.0 时 `R-002` 引用了 `duplicated_structure_across_tickets`，
> 该特征**从未在 `game.yaml` 声明过，且全仓库没有任何执行入口**。
> 策略被发布出去，消费者却无法执行它 —— 契约缺了整整一层。
> 现在该特征已正式声明为 `scope: cross` 并改名 `has_duplicated_structure`，
> `validate_strategy()` 会对每条跨注规则做**真样本冒烟执行**。

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
2. 本仓库的一切结论**不提高中奖概率**（各奖级概率恒定，红线，数学事实）。
3. 唯一可优化量是"中奖时的期望奖金"，且幅度有限、受封顶稀释、
   只在极小概率的中奖事件上兑现。
4. 任何分析结果**不得用于借贷投注**或其他超出承受能力的支出。
5. **理性购彩，量力而行。**

> 这一立场不写在附录里，写在**入口**里。
> 因为它不是免责声明，它是**结论的一部分**。
