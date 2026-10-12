# -*- coding: utf-8 -*-
"""测试通过计数的**自举**来源。

## 为什么需要它

`README.md` / `tests/README.md` 里写的 `113 / 62 / 43 / 32 / 69` 是**运行时**计数，
不是静态行数 —— 很多 `check()` 在循环里（例如对 21 个原语逐个断言只占一行源码）。
静态行数永远不会等于实际断言数，所以手写的数字**一定**会漂移。

本脚本**真跑**每个测试文件，抓其末尾打印的 `通过 N  失败 M`，输出一张可贴回文档的表。
文档里的数字因此有了可重算的来源，而不是靠人每次手动对齐。

## 用法

```bash
python tools/count_tests.py
```

非零退出 = 任一测试有失败项（可直接接 CI）。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

# 顺序即文档里列举的顺序；新增测试文件时在此登记即可。
TEST_FILES = [
    "tests/test_core.py",
    "tests/test_cross_scope.py",
    "tests/test_claim_type.py",
    "tests/test_evidence_anchor.py",
    "tests/test_shadow_game.py",
    "tests/test_structure.py",
    "tests/test_flywheel.py",
    "tests/test_ai_readability.py",
    "tests/test_consumes_completeness.py",
    "tests/test_meta_variables.py",
    "tests/test_open_questions_consistency.py",
    "tests/test_research_lib.py",
    "tests/test_round_stall.py",
    "tests/test_round_counter_sync.py",
    "tests/test_derive_tasks.py",
]

# 覆盖说明（tests/README.md 表格的权威来源；--inject 时用此重建表格）
TEST_COVERAGE = {
    "tests/test_core.py": "红线 / 原语 / Ticket / DSL / 作用域 / 数学 / 端到端 / 声明静态检查",
    "tests/test_cross_scope.py": "★ 跨注层：跨注原语 / `Portfolio` / `evaluate_cross` / `judge_cross` / 三路切分 / 端到端 / 铁律扫描",
    "tests/test_claim_type.py": "★ 证据类型：五类约束**真的会拦** / schema 与 Python 双通道一致 / 分类自洽",
    "tests/test_evidence_anchor.py": "★ 证据锚定：漂移真能检出 / 该敏感的要敏感、该迟钝的要迟钝 / 重基线幂等",
    "tests/test_shadow_game.py": "★ 影子彩种：第二彩种全链路跑通 + 铁律扫描（`platform/` 与 `src/` 无 dlt 痕迹）+ 扫描器自检",
    "tests/test_structure.py": "★ 结构完整性（P1-2 根治）：目录树 = 派生物防手改 / 双向登记真的会拦 / 裁剪不误伤 / scripts 聚合",
    "tests/test_flywheel.py": "★ r06 飞轮升级：K 健康度统计 / D1 置信度校准 / D2 矛盾检测（方向+范畴）/ C 依赖图 / F 增量校验冒烟",
    "tests/test_ai_readability.py": "★ r06 AI 可读性：P1 机器地图派生物 / P2 入口完整性 / B 任务书评分 / H 交接模板 / I 压缩到期",
    "tests/test_consumes_completeness.py": "★ 下游声明完整性：逆向检查（正文引用未声明即拦截）真的会拦",
    "tests/test_meta_variables.py": "★ schema 1.3 元数据：convenience/experience/psychology 结构 + 红线恒值 + CLI 展示",
    "tests/test_open_questions_consistency.py": "★ Q 状态一致性：解析归一化 / 头部计数滞后 / 标题缺 ✅ / 优先级表 active 含已清偿 / 状态词非法",
    "tests/test_research_lib.py": "★ 研究资本化（Y）：bootstrap/比率/Wilson 原语已知分布验证 + 分期稳健性判定 + 样本不足不硬报",
    "tests/test_round_stall.py": "★ 轮次停滞（r14.2）：同源自洽陷阱必须被识破 / 已对齐与未声明活文档不误伤 / bump_iteration 能修复",
    "tests/test_round_counter_sync.py": "★ 轮次号与待办双源对账（r15）：dry-run 无副作用 / 轮次号只认已收尾轮 / 双源不一致必报 / 已落地任务未勾选必报且提及不误报",
    "tests/test_derive_tasks.py": "★ 任务源派生（r16 ★源自救）：open Q 必派生 / 已答不派生；H unverified+partial 派生、refuted 不派生；resource 标记保留；幂等（跑两次不重复）；dry-run 不落盘；派生条目可被任务书解析",
}

_LINE_RE = re.compile(r"通过\s+(\d+)\s+失败\s+(\d+)")

_TESTS_README = os.path.join(_ROOT, "tests", "README.md")
_TABLE_RE = re.compile(
    r"(## 现状\n\n\| 文件 \| 项数 \| 覆盖 \|\n\|---\|---\|---\|\n)(.*?)(\n\n\*\*计数自举)",
    re.S,
)


def _count(path: str) -> tuple[int, int, str] | None:
    """跑一个测试文件，返回 (passed, failed, err)。err 非空表示运行/解析失败。"""
    full = os.path.join(_ROOT, path)
    if not os.path.exists(full):
        return None
    try:
        r = subprocess.run(
            [sys.executable, full], cwd=_ROOT,
            capture_output=True, text=True,
        )
    except OSError as e:  # noqa: BLE001
        return None
    m = _LINE_RE.search(r.stdout)
    if not m:
        tail = (r.stdout or r.stderr)[-200:]
        return 0, 0, f"无法解析输出（exit={r.returncode}）：{tail!r}"
    return int(m.group(1)), int(m.group(2)), ""


def render_table() -> tuple[str, int, int]:
    """真跑全部测试，返回 (markdown 表格块, 通过合计, 失败合计)。"""
    rows = []
    total_pass = 0
    total_fail = 0
    for t in TEST_FILES:
        res = _count(t)
        if res is None:
            rows.append(f"| `{t}` | **缺文件** | |")
            continue
        passed, failed, err = res
        if err:
            rows.append(f"| `{t}` | **ERR** | {err} |")
            continue
        total_pass += passed
        total_fail += failed
        cov = TEST_COVERAGE.get(t, "")
        mark = "（全绿）" if failed == 0 else f"（失败 {failed}）"
        rows.append(f"| `{t}` | **{passed}**{mark} | {cov} |")
    total = f"| **合计** | **{total_pass}**（全绿） | 无需 pytest，直接 `python tests/test_*.py` |" if total_fail == 0 \
        else f"| **合计** | **{total_pass}**（失败 {total_fail}） | ⚠ 有失败 |"
    rows.append(total)
    return "\n".join(rows), total_pass, total_fail


def inject_tests_readme() -> int:
    """把 tests/README.md 的『现状』表格替换为实跑结果（T-045：计数自动注入）。"""
    table, total_pass, total_fail = render_table()
    if not os.path.exists(_TESTS_README):
        print(f"✗ {_TESTS_README} 不存在，无法注入")
        return 1
    txt = open(_TESTS_README, encoding="utf-8").read()
    m = _TABLE_RE.search(txt)
    if not m:
        print("✗ tests/README.md 缺少『## 现状』表格块（格式：| 文件 | 项数 | 覆盖 |），拒绝注入")
        return 1
    new = txt[:m.start()] + m.group(1) + table + m.group(3)
    open(_TESTS_README, "w", encoding="utf-8", newline="\n").write(new)
    print(f"✓ tests/README.md 计数已注入（合计 {total_pass}，失败 {total_fail}）")
    return 0 if total_fail == 0 else 1


def main() -> int:
    if "--inject" in sys.argv:
        return inject_tests_readme()
    print("测试通过计数（自举：真跑测试后抓取，非静态行数）")
    print(f"{'文件':40s} {'通过':>6s} {'失败':>6s}")
    print("-" * 54)
    total_pass = 0
    total_fail = 0
    bad = False
    for t in TEST_FILES:
        res = _count(t)
        if res is None:
            print(f"{t:40s} {'缺文件':>6s}")
            bad = True
            continue
        passed, failed, err = res
        if err:
            print(f"{t:40s} {'ERR':>6s}  {err}")
            bad = True
            continue
        total_pass += passed
        total_fail += failed
        if failed:
            bad = True
        print(f"{t:40s} {passed:>6d} {failed:>6d}")
    print("-" * 54)
    print(f"{'合计':40s} {total_pass:>6d} {total_fail:>6d}")
    if bad:
        print("\n⚠ 存在失败或无法解析的测试 —— 退出码 1")
        return 1
    print("\n✅ 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
