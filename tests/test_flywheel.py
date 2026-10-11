# -*- coding: utf-8 -*-
"""飞轮健康度（K）+ 置信度校准（D1）+ 矛盾检测增强（D2）测试。

无需 pytest：`python tests/test_flywheel.py`
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from spc.flywheel import collect_metrics, render_health, calibration_text  # noqa: E402
from spc.depmap import render_dependency_map  # noqa: E402

# framework 非包（无 __init__.py），用 importlib 直接加载 ingate 模块
_spec = importlib.util.spec_from_file_location(
    "ingate", os.path.join(_ROOT, "framework", "tools", "ingate.py"))
_ingate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ingate)  # type: ignore[union-attr]
_semantic_conflict = _ingate._semantic_conflict  # noqa: E402

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


# ---------------------------------------------------------------- K 飞轮健康度

def test_flywheel_metrics() -> None:
    m = collect_metrics(_ROOT)
    check(m["total"] == 41, "K: FACTS 台账统计 41 条结论（F-0001~F-0041）")
    check(m["dead"] == 3, "K: 被推翻结论 3 条（F-0007/F-0015/F-0032 superseded）")
    check(abs(m["survival"] - 38 / 41) < 1e-9, "K: 存活率 = 38/41（可复核）")
    check("by_round" in m and "by_confidence" in m, "K: 按轮/按置信度分层统计存在")


def test_render_health() -> None:
    md = render_health(collect_metrics(_ROOT))
    check("# FLYWHEEL_HEALTH" in md, "K: 文档标题正确")
    check("派生物" in md, "K: 含派生物注记（防手改）")
    check("存活率" in md and "推翻" in md, "K: 含存活率与推翻率指标")
    check("| 5★ |" in md or "| 1★ |" in md, "K: 置信度分层表渲染")


def test_calibration_text() -> None:
    t = calibration_text(collect_metrics(_ROOT))
    check("置信度校准报告" in t, "D1: 报告标题")
    check("★" in t and "推翻率" in t, "D1: 分层推翻率输出")


# ---------------------------------------------------------------- D2 矛盾检测增强

def test_semantic_conflict_direction() -> None:
    active = [{"id": "F-X9", "status": "established", "claim_type": "empirical",
               "claim": "节假日的撞号效应更弱（方向相反）"}]
    fact = {"id": "F-999", "claim_type": "empirical",
            "claim": "春节窗口的撞号效应更强"}
    msgs = _semantic_conflict(fact, active)
    check(any("疑似矛盾" in x for x in msgs),
          "D2: 同主题「春节/撞号」方向词（更强 vs 更弱）触发方向冲突")
    check(any("同 claim_type" in x for x in msgs),
          "D2: 同 claim_type 同主题方向相反 → 必须 revision 提示")


def test_semantic_conflict_redline() -> None:
    active = [{"id": "F-0001", "status": "established",
               "claim": "任何选号方式都不能改变单注的中奖概率"}]
    fact = {"id": "F-998", "claim_type": "analytic",
            "claim": "某策略可提高中奖概率"}
    # F-0001 是「不改变」，新结论称「提高」——方向冲突表不直接覆盖，
    # 但红线范畴断言应被 MUTEX_PAIRS 或范畴逻辑拦下
    msgs = _semantic_conflict(fact, active)
    check(any("红线" in x or "疑似矛盾" in x for x in msgs),
          "D2: 范畴断言（提高中奖概率）与 F-0001 红线冲突可见")
    # 反向：与 F-0001 同向（不提高）不误报
    ok_fact = {"id": "F-997", "claim_type": "analytic",
               "claim": "投注方式不改变中奖概率"}
    msgs2 = _semantic_conflict(ok_fact, active)
    check(not any("冲突" in x for x in msgs2),
          "D2: 与 F-0001 同向（不提高）不误报")


def test_semantic_conflict_noise() -> None:
    active = [{"id": "F-0003", "status": "established", "claim_type": "empirical",
               "claim": "连号形态（run>=2）的投注人群密度更高，撞号效应真实存在"}]
    fact = {"id": "F-996", "claim_type": "documentary",
            "claim": "奖金规则已变更 6 次，跨 epoch 比较奖金金额无意义"}
    msgs = _semantic_conflict(fact, active)
    check(not msgs, "D2: 无关主题不误报（规则变更 vs 连号撞号）")


# ---------------------------------------------------------------- C 依赖图

def test_dependency_map() -> None:
    md = render_dependency_map(_ROOT)
    check("# DEPENDENCY_MAP" in md, "C: 依赖图标题")
    check("派生物" in md, "C: 含派生物注记")
    check("strategy.json" in md and "FACTS:" in md,
          "C: 策略→结论引用关系（evidence_refs）已入图")
    check("game.yaml" in md, "C: 彩种特征→原语引用已入图")


# ---------------------------------------------------------------- F 增量校验冒烟

def test_validate_incremental_smoke() -> None:
    from spc import validate as V
    rep = V.validate_incremental(_ROOT)
    # 登记完成后应通过；未登记新文件时结构完整性会红（机制有效）
    check(rep.passed, f"F: validate --incremental 真实仓库通过（{len(rep.checked)} 项检查）")


if __name__ == "__main__":  # pragma: no cover
    test_flywheel_metrics()
    test_render_health()
    test_calibration_text()
    test_semantic_conflict_direction()
    test_semantic_conflict_redline()
    test_semantic_conflict_noise()
    test_dependency_map()
    test_validate_incremental_smoke()
    print(f"\n通过 {_PASS}  失败 {_FAIL}")
    if _FAILURES:
        print("失败项：")
        for f in _FAILURES:
            print(f"  ✗ {f}")
    sys.exit(1 if _FAIL else 0)
