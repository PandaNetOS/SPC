# TODO.md — 待办池（工作记忆）

> **版本**：`2.2` ｜ 轮次 `r16` ｜ 更新 2026-10-12 ｜ 权威源 `VERSION_INDEX.md`
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

- [x] **T-050** value: 90 ★ r10 首推：**概率数字口径标注根治**——「中奖概率 1/21,425,712」实际是**一等奖**概率，任一奖级合计约 1/15（6.67%）。
      FACTS/AI_CONTEXT/README/STRATEGY_GUIDE 中所有概率类表述必须带奖级限定（「一等奖」「任一奖级」「全奖级」）；
      validate 增加口径检查（出现「中奖概率」且上下文无奖级限定 → WARN/FAIL）。
      范围：F-0001 表述校正 + 全文检索「4.67e-08 / 21,425,712」逐处标注 + 校验规则落地。
      根因：静默错误——数值本身正确（=一等奖概率），错在标签语义无结构化承载，且手写速览区未纳入生成/校验闭环。

- [x] **T-048** ✅ **r11 完成**：L3 组合优化预备——时序 hold-out 评测设计文档（`round11/T048_HOLDOUT_DESIGN.md`，含切分/指标/防泄漏/组合搜索边界/验收护栏；不落 L2）
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

- [x] **T-020** 逐号偏好权重建模（Q-006 / H-002）✅ **r09 完成** → **F-0038**：后段逐号相对撞号强度 S_j（1.0=无偏好）号码间明显分异（9/11/19 偏高、35 偏低），生日段（1-31）均值 1.005 vs 高段（32-35）0.958（差 0.047，CI [-0.0109, 0.0962] 含 0 → 段级无显著差异）；OLS 逐号项 R² 由 0.00869 → 0.04527（ΔR²=0.03657，30/35 个号系数 |β|>0.05），n=1973。脚本 `round09/scripts/t020_number_weight.py`。
      **⚠ r16 补记**：本条此前**缺完成记录**，导致 r15 误判为「已勾选但无产出」（见 `round15/HANDOFF.md` §4）。产出一直存在（F-0038），缺口只是登记 —— 已完成项的 `✅ → F-xxxx` 记录不是装饰，是下轮不被误判的依据。
      用 `prize2_winners` 全量回归校准，替代现有单一 α
      产出：`F-0004` 置信度可能从 ★★★☆☆ 提升
      **⚠ r15 存疑（未改勾选状态，待裁定）**：round08 manifest `actual_updates` 记「TODO.md：T-046/T-047/T-020 → done」，
      但 round08/HANDOFF.md 下轮表中 T-020 仍列 TODO；且本条**无 `✅ rXX 完成 → F-xxxx` 记录**（与其余已完成条目格式不符），
      Q-006 至今 `open`，`F-0004` 置信度仍为 ★★★☆☆（established_in=round12，属重校准而非本任务产出）。
      即：「已勾选」与「产出落地」不一致。本轮只标注、不下结论——
      需要人工判定是「r08 提前勾错（应回退为 `- [ ]`）」还是「做了但未入库（应补 F-xxxx 与 Q-006 → answered）」。

- [x] **T-021** 销量内生性检验（Q-005）
      Granger + VAR；对比"含销量/不含销量"两版注数模型

- [x] **T-022** 随机性错觉假设检验（H-001）
      枚举等差序列等"看起来不随机"的形态，测其撞号程度

- [x] **T-023** 效应弱化的滚动复验（Q-011）✅ **r11 完成** → F-0042：后段内部效应进入平台期（W=300/500 滚动复验无显著持续弱化），F-0003 无需弱化标注

- [x] **T-024** 机选占比的代理变量（Q-015）✅ **r11 完成** → F-0043：连号注数比/偏好基尼代理可观测（显著变点），F-0021 caveats 已更新（补代理证据 + 概率口径限定）

- [x] **T-049** value: 80 ★ r12 首推：L3 组合优化的时序 hold-out 评测实现 + 规则搜索 v1 ✅ **r12 完成** → F-0044：测试窗 R001_norun_high_mirror 906.4 万 vs 随机 708.7 万（+27.9%，CI 下界高于随机，验收 met=True）；R-001/R-003 获 B 档样本外确认；R_new（镜像对避让）待用户批准落地

- [x] **T-051** value: 80 ★ r13 首推：L3 规则搜索 v2 —— walk-forward 滚动再训练 + 候选池扩展 ✅ **r13 完成** → F-0045：5 步 walk-forward（150 期评估窗），R_new 正增益步 4/5（80%）、中位增益 +150 万、总增益 +604 万，二次样本外确认 met=True；冷热号避让候选未超 R_new，winner 分布 3/5 归 R_new

- [x] **T-052** value: 40 ★ r14 候选：R_new（R001_norun_high_mirror）正式落地为 R-004 ✅ **r14.1 完成（用户已批准）** → strategy.json 新增 R-004（effectiveness_grade=B，引用 F-0044/F-0045/F-0046/F-0047）；STRATEGY_GUIDE v1.8→v1.9 §2 同步；game.yaml config_version 2.1→2.2（+has_mirror_pair 特征原语）；evidence_hash 重算；commit f6dff41
      **⚠ r15 状态修正**：r14 收尾时本条未勾选（manifest 记 `strategy_landed` 有落地，TODO 仍 `- [ ]`），
      导致 r15 任务书自动把已完成的 T-052 当成唯一可执行候选。
      已由新增校验项 ★T（`_check_todo_landed_sync`）捕获并修正——
      待办池是 `render_task_brief` 的唯一输入源，滞后会直接污染下一轮任务书。

- [x] **T-053** value: 30 P4：F-0041 补强——三连号之外形态复验（CI 宽）✅ **r14 完成** → F-0046：后段 high_zone_ge32 撞号比 0.9117 CI [0.8537,0.9716] 显著<1（高区避让机制证据）；run=2 1.0046 不显著；run>=3 1.2423 CI 宽未达显著（n=96）

- [x] **T-054** value: 30 P4：walk-forward 每步 bootstrap CI（当前单步仅点估计）✅ **r14 完成** → F-0047：单步显著正增益 1/5（step3 CI [594,906,2,913,333]），CI 宽源于小窗命中样本；F-0045 判据补不确定性限定

- [x] **T-055** value: 20 P4：README「版本体系」补 build_versions.py 禁用说明（T-044 收尾）✅ **r13 完成**
      README 版本体系小节已补：`tools/build_versions.py --write` 已禁用（防 versions.json 回退），
      权威维护流程=手工登记 + render 五件套 + inject_version_lines

- [x] **T-057** value: 50 ★ r15 治理：dry-run 副作用根治（A1）✅ **r15 完成**
      `tools/render_task_brief.py` 的 `os.makedirs` 曾写在 `--write` 判断**之前**，
      于是「只想预览任务书」也会凭空建出 `roundNN/` 空目录。已移入 `--write` 分支。
      实测：两次 dry-run 造出空的 round15/round16。

- [x] **T-058** value: 50 ★ r15 治理：轮次号只认已收尾轮（A2）✅ **r15 完成**
      `_next_round`（render_task_brief）/ `current_iteration_round`（validate）曾按
      `roundNN` 目录名取 max —— 空目录即可推高轮号，与 A1 叠加成自激回路。
      判据改为「含 `manifest.json`」（新增 `delivered_round_dirs`）。
      效果：validate 重校准警告由虚增的 7 轮回落为真实的 5 轮，轮号 round16 → round14。

- [x] **T-059** value: 50 ★ r15 治理：轮次号双源对账 ★R（A3）✅ **r15 完成**
      versions.json `current_iteration` 与「最新已收尾轮」必须相等，否则报错。
      背景：r14.2 立 versions.json 为权威源，但目录扫描那一路无人校验，两边静默分叉。

- [x] **T-060** value: 50 ★ r15 治理：已落地任务必须勾选 ★T + T-052 对齐（A4）✅ **r15 完成**
      新增 `_check_todo_landed_sync`：已 delivered 轮 manifest 的 `strategy_landed`
      中出现的 T-nnn 必须在 TODO 为已完成。只扫 `strategy_landed`（专门的落地登记），
      不扫 `actual_updates`（含「T-025 external-data 前置降备选」这类提及，泛化会误报）。

- [x] **T-061** value: 40 ★ r15 治理：无可执行候选时不得提升资源缺口型为必做 ✅ **r15 完成**
      `_render_brief` 旧实现在可执行候选为 0 时退回 `items[:top_n]`，
      把 `external-data` / `unverifiable` 任务提升为必做，正面违背 Z 协议。
      该路径此前从未被走到（待办池恒有可执行项），T-052 勾选后才首次触发。

- [x] **T-066** value: 50 ★ r16：动态锚点重校准（B1）✅ **r16 完成**
      7 条超期结论（F-0016/17/22/23 由 round09，F-0028/29/31 由 round10）
      **全部复跑脚本后判定维持**：E6 一等奖总派发 max 0.9788 亿 < 1 亿、触发 0 次；
      锚点 w1 中位 6 / 派发额中位 0.4252 亿精确复现；奖池 AR(1) 斜率 0.9994（SE 0.00064）
      与 ACF 复现。处治 = NOOP 重记（noop_count+1）+ **刷新 established_in → round16**。
      **关键发现**：只写 `recalibrated_roundNN` 而**不刷新 `established_in` 是清不掉告警的**——
      validate 的 `check_recalibration` 按 `established_in` 计时。

- [x] **T-067** value: 40 ★ r16：策略侧证据登记还债（B2）✅ **r16 完成**
      `strategy.json.evidence_index` 补 F-0044~F-0047（共 25 条）；
      `VERSIONS` 中 STRATEGY_GUIDE.md 的 `consumes` 补 F-0041/F-0044/F-0045/F-0046（共 28 项）。
      → 7 条结构性警告清零。

- [x] **T-064** value: 30 ★ r16 派生：H-002 三段单调检验 ✅ **r16 完成** → **F-0048**  [derive:H-002]
      用 F-0038 已估出的 S_j 直接检验 H-002 的「月 1-12 > 日 13-31 > 高段 32-35」预测：
      点估计全序单调（1.0213 / 0.9947 / 0.9580），**仅端点差显著**
      （1-12 − 32-35 = +0.0633，bootstrap CI [+0.0045, +0.1211]），
      中间分段差 CI 含 0，序型置换检验 **p = 0.2103（不显著）**
      → 支持「小号段更易撞车」，**不支持**「严格三段递减」。H-002 → `partial`。

- [x] **T-068** value: 60 ★ r16：待办池任务源派生机制（★源自救）✅ **r16 完成**
      新增 `tools/derive_tasks.py`：从 `OPEN_QUESTIONS.md` 的 open 项、
      `HYPOTHESES.md` 的未验证/部分验证假设、以及 `validate --all` 的告警清单
      派生候选任务入池，带 `resource` 标记与 `[derive:…]` 幂等标记。
      背景：r15 待办池可执行候选归零，根因是**没有补给通道**，不是事情做完了。

- [x] **T-069** value: 30 ★ r16：修正 r15 对 T-020 的误判 ✅ **r16 完成**
      r15 判 T-020「存疑：已勾选但无产出」是**误判**——产出早已由 r09 入库为 **F-0038**，
      缺口只是 TODO 条目缺 `✅ → F-xxxx` 记录。已补 T-020 完成记录（→ F-0038）、
      Q-006 → answered（15/15）、并在记录里留痕误判来源，防止后人再踩。

- [x] **T-070** value: 60 ★ r17：全形态穷举筛选 + R-005 落地 ✅ **r17 完成** → F-0049
      40 个 boolean 形态撞号比筛选（B=2000 bootstrap），4 个显著冷门形态落地为 R-005（prefer，权重 1.2，C 档）：
      front_mingap_eq2 / front_max_ge31 / back_all_even / back_same_tail
      29 个形态不显著（同尾聚集/吉祥号/忌讳号/全奇全偶/镜像对等均无证据）
      护栏：validate 新增"目录最大轮次 > current_iteration 时报 ERROR"

- [ ] **T-025** E6 固定奖加成是否真实发生（Q-016）★ r04 新增 `resource: external-data`
      需三至七等奖实发额（外部数据源）；先做事件计数再谈影响（L10）
      产出：新增 F-0xxx（拿到数据后）或保持 blocked

## P3 — 结构性 / 长期

- [x] **T-030** 明确"策略有效性"的三档标准并写入 schema（Q-008）✅ **r12 完成** → strategy.schema.json 1.4 `effectiveness_grade`（A 数学恒真 / B 统计确立 / C 模型估计）+ R-001=B/R-002=A/R-003=B 回填；STRATEGY_GUIDE §2 三档表；Q-008 → answered

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

- [x] **T-040** 从本仓库实践中提炼的框架改进，回写 `framework/protocol/` ✅ **r12 完成** → ITERATION_PROTOCOL §6 校验扩展（概率口径派生扫描/★S 策略同步/deliverables 对象数组/schema 全字段）+ §7 禁止事项 +5（BOM 编码/策略版本落后/任务 id 纯数字/渲染五件套/deliverables 字符串）；遗留建议：`evidence.effect` 区分"观测事件/归因"（F-0015 教训）已记入 T-040 文本，仍开放可选做

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

- [x] **T-044** ★ r04 新增：`tools/build_versions.py` 与 `versions.json` 脱节 ✅ **r13 完成（走"降级为参考实现"方案）**
      内嵌版本表停留在 r03，直接 `--write` 会回退 versions.json → **`--write` 已禁用（运行即报错退出）**；
      文件头显式声明降级为参考实现 + 权威维护流程（手工登记 + render 五件套 + inject_version_lines）

- [x] **T-045** ★ r04 新增：文档里的测试计数应自动注入 ✅ **r11 已实际落地，r13 核实销账**
      `tools/count_tests.py --inject` 已实现（`inject_tests_readme`，finish_round 自动调用），
      文档计数与实跑结果一致（tests/README 表格由 --inject 重建）

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

---

## 派生候选（由 tools/derive_tasks.py 生成，勿手改条目内容）

- [ ] **T-062** value: 40 ★ 派生 `resource: external-data` Q-016 E6 固定奖加成是否真实发生（r04 新增）  [derive:Q-016]
      出处 `OPEN_QUESTIONS.md` Q-016（方法/验收判据见原条目）

- [ ] **T-063** value: 30 ★ 派生 H-001 连号偏好源于"随机性错觉"（已部分验证，补剩余判据）  [derive:H-001]
      出处 `HYPOTHESES.md` H-001（可证伪预测与检验方法见原条目）

- [ ] **T-065** value: 30 ★ 派生 `resource: unverifiable` H-003 2013-08 的号码分布变化源于摇奖设备/球组更换  [derive:H-003]
      出处 `HYPOTHESES.md` H-003（可证伪预测与检验方法见原条目）
