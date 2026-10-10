# -*- coding: utf-8 -*-
"""hash_and_list.py — 实算 raw 数据 SHA256 并列出本彩种 data/ 文件清单

用途：
  1. 为 game.yaml 的 data.raw[].sha256 提供**实算值**（禁止手填）
  2. 输出文件清单，供人工核对交付完整性

路径自锚定：本文件在 games/<id>/data/build_scripts/ 下，
           raw 数据在 games/<id>/data/raw/。
"""
import hashlib
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))   # data/build_scripts/
DATA_DIR = os.path.dirname(HERE)                    # data/
RAW_DIR = os.path.join(DATA_DIR, "raw")

RAW_FILES = ["dlt_full_2933.csv", "dlt_full_2933.jsonl"]


def sha256(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    print("=" * 78)
    print("raw 数据 SHA256（写入 game.yaml 的 data.raw[].sha256）")
    print("=" * 78)

    ok = True
    for name in RAW_FILES:
        p = os.path.join(RAW_DIR, name)
        if not os.path.exists(p):
            print(f"✗ 缺失: {os.path.relpath(p, DATA_DIR)}")
            ok = False
            continue
        print(f"{name:28s} {sha256(p)}")

    print()
    print("=" * 78)
    print("文件清单")
    print("=" * 78)
    for root, dirs, files in os.walk(DATA_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if f.endswith((".pyc", ".log")):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, DATA_DIR).replace("\\", "/")
            print(f"FILE  {rel:50s} {os.path.getsize(p):>10d}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
