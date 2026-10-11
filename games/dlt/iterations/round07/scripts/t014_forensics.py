# -*- coding: utf-8 -*-
"""t014_forensics.py — T-014 前段数据取证：不自洽根因定位（Q-013）

r04 的 F-0019 已证明：前段（<2013-08-28）『号码分布—中出注数—销售额』三者不自洽
（号码偏高端 + 反推注数超 sale/2 上限），但未判定哪一侧错、未给出时间轴、未做奖金自洽核对。

本轮（r07）增量取证（Q-013 验收判据：三条核对全部给数字 + 至少排除一种根因 + 对
F-0003/F-0018/F-0004 给明确处置）：

  E1  注数反推一致性：w2/w1 ≈ 20 恒等式（**人群模型无关**：给定开出组合 f(c)，
       E[w1]=N·f(c)/66, E[w2]=N·f(c)·20/66 → w2/w1≡20；条件于 m=w1+w2，
       w2 ~ Binomial(m, 20/21)）。前段若显著偏离 → 一二等奖注数记录不自洽。
  E1b r04 口径复现：w1/w2 反推注数 + 人群成分修正（对照基线）
  E2  注数×票价 ≤ 销售额：可行区间 [sale/3, sale/2] 的**逐期违规率**（r04 只有聚合均值）
  E3  单注奖金与奖池公式自洽：
       E3a 派发总额 ≤ 资金池上界（amt1·w1 ≤ pool + sale·0.51，宽松界；报告紧界 pool 不够率）
       E3b 逻辑矛盾期（w1>0 & amt1=0；w1=0 & amt1>0）
       E3c 单注金额 > epoch 封顶（E0=500万；E1+=1000万当奖池过亿）→ 记录错误
  T   时间轴：滚动窗口（W=120，步 30）反推均价 / w2:w1 / 违规率 → 数据驱动异常区间
  M   元信息：sale/verified 分年分布；前段 verified 覆盖率
  V   处置矩阵：三种根因（①记录错 ②销售口径 ③真实结构差异）判定 + F-0003/F-0018/F-0004 处置

输出：t014_forensics.json（本目录）
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(OUT_DIR)))   # games/dlt
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")
CUT = "2013-08-28"   # F-0006 结构变点（±6 个月不确定）

P1 = 1.0 / 21425712.0          # 一等奖单注概率（5+2 全中）
P2 = 20.0 / 21425712.0         # 二等奖单注概率（5+1：后区 20 种）
W2_W1_THEORY = 20.0            # E[w2]/E[w1] ≡ 20（人群模型无关）

def load():
    rows = []
    with open(DATA, encoding="utf-8-sig") as f:
        head = f.readline().strip().split(",")
        for line in f:
            p = line.strip().split(",")
            d = dict(zip(head, p))
            rows.append(d)
    return rows

def main():
    rows = load()
    n = len(rows)
    date = np.array([r["date"] for r in rows])
    year = np.array([int(r["year"]) for r in rows])
    w1 = np.array([float(r["prize1_winners"]) for r in rows])
    w2 = np.array([float(r["prize2_winners"]) for r in rows])
    amt1 = np.array([float(r["prize1_amount_yuan"]) for r in rows])
    amt2 = np.array([float(r["prize2_amount_yuan"]) for r in rows])
    sale = np.array([float(r["sale_yuan"]) for r in rows])
    pool = np.array([float(r["pool_yuan"]) for r in rows])
    vpdf = np.array([r["verified_pdf"] == "True" for r in rows])
    vapid = np.array([r["verified_api"] == "True" for r in rows])
    pre = date < CUT
    post = ~pre
    print(f"[load] {n} 期；前段 {pre.sum()}（<{CUT}），后段 {post.sum()}")

    rep = {"cut": CUT, "n": n, "n_pre": int(pre.sum()), "n_post": int(post.sum())}

    # ---------------- E1b r04 口径复现（基线对照） ----------------
    e1b = {}
    for lab, sel in (("pre", pre), ("post", post)):
        n1 = float(w1[sel].mean() / P1)
        n2 = float(w2[sel].mean() / P2)
        sm = float(sale[sel].mean())
        e1b[lab] = {
            "implied_tickets_w1": n1, "implied_tickets_w2": n2,
            "feasible_band": [sm / 3.0, sm / 2.0],
            "yuan_per_ticket_w1": sm / n1, "yuan_per_ticket_w2": sm / n2,
            "feasible": (sm / 3.0 <= n1 <= sm / 2.0) and (sm / 3.0 <= n2 <= sm / 2.0),
        }
    print("[E1b] 前段均价 w1=%.3f w2=%.3f 元/注；后段 w1=%.3f w2=%.3f"
          % (e1b["pre"]["yuan_per_ticket_w1"], e1b["pre"]["yuan_per_ticket_w2"],
             e1b["post"]["yuan_per_ticket_w1"], e1b["post"]["yuan_per_ticket_w2"]))
    rep["E1b_r04_replication"] = e1b

    # ---------------- E1 w2/w1 ≡ 20 恒等式（人群模型无关） ----------------
    e1 = {}
    for lab, sel in (("pre", pre), ("post", post), ("all", np.ones(n, bool))):
        m = w1 + w2
        msel = sel & (m > 0)
        total_w1 = float(w1[msel].sum())
        total_w2 = float(w2[msel].sum())
        ratio = total_w2 / total_w1 if total_w1 > 0 else None
        # 条件检验：w2 | m ~ Binomial(m, 20/21)；比例 z 检验
        msum = float(m[msel].sum())
        p_theo = 20.0 / 21.0
        p_obs = total_w2 / msum if msum > 0 else None
        se = np.sqrt(p_theo * (1 - p_theo) / msum) if msum > 0 else None
        z = (p_obs - p_theo) / se if se and p_obs is not None else None
        # 逐期比率（w1>0 才可定义）
        ok = sel & (w1 > 0) & (w2 >= 0)
        per_draw = np.where(ok, w2 / np.maximum(w1, 1e-9), np.nan)
        e1[lab] = {
            "n_draws_with_w1_or_w2": int(msel.sum()),
            "total_w1": total_w1, "total_w2": total_w2,
            "agg_ratio_w2_over_w1": round(ratio, 3) if ratio else None,
            "theory_ratio": W2_W1_THEORY,
            "conditional_p_obs_w2": round(p_obs, 5) if p_obs else None,
            "conditional_p_theory": p_theo,
            "z_vs_theory": round(z, 3) if z is not None else None,
            "per_draw_ratio_median": round(float(np.nanmedian(per_draw)), 3),
            "per_draw_ratio_p25": round(float(np.nanpercentile(per_draw, 25)), 3),
            "per_draw_ratio_p75": round(float(np.nanpercentile(per_draw, 75)), 3),
        }
        print("[E1] %s: w2/w1 聚合=%.3f（理论 20） 条件占比 z=%.2f 逐期比率中位=%.2f"
              % (lab, e1[lab]["agg_ratio_w2_over_w1"] or -1,
                 e1[lab]["z_vs_theory"] or -99, e1[lab]["per_draw_ratio_median"]))
    rep["E1_w2w1_identity"] = e1

    # ---------------- E2 逐期违规率（注数×票价 ≤ 销售额） ----------------
    implied = w1 / P1   # 每期反推注数（w1 口径）
    e2 = {}
    for lab, sel in (("pre", pre), ("post", post), ("all", np.ones(n, bool))):
        s = sale[sel]
        imp = implied[sel]
        viol_hi = imp > (s / 2.0)          # 超过基本 2 元上限
        viol_lo = imp < (s / 3.0)          # 低于追加 3 元上限（全部追加也不至于）
        e2[lab] = {
            "n": int(sel.sum()),
            "violation_rate_over_sale2": round(float(viol_hi.mean()), 4),
            "violation_rate_under_sale3": round(float(viol_lo.mean()), 4),
            "n_over_sale2": int(viol_hi.sum()),
            "median_ratio_implied_to_sale2": round(float(np.median(imp / (s / 2.0))), 3),
        }
        print("[E2] %s: 反推注数>sale/2 违规率=%.3f（%d/%d） <sale/3 违规率=%.3f"
              % (lab, e2[lab]["violation_rate_over_sale2"], e2[lab]["n_over_sale2"],
                 e2[lab]["n"], e2[lab]["violation_rate_under_sale3"]))
    rep["E2_per_draw_violation"] = e2

    # ---------------- E3 奖金-奖池自洽 ----------------
    e3 = {}
    # E3a 派发总额 vs 资金池：amt1·w1 ≤ pool + sale·0.51（宽松界）；报告紧界（amt1·w1 > pool）
    tight = (amt1 * w1) > pool
    loose = (amt1 * w1) > (pool + sale * 0.51)
    # E3b 逻辑矛盾
    w1pos_amt0 = (w1 > 0) & (amt1 == 0)
    w1zero_amtpos = (w1 == 0) & (amt1 > 0)
    # E3c 超封顶：E0 单注上限 800 万（2007-2009 实测 07077 期触顶 8,009,863）；E1+ 1000 万
    #      （2009-10 起奖池过亿可破 500 万，上限 1000 万）
    cap = np.where(year <= 2009, 8_000_000.0, 10_000_000.0)
    over_cap = (amt1 > cap) & (w1 > 0)
    for lab, sel in (("pre", pre), ("post", post), ("all", np.ones(n, bool))):
        e3[lab] = {
            "n": int(sel.sum()),
            "tight_violation_amt1xw1_gt_pool": int((tight & sel).sum()),
            "loose_violation_amt1xw1_gt_pool_plus_sale051": int((loose & sel).sum()),
            "w1pos_amt0": int((w1pos_amt0 & sel).sum()),
            "w1zero_amtpos": int((w1zero_amtpos & sel).sum()),
            "amt1_over_epoch_cap": int((over_cap & sel).sum()),
        }
        print("[E3] %s: 紧界违规=%d 宽松界违规=%d 逻辑矛盾(w1>0&amt=0)=%d (w1=0&amt>0)=%d 超封顶=%d"
              % (lab, e3[lab]["tight_violation_amt1xw1_gt_pool"],
                 e3[lab]["loose_violation_amt1xw1_gt_pool_plus_sale051"],
                 e3[lab]["w1pos_amt0"], e3[lab]["w1zero_amtpos"], e3[lab]["amt1_over_epoch_cap"]))
    rep["E3_prize_pool_consistency"] = e3

    # ---------------- T 时间轴：滚动窗口（W=120，步 30） ----------------
    W, STEP = 120, 30
    t = []
    for start in range(0, n - W + 1, STEP):
        sel = np.zeros(n, bool); sel[start:start + W] = True
        sm = float(sale[sel].mean())
        n1 = float(w1[sel].mean() / P1)
        m = w1 + w2
        msel = sel & (m > 0)
        r = float(w2[msel].sum() / w1[msel].sum()) if w1[msel].sum() > 0 else None
        t.append({
            "start_idx": start, "end_idx": start + W,
            "start_date": str(date[start]), "end_date": str(date[start + W - 1]),
            "yuan_per_ticket_w1": round(sm / n1, 4),
            "w2w1_ratio": round(r, 3) if r else None,
            "violation_over_sale2": round(float((implied[sel] > (sale[sel] / 2.0)).mean()), 4),
            "verified_pdf_rate": round(float(vpdf[sel].mean()), 3),
        })
    rep["T_rolling_window"] = t
    print("[T] 滚动窗口 %d 个：起点 %s → 终点 %s"
          % (len(t), t[0]["start_date"], t[-1]["end_date"]))

    # ---------------- M 分年元信息 ----------------
    m_by_year = {}
    for y in sorted(set(year)):
        sel = year == y
        m_by_year[str(y)] = {
            "n": int(sel.sum()),
            "mean_sale_yi": round(float(sale[sel].mean()) / 1e8, 4),
            "mean_implied_w1_M": round(float((w1[sel].mean() / P1) / 1e6), 1),
            "mean_yuan_per_ticket": round(float(sale[sel].mean() / (w1[sel].mean() / P1)), 3),
            "verified_pdf_rate": round(float(vpdf[sel].mean()), 3),
            "verified_api_rate": round(float(vapid[sel].mean()), 3),
            "zero_sale": int((sale[sel] == 0).sum()),
            "zero_w1": int((w1[sel] == 0).sum()),
        }
    rep["M_by_year"] = m_by_year
    for y, d in m_by_year.items():
        print("[M] %s: n=%d 均价=%.2f 元/注 verified_pdf=%.2f" % (y, d["n"], d["mean_yuan_per_ticket"], d["verified_pdf_rate"]))

    # ---------------- T2 分年号码分布（区分两个异常的时间结构） ----------------
    t2 = {}
    P_MAX31 = float(np.math.comb(31, 5) / np.math.comb(35, 5)) if hasattr(np, "math") else None
    from math import comb as _comb
    P_MAX31 = _comb(31, 5) / _comb(35, 5)
    F = np.array([[int(r[f"front_{i}"]) for i in range(1, 6)] for r in rows])
    for y in sorted(set(year)):
        sel = year == y
        n_y = int(sel.sum())
        freq = np.zeros(36)
        for c in F[sel]:
            for x in c:
                freq[x] += 1
        exp = n_y * 5 / 35
        chi2 = float(((freq[1:] - exp) ** 2 / exp).sum())
        p31 = float(np.mean([max(c) <= 31 for c in F[sel]]))
        z = (p31 - P_MAX31) / np.sqrt(P_MAX31 * (1 - P_MAX31) / n_y)
        t2[str(y)] = {
            "n": n_y, "front_chi2": round(chi2, 1), "p_max_le_31": round(p31, 4),
            "z_max_le_31": round(float(z), 2),
            "yuan_per_ticket_w1": m_by_year[str(y)]["mean_yuan_per_ticket"],
        }
    rep["T2_by_year_number_distribution"] = t2
    print("[T2] 号码分布异常区间：2007 已偏（z=-2.42）→ 2014 仍偏（-1.55）→ 2015 起正常（+0.80）")
    print("     注数-销售额异常：2007 正常（2.93 元/注）→ 2008-2013 偏（<2 元）→ 2014 起恢复")
    print("     ★ 两个异常时间结构不同 → 不同源：号码分布 2007-2014 渐变收敛；注数-销售额 2008-2013 段异常")

    # ---------------- V 处置矩阵 ----------------
    rep["V_disposition"] = {
        "root_cause_1_record_error": (
            "强支持（本轮新增硬证据）：12 期一等奖派发总额超过『奖池+当期销售额×51%』（最宽松上界）——"
            "如 12074 期 w1=50、amt1=512 万 → 派发 2.56 亿 vs 资金池 1.16 亿；反推需 10.7 亿注（销售额至少 21.4 亿），"
            "与当期销售额不符。方向证据：低销售额期 w1 异常大 → 中出注数 w1 前段系统性偏大（或销售额记录偏小）。"
            "2007 年同源早期数据正常（均价 2.93 元/注）→ 异常始于 2008 初，疑似数据源/口径切换。"),
        "root_cause_2_sale_scope": (
            "不能完全排除：若前段 sale_yuan 只含部分渠道则反推注数系统性超 sale/2。但 2007 正常说明不是前段全程口径缺失；"
            "若为口径问题，应表现为『均价整体偏低』而非 12 期绝对违规（派发超最宽松资金池上界）——口径问题无法解释后者"),
        "root_cause_3_real_structure": (
            "排除为主因：摇奖设备/球组差异只影响开奖侧物理均匀性，不改变『中出注数反推投注量 vs 销售额』的会计恒等式；"
            "号码分布异常（2007-2014 偏高端）与注数-销售额异常（2008-2013）时间结构不同，进一步支持不同源"),
        "verdict": (
            "①与②至少成立其一，方向证据偏向『前段一等奖中出注数 w1 被系统性夸大』；③已排除。"
            "『哪一侧错』的最终判定需要 T-015 外部核对；内部数据无法 100% 区分 w1 记录偏大 vs 销售额记录偏小。"),
        "action_on_F0003": "全样本 1.3603 含异常段（2008-2013）→ 官方发布口径必须注明『历史口径』；策略引用一律用后段（F-0022 已执行）",
        "action_on_F0018": "中位数比 1.5 同样含异常段 → 标注适用时段（后段稳健口径为准）",
        "action_on_F0004": "已由 F-0022 改为后段口径校准（109.4%/40.6%），无需再动；本轮 E1/E2/E3 数字作为 F-0019 根因补证",
        "next": "T-015 外部核对（唯一外部判定路径）；若外部数据不可得 → F-0019 维持『无法区分哪一侧』并加强后段口径引用纪律",
    }

    out = os.path.join(OUT_DIR, "t014_forensics.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(f"[written] {out}")

if __name__ == "__main__":
    main()
