# -*- coding: utf-8 -*-
"""spc.core.stats — 高级统计方法库（彩种无关）

## 包含的模块

1. **FDR 校正**（Benjamini-Hochberg）—— 探索性研究假发现率控制
2. **Rolling-origin 交叉验证** —— 时序多切点验证
3. **贝叶斯因子** —— 后验概率 / Bayes Factor
4. **元分析** —— 多条同主题效应量加权合并 + 异质性检验
5. **前视偏差检查** —— 特征脚本静态扫描
6. **confidence 自动评分** —— 基于样本量/效应量/稳健性
7. **策略效果监控** —— 预期 vs 实际偏差检验

## 设计原则

- 纯函数，无副作用
- 输入输出都是 numpy array / 标准类型
- 所有方法都有默认参数，可直接调用
"""

from __future__ import annotations
import numpy as np
from typing import List, Tuple, Dict, Optional


# ============================================================
# 1. FDR 校正（Benjamini-Hochberg）
# ============================================================

def bh_fdr(pvalues: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """Benjamini-Hochberg FDR 校正。

    Parameters
    ----------
    pvalues : array
        原始 p 值数组
    alpha : float
        显著性水平（默认 0.05）

    Returns
    -------
    reject : array of bool
        每个 p 值是否拒绝零假设
    adjusted_p : array
        校正后的 p 值（FDR-adjusted）

    Notes
    -----
    与置换检验（FWER）的区别：
    - FWER（Family-Wise Error Rate）：控制"至少一个假阳性"的概率
    - FDR（False Discovery Rate）：控制"假发现占总发现的比例"

    探索性研究（筛 k 个候选找信号）用 FDR；
    确认性研究（验证某个特定效应）用 FWER。
    """
    p = np.asarray(pvalues, dtype=float)
    n = len(p)
    if n == 0:
        return np.array([], dtype=bool), np.array([])

    # 排序
    sorted_idx = np.argsort(p)
    sorted_p = p[sorted_idx]

    # 计算 adjusted p
    adjusted_sorted = np.zeros(n)
    adjusted_sorted[-1] = sorted_p[-1]
    for i in range(n - 2, -1, -1):
        adjusted_sorted[i] = min(
            sorted_p[i] * n / (i + 1),
            adjusted_sorted[i + 1]
        )

    # 还原顺序
    adjusted = np.zeros(n)
    adjusted[sorted_idx] = adjusted_sorted

    reject = adjusted < alpha
    return reject, adjusted


# ============================================================
# 2. Rolling-origin 交叉验证
# ============================================================

def rolling_origin_cv(
    data: np.ndarray,
    min_train: int,
    test_window: int,
    step: int = 1,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Rolling-origin 交叉验证（时序多切点）。

    Parameters
    ----------
    data : array
        时序数据（一维或二维，行是时间）
    min_train : int
        最小训练集大小
    test_window : int
        测试集窗口大小
    step : int
        每次滚动的步长

    Returns
    -------
    splits : list of (train_idx, test_idx)
        每个切点的训练集和测试集索引

    Examples
    --------
    >>> data = np.arange(100)
    >>> splits = rolling_origin_cv(data, min_train=60, test_window=10, step=10)
    >>> len(splits)
    3
    """
    n = len(data)
    splits = []
    t = min_train
    while t + test_window <= n:
        train_idx = np.arange(0, t)
        test_idx = np.arange(t, t + test_window)
        splits.append((train_idx, test_idx))
        t += step
    return splits


def rolling_origin_score(
    features: np.ndarray,
    target: np.ndarray,
    model_fn,
    min_train: int,
    test_window: int,
    step: int = 1,
    score_fn=None,
) -> Dict:
    """Rolling-origin 交叉验证并打分。

    Parameters
    ----------
    features : array, shape (n, d)
        特征矩阵
    target : array, shape (n,)
        目标变量
    model_fn : callable
        模型函数：(X_train, y_train) -> model
    min_train : int
        最小训练集大小
    test_window : int
        测试集窗口大小
    step : int
        滚动步长
    score_fn : callable, optional
        评分函数：(model, X_test, y_test) -> float
        默认用 R²

    Returns
    -------
    result : dict
        scores: 每个切点的分数列表
        mean_score: 平均分
        std_score: 分数标准差
        n_splits: 切点数
    """
    if score_fn is None:
        score_fn = _r2_score

    splits = rolling_origin_cv(features, min_train, test_window, step)
    scores = []
    for train_idx, test_idx in splits:
        X_train, y_train = features[train_idx], target[train_idx]
        X_test, y_test = features[test_idx], target[test_idx]
        model = model_fn(X_train, y_train)
        s = score_fn(model, X_test, y_test)
        scores.append(s)

    return {
        "scores": scores,
        "mean_score": float(np.mean(scores)) if scores else None,
        "std_score": float(np.std(scores)) if scores else None,
        "n_splits": len(scores),
    }


def _r2_score(model, X_test, y_test) -> float:
    """默认 R² 评分。"""
    y_pred = model.predict(X_test)
    ss_res = np.sum((y_test - y_pred) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - ss_res / ss_tot


# ============================================================
# 3. 贝叶斯因子 / 后验概率
# ============================================================

def bayes_factor_normal(
    observed_effect: float,
    se: float,
    prior_mean: float = 0.0,
    prior_sd: float = 1.0,
) -> Dict:
    """正态-正态模型的贝叶斯因子（H₀: effect=0 vs H₁: effect~N(prior_mean, prior_sd)）。

    Parameters
    ----------
    observed_effect : float
        观测到的效应量
    se : float
        效应量的标准误
    prior_mean : float
        H₁ 先验均值（默认 0，即对称先验）
    prior_sd : float
        H₁ 先验标准差（默认 1.0）

    Returns
    -------
    result : dict
        bf10: Bayes Factor（H₁ vs H₀）
        post_prob: H₁ 后验概率（假设 H₀/H₁ 先验各 0.5）
        interpretation: 文字解释

    Notes
    -----
    Bayes Factor 解读（Kass & Raftery, 1995）：
    - BF < 1: 支持 H₀
    - 1 < BF < 3: 弱证据支持 H₁
    - 3 < BF < 10: 中等证据支持 H₁
    - 10 < BF < 30: 强证据支持 H₁
    - 30 < BF < 100: 很强证据支持 H₁
    - BF > 100: 极强证据支持 H₁
    """
    from scipy import stats

    # H₀ 下的似然：effect ~ N(0, se²)
    likelihood_h0 = stats.norm.pdf(observed_effect, loc=0, scale=se)

    # H₁ 下的边缘似然：effect ~ N(prior_mean, se² + prior_sd²)
    marginal_h1 = stats.norm.pdf(
        observed_effect,
        loc=prior_mean,
        scale=np.sqrt(se ** 2 + prior_sd ** 2)
    )

    bf10 = marginal_h1 / likelihood_h0 if likelihood_h0 > 0 else float("inf")

    # 后验概率（先验各 0.5）
    post_prob_h1 = bf10 / (1 + bf10)

    # 解读
    if bf10 < 1:
        interp = "支持 H₀（无效应）"
    elif bf10 < 3:
        interp = "弱证据支持 H₁"
    elif bf10 < 10:
        interp = "中等证据支持 H₁"
    elif bf10 < 30:
        interp = "强证据支持 H₁"
    elif bf10 < 100:
        interp = "很强证据支持 H₁"
    else:
        interp = "极强证据支持 H₁"

    return {
        "bf10": float(bf10),
        "post_prob_h1": float(post_prob_h1),
        "interpretation": interp,
    }


# ============================================================
# 4. 元分析（Meta-Analysis）
# ============================================================

def meta_analysis(
    effect_sizes: List[float],
    standard_errors: List[float],
) -> Dict:
    """固定效应 + 随机效应元分析。

    Parameters
    ----------
    effect_sizes : list of float
        各研究的效应量
    standard_errors : list of float
        各研究效应量的标准误

    Returns
    -------
    result : dict
        fe_estimate: 固定效应估计
        fe_se: 固定效应标准误
        fe_z: 固定效应 z 值
        fe_p: 固定效应 p 值
        re_estimate: 随机效应估计（DerSimonian-Laird）
        re_se: 随机效应标准误
        tau2: 异质性方差估计
        i_squared: I² 统计量（%）
        q_statistic: Cochran's Q
        q_p: Q 检验 p 值

    Notes
    -----
    I² 解读（Higgins et al., 2003）：
    - I² < 25%: 低异质性
    - 25% < I² < 50%: 中等异质性
    - I² > 50%: 高异质性
    """
    from scipy import stats

    es = np.asarray(effect_sizes)
    se = np.asarray(standard_errors)
    k = len(es)

    # 权重（固定效应 = 1/se²）
    w = 1.0 / se ** 2

    # 固定效应估计
    fe_est = np.sum(w * es) / np.sum(w)
    fe_se = np.sqrt(1.0 / np.sum(w))
    fe_z = fe_est / fe_se
    fe_p = 2 * (1 - stats.norm.cdf(abs(fe_z)))

    # Cochran's Q
    q = np.sum(w * (es - fe_est) ** 2)
    q_df = k - 1
    q_p = 1 - stats.chi2.cdf(q, q_df) if q_df > 0 else 1.0

    # I²
    i_squared = max(0, (q - q_df) / q * 100) if q > 0 else 0

    # DerSimonian-Laird 随机效应
    tau2 = max(0, (q - q_df) / (np.sum(w) - np.sum(w ** 2) / np.sum(w))) if k > 1 else 0

    # 随机效应权重
    w_re = 1.0 / (se ** 2 + tau2)
    re_est = np.sum(w_re * es) / np.sum(w_re)
    re_se = np.sqrt(1.0 / np.sum(w_re))

    return {
        "fe_estimate": float(fe_est),
        "fe_se": float(fe_se),
        "fe_z": float(fe_z),
        "fe_p": float(fe_p),
        "re_estimate": float(re_est),
        "re_se": float(re_se),
        "tau2": float(tau2),
        "i_squared": float(i_squared),
        "q_statistic": float(q),
        "q_p": float(q_p),
        "n_studies": k,
    }


# ============================================================
# 5. 前视偏差检查（Look-ahead Bias Check）
# ============================================================

def check_lookahead_bias(script_path: str) -> Dict:
    """静态扫描特征脚本，检查是否存在前视偏差。

    检查内容：
    - 是否用了未来期的数据（如 df.iloc[t+1] / df.shift(-1)）
    - 是否用了全样本统计量（如 df.mean() 而非 rolling().mean()）

    Parameters
    ----------
    script_path : str
        脚本文件路径

    Returns
    -------
    result : dict
        has_lookahead: bool
        warnings: list of str
        line_numbers: list of int
    """
    warnings = []
    line_numbers = []

    # 前视偏差的常见模式
    suspicious_patterns = [
        ("shift(-1)", "用了未来一期的数据（shift(-1)）"),
        ("shift(-2)", "用了未来两期的数据（shift(-2)）"),
        (".iloc[t+1]", "用了未来索引（iloc[t+1]）"),
        (".iloc[t+2]", "用了未来索引（iloc[t+2]）"),
        (".rolling(window=", "确认 rolling 是否对齐到当前期（closed='right'）"),
        (".expanding(", "确认 expanding 是否只用到当前期"),
        (".mean()", "⚠️ 全样本均值可能是前视偏差——应改用 rolling()"),
        (".std()", "⚠️ 全样本标准差可能是前视偏差——应改用 rolling()"),
    ]

    try:
        with open(script_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return {"has_lookahead": None, "warnings": ["无法读取文件"], "line_numbers": []}

    for i, line in enumerate(lines, 1):
        for pattern, msg in suspicious_patterns:
            if pattern in line:
                warnings.append(f"  行 {i}: {msg} → {line.strip()}")
                line_numbers.append(i)

    return {
        "has_lookahead": len(warnings) > 0,
        "warnings": warnings,
        "line_numbers": line_numbers,
    }


# ============================================================
# 6. Confidence 自动评分
# ============================================================

def auto_confidence_score(
    n: int,
    effect_size: float,
    robust: bool = True,
    out_of_sample: bool = False,
    multiple_testing_corrected: bool = True,
) -> Dict:
    """基于样本量/效应量/稳健性自动计算 confidence 评分。

    Parameters
    ----------
    n : int
        样本量
    effect_size : float
        效应量（绝对值）
    robust : bool
        是否通过稳健性复核（重尾/分期）
    out_of_sample : bool
        是否通过样本外验证
    multiple_testing_corrected : bool
        是否通过多重比较校正

    Returns
    -------
    result : dict
        score: 1-5 分
        grade: low / moderate / high
        breakdown: 各项得分明细
    """
    breakdown = {}

    # 样本量分（0-2）
    if n >= 1000:
        breakdown["sample_size"] = 2
    elif n >= 100:
        breakdown["sample_size"] = 1
    else:
        breakdown["sample_size"] = 0

    # 效应量分（0-1.5）
    if effect_size >= 0.2:
        breakdown["effect_size"] = 1.5
    elif effect_size >= 0.1:
        breakdown["effect_size"] = 1.0
    elif effect_size >= 0.05:
        breakdown["effect_size"] = 0.5
    else:
        breakdown["effect_size"] = 0

    # 稳健性分（0-0.5）
    breakdown["robustness"] = 0.5 if robust else 0

    # 样本外分（0-1）
    breakdown["out_of_sample"] = 1.0 if out_of_sample else 0

    # 多重比较校正分（0-0.5）
    breakdown["multiple_testing"] = 0.5 if multiple_testing_corrected else 0

    # 总分（满分 5.5，映射到 1-5）
    total = sum(breakdown.values())
    score = min(5, max(1, round(total)))

    if score >= 4:
        grade = "high"
    elif score >= 3:
        grade = "moderate"
    else:
        grade = "low"

    return {
        "score": score,
        "grade": grade,
        "breakdown": breakdown,
    }


# ============================================================
# 7. 策略效果监控
# ============================================================

def monitor_strategy_effect(
    expected_effect: float,
    observed_effect: float,
    observed_se: float,
    tolerance: float = 0.5,
) -> Dict:
    """监控策略预期效果 vs 实际效果的偏差。

    Parameters
    ----------
    expected_effect : float
        策略预期效果（如预期撞号率降低 20%）
    observed_effect : float
        实际观测效果
    observed_se : float
        实际效果的标准误
    tolerance : float
        容忍比例（默认 0.5 = 允许偏差 50%）

    Returns
    -------
    result : dict
        deviation: 偏差比例（(observed - expected) / expected）
        z_score: 偏差的 z 值
        alarm: 是否报警
        status: ok / warning / critical
    """
    if expected_effect == 0:
        return {"alarm": None, "status": "cannot_evaluate", "deviation": None}

    deviation = (observed_effect - expected_effect) / abs(expected_effect)
    z_score = (observed_effect - expected_effect) / observed_se if observed_se > 0 else 0

    abs_dev = abs(deviation)
    if abs_dev < tolerance * 0.5:
        status = "ok"
        alarm = False
    elif abs_dev < tolerance:
        status = "warning"
        alarm = False
    else:
        status = "critical"
        alarm = True

    return {
        "deviation": float(deviation),
        "z_score": float(z_score),
        "alarm": alarm,
        "status": status,
    }


# ============================================================
# 8. 规则交互效应（Factorial Design）
# ============================================================

def factorial_design(
    rule_effects: Dict[str, float],
    interaction_matrix: Optional[np.ndarray] = None,
) -> Dict:
    """计算规则组合的边际效应（含交互项）。

    Parameters
    ----------
    rule_effects : dict
        每条规则的单独效应 {rule_id: effect}
    interaction_matrix : array, shape (n_rules, n_rules), optional
        规则间交互效应矩阵

    Returns
    -------
    result : dict
        total_effect: 所有规则叠加的总效应
        synergy: 协同效应（实际组合 - 简单加总）
        recommendations: 推荐的规则组合
    """
    rules = list(rule_effects.keys())
    n = len(rules)

    # 简单加总
    simple_sum = sum(rule_effects.values())

    # 交互效应
    if interaction_matrix is not None:
        interaction_sum = np.sum(interaction_matrix) / 2  # 对称矩阵，除以2
    else:
        interaction_sum = 0

    total = simple_sum + interaction_sum
    synergy = interaction_sum

    return {
        "total_effect": float(total),
        "simple_sum": float(simple_sum),
        "synergy": float(synergy),
        "n_rules": n,
    }
