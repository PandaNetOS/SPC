# -*- coding: utf-8 -*-
"""tools/derive_tasks.py — 待办池任务源派生（r16，★源自救）

## 为什么要有这个工具

r15 收尾时待办池被消耗到**可执行候选 = 0**，任务书只能输出「本轮必做 0 个」。
根因不是「事情做完了」，而是**待办池没有补给通道**：

    任务只能靠开轮时人工现想 → 想到什么做什么 → 想不到的永远不做
    → 池子越做越空 → 任务书空转

本工具把三个**已经在仓库里、但没进待办池**的存量变成候选任务：

| 源 | 取什么 | 说明 |
|---|---|---|
| `labs/lottery/studies/dlt/memory/workbench/OPEN_QUESTIONS.md` | 状态 = `open` 的 Q-nnn | 问题本身就是任务定义（含方法/验收判据） |
| `labs/lottery/studies/dlt/memory/workbench/HYPOTHESES.md` | 状态 = `unverified` / `partial` 的 H-nnn | 未验证假设 = 未做的检验 |
| `python cli/main.py validate --all` 的警告 | 按类别归并 | 告警清单即欠账清单 |

## 设计取舍

- **只标来源、不臆造内容**：派生项只写「去做什么 + 出处」，方法/判据一律指向
  原 Q/H 条目，不在待办里二次抄写（抄写会分叉）。
- **幂等**：同一来源（Q-nnn / H-nnn / 告警类别）已在 TODO 中则跳过，
  `--write` 可反复跑。
- **资源缺口型如实标记**：Q/H 若标注外部数据/不可验证，带上 `resource: …`，
  使其按 Z 协议不占轮次预算，而不是混进必做。
- **不自动评分吹高**：value 由来源优先级推导（Q 高 60 / 中 40 / 低 20，
  H 30，告警 20~40），不加成、不置顶。

用法：
    python tools/derive_tasks.py              # 打印派生候选（dry-run）
    python tools/derive_tasks.py --write      # 追加到 TODO.md 的「派生候选」段
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, os.path.join(_ROOT, "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from spc import paths  # noqa: E402 路径单一权威（待办池已随记忆下沉到研究组）

# reconfigure 而非重新包装：重新包装会让原 wrapper 失去引用后被 GC 析构，
# 连带关掉底层 buffer —— 本模块被测试 import 时会导致后续 print 全部失败。
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

_STUDY = paths.first_study(root=_ROOT) or "dlt"
_WB = paths.workbench_dir(_STUDY, root=_ROOT)
TODO = os.path.join(_WB, "TODO.md")
QUESTIONS = os.path.join(_WB, "OPEN_QUESTIONS.md")
HYPOTHESES = os.path.join(_WB, "HYPOTHESES.md")
SECTION = "## 派生候选（由 tools/derive_tasks.py 生成，勿手改条目内容）"


def _wb(root: str | None = None, study: str | None = None) -> str:
    """workbench 目录。

    ★ 为什么要函数而不只用模块常量：模块常量在 import 时绑定到**真实仓库**，
    于是测试/外部工具想把这个模块指向别处时，只能 monkeypatch 三个变量
    （漏一个就静默读到真仓库 —— 用错数据比报错危险）。
    本函数按 root/study 现算；模块常量保留是为向后兼容既有 monkeypatch 用法。
    """
    return paths.workbench_dir(study or paths.first_study(root=root or _ROOT) or "dlt",
                               root=root or _ROOT)


def _paths_for(root: str | None = None, study: str | None = None) -> tuple[str, str, str]:
    """(TODO, QUESTIONS, HYPOTHESES) —— 三者必须同源，禁止各算各的。"""
    wb = _wb(root, study)
    return (os.path.join(wb, "TODO.md"),
            os.path.join(wb, "OPEN_QUESTIONS.md"),
            os.path.join(wb, "HYPOTHESES.md"))

_Q_SEC = re.compile(r"^## (Q-\d{3}) — (.+?)(?:\s*✅.*)?$", re.M)
_H_SEC = re.compile(r"^## (H-\d{3}) — (.+)$", re.M)
_STATE = re.compile(r"^\|\s*\*\*状态\*\*\s*\|\s*`([^`]+)`", re.M)
_PRIO = re.compile(r"^\|\s*\*\*优先级\*\*\s*\|\s*\*{0,2}([高中低][^|]*?)\*{0,2}\s*\|", re.M)

# 告警类别 → (匹配串, 标题, value, 资源约束)
_WARN_RULES = [
    ("动态锚点结论已", "动态锚点结论超期 → 走 update 通道重校准", 30, None),
    ("evidence_index", "策略证据索引未覆盖被引结论 → 补 evidence_index 并重算 evidence_hash", 40, None),
    ("下游声明完整性", "下游文档引用了未登记的结论 → 补 consumes 登记", 40, None),
    ("记忆压缩", "记忆压缩到期 → 跑 compress_memory --write", 20, None),
]


def _q_candidates(root: str | None = None, study: str | None = None) -> list[dict]:
    todo_p, questions_p, _ = _paths_for(root, study)
    # 模块常量被 monkeypatch 时优先用它（向后兼容既有测试用法）
    q_p = QUESTIONS if QUESTIONS != _paths_for(_ROOT, _STUDY)[1] else questions_p
    if not os.path.isfile(q_p):
        return []
    txt = open(q_p, encoding="utf-8").read()
    out = []
    for m in _Q_SEC.finditer(txt):
        qid, title = m.group(1), m.group(2).strip()
        seg = txt[m.end():]
        nxt = _Q_SEC.search(seg)
        body = seg[:nxt.start()] if nxt else seg
        sm = _STATE.search(body)
        if not sm or not sm.group(1).startswith("open"):
            continue
        pm = _PRIO.search(body)
        prio = pm.group(1) if pm else "中"
        value = 60 if prio.startswith("高") else (20 if prio.startswith("低") else 40)
        res = None
        low = body[:600]
        if "external-data" in low or "外部数据" in low or "数据缺口" in low:
            res = "external-data"
        out.append({"src": qid, "kind": "question", "title": f"{qid} {title}",
                    "value": value, "resource": res,
                    "detail": f"出处 `OPEN_QUESTIONS.md` {qid}（方法/验收判据见原条目）"})
    return out


def _h_candidates(root: str | None = None, study: str | None = None) -> list[dict]:
    _, _, hypotheses_p = _paths_for(root, study)
    h_p = HYPOTHESES if HYPOTHESES != _paths_for(_ROOT, _STUDY)[2] else hypotheses_p
    if not os.path.isfile(h_p):
        return []
    txt = open(h_p, encoding="utf-8").read()
    out = []
    for m in _H_SEC.finditer(txt):
        hid, title = m.group(1), m.group(2).strip()
        seg = txt[m.end():]
        nxt = _H_SEC.search(seg)
        body = seg[:nxt.start()] if nxt else seg
        sm = _STATE.search(body)
        if not sm:
            continue
        st = sm.group(1)
        if st.startswith(("refuted", "answered", "superseded")):
            continue
        if "unverifiable" in st:
            res = "unverifiable"
        elif "external-data" in body[:600]:
            res = "external-data"
        else:
            res = None
        note = "（已部分验证，补剩余判据）" if st.startswith("partial") else ""
        out.append({"src": hid, "kind": "hypothesis",
                    "title": f"{hid} {title}{note}", "value": 30, "resource": res,
                    "detail": f"出处 `HYPOTHESES.md` {hid}（可证伪预测与检验方法见原条目）"})
    return out


def _warn_candidates(root: str | None = None) -> list[dict]:
    """跑一次 validate --all，按类别归并告警。失败/超时不致命 —— 只跳过。"""
    r_root = root or _ROOT
    try:
        r = subprocess.run([sys.executable, "-X", "utf8",
                            os.path.join(r_root, "cli", "main.py"),
                            "validate", "--all"],
                           cwd=r_root, capture_output=True, text=True, timeout=600)
    except Exception:
        return []
    text = (r.stdout or "") + (r.stderr or "")
    seen: dict[str, int] = {}
    for line in text.splitlines():
        if not line.startswith("  !"):
            continue
        for key, *_ in _WARN_RULES:
            if key in line:
                seen[key] = seen.get(key, 0) + 1
    out = []
    for key, title, value, res in _WARN_RULES:
        n = seen.get(key, 0)
        if not n:
            continue
        out.append({"src": f"warn:{key}", "kind": "warning",
                    "title": f"{title}（当前 {n} 条）", "value": value,
                    "resource": res,
                    "detail": "出处 `python cli/main.py validate --all` 告警清单"})
    return out


def _existing_sources(todo: str) -> set[str]:
    return set(re.findall(r"\[derive:([\w:\-]+)\]", todo))


def _next_tid(todo: str) -> int:
    ids = [int(x) for x in re.findall(r"\*\*T-(\d{3})\*\*", todo)]
    return (max(ids) if ids else 0) + 1


def _guard_write(path: str, new_text: str) -> None:
    """写前护栏：内容不得比原文件少 20% 以上（防分割逻辑吃掉正文）。

    触发即抛 RuntimeError 并留下 .bak —— 调用方不会写盘，数据不丢。
    """
    import shutil

    if not os.path.isfile(path):
        return
    old_lines = len(open(path, encoding="utf-8-sig").read().splitlines())
    new_lines = len(new_text.splitlines())
    if old_lines >= 10 and new_lines < old_lines * 0.8:
        bak = path + ".guard.bak"
        shutil.copy2(path, bak)
        raise RuntimeError(
            f"拒绝写入 {path}：新内容 {new_lines} 行 < 原有 {old_lines} 行的 80% "
            f"（派生应是追加操作，内容骤降说明逻辑吃掉了正文）。\n"
            f"  原文件已备份到 {bak}，请检查 SECTION 分割逻辑后重试。"
        )


def main(root: str | None = None, study: str | None = None) -> int:
    """派生候选任务。root/study 省略时用真实仓库（模块常量）。

    ★ 传 root 时全部路径同源重算 —— 不会出现「TODO 指向临时仓库、
    QUESTIONS 还指向真仓库」的半迁移状态。
    """
    write = "--write" in sys.argv
    todo_p, _, _ = _paths_for(root, study)
    # 向后兼容：模块常量被 monkeypatch 过就用它
    if TODO != _paths_for(_ROOT, _STUDY)[0]:
        todo_p = TODO
    cands = _q_candidates(root, study) + _h_candidates(root, study) + _warn_candidates(root)
    todo = open(todo_p, encoding="utf-8").read() if os.path.isfile(todo_p) else ""
    known = _existing_sources(todo)
    fresh = [c for c in cands if c["src"] not in known]

    print(f"派生源扫描：Q {len(_q_candidates(root, study))} / H {len(_h_candidates(root, study))}"
          f" / 告警 {len(_warn_candidates(root))}")
    print(f"已在池：{len(cands) - len(fresh)}　新增：{len(fresh)}")
    if not fresh:
        print("（无新增候选，待办池已是最新）")
        return 0

    tid = _next_tid(todo)
    lines = []
    for c in fresh:
        line = f"- [ ] **T-{tid:03d}** value: {c['value']} ★ 派生"
        if c["resource"]:
            line += f" `resource: {c['resource']}`"
        line += f" {c['title']}  [derive:{c['src']}]"
        lines.append(line)
        lines.append(f"      {c['detail']}")
        lines.append("")
        tid += 1

    if not write:
        print("\n".join(lines))
        print("（dry-run，未写；加 --write 追加到 TODO.md 的「派生候选」段）")
        return 0

    block = "\n".join(lines)
    # ★ 写前护栏：派生是**追加**操作。若新内容行数远少于原内容，
    #   说明分割/替换逻辑吃掉了正文 —— 那是一次静默的数据丢失。
    #   宁可拒绝写入并保留备份，也不能把 44 条待办变成 5 条。
    #   （2026-10-13 实测过一次：TODO.md 251 行被写成 5 行，只能从 git 恢复。）
    _guard_write(todo_p, todo)
    if SECTION in todo:
        head, rest = todo.split(SECTION, 1)
        nxt = re.search(r"^## ", rest, re.M)
        if nxt:
            todo = (head + SECTION + rest[:nxt.start()].rstrip() + "\n\n"
                    + block + "\n" + rest[nxt.start():])
        else:
            todo = head + SECTION + rest.rstrip() + "\n\n" + block
    else:
        todo = todo.rstrip() + f"\n\n---\n\n{SECTION}\n\n{block}"
    open(todo_p, "w", encoding="utf-8").write(todo)
    print(f"✓ 已向 TODO.md 追加 {len(fresh)} 条派生候选（标记 [derive:…] 保证幂等）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
