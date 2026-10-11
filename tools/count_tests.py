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
]

_LINE_RE = re.compile(r"通过\s+(\d+)\s+失败\s+(\d+)")


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


def main() -> int:
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
