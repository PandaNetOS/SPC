# -*- coding: utf-8 -*-
"""spc.evidence — 证据锚定：把结论与它引用的文件/数字用哈希绑在一起

## 解决什么

结论台账只存 `source` **路径**。路径还在，不代表内容没变 ——
若 `simulation_results.json` 被人改了，`F-0001` 里那个 `4.667289469773513e-08`
就已经是一句**无人担保的断言**，而全仓库没有任何东西会发现。

这就是"证据失效检测"要补的洞：**结论里的数字必须锚在它诞生的那一份文件上。**

## 两个锚

| 锚 | 位置 | 绑的是什么 | 漂移时的含义 |
|---|---|---|---|
| `evidence.source_sha256` | 每条结论 | 该结论的 `source` 文件字节 | **这份证据被改过 → 结论可能失效** |
| `provenance.evidence_hash` | strategy.json | 全部被引用结论的**规范视图** | **策略引用的证据已变更 → 策略可能建立在旧结论上** |

第二个锚是第一个的聚合：一条结论被推翻/改数字/换口径，
策略那边的 `evidence_hash` 就会变，于是"策略与证据脱节"变成可检出的错误，
而不是靠人记得回来复查。

## 为什么第二个锚只摘「规范视图」而不是整条结论

整条结论的 JSON 里含 `created_at` / `updated_at` / `tags` 等**与证据强度无关**的字段。
把它们算进去，任何一次无关编辑都会触发漂移报警 ——
**会误报的检查比没有检查更坏**，甚至更坏：它会训练人忽略报警。

规范视图只取"结论的实质"：
`id` / `claim` / `status` / `confidence` / `claim_type` /
`superseded_by` / `evidence.effect` / `caveats`。

其中 `evidence.effect` 与 `caveats` 是关键：
数字改了、或减损项改了（说明适用条件变了），都应该让下游重新确认。
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Iterable

__all__ = [
    "sha256_file",
    "sha256_text",
    "fact_anchor",
    "evidence_digest",
    "ANCHOR_FIELDS",
]

# 参与证据摘要的字段（顺序固定，与 dict 顺序无关）
ANCHOR_FIELDS = (
    "id",
    "claim",
    "status",
    "confidence",
    "claim_type",
    "superseded_by",
    "evidence.effect",
    "caveats",
)

_CHUNK = 1 << 20


def sha256_file(path: str) -> str:
    """文件的 SHA256（分块读，大文件也安全）。"""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    """文本的 SHA256（UTF-8）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dig(obj: dict, dotted: str) -> Any:
    """按 'a.b' 路径取值，任一层缺失返回 None。"""
    cur: Any = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def fact_anchor(ft: dict) -> dict:
    """抽一条结论的『规范视图』——只含与证据强度有关的字段。"""
    out: dict[str, Any] = {}
    for field in ANCHOR_FIELDS:
        out[field] = _dig(ft, field)
    return out


def evidence_digest(facts: Iterable[dict], ids: Iterable[str] | None = None) -> str:
    """对若干条结论的规范视图求摘要。

    `ids` 为空时，对传入的**全部**结论求摘要（顺序无关，内部按 id 排序）。
    """
    wanted = set(ids) if ids is not None else None
    picked = [
        fact_anchor(f)
        for f in facts
        if wanted is None or f.get("id") in wanted
    ]
    picked.sort(key=lambda a: str(a.get("id")))
    canonical = json.dumps(
        picked, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return sha256_text(canonical)


def load_facts(repo_root: str | None = None, study: str | None = None) -> list[dict]:
    """读 FACTS.jsonl。与 validate.load_fact_ids 分开，避免循环导入。

    路径一律经 spc.paths（研究组记忆已从仓库根 memory/ 下沉）。
    """
    root = repo_root or os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    from . import paths  # 延迟导入避免环

    study = study or paths.first_study(root=root)
    if not study:
        return []
    p = paths.facts_path(study, root=root)
    if not os.path.exists(p):
        return []
    out: list[dict] = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
