# -*- coding: utf-8 -*-
"""new_study.py — 新研究组初始化工具

一键生成新研究组的目录结构 + 模板文件。

用法：
    python tools/new_study.py <lab> <study_name>

示例：
    python tools/new_study.py lottery ssq
    → 在 labs/lottery/studies/ssq/ 下生成完整目录结构
"""

import os
import sys
import json
import hashlib
from datetime import date


def new_study(lab: str, study: str, root: str = ".") -> str:
    """创建新研究组目录结构。

    Parameters
    ----------
    lab : str
        实验室名（如 lottery / stock / medical）
    study : str
        研究组名（如 dlt / ssq / hs300_etf）
    root : str
        项目根目录

    Returns
    -------
    created_path : str
        创建的目录路径
    """
    study_dir = os.path.join(root, "labs", lab, "studies", study)

    # 目录结构
    dirs = [
        study_dir,
        os.path.join(study_dir, "data", "raw"),
        os.path.join(study_dir, "data", "derived"),
        os.path.join(study_dir, "data", "build_scripts"),
        os.path.join(study_dir, "iterations"),
        os.path.join(study_dir, "findings"),
        os.path.join(study_dir, "strategy"),
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 生成 game.yaml 模板
    game_yaml = f"""# game.yaml — {study} 研究组配置
# 由 tools/new_study.py 自动生成

study_id: "{study}"
lab: "{lab}"
created_at: "{date.today().isoformat()}"

# 数据版本（手动更新）
data:
  raw:
    path: "data/raw/{study}_full.csv"
    sha256: ""  # TODO: 放数据后填

# 特征声明（示例，按需修改）
features: []

# 机器参数（彩种相关，按需修改）
machine: {{}}
"""
    with open(os.path.join(study_dir, "game.yaml"), "w", encoding="utf-8") as f:
        f.write(game_yaml)

    # 生成 README.md
    readme = f"""# {study} 研究组

> 所属实验室：{lab}
> 创建日期：{date.today().isoformat()}

## 目录结构

```
{study}/
├── game.yaml           # 配置
├── data/               # 数据
│   ├── raw/            # 原始数据
│   └── derived/        # 派生数据
├── iterations/         # 研究轮次
├── findings/           # 结论库
└── strategy/           # 策略规则
```

## 快速开始

1. 把原始数据放到 `data/raw/`
2. 更新 `game.yaml` 里的 sha256
3. 开第一轮：`python cli/main.py new-round {study}`
"""
    with open(os.path.join(study_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    # 生成 findings/FACTS.jsonl 空文件
    with open(os.path.join(study_dir, "findings", "FACTS.jsonl"), "w", encoding="utf-8") as f:
        f.write("")

    print(f"✅ 新研究组已创建：{study_dir}")
    print(f"   下一步：")
    print(f"   1. 把原始数据放到 {study_dir}/data/raw/")
    print(f"   2. 更新 game.yaml 里的 sha256")
    print(f"   3. 开第一轮研究")

    return study_dir


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：python tools/new_study.py <lab> <study_name>")
        print("示例：python tools/new_study.py lottery ssq")
        sys.exit(1)
    new_study(sys.argv[1], sys.argv[2])
