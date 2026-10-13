# -*- coding: utf-8 -*-
"""platform.ingest.normalize — 记录归一（声明式字段映射，彩种无关引擎）

引擎只认 `field_map`（来源字段 → SPC 标准字段），**不含任何彩种知识**。
映射表写在 `game.yaml` 的 `data_source.field_map`，换彩种只改配置。

支持两种取值形态：
  - 字符串路径：`"lotteryDrawNum"` / `"poolBalanceAfterdraw"`（点号穿字典/列表）
  - 命名空间：`"prizeLevels.101.stakeCount"` —— 先按 prizes 命名空间建索引再取
"""
from __future__ import annotations

import re
from typing import Any


def _as_number(s: Any) -> Any:
    """把 "1,234.00" / "---" / "" 归一成 float / int / None。"""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return s
    t = str(s).strip().replace(",", "")
    if t in {"", "---", "-", "null", "None"}:
        return None
    try:
        f = float(t)
    except ValueError:
        return t
    return int(f) if f.is_integer() else f


def _dig_path(rec: Any, path: str) -> Any:
    cur = rec
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            idx = int(part)
            cur = cur[idx] if 0 <= idx < len(cur) else None
        else:
            return None
        if cur is None:
            return None
    return cur


def _prize_index(prizes: list[dict], key: str) -> dict[str, dict]:
    """把奖级列表按指定键（如 group=101 → sort）建成 {key: item}。"""
    idx: dict[str, dict] = {}
    for it in prizes or []:
        if not isinstance(it, dict):
            continue
        k = str(it.get(key, "")).strip()
        if k:
            idx[k] = it
    return idx


def normalize_draw(
    record: dict,
    field_map: dict[str, str],
    *,
    prizes_key: str | None = None,
    prize_index_key: str | None = None,
    draw_result_field: str | None = None,
    zones: list | None = None,
    zone_big_threshold: int | None = None,
    derived: bool = True,
) -> dict:
    """把一条源记录映射成 SPC 标准行。

    field_map: {标准字段: 源路径}
    prizes_key: 奖级数组在源记录里的键名（如 "prizeLevelList"）
    prize_index_key: 奖级数组索引用哪个键（如 "group"）
    """
    prizes = _dig_path(record, prizes_key) if prizes_key else None
    pidx = (
        _prize_index(prizes, prize_index_key)
        if isinstance(prizes, list) and prize_index_key
        else {}
    )

    row: dict[str, Any] = {}
    for std, src in field_map.items():
        m = re.match(r"^prizeIndex\.([^.]+)\.(\w+)$", src)
        if m:
            it = pidx.get(m.group(1), {})
            val = _dig_path(it, m.group(2))
        elif src.startswith("prizeIndex."):
            val = None
        else:
            val = _dig_path(record, src)
        row[std] = _as_number(val) if not isinstance(val, (dict, list)) else val

    # 号码串切分（zones 声明式，非彩种知识）
    if draw_result_field and zones:
        raw_nums = str(_dig_path(record, draw_result_field) or "").split()
        for z in zones:
            pfx = z.get("prefix")
            start = int(z.get("start", 0))
            cnt = int(z.get("count", 0))
            for i in range(cnt):
                pos = start + i
                if pos < len(raw_nums):
                    row[f"{pfx}_{i + 1}"] = _as_number(raw_nums[pos])

    if derived:
        row = _derive(row, zone_big_threshold=zone_big_threshold)
    return row


def _derive(row: dict, *, zone_big_threshold: int | None = None) -> dict:
    """派生纯计算列。

    zone_big_threshold 是彩种特定的「多大算大号」阈值，由 game.yaml 的
    data_source.zone_big_threshold 提供 —— 框架层不猜（35 选 5 的大号起点是 18，
    但这是彩票规则，不是通用公式）。未提供时只算 sum/odd/span。
    """
    def ints(prefix: str) -> list[int]:
        return [int(row[f"{prefix}_{i}"]) for i in range(1, 6)
                if row.get(f"{prefix}_{i}") is not None]

    front = ints("front")
    back = ints("back")
    thr = zone_big_threshold if zone_big_threshold is not None else 10 ** 9
    if front:
        row["front_sum"] = sum(front)
        row["front_odd"] = sum(1 for v in front if v % 2)
        row["front_big"] = sum(1 for v in front if v >= thr)
        row["front_span"] = max(front) - min(front)
    if back:
        row["back_span"] = max(back) - min(back)
    if row.get("date"):
        try:
            y, m, d = (int(x) for x in str(row["date"]).split("-"))
            row["year"] = y
        except (ValueError, TypeError):
            pass
    return row
