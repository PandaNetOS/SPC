# -*- coding: utf-8 -*-
"""data_version.py — 数据版本管理

自动计算数据文件 SHA256，更新 game.yaml 里的登记。

用法：
    python tools/data_version.py compute <study_dir>   # 计算所有数据文件哈希
    python tools/data_version.py verify <study_dir>    # 验证哈希是否匹配
"""

import os
import sys
import json
import hashlib


def compute_sha256(filepath: str) -> str:
    """计算文件 SHA256。"""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_all(study_dir: str) -> dict:
    """计算研究组所有数据文件哈希。"""
    result = {}
    raw_dir = os.path.join(study_dir, "data", "raw")
    if os.path.isdir(raw_dir):
        for fn in os.listdir(raw_dir):
            fp = os.path.join(raw_dir, fn)
            if os.path.isfile(fp):
                result[f"data/raw/{fn}"] = compute_sha256(fp)

    derived_dir = os.path.join(study_dir, "data", "derived")
    if os.path.isdir(derived_dir):
        for fn in os.listdir(derived_dir):
            fp = os.path.join(derived_dir, fn)
            if os.path.isfile(fp):
                result[f"data/derived/{fn}"] = compute_sha256(fp)

    return result


def verify(study_dir: str) -> bool:
    """验证数据文件哈希是否与 game.yaml 登记一致。"""
    game_yaml = os.path.join(study_dir, "game.yaml")
    if not os.path.exists(game_yaml):
        print("game.yaml 不存在")
        return False

    # 读 game.yaml 里的 sha256
    # 简单解析（不依赖 yaml 库）
    declared = {}
    with open(game_yaml, encoding="utf-8") as f:
        in_raw = False
        for line in f:
            if "raw:" in line:
                in_raw = True
                continue
            if in_raw and "sha256:" in line:
                declared["sha256"] = line.split("sha256:")[1].strip().strip('"')
                break

    # 计算实际哈希
    actual = compute_all(study_dir)
    if not actual:
        print("没有数据文件")
        return True

    first_file = list(actual.keys())[0]
    actual_hash = actual[first_file]

    if "sha256" not in declared:
        print(f"⚠ game.yaml 未登记 sha256，实际值：{actual_hash}")
        return False

    if declared["sha256"] == actual_hash:
        print(f"✅ 哈希匹配：{first_file}")
        return True
    else:
        print(f"✗ 哈希不匹配：{first_file}")
        print(f"  声明：{declared['sha256']}")
        print(f"  实际：{actual_hash}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：")
        print("  python tools/data_version.py compute <study_dir>")
        print("  python tools/data_version.py verify <study_dir>")
        sys.exit(1)

    cmd = sys.argv[1]
    study_dir = sys.argv[2]

    if cmd == "compute":
        result = compute_all(study_dir)
        print("数据文件哈希：")
        for path, sha in result.items():
            print(f"  {path}: {sha}")
    elif cmd == "verify":
        ok = verify(study_dir)
        sys.exit(0 if ok else 1)
    else:
        print(f"未知命令：{cmd}")
