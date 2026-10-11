# -*- coding: utf-8 -*-
"""framework/tools/memory.py — 记忆层读写库（彩种无关）

提供 FACTS.jsonl / LESSONS.md / workbench 的程序化读写接口。

设计原则：
  1. **追加式写入**：新结论追加到文件末尾，不重排（git diff 干净）
  2. **id 永不复用**：`next_fact_id()` 只看当前最大值 +1
  3. **演化链双向一致**：`supersede()` 同时改两条
  4. **红线强制**：写入前检查 affects_win_probability 恒为 False

用法：
    from framework.tools.memory import Memory

    mem = Memory("D:/PNOS/spc")
    mem.load_facts()
    mem.add_fact({...})                   # 追加新结论
    mem.supersede("F-0007", "F-0006")     # 建立取代关系（双向）
    mem.render_index()                    # 重生成 INDEX.md
    mem.validate_facts()                  # 一致性校验
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

# ---------------------------------------------------------------- 常量

FACT_ID_RE = re.compile(r"^F-(\d{4})$")
QUESTION_ID_RE = re.compile(r"^Q-(\d{3})$")
LESSON_ID_RE = re.compile(r"^L-(\d+)$")

RED_LINE_FIELD = "affects_win_probability"

FACT_REQUIRED = [
    "id", "game", "claim", "status", "confidence", "category",
    "affects_win_probability", "evidence", "established_in",
    "supersedes", "superseded_by", "source", "created_at",
]

VALID_STATUS = {"established", "tentative", "refuted", "superseded"}

VALID_CATEGORY = {
    "probability", "fairness", "structure_preference", "predictability",
    "prize_mechanism", "sales_external", "methodology", "rules_scope",
}


# ---------------------------------------------------------------- 异常

class MemoryError(Exception):
    """记忆层操作错误。"""


class RedLineViolation(MemoryError):
    """违反红线：affects_win_probability 必须为 False。"""


# ---------------------------------------------------------------- 主类

class Memory:
    """记忆层读写器。

    repo_root: 仓库根目录（含 memory/ 的那一级）
    """

    def __init__(self, repo_root: str):
        self.root = os.path.abspath(repo_root)
        self.mem_dir = os.path.join(self.root, "memory")
        self.facts_path = os.path.join(self.mem_dir, "facts", "FACTS.jsonl")
        self.index_path = os.path.join(self.mem_dir, "facts", "INDEX.md")
        self.lessons_path = os.path.join(self.mem_dir, "lessons", "LESSONS.md")
        self.workbench_dir = os.path.join(self.mem_dir, "workbench")
        self.journal_dir = os.path.join(self.mem_dir, "journal")
        self.games_dir = os.path.join(self.root, "games")
        self._facts: list[dict] | None = None

    # -------------------------------------------------- FACTS 读

    def load_facts(self, reload: bool = False) -> list[dict]:
        """读入全部结论。结果缓存；reload=True 强制重读。"""
        if self._facts is not None and not reload:
            return self._facts
        if not os.path.exists(self.facts_path):
            self._facts = []
            return self._facts

        facts: list[dict] = []
        with open(self.facts_path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise MemoryError(
                        f"{self.facts_path}:{lineno} JSON 解析失败: {e}"
                    ) from e
                obj["__line__"] = lineno
                facts.append(obj)
        self._facts = facts
        return facts

    def fact(self, fact_id: str) -> dict | None:
        for f in self.load_facts():
            if f["id"] == fact_id:
                return f
        return None

    def facts_by(self, **kw) -> list[dict]:
        """按字段筛选。例：facts_by(game='dlt', status='established')"""
        out = []
        for f in self.load_facts():
            if all(f.get(k) == v for k, v in kw.items()):
                out.append(f)
        return out

    def next_fact_id(self) -> str:
        """最大编号 +1。**永不复用**已删除的编号（本仓库禁止删除结论）。"""
        nums = []
        for f in self.load_facts():
            m = FACT_ID_RE.match(f.get("id", ""))
            if m:
                nums.append(int(m.group(1)))
        return f"F-{max(nums) + 1:04d}" if nums else "F-0001"

    # -------------------------------------------------- FACTS 写

    def add_fact(self, fact: dict, auto_id: bool = True) -> str:
        """追加一条结论。返回其 id。

        校验：
          - 红线 affects_win_probability 必须为 False
          - status / category 合法
          - confidence 在 1..5
          - 必填字段齐全
          - source 文件真实存在
        """
        fact = dict(fact)

        if auto_id and not fact.get("id"):
            fact["id"] = self.next_fact_id()

        # 红线（先查，因为这个最重要）
        if fact.get(RED_LINE_FIELD) is not False:
            raise RedLineViolation(
                f"{fact.get('id')}: {RED_LINE_FIELD} 必须为 False（红线）。"
                f"选号方式在数学上不可能改变中奖概率。"
                f"当前值 = {fact.get(RED_LINE_FIELD)!r}"
            )

        # 重复 id
        if self.fact(fact["id"]) is not None:
            raise MemoryError(f"{fact['id']} 已存在。结论 id 永不复用，请用 next_fact_id()")

        # 必填
        missing = [k for k in FACT_REQUIRED if k not in fact]
        if missing:
            raise MemoryError(f"{fact['id']}: 缺少必填字段 {missing}")

        # 枚举
        if fact["status"] not in VALID_STATUS:
            raise MemoryError(f"{fact['id']}: status={fact['status']!r} 非法")
        if fact["category"] not in VALID_CATEGORY:
            raise MemoryError(f"{fact['id']}: category={fact['category']!r} 非法")
        if not isinstance(fact["confidence"], int) or not 1 <= fact["confidence"] <= 5:
            raise MemoryError(f"{fact['id']}: confidence 必须为 1..5 的整数")

        # source 存在性
        src = fact.get("source", "")
        if src and not os.path.exists(os.path.join(self.root, src)):
            raise MemoryError(
                f"{fact['id']}: source 指向不存在的文件: {src}\n"
                f"  仓库根 = {self.root}"
            )

        # 追加写入（单行 JSON，UTF-8 无 BOM）
        os.makedirs(os.path.dirname(self.facts_path), exist_ok=True)
        line = json.dumps(fact, ensure_ascii=False, sort_keys=False)
        with open(self.facts_path, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")

        self._facts = None  # 使缓存失效
        return fact["id"]

    def supersede(self, old_id: str, new_id: str, note: str | None = None) -> None:
        """建立取代关系：old → superseded，new.supersedes = old。**双向一致**。

        本方法会**重写整个 FACTS.jsonl**（因为要改旧行）。
        但只改动这两条的对应字段，其它行原样保留（保持 diff 最小）。
        """
        facts = self.load_facts(reload=True)
        old = self.fact(old_id)
        new = self.fact(new_id)
        if old is None:
            raise MemoryError(f"{old_id} 不存在")
        if new is None:
            raise MemoryError(f"{new_id} 不存在")
        if new.get("supersedes") not in (None, old_id):
            raise MemoryError(
                f"{new_id}.supersedes 已为 {new['supersedes']!r}，"
                f"不能改为 {old_id}（一条结论只能取代一条）"
            )

        old["status"] = "superseded"
        old["superseded_by"] = new_id
        new["supersedes"] = old_id
        if note:
            new.setdefault("caveats", [])
            new["caveats"].append(f"取代 {old_id}：{note}")

        self._rewrite_facts(facts)

    def refute(self, fact_id: str, reason: str) -> None:
        """把某条标为 refuted，并把理由追加到 caveats。**不删除**。"""
        facts = self.load_facts(reload=True)
        f = self.fact(fact_id)
        if f is None:
            raise MemoryError(f"{fact_id} 不存在")
        f["status"] = "refuted"
        f.setdefault("caveats", [])
        f["caveats"].append(f"已推翻：{reason}")
        self._rewrite_facts(facts)

    def _rewrite_facts(self, facts: list[dict]) -> None:
        """重写 FACTS.jsonl（去掉内部 __line__ 字段）。"""
        lines = []
        for f in facts:
            f = {k: v for k, v in f.items() if k != "__line__"}
            lines.append(json.dumps(f, ensure_ascii=False, sort_keys=False))
        with open(self.facts_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        self._facts = None

    # -------------------------------------------------- 校验

    def validate_facts(self) -> list[str]:
        """一致性校验。返回错误列表（空 = 通过）。"""
        errs: list[str] = []
        try:
            facts = self.load_facts(reload=True)
        except MemoryError as e:
            return [str(e)]

        ids = [f.get("id") for f in facts]

        # 重复 id
        seen: set[str] = set()
        for i in ids:
            if i in seen:
                errs.append(f"重复 id: {i}")
            seen.add(i)

        by_id = {f["id"]: f for f in facts}

        for f in facts:
            fid = f.get("id", "<no-id>")

            # 红线
            if f.get(RED_LINE_FIELD) is not False:
                errs.append(f"{fid}: 红线违反 {RED_LINE_FIELD}={f.get(RED_LINE_FIELD)!r}")

            # 必填 / 枚举
            for k in FACT_REQUIRED:
                if k not in f:
                    errs.append(f"{fid}: 缺少字段 {k}")
            if f.get("status") not in VALID_STATUS:
                errs.append(f"{fid}: status={f.get('status')!r} 非法")
            if f.get("category") not in VALID_CATEGORY:
                errs.append(f"{fid}: category={f.get('category')!r} 非法")
            c = f.get("confidence")
            if not isinstance(c, int) or not 1 <= c <= 5:
                errs.append(f"{fid}: confidence={c!r} 非法")

            # source 存在
            src = f.get("source")
            if src and not os.path.exists(os.path.join(self.root, src)):
                errs.append(f"{fid}: source 不存在: {src}")

            # supersede 双向
            sb, ss = f.get("superseded_by"), f.get("supersedes")
            if sb:
                if sb not in by_id:
                    errs.append(f"{fid}: superseded_by={sb} 不存在")
                elif by_id[sb].get("supersedes") != fid:
                    errs.append(
                        f"{fid}: 双向不一致 — {sb}.supersedes="
                        f"{by_id[sb].get('supersedes')!r}，应为 {fid!r}"
                    )
                if f.get("status") != "superseded":
                    errs.append(f"{fid}: 有 superseded_by 但 status={f.get('status')!r}")
            if ss:
                if ss not in by_id:
                    errs.append(f"{fid}: supersedes={ss} 不存在")
                elif by_id[ss].get("superseded_by") != fid:
                    errs.append(
                        f"{fid}: 双向不一致 — {ss}.superseded_by="
                        f"{by_id[ss].get('superseded_by')!r}，应为 {fid!r}"
                    )

            # caveats 约定非空
            cav = f.get("caveats")
            if not cav:
                errs.append(f"{fid}: caveats 为空（本仓库约定必须非空，否则 caveat→问题 的传导断裂）")

            # evidence 结构
            ev = f.get("evidence") or {}
            if "method" not in ev:
                errs.append(f"{fid}: evidence.method 缺失")
            if "result_summary" not in ev:
                errs.append(f"{fid}: evidence.result_summary 缺失")
            script = ev.get("script")
            if script and not os.path.exists(os.path.join(self.root, script)):
                errs.append(f"{fid}: evidence.script 不存在: {script}")

        return errs

    # -------------------------------------------------- INDEX 生成

    def _facts_content_version(self) -> str:
        """从 versions.json 读 FACTS.jsonl 的 content_version（兜底 1.0）。"""
        p = os.path.join(self.root, "versions.json")
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            for e in d.get("entries") or []:
                if e.get("path") == "memory/facts/FACTS.jsonl":
                    return e.get("content_version") or "1.0"
        except (OSError, json.JSONDecodeError):
            pass
        return "1.0"

    def _current_iteration(self) -> str:
        p = os.path.join(self.root, "versions.json")
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            return d.get("current_iteration") or "r02"
        except (OSError, json.JSONDecodeError):
            return "r02"

    def render_index(self) -> str:
        """从 FACTS.jsonl 生成 INDEX.md 内容（不写盘）。"""
        facts = self.load_facts(reload=True)
        n = len(facts)
        by_status: dict[str, int] = {}
        for f in facts:
            by_status[f["status"]] = by_status.get(f["status"], 0) + 1

        stars = lambda c: "★" * c + "☆" * (5 - c)

        out: list[str] = []
        out.append("# memory/facts/INDEX.md — 结论台账速览")
        out.append("")
        out.append("> **本文件由 `cli/main.py index` 从 `FACTS.jsonl` 自动生成。请勿手工编辑。**")
        out.append("> 权威源是 `FACTS.jsonl`（每行一条，受 `spec/fact.schema.json` 约束）。")
        out.append("")
        ver = self._facts_content_version()
        it = self._current_iteration()
        out.append(f"> **版本**：`{ver}` ｜ 轮次 `{it}` ｜ 权威源 `VERSION_INDEX.md`")
        out.append("> 版本规则见 `docs/VERSIONING_DOCS.md`")
        out.append("")
        stat = " / ".join(f"{v} {k}" for k, v in sorted(by_status.items()))
        out.append(f"**当前状态**：{n} 条结论 | {stat} | 生成日期 {self._today()}")
        out.append("")
        out.append("---")
        out.append("")

        # 按状态
        out.append("## 全部结论")
        out.append("")
        out.append("| id | 彩种 | 结论 | 状态 | 置信度 | 类别 | ★证据类型 | 轮次 |")
        out.append("|---|---|---|---|---|---|---|---|")
        for f in sorted(facts, key=lambda x: x["id"]):
            claim = f["claim"]
            if len(claim) > 46:
                claim = claim[:44] + "…"
            claim = claim.replace("|", "\\|")
            ct = f.get("claim_type") or "—"
            out.append(
                f"| {f['id']} | {f['game']} | {claim} | {f['status']} "
                f"| {stars(f['confidence'])} | `{f['category']}` | `{ct}` "
                f"| {f['established_in']} |"
            )
        out.append("")

        # 按类别
        out.append("## 按类别")
        out.append("")
        by_cat: dict[str, list[str]] = {}
        for f in facts:
            by_cat.setdefault(f["category"], []).append(f["id"])
        out.append("| 类别 | 结论 |")
        out.append("|---|---|")
        for cat in sorted(by_cat):
            out.append(f"| `{cat}` | {' · '.join(sorted(by_cat[cat]))} |")
        out.append("")

        # 按证据类型（★ 本轮新增：回答"这个数字靠什么立住"）
        out.append("## 按证据类型（引用时必看）")
        out.append("")
        out.append(
            "> `claim_type` 的判据不是『用了什么方法』，而是『**它会在什么情况下变错**』。"
            "与『类别』正交：类别说这结论属于哪一层，证据类型说它靠什么立住。"
        )
        out.append("")
        ct_notes = [
            ("analytic", "只有**模型定义**错了才会错", "可当不变量用；但不可拿来『验证』统计结论（L8）"),
            ("empirical", "**数据换了 / 时段移位**就会错", "引用前必看 `data_version` 与 `n_observations`"),
            ("simulation", "**模型假设**变了就会错", "依赖输入参数；**禁止当作真值引用**"),
            ("documentary", "**官方规则文本**变了就会错", "必须带 `rules_epoch`，脱离 epoch 无意义"),
            ("methodological", "关于**方法本身**的判断", "不产效应量；价值全在 caveats 的失效边界"),
        ]
        out.append("| 证据类型 | 失效方式 | 引用须知 | 结论 |")
        out.append("|---|---|---|---|")
        for ct, how, note in ct_notes:
            ids = sorted(f["id"] for f in facts if f.get("claim_type") == ct)
            out.append(
                f"| `{ct}` | {how} | {note} | {' · '.join(ids) if ids else '（无）'} |"
            )
        out.append("")

        # 按置信度
        out.append("## 按置信度（引用时必看）")
        out.append("")
        tiers = [
            (5, "★★★★★ 解析可证 / 精确枚举真值", "可直接作为不变量依赖"),
            (4, "★★★★☆ 强观测 + 多源交叉确认", "可用，但须声明适用条件"),
            (3, "★★★☆☆ 依赖模型的估计", "可用作方向判断，**禁止当作真值引用**"),
            (2, "★★☆☆☆ 弱迹象", "不可引用"),
            (1, "★☆☆☆☆ 已推翻", "禁止引用，仅作历史记录"),
        ]
        for lvl, label, note in tiers:
            ids = [f["id"] for f in facts if f["confidence"] == lvl]
            out.append(f"**{label}** — {note}")
            out.append("")
            out.append(f"`{'` `'.join(sorted(ids)) if ids else '（无）'}`")
            out.append("")

        # 演化链
        out.append("## 结论演化链")
        out.append("")
        chains = [f for f in facts if f.get("supersedes") or f.get("superseded_by")]
        if chains:
            for f in sorted(chains, key=lambda x: x["id"]):
                if f.get("supersedes"):
                    old = f["supersedes"]
                    out.append(f"- `{old}` ──被取代──> `{f['id']}`  （`{f['id']}.supersedes = {old}`）")
        else:
            out.append("（暂无）")
        out.append("")
        out.append("> **演化链是本仓库记忆的核心机制**：结论不被删除，而是带着血统被取代。")
        out.append("> 删除被推翻的结论会导致下一轮重复走同一条弯路。")
        out.append("")

        # 高危提醒（自动收集）
        out.append("## 自动提醒")
        out.append("")
        warned = [f for f in facts if f["confidence"] <= 3 or f["status"] != "established"]
        if warned:
            out.append("以下结论**引用前必读 caveats**：")
            out.append("")
            for f in sorted(warned, key=lambda x: x["id"]):
                why = []
                if f["status"] != "established":
                    why.append(f"status={f['status']}")
                if f["confidence"] <= 3:
                    why.append(f"置信度仅 {f['confidence']}/5")
                out.append(f"- **{f['id']}**（{'; '.join(why)}）：{f['claim'][:70]}")
        else:
            out.append("（全部结论均为 established 且置信度 ≥ 4）")
        out.append("")

        out.append("---")
        out.append("")
        out.append("## 新增结论的操作步骤")
        out.append("")
        out.append("1. 在 `FACTS.jsonl` **末尾追加**（不要插在中间，便于 diff）")
        out.append("2. id 取当前最大编号 +1（**永不复用**）")
        out.append(f"3. `{RED_LINE_FIELD}` 必须为 `false`（红线，`validate` 会检查）")
        out.append("4. 若推翻旧结论：旧条 `status=superseded` + 填 `superseded_by`；"
                   "新条填 `supersedes`。**双向必须一致**")
        out.append("5. `source` 必须是真实存在的文件路径；`evidence.script` 能复现")
        out.append(
            "6. ★ 填 `claim_type` —— 判据是『**它会在什么情况下变错**』，不是『用了什么方法』。"
            "五选一：`analytic`（模型定义错才错）/ `empirical`（数据或时段变了就错）"
            " / `simulation`（模型假设变了就错）/ `documentary`（规则文本变了就错）"
            " / `methodological`（方法本身的判断）。填错会被 `validate` 按类型拒收"
        )
        out.append("7. 跑 `python cli/main.py validate --facts` 确认无报错")
        out.append("8. 跑 `python cli/main.py index` 重新生成本文件")
        out.append("")

        return "\n".join(out)

    def write_index(self) -> str:
        content = self.render_index()
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        return self.index_path

    # -------------------------------------------------- 工作记忆

    def next_question_id(self) -> str:
        p = os.path.join(self.workbench_dir, "OPEN_QUESTIONS.md")
        nums = self._scan_ids(p, QUESTION_ID_RE)
        return f"Q-{max(nums) + 1:03d}" if nums else "Q-001"

    def open_questions(self) -> list[tuple[str, str]]:
        """返回 [(id, 状态)] —— 从 OPEN_QUESTIONS.md 粗解析。"""
        p = os.path.join(self.workbench_dir, "OPEN_QUESTIONS.md")
        if not os.path.exists(p):
            return []
        out = []
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        for m in re.finditer(r"^##\s+(Q-\d{3})\s+—\s+(.+)$", txt, re.M):
            qid, title = m.group(1), m.group(2)
            # 找该节内的状态
            seg = txt[m.end(): m.end() + 2000]
            sm = re.search(r"\|\s*\*\*状态\*\*\s*\|\s*`?([\w\s()→\-]+?)`?\s*\|", seg)
            out.append((qid, (sm.group(1).strip() if sm else "unknown"), title))
        return out

    def next_lesson_id(self) -> str:
        nums = self._scan_ids(self.lessons_path, LESSON_ID_RE)
        return f"L{max(nums) + 1}" if nums else "L1"

    def append_lesson(self, title: str, symptom: str, consequence: str,
                      correct: str, detection: str, facts: list[str] | None = None,
                      script: str | None = None) -> str:
        """追加一条教训（四段结构）。返回其 id。"""
        lid = self.next_lesson_id()
        os.makedirs(os.path.dirname(self.lessons_path), exist_ok=True)
        block = [
            "",
            "---",
            "",
            f"## {lid} — {title}",
            "",
            "| 项 | 内容 |",
            "|---|---|",
            f"| **症状** | {symptom} |",
            f"| **后果** | {consequence} |",
            f"| **正确做法** | {correct} |",
            f"| **检测方法** | ★ {detection} |",
            f"| **相关结论** | {' · '.join(facts) if facts else '（待补）'} |",
            f"| **脚本** | `{script}` |" if script else "| **脚本** | （待补） |",
            "",
        ]
        with open(self.lessons_path, "a", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(block))
        return lid

    def render_todo_from_caveats(self, only_status: tuple[str, ...] = ("established",)) -> str:
        """从结论的 caveats 生成 TODO 建议段（**不写盘**）。

        这是本仓库自我迭代传导机制的机械化部分：
        每条 caveat 都应变成一个开放问题 / 待办。
        """
        facts = self.load_facts(reload=True)
        lines = ["## 由 caveats 自动收集的待办建议", "",
                 "> 本段由 `Memory.render_todo_from_caveats()` 生成。",
                 "> 每条 caveat 都应转化为一个开放问题（见 `MEMORY_PROTOCOL.md` §1.5）。", ""]
        cnt = 0
        for f in sorted(facts, key=lambda x: x["id"]):
            if f["status"] not in only_status:
                continue
            cav = f.get("caveats") or []
            if not cav:
                continue
            lines.append(f"**{f['id']}** — {f['claim'][:60]}")
            for c in cav:
                c1 = c if len(c) <= 100 else c[:98] + "…"
                lines.append(f"- [ ] {c1}")
            lines.append("")
            cnt += len(cav)
        lines.append(f"共 {cnt} 条待转化 caveat。")
        return "\n".join(lines)

    # -------------------------------------------------- 内部工具

    @staticmethod
    def _scan_ids(path: str, pattern: re.Pattern) -> list[int]:
        if not os.path.exists(path):
            return []
        nums = []
        with open(path, encoding="utf-8") as f:
            for m in pattern.finditer(f.read()):
                try:
                    nums.append(int(m.group(1)))
                except ValueError:
                    pass
        return nums

    @staticmethod
    def _today() -> str:
        import datetime
        return datetime.date.today().isoformat()

    # -------------------------------------------------- 彩种

    def games(self) -> list[str]:
        """列出 games/ 下的彩种 id（排除 _template）。"""
        d = self.games_dir
        if not os.path.isdir(d):
            return []
        out = []
        for name in sorted(os.listdir(d)):
            if name.startswith("_") or name.startswith("."):
                continue
            if os.path.isfile(os.path.join(d, name, "game.yaml")):
                out.append(name)
        return out

    def game_dir(self, game: str) -> str:
        return os.path.join(self.games_dir, game)


# ---------------------------------------------------------------- 便捷函数

def load_game_config(repo_root: str, game: str) -> dict:
    """读 games/<game>/game.yaml。

    yaml 依赖是可选的 —— 若未安装 PyYAML，抛清晰错误。
    本仓库的 game.yaml 只用「映射 / 序列 / 标量」，可被最小解析器处理；
    但正式用法仍建议安装 PyYAML。
    """
    path = os.path.join(repo_root, "games", game, "game.yaml")
    if not os.path.exists(path):
        raise MemoryError(f"game.yaml 不存在: {path}")
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise MemoryError(
            "读取 game.yaml 需要 PyYAML。请安装：\n"
            "  pip install pyyaml\n"
            "（或使用 cli/main.py 的内置最小解析器）"
        ) from e
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":  # pragma: no cover
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    mem = Memory(root)
    print(f"仓库根: {mem.root}")
    print(f"结论数: {len(mem.load_facts())}")
    print(f"彩种:   {mem.games()}")
    print(f"下个结论 id: {mem.next_fact_id()}")
    print(f"下个问题 id: {mem.next_question_id()}")
    print(f"下个教训 id: {mem.next_lesson_id()}")
    errs = mem.validate_facts()
    if errs:
        print(f"\n校验失败 {len(errs)} 项：")
        for e in errs:
            print("  ✗", e)
        sys.exit(1)
    print("\n✓ 结论台账校验通过")
