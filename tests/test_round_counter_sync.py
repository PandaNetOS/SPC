# -*- coding: utf-8 -*-
"""轮次号与待办状态双源对账（r15 A1~A4 根治）测试 —— 无需 pytest，直接
`python tests/test_round_counter_sync.py`

## 这批 bug 长什么样

进入 r15 开轮侦察时，连着撞出四个同源问题：

1. **dry-run 有副作用**：`render_task_brief.py` 的 `os.makedirs` 写在 `--write`
   判断**之前**，于是「只想看看任务书长什么样」也会凭空建出 `roundNN/` 空目录。
2. **轮次号由目录存在性推断**：`_next_round` / `current_iteration_round` 都按
   `roundNN` 目录名取 max。空目录一出现，轮号就 +1。两次 dry-run → 造出空的
   round15/round16 → validate 的重校准警告从真实的 5 轮虚增到 7 轮，并报
   「当前 round16」，而 versions.json 的权威 `current_iteration` 仍是 `r14`。
3. **轮次号两个真源互不看**：r14.2 刚把 versions.json 立为权威源，目录扫描那一路
   没人校验它，于是两边各自自洽、静默分叉。
4. **待办池滞后**：T-052 在 r14.1 已实际落地（strategy.json 有 R-004），TODO 仍是
   `- [ ]`。待办池是 `render_task_brief` 的**唯一输入源**，于是 r15 任务书自动把
   一个早已完成的任务当成唯一可执行候选。

合起来是 r14.2 那个「同源双向比对盲区」的又一次变形：每一处单独看都自洽，
合起来就是飞轮在错误的轮号上、推着已完成的任务往下跑。

## 本文件要守住的六条

1. dry-run **不得**产出任何目录（副作用必须只在 `--write` 时发生）；
2. `--write` 才建目录；
3. 轮次号**只认已收尾轮**（含 manifest.json），空 `roundNN` 目录不得推高轮号；
4. `current_iteration_round` 同样忽略空目录；
5. 轮次号双源不一致 → 报错；一致 → 报 OK；
6. 已落地（manifest `strategy_landed`）的任务在 TODO 未勾选 → 报错；勾选 → 不报；
   且**不得**因 `actual_updates` 里的提及而误报（护栏宁可窄而准）。
"""
from __future__ import annotations

import importlib.util
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

from spc import paths  # noqa: E402
from spc.validate import (  # noqa: E402
    ValidationReport,
    _check_iteration_counter_sync,
    _check_todo_landed_sync,
    current_iteration_round,
    delivered_round_dirs,
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


def _w(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)


def _manifest(round_no: int, strategy_landed=None, actual_updates=None) -> str:
    return json.dumps({
        "round": f"r{round_no:02d}",
        "game": "dlt",
        "title": "t",
        "status": "delivered",
        "outputs": {
            "strategy_landed": strategy_landed or [],
            "actual_updates": actual_updates or [],
        },
    }, ensure_ascii=False)


def _mkrepo(root: str, todo_t052: str = " ") -> None:
    """构造最小仓库：round14 已收尾（T-052 落地）+ 一个空的 round15 目录。"""
    _w(os.path.join(root, "versions.json"),
       json.dumps({"current_iteration": "r14", "entries": []}, ensure_ascii=False))
    # paths.list_studies 的判据是「该目录含 game.yaml」—— 夹具必须造它，
    # 否则研究组根本不会被发现（这是 paths 的既定契约，不是缺陷）。
    _w(paths.game_yaml_path("dlt", root=root), 'id: "dlt"\nname: "fixture"\n')
    it = paths.iterations_dir("dlt", root=root)
    _w(os.path.join(it, "round14", "manifest.json"),
       _manifest(14,
                 strategy_landed=["r14.1 用户批准 T-052：R-004 落地"],
                 # 提及而非完成 —— 窄扫描不得误报
                 actual_updates=["T-099 external-data 前置降备选"]))
    os.makedirs(os.path.join(it, "round15"), exist_ok=True)   # 空壳
    _w(os.path.join(paths.workbench_dir("dlt", root=root), "TODO.md"),
       f"- [x] **T-051** 已完成的\n\n"
       f"- [{todo_t052}] **T-052** value: 40 ★ r14 候选：R_new 落地为 R-004\n")


def main() -> int:
    print("A2 — 轮次号只认已收尾轮")
    with tempfile.TemporaryDirectory() as tmp:
        _mkrepo(tmp)
        check(current_iteration_round(tmp) == 14,
              "空 round15 目录不推高轮号（current_iteration_round == 14）")
        check([n for _, n in delivered_round_dirs(tmp)] == [14],
              "delivered_round_dirs 只返回含 manifest 的轮")

        spec = importlib.util.spec_from_file_location(
            "rtb", os.path.join(_ROOT, "tools", "render_task_brief.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        check(mod._next_round(tmp) == 15,
              "_next_round == 15（由 round14 推导，而非空壳 round15 → 16）")

        print("A1 — dry-run 无副作用")
        mod._ROOT = tmp
        saved_argv, saved_out = sys.argv, sys.stdout
        # 必须持有强引用：main() 会用 sys.stdout.buffer 再包一层，
        # 原 wrapper 一旦失去最后一个引用就被 GC 析构，连带关掉底层 BytesIO。
        sink = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        try:
            sys.argv = ["render_task_brief.py"]
            sys.stdout = sink
            mod.main()
        finally:
            sys.stdout = saved_out
            sys.argv = saved_argv
        check(not os.path.isdir(os.path.join(tmp, "labs", "lottery", "studies", "dlt", "iterations", "round16")),
              "dry-run 未新建任何 roundNN 目录")
        check(os.path.isdir(os.path.join(tmp, "labs", "lottery", "studies", "dlt", "iterations", "round15")),
              "dry-run 也未『补写』已存在的空壳 round15")

        sink2 = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        try:
            sys.argv = ["render_task_brief.py", "--write"]
            sys.stdout = sink2
            mod.main()
        finally:
            sys.stdout = saved_out
            sys.argv = saved_argv
        check(os.path.isfile(
            os.path.join(tmp, "labs", "lottery", "studies", "dlt", "iterations", "round15", "TASK_BRIEF.md")),
            "--write 时才创建目录并写入 TASK_BRIEF.md")

    print("A3 — 轮次号双源对账")
    with tempfile.TemporaryDirectory() as tmp:
        _mkrepo(tmp)
        rep = ValidationReport()
        _check_iteration_counter_sync(tmp, rep)
        check(not rep.errors and any("轮次号对账" in c for c in rep.checked),
              "双源一致（r14 == round14）→ 报 OK、无错误")

        _w(os.path.join(tmp, "versions.json"),
           json.dumps({"current_iteration": "r12", "entries": []}, ensure_ascii=False))
        rep = ValidationReport()
        _check_iteration_counter_sync(tmp, rep)
        check(len(rep.errors) == 1 and "双源不一致" in rep.errors[0],
              "双源不一致（r12 vs round14）→ 报错")

    print("A4 — 已落地任务必须勾选")
    with tempfile.TemporaryDirectory() as tmp:
        _mkrepo(tmp, todo_t052=" ")          # T-052 未勾选
        rep = ValidationReport()
        _check_todo_landed_sync(tmp, rep)
        check(any("T-052" in e and "待办状态滞后" in e for e in rep.errors),
              "T-052 已落地但未勾选 → 报错")
        check(not any("T-099" in e for e in rep.errors)
              and not any("T-099" in w for w in rep.warnings),
              "actual_updates 里的提及（T-099）不误报（窄扫描）")

    with tempfile.TemporaryDirectory() as tmp:
        _mkrepo(tmp, todo_t052="x")          # T-052 已勾选
        rep = ValidationReport()
        _check_todo_landed_sync(tmp, rep)
        check(not rep.errors and any("待办落地对账" in c for c in rep.checked),
              "勾选后 → 报 OK、无错误")

    print()
    print(f"通过 {_PASS}  失败 {_FAIL}")
    if _FAIL:
        for f in _FAILURES:
            print(f"  ✗ {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
