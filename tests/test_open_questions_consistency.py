# -*- coding: utf-8 -*-
"""开放问题状态一致性测试（Q 状态根治）—— 无需 pytest，直接 `python tests/test_open_questions_consistency.py`

## 为什么单独一个文件

2026-10-11 滞后事件：Q-012/013/014 内容状态字段已改 `answered`，
但头部统计（仍写 6 answered）、标题 ✅ 标记、优先级总览表（仍列
「下轮首推」）三处未同步 → CLI `questions` 显示为 open/unknown。

根因：answered 标记需 4 处手动同步（状态字段 / 标题 ✅ / 头部统计 /
优先级表），漏一处即滞后；且 CLI 状态解析正则对 `→`、`（`、`+` 等
说明字符容错差，进一步放大不一致。

本文件守住：
  1. 状态解析对带说明字符的值正确归一化（answered/open/blocked/unknown）
  2. validate 新增 `_check_open_questions_consistency` 真的会拦
     （头部计数滞后 / 标题缺 ✅ / 优先级表 active 含已清偿 / 状态词非法）
  3. 一致文件不误报
"""
from __future__ import annotations

import io
import os
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "platform", "tools"))

from spc import validate as V  # noqa: E402
from spc.memory import Memory  # noqa: E402

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


def _write_q_file(root: str, body: str) -> str:
    """在临时仓库写 OPEN_QUESTIONS.md，返回其路径。"""
    d = os.path.join(root, "memory", "workbench")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "OPEN_QUESTIONS.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    return p


def _run_check(root: str) -> tuple[V.ValidationReport, list[str]]:
    rep = V.ValidationReport()
    V._check_open_questions_consistency(root, rep)
    return rep, rep.errors


# ---------------------------------------------------------------- 1. 解析归一化

def test_status_parsing_normalizes() -> None:
    body = """# OPEN_QUESTIONS.md
**当前状态**：3 个开放问题 | **1 answered**（Q-001 by r01）

## Q-001 — 撞号效应 ✅ answered in r01

| 项 | 内容 |
|---|---|
| **状态** | `answered`（r01 → F-0001，含 → 与（）与 + 说明字符） |

## Q-002 — 销量内生

| 项 | 内容 |
|---|---|
| **状态** | `open`（数据缺口：缺 X） |

## Q-003 — 无状态字段的旧条

---
"""
    qs = V._question_sections(body)
    by_id = {qid: st for qid, st, _ in qs}
    check(by_id.get("Q-001") == "answered",
          "Q-001 状态值含 →/（）/+ 等说明字符 → 归一化为 answered")
    check(by_id.get("Q-002") == "open",
          "Q-002 open 带括号说明 → 归一化为 open")
    check(by_id.get("Q-003") == "unknown",
          "Q-003 无状态字段 → unknown")


def test_memory_open_questions_normalizes() -> None:
    tmp = tempfile.mkdtemp(prefix="spc_qparse_")
    _write_q_file(tmp, """# OPEN_QUESTIONS.md

## Q-001 — 撞号效应 ✅ answered in r01

| 项 | 内容 |
|---|---|
| **状态** | `answered`（r01 → F-0001） |

## Q-002 — 后区撞号

| 项 | 内容 |
|---|---|
| **状态** | `open`（未建模） |
""")
    mem = Memory(tmp)
    qs = mem.open_questions()
    by_id = {qid: st for qid, st, _ in qs}
    check(by_id.get("Q-001") == "answered",
          "Memory.open_questions() 对 answered（含 →）归一化")
    check(by_id.get("Q-002") == "open",
          "Memory.open_questions() 对 open（含括号）归一化")


# ---------------------------------------------------------------- 2. 一致文件通过

def test_consistent_file_passes() -> None:
    tmp = tempfile.mkdtemp(prefix="spc_qcons_")
    _write_q_file(tmp, """# OPEN_QUESTIONS.md

**当前状态**：2 个开放问题 | **1 answered**（Q-001 by r01）

## Q-001 — 撞号效应 ✅ answered in r01

| 项 | 内容 |
|---|---|
| **状态** | `answered`（r01 → F-0001） |

## Q-002 — 销量内生

| 项 | 内容 |
|---|---|
| **状态** | `open` |

## 优先级总览

| 优先级 | 问题 | 理由 |
|---|---|---|
| ~~高~~ | ~~Q-001~~ | ✅ r01 已清偿 |
| **中** | **Q-002** | 待办 |
""")
    rep, errs = _run_check(tmp)
    check(not errs, "一致文件（4 处同步）→ 无 error")


# ---------------------------------------------------------------- 3. 各类滞后会拦

def test_header_count_lag_is_blocked() -> None:
    tmp = tempfile.mkdtemp(prefix="spc_qlag_")
    _write_q_file(tmp, """# OPEN_QUESTIONS.md

**当前状态**：2 个开放问题 | **1 answered**（Q-001 by r01）

## Q-001 — 撞号效应 ✅ answered in r01

| 项 | 内容 |
|---|---|
| **状态** | `answered`（r01 → F-0001） |

## Q-002 — 前段取证 ✅ answered in r02

| 项 | 内容 |
|---|---|
| **状态** | `answered`（r02 → F-0002） |
""")
    rep, errs = _run_check(tmp)
    check(any("头部 answered 计数 1 ≠ 实际 2" in e for e in errs),
          "头部计数滞后（写 1、实际 2）→ error")


def test_title_mark_lag_is_blocked() -> None:
    tmp = tempfile.mkdtemp(prefix="spc_qtitle_")
    _write_q_file(tmp, """# OPEN_QUESTIONS.md

**当前状态**：1 个开放问题 | **1 answered**（Q-001 by r01）

## Q-001 — 撞号效应

| 项 | 内容 |
|---|---|
| **状态** | `answered`（r01 → F-0001） |
""")
    rep, errs = _run_check(tmp)
    check(any("Q-001 状态=answered 但标题缺『✅ answered』标记" in e for e in errs),
          "标题缺 ✅（状态已 answered）→ error")


def test_priority_table_lag_is_blocked() -> None:
    tmp = tempfile.mkdtemp(prefix="spc_qprio_")
    _write_q_file(tmp, """# OPEN_QUESTIONS.md

**当前状态**：1 个开放问题 | **1 answered**（Q-001 by r01）

## Q-001 — 撞号效应 ✅ answered in r01

| 项 | 内容 |
|---|---|
| **状态** | `answered`（r01 → F-0001） |

## 优先级总览

| 优先级 | 问题 | 理由 |
|---|---|---|
| **高** | **Q-001**（★ 下轮首推） | 已清偿却仍 active |
""")
    rep, errs = _run_check(tmp)
    check(any("优先级总览 active 行仍列出已清偿问题" in e and "Q-001" in e for e in errs),
          "优先级表 active 行含已清偿 Q-001 → error")


def test_bad_status_word_is_blocked() -> None:
    tmp = tempfile.mkdtemp(prefix="spc_qbad_")
    _write_q_file(tmp, """# OPEN_QUESTIONS.md

**当前状态**：1 个开放问题 | **0 answered**

## Q-001 — 撞号效应

| 项 | 内容 |
|---|---|
| **状态** | `进行中` |
""")
    rep, errs = _run_check(tmp)
    check(any("状态字段无法解析" in e and "Q-001" in e for e in errs),
          "状态词非法（非 answered/open/blocked）→ error")


def test_missing_priority_section_is_blocked() -> None:
    tmp = tempfile.mkdtemp(prefix="spc_qnoprio_")
    _write_q_file(tmp, """# OPEN_QUESTIONS.md

**当前状态**：1 个开放问题 | **0 answered**

## Q-001 — 撞号效应

| 项 | 内容 |
|---|---|
| **状态** | `open` |
""")
    rep, errs = _run_check(tmp)
    check(any("缺少『优先级总览』段" in e for e in errs),
          "缺少优先级总览段 → error")


# ---------------------------------------------------------------- 4. 真实仓库绿

def test_real_repo_passes() -> None:
    rep = V.ValidationReport()
    V._check_open_questions_consistency(_ROOT, rep)
    check(not rep.errors,
          "真实仓库：_check_open_questions_consistency 无 error（当前 4 处已同步）")


if __name__ == "__main__":  # pragma: no cover
    test_status_parsing_normalizes()
    test_memory_open_questions_normalizes()
    test_consistent_file_passes()
    test_header_count_lag_is_blocked()
    test_title_mark_lag_is_blocked()
    test_priority_table_lag_is_blocked()
    test_bad_status_word_is_blocked()
    test_missing_priority_section_is_blocked()
    test_real_repo_passes()
    print(f"\n通过 {_PASS}  失败 {_FAIL}")
    if _FAILURES:
        print("失败项：")
        for f in _FAILURES:
            print(f"  ✗ {f}")
    sys.exit(1 if _FAIL else 0)
