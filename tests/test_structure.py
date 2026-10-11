# -*- coding: utf-8 -*-
"""结构完整性测试（P1-2 根治）—— 无需 pytest，直接 `python tests/test_structure.py`

## 为什么单独一个文件

2026-10-11 目录结构遗漏事件：README 目录树是手写静态文本，校验只做一致性
（树标注 vs 索引），不做完整性（实际文件 vs 登记）—— v2.0 新增 8 文件/目录
全部漏进树，validate 67 项全绿仍漏 13 处。

根治三道防线，本文件守住其中的"机制真的会拦"：
  1. 目录树 = 派生物（spc.tree.render_tree），任何手改 → 真实仓库检查红字
  2. 受管目录实际文件 ↔ versions.json 双向登记，漏登记 → 红字
  3. 数据/夹具/模板不要求登记（防误报），scripts/ 聚合防树膨胀

## 本文件特别要守住的三条

1. **真实仓库 README 目录树 == render_tree(versions.json)** —— 一次 `--write`
   没跑或手改树，全测试红字（防回归主闸）
2. **双向登记真的会拦** —— 构造临时仓库证明：受管未登记 → 报错；登记后 → 通过
3. **裁剪规则不误伤** —— data/、fixtures/、templates/ 不要求登记；scripts/ 聚合
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

from spc import validate as V  # noqa: E402
from spc.tree import load_versions, render_tree  # noqa: E402

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


# ---------------------------------------------------------------- 1. 派生物一致性

def test_tree_is_derived() -> None:
    v = load_versions(_ROOT)
    expected = render_tree(v["entries"]).strip()

    rp = os.path.join(_ROOT, "README.md")
    text = open(rp, encoding="utf-8").read()
    lines = text.split("\n")
    start = end = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## 目录结构":
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "```":
                    start = j
                    break
            break
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == "```":
            end = j
            break
    actual = "\n".join(lines[start + 1:end]).strip()

    check(actual == expected,
          "真实仓库：README 目录树 == render_tree(versions.json)（手改/漏 --write 会红）")
    check("派生物" in text,
          "README 目录树区块后标注「派生物」提示（勿手改）")

    # 确定性：同输入两次渲染一致
    check(render_tree(v["entries"]) == render_tree(v["entries"]),
          "render_tree 确定性：同输入两次输出一致")


# ---------------------------------------------------------------- 2. 双向登记会拦

def test_bidirectional_registration() -> None:
    tmp = tempfile.mkdtemp(prefix="sc_struct_")
    # 受管文件（未登记）
    os.makedirs(os.path.join(tmp, "src", "spc"), exist_ok=True)
    with open(os.path.join(tmp, "src", "spc", "a.py"), "w", encoding="utf-8") as f:
        f.write("x = 1\n")
    # 数据 / 夹具 / 模板（不要求登记）
    os.makedirs(os.path.join(tmp, "games", "dlt", "data", "raw"), exist_ok=True)
    with open(os.path.join(tmp, "games", "dlt", "data", "raw", "a.csv"), "w", encoding="utf-8") as f:
        f.write("a,b\n")
    os.makedirs(os.path.join(tmp, "tests", "fixtures", "shadow"), exist_ok=True)
    with open(os.path.join(tmp, "tests", "fixtures", "shadow", "g.yaml"), "w", encoding="utf-8") as f:
        f.write("game: x\n")

    with open(os.path.join(tmp, "versions.json"), "w", encoding="utf-8") as f:
        json.dump({"index_version": "1.2", "entries": []}, f)

    # 未登记 → 报错
    rep = V.ValidationReport()
    V._check_structure_completeness(tmp, rep)
    check(bool(rep.errors) and "src/spc/a.py" in rep.errors[0],
          "受管文件未登记 → check_structure 报错（漏登记真的会拦）")

    # 登记后 → 通过（data/fixtures 不被误报；versions.json 自身也须登记）
    with open(os.path.join(tmp, "versions.json"), "w", encoding="utf-8") as f:
        json.dump({"index_version": "1.2", "entries": [
            {"path": "versions.json", "level": "A", "kind": "index"},
            {"path": "src/spc/a.py", "level": "B", "kind": "code"},
        ]}, f)
    rep2 = V.ValidationReport()
    V._check_structure_completeness(tmp, rep2)
    check(not rep2.errors,
          "登记后 → 通过；data/fixtures 不要求登记（裁剪不误伤）")


# ---------------------------------------------------------------- 3. 裁剪与聚合

def test_filter_and_aggregate() -> None:
    entries = [
        {"path": "games/x/data/raw/a.csv", "level": "D"},
        {"path": "tests/fixtures/y.yaml", "level": "D"},
        {"path": "framework/protocol/templates/t.md", "level": "D"},
        {"path": "games/g/iterations/r1/scripts/a.py", "level": "A", "content_version": "1.0"},
        {"path": "games/g/iterations/r1/scripts/b.py", "level": "A", "content_version": "1.0"},
        {"path": "src/spc/t.py", "level": "B"},
    ]
    tree = render_tree(entries)
    check("data/raw/a.csv" not in tree and "fixtures" not in tree and "templates" not in tree,
          "裁剪：data/fixtures/templates 不进入目录树")
    check("scripts/  ← 轮次脚本（2 个）" in tree,
          "聚合：scripts/ 折叠为一行（N 个脚本）")
    check("t.py" in tree,
          "常规文件正常渲染（叶子名出现于树中）")


if __name__ == "__main__":  # pragma: no cover
    test_tree_is_derived()
    test_bidirectional_registration()
    test_filter_and_aggregate()
    print(f"\n通过 {_PASS}  失败 {_FAIL}")
    if _FAILURES:
        print("失败项：")
        for f in _FAILURES:
            print(f"  ✗ {f}")
    sys.exit(1 if _FAIL else 0)
