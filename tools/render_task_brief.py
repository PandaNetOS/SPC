# -*- coding: utf-8 -*-
"""tools/render_task_brief.py — 下轮任务书生成器（B+G 升级）。

从 labs/lottery/studies/dlt/memory/workbench/TODO.md 待办池按价值评分排序，生成候选 TOP-N 与
下轮任务书草稿 —— 把「AI 恰好想到挑哪个」变成可机械复核的排序。

评分（B+G：TODO 条目加 value 字段，0-100；无 value 时按 P 级基础分）：
    base：P0=100 / P1=80 / P2=60 / P3=40 / P4=20
    value：显式 `value: N` 直接覆盖基础分（影响面/置信度缺口/可证伪性）
    ★ 首推标记（`★ rNN 首推`）：+10

资源依赖前置（Z 方向）：
    TODO 条目可声明 `resource: <类型>`（如 external-data / unverifiable）——
    资源缺口型任务**不占本批必做预算**（数据就绪前不会把轮次浪费在推不动的事上），
    任务书对它们显式标注 ⚠ 并列入备选，而非必做。

用法：
    python tools/render_task_brief.py [--round NN] [--top N] [--write]
        # 默认下一轮 = 当前最大轮 + 1；--top 控制本轮必做任务数（默认 3）；
        # --write 写 labs/lottery/studies/dlt/iterations/roundNN/TASK_BRIEF.md
    python tools/render_task_brief.py --score   # 只打印评分榜

依据：DOLPHIN（idea 生成→反馈闭环）、主动学习（按不确定性/价值采样）。
"""
from __future__ import annotations

import io
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

_BASE_BY_PRIORITY = {"P0": 100, "P1": 80, "P2": 60, "P3": 40, "P4": 20}
_PRIORITY_RE = re.compile(r"^##\s*(P[0-4])")
_ITEM_RE = re.compile(r"^-\s*\[\s\]\s*\*\*(T-\d{3})\*\*\s*(.*?)(?:\s*★\s*(.*))?$")
_RESOURCE_RE = re.compile(r"resource[:：]\s*([\w\-/]+)")
_DEFAULT_TOP = 3


def _parse_todo(root: str) -> list[dict]:
    p = os.path.join(root, "memory", "workbench", "TODO.md")
    if not os.path.exists(p):
        return []
    items: list[dict] = []
    priority = "P4"
    with open(p, encoding="utf-8") as f:
        for line in f:
            m = _PRIORITY_RE.match(line.strip())
            if m:
                priority = m.group(1)
                continue
            im = _ITEM_RE.match(line.strip())
            if not im:
                continue
            tid, title, star = im.groups()
            value_m = re.search(r"value[:：]\s*(\d{1,3})", line)
            base = _BASE_BY_PRIORITY.get(priority, 40)
            score = int(value_m.group(1)) if value_m else base
            if star and "首推" in star:
                score += 10
            res_m = _RESOURCE_RE.search(line)
            items.append({
                "tid": tid, "title": title.strip(), "priority": priority,
                "star": (star or "").strip(), "score": score,
                "resource": res_m.group(1) if res_m else None,
                "line": line.strip(),
            })
    items.sort(key=lambda it: (-it["score"], it["tid"]))
    return items


def _next_round(root: str) -> int:
    """下一轮号 = 最新**已收尾**轮（该轮目录含 manifest.json）+ 1。

    ★ r15 根治（A2）：此前按「roundNN 目录是否存在」取 max —— 而本工具自己在
    dry-run 时就会 makedirs 目标目录（见 main() 旧实现），于是形成自激回路：
    「跑一次 dry-run → 目录出现 → 下一轮号 +1」。实测两次 dry-run 造出空的
    round15/round16，validate 的重校准警告随之虚增 2 轮（报「当前 round16」）。
    判据必须是**已收尾**（有 manifest），不能是**目录存在**。
    """
    best = 0
    d = os.path.join(root, "games", "dlt", "iterations")
    if os.path.isdir(d):
        for name in os.listdir(d):
            m = re.match(r"^round(\d{2})$", name)
            if m and os.path.isfile(os.path.join(d, name, "manifest.json")):
                best = max(best, int(m.group(1)))
    return best + 1


def _render_brief(root: str, items: list[dict], rnd: int, top_n: int = _DEFAULT_TOP) -> str:
    if top_n < 1:
        top_n = _DEFAULT_TOP
    # 可执行（无资源依赖）优先进入必做；资源缺口型降为备选（Z：不占轮次预算）
    #
    # ★ r15：旧实现在「无可执行候选」时退回 `items[:top_n]` —— 于是把
    # `external-data` / `unverifiable` 的资源缺口型任务**提升为必做**，
    # 正面违背 Z 协议（资源缺口不占轮次预算）。待办池被收尾轮消耗到 0 可执行项
    # 后（r15 勾选 T-052 后正是如此）这条降级路径就会触发，
    # 而它此前从未被走到，所以一直没暴露。无可执行项就如实说 0 个。
    executable = [it for it in items if not it.get("resource")]
    top = executable[:top_n]
    resource_waiting = [it for it in items if it.get("resource")]
    no_executable = not executable

    lines = [
        f"# TASK_BRIEF —— round{rnd:02d} 任务书",
        "",
        f"> 本任务书由 `tools/render_task_brief.py` 从 TODO 待办池按价值评分生成",
        f"> （派生物草稿，人工确认后可改）。本轮必做 **{len(top)}** 个（`--top {top_n}` 可调）。",
        "> 评分依据：TODO 条目 value / P 级 / ★首推。",
        "",
    ]
    # 头部版本行：单一来源 = versions.json 登记（勿手写/硬编码）
    try:
        from spc.versions import registered_version, version_line
        path = f"labs/lottery/studies/dlt/iterations/round{rnd:02d}/TASK_BRIEF.md"
        cv, it, upd = registered_version(root, path)
        if cv:
            lines += ["", version_line(cv, it, upd), ""]
    except ImportError:  # noqa: S110
        pass
    lines += [
        "## 本轮候选（按评分排序 TOP-N）",
        "",
        "| 排序 | 任务 | 优先级 | 评分 | 说明 |",
        "|---|---|---|---|---|",
    ]
    if no_executable:
        lines.append("| — | （无可执行候选） | — | — | 待办池已无非资源缺口型条目 |")
    for i, it in enumerate(top, 1):
        flag = f"⚠ 资源依赖: {it['resource']}" if it.get("resource") else (it["star"] or "")
        lines.append(f"| {i} | {it['tid']} {it['title']} | {it['priority']} | {it['score']} | {flag} |")
    lines += [
        "",
        "## 本轮必做任务（引用 TODO 原条目）",
        "",
    ]
    if no_executable:
        lines += [
            "**本轮无可执行的非资源缺口任务。** 待办池剩余条目全部挂在"
            "`external-data` / `unverifiable` 上（见下方备选段）——"
            "按 Z 协议，资源缺口型不得占用轮次预算，因此本轮不派发研究任务。",
            "",
            "处置建议：① 从 `OPEN_QUESTIONS.md` / `HYPOTHESES.md` 派新任务入池；"
            "② 或做不依赖外部数据的治理/还债项（validate 警告清单即任务源）。",
            "",
        ]
    for it in top:
        src = f"`{it['priority']}` 段（评分 {it['score']}）"
        if it.get("resource"):
            src += f"，⚠ 资源依赖: {it['resource']}"
        lines.append(f"- [ ] **{it['tid']}** —— 来源：`labs/lottery/studies/dlt/memory/workbench/TODO.md` 的 {src}。")
    if resource_waiting:
        lines += [
            "",
            "## ⚠ 资源缺口型备选（不占本批预算，数据就绪后自动进入候选）",
            "",
        ]
        for it in resource_waiting:
            lines.append(
                f"- **{it['tid']}** {it['title']}（评分 {it['score']}）—— 需 `{it['resource']}`，"
                f"当前未就绪，不列为必做。"
            )
    lines += [
        "",
        "## 验收判据",
        "",
        f"1. 本批 {len(top)} 个任务全部完成后更新 FACTS.jsonl（新结论必须过三闸门，带 caveats）；",
        "2. `python cli/main.py validate --all` 全绿；",
        "3. 收轮四件套 + 版本登记 + 下轮任务书。",
        "",
    ]
    # X 协议：并行研究建议（研究可并行，入库串行过三闸门）
    parallel = [it for it in top if not it.get("resource")]
    if len(parallel) >= 2:
        lines += [
            "## 并行研究建议（X 协议，见 ITERATION_SOP_v2 §9）",
            "",
            f"本批有 **{len(parallel)}** 个可执行任务（无资源缺口）互不依赖，可并行研究：",
            "",
        ]
        for it in parallel:
            lines.append(f"- {it['tid']} {it['title']}")
        lines += [
            "",
            "约束：① 各任务独立研究、各自出草案；② **入库必须串行过三闸门**（INV1/2/3 不豁免）；",
            "③ 共享文档（FACTS/STRATEGY_GUIDE/strategy.json）在汇合后统一串行更新，避免并发写冲突；",
            "④ 收尾统一跑 `tools/finish_round.py`。",
            "",
        ]
    return "\n".join(lines)


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    rnd = _next_round(_ROOT)
    if "--round" in sys.argv:
        i = sys.argv.index("--round")
        rnd = int(sys.argv[i + 1])
    top_n = _DEFAULT_TOP
    if "--top" in sys.argv:
        i = sys.argv.index("--top")
        top_n = int(sys.argv[i + 1])
    items = _parse_todo(_ROOT)
    if not items:
        print("TODO.md 无待办条目（或未按 T-nnn 格式），无法生成任务书。")
        return 1

    if "--score" in sys.argv:
        print("TODO 待办评分榜：")
        for it in items:
            res = f"  [资源:{it['resource']}]" if it.get("resource") else ""
            print(f"  {it['tid']} [{it['priority']}] 评分 {it['score']:>3}  {it['title']}{res}")
        return 0

    brief = _render_brief(_ROOT, items, rnd, top_n)
    out = os.path.join(_ROOT, "games", "dlt", "iterations", f"round{rnd:02d}", "TASK_BRIEF.md")
    # ★ r15 根治（A1）：makedirs 曾在本函数无条件执行（早于 --write 判断），
    # 于是 dry-run 也会建出 roundNN 空目录，进而经 _next_round 把轮号推高。
    # 派生物的产出目录只能在**真的要写**时创建。
    if "--write" in sys.argv:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(brief)
        print(f"✓ 已写 {os.path.relpath(out, _ROOT)}（必做 {top_n} 条，可执行优先）")
        return 0
    print(brief)
    print(f"（dry-run，未写；加 --write 写入 round{rnd:02d}/TASK_BRIEF.md）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
