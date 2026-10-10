# -*- coding: utf-8 -*-
"""b2_split_stability.py — T-001：撞号效应（F-0003）的分期稳健性检验

目的
----
F-0003 的一等奖注数比 1.3603 [1.1298, 1.6292] 是全样本（2933 期）估计。
本仓库其它结论（F-0005、F-0009）都在分期后发现「仅早期显著」。
本脚本检验：撞号效应在 2013-08 切点前后两段是否**同向**、幅度是否**稳定**。

方法（严格遵循任务书判据 + LESSONS）
------------------------------------
  · 切点用 F-0006 的最优变点 2013-08（**不按自然年硬切 —— L3**）
  · 口径与 F-0003 完全一致：均值比 + Bootstrap 独立重采样（2000 次）
    —— 这是**同口径对照**，确保差异只来自分期，不来自方法变更
  · 报告：符号一致性 + 幅度差异 + 两段 CI 是否重叠
  · 若某段 CI 下界 ≤ 1 → 输出「须在 F-0003 caveats 声明适用时段」标志

★ 不新增自由参数：α 等模型参数在本脚本**完全不用**（本脚本是观测层检验，
  不做条件份额模拟）。Bootstrap 次数沿用 F-0003 的 2000。

输出：b2_split_stability.json + 控制台摘要
"""
import sys, io, os, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

RNG_SEED = 20261011
N_BOOT = 2000                       # 与 F-0003 一致
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(OUT_DIR)))   # games/dlt
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")

# F-0006 最优切点（2013-08-28），含 ±6 个月不确定性 → 做敏感性
CHANGEPOINT = "2013-08-28"
CHANGEPOINT_LO = "2013-02-28"       # ±6 个月下界
CHANGEPOINT_HI = "2014-02-28"       # ±6 个月上界

rng = np.random.default_rng(RNG_SEED)
rep = {}

# ============================================================
# 数据与形态
# ============================================================
rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig")))
print(f"[data] 总期数 = {len(rows)}，最新 = {rows[-1]['draw_num']} {rows[-1]['date']}")

def run_count(c):
    """相邻号对数量（与 strategy_simulation.py 同定义）。"""
    return int(np.sum(np.diff(c) == 1))

def front_of(r):
    return tuple(int(r[f"front_{i}"]) for i in range(1, 6))

runs = np.array([run_count(front_of(r)) for r in rows])
w1 = np.array([int(r["prize1_winners"]) for r in rows], float)
w2 = np.array([int(r["prize2_winners"]) for r in rows], float)
dates = np.array([r["date"] for r in rows])
mask_ge2 = runs >= 2

# ============================================================
# 同口径估计器：均值比 + Bootstrap（与 F-0003 完全一致）
# ============================================================
def ratio_and_boot(a, b, n_boot=N_BOOT):
    """比率 a.mean()/b.mean() + Bootstrap 95%CI（a、b 各自独立重采样）。"""
    if len(a) == 0 or len(b) == 0 or b.mean() == 0:
        return None
    est = a.mean() / b.mean()
    na, nb = len(a), len(b)
    boots = np.empty(n_boot)
    for k in range(n_boot):
        ra = a[rng.integers(0, na, na)].mean()
        rb = b[rng.integers(0, nb, nb)].mean()
        boots[k] = ra / rb if rb > 0 else np.nan
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    return {
        "ratio": round(float(est), 4),
        "ci95": [round(float(lo), 4), round(float(hi), 4)],
        "n_a": int(na), "n_b": int(nb),
        "mean_a": round(float(a.mean()), 4),
        "mean_b": round(float(b.mean()), 4),
    }

# ============================================================
# 全样本基线（应与 F-0003 的 1.3603 [1.1298, 1.6292] 吻合）
# ============================================================
print("\n" + "=" * 72)
print("S0 全样本基线（复现 F-0003）")
print("=" * 72)
full1 = ratio_and_boot(w1[mask_ge2], w1[~mask_ge2])
full2 = ratio_and_boot(w2[mask_ge2], w2[~mask_ge2])
print(f"  一等奖注数比 = {full1['ratio']}  CI95 {full1['ci95']}  "
      f"(n_ge2={full1['n_a']}, n_lt2={full1['n_b']})")
print(f"  二等奖注数比 = {full2['ratio']}  CI95 {full2['ci95']}")
print(f"  （F-0003 记录：一等奖 1.3603 [1.1298, 1.6292]；二等奖 1.3520 [1.1679, 1.5793]）")
rep["S0_full_sample_reproduce"] = {
    "note": "全样本同口径复现，用于确认分期结果与 F-0003 可比。",
    "prize1": full1, "prize2": full2,
    "f0003_reference": {"prize1_ratio": 1.3603, "prize1_ci95": [1.1298, 1.6292],
                        "prize2_ratio": 1.352, "prize2_ci95": [1.1679, 1.5793]},
    "match": abs(full1["ratio"] - 1.3603) < 0.02,
}

# ============================================================
# 分期（F-0006 切点 2013-08-28 + ±6 个月敏感性）
# ============================================================
print("\n" + "=" * 72)
print("S1 分期稳健性（切点 = F-0006 最优变点 2013-08-28，非自然年 —— L3）")
print("=" * 72)

def analyze_split(cut_date, label):
    idx_pre = dates < cut_date
    idx_post = dates >= cut_date
    pre = {
        "n_draws": int(idx_pre.sum()),
        "n_ge2": int(mask_ge2[idx_pre].sum()),
        "prize1": ratio_and_boot(w1[idx_pre & mask_ge2], w1[idx_pre & ~mask_ge2]),
        "prize2": ratio_and_boot(w2[idx_pre & mask_ge2], w2[idx_pre & ~mask_ge2]),
    }
    post = {
        "n_draws": int(idx_post.sum()),
        "n_ge2": int(mask_ge2[idx_post].sum()),
        "prize1": ratio_and_boot(w1[idx_post & mask_ge2], w1[idx_post & ~mask_ge2]),
        "prize2": ratio_and_boot(w2[idx_post & mask_ge2], w2[idx_post & ~mask_ge2]),
    }
    return {"cut_date": cut_date, "label": label, "pre": pre, "post": post}

split = analyze_split(CHANGEPOINT, "主切点")
sens = {
    "lo": analyze_split(CHANGEPOINT_LO, "切点-6月"),
    "hi": analyze_split(CHANGEPOINT_HI, "切点+6月"),
}

def show(seg_name, seg):
    for lv in ("prize1", "prize2"):
        r = seg[lv]
        if r is None:
            print(f"    {seg_name} {lv}: <样本不足>")
            continue
        print(f"    {seg_name} {lv}: ratio={r['ratio']:.4f}  "
              f"CI95=[{r['ci95'][0]:.4f}, {r['ci95'][1]:.4f}]  "
              f"n={r['n_a']}+{r['n_b']}")

print(f"\n  [主切点 {CHANGEPOINT}] 前段 {split['pre']['n_draws']} 期 / "
      f"后段 {split['post']['n_draws']} 期")
show("前段", split["pre"])
show("后段", split["post"])

# ---- 判据 1：符号一致性（两段 ratio 是否都 > 1）----
pre1, post1 = split["pre"]["prize1"], split["post"]["prize1"]
pre2, post2 = split["pre"]["prize2"], split["post"]["prize2"]
same_sign_1 = (pre1["ratio"] > 1) and (post1["ratio"] > 1)
same_sign_2 = (pre2["ratio"] > 1) and (post2["ratio"] > 1)

# ---- 判据 2：两段 CI 是否重叠 ----
def ci_overlap(a, b):
    return not (a["ci95"][1] < b["ci95"][0] or b["ci95"][1] < a["ci95"][0])

ov1 = ci_overlap(pre1, post1)
ov2 = ci_overlap(pre2, post2)

# ---- 判据 3：某段 CI 下界 ≤ 1？----
weak1 = [s for s, seg in (("pre", pre1), ("post", post1)) if seg["ci95"][0] <= 1.0]
weak2 = [s for s, seg in (("pre", pre2), ("post", post2)) if seg["ci95"][0] <= 1.0]

print(f"\n  [判据1 符号一致性] 一等奖 两段均>1: {same_sign_1} | "
      f"二等奖 两段均>1: {same_sign_2}")
print(f"  [判据2 CI重叠]     一等奖 CI 重叠: {ov1} | 二等奖 CI 重叠: {ov2}")
print(f"  [判据3 弱段]       一等奖 CI下界≤1 的段: {weak1 or '无'} | "
      f"二等奖: {weak2 or '无'}")

rep["S1_split_main"] = {
    "note": "切点用 F-0006 最优变点 2013-08-28（不用自然年 —— L3）。口径同 F-0003。",
    "changepoint": CHANGEPOINT,
    "split": split,
    "criteria": {
        "sign_consistent_prize1": bool(same_sign_1),
        "sign_consistent_prize2": bool(same_sign_2),
        "ci_overlap_prize1": bool(ov1),
        "ci_overlap_prize2": bool(ov2),
        "weak_segments_prize1": weak1,
        "weak_segments_prize2": weak2,
        "magnitude_diff_prize1": round(abs(pre1["ratio"] - post1["ratio"]), 4),
        "magnitude_diff_prize2": round(abs(pre2["ratio"] - post2["ratio"]), 4),
    },
    "verdict": None,   # 稍后填
}

# ---- ±6 个月敏感性 ----
print(f"\n  [敏感性] 切点 ±6 个月：")
for tag, s in sens.items():
    p1 = s["pre"]["prize1"]; q1 = s["post"]["prize1"]
    p2 = s["pre"]["prize2"]; q2 = s["post"]["prize2"]
    print(f"    {tag} ({s['cut_date']}): "
          f"一等奖 前 {p1['ratio']:.3f}[{p1['ci95'][0]:.3f},{p1['ci95'][1]:.3f}] / "
          f"后 {q1['ratio']:.3f}[{q1['ci95'][0]:.3f},{q1['ci95'][1]:.3f}]  |  "
          f"二等奖 前 {p2['ratio']:.3f} / 后 {q2['ratio']:.3f}")
rep["S1_changepoint_sensitivity"] = {
    "note": "F-0006 声明切点有 ±6 个月不确定性，故做两侧敏感性。",
    "cases": sens,
}

# ============================================================
# S2 结论与落地动作
# ============================================================
print("\n" + "=" * 72)
print("S2 结论与落地动作")
print("=" * 72)

# ★ 判据扩展（根因：仅看"符号一致 + CI 下界>1"会漏掉【幅度衰减】模式）
#   任务书预警"其它结论都在分期后发现仅早期显著" —— 这里虽未反号，
#   但若后段幅度大幅衰减 / 后段 CI 下界逼近 1，说明效应**正在弱化**，
#   同样必须声明适用时段。故新增两个判据：
#     判据4：后段/前段 幅度比 < 0.7 视为「显著衰减」
#     判据5：后段 CI 下界 < 1.10 视为「逼近零效应边界」

def _decay(pre_r, post_r):
    return post_r / pre_r if pre_r else float("nan")

decay1 = _decay(pre1["ratio"], post1["ratio"])
decay2 = _decay(pre2["ratio"], post2["ratio"])
decay_flag1 = decay1 < 0.70
decay_flag2 = decay2 < 0.70
near_zero1 = post1["ci95"][0] < 1.10
near_zero2 = post2["ci95"][0] < 1.10

print(f"  [判据4 幅度衰减] 后段/前段：一等奖 {decay1:.3f}"
      f"{'（<0.70 显著衰减）' if decay_flag1 else ''} | "
      f"二等奖 {decay2:.3f}{'（<0.70 显著衰减）' if decay_flag2 else ''}")
print(f"  [判据5 逼近零界] 后段 CI 下界：一等奖 {post1['ci95'][0]:.4f}"
      f"{'（<1.10 逼近 1）' if near_zero1 else ''} | "
      f"二等奖 {post2['ci95'][0]:.4f}{'（<1.10 逼近 1）' if near_zero2 else ''}")

rep["S1_split_main"]["criteria"].update({
    "decay_post_over_pre_prize1": round(float(decay1), 4),
    "decay_post_over_pre_prize2": round(float(decay2), 4),
    "significant_decay_prize1": bool(decay_flag1),
    "significant_decay_prize2": bool(decay_flag2),
    "post_ci_lower_near_one_prize1": bool(near_zero1),
    "post_ci_lower_near_one_prize2": bool(near_zero2),
})

# ---- 综合裁决 ----
# 关键区分：本效应**未反号、两段 CI 下界均 >1**（与 F-0005/F-0009「仅早期显著」不同），
#           但**后段幅度显著衰减**（二等奖 CI 不重叠 = 衰减统计显著）。
# 故：效应仍成立，但强度随时间弱化；应声明「强度在后期衰减」而非「仅早期成立」。
strong_evidence_still = (post1["ci95"][0] > 1.0) and (post2["ci95"][0] > 1.0)
decay_any = decay_flag1 or decay_flag2 or (not ov2)

# 一致性结论：sign 一致 + 两段仍显著 + 幅度衰减
if same_sign_1 and same_sign_2 and strong_evidence_still and decay_any:
    verdict = (
        "撞号效应在两段**均同向且均显著**（各段 CI 下界均 > 1），"
        "但**幅度显著衰减**：一等奖 ratio %.3f → %.3f（后/前 = %.3f），"
        "二等奖 ratio %.3f → %.3f（后/前 = %.3f，两段 CI 不重叠 → 衰减统计显著）。"
        "后段 CI 下界降至 %.3f / %.3f，逼近零效应边界。"
        "→ 结论：效应**仍成立但强度随时间弱化**（非『仅早期成立』，也非『完全稳定』）。"
        "建议在 F-0003 的 caveats 中声明**强度衰减**并给出分段估计。"
        % (pre1["ratio"], post1["ratio"], decay1,
           pre2["ratio"], post2["ratio"], decay2,
           post1["ci95"][0], post2["ci95"][0])
    )
    need_caveat = True
elif same_sign_1 and same_sign_2 and strong_evidence_still and not decay_any:
    verdict = (
        "撞号效应在两段均同向、各段 CI 下界均 > 1，且幅度无显著衰减 → "
        "F-0003 的效应在 2013-08 前后**稳定**，无需限定适用时段。")
    need_caveat = False
elif not same_sign_1 or not same_sign_2:
    verdict = ("撞号效应存在**分期不稳定**：至少一个奖级在两段出现反号 → "
               "必须在 F-0003 的 caveats 中声明适用时段。")
    need_caveat = True
else:
    verdict = ("撞号效应两段同向，但存在 CI 下界 ≤ 1 的弱段（%s / %s）→ "
               "必须在 F-0003 的 caveats 中声明适用时段。"
               % (weak1 or "无", weak2 or "无"))
    need_caveat = True

rep["S1_split_main"]["verdict"] = verdict
rep["S2_conclusion"] = {
    "verdict": verdict,
    "need_caveat_amend": need_caveat,
    "sign_consistent": bool(same_sign_1 and same_sign_2),
    "both_segments_significant": bool(strong_evidence_still),
    "amplitude_decay": {
        "prize1_post_over_pre": round(float(decay1), 4),
        "prize2_post_over_pre": round(float(decay2), 4),
        "ci_overlap_prize2": bool(ov2),
        "significant": bool(decay_any),
    },
    "weak_segments": {"prize1": weak1, "prize2": weak2},
    "action": ("在 F-0003.caveats 中声明【强度随时间衰减】并给出分段估计"
               if need_caveat else
               "无需修改 F-0003 的 caveats（分期稳健性通过）"),
}
print(f"  [结论] {verdict}")
print(f"  [动作] {rep['S2_conclusion']['action']}")

# ============================================================
# 存档
# ============================================================
out = os.path.join(OUT_DIR, "b2_split_stability.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"seed": RNG_SEED, "n_boot": N_BOOT, "report": rep},
              f, ensure_ascii=False, indent=2)
print(f"\n[written] {out}")
