# -*- coding: utf-8 -*-
"""platform.ingest.pipeline — 接入管道编排（fetch → normalize → merge → seal）

彩种无关。全部行为由 `data_source` 声明驱动：

    from platform.ingest import run_pipeline
    report = run_pipeline(root, game="dlt")          # 增量：只补缺失期
    report = run_pipeline(root, game="dlt", full=True)  # 全量重拉

CLI：
    python platform/ingest/pipeline.py --game dlt [--full] [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))

# platform/ 与 Python 标准库 platform 同名，无法按包名导入。
# 故同目录模块一律走 sys.path 注入本目录后按顶层模块名加载。
if __package__ in (None, ""):
    sys.path.insert(0, _HERE)
    import fetch as _fetch_mod
    import normalize as _normalize_mod
    import seal as _seal_mod
else:
    from . import fetch as _fetch_mod
    from . import normalize as _normalize_mod
    from . import seal as _seal_mod

fetch_paged = _fetch_mod.fetch_paged
FetchError = _fetch_mod.FetchError
normalize_draw = _normalize_mod.normalize_draw
merge_csv = _seal_mod.merge_csv
merge_jsonl = _seal_mod.merge_jsonl
seal_dataset = _seal_mod.seal_dataset


def _load_game_cfg(root: str, game: str) -> dict:
    import yaml  # PyYAML 已在仓库依赖内
    p = os.path.join(root, "labs", "lottery", "studies", game, "game.yaml")
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(root: str, game: str, *, full: bool = False,
                 dry_run: bool = False, verbose: bool = True) -> dict:
    """跑一次接入管道。返回报告 dict。"""
    cfg = _load_game_cfg(root, game)
    ds = (cfg or {}).get("data_source")
    if not ds:
        raise FetchError(
            f"game.yaml 未声明 data_source —— 无法自动取数。"
            f"（CP-002：见 proposals/CP-002.md §4.1）"
        )

    data = cfg.get("data") or {}
    raw = data.get("raw") or {}
    raw_path = os.path.join(root, (raw.get("path") or "").replace("/", os.sep))
    fmt = (raw.get("format") or "csv").lower()
    enc = raw.get("encoding") or "utf-8-sig"
    known_last = str(raw.get("last_draw_num") or "")

    ep = (ds.get("endpoints") or [])[0]
    params = dict(ds.get("params") or {})
    fmap = ds.get("field_map") or {}
    prizes_key = ds.get("prizes_key")
    prize_idx = ds.get("prize_index_key")

    def say(*a):
        if verbose:
            print(*a)

    say(f"[1/4] fetch  ← {ep.get('url')}")
    records = fetch_paged(
        ep["url"],
        params=params,
        page_param=ds.get("page_param", "pageNo"),
        size_param=ds.get("size_param", "pageSize"),
        page_size=int(ds.get("page_size", 30)),
        max_pages=int(ds.get("max_pages", 200)),
        total_field=ds.get("total_field", "value.total"),
        list_path=tuple(ds.get("list_path") or ("value", "list")),
    )
    say(f"      拉取 {len(records)} 条源记录")

    say("[2/4] normalize（声明式字段映射）")
    rows = [normalize_draw(r, fmap, prizes_key=prizes_key,
                           prize_index_key=prize_idx,
                           draw_result_field=ds.get("draw_result_field"),
                           zones=ds.get("zones")) for r in records]

    # 增量过滤：按开奖日期（而非期号字符串）判断新旧 —— 期号位数可变，
    # 字符串比较会把 2009 年的 "9153" 误判为比 "26115" 新。
    def rdate(r):
        return str(r.get("date", ""))
    if not full and known_last:
        known_date = raw.get("date_range", [None, None])[-1] or ""
        if known_date:
            newer = [r for r in rows if rdate(r) > known_date]
        else:
            newer = rows  # 拿不到已知日期就全量对账
    else:
        newer = rows
    newer.sort(key=rdate)
    say(f"      {'全量' if full else '增量'}目标 {len(newer)} 期"
        f"（{newer[0]['draw_num'] if newer else '-'} .. {newer[-1]['draw_num'] if newer else '-'}）")

    if dry_run:
        say(f"[3/4] merge  —— dry-run，跳过写盘")
        say("[4/4] seal   —— dry-run，跳过")
        return {"game": game, "dry_run": True, "fetched": len(records),
                "to_merge": len(newer),
                "sample": newer[-1] if newer else None}

    say("[3/4] merge   → " + os.path.relpath(raw_path, root))
    if fmt == "csv":
        added, total = merge_csv(raw_path, newer, encoding=enc)
    else:
        added, total = merge_jsonl(raw_path, newer)
    say(f"      写入 {added} 期，合计 {total} 期")

    say("[4/4] seal（SHA256 + 区间）")
    info = seal_dataset(raw_path)
    say(f"      sha256={info['sha256'][:16]}…  n={info.get('n_rows')}  "
        f"{info.get('first_draw_num')}..{info.get('last_draw_num')}")
    return {"game": game, "added": added, "total": total, "seal": info,
            "to_update_game_yaml": {
                "n_draws": info.get("n_rows"),
                "last_draw_num": info.get("last_draw_num"),
                "date_range": info.get("date_range"),
                "sha256": info.get("sha256"),
            }}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SPC 数据接入管道（CP-002 P1/P2）")
    ap.add_argument("--game", required=True)
    ap.add_argument("--full", action="store_true", help="全量重拉（默认增量只补缺失期）")
    ap.add_argument("--dry-run", action="store_true", help="只拉取不写盘")
    ap.add_argument("--root", default=_ROOT)
    a = ap.parse_args(argv)
    try:
        rep = run_pipeline(a.root, a.game, full=a.full, dry_run=a.dry_run)
    except FetchError as e:
        print(f"✗ 管道失败: {e}", file=sys.stderr)
        return 1
    if rep.get("dry_run"):
        print("\n--- dry-run 预览（未写盘）---")
        print(rep.get("sample"))
    else:
        print("\n--- 请把以下字段同步回 game.yaml 的 data.raw ---")
        for k, v in rep["to_update_game_yaml"].items():
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
