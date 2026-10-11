# -*- coding: utf-8 -*-
"""AI 可读性（P1/P2）+ 任务书生成（B）+ HANDOFF/压缩护栏（H/I）测试。

无需 pytest：`python tests/test_ai_readability.py`
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
sys.path.insert(0, os.path.join(_ROOT, "tools"))

from spc import validate as V  # noqa: E402
from spc.ai_map import load_versions, render_ai_map  # noqa: E402
import render_task_brief as RTB  # noqa: E402

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


# ---------------------------------------------------------------- P1 AI_MAP

def test_ai_map_rendered() -> None:
    v = load_versions(_ROOT)
    md = render_ai_map(v["entries"])
    check("# AI_MAP" in md, "P1: 标题正确")
    check("派生物" in md, "P1: 含派生物注记（防手改）")
    for sec in ("## 入口（先读）", "## 契约", "## 框架", "## 记忆", "## 测试"):
        check(sec in md, f"P1: 分区 {sec} 存在")
    check("`AI_CONTEXT.md`" in md and "`AGENTS.md`" in md,
          "P1: 入口文档在「先读」区列出")
    check("tests/fixtures" not in md and "data/raw" not in md,
          "P1: 裁剪 data/fixtures 不进入机器地图")
    # 确定性
    check(render_ai_map(v["entries"]) == md, "P1: 渲染确定性")


def test_ai_map_check_real() -> None:
    rep = V.ValidationReport()
    V._check_ai_map_rendered(_ROOT, rep)
    check(not rep.errors, "P1: 真实仓库 AI_MAP 派生物一致性通过（--write 已生成）")


def test_ai_map_check_missing() -> None:
    tmp = tempfile.mkdtemp(prefix="sc_aimap_")
    with open(os.path.join(tmp, "versions.json"), "w", encoding="utf-8") as f:
        json.dump({"index_version": "1.2", "entries": []}, f)
    rep = V.ValidationReport()
    V._check_ai_map_rendered(tmp, rep)
    check(bool(rep.errors) and "AI_MAP.md 缺失" in rep.errors[0],
          "P1: AI_MAP.md 缺失 → 校验报错（机制真的会拦）")


# ---------------------------------------------------------------- P2 入口完整性

def test_ai_entry_completeness_real() -> None:
    rep = V.ValidationReport()
    V._check_ai_entry_completeness(_ROOT, rep)
    check(not rep.errors,
          f"P2: 真实仓库 AI_CONTEXT 全部关键锚存在（{len(V._AI_ENTRY_STATIC_ANCHORS)} 静态锚 + 动态锚）")


def test_ai_entry_completeness_missing() -> None:
    tmp = tempfile.mkdtemp(prefix="sc_aientry_")
    with open(os.path.join(tmp, "AI_CONTEXT.md"), "w", encoding="utf-8") as f:
        f.write("# AI_CONTEXT\n\n只有开头，没有锚。\n")
    rep = V.ValidationReport()
    V._check_ai_entry_completeness(tmp, rep)
    check(bool(rep.errors) and "缺少关键锚" in rep.errors[0],
          "P2: 入口缺关键锚 → 校验报错（入口与实现脱节被拦）")


# ---------------------------------------------------------------- B 任务书生成

def test_task_brief_scoring() -> None:
    items = RTB._parse_todo(_ROOT)
    check(len(items) > 0, "B: TODO 待办池可解析")
    top = items[0]
    # r07 前首推是 T-014（评分 90）；任务完成后退池、首推随待办池演化——断言只锁不变式
    check(top["score"] > 0 and top["tid"].startswith("T-"),
          f"B: 首推任务 {top['tid']} 评分 {top['score']} > 0（动态，随待办池演化）")
    check(all(it["tid"] != "T-031" for it in items),
          "B: 已完成项（T-031 ✅）不计入待办评分（只取 [ ] 条目）")
    check(all(items[i]["score"] >= items[i + 1]["score"] for i in range(len(items) - 1)),
          "B: 评分单调降序")


def test_task_brief_render() -> None:
    items = RTB._parse_todo(_ROOT)
    brief = RTB._render_brief(_ROOT, items, 7)
    check("# TASK_BRIEF" in brief and "## 本轮候选" in brief, "B: 任务书结构（候选+判据）")
    check(items[0]["tid"] in brief, f"B: 任务书引用 TODO 原条目 {items[0]['tid']}（可追溯）")


def test_task_brief_top_n_and_resource() -> None:
    items = RTB._parse_todo(_ROOT)
    # --top N：必做数量 = min(top_n, 可用非 resource 候选数)——机制断言而非状态断言：
    # 收尾轮会消耗候选（如 r14 做完 T-053/T-054 后非 resource 待办只剩 T-052），
    # 把「待办池恒 ≥3」当不变式会误报，因此只断言生成器受 top_n 约束且随可用数收敛。
    avail = len([it for it in items if not it.get("resource")])
    brief2 = RTB._render_brief(_ROOT, items, 7, top_n=2)
    brief3 = RTB._render_brief(_ROOT, items, 7)
    must2 = [ln for ln in brief2.splitlines() if ln.strip().startswith("- [ ] **T-")]
    must3 = [ln for ln in brief3.splitlines() if ln.strip().startswith("- [ ] **T-")]
    check(len(must2) == min(2, avail) and len(must3) == min(3, avail)
          and len(must3) >= len(must2),
          f"B: --top N 控制本轮必做任务数（2 与 3，可配置；可用候选 {avail}）")

    # 资源依赖前置：resource 条目被解析并被标注为备选，不占必做
    res_items = [it for it in items if it.get("resource")]
    check(any("external-data" == it["resource"] for it in res_items),
          "B: 资源依赖字段被解析（T-025 external-data）")
    if res_items:
        check("资源缺口型备选" in brief3,
              "B: 资源缺口型任务列入备选段（不占必做预算）")
        check(all(it["tid"] not in must3 for it in res_items),
              "B: 资源缺口型任务不出现在必做段")
    # --score 输出含资源标注
    # （score 分支在 main() 里，这里只验证解析层）
    check(all(it["score"] >= it2["score"] for it, it2 in zip(items, items[1:])),
          "B: 评分单调降序（加 resource 字段后不变式保持）")


# ---------------------------------------------------------------- H/I 护栏

def test_handoff_structure() -> None:
    # 构造：有 manifest 但缺 HANDOFF → 报错
    tmp = tempfile.mkdtemp(prefix="sc_handoff_")
    os.makedirs(os.path.join(tmp, "games", "dlt", "iterations", "round09"), exist_ok=True)
    with open(os.path.join(tmp, "games", "dlt", "iterations", "round09", "manifest.json"),
              "w", encoding="utf-8") as f:
        f.write("{}\n")
    rep = V.ValidationReport()
    V._check_handoff_structure(tmp, rep)
    check(bool(rep.errors) and "缺 HANDOFF.md" in rep.errors[0],
          "H: 已收尾轮有 manifest 无 HANDOFF → 报错")
    # 构造：有 HANDOFF 且含 4+ 段 → 通过（round09 之前缺 HANDOFF 的错误已补全）
    with open(os.path.join(tmp, "games", "dlt", "iterations", "round09", "HANDOFF.md"),
              "w", encoding="utf-8") as f:
        f.write("## 1. 本轮结论清单\n## 2. 遗留问题\n## 3. 下轮建议\n## 4. 风险\n")
    os.makedirs(os.path.join(tmp, "games", "dlt", "iterations", "round08"), exist_ok=True)
    with open(os.path.join(tmp, "games", "dlt", "iterations", "round08", "manifest.json"),
              "w", encoding="utf-8") as f:
        f.write("{}\n")
    with open(os.path.join(tmp, "games", "dlt", "iterations", "round08", "HANDOFF.md"),
              "w", encoding="utf-8") as f:
        f.write("## 1. 本轮结论清单\n## 2. 遗留问题\n## 3. 下轮建议\n## 4. 风险\n")
    rep2 = V.ValidationReport()
    V._check_handoff_structure(tmp, rep2)
    check(not rep2.errors, "H: 结构化 HANDOFF → 通过")


def test_compression_freshness() -> None:
    tmp = tempfile.mkdtemp(prefix="sc_compress_")
    os.makedirs(os.path.join(tmp, "memory", "facts"), exist_ok=True)
    # 当前轮 = 最大**已收尾**轮（round06）。
    # ★ r15：轮号判据已由「目录存在」改为「含 manifest.json」——空壳目录不再算一轮。
    # 夹具必须造一个真收尾轮，否则这里测的是过时的假设。
    os.makedirs(os.path.join(tmp, "games", "dlt", "iterations", "round06"), exist_ok=True)
    with open(os.path.join(tmp, "games", "dlt", "iterations", "round06", "manifest.json"),
              "w", encoding="utf-8") as f:
        f.write('{"round": "r06", "status": "delivered", "outputs": {}}\n')
    with open(os.path.join(tmp, "memory", "facts", "ACTIVE.md"), "w", encoding="utf-8") as f:
        f.write("由 compress_memory.py --write 生成 ｜ 当前轮 round06\n")
    rep = V.ValidationReport()
    V._check_compression_freshness(tmp, rep)
    check(not rep.warnings, "I: 距上次压缩 0 轮 → 无到期警告")
    # 过期场景：round01 → 差 5 轮 → 不警告（>5 才警告）；round00 → 差 6 轮 → 警告
    with open(os.path.join(tmp, "memory", "facts", "ACTIVE.md"), "w", encoding="utf-8") as f:
        f.write("由 compress_memory.py --write 生成 ｜ 当前轮 round01\n")
    rep1 = V.ValidationReport()
    V._check_compression_freshness(tmp, rep1)
    check(not rep1.warnings, "I: 距上次压缩 5 轮 → 边界不警告（>5 才到期）")
    with open(os.path.join(tmp, "memory", "facts", "ACTIVE.md"), "w", encoding="utf-8") as f:
        f.write("由 compress_memory.py --write 生成 ｜ 当前轮 round00\n")
    rep2 = V.ValidationReport()
    V._check_compression_freshness(tmp, rep2)
    check(any("记忆压缩" in w for w in rep2.warnings),
          "I: 距上次压缩 6 轮 → 到期警告（记忆膨胀被看见）")


if __name__ == "__main__":  # pragma: no cover
    test_ai_map_rendered()
    test_ai_map_check_real()
    test_ai_map_check_missing()
    test_ai_entry_completeness_real()
    test_ai_entry_completeness_missing()
    test_task_brief_scoring()
    test_task_brief_render()
    test_task_brief_top_n_and_resource()
    test_handoff_structure()
    test_compression_freshness()
    print(f"\n通过 {_PASS}  失败 {_FAIL}")
    if _FAILURES:
        print("失败项：")
        for f in _FAILURES:
            print(f"  ✗ {f}")
    sys.exit(1 if _FAIL else 0)
