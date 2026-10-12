# -*- coding: utf-8 -*-
"""platform/tools/compress_memory.py — 记忆压缩（v2.0，每 5 轮执行）

学术依据：IterResearch（arXiv 2511.07327）『周期性合成 + 战略性遗忘』；
MEM1（arXiv 2506.15841）『推理驱动的记忆巩固 + 战略性丢弃』；TiM 的 merge。

原则（与 superseded 纪律一致）：
  · 只读 FACTS.jsonl，**不移动、不删除任何数据**（审计留痕优先）
  · 输出两个产物：
      1. memory/facts/ACTIVE.md —— 『当前有效结论清单』（与台账分离，
         解决信噪比：失效条目保留在台账，但 active 视图只给可用结论）
      2. 压缩统计 + merge 候选（同 category 多条 active，提示是否可合并）
  · 动态锚点到期清单：recalibrate_every 到期 → 提示走 update 通道重校准

用法：
    python platform/tools/compress_memory.py            # 只读：打印统计与建议
    python platform/tools/compress_memory.py --write    # 额外写出 ACTIVE.md
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_facts(root: str = ROOT) -> list[dict]:
    p = os.path.join(root, "memory", "facts", "FACTS.jsonl")
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def current_round(root: str = ROOT) -> int:
    best = 0
    gd = os.path.join(root, "games")
    if os.path.isdir(gd):
        for g in os.listdir(gd):
            d = os.path.join(gd, g, "iterations")
            if not os.path.isdir(d):
                continue
            for name in os.listdir(d):
                m = re.match(r"^round(\d{2})$", name)
                if m:
                    best = max(best, int(m.group(1)))
    return best


def analyze(facts: list[dict], cur: int) -> dict:
    total = len(facts)
    active = [f for f in facts if f.get("status") == "established"]
    superseded = [f for f in facts if f.get("status") == "superseded"]
    refuted = [f for f in facts if f.get("status") == "refuted"]
    tentative = [f for f in facts if f.get("status") == "tentative"]

    # 动态锚点到期
    due = []
    for f in active:
        n = f.get("recalibrate_every")
        m = re.match(r"^round(\d{2})$", f.get("established_in") or "")
        if n and m and cur - int(m.group(1)) >= n:
            due.append(f)

    # merge 候选：同 category + 同 claim_type 的 active 多条
    merge_groups = []
    key = Counter()
    for f in active:
        key[(f.get("category"), f.get("claim_type"))] += 1
    for (cat, ct), n in key.items():
        if n >= 3:
            merge_groups.append((cat, ct, n))

    return {
        "total": total, "active": len(active), "superseded": len(superseded),
        "refuted": len(refuted), "tentative": len(tentative),
        "due_recal": due, "merge_groups": merge_groups,
        "by_category": Counter(f.get("category") for f in active),
    }


def render_active_md(facts: list[dict], cur: int) -> str:
    lines = [
        "# 当前有效结论清单（ACTIVE VIEW）",
        "",
        f"> 由 `platform/tools/compress_memory.py --write` 生成 ｜ 当前轮 round{cur:02d}"
        f" ｜ 权威源 `memory/facts/FACTS.jsonl`（台账保留全部历史，本视图只列可用结论）",
        "",
        "| F-id | 结论 | 类型 | 置信度 | 变更通道 | 重校准 | 确立轮 |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in sorted(facts, key=lambda x: x["id"]):
        if f.get("status") != "established":
            continue
        grade = f.get("confidence_grade") or "-"
        ct = f.get("change_type") or "-"
        rec = f.get("recalibrate_every")
        rec_txt = f"{rec} 轮" if rec else "-"
        claim = (f.get("claim") or "")[:64]
        lines.append(
            f"| {f['id']} | {claim} | {f.get('claim_type','')} | {grade} |"
            f" {ct} | {rec_txt} | {f.get('established_in','')} |"
        )
    lines.append("")
    lines.append("## 动态锚点待重校准（update 通道）")
    due = [f for f in facts if f.get("status") == "established"
           and _is_due(f, cur)]
    if due:
        for f in due:
            lines.append(f"- **{f['id']}** {f.get('claim','')[:60]}（{f.get('established_in')} 确立，已超 {f.get('recalibrate_every')} 轮周期）")
    else:
        lines.append("- 无到期项。")
    return "\n".join(lines) + "\n"


def _is_due(f: dict, cur: int) -> bool:
    n = f.get("recalibrate_every")
    m = re.match(r"^round(\d{2})$", f.get("established_in") or "")
    return bool(n and m and cur - int(m.group(1)) >= n)


def main(argv: list[str]) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    facts = load_facts()
    if not facts:
        print("FACTS.jsonl 不存在或为空")
        return 1
    cur = current_round()
    a = analyze(facts, cur)

    print(f"=== 记忆压缩统计（当前 round{cur:02d}） ===")
    print(f"总条目 {a['total']} ｜ 有效 {a['active']} ｜ superseded {a['superseded']}"
          f" ｜ refuted {a['refuted']} ｜ tentative {a['tentative']}")
    print(f"有效结论按分析层：{dict(a['by_category'])}")
    if a["due_recal"]:
        print("⚠ 动态锚点到期（应走 update 通道重校准）：")
        for f in a["due_recal"]:
            print(f"  - {f['id']} {f.get('claim','')[:60]}")
    else:
        print("✓ 无动态锚点到期项")
    if a["merge_groups"]:
        print("🔀 merge 候选（同 category+claim_type ≥3 条，可考虑合并，TiM merge）：")
        for cat, ct, n in a["merge_groups"]:
            print(f"  - {cat} / {ct}：{n} 条")
    else:
        print("✓ 无 merge 候选")

    if "--write" in argv:
        md = render_active_md(facts, cur)
        out = os.path.join(ROOT, "memory", "facts", "ACTIVE.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n✓ 已写出 {os.path.relpath(out, ROOT)}（{len(md)} 字符）")
    print("\n提示：本脚本只读 + 生成视图，不移动/删除任何数据（审计留痕优先）。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
