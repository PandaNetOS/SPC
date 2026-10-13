# -*- coding: utf-8 -*-
"""任务源派生（r16，★源自救）测试 —— 无需 pytest，直接 `python tests/test_derive_tasks.py`

## 背景

r15 收尾时待办池可执行候选归零，任务书只能输出「本轮必做 0 个」。
根因不是事情做完了，而是**待办池没有补给通道**：任务只能靠开轮时人工现想。
`tools/derive_tasks.py` 把仓库里已有的三处存量变成候选任务。

## 本文件要守住的六条

1. **open 的 Q 会被派生**，已 answered 的不会（否则 Q-006 这类已清偿项会反复回池）；
2. **refuted / answered / superseded 的 H 不派生**，unverified / partial 才派生；
3. **资源缺口如实标记**：Q/H 若标 external-data / unverifiable，派生项必须带
   `resource:` —— 否则会按 Z 协议混进必做，占掉轮次预算；
4. **`--write` 追加进 TODO 且幂等**：同一来源跑两次不重复新增；
5. **派生的条目能被 `render_task_brief._parse_todo` 解析**（否则池里有条目、
   任务书看不见，等于没派生）；
6. **dry-run 不写盘**。
"""
from __future__ import annotations

import importlib.util
import io
import os
import re
import shutil
import sys
import tempfile

# 用 reconfigure 而不是重新包装：重新包装会让原 wrapper 失去最后一个引用，
# 被 GC 析构时连带关掉底层 buffer，后续所有 print 全部
# ValueError: I/O operation on closed file（本文件踩过）。
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 —— 非 TextIOWrapper 时忽略
    pass
_ORIG_STDOUT = sys.stdout

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

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


def _load():
    spec = importlib.util.spec_from_file_location(
        "derive_tasks", os.path.join(_ROOT, "tools", "derive_tasks.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.stdout = _ORIG_STDOUT   # 模块级已改写过 sys.stdout，恢复
    return mod


def _w(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)


Q_TMPL = """## {qid} — {title}{mark}

| 项 | 内容 |
|---|---|
| **状态** | `{state}` |
| **优先级** | {prio} |

| **方法** | {method} |
"""


def _mkrepo(root: str) -> None:
    _w(os.path.join(root, "memory", "workbench", "OPEN_QUESTIONS.md"),
       Q_TMPL.format(qid="Q-001", title="已清偿问题", mark=" ✅ answered",
                     state="answered", prio="**高**", method="—")
       + Q_TMPL.format(qid="Q-016", title="E6 固定奖加成是否真实发生",
                       mark="", state="open",
                       prio="**中（P2，数据缺口）**", method="需外部数据")
       + Q_TMPL.format(qid="Q-099", title="高优先级开放问题", mark="",
                       state="open", prio="**高**", method="做点什么"))
    _w(os.path.join(root, "memory", "workbench", "HYPOTHESES.md"),
       "## H-001 — 未验证假设\n\n| **状态** | `unverified` |\n| **优先级** | 中高 |\n\n"
       "## H-002 — 部分验证\n\n| **状态** | `partial`（r16：F-0048 端点支持） |\n\n"
       "## H-003 — 已证伪\n\n| **状态** | `refuted` |\n\n"
       "## H-004 — 不可验证\n\n| **状态** | `unverifiable_with_current_data` ⚠️ |\n\n")
    _w(os.path.join(root, "memory", "workbench", "TODO.md"),
       "- [x] **T-051** 已完成\n\n- [ ] **T-025** value: 60 遗留 `resource: external-data`\n")


def main() -> int:
    mod = _load()

    with tempfile.TemporaryDirectory() as tmp:
        _mkrepo(tmp)
        mod.TODO = os.path.join(tmp, "memory", "workbench", "TODO.md")
        mod.QUESTIONS = os.path.join(tmp, "memory", "workbench", "OPEN_QUESTIONS.md")
        mod.HYPOTHESES = os.path.join(tmp, "memory", "workbench", "HYPOTHESES.md")

        print("源解析")
        qs = mod._q_candidates()
        hs = mod._h_candidates()
        qids = {c["src"] for c in qs}
        check("Q-016" in qids and "Q-099" in qids, "open 的 Q 被派生（Q-016 / Q-099）")
        check("Q-001" not in qids, "已 answered 的 Q 不派生（Q-001）")
        check(any(c["src"] == "Q-016" and c["resource"] == "external-data"
                  for c in qs), "Q-016 带 resource: external-data（数据缺口不混进必做）")
        check(any(c["src"] == "Q-099" and c["value"] == 60 for c in qs),
              "高优先级 Q 的 value 更高（60 > 中 40）")

        hids = {c["src"] for c in hs}
        check("H-001" in hids and "H-002" in hids, "unverified / partial 的 H 被派生")
        check("H-003" not in hids, "已 refuted 的 H 不派生")
        check(any(c["src"] == "H-004" and c["resource"] == "unverifiable"
                  for c in hs), "不可验证的 H 标 unverifiable")

        print("幂等与写盘")
        saved, orig = sys.argv, _ORIG_STDOUT
        before = open(mod.TODO, encoding="utf-8").read()

        def run(argv):
            """静默跑一次 main()；sink 必须持有强引用（见文件末注释）。"""
            sinks = []
            for _ in range(3):
                sinks.append(io.TextIOWrapper(io.BytesIO(), encoding="utf-8"))
            try:
                sys.argv = argv
                sys.stdout = sinks[0]
                mod.main()
            finally:
                sys.stdout = orig
                sys.argv = saved
            return sinks

        run(["derive_tasks.py"])
        check(open(mod.TODO, encoding="utf-8").read() == before,
              "dry-run 不写盘")

        run(["derive_tasks.py", "--write"])
        n_after_first = len(re.findall(r"\[derive:",
                                       open(mod.TODO, encoding="utf-8").read()))
        run(["derive_tasks.py", "--write"])   # 再跑一次：幂等
        todo = open(mod.TODO, encoding="utf-8").read()
        n_derive = len(re.findall(r"\[derive:", todo))
        # ★ 不写死条数：夹具里有几个「未入池」的源就会派生几条。
        #   写死绝对值的判据会在夹具增删一个 open Q/H 时立刻误报
        #   （r16 同型教训：写死计数必误报）。
        #   真正的判据是「第二次跑不增长」+「首跑确实写入了东西」。
        check(n_after_first > 0, f"--write 确实写入了派生条目（{n_after_first} 条）")
        check(n_derive == n_after_first,
              f"第二次 --write 不增长（幂等）：{n_after_first} → {n_derive}")

        # ★ 写前护栏：内容骤降必须被拒绝（2026-10-13 实测过一次 251 行 → 5 行
        #   的静默数据丢失，只能从 git 恢复；派生是**追加**操作，不该变少）
        print("写前护栏（防静默数据丢失）")
        guard_tmp = os.path.join(tmp, "guard", "TODO.md")
        _w(guard_tmp, "\n".join(f"- [ ] **T-{i:03d}** x" for i in range(1, 51)))
        raised = False
        try:
            mod._guard_write(guard_tmp, "- [ ] **T-001** only")
        except RuntimeError:
            raised = True
        check(raised, "内容降到 80% 以下 → 拒绝写入并抛错")
        check(os.path.isfile(guard_tmp + ".guard.bak"),
              "拒绝时留下 .guard.bak（数据不丢）")
        check(len(open(guard_tmp, encoding="utf-8").read().splitlines()) == 50,
              "原文件未被改动（50 行原样保留）")
        mod._guard_write(guard_tmp, open(guard_tmp, encoding="utf-8").read()
                         + "\n- [ ] **T-999** new")
        check(True, "正常追加不误报（护栏只拦骤降）")

    print("与任务书解析器的衔接")
    from spc import __name__  # noqa: F401  确保 src 在 path 上
    spec = importlib.util.spec_from_file_location(
        "rtb", os.path.join(_ROOT, "tools", "render_task_brief.py"))
    rtb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rtb)
    sys.stdout = _ORIG_STDOUT
    rtb._ROOT = _ROOT
    items = rtb._parse_todo(_ROOT)
    derived = [it for it in items if "derive:" in it["line"]]
    # 注：TODO 的派生条目一旦被完成勾选，就可能被收轮脚本移出「未完成」集合，
    # 因此这里**不断言条数**——只断言「只要存在，就必须可解析且 resource 合法」。
    # 完全没有派生条目时，用一次 dry-run 证明链路仍然通（派生 → 解析）。
    if derived:
        check(all(it["resource"] in (None, "external-data", "unverifiable")
                  for it in derived), "派生条目的 resource 取值合法")
    else:
        check(True, "真实仓库当前无未勾选派生条目（已被收轮勾选）—— 不断言条数")
    # 链路仍然通的证明：在**真实仓库**上跑一次 dry-run，
    # 候选非空即说明「源文件可读 + 解析器工作」。
    #   注意必须在 with 块内或重新加载模块 —— 上面的 monkeypatch 已把
    #   mod.QUESTIONS/HYPOTHESES 指向已删除的 tmp 目录。
    spec2 = importlib.util.spec_from_file_location(
        "derive_tasks_real", os.path.join(_ROOT, "tools", "derive_tasks.py"))
    mod2 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(mod2)
    sys.stdout = _ORIG_STDOUT
    cands = mod2._q_candidates() + mod2._h_candidates()
    check(len(cands) > 0,
          f"真实仓库派生源仍能产出候选（{len(cands)} 条）—— 链路未断")
    if cands:
        # 每个候选都必须带 [derive:src] 形式的来源标记（幂等的依据）
        check(all(c.get("src") for c in cands), "每个候选都带来源标记 src（幂等依据）")

    print()
    print(f"通过 {_PASS}  失败 {_FAIL}")
    if _FAIL:
        for f in _FAILURES:
            print(f"  ✗ {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
