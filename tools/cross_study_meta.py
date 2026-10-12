# -*- coding: utf-8 -*-
"""cross_study_meta.py — 跨研究组元分析

对比不同研究组的结论，找共性和差异。

用法：
    python tools/cross_study_meta.py list              # 列出所有研究组
    python tools/cross_study_meta.py compare <study1> <study2>  # 对比两个研究组
"""

import os
import sys
import json


def list_studies(root: str = ".") -> list:
    """列出所有研究组。"""
    labs_dir = os.path.join(root, "labs")
    studies = []
    if not os.path.isdir(labs_dir):
        return studies

    for lab in sorted(os.listdir(labs_dir)):
        lab_dir = os.path.join(labs_dir, lab)
        if not os.path.isdir(lab_dir):
            continue
        studies_dir = os.path.join(lab_dir, "studies")
        if not os.path.isdir(studies_dir):
            continue
        for s in sorted(os.listdir(studies_dir)):
            s_dir = os.path.join(studies_dir, s)
            if os.path.isfile(os.path.join(s_dir, "game.yaml")):
                studies.append(f"{lab}/{s}")
    return studies


def load_facts(study_path: str) -> list:
    """加载研究组的结论库。"""
    facts_path = os.path.join(study_path, "findings", "FACTS.jsonl")
    if not os.path.exists(facts_path):
        return []

    facts = []
    with open(facts_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    facts.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return facts


def compare(study1: str, study2: str, root: str = ".") -> dict:
    """对比两个研究组的结论。"""
    labs_dir = os.path.join(root, "labs")

    def _find_path(study_id: str) -> str:
        for lab in os.listdir(labs_dir):
            p = os.path.join(labs_dir, lab, "studies", study_id)
            if os.path.isdir(p):
                return p
        return ""

    p1 = _find_path(study1)
    p2 = _find_path(study2)

    if not p1 or not p2:
        return {"error": "研究组不存在"}

    facts1 = load_facts(p1)
    facts2 = load_facts(p2)

    # 按 claim_type 分类对比
    by_type1 = {}
    for f in facts1:
        ct = f.get("claim_type", "unknown")
        by_type1.setdefault(ct, []).append(f)

    by_type2 = {}
    for f in facts2:
        ct = f.get("claim_type", "unknown")
        by_type2.setdefault(ct, []).append(f)

    common_types = set(by_type1.keys()) & set(by_type2.keys())

    return {
        "study1": study1,
        "study2": study2,
        "facts1_count": len(facts1),
        "facts2_count": len(facts2),
        "common_claim_types": sorted(common_types),
        "by_type1": {k: len(v) for k, v in by_type1.items()},
        "by_type2": {k: len(v) for k, v in by_type2.items()},
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：")
        print("  python tools/cross_study_meta.py list")
        print("  python tools/cross_study_meta.py compare <study1> <study2>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        studies = list_studies()
        print(f"研究组（{len(studies)} 个）：")
        for s in studies:
            print(f"  {s}")
    elif cmd == "compare":
        if len(sys.argv) < 4:
            print("请提供两个研究组名")
            sys.exit(1)
        result = compare(sys.argv[2], sys.argv[3])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"未知命令：{cmd}")
