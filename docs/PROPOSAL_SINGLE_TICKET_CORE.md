# PROPOSAL — 单注层通用架构（Single-Ticket Core）

> **版本**：`1.1` ｜ 轮次 `r03` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **状态**：✅ **已落地**（全部 11 步完成，`validate --all` 33 项全绿，`tests/test_core.py` 92 项全绿）
> **日期**：2026-10-11（提案）/ 2026-10-11（落地）
> **提出缘起**：对外问答暴露三处缺口（见 §1）
> **实施结果**：见 §10「落地记录」

---

## 1. 缘起：三处已暴露的缺口

在「买单注还是多注」「推荐号码」两次对外问答中，暴露了三处结构性缺口：

| # | 缺口 | 现状 | 后果 |
|---|---|---|---|
| **G1** | **没有号码生成器** | `CONSUMING.md` 明确写「求值语义属于消费方，本仓库只承诺规则是什么」。`machine_rule.predicate` 是一串**给人看的字符串**，没有任何代码能执行它 | 用户要号码时，只能由 AI 临时手写拒绝采样脚本（本次就是这么做的），**不可复现、无校验、无版本** |
| **G2** | **单注级能力散在彩种目录** | 特征计算在 `labs/lottery/studies/dlt/data/tools/_load.py`，撞号模拟在 `labs/lottery/studies/dlt/strategy/strategy_simulation.py` | 接入第二个彩种时要复制粘贴。**违反「唯一硬标准」** |
| **G3** | **多注/组合层完全未建模** | R-002（结构分散）只有推论，`magnitude_pct: null`。`open_questions` 的 Q-001~Q-008 **全是单注策略问题**，组合分散度无对应条目 | 对外输出给出了一条**未量化**的规则，用户无法判断该不该听 |

**共同点**：三者都卡在同一个位置 —— **"一注号码"这个对象，框架里没有一等公民的身份**。
`game.yaml` 描述了号码空间，`strategy.json` 描述了规则，但**中间那层「拿一注号码，能否算出它的特征、能否判定它合规、能否给它打分」是缺失的**。

这就是「单注层通用架构」要补的东西。

---

## 2. 目标与非目标

### 目标

1. 把「一注号码」抽象成框架的**一等公民**（`Ticket`），特征计算由 `game.yaml` 声明驱动
2. 提供**彩种无关**的 `predicate` 求值器，让 `machine_rule` 从「给人看的字符串」变成「可执行且可校验的约束」
3. 提供**通用生成器**（拒绝采样 / 加权采样），任何彩种配置即可用
4. **不引入跨彩种硬编码**：`platform/core/` 里不得出现 `35` / `12` / `"dlt"`
5. 让 G1/G2/G3 有一个**统一的落点**，而不是三处打补丁

### 非目标（本轮明确不做）

| 不做 | 原因 |
|---|---|
| 迁移 `strategy_simulation.py` 的统计逻辑到 core | 那是「已发生的复用」才该做的抽象，目前只有一个彩种。**违反 `platform/core/README.md` 的实践原则** |
| 量化 R-002（组合分散度） | 那是**研究问题**（Q-009），不是架构问题。架构要为它**预留位置**，但不替它下结论 |
| 建 Web UI / 前端 | 用户已明确范围在「单注层的通用架构」 |
| 修改 `strategy.json` 的 `rules` | 规则是研究产物，不由代码生成（`ITERATION_GUIDE.md` §4.3） |

---

## 3. 核心设计：三层抽象

```
┌─────────────────────────────────────────────────────────────┐
│  L3  Portfolio 层（多注）  ← 本轮只留接口，不实现            │
│      · 组合分散度打分                                        │
│      · 预算约束下的选择                                      │
│      · ⚠️ 期望中奖注数 = N/T，与分散度无关（线性）            │
├─────────────────────────────────────────────────────────────┤
│  L2  Scoring 层（评分/判定）                                 │
│      · evaluate(ticket) → {feature: value}                   │
│      · judge(ticket, rules) → exclude | penalize | prefer    │
│      · score(ticket) → float                                 │
├─────────────────────────────────────────────────────────────┤
│  L1  Ticket 层（一注号码）★ 本轮核心                         │
│      · Ticket = {zones: {front: [...], back: [...]}}         │
│      · 由 machine.zones 机械校验合法性                        │
│      · 由 features 声明机械计算特征                           │
└─────────────────────────────────────────────────────────────┘
```

### L1 — `Ticket`（一注号码）

**关键决策：`Ticket` 不含任何彩种知识。**

```python
class Ticket:
    """一注号码。结构由 machine.zones 决定，本类不含彩种参数。"""
    zones: dict[str, tuple[int, ...]]   # {"front": (3,11,17,24,32), "back": (4,9)}

    @classmethod
    def from_lists(cls, **zones): ...

    def validate(self, cfg) -> list[str]:
        """对照 machine.zones 校验：取值范围、个数、去重、有序性。"""
```

**为什么用 `dict[str, tuple]` 而不是 `front: list, back: list`**：
`machine.zones` 是**可变长度**的数组（大乐透 2 区、双色球 2 区、七星彩 1 区、排列五 1 区有序）。
写死 `front`/`back` 就等于把 dlt 的字段名硬编码进框架。

**特征计算的驱动方式 —— 这是最关键的一处设计**：

`game.yaml` 的 `features[].formula` 目前是**给人看的字符串**（如 `"sum(front)"`）。
三个选项：

| 选项 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| **A. 求值 formula** | 把 `formula` 当表达式解析执行 | 配置即代码，最灵活 | **安全风险**（`eval`）；DSL 表达能力有限，复杂特征写不出来 |
| **B. 注册表 + 声明绑定** ★ | 框架提供**通用原语**（连续对数、跨度、和值、奇偶…），彩种在 `game.yaml` 里**声明用哪个原语 + 参数** | 无 `eval`；原语彩种无关、可测试 | `game.yaml` 需从"公式字符串"改为"原语调用"（**破坏性变更**） |
| C. 彩种自己写 Python | 特征函数放 `games/<id>/` | 最灵活 | **框架无保证**，校验器无法验证 predicate（回到 G1） |

**推荐 B**。理由是它**唯一能同时满足**「`predicate` 可执行」与「框架不含彩种知识」：

```yaml
# game.yaml（改造后）
features:
  - key: has_run_ge2
    label: 是否存在 >=2 个相邻号对（3 连及以上）
    type: boolean
    primitive: adjacent_pair_count_ge     # ← 框架提供的通用原语
    args: {zone: front, threshold: 2}     # ← 彩种给的参数
```

框架侧：

```python
# platform/core/features.py —— 全是彩种无关原语
PRIMITIVES = {
    "sum":                  lambda z, **kw: sum(z),
    "span":                 lambda z, **kw: max(z) - min(z),
    "count_odd":            lambda z, **kw: sum(1 for x in z if x % 2),
    "count_ge":             lambda z, threshold, **kw: sum(1 for x in z if x >= threshold),
    "adjacent_pair_count":  lambda z, **kw: sum(1 for a,b in zip(z, z[1:]) if b-a == 1),
    "adjacent_pair_count_ge": lambda z, threshold, **kw: adjacent_pair_count(z) >= threshold,
    "all_le":               lambda z, threshold, **kw: all(x <= threshold for x in z),
    # ... 纯数学，无彩种参数
}
```

**新增彩种时**：如果它的某个特征现有原语表达不了 → 往 `PRIMITIVES` 加一个**纯数学**函数。
**这不违反"唯一硬标准"** —— 加的是彩种无关的通用原语，不是彩种分支。

### L2 — 求值与判定

```python
def evaluate(cfg, ticket) -> dict[str, Any]:
    """按 cfg['features'] 声明算全部特征。"""  # 纯机械，无判断

def judge(cfg, ticket, rules) -> dict:
    """对每条 rule 的 machine_rule 求值。
    返回 {"excluded": bool, "weight": float, "matched": [rule_id...]}"""
```

**`predicate` 的 DSL —— 必须足够小以致可穷举验证。**

现状是裸字符串 `"has_run_ge2 == true"`。建议收紧为**受限表达式**，只允许：

```
<feature_key> <op> <literal>
op ∈ { ==, !=, <, <=, >, >= }
literal ∈ { true, false, 整数, 浮点 }
连接词： and / or （二选一，不支持混合嵌套，避免优先级歧义）
```

**为什么故意这么弱**：校验器要能**静态确认**每个 `feature_key` 都在 `game.yaml` 的 `features[]` 里存在
（现在做不到，`spec/strategy.schema.json` 只校验了 `predicate` 是非空字符串）。
DSL 越弱，静态可验证性越强。

**建议加进 `strategy.schema.json`**：

```jsonc
"predicate": {
  "type": "string",
  "pattern": "^[a-z_][a-z0-9_]*( *[=!<>]= *(-?[0-9]+(\\.[0-9]+)?|true|false))( *(and|or) *[a-z_][a-z0-9_]*( *[=!<>]= *(-?[0-9]+(\\.[0-9]+)?|true|false)))* *$"
}
```

这样**格式错误的 predicate 根本存不进去**（与四条红线同一思路：结构性拒收）。

### L3 — Portfolio（多注层）

**本轮只定义接口，不实现算法。** 因为 R-002 未量化（G3），实现等于用未验证的假设写代码。

但接口必须现在定，否则将来加会破坏 L1/L2：

```python
def spread_penalty(cfg, tickets, rules) -> float:
    """给定一组注，返回结构重复度惩罚（0 = 完全分散）。
    ⚠️ 不影响期望中奖注数（恒为 N/T）。当前仅有 R-002 的推论支撑。"""
    raise NotImplementedError("R-002 未量化，见 Q-009")
```

**强制 `NotImplementedError`** —— 与 CLI 的约定一致（「未实现必须明确报错，不得静默成功」）。
避免将来有人误以为它已经在工作。

---

## 4. 接口边界（谁负责什么）

| 层 | 位置 | 允许出现 | 禁止出现 |
|---|---|---|---|
| 原语 | `platform/core/features.py` | 纯数学函数 | 彩种参数、字段名 |
| 求值 | `platform/core/evaluate.py` | 读 `cfg['features']` 机械执行 | 判断「哪条结论对」 |
| 判定 | `platform/core/judge.py` | 读 `rules[].machine_rule` | 生成规则 |
| 生成 | `platform/core/generate.py` | 拒绝/加权采样 | 彩种专属采样逻辑 |
| 配置 | `games/<id>/game.yaml` | 值、参数、原语选择 | 代码 |
| 规则 | `games/<id>/strategy/strategy.json` | 规则内容 | — |

**依赖方向（不可逆）**：

```
cli/  →  src/spc/  →  platform/core/  →  (无依赖)
                                      ↑
                            games/<id>/game.yaml（仅作数据输入）
```

`platform/core/` **不得 import 任何 `games/` 下的 Python 代码**，只读 `game.yaml`。

---

## 5. 对现有资产的改动清单

| 文件 | 改动 | 破坏性 |
|---|---|---|
| `labs/lottery/studies/dlt/game.yaml` | `features[]` 从 `formula: "sum(front)"` 改为 `primitive: sum, args: {zone: front}` | ⚠️ **是**（`config_version` 需 1.0 → 2.0） |
| `spec/game_config.schema.json` | `features[]` 增加 `primitive`/`args`，`formula` 降为可选的人类可读注释 | ⚠️ **是** |
| `spec/strategy.schema.json` | `predicate` 加 pattern 约束 | ✅ 否（收紧，现有值合规） |
| `platform/core/*.py` | **新建** 5 个模块 | 新增 |
| `src/spc/api.py` | 加 `SmartPick.evaluate()/judge()/pick()` | 新增 |
| `cli/main.py` | 加 `pick` / `eval` 命令 | 新增 |
| `docs/CONSUMING.md` | 改写 §"predicate 是给人看的字符串" | ⚠️ 是（立场变更） |
| `spec/VERSIONING.md` | 记 `game_config` 主版本 2.0 | 新增条目 |

**`CONSUMING.md` 的立场变更是本轮最需要你拍板的一点**：

> 现状：**"本仓库故意不提供求值器，因为求值语义应属于消费方"**
> 提案：**改为"本仓库提供参考求值器；消费方仍可自实现，但不再必须"**

这不是小改 —— 它把本仓库从「只输出规则」变成「也提供规则执行」。
**理由**：G1 的痛点恰恰是"消费方必须自己实现"导致每个消费方都可能实现错（尤其 A-008 那类误读）。
但**代价**是契约面扩大，将来 `predicate` DSL 变更会影响更多下游。

**这一条我倾向让你决定。**

---

## 6. 为什么这样设计（对齐既有原则）

| 设计 | 对齐的原则 |
|---|---|
| `Ticket` 用 `dict[str, tuple]` 而非 `front/back` | `platform/core/README.md`「禁止出现 'dlt'」 |
| 特征用「原语注册表」而非 `eval(formula)` | 安全 + 「框架不知道'连号'是什么，只执行声明」 |
| `predicate` DSL 故意做弱 | 与四条红线同一思路：**结构性拒收**优于文档劝告 |
| L3 只留接口、强制 `NotImplementedError` | `platform/core/README.md`「不为可能的复用做抽象」+ CLI「未实现必须明确报错」 |
| 不迁移 `strategy_simulation.py` | 同上 —— 只有一个彩种时看不出哪里真通用 |

**与 `game.py` 现有 `compute_space()` 的关系**：
它已经在做「由 `machine.zones` 机械算 T」，是 L1 的雏形。
本轮把同一思路从「号码空间级」下沉到「单注级」。

---

## 7. 实施步骤（确认后执行）

| # | 步骤 | 产出 | 可验证判据 |
|---|---|---|---|
| 1 | 写 `platform/core/features.py` 原语库 | ~12 个纯数学原语 | 单测：每个原语对固定输入给固定输出 |
| 2 | 写 `platform/core/ticket.py` | `Ticket` + `validate(cfg)` | 非法票（越界/重复/个数错）全部报错 |
| 3 | 改造 `game.yaml` 的 `features[]` 为原语声明 | 11 个特征改写 | `validate --game dlt` 通过 |
| 4 | 更新 `spec/game_config.schema.json` | `primitive`/`args` 支持 | 旧格式被拒（确认破坏性） |
| 5 | 写 `platform/core/evaluate.py` + `judge.py` | 求值与判定 | 对 `strategy.json` 的 R-001 求值，结果与手工一致 |
| 6 | 收紧 `spec/strategy.schema.json` 的 `predicate` | pattern | 故意写错的 predicate 被 schema 拒收 |
| 7 | 写 `platform/core/generate.py` | 拒绝/加权采样 | `pick --n 10` 全部满足 R-001 |
| 8 | 加 CLI `pick` / `eval` 命令 | 2 个命令 | `pick` 输出格式与本次手写的一致 |
| 9 | 加 `tests/` 用例（红线测试最高优先） | 测试 | 全绿 |
| 10 | 更新 `CONSUMING.md` / `VERSIONING.md` / `AI_CONTEXT.md` | 文档 | 立场表述一致 |
| 11 | 跑 `validate --all` + 提交推送 | commit | 31+ 项全绿，单 main 分支 |

**规模估计**：~600–800 行（含测试），`platform/core/` 从 0 到 5 个模块。

---

## 8. 需要你决策的 4 点

| # | 问题 | 选项 | 我的倾向 |
|---|---|---|---|
| **D1** | `features` 改造方式 | A 求值 formula / **B 原语注册表** / C 彩种自写 | **B** — 唯一能兼顾可执行与彩种无关 |
| **D2** | 是否提供求值器 | **提供参考实现** / 保持"消费方自实现" | **提供** — 但这条影响契约面，需你拍板 |
| **D3** | `predicate` DSL 强度 | **弱（只允许比较+and/or）** / 中（支持算术） / 强（完整表达式） | **弱** — 静态可验证优先 |
| **D4** | 是否同时补 Q-009（R-002 量化） | **分开做（先架构后研究）** / 一起做 | **分开** — 架构与研究混在一轮会互相污染 |

---

## 9. 本轮不碰的东西

- ❌ 不改 `strategy.json` 的 `rules` 内容（规则是研究产物）
- ❌ 不迁移 `strategy_simulation.py`（未发生复用）
- ❌ 不动 `labs/lottery/studies/dlt/memory/facts/FACTS.jsonl`（本轮无新结论）
- ❌ 不新增 Q-009（属 D4）
- ❌ 不建 Web UI

---

## 10. 落地记录（2026-10-11）

### 10.1 决策采纳情况

| # | 问题 | 决策 | 落地位置 |
|---|---|---|---|
| D1 | `features` 改造方式 | **B 原语注册表** | `platform/core/features.py`（21 个原语）+ `labs/lottery/studies/dlt/game.yaml`（11 个特征改写） |
| D2 | 是否提供求值器 | **提供参考实现** | `platform/core/judge.py`；`docs/CONSUMING.md` §6 立场已改写 |
| D3 | `predicate` DSL 强度 | **弱 DSL** | `spec/strategy.schema.json` 的 `pattern` + `platform/core/judge.py` 的 `parse_predicate()` |
| D4 | 是否同时补 Q-009 | **分开做**（架构已落地，Q-009 仍未写入） | `labs/lottery/studies/dlt/memory/workbench/OPEN_QUESTIONS.md` 待补 |

### 10.2 与提案的偏差

| 项 | 提案 | 实际 | 原因 |
|---|---|---|---|
| 原语数量 | ~12 个 | **21 个** | 实现时发现「连号」需要 3 个不同的量（对数 / 阈值对数 / 布尔），且 `count_in_range` / `max_in_range` / `sum_mod` 是常见需求 |
| `platform/core/` 模块数 | 5 个 | **6 个** | 增加 `game_util.py` —— 把 T / p1 / 声明校验从 `game.py` 下沉为纯函数，避免循环依赖 |
| 步骤 9 测试规模 | 未估 | **92 项** | 红线 4 项 + 原语 30 项 + Ticket 校验 15 项 + DSL 14 项 + 作用域 8 项 + 数学 6 项 + 端到端 9 项 + 声明检查 6 项 |

### 10.3 ★ 落地过程中发现的结构性问题（提案未预见）

**R-002 的 predicate 引用了不存在的特征。**

```
R-002: "duplicated_structure_across_tickets == true"
                                              ↑ 这个特征不在 game.yaml 里，也永远不可能在
```

**根因**：这是一条**跨注规则** —— 「整组号码的结构是否重复」需要**多注上下文**，
一注号码**不可能**算出它。这正是原提案 §2「非目标」里写的 L3 边界，
但提案没预见到**它已经存在于现行的 `strategy.json` 里**。

**如果不处理会发生什么**：`judge(cfg, ticket, rules)` 会在求值时抛 `PredicateError`。
若为了「让它跑起来」而用 `try/except` 吞掉异常，**同批规则的 `R-001` 会一起失效**
—— 静默降级，比报错危险得多（正好是 CLI「未实现必须明确报错」原则的反面）。

**处理方式**：设计 `split_by_scope()` / `apply_scope()`，把规则按作用域切开：

| 类别 | 判定 | 处理 |
|---|---|---|
| `single` | 全部特征已在 `game.yaml` 声明 | 单注层正常判定 |
| `cross` | 引用了未声明特征 | **显式上报**，不静默忽略 |

- `SmartPick.judge()` 自动只跑 `single` 层
- `sample_filtered()` 把跳过的跨注规则写进 `stats["cross_scope_skipped"]`
- `validate_strategy()` 对未声明特征给 **warning**（区分「跨注」与「拼错」）

**未决（属研究/契约问题，不属架构）**：`strategy.json` 的 R-002 本身该怎么处置 ——
改 predicate、加跨注层特征声明、还是保持现状只给 warning。这是**已向用户提出、待决策**的点。

> **◆ 后续补记（r03 框架迭代，config_version 2.1）**：此项已决策并落地 ——
> 选 **② 加跨注层特征声明**。当时的三选一里只有 ① 和 ③ 能维持"单注层自洽"，
> 但它们都等于**承认契约缺一层**：`R-002` 被发布出去却永远执行不了。
> 现在的形态：
>
> | 当时 | 现在（2.1） |
> |---|---|
> | 跨注特征**从未声明** | `game.yaml` 显式声明 3 个 `scope: cross` 特征 |
> | 跨注原语**不存在** | `CROSS_PRIMITIVES` 独立注册表，5 个跨注原语 |
> | `split_by_scope()` 二路切分，"跨注"与"拼错"混为一谈 | `classify_rules()` **三路**切分：`single` / `cross` / `undeclared` |
> | 跨注规则只上报、不执行 | `portfolio.py` + `judge_cross()` **真正执行** |
> | `stats["cross_scope_skipped"]` | `stats["cross_scope_pending"]` / `undeclared_skipped` / `cross_scope_evaluated` |
> | `validate` 对未声明特征给 warning | 给 **error**，并对跨注规则做**真样本冒烟执行** |
>
> 另：本提案 §10.5 的 G3 由"部分闭合"升级为"**执行层已闭合，量化仍缺**"。

### 10.4 验证结果

```
python tests/test_core.py
  通过 92  失败 0  ✅ 全部通过

python cli/main.py validate --all -v
  ✓ 全部通过（33 项检查）
  ⚠ 1 项警告：strategy[dlt].R-002 predicate 引用了未声明的特征
              ['duplicated_structure_across_tickets']（见 §10.3）

python cli/main.py pick --game dlt -n 10 --seed 20261011
  10 注全部满足 R-001，接受率 1.000，注间唯一，spread_penalty = 0.2083

python cli/main.py eval --game dlt --ticket "03 11 17 24 32 + 04 09"
  通过（R-001 未命中）
python cli/main.py eval --game dlt --ticket "04 18 22 23 24 + 01 06"
  被 R-001 排除（22-23-24 三连）
```

### 10.5 缺口闭合情况

| # | 缺口 | 状态 |
|---|---|---|
| G1（无生成器） | ✅ 闭合 —— `pick` 命令 + `SmartPick.pick()` + `generate.py`，可复现（`--seed`） |
| G2（单注能力散在彩种目录） | ✅ 闭合 —— 21 原语 + Ticket + 求值 + 判定全在 `platform/core/`，彩种只提供 `game.yaml` 声明 |
| G3（多注层未建模） | ⚠️ **部分闭合** —— L3 接口已建（`spread_penalty` / 跨注规则上报），但**量化研究仍未做**（Q-009 未写入） |

> G3 的剩余部分**不是架构问题**，是研究问题。架构已为它预留了位置。
