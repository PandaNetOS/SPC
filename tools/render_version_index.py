# -*- coding: utf-8 -*-
"""render_version_index.py — 从 versions.json 生成 VERSION_INDEX.md

用法：
    python tools/render_version_index.py            # 打印
    python tools/render_version_index.py --write    # 写盘

设计：**VERSION_INDEX.md 是 versions.json 的派生物**，严禁手改。
权威源是 versions.json（受 spec/version_index.schema.json 约束）。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

# ⚠️ 仅在作为脚本直接运行时替换 stdout（被 import 时不得有副作用）
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

LEVEL_TITLES = {
    "A": "A 级 · 结论性内容",
    "B": "B 级 · 结构性文档 / 框架与库代码",
    "C": "C 级 · 机器契约（用自身既有版本字段）",
    "D": "D 级 · 纯数据 / 分析脚本（不版本化）",
}


def gen() -> str:
    d = json.load(open(os.path.join(_ROOT, "versions.json"), encoding="utf-8"))
    E = d["entries"]
    out: list[str] = []

    out.append("# VERSION_INDEX.md — 仓库版本索引")
    out.append("")
    out.append("> **本文件由 `python tools/render_version_index.py --write` 从 `versions.json` 自动生成。请勿手工编辑。**")
    out.append("> 权威源是 `versions.json`（受 `spec/version_index.schema.json` 约束）。")
    out.append("")
    out.append(f"**索引版本**：`{d['index_version']}` ｜ **框架版本**：`{d['framework_version']}` ｜ "
               f"**实验室版本**：`{d.get('domain_version')}` ｜ "
               f"**顶层版本（release）**：`{d.get('project_version')}` ｜ "
               f"**当前轮次**：`{d['current_iteration']}` ｜ **生成日期**：{d['generated_at']}")
    out.append("")
    out.append("---")
    out.append("")

    # ---------- 0. AI 一分钟版
    out.append("## 0. AI 一分钟版（先读这里）")
    out.append("")
    out.append("**这套版本号要回答的问题是：**")
    out.append("")
    out.append("> 我手里这份内容，是**哪个版本**、**哪一轮产出的**、**改过几次**？")
    out.append("")
    out.append("**四个版本号并存，各答不同问题 —— 不可互相替代：**")
    out.append("")
    out.append("| 版本号 | 答什么问题 | 谁拥有 | 位置 |")
    out.append("|---|---|---|---|")
    out.append("| `schema_version` | 契约**结构**长什么样 | `spec/` | `strategy.json` |")
    out.append("| `config_version` | 彩种**参数**是什么版本 | `games/<id>/` | `game.yaml` |")
    out.append("| `data_version` | 用了**哪份数据** | `data/raw/` | `game.yaml` / manifest |")
    out.append(f"| **`content_version`** ★ | **这份内容改过几版** | **每份内容自己** | **文件内版本行 + 本索引** |")
    out.append(f"| **`framework_version`** ★ | **框架层改过几版** | **`platform/`** | **本索引** |")
    out.append(f"| **`project_version`** ★ | **SPC 整体 release 版本** | **整个包** | **本索引 + pyproject.toml** |")
    out.append("")
    out.append("★ = 本次（2026-10-11）新引入。此前全仓库**没有**「内容版本」与「框架版本」的概念。")
    out.append("")
    out.append("**实例（说明为何不冲突）**：`strategy.json` 的 `schema_version` 可以一直是 `1.0`，")
    out.append("而 `content_version` 从 `1.0` 升到 `1.1` —— 因为**契约结构没动，但规则幅度改了**。")
    out.append("")
    out.append("**版本号格式**：`<主>.<次>`，如 `1.1`。")
    out.append("")
    out.append("- **主** +1：结构变更 / 立场变更 / 破坏性变更（须单独评审）")
    out.append("- **次** +1：内容增补、结论新增、幅度修正")
    out.append("")
    out.append("> 与 `spec/VERSIONING.md` 的三段式（`x.y`）规则一致。")
    out.append("> 轮次归属记在 `iteration` 字段（`r01`/`r02`/…），**不塞进版本号** ——")
    out.append("> 因为同一版本可能跨多轮才定稿，把轮次编码进版本号会造成 `1.0.r02` → `1.0.r03` 的假升级。")
    out.append("")
    out.append("---")
    out.append("")

    # ---------- 1. 分级定义
    out.append("## 1. 四级分区")
    out.append("")
    out.append("**不是所有文件都需要版本号。** 分级依据是「这份内容重复写错的代价有多高」。")
    out.append("")
    out.append("| 级别 | 名称 | 版本化 | 字段 | 判定理由 | 数量 |")
    out.append("|---|---|---|---|---|---|")
    for lvl in "ABCD":
        meta = d["levels"][lvl]
        n = sum(1 for e in E if e["level"] == lvl)
        ver = "✅" if meta["versioned"] else "❌"
        out.append(f"| **{lvl}** | {meta['name']} | {ver} | "
                   f"{('`' + meta['field'] + '`') if meta['field'] else '—'} | "
                   f"{meta['reason']} | {n} |")
    out.append("")
    out.append("**为什么 D 级（数据）不版本化**：`data/raw/` 已有 **SHA256**，")
    out.append("那是**比版本号更强的完整性保证** —— 版本号只能告诉你「变了」，")
    out.append("SHA256 能告诉你「**具体哪里**变了」。给数据加版本号是双重记账。")
    out.append("")
    out.append("**为什么 B 级的 `.py` 不写文件内版本行**：代码的版本信息由 `git blame` 提供，")
    out.append("且远比手写版本行精确。在代码里加注释版本行是纯噪音。")
    out.append("")
    out.append("---")
    out.append("")

    # ---------- 2. 逐级清单
    out.append("## 2. 全量文件版本表")
    out.append("")
    for lvl in "ABCD":
        rows = [e for e in E if e["level"] == lvl]
        if not rows:
            continue
        out.append(f"### {LEVEL_TITLES[lvl]}")
        out.append("")

        if lvl == "A":
            out.append("| 路径 | 版本 | 轮次 | 更新日 | 状态 | 备注 |")
            out.append("|---|---|---|---|---|---|")
            for e in rows:
                out.append(
                    f"| `{e['path']}` | `{e.get('content_version') or '—'}` "
                    f"| `{e.get('iteration') or '—'}` | {e.get('updated_at') or '—'} "
                    f"| {e.get('status', 'active')} | {e.get('note') or ''} |"
                )
        elif lvl == "B":
            out.append("| 路径 | 版本 | 轮次 | 状态 | 备注 |")
            out.append("|---|---|---|---|---|")
            for e in rows:
                cv = e.get("content_version")
                out.append(
                    f"| `{e['path']}` | {('`' + cv + '`') if cv else '—（见备注）'} "
                    f"| `{e.get('iteration') or '—'}` | {e.get('status', 'active')} "
                    f"| {e.get('note') or ''} |"
                )
        elif lvl == "C":
            out.append("| 路径 | 版本字段 | 值 | 备注 |")
            out.append("|---|---|---|---|")
            for e in rows:
                out.append(
                    f"| `{e['path']}` | `{e.get('version_ref') or '—'}` "
                    f"| `{e.get('ref_version') or '—'}` | {e.get('note') or ''} |"
                )
        else:
            out.append("| 路径 | 类型 | SHA256（raw） | 备注 |")
            out.append("|---|---|---|---|")
            for e in rows:
                sh = e.get("sha256")
                out.append(
                    f"| `{e['path']}` | `{e['kind']}` "
                    f"| {('`' + sh[:16] + '…`') if sh else '—'} | {e.get('note') or ''} |"
                )
        out.append("")

    out.append("---")
    out.append("")

    # ---------- 3. 按类型检索
    out.append("## 3. 按内容类型检索")
    out.append("")
    by_kind: dict[str, list[dict]] = {}
    for e in E:
        by_kind.setdefault(e["kind"], []).append(e)
    out.append("| 类型 | 数量 | 级别 | 文件 |")
    out.append("|---|---|---|---|")
    for k in sorted(by_kind, key=lambda x: (-len(by_kind[x]), x)):
        rows = by_kind[k]
        lvls = "/".join(sorted({r["level"] for r in rows}))
        paths = "<br>".join(f"`{r['path']}`" for r in rows)
        out.append(f"| `{k}` | {len(rows)} | {lvls} | {paths} |")
    out.append("")
    out.append("---")
    out.append("")

    # ---------- 4. 演化史
    out.append("## 4. 版本演化史")
    out.append("")
    out.append("> 追加式，**不删历史行**。")
    out.append("")
    out.append("| 版本 | 日期 | 范围 | 变更 |")
    out.append("|---|---|---|---|")
    for h in d.get("history", []):
        out.append(f"| `{h['version']}` | {h['date']} | {h.get('scope') or '—'} | {h['change']} |")
    out.append("")
    out.append("---")
    out.append("")

    # ---------- 5. 维护规则
    out.append("## 5. 维护规则")
    out.append("")
    out.append("### 5.1 改内容时（谁改谁升）")
    out.append("")
    out.append("| 你做了什么 | 版本怎么动 |")
    out.append("|---|---|")
    out.append("| 新增一条结论 / 新增一条教训 | `labs/lottery/studies/dlt/memory/facts/FACTS.jsonl` 次版本 +1 |")
    out.append("| 改了策略规则的幅度 | `strategy.json` 的 `content_version` 次版本 +1（`schema_version` **不动**） |")
    out.append("| 改了 `game.yaml` 的玩法/特征 | `config_version` 次版本 +1 |")
    out.append("| 改了框架协议 / 方法论 / core | `framework_version` 视情况 +1（结构变更升主版本） |")
    out.append("| 新增一轮迭代 | 新目录，各文件 `content_version` 从 `1.0` 起，`iteration` 记新轮次 |")
    out.append("| 改了某份文档的表述 | 该文档次版本 +1（**禁止静默改**） |")
    out.append("")
    out.append("### 5.2 禁止事项")
    out.append("")
    out.append("| 禁止 | 后果 |")
    out.append("|---|---|")
    out.append("| 手改 `VERSION_INDEX.md` | 会被下次生成覆盖（它是派生物） |")
    out.append("| 手改 `versions.json` 而不改对应文件 | `cli/main.py versions` 会报不一致 |")
    out.append("| 改内容但不升版本 | 索引记录的是**错的**，比没有索引更坏 |")
    out.append("| 把轮次编码进版本号 | 造成假升级（见 §0） |")
    out.append("| 给 D 级数据加版本号 | 与 SHA256 双重记账 |")
    out.append("")
    out.append("### 5.3 三条自检命令")
    out.append("")
    out.append("```bash")
    out.append("# 1) 版本一致性（文件内版本行 ↔ versions.json ↔ VERSION_INDEX.md）")
    out.append("python cli/main.py versions")
    out.append("")
    out.append("# 2) 重新生成本索引（改完 versions.json 后）")
    out.append("python tools/render_version_index.py --write")
    out.append("")
    out.append("# 3) 全量校验（含版本检查）")
    out.append("python cli/main.py validate --all -v")
    out.append("```")
    out.append("")
    out.append("---")
    out.append("")

    # ---------- 6. AI 读取顺序
    out.append("## 6. AI 读取顺序（带版本意识）")
    out.append("")
    out.append("```")
    out.append("1. AI_CONTEXT.md                       ← 单一入口")
    out.append("2. VERSION_INDEX.md §0 + §2-A          ← ★ 先知道『我读的是哪一版』")
    out.append("3. labs/lottery/studies/dlt/memory/lessons/LESSONS.md           ← 禁令（记 L1–L9）")
    out.append("4. games/<g>/iterations/roundNN/TASK_BRIEF.md  ← 这轮做什么")
    out.append("5. labs/lottery/studies/dlt/memory/facts/INDEX.md               ← 结论速览")
    out.append("6. labs/lottery/studies/dlt/memory/workbench/{OPEN_QUESTIONS,HYPOTHESES,TODO}.md")
    out.append("7. labs/lottery/studies/dlt/memory/facts/FACTS.jsonl            ← 精确数字（引用前必读 caveats）")
    out.append("```")
    out.append("")
    out.append("**第 2 步是本次新增的**。它的价值：")
    out.append("")
    out.append("- 如果 `FACTS.jsonl` 的 `content_version` 与你在别处看到的引用不符 → **别处的引用已过期**")
    out.append("- 如果 `framework_version` 是别处未记录的版本 → 框架已变，**旧结论的适用条件可能已失效**")
    out.append("- `iteration` 告诉你这份内容最后一次动是哪一轮 → **判断新鲜度**")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 7. 一句话")
    out.append("")
    out.append("> **版本号不是给文件贴标签，是给「引用」定锚点。**")
    out.append(">")
    out.append("> 一份内容若无法被引用者确认「我读的是哪一版」，")
    out.append("> 它就已经在无人察觉的情况下开始漂移 —— 这正是本索引要防的事。")
    out.append("")

    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    text = gen()
    if args.write:
        p = os.path.join(_ROOT, "VERSION_INDEX.md")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"✓ 已写 VERSION_INDEX.md（{len(text)} 字符）")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
