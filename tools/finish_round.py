# -*- coding: utf-8 -*-
"""tools/finish_round.py — 收尾自动化（C1 方向：消灭手写滞后 / 入库即联动）

把 SOP §8 收尾清单里可机械化的步骤一键化：
  §8.2  rehash --strategy（FACTS 变更后证据摘要重算）
  §8.5  count_tests --inject（T-045：测试计数自动注入 tests/README.md）
  §8.7  bump_iteration --write（r14.2：活文档轮次对齐 current_iteration）
  §8.9  render_readme_tree / render_version_index / render_ai_map /
        render_dependency_map / render_flywheel_health --write
        + inject_version_lines --write
  §8.3  validate --all（**渲染后终检**：派生物都是文件，放在渲染前会漏检）
  四件套存在性检查（FINDINGS / HANDOFF / manifest / journal）

⚠️ 顺序不可颠倒：bump_iteration → render_* → inject_version_lines → validate。
   颠倒会先把旧轮次刷进文件头、再改索引，旧值被自洽化后照样全绿（r14.2 事故形态）。

不可自动化（脚本只检查/提示，不代做）：
  - 三闸门 Add（研究轮执行，结论由 Agent 撰写）
  - 四件套内容（研究轮撰写；结构由 validate 的 _check_handoff_structure 拦截）
  - 用户批准门（打印 git 变更摘要，提示确认后提交推送）

用法：
    python tools/finish_round.py [--round NN] [--dry-run]
        # --round 指定轮次（默认 = 当前最大轮）；--dry-run 只检查不写盘/不执行

退出码：0 = 收尾完成待用户批准；1 = 有错误（必须修复后重跑）。
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_PY = sys.executable


def _run(script: str, args: list[str] | None = None, timeout: int = 600) -> int:
    """运行 `python <script> <args>`，实时回显输出。返回退出码。"""
    cmd = [_PY, "-X", "utf8", os.path.join(_ROOT, script)] + (args or [])
    try:
        r = subprocess.run(cmd, cwd=_ROOT, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"  ✗ {script} 超时（>{timeout}s）")
        return 1
    out = (r.stdout or "") + (r.stderr or "")
    if out.strip():
        for line in out.rstrip().splitlines():
            print(f"    {line}")
    return r.returncode


def _latest_round(root: str) -> int:
    best = 0
    d = os.path.join(root, "games", "dlt", "iterations")
    if os.path.isdir(d):
        for name in os.listdir(d):
            m = re.match(r"^round(\d{2})$", name)
            if m:
                best = max(best, int(m.group(1)))
    return best


def _check_four_pieces(root: str, rnd: int) -> list[str]:
    """检查四件套存在性。返回缺失清单（空 = 全齐）。"""
    base = os.path.join(root, "games", "dlt", "iterations", f"round{rnd:02d}")
    needed = {
        "FINDINGS.md": os.path.join(base, "FINDINGS.md"),
        "HANDOFF.md": os.path.join(base, "HANDOFF.md"),
        "manifest.json": os.path.join(base, "manifest.json"),
        "journal": os.path.join(root, "memory", "journal", f"round{rnd:02d}.md"),
    }
    return [k for k, p in needed.items() if not os.path.exists(p)]


def _git_summary(root: str) -> str:
    """git status 摘要（供批准门提示）。"""
    try:
        r = subprocess.run(
            ["git", "status", "--short"], cwd=root, capture_output=True, text=True, timeout=60
        )
        lines = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
        if not lines:
            return "（工作区干净，无未提交变更）"
        return "\n".join(f"    {ln}" for ln in lines[:30]) + (
            f"\n    …共 {len(lines)} 项" if len(lines) > 30 else ""
        )
    except Exception:  # noqa: BLE001
        return "（git status 不可用）"


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    dry = "--dry-run" in sys.argv
    rnd = _latest_round(_ROOT)
    if "--round" in sys.argv:
        i = sys.argv.index("--round")
        rnd = int(sys.argv[i + 1])

    print(f"== 收尾自动化 round{rnd:02d}（{'dry-run 只检查' if dry else '实际执行'}）==")
    problems = []

    # 1. rehash（FACTS 变更后证据摘要重算）
    print("\n[1/7] rehash --strategy（证据摘要重算）")
    if dry:
        print("    （dry-run 跳过）")
    elif _run("cli/main.py", ["rehash", "--strategy"]) != 0:
        problems.append("rehash --strategy 失败")

    # 2. 测试计数注入（T-045：文档计数 = 实跑结果）
    print("\n[2/7] count_tests --inject（tests/README.md 计数自举注入）")
    if dry:
        print("    （dry-run 跳过）")
    elif _run("tools/count_tests.py", ["--inject"]) != 0:
        problems.append("count_tests --inject 失败（有测试失败）")

    # 3. 轮次对齐（r14.2：先改索引，再渲染 —— 顺序反了会把旧值自洽化）
    print(f"\n[3/7] bump_iteration --write（活文档轮次对齐 r{rnd:02d}）")
    if dry:
        print("    （dry-run 跳过）")
    elif _run("tools/bump_iteration.py", ["--write", "--to", f"r{rnd:02d}"]) != 0:
        problems.append("bump_iteration --write 失败")

    # 4. 渲染流水线（派生物全部重新生成）
    print("\n[4/7] 渲染流水线（README 树 / VERSION_INDEX / AI_MAP / 依赖图 / 飞轮 + 版本行注入）")
    if dry:
        print("    （dry-run 跳过）")
    else:
        for t in ("render_readme_tree", "render_version_index", "render_ai_map",
                  "render_dependency_map", "render_flywheel_health"):
            rc = _run(f"tools/{t}.py", ["--write"])
            if rc != 0:
                problems.append(f"{t} --write 失败")
        rc = _run("tools/inject_version_lines.py", ["--write"])
        if rc != 0:
            problems.append("inject_version_lines --write 失败")

    # 5. validate --all（渲染后终检：派生物本身也是文件，渲染前校验会漏）
    print("\n[5/7] validate --all（渲染后终检，必须全绿）")
    if _run("cli/main.py", ["validate", "--all"]) != 0:
        problems.append("validate --all 未全绿（修复后重跑）")

    # 6. 四件套存在性
    print("\n[6/7] 四件套检查")
    missing = _check_four_pieces(_ROOT, rnd)
    if missing:
        problems.append(f"四件套缺失：{', '.join(missing)}（研究轮撰写后重跑）")
        print(f"    ✗ 缺失：{', '.join(missing)}")
    else:
        print("    ✓ FINDINGS / HANDOFF / manifest / journal 均存在")

    # 7. 批准门提示
    print("\n[7/7] 批准门提示（用户确认后才提交推送）")
    print(_git_summary(_ROOT))

    if problems:
        print("\n" + "=" * 60)
        print(f"✗ 收尾未完成（{len(problems)} 项问题）：")
        for p in problems:
            print(f"  ✗ {p}")
        print("修复后重新运行本脚本。")
        return 1

    print("\n" + "=" * 60)
    print("✓ 收尾自动化完成。剩余人工步骤：")
    print("  1. 四件套内容确认（FINDINGS/HANDOFF/manifest/journal 若有缺漏补写）")
    print("  2. 涉及代码/配置/策略 → 你确认方案；")
    print("  3. 你下达 push 指令后提交推送（仅 main 单分支）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
