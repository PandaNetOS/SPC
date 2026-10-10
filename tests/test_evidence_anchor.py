# -*- coding: utf-8 -*-
"""证据锚定测试 —— 无需 pytest，直接 `python tests/test_evidence_anchor.py`

## 为什么单独一个文件

锚定守的不是"算得对不对"，是"**结论还能不能被担保**"。
它介于结论台账与策略之间，和 claim_type（靠什么立住）是相邻但不同的一层。

## 本文件特别要守住的三条

1. **漂移真的会被检出** —— 改了 source 内容而结论没动，必须报错。
   一个从不触发的漂移检查等于没有检查
2. **该敏感的要敏感，该迟钝的要迟钝** —— 改 `effect` / `caveats` / `status`
   必须改哈希（这些是证据实质）；改 `tags` / `updated_at` **不许**改哈希
   （否则无关编辑会训练人忽略报警 —— 会误报的检查比没有检查更坏）
3. **重基线是机械化的** —— `cli rehash` 必须能算出与校验一致的值，
   不允许手填哈希（手填就又变成无人担保的断言）
"""
from __future__ import annotations

import copy
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from smartpickcore.evidence import (  # noqa: E402
    ANCHOR_FIELDS,
    evidence_digest,
    fact_anchor,
    load_facts,
    sha256_file,
    sha256_text,
)
from smartpickcore.validate import (  # noqa: E402
    ValidationReport,
    check_source_anchor,
    validate_facts,
)

_PASS = 0
_FAIL = 0
_FAILURES: list[str] = []


def check(cond: bool, label: str) -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  ✓ {label}")
    else:
        _FAIL += 1
        _FAILURES.append(label)
        print(f"  ✗ {label}")


def section(t: str) -> None:
    print(f"\n{'=' * 72}\n{t}\n{'=' * 72}")


FACTS = load_facts(_ROOT)
BY_ID = {f["id"]: f for f in FACTS}
STRATEGY_PATH = os.path.join(_ROOT, "games", "dlt", "strategy", "strategy.json")
STRATEGY = json.load(open(STRATEGY_PATH, encoding="utf-8"))


def _anchor_errs(ft: dict, root: str | None = None) -> list[str]:
    rep = ValidationReport()
    check_source_anchor(
        ft, ft.get("id", "?"), ft.get("source"), ft.get("evidence") or {},
        root or _ROOT, rep,
    )
    return rep.errors


def _anchor_warns(ft: dict) -> list[str]:
    rep = ValidationReport()
    check_source_anchor(
        ft, ft.get("id", "?"), ft.get("source"), ft.get("evidence") or {},
        _ROOT, rep,
    )
    return rep.warnings


# ================================================================ 1. 哈希基元

def test_primitives() -> None:
    section("1. 哈希基元")

    check(sha256_text("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          "sha256_text('') 等于已知的 SHA256 空串值")

    p = os.path.join(_ROOT, "games", "dlt", "game.yaml")
    a, b = sha256_file(p), sha256_file(p)
    check(a == b, "sha256_file 对同一文件两次调用结果一致")
    check(len(a) == 64 and all(c in "0123456789abcdef" for c in a),
          "输出是 64 位小写十六进制")


# ================================================================ 2. 规范视图

def test_fact_anchor() -> None:
    section("2. 规范视图：只包含与证据强度有关的字段")

    ft = BY_ID["F-0003"]
    anchor = fact_anchor(ft)
    check(set(anchor) == set(ANCHOR_FIELDS),
          f"fact_anchor 恰好取 {len(ANCHOR_FIELDS)} 个锚定字段")

    check("updated_at" not in anchor and "tags" not in anchor,
          "规范视图不含 updated_at / tags（与证据强度无关）")

    # 该迟钝的：无关字段变了，摘要不许变
    noisy = copy.deepcopy(ft)
    noisy["tags"] = ["x", "y", "z"]
    noisy["updated_at"] = "2099-01-01"
    noisy["created_at"] = "1999-01-01"
    check(evidence_digest([ft]) == evidence_digest([noisy]),
          "改 tags / updated_at / created_at → 摘要**不变**（不许误报）")

    # 该敏感的：实质字段变了，摘要必须变
    for field, mutate in (
        ("claim", lambda d: d.__setitem__("claim", d["claim"] + "（改）")),
        ("status", lambda d: d.__setitem__("status", "tentative")),
        ("confidence", lambda d: d.__setitem__("confidence", 2)),
        ("claim_type", lambda d: d.__setitem__("claim_type", "analytic")),
    ):
        v = copy.deepcopy(ft)
        mutate(v)
        check(evidence_digest([ft]) != evidence_digest([v]),
              f"改 {field} → 摘要必须变")

    v = copy.deepcopy(ft)
    v["evidence"]["effect"]["prize1_ratio"] = 9.999
    check(evidence_digest([ft]) != evidence_digest([v]),
          "改 evidence.effect 里的数字 → 摘要必须变")

    v = copy.deepcopy(ft)
    v["caveats"] = list(v["caveats"]) + ["新增一条减损项"]
    check(evidence_digest([ft]) != evidence_digest([v]),
          "新增 caveat → 摘要必须变（适用条件变了）")

    # 顺序无关
    check(
        evidence_digest([BY_ID["F-0001"], BY_ID["F-0003"]])
        == evidence_digest([BY_ID["F-0003"], BY_ID["F-0001"]]),
        "摘要与传入顺序无关",
    )


# ================================================================ 3. 18 条已锚定

def test_real_facts_anchored() -> None:
    section("3. 18 条真实结论：source 均已锚定且实算一致")

    check(len(FACTS) == 18, f"FACTS.jsonl 共 {len(FACTS)} 条")

    unanchored = [
        f["id"] for f in FACTS
        if not (f.get("evidence") or {}).get("source_sha256")
    ]
    check(not unanchored, f"全部已锚定 source_sha256（未锚定：{unanchored or '无'}）")

    drift = [f["id"] for f in FACTS if _anchor_errs(f)]
    check(not drift, f"全部实算一致（漂移：{drift or '无'}）")

    rep = validate_facts(_ROOT)
    check(rep.passed, "validate_facts() 整体通过")


# ================================================================ 4. 漂移真的会拦

def test_drift_detected() -> None:
    section("4. 漂移检测：content 变了没重基线 → 必须报错")

    base = copy.deepcopy(BY_ID["F-0006"])   # source 是 changepoint_scan.py
    check(bool((base.get("evidence") or {}).get("source_sha256")),
          "F-0006 已锚定（用作变异基线）")

    # 4a. 锚定值被改成别的合法哈希
    wrong = copy.deepcopy(base)
    wrong["evidence"]["source_sha256"] = "0" * 64
    errs = _anchor_errs(wrong)
    check(bool(errs), "锚定值与实算不符 → 报错")
    check(any("证据文件已变更" in e for e in errs),
          "错误信息明确指出『证据文件已变更 —— 结论可能失效』")
    check(any("rehash" in e for e in errs),
          "错误信息给出重基线命令（不是只报错不给出路）")

    # 4b. 真的把文件改了（写到临时副本，用临时 root 比对）
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        src_rel = base["source"]
        src_abs = os.path.join(_ROOT, src_rel)
        content = open(src_abs, encoding="utf-8").read()
        fake_root = os.path.join(td, "repo")
        dst = os.path.join(fake_root, src_rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8").write(content + "\n# 被人改了一行\n")
        check(bool(_anchor_errs(base, fake_root)),
              f"source 内容真的被改 → 报错（{src_rel}）")

    # 4c. 未锚定只给 warning，不报错（避免一次性把 18 条全打红）
    nohash = copy.deepcopy(base)
    nohash["evidence"]["source_sha256"] = None
    check(not _anchor_errs(nohash), "未锚定不报错（只警告，避免误报风暴）")
    check(bool(_anchor_warns(nohash)), "未锚定给 warning（明确提示无法检出）")


# ================================================================ 5. 策略侧摘要

def test_strategy_digest() -> None:
    section("5. 策略侧：provenance.evidence_hash 锚定")

    prov = STRATEGY.get("provenance") or {}
    declared = prov.get("evidence_hash")
    check(declared is not None, "strategy.json 的 evidence_hash 已实算（不再是 null）")

    used: set[str] = set()
    for r in STRATEGY.get("rules", []):
        used.update(r.get("evidence_refs") or [])
    for a in STRATEGY.get("avoid_list", []):
        used.update(a.get("refuted_by") or [])
    check(bool(used), f"策略引用了 {len(used)} 条结论")

    got = evidence_digest(FACTS, sorted(used))
    check(got == declared, f"实算摘要 == 锚定值（{declared[:16]}…）")

    # 被引结论被推翻 → 摘要必须变 → 策略与证据脱节可被检出
    poisoned = []
    for f in FACTS:
        g = copy.deepcopy(f)
        if g["id"] == sorted(used)[0]:
            g["status"] = "refuted"
        poisoned.append(g)
    check(evidence_digest(poisoned, sorted(used)) != declared,
          f"被引结论 {sorted(used)[0]} 被推翻 → 摘要变化（策略侧能检出）")


# ================================================================ 6. 重基线通道

def test_rehash_consistent() -> None:
    section("6. 重基线：cli rehash 算出的值必须与校验一致")

    # 直接用库函数复算，确认"校验看到的值"和"重基线写入的值"同源
    for fid in ("F-0001", "F-0013", "F-0018"):
        ft = BY_ID[fid]
        src_abs = os.path.join(_ROOT, ft["source"])
        recomputed = sha256_file(src_abs)
        check(recomputed == ft["evidence"]["source_sha256"],
              f"{fid}: 实算值 == 已锚定值（重基线是幂等的）")

    # 重基线后再校验，必须干净
    rep = validate_facts(_ROOT)
    check(rep.passed, "重基线后 validate_facts() 仍全绿（无自造漂移）")


def main() -> int:
    test_primitives()
    test_fact_anchor()
    test_real_facts_anchored()
    test_drift_detected()
    test_strategy_digest()
    test_rehash_consistent()

    print("\n" + "=" * 72)
    print("结果")
    print("=" * 72)
    print(f"通过 {_PASS}  失败 {_FAIL}")
    if _FAILURES:
        print("\n失败项：")
        for f in _FAILURES:
            print(f"  ✗ {f}")
        return 1
    print("\n✅ 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
