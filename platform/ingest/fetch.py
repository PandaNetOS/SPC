# -*- coding: utf-8 -*-
"""platform.ingest.fetch — HTTP 拉取（彩种无关）

只用标准库 urllib：管道不得引入第三方网络依赖，也不得写死任何主机名。
端点与分页参数全部由调用方（`game.yaml` 的 data_source）传入。
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request


class FetchError(RuntimeError):
    """拉取失败（网络/状态码/JSON 解析）。"""


def _get(url: str, timeout: int, retries: int, backoff: float) -> bytes:
    last: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "spc-ingest/1.0", "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    raise FetchError(f"HTTP {resp.status}")
                return resp.read()
        except Exception as e:  # noqa: BLE001
            last = e
            if attempt + 1 < max(1, retries):
                time.sleep(backoff * (attempt + 1))
    raise FetchError(f"拉取失败（重试 {retries} 次）: {url} —— {last}")


def fetch_endpoint(
    url: str,
    *,
    params: dict | None = None,
    timeout: int = 20,
    retries: int = 3,
    backoff: float = 1.0,
) -> dict:
    """拉一个 JSON 端点。params 会做 URL 编码拼接。"""
    full = url
    if params:
        qs = urllib.parse.urlencode(params)
        full = url + ("&" if "?" in url else "?") + qs
    raw = _get(full, timeout, retries, backoff)
    try:
        return json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        raise FetchError(f"响应不是合法 JSON: {e}") from e


def fetch_paged(
    url: str,
    *,
    params: dict | None = None,
    page_param: str = "pageNo",
    page_start: int = 1,
    size_param: str = "pageSize",
    page_size: int = 30,
    max_pages: int = 200,
    total_field: str = "total",
    list_path: tuple[str, ...] = ("value", "list"),
    timeout: int = 20,
    retries: int = 3,
    backoff: float = 1.0,
) -> list[dict]:
    """翻页拉全量。返回按源顺序的记录列表（通常是最新在前）。

    通用逻辑：不假设总数字段名以外的结构；list_path 指定记录数组的嵌套路径。
    """
    out: list[dict] = []
    page = page_start
    total: int | None = None
    for _ in range(max_pages):
        p = dict(params or {})
        p[size_param] = page_size
        p[page_param] = page
        doc = fetch_endpoint(url, params=p, timeout=timeout, retries=retries, backoff=backoff)
        node: object = doc
        for key in list_path:
            node = (node or {}).get(key) if isinstance(node, dict) else None
        if not isinstance(node, list):
            raise FetchError(f"记录数组路径 {list_path} 不存在或不是数组")
        out.extend(node)
        if total is None:
            total = _dig(doc, total_field)
        if not node or (total is not None and len(out) >= total):
            break
        page += 1
    return out


def _dig(doc: dict, dotted: str) -> int | None:
    cur: object = doc
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur if isinstance(cur, int) else None
