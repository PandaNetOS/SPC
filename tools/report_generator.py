# -*- coding: utf-8 -*-
"""report_generator.py — 报告生成器

从脚本结果自动生成 FINDINGS.md / HANDOFF.md 草稿。

用法：
    python tools/report_generator.py findings <round_dir>    # 生成 FINDINGS 草稿
    python tools/report_generator.py handoff <round_dir>     # 生成 HANDOFF 草稿
"""

import os
import sys
import json
from datetime import date


def generate_findings(round_dir: str) -> str:
    """生成 FINDINGS.md 草稿。"""
    # 找结果 JSON
    results = []
    scripts_dir = os.path.join(round_dir, "scripts")
    if os.path.isdir(scripts_dir):
        for fn in os.listdir(scripts_dir):
            if fn.endswith(".json"):
                fp = os.path.join(scripts_dir, fn)
                try:
                    with open(fp, encoding="utf-8") as f:
                        data = json.load(f)
                    results.append((fn, data))
                except Exception:
                    pass

    md = f"""# FINDINGS.md — {os.path.basename(round_dir)} 研究发现

> 自动生成草稿，请人工审核修改。

## 1. 数据来源

- 数据版本：dlt_full_2933
- 分析脚本：见 scripts/ 目录

## 2. 核心发现

"""
    for fn, data in results:
        md += f"### 2.{results.index((fn, data))+1} {fn}\n\n"
        md += f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```\n\n"

    md += """## 3. 证伪/修正

> 本轮推翻/修正了哪些既有结论？（必填）

## 4. Caveats

> 每条结论的不确定性来源。

## 5. 下一步

"""
    return md


def generate_handoff(round_dir: str) -> str:
    """生成 HANDOFF.md 草稿。"""
    round_name = os.path.basename(round_dir)
    next_round = f"round{int(round_name.replace('round', ''))+1:02d}"

    return f"""# HANDOFF.md — {round_name} 交接

> 自动生成草稿，请人工审核修改。

## 1. 本轮结论

> 一句话总结本轮最重要的发现。

## 2. 遗留问题

> 本轮没解决、需要下轮继续的问题。

## 3. 下轮建议

> 建议下轮做什么（优先级排序）。

## 4. 风险提示

> 下轮容易踩的坑。

---

*下轮：{next_round}*
"""


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：")
        print("  python tools/report_generator.py findings <round_dir>")
        print("  python tools/report_generator.py handoff <round_dir>")
        sys.exit(1)

    cmd = sys.argv[1]
    round_dir = sys.argv[2]

    if cmd == "findings":
        print(generate_findings(round_dir))
    elif cmd == "handoff":
        print(generate_handoff(round_dir))
    else:
        print(f"未知命令：{cmd}")
