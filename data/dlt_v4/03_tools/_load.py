# -*- coding: utf-8 -*-
"""_load.py — 统一数据装载器（所有工具脚本共用）

从包内 CSV 读取原始数据，并重建派生列（log_sale / run / heat / sum_z / span_z 等）。
所有工具脚本 `from _load import load_df` 后调用即可，保证口径一致且自包含。

用法：
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _load import load_df
    df = load_df()
"""
import os
import numpy as np
import pandas as pd

# 包根目录（本文件位于 <pkg>/03_tools/，上一级为包根）
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# v4：数据源为 2933 期（含最新 26115 期，2026-10-10）
_CSV = os.path.join(_PKG_ROOT, '01_data', 'dlt_full_2933.csv')
# 工具脚本输出目录（与脚本同级，自动创建）
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')


def out_path(name):
    """返回 output/ 下的输出路径，并确保目录存在。"""
    os.makedirs(OUTDIR, exist_ok=True)
    return os.path.join(OUTDIR, name)


def load_df(path=None):
    """装载数据并补齐派生列。

    ⚠️ draw_num 强制为字符串（带前导零，'07001'）；漏掉会变成整数 7001。
    """
    p = path or _CSV
    df = pd.read_csv(p, encoding='utf-8-sig', dtype={'draw_num': str})

    F = df[[f'front_{i}' for i in range(1, 6)]].values

    # ---- 派生列（与原 scripts/df_stage.pkl 口径一致）----
    # 销量对数
    if 'sale_yuan' in df.columns:
        df['log_sale'] = np.log(df['sale_yuan'].astype(float))

    # 连号对数 run = 前区中相邻差为 1 的对数
    if 'run' not in df.columns:
        df['run'] = [int((np.diff(r) == 1).sum()) for r in F]

    # run_ge2 = run >= 2 的指示
    df['run_ge2'] = (df['run'] >= 2).astype(int)

    # 和值 / 跨度 的标准化（全样本口径，仅用于演示；做预测时须改滚动口径，见 E6）
    if 'front_sum' in df.columns:
        s = df['front_sum'].astype(float)
        df['sum_z'] = (s - s.mean()) / s.std(ddof=0)
    if 'front_span' in df.columns:
        sp = df['front_span'].astype(float)
        df['span_z'] = (sp - sp.mean()) / sp.std(ddof=0)

    # 后区跨度（若原始数据没有）
    if 'back_span' not in df.columns:
        B = df[[f'back_{i}' for i in range(1, 3)]].values
        df['back_span'] = B.max(1) - B.min(1)

    # heat = 组合冷热（组合历史频率的均值 / 平均频率），全样本口径
    #  ⚠️ 该定义含前视偏差（E6），此处仅为复现历史讨论；正确做法见 05_known_errors.md
    if 'heat' not in df.columns:
        cnt = np.zeros(36, dtype=float)
        raw_heat = np.full(len(df), np.nan)
        for t, r in enumerate(F):
            if t >= 1:
                raw_heat[t] = cnt[r].mean() / (cnt[1:].sum() / 35.0)
            for v in r:
                cnt[v] += 1
        fill = np.nanmean(raw_heat)
        raw_heat[np.isnan(raw_heat)] = fill
        df['heat'] = raw_heat

    return df


if __name__ == '__main__':
    d = load_df()
    print('shape:', d.shape)
    print('cols:', list(d.columns))
    print('draw_num first/last:', d.draw_num.iloc[0], d.draw_num.iloc[-1])
