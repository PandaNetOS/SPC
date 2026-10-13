# -*- coding: utf-8 -*-
"""spc.paths — 仓库路径的**唯一权威来源**

## 为什么要有这个模块

2026-10-12 的架构升级把 `games/` 迁到 `labs/<lab>/studies/<id>/`、
`framework/` 迁到 `platform/`、研究组记忆从 `memory/` 下沉到
`labs/<lab>/studies/<id>/memory/`。迁移本身只做了 `git mv` + 文档同步，
**代码里的路径是各文件自己拼的字符串** —— 于是飞轮的三条主动脉同时断掉：

    flywheel.py 读 memory/facts/FACTS.jsonl          → 仪表盘全空
    derive_tasks.py 读 memory/workbench/*.md          → 待办池补给断裂
    api/game/strategy/validate/... 拼 games/<id>/...  → validate / pick / 收轮全瘫

根因不是「漏改了几处」，而是**没有路径抽象**：每个调用点各自
`os.path.join(root, "games", ...)`。只要再迁一次目录，同样的断链会
再来一遍。

## 设计原则

1. **单一权威**：所有路径都从本模块的函数取，禁止在调用点拼装路径片段。
2. **向后兼容探测**：新路径（`labs/<lab>/studies/<id>/`）不存在时回落到旧
   路径（`games/<id>/`），迁移期不炸；两者都存在时以新路径为准。
3. **彩种无关**：函数一律接收 `study`（或 `game`）参数，不写死 `dlt`。
4. **不猜**：找不到目录就返回不存在的路径，让调用方按「文件不存在」处理，
   而不是静默指向一个错误位置。

## 与 repo_root() 的关系

`src/spc/__init__.py` 的 `repo_root()` 判据已从「含 `games/`」改为
「含 `spec/` 与 `labs/`」（迁移后 `games/` 已删除）。本模块复用同一判据，
避免两处根目录探测逻辑分叉。
"""
from __future__ import annotations

import os

__all__ = [
    "repo_root",
    "labs_dir",
    "lab_dir",
    "studies_dir",
    "study_dir",
    "study_memory_dir",
    "workbench_dir",
    "facts_path",
    "facts_index_path",
    "lessons_path",
    "iterations_dir",
    "iteration_dir",
    "strategy_dir",
    "strategy_json_path",
    "game_yaml_path",
    "rules_history_path",
    "data_dir",
    "list_studies",
    "first_study",
    "rel_study",
    "lab_state_path",
    "platform_dir",
    "spec_dir",
]


# ------------------------------------------------------------------ 根目录

def repo_root(start: str | None = None) -> str:
    """解析仓库根。

    `start` 为 None 时**向上探测**（含 `spec/` 与 `labs/` 的那一级）；
    给了 `start` 则**它就是根**，原样返回（不再向上找）。

    ★ 为什么「给了就必须用」：调用方显式传 root 时（测试构造的临时仓库、
    外部工具指定的数据目录），向上探测会一路找到**真实仓库根**，
    于是所有路径都指向真仓库而临时目录被无视 —— 静默地用错数据，
    比报错危险得多。

    兼容 `games/` 旧布局：向上找不到 `labs/` 但找到 `games/`，同样认为是根
    （迁移中间态 / 旧 checkout）。
    """
    if start is not None:
        return os.path.abspath(start)
    cur = os.path.dirname(__file__)
    for _ in range(8):
        if os.path.isdir(os.path.join(cur, "spec")) and (
            os.path.isdir(os.path.join(cur, "labs"))
            or os.path.isdir(os.path.join(cur, "games"))
        ):
            return os.path.abspath(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    # 兜底：src/spc/ → 仓库根
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ------------------------------------------------------ labs/<lab>/studies/<id>

def labs_dir(root: str | None = None) -> str:
    return os.path.join(repo_root(root), "labs")


def lab_dir(lab: str, root: str | None = None) -> str:
    return os.path.join(labs_dir(root), lab)


def studies_dir(lab: str = "lottery", root: str | None = None) -> str:
    """研究组集合目录。旧布局下等价于 `games/`（无 lab 层级）。

    ★ `lab` 带默认值且可省略：本仓库当前只有 lottery 一个实验室，
    要求每个调用点都传 lab 只会制造噪音。签名与其余函数一致
    （`(study, lab="lottery", root=None)`），避免关键字调用 `root=` 时炸。
    """
    r = repo_root(root)
    new = os.path.join(r, "labs", lab, "studies")
    if os.path.isdir(new):
        return new
    legacy = os.path.join(r, "games")
    if os.path.isdir(legacy):
        return legacy
    return new


def study_dir(study: str, lab: str = "lottery", root: str | None = None) -> str:
    """单个研究组目录。新旧布局只认一个（新优先），见 `studies_dir`。"""
    return os.path.join(studies_dir(lab, root), study)


# ------------------------------------------------------------ 研究组内部结构

def study_memory_dir(study: str, lab: str = "lottery",
                     root: str | None = None) -> str:
    r = repo_root(root)
    new = os.path.join(study_dir(study, lab, r), "memory")
    if os.path.isdir(new):
        return new
    # 旧布局：记忆在仓库根 memory/（彩种结论混在总台账，用 game 字段区分）
    legacy = os.path.join(r, "memory")
    if os.path.isdir(legacy):
        return legacy
    return new


def workbench_dir(study: str, lab: str = "lottery",
                  root: str | None = None) -> str:
    return os.path.join(study_memory_dir(study, lab, root), "workbench")


def facts_path(study: str, lab: str = "lottery",
               root: str | None = None) -> str:
    return os.path.join(study_memory_dir(study, lab, root), "facts", "FACTS.jsonl")


def facts_index_path(study: str, lab: str = "lottery",
                     root: str | None = None) -> str:
    return os.path.join(study_memory_dir(study, lab, root), "facts", "INDEX.md")


def lessons_path(study: str, lab: str = "lottery",
                 root: str | None = None) -> str:
    return os.path.join(study_memory_dir(study, lab, root), "lessons", "LESSONS.md")


def iterations_dir(study: str, lab: str = "lottery",
                   root: str | None = None) -> str:
    return os.path.join(study_dir(study, lab, root), "iterations")


def iteration_dir(study: str, rnd: int | str, lab: str = "lottery",
                  root: str | None = None) -> str:
    return os.path.join(iterations_dir(study, lab, root), f"round{int(rnd):02d}")


def strategy_dir(study: str, lab: str = "lottery",
                 root: str | None = None) -> str:
    return os.path.join(study_dir(study, lab, root), "strategy")


def strategy_json_path(study: str, lab: str = "lottery",
                       root: str | None = None) -> str:
    return os.path.join(strategy_dir(study, lab, root), "strategy.json")


def game_yaml_path(study: str, lab: str = "lottery",
                   root: str | None = None) -> str:
    return os.path.join(study_dir(study, lab, root), "game.yaml")


def rules_history_path(study: str, lab: str = "lottery",
                       root: str | None = None) -> str:
    return os.path.join(study_dir(study, lab, root), "rules_history.md")


def data_dir(study: str, lab: str = "lottery",
             root: str | None = None) -> str:
    return os.path.join(study_dir(study, lab, root), "data")


# ------------------------------------------------------------------ 枚举

def list_studies(lab: str = "lottery", root: str | None = None) -> list[str]:
    """列出研究组 id（含 game.yaml 者；排除 `_template` 与隐藏目录）。"""
    d = studies_dir(lab, root)
    if not os.path.isdir(d):
        return []
    out: list[str] = []
    for name in sorted(os.listdir(d)):
        if name.startswith("_") or name.startswith("."):
            continue
        if os.path.isfile(os.path.join(d, name, "game.yaml")):
            out.append(name)
    return out


def first_study(lab: str = "lottery", root: str | None = None) -> str | None:
    """第一个研究组 id（彩种无关：用于「仓库里只有一个彩种」的默认场景）。"""
    ids = list_studies(lab, root)
    return ids[0] if ids else None


def rel_study(study: str, lab: str = "lottery",
              root: str | None = None) -> str:
    """研究组目录相对仓库根的**正斜杠**相对路径（用于登记/展示，勿用于 IO）。

    例：`labs/lottery/studies/dlt`。旧布局下为 `games/dlt`。
    正斜杠是 versions.json / DEPENDENCY_MAP 等登记格式的既定约定
    （Windows 下 os.path.join 会给出反斜杠，不能直接用于登记）。
    """
    r = repo_root(root)
    return os.path.relpath(study_dir(study, lab, r), r).replace(os.sep, "/")


# ------------------------------------------------------- 实验室层（定时迭代）

def lab_state_path(lab: str, root: str | None = None) -> str:
    """实验室层状态文件（定时迭代的时钟，见 docs/ARCHITECTURE.md）。

    记录上次体检轮次 / 到期规则 / 上次元分析结论，由
    `tools/lab_healthcheck.py` 读写。**按轮次定时，不按墙钟时间** ——
    SPC 的迭代节奏由数据驱动，轮次是唯一可靠的时钟。
    """
    return os.path.join(lab_dir(lab, root), "LAB_STATE.json")


# ------------------------------------------------------------ 平台层 / 契约层

def platform_dir(root: str | None = None) -> str:
    return os.path.join(repo_root(root), "platform")


def spec_dir(root: str | None = None) -> str:
    return os.path.join(repo_root(root), "spec")
