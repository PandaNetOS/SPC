# -*- coding: utf-8 -*-
"""统一路径层（spc.paths）测试 —— 无需 pytest，直接 `python tests/test_paths.py`

## 为什么必须有这个文件

2026-10-12 的架构升级（`games/` → `labs/<lab>/studies/<id>/`、`framework/` →
`platform/`、研究组记忆下沉）**只做了 git mv + 文档同步**，代码里的路径是各文件
自己拼的字符串。结果飞轮的三条主动脉同时断掉：

    flywheel.py 读 memory/facts/FACTS.jsonl      → FLYWHEEL_HEALTH 全空
    derive_tasks.py 读 memory/workbench/*.md      → 待办池补给断裂（r15 空池事故重演）
    14 处 os.path.join(root, "games", ...)        → validate / pick / 收轮全瘫

validate 从 0 错误涨到 123 项。根因不是「漏改几处」，是**没有路径抽象**。

本文件守住四条：

1. **显式 root 必须被尊重**：传了 root 它就是根，不得向上探测到真仓库
   （否则测试/外部工具的临时目录被静默无视 —— 用错数据比报错危险）；
2. **新旧布局双场景**：新布局（labs/<lab>/studies/<id>）与旧布局（games/<id>）
   都要能解析，迁移期不炸；
3. **无硬编码彩种名**：所有函数收 study/lab 参数，`first_study`/`list_studies`
   动态发现（唯一硬标准：加第二个彩种不改 paths 一行）；
4. **派生扫描源不再漏**：validate 的 `delivered_round_dirs` 等消费方必须走 paths，
   本文件用「造一个只有旧布局的临时仓库」证明它们不会静默返回空。
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 —— 非 TextIOWrapper 时忽略
    pass
_ORIG_STDOUT = sys.stdout

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, os.path.join(_ROOT, "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from spc import paths  # noqa: E402

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


def _w(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)


# ================================================================ 1. 根目录语义

def test_root_semantics() -> None:
    section("1. repo_root：显式 root 必须被尊重")

    r = paths.repo_root()
    check(os.path.isdir(os.path.join(r, "spec")),
          "repo_root() 向上探测到含 spec/ 的仓库根")
    check(os.path.isdir(os.path.join(r, "labs")) or
          os.path.isdir(os.path.join(r, "games")),
          "探测到的根同时含 labs/ 或 games/（新旧布局之一）")

    with tempfile.TemporaryDirectory() as tmp:
        # 显式传 root → 原样返回，不得向上跑到真仓库
        check(paths.repo_root(tmp) == os.path.abspath(tmp),
              "repo_root(tmp) 返回 tmp 本身（不向上探测）")
        # 空目录也给（由调用方按「文件不存在」处理）
        check(paths.repo_root(os.path.join(tmp, "nonexistent")) ==
              os.path.abspath(os.path.join(tmp, "nonexistent")),
              "repo_root(不存在的路径) 也原样返回（不猜、不静默改指向）")


# ================================================================ 2. 新布局

def test_new_layout() -> None:
    section("2. 新布局 labs/<lab>/studies/<id>/")

    r = paths.repo_root()
    sd = paths.studies_dir("lottery", r)
    check(os.path.isdir(sd), f"studies_dir 指向真实目录（{os.path.relpath(sd, r)}）")
    check(sd.endswith(os.path.join("labs", "lottery", "studies")),
          "新布局判据：labs/<lab>/studies")

    ids = paths.list_studies("lottery", r)
    check(len(ids) >= 1, f"list_studies 发现研究组 {ids}")
    check("_template" not in ids and not any(i.startswith(".") for i in ids),
          "_template 与隐藏目录被排除")

    if ids:
        g = ids[0]
        check(os.path.isfile(paths.game_yaml_path(g, root=r)),
              f"game_yaml_path({g}) 指向真实文件")
        check(os.path.isfile(paths.facts_path(g, root=r)),
              f"facts_path({g}) 指向真实 FACTS.jsonl")
        check(os.path.isdir(paths.workbench_dir(g, root=r)),
              f"workbench_dir({g}) 指向真实目录")
        check(os.path.isdir(paths.iterations_dir(g, root=r)),
              f"iterations_dir({g}) 指向真实目录")
        check(os.path.isfile(paths.strategy_json_path(g, root=r)),
              f"strategy_json_path({g}) 指向真实 strategy.json")
        check(paths.rel_study(g, root=r) == f"labs/lottery/studies/{g}",
              f"rel_study({g}) 返回正斜杠相对路径（登记格式）")
        check("\\" not in paths.rel_study(g, root=r),
              "rel_study 不含反斜杠（Windows 下也要能进 versions.json）")

    check(paths.first_study("lottery", r) == (ids[0] if ids else None),
          "first_study == list_studies[0]（彩种无关，不写死 dlt）")
    check(paths.lab_state_path("lottery", r).endswith("LAB_STATE.json"),
          "lab_state_path 指向实验室层状态文件（定时迭代时钟）")


# ================================================================ 3. 旧布局兼容

def test_legacy_layout() -> None:
    section("3. 旧布局 games/<id>/ 兼容（迁移中间态）")

    with tempfile.TemporaryDirectory() as tmp:
        # 只造旧布局：games/dlt/（无 labs/）
        _w(os.path.join(tmp, "games", "dlt", "game.yaml"), 'id: "dlt"\n')
        _w(os.path.join(tmp, "games", "dlt", "strategy", "strategy.json"), "{}")
        _w(os.path.join(tmp, "games", "dlt", "memory", "facts", "FACTS.jsonl"), "")
        _w(os.path.join(tmp, "games", "dlt", "memory", "workbench", "TODO.md"), "- [ ]\n")
        os.makedirs(os.path.join(tmp, "games", "dlt", "iterations", "round01"),
                    exist_ok=True)
        _w(os.path.join(tmp, "games", "dlt", "iterations", "round01", "manifest.json"),
           json.dumps({"round": "r01", "status": "delivered"}))

        check(paths.studies_dir("lottery", tmp) ==
              os.path.join(tmp, "games"),
              "无 labs/ 时回落到 games/（旧布局兼容）")
        check(paths.list_studies("lottery", tmp) == ["dlt"],
              "旧布局下 list_studies 仍能发现 dlt")
        check(os.path.isfile(paths.facts_path("dlt", root=tmp)),
              "旧布局下 facts_path 指向 games/dlt/memory/facts/FACTS.jsonl")
        check(os.path.isfile(paths.strategy_json_path("dlt", root=tmp)),
              "旧布局下 strategy_json_path 指向 games/dlt/strategy/strategy.json")
        check(paths.rel_study("dlt", root=tmp) == "games/dlt",
              "旧布局下 rel_study 为 games/dlt（与登记格式一致）")
        check(os.path.isdir(paths.iterations_dir("dlt", root=tmp)),
              "旧布局下 iterations_dir 可解析")

        # ★ 新旧并存时以新布局为准（不得两个都认 → 静默用错数据）
        _w(os.path.join(tmp, "labs", "lottery", "studies", "dlt", "game.yaml"),
           'id: "dlt"\n')
        check(paths.studies_dir("lottery", tmp) ==
              os.path.join(tmp, "labs", "lottery", "studies"),
              "新旧并存时以新布局为准（优先级明确，不歧义）")


# ================================================================ 4. 消费方不断链

def test_consumers() -> None:
    section("4. 消费方走 paths（validate / flywheel / derive_tasks）")

    with tempfile.TemporaryDirectory() as tmp:
        # 新布局最小仓库：一个已收尾轮 + workbench + facts
        base = os.path.join(tmp, "labs", "lottery", "studies", "dlt")
        _w(os.path.join(base, "game.yaml"), 'id: "dlt"\n')
        _w(os.path.join(base, "iterations", "round03", "manifest.json"),
           json.dumps({"round": "r03", "game": "dlt", "status": "delivered"}))
        _w(os.path.join(base, "memory", "facts", "FACTS.jsonl"),
           json.dumps({"id": "F-0001", "status": "established",
                       "confidence": 5, "claim_type": "analytic",
                       "established_in": "round03", "claim": "x",
                       "affects_win_probability": False}) + "\n")
        _w(os.path.join(base, "memory", "workbench", "TODO.md"), "# TODO\n")
        _w(os.path.join(base, "memory", "workbench", "OPEN_QUESTIONS.md"),
           "## Q-001 — t\n\n| **状态** | `open` |\n| **优先级** | 高 |\n")
        _w(os.path.join(base, "memory", "workbench", "HYPOTHESES.md"),
           "## H-001 — t\n\n| **状态** | `unverified` |\n")

        from spc.validate import current_iteration_round, delivered_round_dirs

        check(delivered_round_dirs(tmp) == [("dlt", 3)],
              "validate.delivered_round_dirs 在临时仓库正确工作（走 paths）")
        check(current_iteration_round(tmp) == 3,
              "validate.current_iteration_round == 3（不读到真仓库的 18）")

        from spc import flywheel

        m = flywheel.collect_metrics(tmp)
        check(m["total"] == 1,
              f"flywheel.collect_metrics(tmp) 统计临时仓库 1 条（实得 {m['total']}）")

        spec = importlib.util.spec_from_file_location(
            "derive_tasks_paths", os.path.join(_ROOT, "tools", "derive_tasks.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.stdout = _ORIG_STDOUT
        qs = mod._q_candidates(tmp)
        hs = mod._h_candidates(tmp)
        check(len(qs) == 1 and qs[0]["src"] == "Q-001",
              f"derive_tasks 在临时仓库解析出 Q-001（实得 {[c['src'] for c in qs]}）")
        check(len(hs) == 1 and hs[0]["src"] == "H-001",
              f"derive_tasks 在临时仓库解析出 H-001（实得 {[c['src'] for c in hs]}）")


# ================================================================ 5. 反硬编码

def test_no_hardcoded_study() -> None:
    section("5. 彩种无关：换一个 study id 全部函数照常工作")

    with tempfile.TemporaryDirectory() as tmp:
        for gid in ("ssq", "another-game"):
            _w(os.path.join(tmp, "labs", "lottery", "studies", gid, "game.yaml"),
               f'id: "{gid}"\n')
        ids = paths.list_studies("lottery", tmp)
        check(sorted(ids) == ["another-game", "ssq"],
              f"两个研究组都被发现且排序稳定（{ids}）")
        for gid in ids:
            check(os.path.isfile(paths.game_yaml_path(gid, root=tmp)),
                  f"game_yaml_path({gid}) 无需改代码")
            check(os.path.isdir(paths.iterations_dir(gid, root=tmp)) is False or
                  os.path.isdir(paths.iterations_dir(gid, root=tmp)),
                  f"iterations_dir({gid}) 可构造")
        check(paths.first_study("lottery", tmp) == "another-game",
              "first_study 取排序第一个（不写死 dlt）")

    # 空目录不得炸
    with tempfile.TemporaryDirectory() as tmp:
        check(paths.list_studies("lottery", tmp) == [],
              "空目录 list_studies 返回 []（不抛异常）")
        check(paths.first_study("lottery", tmp) is None,
              "空目录 first_study 返回 None（不抛异常）")
        check(paths.facts_path("dlt", root=tmp).endswith("FACTS.jsonl"),
              "空目录 facts_path 仍返回合法路径（由调用方判存在性）")


def main() -> int:
    test_root_semantics()
    test_new_layout()
    test_legacy_layout()
    test_consumers()
    test_no_hardcoded_study()
    print()
    print(f"通过 {_PASS}  失败 {_FAIL}")
    if _FAIL:
        for f in _FAILURES:
            print(f"  ✗ {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
