# -*- coding: utf-8 -*-
"""t050_calibration.py — T-050 概率口径标注：各奖级精确概率表 + 受管文件口径检索清单

输出：
1. 各奖级中奖注数与概率（解析计算，全奖级合计）；
2. 全文检索「中奖概率 / 4.667e-08 / 21,425,712 / 21425712」的出现位置，
   标注哪些需要补奖级限定（T-050 文档修改依据）。
"""
import io, json, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from math import comb

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "t050_calibration.json")

# ---------- 1. 各奖级精确概率 ----------
T = comb(35, 5) * comb(12, 2)  # 21,425,712
# 中奖注数（现行 E6 9 奖级）
prizes = [
    ("一等奖", "5+2", 1),
    ("二等奖", "5+1", comb(2, 1) * comb(10, 1)),
    ("三等奖", "5+0", comb(10, 2)),
    ("四等奖", "4+2", comb(5, 4) * comb(30, 1)),
    ("五等奖", "4+1", comb(5, 4) * comb(30, 1) * comb(2, 1) * comb(10, 1)),
    ("六等奖", "3+2", comb(5, 3) * comb(30, 2)),
    ("七等奖", "4+0", comb(5, 4) * comb(30, 1) * comb(10, 2)),
    ("八等奖", "3+1 或 2+2", comb(5, 3) * comb(30, 2) * comb(2, 1) * comb(10, 1)
     + comb(5, 2) * comb(30, 3)),
    ("九等奖", "3+0 / 2+1 / 1+2 / 0+2", comb(5, 3) * comb(30, 2) * comb(10, 2)
     + comb(5, 2) * comb(30, 3) * comb(2, 1) * comb(10, 1)
     + comb(5, 1) * comb(30, 4) + comb(30, 5)),
]
total_wins = sum(w for _, _, w in prizes)
table = [{"prize": p, "match": m, "n_wins": w, "prob": round(w / T, 10),
          "one_in": round(T / w, 1)} for p, m, w in prizes]
assert T == 21425712, f"总组合校验失败: {T}"
assert total_wins == 1429197, f"全奖级中奖注数校验失败: {total_wins}"

# ---------- 2. 受管文件口径检索 ----------
SCAN_DIRS = [ROOT]
SCAN_GLOB = ["*.md", "*.py", "*.json", "*.yaml"]
PAT_PROB = re.compile(r"(中奖概率|4\.667e-08|4\.67e-08|21[,]?425[,]?712|21425712)")
PAT_QUAL = re.compile(r"(一等奖|任一奖级|全奖级|任意奖级|各奖级|头奖)")

hits = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in (".git", "target", "__pycache__", ".sessions", "node_modules")]
    for fn in files:
        if not fn.endswith((".md", ".py", ".json", ".yaml")):
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if PAT_PROB.search(line):
                qual = bool(PAT_QUAL.search(line))
                if not qual:
                    hits.append({"path": rel, "line": i,
                                 "snippet": line.strip()[:110]})

# ---------- 汇总 ----------
rep = {
    "total_combinations": T,
    "first_prize_prob": {"as_fraction": f"1/{T}", "decimal": round(1 / T, 10)},
    "any_prize_prob": {"fraction_approx": "≈1/15", "decimal": round(total_wins / T, 6),
                       "percent": round(100 * total_wins / T, 2)},
    "prize_table": table,
    "total_wins_combos": total_wins,
    "needs_calibration_hits": hits,
    "n_hits_without_qualifier": len(hits),
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"[prob] 一等奖 1/{T} = {1/T:.3e}；任一奖级 ≈ {total_wins/T:.4f}（1/15）")
print(f"[scan] 缺奖级限定的匹配 {len(hits)} 处：")
for h in hits[:30]:
    print(f"  {h['path']}:{h['line']}  {h['snippet'][:70]}")
print(f"[write] {os.path.basename(OUT)}")
print("done")
