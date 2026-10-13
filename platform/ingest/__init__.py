# -*- coding: utf-8 -*-
"""platform.ingest — 数据接入管道（CP-002 P1/P2）

彩种无关的通用管道。**本包不得出现任何彩种名或号码池常量** ——
数据源与字段映射全部来自 `game.yaml` 的 `data_source` 声明。

阶段：fetch → normalize → merge → validate → seal
用法见 platform/ingest/README.md
"""
from .pipeline import run_pipeline, fetch_endpoint, normalize_draw
from .seal import seal_dataset

__all__ = ["run_pipeline", "fetch_endpoint", "normalize_draw", "seal_dataset"]
