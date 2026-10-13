# -*- coding: utf-8 -*-
"""跨注层（L3 / scope: cross）测试 —— 无需 pytest，直接 `python tests/test_cross_scope.py`

## 为什么单独一个文件

`test_core.py` 覆盖 L1/L2（单注层）。跨注层是**另一个作用域**：
输入是一组注而非一注，求值入口与判定入口都不同。
混在一起会让"哪个作用域没过"变模糊。

## 本文件特别要守住的三条

1. **跨注原语是纯数学** —— 不含任何彩种常量，换彩种直接可用
2. **作用域不可混用** —— 单注原语用在 cross 特征上必须报错（反之亦然）
3. **跨注规则真的能执行** —— 不是"声明了 cross"就算数，
   `judge_cross()` 必须能在实际数据上跑出判定结果
   （1.0 时代的 R-002 就死在这一条上）
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "platform"))  # framework→platform（2026-10-12）

import yaml  # noqa: E402

from core import (  # noqa: E402
    Portfolio,
    PortfolioError,
    Ticket,
    classify_rules,
    evaluate_cross,
    evaluate_cross_one,
    evaluate_one,
    evaluable_cross_features,
    judge_cross,
    sample_batch,
    validate_feature_declarations,
)
from core.features import (  # noqa: E402
    PrimitiveError,
    apply_cross_primitive,
    list_primitives,
)
from core.game_util import cross_feature_keys, single_feature_keys  # noqa: E402
from core.judge import PredicateError  # noqa: E402

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


def check_raises(fn, exc, label: str) -> None:
    global _PASS, _FAIL
    try:
        fn()
    except exc:
        _PASS += 1
        print(f"  ✓ {label}（正确抛出 {exc.__name__}）")
    except Exception as e:  # noqa: BLE001
        _FAIL += 1
        _FAILURES.append(label)
        print(f"  ✗ {label}（抛了 {type(e).__name__} 而非 {exc.__name__}: {e}）")
    else:
        _FAIL += 1
        _FAILURES.append(label)
        print(f"  ✗ {label}（竟然没抛错）")


def section(t: str) -> None:
    print(f"\n{'=' * 72}\n{t}\n{'=' * 72}")


CFG = yaml.safe_load(open(os.path.join(_ROOT, "labs/lottery/studies/dlt/game.yaml"), encoding="utf-8"))
ST = json.load(open(os.path.join(_ROOT, "labs/lottery/studies/dlt/strategy/strategy.json"), encoding="utf-8"))


# ================================================================ 1. 跨注原语（纯数学）

def test_primitives() -> None:
    section("1. 跨注原语：纯数学，不依赖任何彩种参数")

    # 三注：前两注结构相同（间隔都是 2），第三注不同
    groups = [[1, 3, 5], [2, 4, 6], [10, 20, 30]]

    n = apply_cross_primitive("duplicate_structure_count", groups)
    check(n == 2, f"duplicate_structure_count = {n}（前两注同构 → 2）")

    d = apply_cross_primitive("distinct_structure_count", groups)
    check(d == 2, f"distinct_structure_count = {d}（两种结构）")

    cov = apply_cross_primitive("coverage_unique_count", groups)
    check(cov == 9, f"coverage_unique_count = {cov}（9 个不同号码）")

    shared = apply_cross_primitive("max_shared_count", groups)
    check(shared == 0, f"max_shared_count = {shared}（无重叠号码）")

    hit = apply_cross_primitive("duplicate_structure_count_ge", groups, {"threshold": 1})
    check(hit is True, f"duplicate_structure_count_ge(threshold=1) = {hit}")

    hit3 = apply_cross_primitive("duplicate_structure_count_ge", groups, {"threshold": 3})
    check(hit3 is False, f"duplicate_structure_count_ge(threshold=3) = {hit3}")

    # 全同构
    same = [[1, 3, 5], [2, 4, 6], [7, 9, 11]]
    check(apply_cross_primitive("distinct_structure_count", same) == 1,
          "全同构：distinct_structure_count = 1")
    check(apply_cross_primitive("duplicate_structure_count", same) == 3,
          "全同构：duplicate_structure_count = 3")

    # 全异
    diff = [[1, 3, 5], [2, 10, 30], [4, 15, 16]]
    check(apply_cross_primitive("duplicate_structure_count", diff) == 0,
          "全异：duplicate_structure_count = 0")

    # 结构签名用间隔向量而非号码本身 —— 号码不同但结构相同必须能判出同构
    check(apply_cross_primitive("distinct_structure_count",
                                [[1, 3, 5], [30, 32, 34]]) == 1,
          "号码不同但间隔向量相同 → 判为同构（(1,3,5) 与 (30,32,34)）")

    # 空组 / 脏输入必须报错，不静默给 0
    check_raises(lambda: apply_cross_primitive("duplicate_structure_count", []),
                 PrimitiveError, "空组报错（不静默返回 0）")
    check_raises(lambda: apply_cross_primitive("duplicate_structure_count", [[1, 1]]),
                 PrimitiveError, "含重复元素的组报错")

    # 单注原语不得被当作跨注原语使用（反之亦然）
    check_raises(lambda: apply_cross_primitive("sum", groups),
                 PrimitiveError, "单注原语 sum 走跨注入口 → 报错")
    check_raises(lambda: apply_cross_primitive("nonexistent", groups),
                 PrimitiveError, "未知跨注原语 → 报错")


# ================================================================ 2. Portfolio

def test_portfolio() -> None:
    section("2. Portfolio：一组注的一等公民")

    t1 = Ticket({"front": (1, 3, 5, 7, 9), "back": (1, 2)})
    t2 = Ticket({"front": (2, 4, 6, 8, 10), "back": (3, 4)})
    pf = Portfolio([t1, t2])

    check(len(pf) == 2, f"长度 = {len(pf)}")
    check(pf[0] == t1, "索引访问返回原 Ticket")
    check(list(pf.zone_values("front")) == [[1, 3, 5, 7, 9], [2, 4, 6, 8, 10]],
          "zone_values('front') 返回每注的前区号码")

    check_raises(lambda: Portfolio([]), PortfolioError, "空 Portfolio 报错")
    check_raises(lambda: Portfolio(t1), PortfolioError,
                 "把单注当 Portfolio 构造 → 报错（须包一层）")

    # 不合法号码必须被校验出来
    bad = Portfolio([t1, Ticket({"front": (1, 2, 3, 4, 99), "back": (1, 2)})])
    errs = bad.validate(CFG)
    check(len(errs) > 0, f"越界号码被校验出（{len(errs)} 条错误）")

    # 区名不一致
    weird = Portfolio([t1, Ticket({"front": (1, 2, 3, 4, 5)})])
    check(any("区名集合" in e for e in weird.validate(CFG)),
          "区名集合与配置不一致被检出")

    # 可哈希 / 可比较
    check(hash(Portfolio([t1, t2])) == hash(pf), "同内容 Portfolio 哈希相同")
    check(Portfolio([t1, t2]) == pf, "同内容 Portfolio 相等")

    # 追加返回新对象，不改自身
    pf2 = pf.append(Ticket({"front": (11, 13, 15, 17, 19), "back": (5, 6)}))
    check(len(pf) == 2 and len(pf2) == 3, "append 返回新 Portfolio，原对象不变")


# ================================================================ 3. 跨注求值

def test_evaluate_cross() -> None:
    section("3. evaluate_cross：按声明求值跨注特征")

    keys = evaluable_cross_features(CFG)
    check(len(keys) == 5, f"可执行跨注特征 {len(keys)} 个：{keys}")

    # 两注同构 + 一注不同
    pf = Portfolio([
        Ticket({"front": (1, 3, 5, 7, 9), "back": (1, 2)}),
        Ticket({"front": (2, 4, 6, 8, 10), "back": (3, 4)}),
        Ticket({"front": (1, 10, 20, 30, 35), "back": (5, 6)}),
    ])
    feats = evaluate_cross(CFG, pf)
    check(feats["duplicated_structure_across_tickets"] == 2,
          f"duplicated_structure_across_tickets = "
          f"{feats['duplicated_structure_across_tickets']}（前两注同构）")
    check(feats["has_duplicated_structure"] is True,
          "has_duplicated_structure = True")
    check(feats["distinct_structure_count"] == 2,
          f"distinct_structure_count = {feats['distinct_structure_count']}")

    # 全异结构
    pf_diff = Portfolio([
        Ticket({"front": (1, 3, 5, 7, 9), "back": (1, 2)}),
        Ticket({"front": (2, 10, 18, 26, 34), "back": (3, 4)}),
        Ticket({"front": (4, 12, 19, 27, 33), "back": (5, 6)}),
    ])
    f2 = evaluate_cross(CFG, pf_diff)
    check(f2["has_duplicated_structure"] is False,
          "全异组：has_duplicated_structure = False")

    # ★ 作用域边界：单注入口不得求值跨注特征（反之亦然）
    check_raises(
        lambda: evaluate_one(CFG, pf[0], "has_duplicated_structure"),
        Exception,
        "evaluate_one() 求跨注特征 → 报错（不是静默给假值）",
    )
    check_raises(
        lambda: evaluate_cross_one(CFG, pf, "has_run_ge2"),
        PortfolioError,
        "evaluate_cross_one() 求单注特征 → 报错",
    )


# ================================================================ 4. 作用域不可混用

def test_scope_mixing_rejected() -> None:
    section("4. 结构性拒收：scope 与原语作用域必须一致")

    import copy

    # ① 跨注原语用在 single 特征上
    cfg1 = copy.deepcopy(CFG)
    cfg1["features"].append({
        "key": "bad_cross_on_single",
        "label": "错误示范",
        "type": "integer",
        "primitive": "duplicate_structure_count",
        "args": {"zone": "front"},
        "formula": "x",
    })
    errs = validate_feature_declarations(cfg1)
    check(any("bad_cross_on_single" in e and "single" in e for e in errs),
          f"跨注原语用在 scope=single → 报错（{len(errs)} 条）")

    # ② 单注原语用在 cross 特征上
    cfg2 = copy.deepcopy(CFG)
    cfg2["features"].append({
        "key": "bad_single_on_cross",
        "label": "错误示范",
        "type": "integer",
        "scope": "cross",
        "primitive": "sum",
        "args": {"zone": "front"},
        "formula": "x",
    })
    errs2 = validate_feature_declarations(cfg2)
    check(any("bad_single_on_cross" in e for e in errs2),
          f"单注原语用在 scope=cross → 报错（{len(errs2)} 条）")

    # ③ 非法 scope 值
    cfg3 = copy.deepcopy(CFG)
    cfg3["features"].append({
        "key": "bad_scope_value",
        "label": "错误示范",
        "type": "integer",
        "scope": "both",
        "primitive": "sum",
        "args": {"zone": "front"},
        "formula": "x",
    })
    errs3 = validate_feature_declarations(cfg3)
    check(any("scope=" in e for e in errs3), "非法 scope 值 → 报错")

    # ④ 正常配置应零错误（回归）
    check(not validate_feature_declarations(CFG),
          "现有 game.yaml 声明零错误")

    # ⑤ 注册表分层正确
    check(len(list_primitives("single")) == 28,
          f"单注原语 {len(list_primitives('single'))} 个（注册表实际数；r14.1 曾预期 22，后新增原语使总数升到 28）")
    check(len(list_primitives("cross")) == 7,
          f"跨注原语 {len(list_primitives('cross'))} 个（5 + duplicate_ticket_count/_ge）")
    check(not (set(single_feature_keys(CFG)) & set(cross_feature_keys(CFG))),
          "单注与跨注特征 key 无交集")


# ================================================================ 5. 跨注判定

def test_judge_cross() -> None:
    section("5. judge_cross：R-002 真的能被执行")

    r002 = [r for r in ST["rules"] if r["id"] == "R-002"]
    check(len(r002) == 1, "strategy.json 含 R-002")
    check(r002[0]["scope"] == "cross",
          f"R-002 的 scope = {r002[0]['scope']}（应为 cross）")

    # 完全相同号码组 → 命中 exclude（r06 语义重构：禁止完全重复，F-0027）
    pf_same = Portfolio([
        Ticket({"front": (1, 3, 5, 7, 9), "back": (1, 2)}),
        Ticket({"front": (1, 3, 5, 7, 9), "back": (1, 2)}),
    ])
    jr = judge_cross(CFG, pf_same, r002)
    check(jr.matched == ["R-002"], f"完全相同组命中 {jr.matched}")
    check(jr.excluded, "完全相同组被 exclude")

    # 结构同构（号码不同）→ 不命中（F-0028：同构无害，r06 已废除该惩罚）
    pf_iso = Portfolio([
        Ticket({"front": (1, 3, 5, 7, 9), "back": (1, 2)}),
        Ticket({"front": (2, 4, 6, 8, 10), "back": (3, 4)}),
    ])
    jr1 = judge_cross(CFG, pf_iso, r002)
    check(jr1.matched == [], f"结构同构组不命中（matched={jr1.matched}）")
    check(not jr1.excluded, "结构同构组放行")

    # 完全不同的组 → 不命中
    pf_diff = Portfolio([
        Ticket({"front": (1, 3, 5, 7, 9), "back": (1, 2)}),
        Ticket({"front": (2, 10, 18, 26, 34), "back": (3, 4)}),
    ])
    jr2 = judge_cross(CFG, pf_diff, r002)
    check(jr2.matched == [], f"异构组不命中（matched={jr2.matched}）")
    check(not jr2.excluded, "异构组放行")

    # 单注层规则不得混进跨注判定
    r001 = [r for r in ST["rules"] if r["id"] == "R-001"]
    check_raises(lambda: judge_cross(CFG, pf_same, r001),
                 PredicateError,
                 "把单注规则喂给 judge_cross → 报错（引用完整性检查）")


# ================================================================ 6. 规则三分

def test_classify_rules() -> None:
    section("6. classify_rules：single / cross / undeclared 三分")

    scopes = classify_rules(CFG, ST["rules"])
    check([r["id"] for r in scopes.single] == ["R-001", "R-003", "R-004", "R-005"],
          f"single = {[r['id'] for r in scopes.single]}")
    check([r["id"] for r in scopes.cross] == ["R-002"],
          f"cross = {[r['id'] for r in scopes.cross]}")
    check(scopes.undeclared == [],
          f"undeclared = {[r.get('id') for r in scopes.undeclared]}（应为空）")

    # 拼错的规则必须落到 undeclared（而不是被当成跨注悄悄跳过）
    typo = [{"id": "X-1", "machine_rule": {
        "predicate": "has_run_typo == true", "action": "exclude"}}]
    sc2 = classify_rules(CFG, typo)
    check([r["id"] for r in sc2.undeclared] == ["X-1"],
          "引用未声明特征 → undeclared（配置缺陷，不是跨注）")


# ================================================================ 7. 端到端

def test_e2e() -> None:
    section("7. 端到端：生成 20 注，跨注规则在整组上被真正执行")

    res = sample_batch(CFG, ST["rules"], n=20, seed=20261011)
    check(len(res) == 20, f"生成 20 注（得到 {len(res)}）")

    st = res.stats
    check(st.get("cross_scope_pending") == ["R-002"],
          f"逐注过滤时 R-002 待整组评估：{st.get('cross_scope_pending')}")
    check(st.get("undeclared_skipped") == [],
          f"无未声明规则被跳过：{st.get('undeclared_skipped')}")

    ev = st.get("cross_scope_evaluated")
    check(ev is not None, "★ 跨注规则已在整组上下文执行（1.0 时代这里只会是『跳过』）")
    if ev:
        check(ev["rules"] == ["R-002"], f"执行的跨注规则：{ev['rules']}")
        check("has_identical_tickets" in ev["features"],
              f"求得跨注特征：{sorted(ev['features'])}")
        check(ev["weight"] == 1.0, f"跨注权重 = {ev['weight']}（exclude 不乘权重）")

    # 启发式标记：spread_penalty 必须被标明不是统计结论
    check(st.get("spread_penalty_is_heuristic") is True,
          "spread_penalty 被显式标记为启发式（不允许冒充统计结论）")


# ================================================================ 8. 铁律

def _strip_docs_and_comments(src: str) -> str:
    """去掉 docstring 与注释行，只留下**真正的代码**。

    为什么必须这么做：模块的 docstring 里会**举例**写 `{"front": ...}`、
    也会在铁律清单里写「禁止出现 "front"」—— 那些是文字，不是代码。
    不做剔除的话，扫描会误报，久而久之这类检查就会被人忽略 ——
    **会误报的检查比没有检查更坏**。
    """
    import ast

    tree = ast.parse(src)
    doc_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            if ast.get_docstring(node, clean=False) is None:
                continue
            first = node.body[0]
            doc_lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))

    out = []
    for i, line in enumerate(src.splitlines(), start=1):
        if i in doc_lines or line.strip().startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)


def test_no_game_constants() -> None:
    section("8. 铁律：跨注模块不含任何彩种常量")

    src = open(os.path.join(_ROOT, "platform", "core", "portfolio.py"),
               encoding="utf-8-sig").read()
    code = _strip_docs_and_comments(src)
    for bad in ("dlt", "front", "back", "大乐透"):
        check(bad not in code, f"portfolio.py 代码里不含 {bad!r}")

    # 跨注原语实现里不得出现号码池常量（35 / 12 / 5 / 2 这类来自配置的数）
    fsrc = open(os.path.join(_ROOT, "platform", "core", "features.py"),
               encoding="utf-8-sig").read()
    import ast

    tree = ast.parse(fsrc)
    bad_consts: list[int] = []
    for node in tree.body:
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith("_c_")):
            continue
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, int):
                if n.value not in (0, 1, 2):
                    bad_consts.append(n.value)
    check(not bad_consts,
          f"跨注原语只用到 0/1/2 三个字面量（发现可疑常量 {bad_consts}）")


def main() -> int:
    print("\n跨注层（scope: cross）测试")
    test_primitives()
    test_portfolio()
    test_evaluate_cross()
    test_scope_mixing_rejected()
    test_judge_cross()
    test_classify_rules()
    test_e2e()
    test_no_game_constants()

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
