# -*- coding: utf-8 -*-
"""apply_r03_facts.py — T-004 落地：把 r03 三条任务的结论写入 FACTS.jsonl

动作清单
--------
  1. F-0015  修正：claim 原称「26113 期触发了 1 亿封顶」→ 实测未触发。
             → status 改 superseded（被 F-0016 取代）
  2. F-0016  新增：封顶条款在 E6 现行规则下【从未触发】（解析可证 + 全期扫描）
  3. F-0017  新增：封顶后收益的净值重算（条件模拟 + 封顶后处理）
  4. F-0003  更新：补分期稳健性结论（幅度衰减，非仅早期成立）
  5. F-0004  更新：magnitude 修正为「封顶后净值」+ 新增 caveat
  6. F-0018  新增：L5 技术债清偿（三估计量对照）

写法：JSONL 逐行读 → 定位 → 替换/追加 → 整体回写（保持恰一行一条）。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
FACTS = os.path.join(ROOT, "memory", "facts", "FACTS.jsonl")
TODAY = "2026-10-11"

facts = []
with open(FACTS, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            facts.append(json.loads(line))
byid = {o["id"]: o for o in facts}
print(f"[load] {len(facts)} 条 facts，ids = {[o['id'] for o in facts]}")

# 脚本相对路径（仓库根为基准）
S_CAP = "labs/lottery/studies/dlt/iterations/round03/scripts/cap_adjusted_uplift.py"
S_SPLIT = "labs/lottery/studies/dlt/iterations/round03/scripts/b2_split_stability.py"
S_ROBUST = "labs/lottery/studies/dlt/iterations/round03/scripts/b2_robust_estimators.py"

# ============================================================
# 1. 修正 F-0015 → superseded
# ============================================================
o = byid["F-0015"]
o["claim"] = ("【已修正】第 26113 期（2026-10-05）37 注一等奖的单注 239 万元，"
              "是自然摊薄结果，**并未触发** 1 亿元封顶（当期总额仅 0.8852 亿）")
o["status"] = "superseded"
o["confidence"] = 5
o["confidence_basis"] = ("原结论基于对 26113 期的误读（把自然摊薄当作封顶触发）。"
                         "经全期扫描（E6 共 102 期）核实：总额从未 ≥ 1 亿。"
                         "本条的『封顶机制存在』仍成立，但『已触发』的断言被证伪。")
o["evidence"] = {
    "method": "全期扫描（E6 102 期一等奖总额 w1×amt1）+ 官方规则文本核对",
    "result_summary": ("E6（>=26014 期）全部 102 期中，一等奖单期总额最大值 0.9788 亿"
                       "（26060 期），**没有任何一期达到 1 亿封顶**。26113 期总额 0.8852 亿，"
                       "未触发。单注 239 万 = 0.8852亿/37 的自然摊薄。"
                       "单注上限 1000 万（官方：分档每部分 500 万，合计 1000 万）实测吻合。"),
    "effect": {
        "epoch_draws": 102,
        "max_total1_yi": 0.9788,
        "max_total1_draw": "26060",
        "n_triggered": 0,
        "draw_26113_total1_yi": 0.8852,
        "draw_26113_triggered": False,
    },
    "ci95": None,
    "p_value": None,
    "n_observations": 102,
    "data_version": "dlt_full_2933",
    "rules_epoch": "E6",
    "script": S_CAP,
}
o["caveats"] = [
    "封顶机制确实存在于规则文本（总额 1 亿 / 单注 1000 万），只是现行规则期内样本还不够长 —— 从未被 102 期的实际数据触发。",
    "不能因『从未触发』就断言『永不触发』：若某期一等奖注数显著上升（如 40+ 注），仍可能触发。",
    "原 claim 的 239 万数字正确，但归因（『因封顶而压低』）错误 —— 已由 F-0016 取代。",
]
o["superseded_by"] = "F-0016"
o["updated_at"] = TODAY
print("[fix] F-0015 → superseded（被 F-0016 取代）")

# ============================================================
# 2. 新增 F-0016：封顶从未触发
# ============================================================
byid["F-0016"] = {
    "id": "F-0016",
    "game": "dlt",
    "claim": ("现行规则（E6，>=26014 期）下『一等奖单期总额封顶 1 亿元』条款从未触发："
              "102 期一等奖总额最大值仅 0.9788 亿元"),
    "status": "established",
    "confidence": 5,
    "confidence_basis": "解析可证 + 全期扫描：可分配总额与单注金额均为可观测量，无需估计。封顶阈值由规则文本确定。观测 102 期最大值 < 阈值，结论直接成立。",
    "category": "prize_mechanism",
    "affects_win_probability": False,
    "evidence": {
        "method": "全期扫描（解析）：逐期计算 w1×amt1，与 1 亿阈值比较；单注上限与官方文本核对",
        "result_summary": ("E6 期 102 期一等奖总额最大 0.9788 亿（26060 期），次高 0.8852 亿"
                           "（26113 期）；0 期达到 1 亿封顶。实测单注最大恰 1000.0 万，"
                           "与官方『分档每部分 500 万，合计上限 1000 万』一致。"
                           "临界注数：若单注满 1000 万，则 10 注即达 1 亿；"
                           "按各期实际单注金额算，触发阈值中位数为 13 注（区间 10.0~41.8）。"),
        "effect": {
            "epoch": "E6",
            "n_draws": 102,
            "cap_total_yuan": 100000000,
            "max_total1_yuan": 97883574,
            "max_total1_draw": "26060",
            "n_triggered": 0,
            "critical_w1_at_1000wan": 10,
            "threshold_w1_median": 13.0,
            "threshold_w1_range": [10.0, 41.8],
            "observed_max_single_amt_yuan": 10000000,
        },
        "ci95": None,
        "p_value": None,
        "n_observations": 102,
        "data_version": "dlt_full_2933",
        "rules_epoch": "E6",
        "script": S_CAP,
    },
    "caveats": [
        "『从未触发』是**样本内**结论（102 期）。随 E6 延续，若出现 40+ 注一等奖的期次仍可能触发。",
        "结论依赖于「一等奖所有中奖注数（含追加）总额单期最高 1 亿」这一官方口径（5 个来源交叉确认）。",
        "不涉及号码选择：本条不改变任何中奖概率（affects_win_probability=false）。",
    ],
    "established_in": "round03",
    "supersedes": "F-0015",
    "superseded_by": None,
    "source": S_CAP,
    "tags": ["prize", "cap", "epoch_scan", "analytical"],
    "created_at": TODAY,
    "updated_at": None,
}
print("[new] F-0016 封顶从未触发")

# ============================================================
# 3. 新增 F-0017：封顶后收益净值重算
# ============================================================
byid["F-0017"] = {
    "id": "F-0017",
    "game": "dlt",
    "claim": ("把 1 亿封顶纳入条件份额模拟后，避开连号的期望奖金提升由 121.48%（未计封顶）"
              "降为实测锚点下约 41.4%，且低注数情形下会被单注上限抹平至 0"),
    "status": "established",
    "confidence": 3,
    "confidence_basis": "条件模拟（模型估计）：依赖人群权重模型 α（沿用 F-0004 校准，非真值）。比 F-0016 弱一档。锚点 n0 与 Pool 直接取自实测（未新增自由参数）。",
    "category": "prize_mechanism",
    "affects_win_probability": False,
    "evidence": {
        "method": "条件份额模拟（100 注 × 300000 次）+ 封顶确定性后处理；锚点取实测中位数",
        "result_summary": ("实测锚点：E6 一等奖中出注数中位 6 注、总派发额中位 0.4252 亿。"
                           "三档情形 uplift（含封顶）：anchor(n0=6) 41.42%、"
                           "anchor_lo(n0=3) 0.00%（两侧未封顶单注均超 1000 万上限 → 被抹平）、"
                           "anchor_hi(n0=9) 112.12%。均未触发 1 亿总额封顶。"
                           "未计封顶的 121.48% 为收益上界。"),
        "effect": {
            "uplift_nocap_pct": 121.48,
            "uplift_anchor_pct": 41.42,
            "uplift_anchor_lo_pct": 0.0,
            "uplift_anchor_hi_pct": 112.12,
            "anchor_n0_tickets": 6.0,
            "anchor_pool_yi": 0.4252,
            "cap_triggered": False,
            "n_sim": 300000,
            "n_tickets": 100,
            "rng_seed": 20261011,
        },
        "ci95": [0.4491, 0.4547],
        "p_value": None,
        "n_observations": 300000,
        "data_version": "dlt_full_2933",
        "rules_epoch": "E6",
        "script": S_CAP,
    },
    "caveats": [
        "模型依赖：α=13.9405 与生日偏好系数由历史注数近似校准，是估计非真值。",
        "锚点 n0/Pool 取 E6 实测中位数；±50% 为敏感性区间而非置信区间 —— 真实行情形可能超出该范围。",
        "『单注上限抹平』（uplift→0）是封顶条款的真实作用：当两家未封顶单注都 > 1000 万时，差距被同一上限压平。",
        "只在中奖时兑现：中奖概率 4.67e-8 不变，期望回报提升被极小概率折现。",
    ],
    "established_in": "round03",
    "supersedes": None,
    "superseded_by": None,
    "source": S_CAP,
    "tags": ["collision", "economic", "simulation", "cap"],
    "created_at": TODAY,
    "updated_at": None,
}
print("[new] F-0017 封顶后收益净值")

# ============================================================
# 4. 更新 F-0003：补分期稳健性
# ============================================================
o = byid["F-0003"]
o["evidence"]["result_summary"] = (
    "全样本（2933 期）同期一等奖注数比 1.3603 [1.1415, 1.6243]；二等奖注数比 1.3520"
    " [1.1667, 1.5761]。n_ge2=292，n_lt2=2641。**分期（切点 2013-08-28）："
    "前段 960 期一等奖比 2.1072 [1.3213, 3.2616]、后段 1973 期 1.2472 [1.0315, 1.4907]；"
    "二等奖前段 2.4250 [1.5817, 3.5869]、后段 1.2075 [1.0475, 1.4093]。"
    "两段均同向且显著，但幅度衰减过半（后/前 = 0.59 / 0.50，二等奖两段 CI 不重叠 → 衰减显著）。**"
)
o["evidence"]["effect"]["split_2013_08"] = {
    "changepoint": "2013-08-28",
    "pre_n": 960, "post_n": 1973,
    "pre_prize1_ratio": 2.1072, "pre_prize1_ci95": [1.3213, 3.2616],
    "post_prize1_ratio": 1.2472, "post_prize1_ci95": [1.0315, 1.4907],
    "pre_prize2_ratio": 2.4250, "post_prize2_ratio": 1.2075,
    "decay_post_over_pre_prize1": 0.592,
    "decay_post_over_pre_prize2": 0.498,
    "sign_consistent": True,
    "amplitude_decay_significant": True,
}
# 更新第二条 caveat（原为"尚未做分期稳健性"）
o["caveats"] = [
    "用了均值比，而一等奖注数是重尾分布（var/mean=8.46）—— L5 风险。"
    "已清偿：见 F-0018（中位数比 1.5 与截尾检验均支持效应稳健）。",
    "**强度随时间衰减**：分期检验显示幅度从早期的 ~2.1 降至后期的 ~1.25"
    "（后段 CI 下界仅 1.03，逼近零效应边界）。效应仍成立，但不应按全样本 1.36 恒定外推。",
    "这是『被选中率』，不是『开出率』，两者不可混用（见 F-0005）。",
]
o["evidence"]["script"] = S_SPLIT
o["updated_at"] = TODAY
print("[fix] F-0003 补分期稳健性（幅度衰减）")

# ============================================================
# 5. 更新 F-0004：magnitude 改为封顶后净值
# ============================================================
o = byid["F-0004"]
o["claim"] = ("在固定预算下避开连号形态，可提高『中奖时的期望奖金』—— "
              "未计封顶的上界为 121%，计入封顶后实测锚点下约 41%")
o["evidence"]["result_summary"] = (
    "避开连号使条件撞号系数由 1.0028 降至 0.4528；比值 0.4515，95%CI [0.4487, 0.4543]；"
    "等价于中一等奖时的期望奖金提升 121.48%（**未计封顶的上界**）。"
    "计入 1 亿总额封顶后（F-0017）：实测锚点下 uplift = 41.42%；"
    "低注数情形被单注上限抹平至 0%；高注数情形 112.12%。"
)
o["evidence"]["effect"]["prize_uplift_pct_nocap"] = 121.48
o["evidence"]["effect"]["prize_uplift_pct_with_cap_anchor"] = 41.42
o["evidence"]["effect"]["cap_adjusted_script"] = S_CAP
o["caveats"] = [
    "模型依赖：α=13.9405 与生日偏好系数由历史注数近似校准，是估计非真值。",
    "**封顶稀释（已量化）**：未计封顶的 121% 是上界；计入 1 亿总额封顶后实测锚点下约 41%（F-0017）。"
    "封顶在 E6 从未实际触发（F-0016），但其存在会压缩收益 —— 尤其低注数情形会被单注上限抹平。",
    "只在中奖时兑现：中奖概率 4.67e-8 不变，期望回报的提升被极小中奖概率大幅折现。",
    "长期期望回报仍为负（约 −0.98 元/注），本结论不改变这一事实。",
]
o["evidence"]["script"] = S_CAP
o["updated_at"] = TODAY
print("[fix] F-0004 magnitude = 封顶后净值")

# ============================================================
# 6. 新增 F-0018：L5 技术债清偿
# ============================================================
byid["F-0018"] = {
    "id": "F-0018",
    "game": "dlt",
    "claim": ("F-0003 的撞号效应不依赖均值比：中位数比 1.5 [1.5, 2.0] 与均值比同向，"
              "且截尾检验显示重尾仅贡献 1.72% —— L5 技术债可清偿"),
    "status": "established",
    "confidence": 4,
    "confidence_basis": "观测 + Bootstrap（中位数比）+ 参数模型（NB2 MLE）+ 截尾敏感性。多口径交叉，非解析。",
    "category": "methodology",
    "affects_win_probability": False,
    "evidence": {
        "method": "三估计量对照（均值比 / 中位数比 + Bootstrap / NB2-MLE IRR + HAC）+ L1 过度离散检查 + L5 截尾检验",
        "result_summary": ("一等奖：均值比 1.3603 [1.1415, 1.6243]、中位数比 1.5 [1.5, 2.0]、"
                           "NB2 IRR 1.3603（HAC [1.1352, 1.6301]，alpha_MLE=1.0034）。"
                           "三口径方向一致、CI 下界均 > 1。"
                           "L1：var/mean=8.46 >> 1 → 泊松失效，须 NB2（已满足）。"
                           "L5：剔除 w1>P99 后均值比 1.3603→1.3369（仅变化 1.72%）→ 重尾不主导。"
                           "注：NB2 log 链接下 IRR 数值上等于均值比，故独立证据是中位数比。"),
        "effect": {
            "mean_ratio": 1.3603, "mean_ratio_ci95": [1.1415, 1.6243],
            "median_ratio": 1.5, "median_ratio_ci95": [1.5, 2.0],
            "nb2_irr": 1.3603, "nb2_irr_ci95_HAC": [1.1352, 1.6301],
            "nb2_alpha_mle": 1.0034,
            "var_over_mean_w1": 8.4628,
            "trim_p99_relative_change": 0.0172,
            "all_same_direction": True,
        },
        "ci95": [1.5, 2.0],
        "p_value": 0.000006,
        "n_observations": 2933,
        "data_version": "dlt_full_2933",
        "rules_epoch": None,
        "script": S_ROBUST,
    },
    "caveats": [
        "中位数比 CI [1.5, 2.0] 较宽（中位数取值离散 → Bootstrap 分布呈阶梯），CI 下界恰为 1.5。",
        "NB2 IRR 与均值比数值等价，不构成独立证据；独立证据是中位数比 + 截尾检验。",
        "本条只清偿『重尾是否主导均值比』的方法学质疑，不改变 F-0003 的幅度衰减结论（见 F-0003）。",
    ],
    "established_in": "round03",
    "supersedes": None,
    "superseded_by": None,
    "source": S_ROBUST,
    "tags": ["methodology", "robustness", "l5_debt", "collision"],
    "created_at": TODAY,
    "updated_at": None,
}
print("[new] F-0018 L5 技术债清偿")

# ============================================================
# 回写
# ============================================================
ordered = sorted(byid.values(), key=lambda x: x["id"])
with open(FACTS, "w", encoding="utf-8") as f:
    for o in ordered:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"[write] {FACTS}  共 {len(ordered)} 条")
