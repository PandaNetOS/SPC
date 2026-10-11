# -*- coding: utf-8 -*-
"""结论证据类型（claim_type）测试 —— 无需 pytest，直接 `python tests/test_claim_type.py`

## 为什么单独一个文件

`claim_type` 守的不是计算，是**结论的可信边界**。它和单注/跨注不是一层东西，
和红线也不是一层东西（红线管"能不能说"，claim_type 管"这个数字靠什么立住"）。

## 本文件特别要守住的三条

1. **35 条真实结论全部有 claim_type 且合规** —— 回填不是贴标签，每条都要站得住
2. **五种类型的约束真的会拦** —— 一个从不触发的检查等于没有检查。
   每条约束都要用"变异后的真实结论"证明它会报错
3. **schema 与 Python 双通道一致** —— schema 是结构性拒收的第一道，
   Python 侧是 jsonschema 缺失时的兜底（红线字段就是这么写的）。
   两边必须判同一件事，否则会出现"schema 过了但 validate 报错"的分裂

## 分类判据（不是"用了什么方法"，是"它会在什么情况下变错"）

| claim_type | 失效方式 | 因此必须强制 |
|---|---|---|
| `analytic` | 只有模型定义错了才会错 | 不含 p_value / ci95（解析量没有抽样误差） |
| `empirical` | 数据换了、时段移位就会错 | 声明 data_version + n_observations |
| `simulation` | 模型假设变了就会错 | effect 含 n_sim 或 rng_seed 可复现；caveats ≥ 2 写清假设 |
| `documentary` | 官方规则文本变了就会错 | 声明 rules_epoch |
| `methodological` | 关于方法本身的判断 | caveats 非空（价值全在失效边界） |
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

from spc.validate import (  # noqa: E402
    CLAIM_TYPES,
    ValidationReport,
    check_claim_type,
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


FACTS_PATH = os.path.join(_ROOT, "memory", "facts", "FACTS.jsonl")
FACTS = [json.loads(l) for l in open(FACTS_PATH, encoding="utf-8") if l.strip()]
BY_ID = {f["id"]: f for f in FACTS}

try:
    import jsonschema

    SCHEMA = json.load(
        open(os.path.join(_ROOT, "spec", "fact.schema.json"), encoding="utf-8")
    )
    HAS_JSONSCHEMA = True
except ImportError:  # pragma: no cover
    jsonschema = None  # type: ignore[assignment]
    SCHEMA = None
    HAS_JSONSCHEMA = False


def _errs_of(ft: dict) -> list[str]:
    """跑 Python 侧检查，返回错误列表。"""
    rep = ValidationReport()
    check_claim_type(ft, ft.get("id", "?"), rep)
    return rep.errors


def _schema_ok(ft: dict) -> bool:
    """跑 schema 侧检查，返回是否通过。"""
    if not HAS_JSONSCHEMA:
        return True
    try:
        jsonschema.validate(ft, SCHEMA)
        return True
    except jsonschema.ValidationError:
        return False


# ================================================================ 1. 枚举与回填

def test_enum_and_backfill() -> None:
    section("1. 35 条结论的 claim_type 回填")

    check(len(FACTS) == 35, f"FACTS.jsonl 共 {len(FACTS)} 条（本文件按 35 条编写）")

    missing = [f["id"] for f in FACTS if not f.get("claim_type")]
    check(not missing, f"每条结论都有 claim_type（缺失：{missing or '无'}）")

    bad = [f["id"] for f in FACTS if f.get("claim_type") not in CLAIM_TYPES]
    check(not bad, f"claim_type 全部落在枚举内（越界：{bad or '无'}）")

    for ct, why in CLAIM_TYPES.items():
        check(ct in {"analytic", "empirical", "simulation", "documentary",
                     "methodological"},
              f"枚举成员 {ct} —— {why}")

    # 五类都要有人用，否则某个分支永远走不到（等于死约束）
    used = {f["claim_type"] for f in FACTS}
    check(
        used == set(CLAIM_TYPES),
        f"五类均被真实结论使用（实际用到：{sorted(used)}）",
    )


# ================================================================ 2. 真实结论全绿

def test_real_facts_pass() -> None:
    section("2. 35 条真实结论：schema 与 Python 双通道都通过")

    if not HAS_JSONSCHEMA:
        print("  （jsonschema 未安装，跳过 schema 通道）")

    bad_py = {f["id"]: _errs_of(f) for f in FACTS if _errs_of(f)}
    check(not bad_py, f"Python 侧：35 条全部合规（违规：{list(bad_py) or '无'}）")

    if HAS_JSONSCHEMA:
        bad_sc = [f["id"] for f in FACTS if not _schema_ok(f)]
        check(not bad_sc, f"schema 侧：35 条全部合规（违规：{bad_sc or '无'}）")

    rep = validate_facts(_ROOT)
    check(rep.passed, "validate_facts() 整体通过")
    check(
        any("证据类型分布" in c for c in rep.checked),
        "校验报告里给出了证据类型分布（不是只查不报）",
    )


# ================================================================ 3. 缺失 / 非法

def test_missing_and_invalid() -> None:
    section("3. 缺失与非法 claim_type 必须报错")

    base = copy.deepcopy(BY_ID["F-0003"])

    no_ct = copy.deepcopy(base)
    del no_ct["claim_type"]
    check(bool(_errs_of(no_ct)), "缺 claim_type → 报错（不给默认值，缺就是缺）")
    if HAS_JSONSCHEMA:
        check(not _schema_ok(no_ct), "缺 claim_type → schema 拒收")

    wrong = copy.deepcopy(base)
    wrong["claim_type"] = "empirical-ish"
    check(bool(_errs_of(wrong)), "claim_type 不在枚举内 → 报错")
    if HAS_JSONSCHEMA:
        check(not _schema_ok(wrong), "claim_type 不在枚举内 → schema 拒收")

    # 故意保留一个危险的默认值：宁可报错，也不要"看起来通过了"
    check(
        "claim_type" in json.load(
            open(os.path.join(_ROOT, "spec", "fact.schema.json"), encoding="utf-8")
        )["required"],
        "schema 把 claim_type 列为必填（不给会骗人的默认值）",
    )


# ================================================================ 4. 五类约束真的会拦

def test_analytic() -> None:
    section("4a. analytic —— 解析结论不含抽样不确定性")

    base = copy.deepcopy(BY_ID["F-0001"])
    check(base["claim_type"] == "analytic", "F-0001 是 analytic（组合学恒等式）")

    for key, val in (("p_value", 0.03), ("ci95", [1.0, 2.0])):
        v = copy.deepcopy(base)
        v["evidence"][key] = val
        check(bool(_errs_of(v)), f"analytic 却带 evidence.{key} → 报错")
        if HAS_JSONSCHEMA:
            check(not _schema_ok(v), f"analytic 却带 evidence.{key} → schema 拒收")


def test_empirical() -> None:
    section("4b. empirical —— 必须声明数据与样本量")

    base = copy.deepcopy(BY_ID["F-0003"])
    check(base["claim_type"] == "empirical", "F-0003 是 empirical（观测 + Bootstrap）")

    no_dv = copy.deepcopy(base)
    no_dv["evidence"]["data_version"] = None
    check(bool(_errs_of(no_dv)), "empirical 未声明 data_version → 报错")
    if HAS_JSONSCHEMA:
        check(not _schema_ok(no_dv), "empirical 未声明 data_version → schema 拒收")

    no_n = copy.deepcopy(base)
    no_n["evidence"]["n_observations"] = None
    check(bool(_errs_of(no_n)), "empirical 未声明 n_observations → 报错")
    if HAS_JSONSCHEMA:
        check(not _schema_ok(no_n), "empirical 未声明 n_observations → schema 拒收")


def test_simulation() -> None:
    section("4c. simulation —— 必须可复现且写清假设")

    base = copy.deepcopy(BY_ID["F-0017"])
    check(base["claim_type"] == "simulation", "F-0017 是 simulation（条件份额模拟）")

    no_repro = copy.deepcopy(base)
    no_repro["evidence"]["effect"].pop("n_sim", None)
    no_repro["evidence"]["effect"].pop("rng_seed", None)
    check(bool(_errs_of(no_repro)), "simulation 既无 n_sim 也无 rng_seed → 报错")
    if HAS_JSONSCHEMA:
        check(not _schema_ok(no_repro), "simulation 不可复现 → schema 拒收")

    one_caveat = copy.deepcopy(base)
    one_caveat["caveats"] = ["只有一条"]
    check(bool(_errs_of(one_caveat)), "simulation 的 caveats 少于 2 条 → 报错")
    if HAS_JSONSCHEMA:
        check(not _schema_ok(one_caveat), "simulation 假设未写清 → schema 拒收")


def test_documentary() -> None:
    section("4d. documentary —— 必须声明 rules_epoch")

    base = copy.deepcopy(BY_ID["F-0014"])
    check(base["claim_type"] == "documentary", "F-0014 是 documentary（规则沿革核对）")

    no_epoch = copy.deepcopy(base)
    no_epoch["evidence"]["rules_epoch"] = None
    check(bool(_errs_of(no_epoch)), "documentary 未声明 rules_epoch → 报错")
    if HAS_JSONSCHEMA:
        check(not _schema_ok(no_epoch), "documentary 脱离 epoch → schema 拒收")

    # F-0016 也是数据实扫，不强挂 documentary —— 分类看失效方式而非方法名
    check(
        BY_ID["F-0016"]["claim_type"] == "empirical",
        "F-0016 虽与规则有关，但决定性数字来自 102 期实扫 → 归 empirical",
    )


def test_methodological() -> None:
    section("4e. methodological —— 必须有减损项")

    base = copy.deepcopy(BY_ID["F-0018"])
    check(base["claim_type"] == "methodological", "F-0018 是 methodological（估计量对照）")

    empty_cav = copy.deepcopy(base)
    empty_cav["caveats"] = []
    check(bool(_errs_of(empty_cav)), "methodological 的 caveats 为空 → 报错")
    if HAS_JSONSCHEMA:
        check(not _schema_ok(empty_cav), "methodological 无失效边界 → schema 拒收")


# ================================================================ 5. 分类判据自洽

def test_classification_rationale() -> None:
    section("5. 分类判据自洽：同一条结论不该同时符合两类")

    # F-0004（121%，未计封顶）与 F-0017（41.4%，计入封顶）是同一模型的两个口径。
    # 它们的差距正来自"模型假设"，因此都必须是 simulation ——
    # 若一条归 empirical，就暗示"换个数据集就能解决"，那是误导。
    check(
        BY_ID["F-0004"]["claim_type"] == BY_ID["F-0017"]["claim_type"] == "simulation",
        "F-0004 / F-0017 同为 simulation（121% vs 41.4% 的差距源于假设，不是数据）",
    )

    # F-0015 被 F-0016 取代，两条性质相同，分类必须一致 ——
    # 否则"取代链"上会出现同案不同判。
    check(
        BY_ID["F-0015"]["claim_type"] == BY_ID["F-0016"]["claim_type"],
        "F-0015 / F-0016 分类一致（取代链上同案同判）",
    )

    # 两条红线结论：F-0001 是数学恒等式（analytic），F-0002 的返奖率来自规则。
    # 二者都"恒为真"，但失效方式不同 —— 这正是 claim_type 存在的理由。
    check(
        BY_ID["F-0001"]["claim_type"] == "analytic"
        and BY_ID["F-0002"]["claim_type"] == "documentary",
        "F-0001 与 F-0002 同为『恒真』但分类不同（定义 vs 规则文本）",
    )


def main() -> int:
    test_enum_and_backfill()
    test_real_facts_pass()
    test_missing_and_invalid()
    test_analytic()
    test_empirical()
    test_simulation()
    test_documentary()
    test_methodological()
    test_classification_rationale()

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
