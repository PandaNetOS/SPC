# -*- coding: utf-8 -*-
"""下游声明完整性（consumes 逆向检查）测试 —— 无需 pytest，直接 `python tests/test_consumes_completeness.py`

## 为什么单独一个文件

`_check_consumes_completeness` 守的不是计算，是**下游文档的声明完整性**：
正文引用了某个 F-xxxx，但 versions.json 的 consumes 没登记 —— 该结论被推翻时
这份文档会**静默过期**（正是 r07 发现 STRATEGY_GUIDE/rules_history 历史遗漏的根因）。
单行道检查（_check_consumes_freshness）只看得见"声明了的"，
本检查是逆向的：从正文引用反查声明。

## 本文件特别要守住的三条

1. **已声明且被引用 → 不报**（正常路径不误伤）
2. **正文引用未声明（strategy_guide）→ error**（依赖被推翻时会静默过期，必须拦）
3. **历史沿革式提及（作废/更正/superseded 等上下文）→ 豁免**（沿革记录不是依赖）
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from spc.validate import ValidationReport, _check_consumes_completeness  # noqa: E402

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


def _mk(root: str, path: str, text: str, consumes: list[str], kind: str = "doc") -> None:
    """建一个受管文档 + 把它登记进临时 versions.json。"""
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    vp = os.path.join(root, "versions.json")
    entries = json.load(open(vp, encoding="utf-8")).get("entries", []) if os.path.exists(vp) else []
    entries.append({"path": path, "level": "A", "kind": kind,
                    "consumes": consumes, "content_version": "1.0"})
    with open(vp, "w", encoding="utf-8") as f:
        json.dump({"index_version": "1.0", "entries": entries}, f, ensure_ascii=False)


def test_declared_ref_no_error() -> None:
    section("1. 已声明且被引用 → 不报")
    with tempfile.TemporaryDirectory() as root:
        _mk(root, "doc.md", "结论 F-0001 与 F-0003 均成立。", ["F-0001", "F-0003"])
        rep = ValidationReport()
        _check_consumes_completeness(root, rep)
        check(not rep.errors and not rep.warnings, "正常路径：零 error 零 warning")


def test_undeclared_ref_strategy_is_error() -> None:
    section("2. 正文引用未声明（strategy_guide）→ error")
    with tempfile.TemporaryDirectory() as root:
        _mk(root, "guide.md", "本策略依赖 F-0027 与 F-0028。", ["F-0027"], kind="strategy_guide")
        rep = ValidationReport()
        _check_consumes_completeness(root, rep)
        hit = any("F-0028" in e and "未登记 consumes" in e for e in rep.errors)
        check(hit, f"未声明引用被拦为 error（实际 errors={rep.errors or '无'}）")


def test_undeclared_ref_generic_is_warning() -> None:
    section("3. 正文引用未声明（普通 doc）→ warning")
    with tempfile.TemporaryDirectory() as root:
        _mk(root, "notes.md", "相关结论见 F-0019。", ["F-0001"])
        rep = ValidationReport()
        _check_consumes_completeness(root, rep)
        hit = any("F-0019" in w for w in rep.warnings)
        check(not rep.errors, "普通文档未声明 → 不升 error")
        check(hit, "普通文档未声明 → warning 提示")


def test_honorific_mention_exempted() -> None:
    section("4. 历史沿革式提及 → 豁免")
    with tempfile.TemporaryDirectory() as root:
        _mk(root, "guide.md", "早期结论 F-0015 已作废，不再引用。", [], kind="strategy_guide")
        rep = ValidationReport()
        _check_consumes_completeness(root, rep)
        check(not rep.errors and not rep.warnings, "『已作废』上下文豁免（不报）")


def test_consumes_empty_doc_skipped() -> None:
    section("5. 未声明 consumes 的文档 → 跳过（非受管依赖文档）")
    with tempfile.TemporaryDirectory() as root:
        _mk(root, "plain.md", "正文引用 F-0001。", [])
        rep = ValidationReport()
        _check_consumes_completeness(root, rep)
        check(not rep.errors and not rep.warnings, "无 consumes 声明 → 不检查（兼容既有非依赖文档）")


def main() -> int:
    test_declared_ref_no_error()
    test_undeclared_ref_strategy_is_error()
    test_undeclared_ref_generic_is_warning()
    test_honorific_mention_exempted()
    test_consumes_empty_doc_skipped()

    print("\n" + "=" * 72)
    print("结果")
    print("=" * 72)
    print(f"通过 {_PASS}  失败 {_FAIL}")
    if _FAILURES:
        print("\n失败项：")
        for f in _FAILURES:
            print(f"  ✗ {f}")
        return 1
    print("✅ 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
