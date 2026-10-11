# -*- coding: utf-8 -*-
"""b2_fill_evidence_index.py — r16 还债（B2）：补齐策略侧的证据登记

清掉 7 条结构性警告：

| 警告 | 条数 | 修法 |
|---|---|---|
| `evidence_index 未覆盖被引用的结论 F-0044~F-0047` | 1 | `strategy.json.evidence_index` 补 4 条 |
| `STRATEGY_GUIDE.md 正文引用了 F-0041/F-0044/F-0045/F-0046 但未登记 consumes` | 6 | `versions.json` 该条目 `consumes` 补 4 项 |

为什么算「债」而不是「新研究」：这些结论在 r12~r14 就已入库并被策略引用
（R-004 的 `evidence_refs` 直接列了 F-0044~F-0047），只是**索引侧没跟上**。
证据索引是给下游消费者看的摘要层，缺了就迫使消费者回读 FACTS.jsonl ——
正是 validate 那条警告的意思。

⚠️ `evidence_index` 变更后 `evidence_hash` 必须重算（`rehash --strategy`），
否则策略契约与它的证据摘要再次分叉（同源双向比对的又一处）。
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
STRATEGY = os.path.join(ROOT, "games", "dlt", "strategy", "strategy.json")
VERSIONS = os.path.join(ROOT, "versions.json")
FACTS = os.path.join(ROOT, "memory", "facts", "FACTS.jsonl")
GUIDE_PATH = "games/dlt/strategy/STRATEGY_GUIDE.md"

ADD_INDEX = ["F-0044", "F-0045", "F-0046", "F-0047"]
ADD_CONSUMES = ["F-0041", "F-0044", "F-0045", "F-0046"]


def main() -> int:
    facts = {}
    for line in open(FACTS, encoding="utf-8"):
        line = line.strip()
        if line:
            o = json.loads(line)
            facts[o["id"]] = o

    # 1) strategy.json evidence_index
    st = json.load(open(STRATEGY, encoding="utf-8"))
    idx = st.get("evidence_index") or []
    have = {e.get("id") for e in idx}
    n_add = 0
    for fid in ADD_INDEX:
        if fid in have:
            print(f"  = evidence_index 已含 {fid}")
            continue
        f = facts.get(fid)
        if f is None:
            print(f"  ! FACTS 缺 {fid}，跳过")
            continue
        idx.append({
            "id": f["id"],
            "claim": f["claim"],
            "status": f.get("status"),
            "confidence": f.get("confidence"),
        })
        n_add += 1
        print(f"  + evidence_index 补 {fid}")
    if n_add:
        st["evidence_index"] = idx
        json.dump(st, open(STRATEGY, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        open(STRATEGY, "a", encoding="utf-8").write("\n")
        print(f"[write] strategy.json（evidence_index +{n_add}，"
              f"共 {len(idx)} 条；记得跑 rehash --strategy）")

    # 2) versions.json STRATEGY_GUIDE.md consumes
    v = json.load(open(VERSIONS, encoding="utf-8"))
    for e in v["entries"]:
        if e["path"] != GUIDE_PATH:
            continue
        cur = e.get("consumes") or []
        miss = [x for x in ADD_CONSUMES if x not in cur]
        if not miss:
            print("  = consumes 已齐")
            continue
        e["consumes"] = sorted(set(cur) | set(ADD_CONSUMES))
        e["updated_at"] = "2026-10-12"
        print(f"  + consumes 补 {miss}（共 {len(e['consumes'])} 项）")
        json.dump(v, open(VERSIONS, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        open(VERSIONS, "a", encoding="utf-8").write("\n")
        print("[write] versions.json")
        break
    else:
        print("  ! 未找到 STRATEGY_GUIDE.md 登记条目")
    return 0


if __name__ == "__main__":
    sys.exit(main())
