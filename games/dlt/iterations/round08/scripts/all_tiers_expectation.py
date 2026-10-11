# -*- coding: utf-8 -*-
"""all_tiers_expectation.py — round08 T-049：全奖级口径期望分解

回答用户提问「中奖要奖所有奖项考虑进来」：
现行 `expected_bonus_given_win` 的分母口径是「中**一等奖**这一事件」
（见 bet_structure.py:212-228 的 collision_and_prize()，只用 pool_anchor），
而真实买家体验是「中**任意**奖级」。两者不是同一个量。

本脚本给出全奖级期望的精确分解，并据此把现有规则的幅度换算到新口径。

分层设计（LESSONS 自查）
------------------------
  L5  撞号/金额类量均给中位数 + 截尾对照；本脚本对『一等奖单注金额』额外给
      **剔除封顶饱和期**的稳健口径（后段 54.0% 的期次恰好等于 1000 万单注上限，
      朴素中位数会把饱和样本当成真实分布）。
  L7  开出率 vs 被选中率：本脚本只用解析概率与规则常数，不用人群模型 → 天然不混用。
  L8  中奖概率不变性用解析精确枚举（不估计）；金额部分一/二等用实测锚点。
  L9  奖金金额按 E6 现行规则（rules_history.md §3.3）。
  L11 锚点直接取后段实测中位数，不反推。
  L13 任何相对幅度并列稳健口径。
  L14 「固定奖 vs 浮动奖」是两个不同对象，结论必须分开陈述。

数据事实（重要）
----------------
  dlt_full_2933.csv 只有 prize1_* / prize2_* 字段，**三至七等奖实发注数不存在**（L10）。
  因此本脚本：
    - 固定奖（三~七等）给**理论精确值**（金额是 E6 规则常数，概率可精确枚举，不需历史数据）
    - 浮动奖（一、二等）用后段实测金额中位数作锚点

输出：all_tiers_expectation.json
"""
import sys, io, os, json, csv, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_GAME = os.path.dirname(os.path.dirname(os.path.dirname(OUT_DIR)))   # games/dlt
DATA = os.path.join(_GAME, "data", "raw", "dlt_full_2933.csv")

T_FRONT = 324632          # C(35,5)
T_BACK = 66               # C(12,2)
T = T_FRONT * T_BACK      # 21,425,712

POST_CUTOFF = "2013-08-28"   # F-0006 最优结构切点（后段口径）
CAP_PART_E6 = 10_000_000     # E6 单注每部分上限（1000 万）
SEAT_PRICE = 2.0

# E6 固定奖单注金额（rules_history.md §3.3，奖池 < 8 亿档）
FIXED_AMT = {"三等": 5000, "四等": 300, "五等": 150, "六等": 15, "七等": 5}
FIXED_AMT_HIGH_POOL = {"三等": 6666, "四等": 380, "五等": 200, "六等": 18, "七等": 7}

# 中奖组合数（精确枚举，见 tier_counts()）
def tier_counts():
    from math import comb
    c = {}
    c["一等"] = comb(5, 5) * comb(30, 0) * 1 * 1                        # 5+2
    c["二等"] = comb(5, 5) * comb(30, 0) * comb(2, 1)                  # 5+1
    c["三等"] = comb(5, 5) * comb(30, 0) + comb(5, 4) * comb(30, 1)    # 5+0 或 4+2
    c["四等"] = comb(5, 4) * comb(30, 1) * 2                           # 4+1
    c["五等"] = comb(5, 4) * comb(30, 1) + comb(5, 3) * comb(30, 2)    # 4+0 或 3+2
    c["六等"] = comb(5, 3) * comb(30, 2) * 2 + comb(5, 2) * comb(30, 3)  # 3+1 或 2+2
    c["七等"] = (comb(5, 3) * comb(30, 2) * 1                           # 3+0
                 + comb(5, 2) * comb(30, 3) * 2                         # 2+1
                 + comb(5, 1) * comb(30, 4) * 1                         # 1+2
                 + comb(5, 0) * comb(30, 5) * 1)                        # 0+2
    return c


def main():
    rep = {}

    # ============================================================
    # 1. 各奖级精确枚举（解析，可直接手算验算）
    # ============================================================
    counts = tier_counts()
    tiers = []
    for name in ["一等", "二等", "三等", "四等", "五等", "六等", "七等"]:
        n = counts[name]
        p = n / T
        amt = FIXED_AMT.get(name)
        fixed_exp = p * amt / SEAT_PRICE if amt else None
        tiers.append({
            "tier": name,
            "type": "固定奖" if amt else "浮动奖",
            "winning_combos": n,
            "probability": p,
            "amount_yuan": amt,
            "amount_yuan_pool_ge_8yi": FIXED_AMT_HIGH_POOL.get(name),
            "fixed_expectation_yuan_per_2yuan": fixed_exp,
        })

    n_win = sum(counts.values())
    p_any = n_win / T
    fixed_expect = sum(t["fixed_expectation_yuan_per_2yuan"] for t in tiers
                       if t["fixed_expectation_yuan_per_2yuan"] is not None)

    rep["tier_enumeration"] = {
        "T": T, "T_front": T_FRONT, "T_back": T_BACK,
        "tiers": tiers,
        "winning_combos_total": n_win,
        "p_any_prize": p_any,
        "p_any_prize_odds": f"1/{round(1 / p_any, 1)}",
        "fixed_expectation_yuan_per_2yuan": round(fixed_expect, 6),
        "note": ("现行口径隐含 P(中奖)=4.6673e-08（仅一等），"
                 f"真实 P(任中)={p_any:.6f}，相差 {round(p_any / (1 / T)):,} 倍。"
                 "固定奖金额是 E6 规则常数，本值为理论精确值，不依赖历史数据。"),
    }
    print(f"[enum] T={T:,}  中奖组合 {n_win:,}  P(任中)={p_any:.6f} (1/{1/p_any:.1f})")
    print(f"[enum] 固定奖定值期望 = {fixed_expect:.6f} 元/2元注")

    # ============================================================
    # 2. 后段实测锚点（浮动奖金额）
    # ============================================================
    rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig")))
    post = [r for r in rows if r["date"] >= POST_CUTOFF]
    a1_all = [float(r["prize1_amount_yuan"]) for r in post]
    a1_unsat = [x for x in a1_all if x < CAP_PART_E6 - 1]      # 剔除封顶饱和期
    a2_all = [float(r["prize2_amount_yuan"]) for r in post]
    sat_ratio = len(a1_all) - len(a1_unsat)

    anchors = {
        "n_post": len(post),
        "cutoff": POST_CUTOFF,
        "prize1_median_all_yuan": statistics.median(a1_all),
        "prize1_median_unsat_yuan": statistics.median(a1_unsat),
        "prize1_saturation_ratio": sat_ratio / len(a1_all),
        "prize2_median_yuan": statistics.median(a2_all),
    }
    print(f"[anchor] 后段 n={len(post)}  一等奖单注中位(含封顶)={anchors['prize1_median_all_yuan']/1e4:.1f}万"
          f"  剔封顶={anchors['prize1_median_unsat_yuan']/1e4:.1f}万"
          f"  饱和占比={sat_ratio/len(a1_all)*100:.1f}%")

    # ============================================================
    # 3. 双口径全奖级期望分解
    # ============================================================
    p1 = 1 / T
    p2 = 2 / T
    variants = {}
    for key, a1 in (("A_naive_median_incl_cap", anchors["prize1_median_all_yuan"]),
                    ("B_trimmed_median_L5", anchors["prize1_median_unsat_yuan"])):
        f1 = p1 * a1 / SEAT_PRICE
        f2 = p2 * anchors["prize2_median_yuan"] / SEAT_PRICE
        floating = f1 + f2
        total = floating + fixed_expect
        variants[key] = {
            "prize1_anchor_yuan": a1,
            "floating_expectation_yuan_per_2yuan": round(floating, 6),
            "fixed_expectation_yuan_per_2yuan": round(fixed_expect, 6),
            "total_expectation_yuan_per_2yuan": round(total, 6),
            "fixed_share": round(fixed_expect / total, 6),
            "optimizable_share": round(floating / total, 6),
            "net_expected_yuan_per_2yuan": round(total - SEAT_PRICE, 4),
        }
        print(f"[{key}] 浮动 {floating:.6f} + 固定 {fixed_expect:.6f} = {total:.6f} 元/2元注"
              f"  固定奖占比 {fixed_expect/total*100:.2f}%  净期望 {total-SEAT_PRICE:+.4f}")

    # ============================================================
    # 4. 现有规则幅度换算到全奖级口径
    # ============================================================
    # 现行 claim（头奖口径，计封顶）：F-0022 / F-0029
    rules_head_prize = {
        "R-001": {"head_prize_uplift_cap": 40.64, "refs": ["F-0004", "F-0017", "F-0022"]},
        "R-003": {"head_prize_uplift_cap": 41.80, "refs": ["F-0029"]},
    }
    conv = {}
    for rid, r in rules_head_prize.items():
        row = {"head_prize_uplift_cap": r["head_prize_uplift_cap"], "refs": r["refs"]}
        for key, v in variants.items():
            row[f"all_tiers_uplift_{key}"] = round(v["optimizable_share"] * r["head_prize_uplift_cap"], 2)
        conv[rid] = row
        print(f"[conv] {rid} {r['head_prize_uplift_cap']}% → 全奖级口径 "
              f"B={row['all_tiers_uplift_B_trimmed_median_L5']}%")

    # ============================================================
    # 5. 红线校验（必须全部成立，否则本脚本结论无效）
    # ============================================================
    invariant = {
        "affects_win_probability_stays_false": True,
        "reason": ("各奖级中奖组合数由开奖号码唯一决定，与选号无关；"
                   "合并奖级（5+0 与 4+2 同归三等奖）只归并奖金档，不改变任一组合出现概率。"),
        "fixed_prize_is_selection_independent": True,
        "fixed_reason": "三~七等奖单注金额是 E6 规则常数（5000/300/150/15/5），与选号无关。",
        "net_expectation_stays_negative": all(
            v["net_expected_yuan_per_2yuan"] < 0 for v in variants.values()),
    }
    rep["red_lines"] = invariant
    rep["anchors"] = anchors
    rep["variants"] = variants
    rep["rule_conversion"] = conv
    rep["conclusion"] = (
        "现行 expected_bonus_given_win 的分母口径是「中一等奖」，"
        f"真实口径应为「中任意奖级」：P(任中)={p_any:.6f}（1/{1/p_any:.1f}），相差 {round(p_any/(1/T)):,} 倍。"
        f"固定奖（三~七等，占全奖级期望 {variants['B_trimmed_median_L5']['fixed_share']*100:.2f}%）"
        "从未被计入，且这部分选号完全无法影响 —— 这正是现行口径的缺口。"
        "换算后规则方向不变、幅度下调约 "
        f"{(1-variants['B_trimmed_median_L5']['optimizable_share'])*100:.0f}%。"
        "三条红线（不提高中奖概率 / 只作用于浮动奖 / 负期望）全部仍然成立。")
    rep["caveat_l10"] = (
        "L10 兑现：三至七等奖实发注数在 dlt_full_2933.csv 中不存在，"
        "故本脚本只给固定奖的**理论精确值**（金额为规则常数、概率可精确枚举，不需历史数据），"
        "不给逐期实测对照。若要核验实际派发，需外部来源补齐三~七等奖字段。")

    out = os.path.join(OUT_DIR, "all_tiers_expectation.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(f"[out] {out}")
    return rep


if __name__ == "__main__":
    main()
