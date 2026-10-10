# -*- coding: utf-8 -*-
"""影子彩种回归测试 —— 无需 pytest，直接 `python tests/test_shadow_game.py`

## 这个文件守的是什么

本仓库的**唯一硬标准**是：

> 加入第二个彩种，不得修改 `framework/` 或 `src/` 的任何一行代码。

这条标准此前**从未被验证过**（`memory/workbench/TODO.md` 的 T-031，P3）。
原因很现实：仓库里只有一个彩种（dlt），而"只有一个实例"恰恰是
最容易让通用性假象存活的状态 —— 只要你从没接过第二个，
`if game == "dlt"` 这种代码就永远不会被发现。

本文件补的就是这个缺口：造一个**处处不同**的第二个彩种（影子彩种 `shadow`），
让它走完全部真实路径，然后断言 `framework/` 与 `src/` 里没有它的痕迹。

## 为什么叫"影子"

它**不是**一个真实彩种，也不登记进 `games/`（`games/` 只放真实彩种）。
它是测试夹具，位于 `tests/fixtures/shadow/`，运行时被复制到一个临时仓库根的
`games/shadow/` 下，再走真实的 `load_game_config()` / `validate_game()`。

刻意做成与 dlt 处处不同，否则测不出硬编码：

| 维度 | dlt | shadow |
|---|---|---|
| 区名 | `front` / `back` | `red` / `blue` |
| 号码池 | 35 选 5 + 12 选 2 | 9 选 3 + 5 选 2 |
| 下界 | `min_value: 1` | 红区 `min_value: **0**` |
| T | 21,425,712 | 840 |
| epoch | 7 个（E0–E6） | 1 个（S1） |
| 特征 key | 11 + 3 | 5 + 2（与 dlt **零交集**） |

## 本文件的三段命题

1. **能跑通** —— 装载 / 校验 / 求值 / 判定 / 跨注 / 生成，全链路在影子彩种上可用
2. **没作弊** —— `framework/` 与 `src/` 的代码里没有 dlt 的区名、特征名、号码池常量
3. **真通用** —— 换个区数（单区变体）照样能跑，不靠"恰好两区"
"""
from __future__ import annotations

import ast
import copy
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "framework"))

import yaml  # noqa: E402

from core import (  # noqa: E402
    Portfolio,
    Ticket,
    classify_rules,
    evaluate,
    evaluate_cross,
    evaluate_one,
    judge,
    judge_cross,
    sample_batch,
    validate_feature_declarations,
)
from core.evaluate import EvaluateError  # noqa: E402
from core.features import list_primitives  # noqa: E402
from core.game_util import (  # noqa: E402
    cross_feature_keys,
    single_feature_keys,
    total_combinations,
    zone_keys,
)
from core.judge import PredicateError  # noqa: E402
from smartpickcore import validate as V  # noqa: E402
from smartpickcore.game import (  # noqa: E402
    compute_space,
    list_games,
    load_game_config,
)

_FIX = os.path.join(_HERE, "fixtures", "shadow")
_DLT_CFG = yaml.safe_load(
    open(os.path.join(_ROOT, "games/dlt/game.yaml"), encoding="utf-8")
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


# ---------------------------------------------------------------- 临时仓库根
#
# 影子彩种必须走 **真实的** `games/<id>/game.yaml` 路径，否则测的是"喂个 dict 给函数"
# 而不是"接入第二个彩种"。所以这里造一个临时仓库根，把夹具复制成 games/shadow/。
#
# validate_game() 会按 repo_root 拼 `spec/` 与 `framework/` 的路径，
# 因此这两个目录也要一并复制（省得它只能降级成 warning）。

def _make_repo_root() -> str:
    tmp = tempfile.mkdtemp(prefix="spc_shadow_")
    gdir = os.path.join(tmp, "games")
    os.makedirs(gdir)
    shutil.copytree(_FIX, os.path.join(gdir, "shadow"))
    shutil.copytree(
        os.path.join(_ROOT, "spec"), os.path.join(tmp, "spec"),
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(
        os.path.join(_ROOT, "framework"), os.path.join(tmp, "framework"),
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    # sha256 必须**实算**：夹具里填的是全 0，是为了避免 Git 换行符差异
    # 让夹具自带的哈希失效（那会造出一个与环境相关的假失败）。
    csv = os.path.join(gdir, "shadow", "data", "raw", "shadow.csv")
    digest = hashlib.sha256(open(csv, "rb").read()).hexdigest()
    ypath = os.path.join(gdir, "shadow", "game.yaml")
    cfg = yaml.safe_load(open(ypath, encoding="utf-8"))
    cfg["data"]["raw"]["sha256"] = digest
    with open(ypath, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
    return tmp


def _load_fixture() -> tuple[dict, list[dict]]:
    """直接读夹具（不走临时仓库根），供纯框架层测试用。"""
    cfg = yaml.safe_load(
        open(os.path.join(_FIX, "game.yaml"), encoding="utf-8")
    )
    st = json.load(
        open(os.path.join(_FIX, "strategy", "strategy.json"), encoding="utf-8")
    )
    return cfg, st["rules"]


CFG, RULES = _load_fixture()


# ================================================================ 1. 装载

def test_load() -> None:
    section("1. 装载：影子彩种走真实的 games/<id>/ 路径")

    tmp = _make_repo_root()
    try:
        cfg = load_game_config("shadow", repo_root=tmp)
        check(cfg["id"] == "shadow", f"装载成功，id={cfg['id']}")
        check(list_games(tmp) == ["shadow"],
              f"list_games(临时根) = {list_games(tmp)}（dlt 不在其中）")

        sp = compute_space(cfg)
        check(sp["total_combinations"] == 840,
              f"T = {sp['total_combinations']}（= C(9,3)×C(5,2) = 84×10，不是 dlt 的 21,425,712）")
        check(abs(sp["first_prize_probability"] - 1.0 / 840) < 1e-15,
              f"p1 = {sp['first_prize_probability']}（= 1/840）")
        check([z["key"] for z in sp["zones"]] == ["red", "blue"],
              f"区名 = {[z['key'] for z in sp['zones']]}（不是 front/back）")

        rep = V.validate_game("shadow", repo_root=tmp)
        check(not rep.errors,
              f"validate_game() 零错误（{len(rep.checked)} 项检查）"
              + ("" if not rep.errors else f"：{rep.errors[:3]}"))
        check(any("SHA256 一致" in c for c in rep.checked),
              "SHA256 一致性检查在影子彩种上同样生效（不是只认 dlt 的文件）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 目录名与 id 不一致 → 报错（这条规则也不能只对 dlt 生效）
    tmp2 = _make_repo_root()
    try:
        os.rename(os.path.join(tmp2, "games", "shadow"),
                  os.path.join(tmp2, "games", "renamed"))
        check_raises(lambda: load_game_config("shadow", repo_root=tmp2),
                     Exception, "games/ 下没有 shadow 目录 → 报错（而不是静默兜底）")
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)


# ================================================================ 2. 声明

def test_declarations() -> None:
    section("2. 声明：影子彩种的特征能被框架静态确认可执行")

    errs = validate_feature_declarations(CFG)
    check(not errs, f"features 声明零错误（{len(CFG['features'])} 个特征）"
          + ("" if not errs else f"：{errs[:3]}"))

    ks, kc = single_feature_keys(CFG), cross_feature_keys(CFG)
    check(len(ks) == 5, f"单注特征 {len(ks)} 个：{ks}")
    check(len(kc) == 2, f"跨注特征 {len(kc)} 个：{kc}")

    dlt_keys = {f["key"] for f in _DLT_CFG["features"]}
    check(not (set(ks) | set(kc)) & dlt_keys,
          "★ 影子彩种与 dlt 的特征 key **零交集**（框架不认识任何具体特征名）")
    check(not (set(zone_keys(CFG)) & set(zone_keys(_DLT_CFG))),
          f"区名零交集：{zone_keys(CFG)} vs {zone_keys(_DLT_CFG)}")
    check(total_combinations(CFG) != total_combinations(_DLT_CFG),
          f"T 不同：{total_combinations(CFG)} vs {total_combinations(_DLT_CFG)}")

    # 影子彩种用的原语**全部来自同一张注册表**，没有为它新增过任何原语
    used = {f["primitive"] for f in CFG["features"] if f.get("primitive")}
    allp = set(list_primitives())
    check(used <= allp,
          f"影子彩种用到的 {len(used)} 个原语全部来自既有注册表（未新增）")


# ================================================================ 3. 号码校验

def test_ticket() -> None:
    section("3. Ticket：号码的合法边界由配置决定，不是写死的")

    ok = Ticket({"red": (0, 4, 8), "blue": (1, 5)})
    check(ok.is_valid(CFG), f"{ok.render()} 合法")

    low = Ticket({"red": (0, 1, 2), "blue": (1, 5)})
    check(low.is_valid(CFG),
          "★ 红区含 0 合法 —— min_value=0 真的从配置读了（硬编码 1 会在这里暴露）")

    over = Ticket({"red": (0, 4, 9), "blue": (1, 5)})
    errs = over.validate(CFG)
    check(any("越界" in e for e in errs), f"红区 9 越界被拒（上界 = 0+9-1 = 8）：{errs}")

    under = Ticket({"red": (-1, 4, 8), "blue": (1, 5)})
    check(any("越界" in e for e in under.validate(CFG)), "红区 -1 越界被拒")

    miss = Ticket({"red": (0, 4, 8)})
    check(any("缺少区" in e for e in miss.validate(CFG)), "缺 blue 区被拒")

    extra = Ticket({"red": (0, 4, 8), "blue": (1, 5), "green": (1,)})
    check(any("多出未声明的区" in e for e in extra.validate(CFG)),
          "多出未声明区被拒")

    # ★ 拿 dlt 的区名去构造 —— 对影子彩种来说那是两个陌生区
    dlt_style = Ticket({"front": (1, 2, 3, 4, 5), "back": (1, 2)})
    e2 = dlt_style.validate(CFG)
    check(any("缺少区" in e for e in e2) and any("多出未声明的区" in e for e in e2),
          "★ 用 dlt 的 front/back 校验影子彩种 → 被拒（区名不是框架内置的）")

    check(not Ticket({"red": (0, 4, 8), "blue": (1, 5)}).validate(_DLT_CFG) == [],
          "反向：影子彩种的号码在 dlt 配置下也不合法（两侧互不相通）")


# ================================================================ 4. 求值

def test_evaluate() -> None:
    section("4. 求值：单注特征按影子彩种的声明机械算出")

    t = Ticket({"red": (0, 4, 8), "blue": (1, 5)})
    f = evaluate(CFG, t)
    check(f["red_sum"] == 12, f"red_sum = {f['red_sum']}（0+4+8）")
    check(f["red_span"] == 8, f"red_span = {f['red_span']}")
    check(f["red_odd"] == 0, f"red_odd = {f['red_odd']}（0/4/8 全偶）")
    check(f["has_pair"] is False, f"has_pair = {f['has_pair']}（间隔 4,4 无相邻对）")
    check(f["blue_sum"] == 6, f"blue_sum = {f['blue_sum']}（1+5）")
    check(set(f) == set(single_feature_keys(CFG)),
          f"结果恰好覆盖 {len(f)} 个单注特征，不多不少")
    check("has_dup_struct" not in f and "red_dup_struct" not in f,
          "★ 跨注特征不出现在单注求值结果里")

    t2 = Ticket({"red": (1, 2, 8), "blue": (2, 3)})
    f2 = evaluate(CFG, t2)
    check(f2["has_pair"] is True, f"{t2.render()} 的 has_pair = True（1,2 相邻）")
    check(f2["red_odd"] == 1, f"{t2.render()} 的 red_odd = {f2['red_odd']}")

    # dlt 的特征名在影子彩种上不存在 —— 必须是显式错误
    check_raises(lambda: evaluate_one(CFG, t, "has_run_ge2"),
                 EvaluateError, "求 dlt 的特征 has_run_ge2 → 报错（不是静默给 None）")
    check_raises(lambda: evaluate_one(CFG, t, "has_dup_struct"),
                 EvaluateError, "单注入口求跨注特征 → 报错")


# ================================================================ 5. 判定

def _rule(rid: str) -> list[dict]:
    return [r for r in RULES if r["id"] == rid]


def test_judge() -> None:
    section("5. 判定：单注规则在影子彩种上被真正执行")

    bad = Ticket({"red": (1, 2, 8), "blue": (2, 3)})     # 含相邻对
    good = Ticket({"red": (0, 4, 8), "blue": (1, 5)})    # 不含

    r = judge(CFG, bad, _rule("R-101"))
    check(r.excluded and r.matched == ["R-101"],
          f"{bad.render()} 被 R-101 排除（matched={r.matched}）")

    r2 = judge(CFG, good, _rule("R-101"))
    check(not r2.excluded and r2.matched == [],
          f"{good.render()} 通过 R-101")

    # require 分支
    r3 = judge(CFG, good, _rule("R-103"))                # red_odd = 0
    check(r3.required_failed, f"red_odd=0 触发 R-103 的 require 失败")
    r4 = judge(CFG, bad, _rule("R-103"))                 # red_odd = 1
    check(not r4.required_failed, "red_odd=1 满足 R-103")

    check_raises(
        lambda: judge(CFG, good, [{"id": "X-9", "machine_rule": {
            "predicate": "has_run_ge2 == true", "action": "exclude"}}]),
        PredicateError, "引用 dlt 特征 has_run_ge2 → PredicateError")


# ================================================================ 6. 跨注层

def test_cross() -> None:
    section("6. 跨注层：影子彩种的 R-102 同样能真的执行")

    # 两注红区间隔向量都是 (2,2) → 同构
    same = Portfolio([
        Ticket({"red": (0, 2, 4), "blue": (1, 2)}),
        Ticket({"red": (1, 3, 5), "blue": (3, 4)}),
    ])
    fs = evaluate_cross(CFG, same)
    check(fs["red_dup_struct"] == 2, f"red_dup_struct = {fs['red_dup_struct']}（两注同构）")
    check(fs["has_dup_struct"] is True, "has_dup_struct = True")

    jr = judge_cross(CFG, same, _rule("R-102"))
    check(jr.matched == ["R-102"] and abs(jr.weight - 0.5) < 1e-9,
          f"同构组命中 R-102，权重降到 {jr.weight}")

    diff = Portfolio([
        Ticket({"red": (0, 2, 4), "blue": (1, 2)}),
        Ticket({"red": (0, 3, 7), "blue": (3, 4)}),
    ])
    fd = evaluate_cross(CFG, diff)
    check(fd["red_dup_struct"] == 0, f"异构组 red_dup_struct = {fd['red_dup_struct']}")
    jr2 = judge_cross(CFG, diff, _rule("R-102"))
    check(jr2.matched == [] and abs(jr2.weight - 1.0) < 1e-9,
          f"异构组不命中，权重保持 {jr2.weight}")

    check_raises(lambda: judge_cross(CFG, same, _rule("R-101")),
                 PredicateError, "把单注规则喂给 judge_cross → 报错")

    sc = classify_rules(CFG, RULES)
    check([r["id"] for r in sc.single] == ["R-101", "R-103"],
          f"single = {[r['id'] for r in sc.single]}")
    check([r["id"] for r in sc.cross] == ["R-102"],
          f"cross = {[r['id'] for r in sc.cross]}")
    check(sc.undeclared == [], "undeclared 为空")


# ================================================================ 7. 端到端

def test_e2e() -> None:
    section("7. 端到端：生成 6 注影子号码，跨注规则在整组上被执行")

    res = sample_batch(CFG, RULES, n=6, seed=20261012)
    check(len(res) == 6, f"生成 {len(res)} 注")

    bad = [t.render() for t in res if not t.is_valid(CFG)]
    check(not bad, f"全部合法（不合法的：{bad or '无'}）")

    rng_ok = all(
        0 <= v <= 8 for t in res for v in t.zone("red")
    ) and all(
        1 <= v <= 5 for t in res for v in t.zone("blue")
    )
    check(rng_ok, "★ 号码全部落在配置声明的区间内（红区 0–8、蓝区 1–5）")

    single_only = _rule("R-101") + _rule("R-103")
    viol = [t.render() for t in res if not judge(CFG, t, single_only).passes]
    check(not viol, f"全部通过单注规则 R-101/R-103（违规：{viol or '无'}）")

    st = res.stats
    check(st.get("cross_scope_pending") == ["R-102"],
          f"逐注过滤时 R-102 待整组评估：{st.get('cross_scope_pending')}")
    ev = st.get("cross_scope_evaluated")
    check(ev is not None, "★ 跨注规则 R-102 在整组上下文里被真正执行")
    if ev:
        check(ev["rules"] == ["R-102"], f"执行的跨注规则：{ev['rules']}")
        check("has_dup_struct" in ev["features"],
              f"求得跨注特征：{sorted(ev['features'])}")

    again = sample_batch(CFG, RULES, n=6, seed=20261012)
    check([t.render() for t in again] == [t.render() for t in res],
          "同种子可复现")


# ================================================================ 8. 单区变体

def test_single_zone_variant() -> None:
    section("8. 单区变体：区数不是写死的 2")

    cfg1 = copy.deepcopy(CFG)
    cfg1["machine"]["zones"] = [z for z in cfg1["machine"]["zones"]
                                if z["key"] == "red"]
    cfg1["features"] = [f for f in cfg1["features"]
                        if (f.get("args") or {}).get("zone") != "blue"]

    check(zone_keys(cfg1) == ["red"], f"变体只剩一个区：{zone_keys(cfg1)}")
    check(total_combinations(cfg1) == 84, f"单区 T = {total_combinations(cfg1)} = C(9,3)")

    t = Ticket({"red": (0, 1, 4)})          # 间隔 (1,3)：含一个相邻对
    check(t.is_valid(cfg1), "单区注合法")
    f = evaluate(cfg1, t)
    check(f["red_sum"] == 5 and f["has_pair"] is True,
          f"单区求值正常：red_sum={f['red_sum']}, has_pair={f['has_pair']}")

    # ★ 未声明 zone 的原语：单区彩种可自动推断，多区彩种必须显式给
    cfg1["features"].append({
        "key": "red_sum_nozone",
        "label": "不指定 zone 的和值",
        "type": "integer",
        "primitive": "sum",
        "formula": "sum(red)",
    })
    check(evaluate_one(cfg1, t, "red_sum_nozone") == 5,
          "单区彩种：args 省略 zone 也能求值（自动取唯一区）")


# ================================================================ 9. 铁律扫描

def _docstring_lines(src: str) -> set[int]:
    """docstring 覆盖的行号。

    必须剔除：铁律清单本身就把被禁字符串写在 docstring 里（"禁止出现 front"），
    不剔除的话扫描会把"禁令"判成"违规" —— **会误报的检查比没有检查更坏**。
    """
    tree = ast.parse(src)
    out: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            if ast.get_docstring(node, clean=False) is None:
                continue
            first = node.body[0]
            out.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return out


def _scan(pkg_dir: str) -> tuple[set[str], set[int]]:
    """扫一个包目录下所有 .py：**代码里**（剥掉 docstring）出现的字符串与整数字面量。"""
    strs: set[str] = set()
    ints: set[int] = set()
    for fn in sorted(os.listdir(pkg_dir)):
        if not fn.endswith(".py"):
            continue
        src = open(os.path.join(pkg_dir, fn), encoding="utf-8").read()
        doc_lines = _docstring_lines(src)
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Constant) or node.lineno in doc_lines:
                continue
            if isinstance(node.value, str):
                strs.add(node.value)
            elif isinstance(node.value, int) and not isinstance(node.value, bool):
                ints.add(node.value)
    return strs, ints


def test_iron_law() -> None:
    section("9. 铁律：framework/ 与 src/ 里没有 dlt 的任何痕迹")

    packages = [
        os.path.join(_ROOT, "framework", "core"),
        os.path.join(_ROOT, "src", "smartpickcore"),
    ]
    strs: set[str] = set()
    ints: set[int] = set()
    for p in packages:
        s, i = _scan(p)
        strs |= s
        ints |= i

    forbidden_str = {
        "dlt", "大乐透",                      # 彩种标识
        "front", "back",                      # dlt 的区名
        "has_run_ge2", "adjacent_pairs",      # dlt 的特征名
        "duplicated_structure_across_tickets",
        "front_sum", "back_sum", "front_span",
    }
    hit = sorted(forbidden_str & strs)
    check(not hit, f"framework/core + src/smartpickcore 代码里不含 dlt 专有字符串"
                   + ("" if not hit else f"：{hit}"))

    # 号码池常量。为什么只查这三个：2 / 5 这类小整数在 `len(s) < 2`、
    # `width=2` 里必然出现，一并查会误报；而 35 / 12 / 21425712 没有任何
    # 与彩种无关的正当用途。
    forbidden_int = {35, 12, 21425712}
    hitn = sorted(forbidden_int & ints)
    check(not hitn, "代码里不含 dlt 的号码池常量（35 / 12 / 21425712）"
                    + ("" if not hitn else f"：{hitn}"))

    # 框架不得 import games/ 下的任何东西（依赖方向：src → framework，不可逆）
    imported: set[str] = set()
    for p in packages:
        for fn in sorted(os.listdir(p)):
            if not fn.endswith(".py"):
                continue
            src = open(os.path.join(p, fn), encoding="utf-8").read()
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Import):
                    imported |= {a.name for a in node.names}
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
    check(not any(m.startswith("games") for m in imported),
          f"framework/ 与 src/ 不 import games/ 下的模块（共 {len(imported)} 个 import）")

    # 反向自证：本测试用的两套配置彼此独立，且**都没改过**框架
    check(len(single_feature_keys(CFG)) == 5 and len(single_feature_keys(_DLT_CFG)) == 11,
          "两套配置各自声明自己的特征（5 vs 11），框架只是执行方")


def test_scanner_not_vacuous() -> None:
    section("10. 扫描器自检：它真的抓得住违规")

    # 一个"永远全绿"的扫描器比没有扫描器更坏 —— 它给人虚假的安全感。
    # 所以这里喂给它一份**确定违规**的代码，确认它真的会响。
    tmp = tempfile.mkdtemp(prefix="spc_scan_")
    try:
        p = os.path.join(tmp, "bad.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write('ZONE = "front"\nPOOL = 35\n')
        s, i = _scan(tmp)
        check("front" in s, "能抓到被禁字符串 'front'（否则第 9 段形同虚设）")
        check(35 in i, "能抓到被禁常量 35")

        with open(p, "w", encoding="utf-8") as f:
            f.write('"""铁律：禁止出现 front / back。"""\nX = 1\n')
        s2, _ = _scan(tmp)
        check("front" not in s2,
              "★ docstring 里的同名字符串不算违规（否则『禁令清单』本身会被判成违规）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    print("\n影子彩种（shadow）回归测试 —— 唯一硬标准的第一次实测")
    test_load()
    test_declarations()
    test_ticket()
    test_evaluate()
    test_judge()
    test_cross()
    test_e2e()
    test_single_zone_variant()
    test_iron_law()
    test_scanner_not_vacuous()

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
