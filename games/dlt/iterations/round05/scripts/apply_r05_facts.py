# -*- coding: utf-8 -*-
"""apply_r05_facts.py — round05 落地：投注方式 + 时间因素研究的结论写入 FACTS.jsonl

新增（7 条）：
  F-0026 投注方式的数学等价性（单注/复式/胆拖/倍投/追加）                [T-205, analytic]
  F-0027 『买 K 注完全相同号码』的自我摊薄公式 (1+m)/(K+m)              [T-205, analytic]
  F-0028 R-002 量化：结构同构不改变期望奖金（CI 含 0 → not_established）[T-205, simulation]
  F-0029 R-003 候选：避开连号+生日号区 → 未计封顶 +136%（vs R-001 +111%）[T-205, simulation]
  F-0030 H-005 证伪：周六连号撞号效应更弱（方向相反），不构成择时      [T-206, empirical]
  F-0031 期初奖池 AR(1)≈0.9994 → 高度可预测但不可利用                   [T-206, empirical]
  F-0032 国庆/元旦窗口连号比偏低（探索性，tentative → H-006）           [T-206, empirical]

写法：JSONL 逐行读 → 追加 → 按 id 排序整体回写（恰一行一条）。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
FACTS = os.path.join(ROOT, "memory", "facts", "FACTS.jsonl")
TODAY = "2026-10-11"

S_BET = "games/dlt/iterations/round05/scripts/bet_structure.py"
S_TMG = "games/dlt/iterations/round05/scripts/timing_weekday.py"

facts = []
with open(FACTS, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            facts.append(json.loads(line))
byid = {o["id"]: o for o in facts}
print(f"[load] {len(facts)} 条：{sorted(byid)}")


def new_fact(fid, **kw):
    base = {
        "id": fid, "game": "dlt", "status": "established", "affects_win_probability": False,
        "established_in": "round05", "supersedes": None, "superseded_by": None,
        "created_at": TODAY, "updated_at": None, "caveats": [],
    }
    base.update(kw)
    byid[fid] = base
    print(f"[new] {fid} {kw['claim'][:50]}...")


# ============================================================ F-0026
new_fact(
    "F-0026", confidence=5,
    confidence_basis=("解析可证：所有投注方式都只是『同一注基本票的组合展开/金额倍数』，"
                      "期望回报率由返奖率 51% 唯一决定，与投注方式无关。"),
    claim=("单注、复式、胆拖、倍投、追加五种投注方式在『每元期望回报率』上数学等价"
           "（都落在 51% 返奖率内）：复式=组合展开、胆拖=拖码组合展开、倍投=金额线性放大、"
           "追加=浮动奖加成但返奖率不变；投注方式只影响资金在组合空间的分布粒度，"
           "不改变期望回报率，唯一可被其影响的变量是覆盖组合集合的撞号水平与组内重复"),
    category="prize_mechanism", claim_type="analytic",
    evidence={
        "method": "解析推导：每注基本票期望 = 2×0.51 元；复式 C(m,5) 注 = C(m,5)×单注期望；"
                  "倍投 k 倍 = k×单注期望；追加票返奖率同为 51%（E5 起追加仅一二等奖 +80%，浮动奖结构内转移）",
        "result_summary": (
            "单注（2 元）：p=1/21,425,712，期望回报率 = 返奖率 51%。"
            "复式/胆拖：中奖概率与成本同比例放大（n 注 = n×单注），每元回报率不变。"
            "倍投：期望与方差按倍数线性放大，每元回报率不变（负期望同样放大）。"
            "追加（3 元）：仅影响一二等奖金额（+80%），长期返奖率口径不变。"
            "推论：『拆成单注买还是合成多注买，期望完全相同，只影响方差』—— 与 STRATEGY_GUIDE §6 一致。"),
        "effect": None, "ci95": None, "p_value": None, "n_observations": None,
        "data_version": "dlt_full_2933", "rules_epoch": "E6", "script": S_BET,
    },
    caveats=[
        "追加投注的 '+80%' 只作用于一/二等奖；其金额结构随 epoch 变化（E0~E6），本结论只声明『返奖率口径等价』。",
        "等价性是『期望回报率』层面；方差与奖级结构仍随投注方式不同（复式覆盖更多组合 → 方差更小）。",
        "不涉及中奖概率（恒 1/21,425,712）。",
    ],
    source=S_BET, tags=["betting_structure", "analytic", "l2"],
)

# ============================================================ F-0027
new_fact(
    "F-0027", confidence=5,
    confidence_basis=("解析可证：中奖注数线性分摊奖池的确定性公式。"),
    claim=("『买 K 注完全相同的号码』会自我摊薄：若中奖，K 注同时命中一等奖、总奖金被 K 份瓜分，"
           "每元期望回报比 = (1+m)/(K+m)（m=其他同号注数）；锚点 m=6 下，K=2/5/10 的每元回报"
           "分别为单注的 87.5%/63.6%/43.8%（损失 12.5%/36.4%/56.2%）"),
    category="prize_mechanism", claim_type="analytic",
    evidence={
        "method": "解析推导：买 1 注中奖时单注奖金 = Pool/(1+m)；买 K 注相同号码中奖时总奖金 = "
                  "K·Pool/(K+m)，每元回报 = [K·Pool/(K+m)]/(2K) vs [Pool/(1+m)]/2 → 比值 = (1+m)/(K+m)",
        "result_summary": (
            "K=1: 1.000（基线）；K=2: 0.875（−12.5%）；K=3: 0.778（−22.2%）；"
            "K=5: 0.636（−36.4%）；K=10: 0.438（−56.2%）。"
            "m 越大（撞号越严重），重复投注的相对损失越小，但恒为损失（m>0 时 (1+m)/(K+m) < 1）。"),
        "effect": {
            "formula": "(1+m)/(K+m)",
            "per_K_with_m6": {"K2": 0.875, "K3": 0.778, "K5": 0.636, "K10": 0.438},
            "loss_pct_with_m6": {"K2": 12.5, "K3": 22.2, "K5": 36.4, "K10": 56.2},
            "anchor_m": 6,
        },
        "ci95": None, "p_value": None, "n_observations": None,
        "data_version": "dlt_full_2933", "rules_epoch": "E6", "script": S_BET,
    },
    caveats=[
        "这是『完全相同号码』的自我摊薄；与 F-0028 的『结构同构（号码不同）』严格不同 —— 后者无此效应。",
        "m 是当期其他同号注数（随机变量）；锚点取 E6 实测中位 n0=6（F-0017）。",
        "若实际撞号更重（m 更大），相对损失缩小但绝对期望仍为负；不改变 F-0002。",
        "不涉及中奖概率（恒 1/21,425,712）。",
    ],
    source=S_BET, tags=["betting_structure", "analytic", "duplicate", "l2"],
)

# ============================================================ F-0028
new_fact(
    "F-0028", confidence=3,
    confidence_basis=("条件份额模拟（模型估计）：人群权重模型与 F-0004/F-0022 一致（α=12.7815 后段校准、"
                      "生日号 1.25），锚点 E6（n0=6、Pool=0.4252 亿）；结论是 Q-012 的验收判据直接输出。"),
    claim=("R-002 判定的『结构同构』（gap 向量相同但号码不同）不改变期望奖金：10 注同构 vs 10 注分散的"
           "期望撞号差 +0.024（CI [-0.011, 0.064] 含 0）、未计封顶每注奖金增益 +5.24%"
           "（CI [-2.1, 14.3] 含 0）、含封顶增益 0%（单注上限饱和）；且同构组撞号方差反而更低"
           "（cf 标准差 0.0105 vs 0.0172）。按 Q-012 判据，R-002 的 magnitude_pct 应标 not_established，"
           "权重应为 1.0（不 penalize）"),
    category="structure_preference", claim_type="simulation",
    evidence={
        "method": "枚举 C(35,5)=324632 组合，gap 向量分组；在 run=0 组合内构造覆盖集（spread=随机分散 10 注 / "
                  "cluster=同构组>=10 的种子抽 10 个不同同构组合）；条件撞号 = mean(w 覆盖集)/mean(w)，"
                  "E6 锚点 + 单注 1000 万/总额 1 亿封顶后处理；Bootstrap 2000（seeded）",
        "result_summary": (
            "撞号系数：spread 0.4760 vs cluster 0.5003，差 +0.0243 CI [-0.0106, 0.0638]。"
            "未计封顶每注奖金：spread 1490.6 万 vs cluster 1417.0 万，增益 +5.24% CI [-2.13, 14.29]。"
            "含封顶：两侧均为 1000 万（锚点处饱和），增益 0.00%。"
            "同构组补足率 0.000（设计上避免重复号码混入）。"
            "真正有害的『重复』是 F-0027 的完全相同号码（K=10 → 每元回报损失 56%），"
            "而 R-002 的 gap 同构判定并不包含它。"),
        "effect": {
            "collision_spread": 0.4760, "collision_cluster": 0.5003,
            "collision_delta": 0.0243, "collision_delta_ci95": [-0.0106, 0.0638],
            "prize_nocap_spread_yuan": 14906043, "prize_nocap_cluster_yuan": 14170064,
            "uplift_nocap_pct": 5.24, "uplift_nocap_ci95": [-2.1277, 14.2857],
            "uplift_cap_pct": 0.00, "cf_std_spread": 0.0172, "cf_std_cluster": 0.0105,
            "n_tickets": 10, "n_sim": 2000, "rng_seed": 20261011,
        },
        "ci95": [-2.1277, 14.2857], "p_value": None, "n_observations": 2000,
        "data_version": "dlt_full_2933", "rules_epoch": "E6", "script": S_BET,
    },
    caveats=[
        "模型估计：依赖人群权重模型（α、生日号 1.25）与 E6 锚点；模型假设变化则数值变化。",
        "『结构同构』只覆盖 gap 向量相同；若工具的 R-002 判定实际包含『完全重复号码』，则应按 F-0027 另设权重。",
        "cluster 抽样限定同构组 >= 10 的种子（47.2% 的 run=0 组合）；同构组小者不参与 —— 不影响期望结论。",
        "只在中奖时兑现：中奖概率 4.67e-08 不变。",
        "含封顶口径在锚点被单注上限饱和，差异为 0 —— 不改变未计封顶口径的结论。",
    ],
    source=S_BET, tags=["R002", "cross_scope", "simulation", "l2", "l5"],
)

# ============================================================ F-0029
new_fact(
    "F-0029", confidence=3,
    confidence_basis=("条件份额模拟（模型估计）：与 F-0028 同一模型与锚点；"
                      "R-003 是在 R-001 基础上叠加避开生日号区的候选规则增量。"),
    claim=("同时避开连号（run>=2）与生日号区（max<=31）的覆盖，条件撞号系数由随机基线 1.005 降至 0.425"
           "（仅避开连号为 0.476）；未计封顶的期望奖金提升 +136.2%（R-001 为 +111.2%，增量 +25pp）；"
           "含封顶在锚点 n0=6 处同为 +41.8%（单注上限饱和）、n0=9 处 +112.2%（vs R-001 +110.6%）"),
    category="structure_preference", claim_type="simulation",
    evidence={
        "method": "同 F-0028 的枚举与锚点模型：baseline=全体随机、R-001=run=0、R-003=run=0 且 max>=32；"
                  "n0 敏感性三档（3/6/9）",
        "result_summary": (
            "组合池规模：run=0 共 169911 个（52.3%），run=0 且 max>=32 共 89181 个（27.5%）。"
            "cf：随机 1.0046 → R-001 0.4759 → R-003 0.4254。"
            "未计封顶 uplift：R-001 +111.18%、R-003 +136.23%（+25.05pp）。"
            "含封顶：n0=3 均为 +0.00%（单注上限抹平）、n0=6 均为 +41.82%、n0=9 R-001 +110.55% / R-003 +112.19%。"
            "R-003 的覆盖集合人群权重恒为 1.0（无连号偏好、无生日号偏好加成），是理论最低撞号覆盖。"),
        "effect": {
            "cf_random": 1.0046, "cf_r001": 0.4759, "cf_r003": 0.4254,
            "uplift_nocap_r001_pct": 111.18, "uplift_nocap_r003_pct": 136.23,
            "uplift_nocap_increment_pct": 25.05,
            "uplift_cap_n0_6_r001": 41.82, "uplift_cap_n0_6_r003": 41.82,
            "uplift_cap_n0_9_r001": 110.55, "uplift_cap_n0_9_r003": 112.19,
            "n_pool_norun": 169911, "n_pool_r003": 89181,
            "n_sim": 300000, "rng_seed": 20261011,
        },
        "ci95": None, "p_value": None, "n_observations": 300000,
        "data_version": "dlt_full_2933", "rules_epoch": "E6", "script": S_BET,
    },
    caveats=[
        "模型估计：依赖人群权重模型（含生日号 1.25 与连号 α）；生日号权重来自 F-0004 的历史校准，是估计非真值。",
        "R-003 是候选规则（未入 strategy.json）：是否纳入、以及其 predicate 定义（max>=32 的边界）需用户决策。",
        "含封顶净值在锚点 n0=6 处与 R-001 相同 —— 实际收益取决于当期注数（n0 低时被单注上限抹平）。",
        "只在中奖时兑现：中奖概率 4.67e-08 不变；长期期望仍为负（−0.98 元/注）。",
        "与 F-0004/R-001 的数字对照基于同一模型口径，可并列引用；α 口径为后段 12.7815。",
    ],
    source=S_BET, tags=["R003_candidate", "simulation", "birthday_effect", "l2", "l5"],
)

# ============================================================ F-0030
new_fact(
    "F-0030", confidence=3,
    confidence_basis=("观测 + 回归：后段 NB2（控制销量）的 run×周六 交互显著为负（w1 p=0.039、w2 p<0.0001），"
                      "与 Bootstrap 比值两两差（CI 全含 0）方向一致；负结论（不构成可利用择时）"
                      "不因多重比较被制造出来（Holm 校正后 w2 保留）。"),
    claim=("撞号效应的星期交互方向与 H-005 假设相反：后段控制销量后 run×周六 交互显著为负"
           "（w1 −0.268，p=0.039；w2 −0.607，p<0.0001）—— 周六（高销量日）的连号撞号效应更弱"
           "（尤其二等奖口径）；但 Bootstrap 两两差 CI 全含 0、幅度小，不构成可利用的择时因素，"
           "维持 F-0023『不存在可利用的时间因素』与 A-009（驳回择时）"),
    category="structure_preference", claim_type="empirical",
    evidence={
        "method": "后段（>=2013-08-28，n=1973）NB2 GLM：log(w) ~ run + sat + mon + run×sat + run×mon + "
                  "offset(log(sale/2))；逐星期分组 Bootstrap 连号注数比（B=4000）+ 两两差（B=2000）",
        "result_summary": (
            "后段连号注数比（w1）：周一 1.097、周三 1.251、周六 1.367；w2：周一 1.154、周三 1.450、周六 1.050。"
            "NB2 交互：w1 run×sat −0.2678（p=0.0385）、run×mon −0.0996（p=0.451）；"
            "w2 run×sat −0.6071（p<0.0001）、run×mon −0.1718（p=0.120）。"
            "Bootstrap 两两差 6 组 CI 全含 0；Holm 校正后仅 w2 的 run×sat 保留。"
            "解释方向：周六销量高但连号注数占比低 → 购彩人群构成不同（更多随机/非偏好型买家稀释连号密度）。"),
        "effect": {
            "nb2_run_sat_w1": -0.2678, "nb2_run_sat_p_w1": 0.0385,
            "nb2_run_sat_w2": -0.6071, "nb2_run_sat_p_w2": 0.0000,
            "nb2_run_mon_w1": -0.0996, "nb2_run_mon_p_w1": 0.4512,
            "nb2_run_mon_w2": -0.1718, "nb2_run_mon_p_w2": 0.1196,
            "ratio_w1": {"mon": 1.097, "wed": 1.251, "sat": 1.367},
            "ratio_w2": {"mon": 1.154, "wed": 1.450, "sat": 1.050},
            "pairwise_diff_ci_all_contain_zero": True,
            "holm_survivor": "w2 run×sat", "n_boot": 4000, "rng_seed": 20261011,
        },
        "ci95": None, "p_value": 0.0001, "n_observations": 1973,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_TMG,
    },
    caveats=[
        "H-005 原假设（周六撞号更强）被证伪（方向相反）；这不是『周六可用来择时』的证据 —— 幅度小、且负期望不变。",
        "NB2 为参数模型：隐含乘性人群密度；若真实偏好非同质，交互项受模型设定影响。",
        "Bootstrap 两两差 CI 全含 0（噪声大：w1 零值率高），回归显著性依赖模型假设 —— 结论标 ★★★☆☆。",
        "只描述『被选中率』的星期结构，不涉及开出率（L7）；号码本身的星期效应仍为 F-0012（无）。",
        "不构成新的择时规则：维持 A-009 与 F-0023。",
    ],
    source=S_TMG, tags=["timing", "weekday", "H005_closed", "collision", "l5", "l13"],
)

# ============================================================ F-0031
new_fact(
    "F-0031", confidence=4,
    confidence_basis=("观测 + OLS/ACF：后段单一稳定规则期内的时序统计，非模型推断；"
                      "结论『可预测但不可利用』由 F-0023 的期望分析支撑。"),
    claim=("期初奖池序列高度可预测：后段 AR(1) 斜率 0.9994（SE 0.0006）、ACF lag1-3 均 ≈ 1.0"
           "（奖池几乎完全由上期滚存决定）；但可预测 ≠ 可利用 —— F-0023 已证奖池分位对每元期望派发"
           "无稳健差异，奖池时序可预测性不构成择时依据"),
    category="prize_mechanism", claim_type="empirical",
    evidence={
        "method": "后段（n=1973）pool_yuan 的 AR(1) OLS + 去趋势 ACF(lag1-3)",
        "result_summary": (
            "pool_t = 1.54e6 + 0.9994·pool_{t-1}（SE 0.0006）；ACF lag1-3 = [1.0, 0.999, 0.999]。"
            "奖池几乎完全由上一期滚存决定（周期内无大奖排空时斜率≈1）。"
            "与 F-0023 合读：奖池水平可预测，但其变化对期望派发无稳健影响 → 择时无价值。"),
        "effect": {
            "ar1_slope": 0.9994, "ar1_se": 0.0006, "ar1_intercept": 1540000,
            "acf": [1.0, 0.999, 0.999], "n_post": 1973,
        },
        "ci95": None, "p_value": None, "n_observations": 1973,
        "data_version": "dlt_full_2933", "rules_epoch": "E6", "script": S_TMG,
    },
    caveats=[
        "AR(1) 斜率≈1 是滚存机制的直接结果；大奖排空期（如 2019）会打断该结构 —— 描述性结论。",
        "『可预测』是统计意义上的（R² 高），『不可利用』来自 F-0023 的期望分析 —— 两条结论必须合读。",
        "不涉及中奖概率。",
    ],
    source=S_TMG, tags=["pool", "timing", "ar1", "l6"],
)

# ============================================================ F-0032
new_fact(
    "F-0032", confidence=2,
    confidence_basis=("观测 + Bootstrap：样本小（n=82/67）、窗口定义为探索性，CI 宽 —— 只能作为假设种子，"
                      "不能作为策略依据。"),
    claim=("国庆（9/25-10/10）与元旦（12/26-1/6）窗口的一等奖连号注数比低于基线（国庆 0.72 vs 1.28，"
           "元旦 0.73 vs 1.27），销量略低（休市，销量比 0.90/0.97）；但样本小、CI 很宽，"
           "属探索性信号 —— 开 H-006 待下轮以更严谨的窗口定义与农历精确映射验证"),
    category="structure_preference", claim_type="empirical", status="tentative",
    evidence={
        "method": "后段窗口分组 Bootstrap 连号注数比（B=2000）+ 销量均值对照；窗口为公历近似"
                  "（国庆 9/25-10/10、元旦 12/26-1/6、春节=2 月近似）",
        "result_summary": (
            "国庆窗口 n=82：销量比 0.899（2.28 亿 vs 2.53 亿），w1 连号比 0.719 CI [0.393, 1.094] vs 基线 1.280。"
            "元旦窗口 n=67：销量比 0.972，连号比 0.734 CI [0.392, 1.125] vs 基线 1.272。"
            "2 月（春节近似）n=110：连号比 1.033 CI [0.417, 1.886] vs 基线 1.258（不显著）。"
            "三个窗口的 CI 均含基线水平的宽区间，且窗口定义武断 → tentative。"),
        "effect": {
            "national_n": 82, "national_ratio": 0.719, "national_ci95": [0.393, 1.094],
            "national_baseline": 1.280, "national_sale_ratio": 0.899,
            "newyear_n": 67, "newyear_ratio": 0.734, "newyear_ci95": [0.392, 1.125],
            "newyear_baseline": 1.272, "newyear_sale_ratio": 0.972,
            "feb_n": 110, "feb_ratio": 1.033, "feb_ci95": [0.417, 1.886], "feb_baseline": 1.258,
            "n_boot": 2000, "rng_seed": 20261011,
        },
        "ci95": [0.393, 1.094], "p_value": None, "n_observations": 82,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_TMG,
    },
    caveats=[
        "样本小（82/67 期）且窗口定义为探索性 —— 结论为 tentative，绝不构成策略依据。",
        "春节窗口用 2 月近似（未做农历精确映射）；真实春节前后期次定义需农历日期表。",
        "若节假日人群构成确实不同（更多随机型买家），连号比偏低与 F-0030 的周六效应同源 —— 属待验证假设。",
        "只涉及被选中率结构，不涉及开出率与中奖概率。",
    ],
    source=S_TMG, tags=["holiday", "timing", "tentative", "H006", "l5"],
)

# ============================================================
ordered = sorted(byid.values(), key=lambda x: x["id"])
with open(FACTS, "w", encoding="utf-8") as f:
    for o in ordered:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"[write] {FACTS} 共 {len(ordered)} 条（新增 7 条）")
