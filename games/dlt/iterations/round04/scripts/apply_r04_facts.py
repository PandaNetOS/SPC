# -*- coding: utf-8 -*-
"""apply_r04_facts.py — round04 落地：把三条任务线的结论写入 FACTS.jsonl

新增：
  F-0019 前段（<2013-08）数据三者不自洽（号码分布 / 中出注数 / 销售额）  [T-101]
  F-0020 F-0003 的「衰减过半」是估计量依赖的（稳健口径 decay 0.65~0.83）  [T-101]
  F-0021 弱化与 F-0006 的 2013-08 变点同期；销量稀释已排除              [T-101]
  F-0022 后段口径下 F-0004 的重算（上界 121.5% → 109.4%）              [T-101]
  F-0023 不存在稳健的「高期望期」（择时）                              [T-102]
  F-0024 r_t 与 er_t 背离：用派发比衡量择时价值会误判                  [T-102]
  F-0025 后区撞号存在但不可靠可利用（开出率均匀 / 被选中率非均匀）      [T-103]
更新：
  F-0003 幅度口径修正（引用 F-0019~F-0021）
  F-0004 校准口径改为后段（引用 F-0022）
  F-0011 修正「后区无偏好结构」的口径混淆（引用 F-0025；L7）

写法：JSONL 逐行读 → 定位 → 替换/追加 → 按 id 排序整体回写（恰一行一条）。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
FACTS = os.path.join(ROOT, "memory", "facts", "FACTS.jsonl")
TODAY = "2026-10-11"

S_DECAY = "games/dlt/iterations/round04/scripts/decay_cause.py"
S_TOBIT = "games/dlt/iterations/round04/scripts/prize_mechanism_tobit.py"
S_BACK = "games/dlt/iterations/round04/scripts/back_collision.py"

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
        "established_in": "round04", "supersedes": None, "superseded_by": None,
        "created_at": TODAY, "updated_at": None, "caveats": [],
    }
    base.update(kw)
    byid[fid] = base
    print(f"[new] {fid} {kw['claim'][:40]}...")


# ============================================================ F-0019
new_fact(
    "F-0019", confidence=4,
    confidence_basis=("观测：两组互相独立的异常（号码分布均匀性检验 + 注数/销售额的可行性核算），"
                      "且已用人群成分修正排除『两段开出的号码成分不同』这一替代解释。非解析结论。"),
    claim=("2013-08 之前那段数据在『号码分布—中出注数—销售额』三者间不自洽：前区号码分布严重偏高端"
           "（χ²=251.5，P(前区全部<=31)=0.395 vs 精确 0.5234，z=−7.98），且由中出注数反推的投注量"
           "超出售额允许上限（均价 1.75~1.87 元/注 < 最低票价 2 元）；后段两项均自洽"),
    category="methodology", claim_type="empirical",
    evidence={
        "method": "观测 + 精确核算：前区单号频率 χ² 均匀性检验、P(max<=31) 二项检验、"
                  "由中出注数无偏反推投注量并核对可行区间 [sale/3, sale/2]（基本 2 元 / 追加 3 元）",
        "result_summary": (
            "前段（<2013-08-28，n=960）：单号频率 χ²=251.5（df=34），P(前区全部<=31)=0.395（精确 0.5234，z=−7.98）；"
            "反推注数 w1 口径 38.7M、w2 口径 36.1M，均高于销售额允许上限 33.8M（sale/2），均价 1.75~1.87 元/注 < 2 元；"
            "用人群模型做号码成分修正后仍为 1.84 元/注。后段（>=2013-08-28，n=1973）：χ²=32.1，P(max<=31)=0.535（z=+1.01），"
            "反推注数 104.2M / 108.3M 落在可行区间 [84.0M,126.0M]，均价 2.42/2.33 元/注。"),
        "effect": {
            "pre_chi2": 251.5, "pre_z_max_le_31": -7.98, "pre_p_max_le_31": 0.395,
            "post_chi2": 32.1, "post_z_max_le_31": 1.01, "post_p_max_le_31": 0.535,
            "theory_p_max_le_31": 0.5234,
            "pre_implied_tickets_w1": 38700000, "pre_implied_tickets_w2": 36100000,
            "pre_feasible_band": [22500000, 33800000],
            "pre_yuan_per_ticket_w1": 1.746, "pre_yuan_per_ticket_w2": 1.872,
            "pre_yuan_per_ticket_composition_corrected": 1.842,
            "post_implied_tickets_w1": 104200000, "post_implied_tickets_w2": 108300000,
            "post_feasible_band": [84000000, 126000000],
            "post_yuan_per_ticket_w1": 2.419, "post_yuan_per_ticket_w2": 2.328,
            "verified_pdf_rate_pre": 0.0, "verified_pdf_rate_post": 0.51,
        },
        "ci95": None, "p_value": None, "n_observations": 2933,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_DECAY,
    },
    caveats=[
        "只证明三者互相不自洽，不能判定哪一侧（中出注数 / 销售额 / 号码记录）出错 —— 『能排除什么』止于此。",
        "号码分布检验的最小期望频数 137/号（>>5），渐近 χ² 可用（L2 不触发）；但未构造精确枚举零分布。",
        "前段 w1 零值率 40.6%、var/mean=8.46，任何基于均值比的前段估计都不稳（见 F-0020）。",
        "前段的『P(max<=31) 偏低』与『反推注数偏高』在方向上是相互矛盾的（低号更受人群偏好），"
        "这一点本身也支持『数据记录不自洽』而非单一真实行为变化。",
        "本条只涉及数据一致性，不涉及中奖概率（恒 1/21,425,712）。",
    ],
    source=S_DECAY, tags=["data_quality", "epoch_break", "l7", "l5"],
)

# ============================================================ F-0020
new_fact(
    "F-0020", confidence=4,
    confidence_basis=("方法论结论：同一数据上多估计量对照（均值 / 中位数 / 10% 截尾 / Jackknife 剔除极端期）。"
                      "不产出新的效应量，只修正已有效应量的口径边界。"),
    claim=("F-0003 的分期『衰减过半』是估计量依赖的：均值比口径给出 post/pre = 0.592（w1）/ 0.498（w2），"
           "稳健口径（中位数比 / 10% 截尾 / 剔除最大 3 期）给出 0.65~0.83；前段 w1 均值比 2.107 在被剔掉"
           "最大 1 期后即降到 1.719、3 期后 1.466"),
    category="methodology", claim_type="methodological",
    evidence={
        "method": "分期同口径 + 多估计量对照（均值比 / 中位数比(+0.5) / 10% 截尾比 / 剔除 top-k 期）+ Bootstrap 2000（seeded）",
        "result_summary": (
            "前段 w1：均值比 2.107、中位数比 1.000、截尾 10% 2.032、剔 top1 1.719、剔 top3 1.466；"
            "前段 w2：均值比 2.425、中位数比 1.400、截尾 1.622、剔 top3 1.655。"
            "后段 w1：1.247 / 1.286 / 1.205；后段 w2：1.208 / 1.168 / 1.169。"
            "衰减比 post/pre：w1 均值 0.592、截尾 0.593、剔 top3 0.746；w2 均值 0.498、中位数 0.834、截尾 0.721、剔 top3 0.651。"),
        "effect": {
            "decay_mean_w1": 0.592, "decay_trim10_w1": 0.593, "decay_drop_top3_w1": 0.746,
            "decay_mean_w2": 0.498, "decay_median_w2": 0.834, "decay_trim10_w2": 0.721,
            "decay_drop_top3_w2": 0.651,
            "pre_w1_mean_ratio": 2.1072, "pre_w1_median_ratio": 1.0,
            "pre_w1_drop_top1": 1.719, "pre_w1_drop_top3": 1.466,
            "post_w1_mean_ratio": 1.2472, "post_w1_median_ratio": 1.286,
            "n_boot": 2000, "rng_seed": 20261011,
        },
        "ci95": None, "p_value": None, "n_observations": 2933,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_DECAY,
    },
    caveats=[
        "前段 w1 的中位数比退化为 1.000（两组中位数都是 1）—— 零值率高的段里中位数比不是有效口径，"
        "稳健口径应以样本量约 80 倍的 w2 为准。",
        "稳健口径本身也有不确定性：前段 w2 的截尾比 1.622 与剔 top3 比 1.655 相差 2%，说明前段估计仍受尾部影响。",
        "本条只修正幅度口径，不否定『衰减存在』（NB2 交互项显著，见 F-0021）。",
        "均值比口径与 F-0003/F-0018 一致，故两者并列报告（同口径对照），而非互相取代。",
    ],
    source=S_DECAY, tags=["methodology", "l5", "robustness", "collision"],
)

# ============================================================ F-0021
new_fact(
    "F-0021", confidence=3,
    confidence_basis=("归因类结论：三组证据（NB2 规模控制、分层标准化、滚动窗口变点）方向一致，"
                      "但『同期』不等于因果，且前段数据本身不自洽（F-0019），故降一档。"),
    claim=("撞号效应的弱化与 F-0006 的 2013-08 号码结构变点同期（滚动窗口 W=300/400/500 的数据驱动最优切点"
           "落在 2013-04~2014-04），且不是销量规模稀释造成的（NB2 以 log(销量/2) 为 offset，run×post "
           "交互 IRR=0.596 [0.462,0.769]（w1）/0.521（w2））"),
    category="structure_preference", claim_type="empirical",
    evidence={
        "method": "NB2 GLM（offset=log(销量/2)，L1 过度离散要求）+ 分层标准化比（MH，按前区和值五分位×生日号区）"
                  "+ 数据驱动滚动窗口变点扫描（L3：不按自然年硬切）",
        "result_summary": (
            "NB2：run IRR 前段 2.064 [1.667,2.555]、后段 1.230 [1.070,1.414]，交互 IRR 0.596 [0.462,0.769] p=7e-5；"
            "w2 交互 0.521 [0.448,0.606]。分层标准化比（MH，固定成分权重）前段 2.028 → 后段 1.273，衰减比 0.627。"
            "滚动窗口 W=400/step=50 最优切点 2013-04-10（w1/w2 一致）；敏感性 W=300/step=25→2013-06-08、"
            "W=500/step=100→2013-08-05、W=300 非重叠→2014-04-02。"),
        "effect": {
            "nb2_interaction_irr_w1": 0.596, "nb2_interaction_ci95_w1": [0.4618, 0.7692],
            "nb2_interaction_p_w1": 7e-05,
            "nb2_interaction_irr_w2": 0.521, "nb2_interaction_ci95_w2": [0.4484, 0.6055],
            "nb2_irr_run_pre_w1": 2.0636, "nb2_irr_run_post_w1": 1.230,
            "standardized_pre": 2.0279, "standardized_post": 1.2725, "standardized_decay": 0.627,
            "rolling_breakpoint": "2013-04-10",
            "rolling_breakpoint_sensitivity": ["2013-06-08", "2013-08-05", "2014-04-02"],
            "f0006_changepoint": "2013-08-28",
        },
        "ci95": [0.4618, 0.7692], "p_value": 7e-05, "n_observations": 2933,
        "data_version": "dlt_full_2933", "rules_epoch": None, "script": S_DECAY,
    },
    caveats=[
        "『同期』只说明两件事同时发生，不构成因果：滚动窗口互相重叠、每窗 run>=2 仅 30~50 期，切点分辨率约 ±半年。",
        "前段数据本身不自洽（F-0019），故前段的效应水平不能当作纯人群行为基线。",
        "NB2 隐含乘性人群密度模型；若真实偏好非同质，交互项会被模型设定影响。",
        "无法排除『机选（随机选号）占比上升』这类行为变化 —— 本数据集没有投注方式字段，属未观测混杂。",
        "不涉及中奖概率（恒 1/21,425,712）；本条只关乎撞号密度的时变。",
    ],
    source=S_DECAY, tags=["collision", "changepoint", "attribution", "l3"],
)

# ============================================================ F-0022
new_fact(
    "F-0022", confidence=3,
    confidence_basis="条件份额模拟（模型估计）：依赖与 F-0004 相同的人群权重模型与实测锚点，属模型估计非真值。",
    claim=("把 F-0004 的校准口径从全样本 1.3603 改为后段 1.2472 后，未计封顶的收益上界由 121.5% 降为 109.4%，"
           "而含 1 亿元总额封顶的实测锚点净值几乎不变（41.0% → 40.6%）"),
    category="prize_mechanism", claim_type="simulation",
    evidence={
        "method": "条件份额模拟（枚举 C(35,5)=324632 的全部组合）+ 封顶确定性后处理；α 由观测形态比校准；"
                  "锚点取 E6 实测中位（n0=6 注、Pool=0.4252 亿）",
        "result_summary": (
            "全样本口径 R=1.3603 → α=13.9405：未计封顶 uplift 120.59%，含封顶实测锚点 41.02%；"
            "后段口径 R=1.2472 → α=12.7815：未计封顶 109.39%，含封顶 40.64%；"
            "后段 w2 稳健口径 R=1.1695 → α=11.9852：未计封顶 103.08%，含封顶 41.30%。"
            "含封顶净值对 α 不敏感：锚点处单注金额被 1000 万元单注上限饱和，收益差被同一上限压平。"),
        "effect": {
            "alpha_full": 13.9405, "alpha_post": 12.7815,
            "uplift_nocap_full": 120.59, "uplift_nocap_post": 109.39,
            "uplift_cap_full": 41.02, "uplift_cap_post": 40.64,
            "uplift_nocap_post_w2_trim": 103.08, "uplift_cap_post_w2_trim": 41.30,
            "anchor_n0_tickets": 6, "anchor_pool_yi": 0.4252,
            "n_sim": 200000, "rng_seed": 20261011,
        },
        "ci95": None, "p_value": None, "n_observations": 200000,
        "data_version": "dlt_full_2933", "rules_epoch": "E6", "script": S_DECAY,
    },
    caveats=[
        "依赖同一人群权重模型（连号 α + 生日号 1.25）与 E6 实测锚点（n0=6、Pool=0.4252 亿），属估计非真值。",
        "α 的口径选择本身带不确定性：后段 w2 稳健口径给出 α=11.99 → 未计封顶上界 103.1%。",
        "含封顶净值对 α 不敏感，是因为锚点处单注金额已被 1000 万元单注上限饱和 —— 不是『口径无关』，而是封顶主导。",
        "只在中奖时兑现：中奖概率 4.67e-08 不变。",
    ],
    source=S_DECAY, tags=["simulation", "cap", "recalibration", "collision"],
)

# ============================================================ F-0023
new_fact(
    "F-0023", confidence=4,
    confidence_basis=("观测 + Bootstrap：两个口径（派发比 / 每元期望派发）+ 三个稳健估计量 + 事先固定的确认性检验族"
                      "并做 Holm 校正；负结论不因多重比较被制造出来。"),
    claim=("在可观测的一/二等奖派发口径下不存在稳健的『高期望期』：全局期初奖池分位 top−bottom 的每元期望派发差 "
           "+0.090 [0.073,0.104] 由 epoch 组成与 E4 段 2019 年一次性奖池排空驱动，剔除 2019 后 E4 差降至 "
           "+0.002（不显著）；现行 E6 差 +0.017（p=0.30）"),
    category="prize_mechanism", claim_type="empirical",
    evidence={
        "method": "期初奖池（pool_yuan 滞后一期 —— L6）分位分组 + Bootstrap B=2000 + 事先固定的确认性检验族"
                  "（E1–E6 的 within-epoch er_t）并做 Holm 校正；稳健口径（中位数 / 10% 截尾）对照；Tobit 删失回归按 epoch 分段（L9）",
        "result_summary": (
            "er_t=(p1·amt1+p2·amt2)/2（每 1 元基本投注、一/二等奖的期望派发）。"
            "全局 Q4−Q1：+0.090 [0.073,0.104]；确认性族（E1–E6, Holm）：E1 +0.049、E4 +0.173、E5 +0.027 存活，"
            "E2(p=0.16)、E3(p=0.56)、E6(p=0.30) 为零。E4 剔除 2019 年后 +0.002（不显著）→ E4 的正效应完全来自"
            "2019 年奖池由 73 亿排空到 8 亿的一次性事件。相对口径（pool_prev/近 52 期中位数）无稳健正效应。"
            "Tobit log(amt1)~pool_prev 的半弹性：E4 +3.9%、E5 +2.3% 显著，E6 −1.2%（不显著），"
            "且受 1000 万单注上限饱和，不可全域外推。"),
        "effect": {
            "global_er_diff": 0.090, "global_er_diff_ci95": [0.073, 0.104],
            "E4_er_diff": 0.173, "E4_er_diff_ex2019": 0.002,
            "E5_er_diff": 0.027, "E6_er_diff": 0.017, "E6_er_p": 0.302,
            "holm_survivors": ["E1", "E4", "E5"], "holm_family_size": 6,
            "tobit_semi_elast_pct": {"E4": 3.9, "E5": 2.3, "E6": -1.2},
            "E6_cap_total_triggered": 0, "E6_max_total1_yi": 0.9788,
            "n_boot": 2000, "rng_seed": 20261011,
        },
        "ci95": [0.073, 0.104], "p_value": None, "n_observations": 2932,
        "data_version": "dlt_full_2933", "rules_epoch": "E6", "script": S_TOBIT,
    },
    caveats=[
        "数据集只有一/二等奖派发额 → er_t 只覆盖浮动奖，是三至七等奖缺失下的**下界**。",
        "E0/E1 段的注数-销售额不自洽（聚合均价 1.98 / 1.81 元/注 < 2 元，与 F-0019 一致），该两段的金额口径不可比。",
        "E2 仅 60 期、E6 仅 102 期，功效低；E0 奖金结构最混乱（5M/10M 双轨 + 超封顶观测）。",
        "确认性检验族已 Holm 校正，其余数以十计的切法/估计量对照属探索性（多重性不能制造『零效应』这一负结论）。",
        "规则文本『奖池>=8 亿时三至七等奖 +20%~40%』解析上每元期望派发 +0.095、36.3% 的 E6 期数满足必要条件，"
        "但缺三至七等奖实发数据，无法核验是否真实发生（L10）。",
        "不涉及中奖概率：单注一等奖概率恒 1/21,425,712。",
    ],
    source=S_TOBIT, tags=["prize_mechanism", "timing", "tobit", "l9", "l6"],
)

# ============================================================ F-0024
new_fact(
    "F-0024", confidence=4,
    confidence_basis="方法论结论：同一数据上两个口径的直接对照（派发/销售额 vs 每元期望派发）+ 每注均价分组，非模型推断。",
    claim=("用『派发额/销售额』(r_t) 衡量择时价值会误判：E4 段剔除 2019 后 r_t 仍随奖池显著上升（+0.067）"
           "而每元期望派发 er_t 无变化（+0.002），差异来自高奖池期追加投注占比下降导致的每注均价变化"),
    category="methodology", claim_type="methodological",
    evidence={
        "method": "同数据双口径对照：r_t=(w1·amt1+w2·amt2)/sale 与 er_t=(p1·amt1+p2·amt2)/2；"
                  "每注均价 = sale / (w2/p2) 分组比较",
        "result_summary": (
            "E4 段（19019–23000，n=566）：r_t 的 pool Q4−Q1 = +0.067（显著），而 er_t = +0.002（零）；"
            "同期每注均价由 Q1 的 3.08 元降到 Q4 的 2.66 元（高奖池期追加投注占比下降）。"
            "全局 r_t 差 +0.090 亦主要为 epoch 组成效应。"),
        "effect": {
            "E4_delta_r_t_ex2019": 0.067, "E4_delta_er_t_ex2019": 0.002,
            "E4_price_q1": 3.08, "E4_price_q4": 2.66,
            "global_delta_r_t": 0.090, "global_delta_er_t": 0.090,
        },
        "ci95": None, "p_value": None, "n_observations": 2932,
        "data_version": "dlt_full_2933", "rules_epoch": "E6", "script": S_TOBIT,
    },
    caveats=[
        "两个口径都只覆盖一/二等奖（三至七等奖缺失），故都不等于总返奖率。",
        "每注均价由 sale/(w2/p2) 反推，而 n2 本身含人群密度信息（与分子同源），不是完全独立的测量。",
        "本条是口径警示，不产出效应量；它解释了 F-0023 中『全局看似正效应』的来源之一。",
    ],
    source=S_TOBIT, tags=["methodology", "l12", "timing", "prize_mechanism"],
)

# ============================================================ F-0025
new_fact(
    "F-0025", confidence=4,
    confidence_basis=("观测 + 参数模型 + 精确检验：条件二项 MLE（11 参数独立模型）与 66 参数饱和模型交叉，"
                      "Monte-Carlo 精确检验（B=10000），并用前/后段交叉验证评估样本外可用性。"),
    claim=("后区撞号结构存在但不可靠可利用：后区 66 对的『被选中率』强烈非均匀（过散布 8.72×，MC p<1e-4；"
           "最热对/最冷对密度比 2.25×），而『开出率』均匀（χ²=64.1，MC p=0.51）；前/后段交叉验证的避让收益"
           "K=5/10 仅约 1.1%/3.0%，95%CI 含 0"),
    category="structure_preference", claim_type="empirical",
    evidence={
        "method": "可分离假设 p(F,B)∝u(F)·v(B) 下的条件二项 MLE（w1|m~Binomial(m,p_B)，m=w1+w2）；"
                  "11 参数独立号码模型 + 66 参数饱和模型；Monte-Carlo 精确检验（B=10000）；前/后段交叉验证",
        "result_summary": (
            "开出率：66 组合 χ²=64.09（df=65），MC p=0.51；12 号码 χ²=10.42（df=11），MC p=0.49 → 均匀（与 F-0011 一致）。"
            "被选中率：66 对聚合二项检验 χ²=567.1（df=65），过散布 8.72×，MC p<1e-4 → 强烈非均匀。"
            "独立 s 模型：s∈[0.747(12号), 1.197(9号)]，组合密度 max/min=2.245×，LR(vs 均匀)=139.3（df=11）。"
            "饱和模型 LR(vs 独立 s)=423.4（df=54）→ 存在对特异偏好。"
            "条件份额（给定 v 为有限集精确期望）：in-sample K=1/5/10 → 0.59%/2.86%/5.68%（含前视，上界）；"
            "前/后段交叉验证 → 0.10%/1.07%/2.96%，95%CI 含 0。前区参照（同一模型）避开 run>=2 的 uplift=119.1%。"),
        "effect": {
            "open_rate_pair_chi2": 64.09, "open_rate_pair_mc_p": 0.5104,
            "picked_rate_pair_chi2": 567.10, "overdispersion": 8.72, "picked_rate_mc_p": 0.0001,
            "s_min": 0.747, "s_min_number": 12, "s_max": 1.197, "s_max_number": 9,
            "pair_density_ratio": 2.245, "lr_indep_vs_uniform": 139.28, "lr_indep_df": 11,
            "lr_sat_vs_indep": 423.37, "lr_sat_df": 54,
            "uplift_in_sample_pct": {"K1": 0.59, "K5": 2.86, "K10": 5.68},
            "uplift_cross_validated_pct": {"K1": 0.10, "K5": 1.07, "K10": 2.96},
            "uplift_cv_ci95_K10": [-1.48, 9.10],
            "front_reference_uplift_pct": 119.10,
            "s_corr_split_2013_08": 0.4926,
            "n_bootstrap": 2000, "n_mc": 10000, "rng_seed": 20261011,
        },
        "ci95": [-1.48, 9.10], "p_value": 0.0001, "n_observations": 2933,
        "data_version": "dlt_full_2933", "rules_epoch": "E6", "script": S_BACK,
    },
    caveats=[
        "识别依赖 p(F,B)∝u(F)·v(B)（前后区偏好可分离）—— 现有数据无法直接检验该假设。",
        "独立号码假设被饱和模型拒绝（LR=423.4，df=54）；s 的 Bootstrap CI 只含抽样不确定性，不含模型错设偏差。",
        "对特异偏好（饱和模型）的排名跨期显著不稳（相关 0.182 vs 稳定零模型 CI [0.572,0.815]），"
        "硬排除『历史热门对』会引入前视偏差（L6）。",
        "E6 仅 102 期，单独估计 66 个对密度功效不足；本条结论以全期合并为主。",
        "『开出率均匀』与『被选中率非均匀』必须分开表述（L7）—— 本条的全部策略含义只来自后者。",
        "不涉及中奖概率：单注一等奖概率恒 1/21,425,712。",
    ],
    source=S_BACK, tags=["back_zone", "collision", "l7", "l6"],
)

# ============================================================ 更新 F-0003
o = byid["F-0003"]
o["evidence"]["result_summary"] = (
    "全样本（2933 期）同期一等奖注数比 1.3603 [1.1415, 1.6243]；二等奖注数比 1.3520 [1.1667, 1.5761]。"
    "分期（切点 2013-08-28，F-0006 变点）：前段 960 期一等奖比 2.1072 [1.3045, 3.2397]、后段 1973 期 1.2472 "
    "[1.0360, 1.5075]；二等奖前段 2.4250、后段 1.2075。两段同向且显著，但幅度按均值比衰减 0.592 / 0.498；"
    "**稳健口径下衰减比只有 0.65~0.83**（前段 w1 均值比 2.107 剔除最大 1 期即降到 1.719、中位数比 1.000 —— 见 F-0020）；"
    "控制销量（NB2 offset）与成分（MH 标准化）后衰减仍显著，且与 F-0006 的号码结构变点同期（见 F-0021）。")
o["evidence"]["effect"]["split_2013_08"].update({
    "pre_prize1_ci95": [1.3045, 3.2397], "post_prize1_ci95": [1.0360, 1.5075],
    "decay_robust_range": [0.65, 0.83],
    "decay_mean_prize1": 0.592, "decay_mean_prize2": 0.498,
    "note_round04": "均值比口径的『衰减过半』被 r04 修正为估计量依赖（F-0020）；稳健口径 0.65~0.83。",
})
o["evidence"]["decay_script"] = S_DECAY
o["caveats"] = [
    "用了均值比，而一等奖注数是重尾分布（var/mean=8.46）—— L5 风险。r03 已用中位数比对照清偿（F-0018）。",
    "**强度随时间衰减，但幅度是估计量依赖的**：均值比给出后/前 = 0.592（w1）/0.498（w2）；"
    "稳健口径（中位数/截尾/剔除极端期）只有 0.65~0.83（F-0020）。不应按全样本 1.36 恒定外推，"
    "也不应引用『衰减过半』这一均值比说法。",
    "**衰减的归因未定**：前段数据本身在『号码分布—中出注数—销售额』三者间不自洽（F-0019），"
    "因此前段的 2.11 不能当作纯人群行为基线；弱化与号码结构变点同期，且已排除销量稀释（F-0021）。",
    "这是『被选中率』，不是『开出率』，两者不可混用（见 F-0005 / L7）。",
]
o["updated_at"] = TODAY
print("[fix] F-0003 幅度口径修正（引用 F-0019/F-0020/F-0021）")

# ============================================================ 更新 F-0004
o = byid["F-0004"]
o["claim"] = ("在固定预算下避开连号形态，可提高『中奖时的期望奖金』—— 未计封顶的上界为 109%（后段口径）/121%"
              "（全样本口径），计入封顶后实测锚点下约 41%")
o["evidence"]["result_summary"] = (
    "避开连号使条件撞号系数由 1.0028 降至 0.4528；比值 0.4515，95%CI [0.4487, 0.4543]；"
    "未计封顶的期望奖金提升 121.48%（全样本 α=13.9405 口径）。计入 1 亿总额封顶后（F-0017）：实测锚点下 41.42%。"
    "r04 按后段口径（R=1.2472 → α=12.7815）重算：未计封顶上界降为 109.39%，含封顶 40.64%（F-0022）。")
o["evidence"]["effect"].update({
    "prize_uplift_pct_nocap_post_segment": 109.39,
    "prize_uplift_pct_with_cap_anchor_post_segment": 40.64,
    "calibrated_alpha_post_segment": 12.7815,
    "calibration_script": S_DECAY,
})
o["evidence"]["recalibration_script"] = S_DECAY
o["caveats"] = [
    "模型依赖：α 与生日偏好系数由历史注数近似校准，是估计非真值。α 的口径本身有不确定性"
    "（全样本 13.9405 / 后段 12.7815 / 后段稳健 11.99）。",
    "**校准口径应为后段**（F-0022）：未计封顶上界由 121.5% 降为 109.4%；含封顶实测锚点净值几乎不变"
    "（41.0% → 40.6%），因为该处单注已被 1000 万元上限饱和。",
    "**封顶稀释（已量化）**：封顶在 E6 从未实际触发（F-0016），但其存在会压缩收益 —— 低注数情形会被单注上限抹平至 0（F-0017）。",
    "只在中奖时兑现：中奖概率 4.67e-08 不变，期望回报的提升被极小中奖概率大幅折现。",
    "长期期望回报仍为负（约 −0.98 元/注），本结论不改变这一事实。",
]
o["updated_at"] = TODAY
print("[fix] F-0004 校准口径 → 后段（引用 F-0022）")

# ============================================================ 更新 F-0011
o = byid["F-0011"]
o["claim"] = ("后区与前统计独立（互信息 0.203 < 置换基准 0.209），后区号码的『开出率』均匀；"
              "但这**不等于**后区人群偏好均匀 —— 后区的『被选中率』显著非均匀（见 F-0025）。"
              "原表述『不存在可利用的偏好结构』混淆了两个口径")
o["caveats"] = [
    "原结论的证据（66 组合频次 vs 均匀期望）全部是『开出率』，不含『被选中率』；"
    "r04 用 prize1/prize2 注数反推后区人群密度，发现被选中率强烈非均匀（过散布 8.72×，F-0025）。"
    "这是一次 L7 型口径混淆的修正。",
    "『统计独立』部分仍成立（互信息检验），且 66 组合开出率与均匀一致（χ²=64.09，MC p=0.51）。",
    "后区的非均匀偏好不可靠利用：前/后段交叉验证的避让收益 K=5/10 仅约 1~3%、95%CI 含 0（F-0025）。",
    "不涉及中奖概率。",
]
o["evidence"]["round04_crosscheck"] = {
    "script": S_BACK,
    "open_rate_uniform_p": 0.5104, "picked_rate_overdispersion": 8.72,
    "picked_rate_mc_p": 0.0001, "note": "开出率均匀 vs 被选中率非均匀，两者必须分开表述（L7）。",
}
o["updated_at"] = TODAY
print("[fix] F-0011 口径混淆修正（引用 F-0025）")

# ============================================================
ordered = sorted(byid.values(), key=lambda x: x["id"])
with open(FACTS, "w", encoding="utf-8") as f:
    for o in ordered:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"[write] {FACTS} 共 {len(ordered)} 条（新增 7 / 更新 3）")
