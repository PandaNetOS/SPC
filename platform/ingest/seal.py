# -*- coding: utf-8 -*-
"""platform.ingest.seal — 封版：算 SHA256、原子写盘、报告期数区间（彩种无关）"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import tempfile


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def merge_csv(base_path: str, new_rows: list[dict], *, encoding: str = "utf-8-sig",
              key: str = "draw_num") -> tuple[int, int]:
    """把新行并入已有 CSV：同 key 覆盖，新 key 追加，按 key 升序排。

    返回 (新增行数, 总行数)。原子写：先写临时文件再替换。
    """
    existing: dict[str, dict] = {}
    header: list[str] = []
    if os.path.exists(base_path):
        with open(base_path, encoding=encoding, newline="") as f:
            rd = csv.DictReader(f)
            header = rd.fieldnames or []
            for r in rd:
                if r.get(key):
                    existing[str(r[key])] = r
    for r in new_rows:
        k = str(r.get(key, "")).strip()
        if k:
            existing[k] = r

    cols = list(header) or sorted({k for r in existing.values() for k in r})
    for r in new_rows:
        for k in r:
            if k not in cols:
                cols.append(k)

    rows = sorted(existing.values(), key=lambda r: str(r.get(key, "")))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)

    _atomic_write_text(base_path, buf.getvalue(), encoding)
    return len(new_rows), len(rows)


def merge_jsonl(base_path: str, new_rows: list[dict], *, key: str = "draw_num") -> tuple[int, int]:
    existing: dict[str, dict] = {}
    if os.path.exists(base_path):
        with open(base_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                o = json.loads(line)
                k = str(o.get(key, "")).strip()
                if k:
                    existing[k] = o
    for r in new_rows:
        k = str(r.get(key, "")).strip()
        if k:
            existing[k] = r
    rows = sorted(existing.values(), key=lambda r: str(r.get(key, "")))
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    _atomic_write_text(base_path, text, "utf-8")
    return len(new_rows), len(rows)


def _atomic_write_text(path: str, text: str, encoding: str) -> None:
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    enc = encoding if encoding.lower().replace("_", "-") in {"utf-8", "utf8"} else "utf-8"
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=enc, newline="") as f:
            f.write(text)
        if enc.lower() in {"utf-8", "utf8"} and encoding.lower().startswith("utf-8-sig"):
            # 需要 BOM 时重写
            with open(tmp, "r", encoding="utf-8") as r:
                data = r.read()
            with open(tmp, "w", encoding="utf-8-sig", newline="") as w2:
                w2.write(data)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def seal_dataset(path: str) -> dict:
    """封版报告：SHA256 + 期数区间 + 数据量。"""
    info: dict = {"path": path, "sha256": sha256_file(path)}
    if path.endswith(".csv"):
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        info["n_rows"] = len(rows)
        if rows:
            info["first_draw_num"] = rows[0].get("draw_num")
            info["last_draw_num"] = rows[-1].get("draw_num")
            if rows[0].get("date") and rows[-1].get("date"):
                info["date_range"] = [rows[0]["date"], rows[-1]["date"]]
    elif path.endswith(".jsonl"):
        with open(path, encoding="utf-8") as f:
            rows = [json.loads(x) for x in f if x.strip()]
        info["n_rows"] = len(rows)
        if rows:
            info["first_draw_num"] = str(rows[0].get("draw_num"))
            info["last_draw_num"] = str(rows[-1].get("draw_num"))
    return info
