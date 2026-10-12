# -*- coding: utf-8 -*-
"""t062_h002_segment.py — H-002 三段单调预测检验（r16）

## 假设原文（labs/lottery/studies/dlt/memory/workbench/HYPOTHESES.md H-002）

> 生日偏好不是「`max ≤ 31` 一刀切」，而是**按号递减**：1–12 最强（月），
> 13–31 次之（日），32–35 最弱。可证伪预测：逐号权重应满足 1–12 > 13–31 > 32–35。

## 为什么要现在做

F-0038（r09，T-020）已经估出 35 个号的相对撞号强度 S_j，但当时只做了
**两段**比较（1-31 vs 32-35，差 0.047，CI 含 0 → 无显著差异），
**没有检验 H-002 预言的三段单调**。也就是说：产出已存在、假设还挂着
`unverified` —— 数据侧零成本，只差一次按假设口径的复算。

## 方法

直接用 F-0038 的 S_j（脚本 `round09/scripts/t020_number_weight.py`，n=1973 后段期）：
  1. 三段均值与全序关系（点估计）
  2. Bootstrap（10k 次，**按段分层有放回重抽**，段内样本量 12/19/4）
     给出段间差的 95% CI —— 32-35 只有 4 个号，CI 必然宽，这一点必须如实写进结论
  3. 单调性置换检验：随机打乱号→段的分配，看「三段严格递减」这一**序型**
     偶然出现的概率（比逐段 t 检验更贴合「单调」这个可证伪预测）

注意口径：S_j 是**相对撞号强度**（1.0 = 无偏好），越大表示该号被越多的人选中
→ 撞号越严重 → 越应该避开。所以 H-002 预测的是 **撞号强度递减**，不是偏好递减。
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "..", ".."))
SRC = os.path.join(ROOT, "games", "dlt", "iterations", "round09", "scripts",
                   "t020_number_weight.json")
OUT = os.path.join(_HERE, "t062_h002_segment.json")

SEED = 20261012
N_BOOT = 10000
N_PERM = 20000
SEG = {"1-12": (1, 12), "13-31": (13, 31), "32-35": (32, 35)}


def main() -> int:
    rng = np.random.default_rng(SEED)
    d = json.load(open(SRC, encoding="utf-8"))
    s = d["per_number_strength"]
    groups = {k: np.array([s[str(i)] for i in range(a, b + 1)])
              for k, (a, b) in SEG.items()}

    means = {k: float(v.mean()) for k, v in groups.items()}
    sds = {k: float(v.std(ddof=1)) for k, v in groups.items()}
    mono = means["1-12"] > means["13-31"] > means["32-35"]
    print("三段均值（相对撞号强度 S_j，1.0=无偏好）：")
    for k in ("1-12", "13-31", "32-35"):
        print(f"  {k:>6}: n={len(groups[k]):>2}  mean={means[k]:.4f}  sd={sds[k]:.4f}")
    print(f"  全序单调（1-12 > 13-31 > 32-35）: {mono}")

    def boot_diff(a: str, b: str) -> tuple[float, list[float]]:
        ga, gb = groups[a], groups[b]
        diffs = np.empty(N_BOOT)
        for i in range(N_BOOT):
            diffs[i] = (rng.choice(ga, ga.size, replace=True).mean()
                        - rng.choice(gb, gb.size, replace=True).mean())
        return float(means[a] - means[b]), [float(np.percentile(diffs, 2.5)),
                                            float(np.percentile(diffs, 97.5))]

    pairs = {}
    for a, b in (("1-12", "13-31"), ("13-31", "32-35"), ("1-12", "32-35")):
        diff, ci = boot_diff(a, b)
        sig = ci[0] > 0 or ci[1] < 0
        pairs[f"{a}_vs_{b}"] = {"diff": round(diff, 4),
                                "ci95": [round(ci[0], 4), round(ci[1], 4)],
                                "significant": bool(sig)}
        print(f"  {a} − {b}: {diff:+.4f}  CI95 [{ci[0]:+.4f}, {ci[1]:+.4f}]  "
              f"{'显著' if sig else '不显著（含 0）'}")

    # 单调性置换检验：打乱 号→段 的分配（段大小固定 12/19/4）
    allv = np.concatenate([groups["1-12"], groups["13-31"], groups["32-35"]])
    sizes = [len(groups["1-12"]), len(groups["13-31"]), len(groups["32-35"])]
    hits = 0
    for _ in range(N_PERM):
        p = rng.permutation(allv)
        i = 0
        ms = []
        for sz in sizes:
            ms.append(p[i:i + sz].mean())
            i += sz
        if ms[0] > ms[1] > ms[2]:
            hits += 1
    p_mono = hits / N_PERM
    print(f"  单调性置换检验：p = {p_mono:.4f}（H0 = 号与段的分配随机；"
          f"{N_PERM} 次置换，段大小 12/19/4 固定）")

    verdict = ("方向支持" if mono else "不支持")
    if mono and p_mono >= 0.05:
        verdict += "（序型未达显著）"
    out = {
        "source": "labs/lottery/studies/dlt/iterations/round09/scripts/t020_number_weight.json",
        "upstream_fact": "F-0038",
        "n_observations": 1973,
        "segment_means": {k: round(v, 4) for k, v in means.items()},
        "segment_sd": {k: round(v, 4) for k, v in sds.items()},
        "segment_n": {k: len(v) for k, v in groups.items()},
        "monotonic_point": bool(mono),
        "pairwise_diff": pairs,
        "monotonicity_permutation_p": round(p_mono, 4),
        "n_boot": N_BOOT,
        "n_perm": N_PERM,
        "seed": SEED,
        "verdict": verdict,
        "caliber_note": ("S_j 为相对撞号强度（1.0=无偏好），越大=越多人在该号撞车、"
                         "越应避开。H-002 预测的『按号递减』在本口径下即撞号强度递减。"),
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(OUT, "a", encoding="utf-8").write("\n")
    print(f"[written] {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
