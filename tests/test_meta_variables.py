# -*- coding: utf-8 -*-
"""元数据字段（schema 1.3：convenience / experience / psychology）测试
—— 无需 pytest，直接 `python tests/test_meta_variables.py`

## 为什么单独一个文件

schema 1.3 新增的三组元数据是「非收益变量」：
  1. convenience —— 购彩便利性（可行域约束，不改变 ROI，F-0026）
  2. experience  —— 情绪体验与预期校准（anticipation-disappointment utility）
  3. psychology  —— 心理学外部锚点（仅机制说明，非仓库数据核验）

本文件守住三条：
  1. **红线**：三组字段 affects_expected_return 必须全为 False —— 一旦有人把
     元数据误改成「收益信号」，立即拦截（元数据不该影响策略数字）。
  2. **结构**：五方式便利性清单、预期校准、文献映射结构完整。
  3. **CLI 展示**：pick 的「现实预期」行按 experience 元数据输出，不硬编码口径。
"""
from __future__ import annotations

import io
import os
import sys
import contextlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "platform"))  # framework→platform（2026-10-12）
sys.path.insert(0, _ROOT)

from spc.strategy import load_strategy  # noqa: E402

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


def test_schema_version() -> None:
    section("1. schema_version 1.4")
    st = load_strategy("dlt")
    check(st.get("schema_version") == "1.4", "schema_version == 1.4")
    for key in ("convenience", "experience", "psychology"):
        check(key in st, f"顶层字段 {key} 存在")


def test_red_lines() -> None:
    section("2. 红线：元数据不得成为收益信号")
    st = load_strategy("dlt")
    for key in ("convenience", "experience", "psychology"):
        meta = st.get(key) or {}
        check(meta.get("affects_expected_return") is False,
              f"{key}.affects_expected_return is False")


def test_convenience() -> None:
    section("3. convenience：五方式便利性清单")
    st = load_strategy("dlt")
    cv = st.get("convenience") or {}
    check(cv.get("is_decision_variable") is True, "is_decision_variable is True")
    modes = cv.get("modes") or []
    ids = [m.get("id") for m in modes]
    check(set(ids) == {"single", "compound", "dan_tuo", "multiplier", "extra"},
          "modes 覆盖五种投注方式 id")
    for m in modes:
        check(m.get("rating") in ("high", "medium", "low"),
              f"  {m.get('id')} rating 合法（{m.get('rating')}）")
        check(bool(m.get("note")), f"  {m.get('id')} note 非空")
    single = next((m for m in modes if m.get("id") == "single"), None)
    check(single is not None and single.get("rating") == "high",
          "单注标记为高便利（策略默认形态）")
    mult = next((m for m in modes if m.get("id") == "multiplier"), None)
    check(mult is not None and "F-0027" in (mult.get("note") or ""),
          "倍投 note 注明 F-0027 自我摊薄（排除理由）")


def test_experience() -> None:
    section("4. experience：情绪体验与预期校准")
    st = load_strategy("dlt")
    ex = st.get("experience") or {}
    ant = ex.get("anticipation") or {}
    check(bool(ant.get("model")), "anticipation.model 非空（学术模型引用）")
    check(bool(ant.get("design")), "anticipation.design 非空（期待节奏设计）")
    cal = ex.get("expectation_calibration") or {}
    check(bool(cal.get("base_line")), "expectation_calibration.base_line 非空")
    check(bool(cal.get("rule")), "expectation_calibration.rule 非空")


def test_psychology() -> None:
    section("5. psychology：外部学术锚点")
    st = load_strategy("dlt")
    ps = st.get("psychology") or {}
    check(ps.get("is_external_evidence") is True, "is_external_evidence is True")
    refs = ps.get("refs") or []
    check(len(refs) >= 1, f"refs ≥ 1（实际 {len(refs)}）")
    for r in refs:
        check(bool(r.get("ref")), f"  ref 非空（{r.get('ref', '')[:40]}…）")
        check(bool(r.get("maps_to")), f"  maps_to 非空")
        check(bool(r.get("role")), f"  role 非空")


def test_cli_expectation_line() -> None:
    section("6. CLI：pick 现实预期行（按 experience 元数据动态输出）")
    sys.path.insert(0, os.path.join(_ROOT, "cli"))
    try:
        import cli_main  # type: ignore
    except Exception:  # noqa: BLE001 —— cli/main.py 依赖 core 包路径，导入失败则跳过
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cli_main", os.path.join(_ROOT, "cli", "main.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            cli_main = mod
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠ CLI 导入失败，跳过展示断言: {e}")
            return
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            cli_main._print_expectation_calibration("dlt", 10)
    except Exception as e:  # noqa: BLE001
        check(False, f"_print_expectation_calibration 不抛异常（{e}）")
        return
    out = buf.getvalue()
    check("现实预期" in out, "输出含『现实预期』")
    check("%" in out, "输出含概率百分比")


def main() -> None:
    test_schema_version()
    test_red_lines()
    test_convenience()
    test_experience()
    test_psychology()
    test_cli_expectation_line()
    print(f"\n通过 {_PASS}  失败 {_FAIL}")
    if _FAILURES:
        print("失败项：")
        for f in _FAILURES:
            print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
