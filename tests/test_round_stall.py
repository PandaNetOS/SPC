# -*- coding: utf-8 -*-
"""轮次停滞检查（r14.2 根治）测试 —— 无需 pytest，直接 `python tests/test_round_stall.py`

## 这个 bug 长什么样

README 头部版本行写 `轮次 r12`，而权威 `current_iteration = r14`，
**validate 104 项全绿**。原因不是检查写错了，是**检查缺了一类判据**：

    校验器只做「文件内版本行 ↔ versions.json 条目」的同源双向比对，
    而 current_iteration 只作为 stats 打印、从不参与判定。
    索引条目过期 → inject_version_lines 照抄过期值写进文件头 →
    两边一致 → 全绿。抓得住 A≠B，抓不住 A、B 一起过时。

## 本文件特别要守住的四条

1. **同源自洽必须被识破**：文件内版本行与索引**完全一致**（都停在旧轮次）时，
   仍然必须报错 —— 这是本 bug 的核心形态，也是最容易回归的一条。
2. **活文档已对齐 → 不报**（正常路径不误伤）。
3. **未标 follows_current 的稳定文档落后 → 不报**：
   防停滞**只认显式声明**。泛化的「落后 N 轮」告警实测一次刷出 26 条
   无操作价值的噪音，会淹没真正错误（本仓库常态仅十余条警告）。
4. **轮次产物（roundNN/*）落后 → 不报**：它们的轮次天生属于产出那一轮，
   强制对齐反而抹掉真实信息。

外加：修复端 `tools/bump_iteration.py` 能真正把活文档对齐到 current_iteration
（含 `--to` 推进轮次），否则「发现端」报错后无人能自动修复。
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

from spc.versions import verify_versions, version_line  # noqa: E402

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


def _mk_md(root: str, path: str, cv: str, it: str) -> None:
    """建一个 .md，头部写入**与索引同值**的版本行（模拟 inject 已刷过）。"""
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full) or root, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(f"# T\n\n{version_line(cv, it, '2026-10-11')}\n\nbody\n")


def _mk_index(root: str, entries: list[dict], current: str = "r14") -> None:
    with open(os.path.join(root, "versions.json"), "w", encoding="utf-8") as f:
        json.dump({"index_version": "2.1", "current_iteration": current,
                   "entries": entries}, f, ensure_ascii=False)


def _errs(root: str) -> list[str]:
    # 临时仓库没有 VERSION_INDEX.md 派生物（它的存在性是另一条独立检查，
    # 与本文件无关），过滤掉以免干扰断言。
    return [e for e in verify_versions(root)["errors"] if "VERSION_INDEX" not in e]


def _warns(root: str) -> list[str]:
    return [w for w in verify_versions(root)["warnings"] if "VERSION_INDEX" not in w]


# ---------------------------------------------------------------- 1
def test_stale_but_self_consistent_is_caught() -> None:
    """★ 核心回归：文件内版本行与索引一致（都过期）时，仍必须报错。"""
    section("1. 同源自洽陷阱 —— 两边都是 r12，也必须报『轮次停滞』")
    with tempfile.TemporaryDirectory() as root:
        _mk_md(root, "README.md", "1.16", "r12")
        _mk_index(root, [{"path": "README.md", "level": "B", "kind": "doc",
                          "content_version": "1.16", "iteration": "r12",
                          "follows_current": True}])
        errs = _errs(root)
        check(any("轮次停滞" in e for e in errs),
              "活文档落后于 current_iteration → 报错（即使文件头与索引一致）")
        check(not any("版本不一致" in e for e in errs),
              "『文件内 ↔ 索引』一致性检查本身是绿的（证明旧校验器看不见）")


# ---------------------------------------------------------------- 2
def test_aligned_no_error() -> None:
    section("2. 活文档已对齐 → 不报")
    with tempfile.TemporaryDirectory() as root:
        _mk_md(root, "README.md", "1.16", "r14")
        _mk_index(root, [{"path": "README.md", "level": "B", "kind": "doc",
                          "content_version": "1.16", "iteration": "r14",
                          "follows_current": True}])
        check(not _errs(root), "iteration == current_iteration → 无错误")


# ---------------------------------------------------------------- 3
def test_unmarked_stale_doc_not_reported() -> None:
    section("3. 未标 follows_current 的稳定文档落后 → 不报（防噪音）")
    with tempfile.TemporaryDirectory() as root:
        _mk_md(root, "docs/METHODOLOGY.md", "1.0", "r02")
        _mk_index(root, [{"path": "docs/METHODOLOGY.md", "level": "B", "kind": "doc",
                          "content_version": "1.0", "iteration": "r02"}])
        check(not _errs(root), "未声明活文档 → 无错误")
        check(not any("落后" in w for w in _warns(root)),
              "未声明活文档 → 也不刷『落后 N 轮』告警")


# ---------------------------------------------------------------- 4
def test_round_artifact_not_reported() -> None:
    section("4. 轮次产物（roundNN/*）落后 → 不报（轮次天生属于产出那一轮）")
    with tempfile.TemporaryDirectory() as root:
        _mk_md(root, "labs/lottery/studies/dlt/iterations/round12/HANDOFF.md", "1.0", "r12")
        _mk_index(root, [{"path": "labs/lottery/studies/dlt/iterations/round12/HANDOFF.md",
                          "level": "A", "kind": "handoff",
                          "content_version": "1.0", "iteration": "r12"}])
        check(not _errs(root), "轮次产物保持产出轮次 → 无错误")


# ---------------------------------------------------------------- 5
def _load_bump():
    spec = importlib.util.spec_from_file_location(
        "bump_iteration", os.path.join(_ROOT, "tools", "bump_iteration.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_bump_iteration_fixes() -> None:
    section("5. 修复端 bump_iteration 能真正对齐（含 --to 推进轮次）")
    with tempfile.TemporaryDirectory() as root:
        _mk_md(root, "README.md", "1.16", "r12")
        vp = os.path.join(root, "versions.json")
        _mk_index(root, [{"path": "README.md", "level": "B", "kind": "doc",
                          "content_version": "1.16", "iteration": "r12",
                          "follows_current": True}])

        mod = _load_bump()
        mod._VP = vp
        saved_argv = sys.argv
        try:
            sys.argv = ["bump_iteration", "--write", "--to", "r15"]
            rc = mod.main()
        finally:
            sys.argv = saved_argv

        d = json.load(open(vp, encoding="utf-8"))
        e = d["entries"][0]
        check(rc == 0, "bump_iteration --write 退出码 0")
        check(d.get("current_iteration") == "r15", "--to r15 推进了 current_iteration")
        check(e.get("iteration") == "r15", "活文档条目被对齐到 r15")
        check(e.get("content_version") == "1.16",
              "默认不 bump content_version（避免版本通胀）")
        # 对齐后，把文件头也刷成 r15 应当全绿
        _mk_md(root, "README.md", "1.16", "r15")
        check(not _errs(root), "对齐 + 重新注入后 → 无错误")


def main() -> int:
    test_stale_but_self_consistent_is_caught()
    test_aligned_no_error()
    test_unmarked_stale_doc_not_reported()
    test_round_artifact_not_reported()
    test_bump_iteration_fixes()

    print(f"\n{'=' * 72}")
    # 计数自举：tools/count_tests.py 用 `通过 N  失败 M` 解析（保持一致）
    print(f"通过 {_PASS}  失败 {_FAIL}")
    if _FAIL:
        print("失败项：")
        for f in _FAILURES:
            print(f"  ✗ {f}")
        return 1
    print("✓ 全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
