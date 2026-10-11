# TODO.md — 待办池（工作记忆）

> **版本**：`1.7` ｜ 轮次 `r08` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **性质**：跨轮次的任务池。`OPEN_QUESTIONS.md` 是"要回答什么"，
> 本文件是"具体要动手做什么"。
>
> **规则**：只放**未完成**项。完成后**移到 `journal/` 或删除**（与问题池不同，
> 待办是易耗品，不需要留档 —— 它的价值已在结论里兑现）。
>
> **更新时机**：每轮迭代开始前扫一遍，结束时清算。

---

## ✅ r03 已清算（留档一行，便于追溯）

| 任务 | 状态 | 落点 |
|---|---|---|
| T-001 撞号效应分期稳健性 | ✅ done | 更新 F-0003；`b2_split_stability.py` |
| T-002 稳健估计量对照（偿 L5） | ✅ done | 新增 F-0018；`b2_robust_estimators.py` |
| T-003 条件模拟加入 1 亿封顶 | ✅ done | 新增 F-0016/F-0017、更新 F-0004、推翻 F-0015；`cap_adjusted_uplift.py` |
| T-004 跑通 `validate --all` | ✅ done | 43 项通过 |

---

## ✅ r04 已清算（留档一行，便于追溯）

| 任务 | 状态 | 落点 |
|---|---|---|
| T-010 后区撞号建模 | ✅ done | 新增 F-0025、修正 F-0011；`round04/scripts/back_collision.py` |
| T-012 奖金瓜分机制与择时 | ✅ done | 新增 F-0023/F-0024、strategy 新增 A-009；`round04/scripts/prize_mechanism_tobit.py` |
| T-013 撞号效应衰减归因 | ✅ done | 新增 F-0019~F-0022、更新 F-0003/F-0004；`round04/scripts/decay_cause.py` |
| T-004 跑通 `validate --all` | ✅ done | 52 项通过 |

---

## ✅ r05 已清算（留档一行，便于追溯）

| 任务 | 状态 | 落点 |
|---|---|---|
| T-011 撞号效应的星期交互（H-005） | ✅ done | **证伪（方向相反）**：周六连号撞号效应更弱（w2 run×sat −0.607，p<0.0001），不构成可利用择时；新增 F-0030、H-005 标 refuted；`round05/scripts/timing_weekday.py` |
| T-202 R-002 量化（Q-012） | ✅ done | **期望效应不成立**（CI 含 0 → not_established，权重应改 1.0）；新增 F-0028/F-0027；`round05/scripts/bet_structure.py`。**策略处置待用户确认** |
| T-205 最优投注方式研究（用户点名） | ✅ done | 投注方式等价性（F-0026）、重复投注自我摊薄（F-0027）、凯利负期望（并入 F-0026/F-0002）；R-003 候选（避开连号+生日号，F-0029）；`round05/scripts/bet_structure.py` |
| T-206 时间因素研究（用户点名） | ✅ done | 星期×撞号（F-0030）、奖池 AR(1)（F-0031）、节假日探索（F-0032/H-006）；`round05/scripts/timing_weekday.py` |

---

## P0 — 阻塞性 / 正确性欠账

**（r03 / r04 / r05 已全部清偿；r08 起新增 T-046）**

- [x] **T-046** ★ r08 首推：R-002 `magnitude_pct` 量化补齐
      R-002 是唯一「可执行但未量化」的跨注规则（T-033 遗留：`strategy.json` 中
      `magnitude_pct` 仍为 `null`，跨注规则求值需传入整组号码）。
      口径锁定：后段 `dlt_full_2933`。已知数据坑——`draw_num` 为字符串、
      `prize1_amount_yuan` 右删失（单期封顶 1 亿未触发，F-0016，但右删失影响奖金均值估计，须写入 `caveats`）。
      方法（文献 27/28/29）：比例类用 Wilson 区间、连续量用 bootstrap（小样本禁用 CLT 正态近似）；
      重抽样 T≥5 且同一期号内多条记录按聚类稳健标准误处理；与其他并行判据联用时 Holm 校正；
      三态判定 PASS / FAIL / INCONCLUSIVE（INCONCLUSIVE 不算失败，照常过闸门并带 `caveats`）；
      功效分析前置，样本不足直接判 INCONCLUSIVE，禁止硬跑后勉强报显著。
      产出：`magnitude_pct` 填入「点估计 + 95% CI + 口径标注」（落点在 strategy 层规则对象，
      **不写入 `evidence.effect`**）；新增 empirical 事实条目过三闸门；
      命名一致性——`expected_value_impact.metric` 已统一为 `expected_bonus_given_win`（本轮已改）。

## P1 — 策略增强（可能新增可用规则）

- [x] **T-049** ★ r08 新增：`expected_bonus_given_win` 口径由头奖改为全奖级 ✅ **已落地（F-0036）**
      **缺口**：`bet_structure.py:212-228` 的 `collision_and_prize()` 只用 `pool_anchor`（一等奖派发），
      全脚本无 `prize3..prize7` 任何字样 → 三至七等奖从未进入计算。
      原始数据 `dlt_full_2933.csv` 亦只有 `prize1_*` / `prize2_*`（L10 兑现）。
      **影响**：`metric` 的分母口径实为「中一等奖」（4.667e-08），而真实体验是「中任意奖级」——
      P(任中) = 419335/21425712 = **0.019572（1/51.1）**，相差 **419,343 倍**。
      **核心数字**：固定奖（三~七等）定值期望 **0.095327 元/2元注**，占全奖级期望 **34.98%**
      （L5 剔 1000 万单注封顶饱和口径；朴素口径 28.43%），该部分**与选号完全无关**。
      **换算**：R-001 +40.64% → **+26.42%**；R-003 +41.80% → **+27.18%**（方向不变，幅度下调约 35%）。
      **★ 对外表述硬伤已修**：净期望 −0.98 → **−1.7275 元/2元注**（口径B），
      原 `disclaimer.text` 低估了亏损。
      三条红线全部仍然成立。产出 `games/dlt/iterations/round08/scripts/all_tiers_expectation.py` + `.json`，
      `strategy.json` schema_version 1.1 → **1.2**。

- [x] **T-047** ★ r08 新增：F-0032 教训制度化 + FACTS 新增 NOOP
      F-0032 探索性结论复现失败的根因是**口径参数缺失**（结论写得出来，读者复现不出来）。
      分三步：
      1. **Judge 证据分档校验**（✅ 本轮已落地）：按 `claim_type` 分档强制「数据版本 / 口径 / 阈值参数」三要素。
         强校验档 `empirical` + `simulation`（实测 26/35 = 74%）任一缺失 → 退出码 2（拒绝），退出信息指明补哪个字段；
         `simulation` 额外要求 `evidence.source_sha256`。弱校验档 `methodological` / `documentary` 缺失 → 提示（计入建议 tentative）。
         `analytic` 解析可证，仅要求口径标注。已回归验证：对存量 35 条**零影响**，只对 r08 起新条目生效。
         实现见 `framework/tools/ingate.py` 的 `_evidence_tier()` 与 `STRICT_CLAIM_TYPES`。
      2. **NOOP 原子操作**（✅ schema 已就位）：显式记录「证据不足，维持原结论」，替代「什么都不写」的隐式状态。
         理论依据：文献 37（Memory-R1）将 NOOP 作为与 add/update/delete 同级的受训操作；
         文献 35 综述确认「更新/取代优于删除」的演化原则。
         **实现形式：`evidence.noop_count`（整数计数器）**——刻意不进 `status` 与 `change_type` 枚举，
         NOOP 语义上既非 initial/update 也非 revision，用独立字段承载避免污染既有状态机；存量条目为 null，语义等价于 0，不要求回填。
         字段定义已写入 `spec/fact.schema.json`。
      3. **版本号登记**：schema 变更走 `versions.json` + `python tools/render_version_index.py --write`
         重生成 `VERSION_INDEX.md`（**该文件由脚本自动生成，禁止手工编辑**）。存量条目无需改写。
      理论依据文档：`D:/WorkBuddy/2026-10-11-12-06-22/SPC_r08方案审阅报告.md`

- [x] **T-014** 前段（<2013-08）数据取证：不自洽的根因（Q-013）★ **r06 首推（r05 顺延）**
      三条恒等式互相核对（注数反推一致性 / 注数×票价 ≤ 销售额 / 单注与奖池公式自洽）
      + 时间轴定位异常区间（数据驱动切点，L3）
      产出：更新 F-0019（补根因），并决定 F-0003/F-0018/F-0004 的全样本数字处置
      （r05 说明：原 T-201 被用户点名方向（投注方式/时间因素）优先占用，本项顺延至 r06）

- [x] **T-015** 前段外部核对（Q-014）
      抽样 ≥30 期（覆盖 2007–2013）与官方/公开来源比对号码与中出注数
      产出：新增 F-0xxx 或更新 F-0019 的 caveats；无外部数据则标 `blocked`

## P2 — 质量提升（提升置信度）

- [ ] **T-048** ★ r08 新增：L3 组合优化预备（hold-out 评测设计，**本轮只做设计文档不落 L2**）
      L1 已有可组合的规则原料：F-0004（避开连号，中奖时期望奖金 +109%，后段口径，动态锚点）、
      F-0029（连号/生日号区撞号系数 0.425–1.005）、F-0027（同号 K 注自我摊薄 (1+m)/K）。
      两项设计：
      1. **评测设计**：以**时序 hold-out** 替代 shadow game——用后段最后 N 期做 hold-out，
         规则在训练窗拟合、hold-out 窗只评估一次（文献 31/32 的评估纪律）。
      2. **组合搜索边界**：组合只作用于**选号分布**（人群密度避让），
         输出仍为 `expected_bonus_given_win` 优化，三条红线不变。
      ⚠️ 引用陷阱：F-0004 是**奖金提升**而非概率提升，任何 L3 文案不得写成「提高中奖率」。

- [x] **T-016** 节假日窗口撞号效应验证（H-006）★ r05 新增
      农历春节日期精确映射（2007–2026）+ 国庆/元旦窗口复验（F-0032 探索性信号待确认）
      产出：新增 F-0xxx 或更新 F-0032 的状态（tentative → established / refuted）

- [x] **T-020** 逐号偏好权重建模（Q-006 / H-002）
      用 `prize2_winners` 全量回归校准，替代现有单一 α
      产出：`F-0004` 置信度可能从 ★★★☆☆ 提升

- [ ] **T-021** 销量内生性检验（Q-005）
      Granger + VAR；对比"含销量/不含销量"两版注数模型

- [ ] **T-022** 随机性错觉假设检验（H-001）
      枚举等差序列等"看起来不随机"的形态，测其撞号程度

- [ ] **T-023** 效应弱化的滚动复验（Q-011）★ r03 新增
      随数据增长重跑分期；若持续弱化须在 F-0003 标注

- [ ] **T-024** 机选占比的代理变量（Q-015）★ r04 新增
      用分布熵 / 重复结构率 / 低号占比构造代理，检验 F-0021 的「行为变化」通道是否可观测
      产出：新增 F-0xxx 或更新 F-0021 的 caveats

- [ ] **T-025** E6 固定奖加成是否真实发生（Q-016）★ r04 新增 `resource: external-data`
      需三至七等奖实发额（外部数据源）；先做事件计数再谈影响（L10）
      产出：新增 F-0xxx（拿到数据后）或保持 blocked

## P3 — 结构性 / 长期

- [ ] **T-030** 明确"策略有效性"的三档标准并写入 schema（Q-008）
      影响对外表达的可信度，属伦理与质量双重要求

- [x] **T-031** 第二个彩种接入（验证框架的通用性）✅ **r03 框架迭代已落地（影子彩种实测）**
      目前只有 `games/dlt/`。**框架是否真通用，只有接入第二个彩种才知道**
      这是验证"框架/彩种分离"设计的唯一硬标准

      **落地内容**：
      - 新增 `tests/fixtures/shadow/`（与 dlt **处处不同**的第二彩种夹具：9选3+5选2 / 红区 `min_value=0` / T=840 / 5 单注+2 跨注特征，与 dlt 零交集）
      - 新增 `tests/test_shadow_game.py`（**69 项**）：装载/校验/求值/判定/跨注/端到端/单区变体全链路在影子彩种跑通
      - 铁律扫描断言 `framework/` 与 `src/` 无 dlt 痕迹（AST 剥 docstring 防误报），并含**扫描器自检**确认非"永远全绿"
      - **结论：加入第二个彩种无需改 `framework/` 或 `src/` 任何一行 —— 硬标准首次通过**

- [ ] **T-032** 摇奖设备数据的获取评估（H-003）`resource: unverifiable`
      唯一的"推翻 F-0001"路径。当前标 `unverifiable_with_current_data`

- [x] **T-033** R-002 的 predicate 处置 ✅ **r03 框架迭代已落地（选 ② 加跨注层特征声明）**

      **原状态**：warning —— 引用未声明特征 `duplicated_structure_across_tickets`（跨注，L3）。
      **决策**：② 加跨注层特征声明。理由：① 与 ③ 只能维持"单注层自洽"，
      但都等于承认**契约缺一层**（策略被发布却无法执行）。

      **落地内容**：
      - `framework/core/portfolio.py` 新增（Portfolio 一等公民 + `evaluate_cross` + `judge_cross`）
      - `features.py` 新增 `CROSS_PRIMITIVES` 独立注册表（5 个跨注原语）
      - `game.yaml` 声明 3 个 `scope: cross` 特征（config 2.0 → **2.1**）
      - `strategy.json` `rules[]` 新增必填 `scope`；R-002 改引用 `has_duplicated_structure`（schema 1.0 → **1.1**）
      - `judge.classify_rules()` 三路切分 single / cross / undeclared
      - `validate_strategy()` 未声明特征由 warning 升 **error**，并对跨注规则**真样本冒烟执行**
      - 新增 `tests/test_cross_scope.py`（62 项）

      **剩余（不属于本条）**：`R-002.magnitude_pct` 仍为 `null` —— **可执行 ≠ 已量化**

## P4 — 框架自迭代（元层面）

- [ ] **T-040** 从本仓库实践中提炼的框架改进，回写 `framework/protocol/`
      r03 新增建议：**`evidence.effect` 应区分"观测事件"与"归因"两分**（F-0015 的教训）

- [x] **T-041** 自动化：`cli/main.py index` 从 `FACTS.jsonl` 重生成 `INDEX.md` ✅ **已实现（误报，命令位早已落地）**
      `cli/main.py` 的 `index` 子命令（`cmd_index` → `mem.write_index()`）**已实现**，
      `memory/facts/INDEX.md` 由 CLI 生成（`v1.2`，勿手改）。本条为误报，清账。

- [x] **T-042** 校验器增强：证据哈希 ✅ **r03 框架迭代·提案 C 已落地**
      `src/spc/evidence.py` 双锚定（事实级 `evidence.source_sha256` + 策略级 `provenance.evidence_hash`）；
      `validate.py` 检出证据文件变更；新增 `cli/main.py rehash` 重基线。对应 commit 已推送。

- [x] **T-043** 教训库补充 L10–L12 ✅ r03 已落地（`LESSONS.md` 1.0 → 1.1）
      L10 条款写了 ≠ 现实触发过（先做事件计数再谈影响）
      L11 锚点口径不可反推（须取实测可观测统计量）
      L12 换名字不算换人证（新旧估计量点估计是否数值等价）

      （呼应 `spec/VERSIONING.md` 中"数据层静默修改"的风险）

- [ ] **T-044** ★ r04 新增：`tools/build_versions.py` 与 `versions.json` 脱节
      该生成器内部的 `CONTENT_VERSIONS` / `DOC_VERSIONS` 表仍停留在 r02 的值，
      直接跑 `build_versions.py --write` 会把 versions.json **回退**；r04 只能手工维护索引。
      产出：把表同步到当前状态，或在文件头显式声明它已降级为"参考实现"并在 README 里写明正确的维护流程

- [ ] **T-045** ★ r04 新增：文档里的测试计数应自动注入
      同一轮里 `319/113/105` 三个陈旧计数散落在 README / AI_CONTEXT / tests/README / ITERATION_GUIDE / framework/core/README；
      `tools/count_tests.py` 已经能实跑计数，但结果要人手抄进文档。
      产出：给 count_tests.py 加 `--inject`（或新增注入脚本），让文档计数与实跑结果一致

---

## 已完成（本轮）

> r04 开始时已按约定清空本节。r03 的完成项见 `memory/journal/round03.md`；
> r04 的完成项见 `memory/journal/round04.md` 与 `games/dlt/iterations/round04/HANDOFF.md` §1。

---

## 使用约定

1. **编号**：`T-nnn`，按 P 级分配段位（P0: 001-009，P1: 010-019，P2: 020-029，P3: 030-039，P4: 040-049）
2. 每项必须写：**做什么 + 对应哪个 Q/H + 脚本路径 + 产出什么**
   —— 缺任一项的待办会变成"以后再说"的沼泽
3. **不写时间估计** —— 写清范围和验收判据比估时有用
4. 每轮 `HANDOFF.md` 必须说明：本轮清了哪些、留下哪些、为什么
5. 待办**可以删**（与结论和教训不同），但要经过 `HANDOFF.md` 记录
