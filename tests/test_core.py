# -*- coding: utf-8 -*-
"""tests/test_core.py — 框架核心的自动化测试

跑法（无需 pytest，直接 python）：
    python tests/test_core.py

覆盖优先级（按重要性排序）：
  1. **红线测试** —— 最高优先。任何红线被绕过的可能都是 P0
  2. 原语单测 —— 每个原语对固定输入给固定输出
  3. Ticket 校验 —— 非法票必须被拒
  4. predicate DSL —— 合法通过、非法明确拒绝
  5. 作用域切分 —— 跨注规则不能被静默忽略
  6. 数学一致性 —— T 与 p1 必须与解析值一致
  7. 端到端 —— 生成的号码全部合规
"""
from __future__ import annotations

import io
import json
import os
import random
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "framework"))

import yaml  # noqa: E402

from core import (  # noqa: E402
    PRIMITIVES,
    PredicateError,
    Ticket,
    TicketError,
    evaluate,
    first_prize_probability,
    judge,
    parse_predicate,
    sample_batch,
    ticket_from_any,
    total_combinations,
    validate_feature_declarations,
)
from core.features import apply_primitive  # noqa: E402
from core.judge import apply_scope  # noqa: E402

# ---------------------------------------------------------------- 测试框架

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


# ---------------------------------------------------------------- 载入真实配置
CFG = yaml.safe_load(open(os.path.join(_ROOT, "games/dlt/game.yaml"), encoding="utf-8"))
ST = json.load(open(os.path.join(_ROOT, "games/dlt/strategy/strategy.json"), encoding="utf-8"))
DECLARED = [f["key"] for f in CFG["features"]]


# ================================================================ 1. 红线

def test_red_lines() -> None:
    section("1. 红线测试（最高优先）")

    # 1.1 所有可执行特征都不应声称影响中奖概率
    check(
        all("win_probability" not in k for k in DECLARED),
        "特征名里不出现 win_probability（红线：选号不改概率）",
    )

    # 1.2 策略声明必须是负期望且不改变概率
    dis = ST["disclaimer"]
    check(dis["changes_win_probability"] is False,
          "disclaimer.changes_win_probability 恒 false（红线 2）")
    check(dis["is_negative_ev"] is True,
          "disclaimer.is_negative_ev 恒 true")

    # 1.3 可优化目标只能是 expected_bonus_given_win
    check(ST["boundary"]["optimizable_target"] == "expected_bonus_given_win",
          "boundary.optimizable_target 只能是 expected_bonus_given_win（红线 3）")

    # 1.4 奖金规则不影响号码分布
    check(
        all(e.get("sum_affects_numbers") is False
            for e in CFG["prize_model"]["epochs"]),
        "全部 epoch 的 sum_affects_numbers 恒 false（红线 4）",
    )

    # 1.5 judge 的分数不得被误解为概率
    t = Ticket({"front": (3, 11, 17, 24, 32), "back": (4, 9)})
    r = judge(CFG, t, [x for x in ST["rules"] if x["id"] == "R-001"])
    check(r.weight <= 1.0, f"judge 权重 <= 1（得到 {r.weight}）")
    check(r.passes, "合规号码应通过 R-001")


# ================================================================ 2. 原语

def test_primitives() -> None:
    section("2. 原语单测")

    Z = [3, 11, 17, 24, 32]
    cases = [
        ("sum", {}, 87),
        ("span", {}, 29),
        ("min", {}, 3),
        ("max", {}, 32),
        ("count", {}, 5),
        ("count_odd", {}, 3),
        ("count_even", {}, 2),
        ("count_ge", {"threshold": 18}, 2),  # 24, 32 —— 17 < 18
        ("count_le", {"threshold": 11}, 2),
        ("count_in_range", {"lo": 10, "hi": 25}, 3),
        ("adjacent_pair_count", {}, 0),
        ("adjacent_pair_count_ge", {"threshold": 1}, False),
        ("has_consecutive", {}, False),
        ("max_gap", {}, 8),
        ("min_gap", {}, 6),
        ("all_le", {"threshold": 31}, False),
        ("all_ge", {"threshold": 3}, True),
        ("any_le", {"threshold": 5}, True),
        ("any_ge", {"threshold": 30}, True),
        ("max_in_range", {"lo": 1, "hi": 31}, 24),
        ("sum_mod", {"modulus": 10}, 7),
    ]
    for name, args, want in cases:
        got = apply_primitive(name, Z, args)
        check(got == want, f"{name}({args}) = {got}（期望 {want}）")

    # 连号专项（核心判定量载体）
    check(apply_primitive("adjacent_pair_count", [12, 13], {}) == 1,
          "12-13 是 1 对连号")
    check(apply_primitive("adjacent_pair_count", [12, 13, 14], {}) == 2,
          "12-13-14 是 2 对连号")
    check(apply_primitive("adjacent_pair_count_ge", [12, 13, 14], {"threshold": 2}) is True,
          "12-13-14 满足 run>=2（3 连）")
    check(apply_primitive("adjacent_pair_count_ge", [12, 13, 20], {"threshold": 2}) is False,
          "12-13 单对不满足 run>=2")
    check(apply_primitive("adjacent_pair_count", [1, 2, 3, 4, 5], {}) == 4,
          "1-2-3-4-5 是 4 对连号")

    # 参数缺失必须报错，不静默
    check_raises(lambda: apply_primitive("count_ge", Z, {}),
                 Exception, "count_ge 缺 threshold 时报错")
    check_raises(lambda: apply_primitive("不存在的原语", Z, {}),
                 Exception, "未知原语报错")

    # 输入不规范必须报错
    check_raises(lambda: apply_primitive("sum", [1, 1, 2], {}),
                 Exception, "含重复元素的输入被拒")
    check_raises(lambda: apply_primitive("sum", [1, "x"], {}),
                 Exception, "含非整数元素的输入被拒")

    check(len(PRIMITIVES) >= 20, f"原语数量 {len(PRIMITIVES)} >= 20")


# ================================================================ 3. Ticket

def test_ticket() -> None:
    section("3. Ticket 校验")

    ok = Ticket({"front": (3, 11, 17, 24, 32), "back": (4, 9)})
    check(ok.validate(CFG) == [], "合规票无错误")
    check(ok.is_valid(CFG), "is_valid 为 True")

    # 越界
    bad = Ticket({"front": (3, 11, 17, 24, 36), "back": (4, 9)})
    errs = bad.validate(CFG)
    check(any("越界" in e for e in errs), f"越界号被拒: {errs}")

    # 个数不对
    bad2 = Ticket({"front": (3, 11, 17, 24), "back": (4, 9)})
    check(any("需 5 个号" in e for e in bad2.validate(CFG)), "少号被拒")

    # 重复号
    bad3 = Ticket({"front": (3, 3, 17, 24, 32), "back": (4, 9)})
    check(any("重复" in e for e in bad3.validate(CFG)), "重复号被拒")

    # 缺区 / 多区
    bad4 = Ticket({"front": (3, 11, 17, 24, 32)})
    check(any("缺少区" in e for e in bad4.validate(CFG)), "缺区被拒")
    bad5 = Ticket({"front": (3, 11, 17, 24, 32), "back": (4, 9), "extra": (1,)})
    check(any("多出" in e for e in bad5.validate(CFG)), "多区被拒")

    # check() 抛错
    check_raises(lambda: bad.check(CFG), TicketError, "check() 对非法票抛 TicketError")

    # 规范化：可哈希、可去重、可比较
    t1 = Ticket({"front": (32, 3, 24, 11, 17), "back": (9, 4)})
    check(t1 == ok, "顺序不同的同一注相等")
    check(hash(t1) == hash(ok), "顺序不同的同一注哈希相同")
    check(len({t1, ok}) == 1, "可放入集合去重")

    # 渲染
    check(ok.render() == "03 11 17 24 32 + 04 09", f"render() = {ok.render()!r}")

    # from_any 支持字符串分词
    t2 = ticket_from_any({"front": "03 11 17 24 32", "back": "04 09"}, CFG)
    check(t2 == ok, "字符串输入被正确解析")

    # 不写死区名：单区彩种也能用
    single_cfg = {
        "machine": {"zones": [{"key": "main", "pool_size": 10, "pick": 3,
                              "min_value": 1}]},
        "features": [{"key": "s", "label": "和", "type": "integer",
                      "primitive": "sum", "args": {"zone": "main"},
                      "formula": "sum(main)"}],
    }
    t3 = Ticket({"main": (1, 5, 9)})
    check(t3.validate(single_cfg) == [],
          "单区彩种可用（框架未写死 front/back）")


# ================================================================ 4. DSL

def test_dsl() -> None:
    section("4. predicate DSL")

    # 合法
    for s in ["has_run_ge2 == true", "front_sum > 100", "a != false",
              "x >= 3.5", "a == true and b < 3", "a == true or b == false"]:
        try:
            parse_predicate(s)
            check(True, f"合法 predicate 通过: {s!r}")
        except PredicateError as e:
            check(False, f"合法 predicate 被误拒: {s!r} ({e})")

    # 非法 —— 必须明确拒绝，不猜测
    bad_cases = [
        ("a == true and b < 3 or c == 1", "混用 and/or"),
        ("(a == true or b == false) and c == 1", "括号"),
        ("a > b", "右侧非字面量"),
        ("a = 1", "单等号"),
        ("", "空串"),
        ("a == true AND b < 3", "大写 AND"),
    ]
    for s, why in bad_cases:
        check_raises(lambda s=s: parse_predicate(s), PredicateError,
                     f"非法 predicate 被拒（{why}）")

    # 引用未声明特征
    feats = {"has_run_ge2": False}
    check_raises(
        lambda: _eval_pred("unknown_feat == true", feats, DECLARED),
        PredicateError, "引用未声明特征被拒",
    )

    # 布尔与数值不可混比
    check_raises(
        lambda: _eval_pred("has_run_ge2 > 0", feats, DECLARED),
        PredicateError, "布尔特征与数值比较被拒",
    )


def _eval_pred(text, features, declared):
    from core.judge import eval_predicate
    return eval_predicate(text, features, declared=declared)


# ================================================================ 5. 作用域

def test_scope() -> None:
    section("5. 作用域切分（跨注规则不得被静默忽略）")

    single, cross = apply_scope(CFG, ST["rules"])
    check([r["id"] for r in single] == ["R-001"], "R-001 归入单注层")
    check([r["id"] for r in cross] == ["R-002"], "R-002 归入跨注层")

    # 混用规则集必须明确报错（而非静默忽略 R-002）
    check_raises(
        lambda: judge(CFG, Ticket({"front": (3, 11, 17, 24, 32), "back": (4, 9)}),
                      ST["rules"]),
        PredicateError, "混用规则集 judge 明确报错（不静默忽略）",
    )

    # 只跑单注层则正常
    t = Ticket({"front": (3, 11, 17, 24, 32), "back": (4, 9)})
    r = judge(CFG, t, single)
    check(r.passes, "只跑单注层规则时合规票通过")

    # 违规票被排除
    t_bad = Ticket({"front": (4, 18, 22, 23, 24), "back": (1, 6)})
    r_bad = judge(CFG, t_bad, single)
    check(r_bad.excluded, "3 连号被 R-001 排除")
    check("R-001" in r_bad.matched, "命中规则记为 R-001")


# ================================================================ 6. 数学一致性

def test_math() -> None:
    section("6. 数学一致性")

    T = total_combinations(CFG)
    check(T == 21_425_712, f"T = {T:,}（期望 21,425,712）")
    check(T == 324632 * 66, "T = C(35,5) × C(12,2)")

    p = first_prize_probability(CFG)
    check(abs(p - 4.667289469773513e-08) < 1e-22,
          f"p1 = {p}（期望 4.667289469773513e-08）")
    check(abs(p - 1.0 / 21_425_712) < 1e-30, "p1 = 1/T")

    # 概率不可变：与选号无关（解析事实）
    t_a = Ticket({"front": (1, 2, 3, 4, 5), "back": (1, 2)})
    t_b = Ticket({"front": (3, 11, 17, 24, 32), "back": (4, 9)})
    check(p == first_prize_probability(CFG),
          "选号不改变一等奖概率（解析事实，红线 1）")
    check(t_a != t_b, "两注号码不同，但概率相同")


# ================================================================ 7. 端到端

def test_e2e() -> None:
    section("7. 端到端：生成 + 求值 + 判定")

    res = sample_batch(CFG, ST["rules"], n=20, seed=20261011)
    check(len(res) == 20, f"生成 20 注（得到 {len(res)}）")

    bad = [t for t in res if evaluate(CFG, t)["has_run_ge2"]]
    check(not bad, f"全部满足 R-001（违规 {len(bad)} 个）")

    uniq = len(set(res.tickets))
    check(uniq == 20, f"注间唯一（{uniq}/20）")

    # 每注都能被判为通过
    single, _ = apply_scope(CFG, ST["rules"])
    all_pass = all(judge(CFG, t, single).passes for t in res)
    check(all_pass, "全部通过单注层判定")

    # 求值完整性
    feats = evaluate(CFG, res[0])
    check(set(feats) == set(DECLARED),
          f"求值覆盖全部 {len(DECLARED)} 个声明特征")

    # 可复现性：同种子同结果
    res2 = sample_batch(CFG, ST["rules"], n=20, seed=20261011)
    check([t.render() for t in res] == [t.render() for t in res2],
          "同种子生成结果可复现")

    # 不同种子结果不同
    res3 = sample_batch(CFG, ST["rules"], n=20, seed=999)
    check([t.render() for t in res] != [t.render() for t in res3],
          "不同种子产出不同")

    # 不过滤规则时应能被 R-001 拒绝（说明过滤真的在起作用）
    raw = sample_batch(CFG, [], n=200, seed=1)
    n_violate = sum(1 for t in raw if evaluate(CFG, t)["has_run_ge2"])
    check(n_violate > 0,
          f"不过滤时约有 {n_violate}/200 注违反 R-001（≈8.9% 理论值）")

    # 非法规则集必须报错，不静默返回空
    contra = [{"id": "X", "machine_rule": {"predicate": "has_run_ge2 == true",
                                          "action": "exclude"}},
              {"id": "Y", "machine_rule": {"predicate": "has_run_ge2 == true",
                                          "action": "require"}}]
    from core import GenerateError
    check_raises(lambda: sample_batch(CFG, contra, n=1, seed=1),
                 GenerateError, "自相矛盾规则集报错")


# ================================================================ 8. 声明检查

def test_declarations() -> None:
    section("8. features 声明静态检查")

    errs = validate_feature_declarations(CFG)
    check(errs == [], f"真实 game.yaml 声明无误（{len(errs)} 错）")

    # 不存在的 primitive
    bad_cfg = json.loads(json.dumps(CFG))
    bad_cfg["features"][0]["primitive"] = "不存在的原语"
    errs2 = validate_feature_declarations(bad_cfg)
    check(any("未知原语" in e for e in errs2),
          f"不存在的 primitive 被检出: {errs2[:1]}")

    # 缺必需参数
    bad_cfg2 = json.loads(json.dumps(CFG))
    for f in bad_cfg2["features"]:
        if f["key"] == "front_big":
            f["args"] = {"zone": "front"}      # 缺 threshold
    errs3 = validate_feature_declarations(bad_cfg2)
    check(any("threshold" in e for e in errs3),
          f"缺必需参数被检出: {[e for e in errs3 if 'threshold' in e][:1]}")

    # 引用不存在的区
    bad_cfg3 = json.loads(json.dumps(CFG))
    bad_cfg3["features"][0]["args"] = {"zone": "不存在的区"}
    errs4 = validate_feature_declarations(bad_cfg3)
    check(any("不是已声明的区" in e for e in errs4),
          f"引用不存在的区被检出: {errs4[:1]}")

    # 重复 key
    bad_cfg4 = json.loads(json.dumps(CFG))
    bad_cfg4["features"].append(dict(bad_cfg4["features"][0]))
    errs5 = validate_feature_declarations(bad_cfg4)
    check(any("重复" in e for e in errs5), "重复 key 被检出")


# ================================================================ 主流程

def main() -> int:
    print("smartpickcore — 框架核心测试")
    print(f"仓库根: {_ROOT}")
    print(f"game.yaml: dlt（config_version {CFG.get('config_version')}）")

    for fn in (test_red_lines, test_primitives, test_ticket, test_dsl,
               test_scope, test_math, test_e2e, test_declarations):
        fn()

    section("结果")
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
