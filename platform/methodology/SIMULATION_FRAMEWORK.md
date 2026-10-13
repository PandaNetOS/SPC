# SIMULATION_platform.md — 策略效果模拟验证框架

> **版本**：`1.0` ｜ 轮次 `r17` ｜ 更新 2026-10-12 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **本文件定义"策略落地后，怎么验证预期效果是不是真的"。**

---

## 0. 为什么需要模拟验证

策略落地时我们说：
- R-001 能降低撞号率 20%
- R-003 能避开生日号区人群
- R-005 偏好冷门形态

**但实际跑起来才知道效果对不对。**

模拟验证 = 用历史数据回测"如果按策略选号，预期效果是多少"，和实际观测对比。

---

## 1. 模拟验证三步法

### Step 1：定义策略规则

把 strategy.json 的规则转成"选号过滤器"：

```python
def apply_strategy(tickets, strategy_rules):
    """按策略规则过滤号码。"""
    filtered = []
    for ticket in tickets:
        if passes_all_rules(ticket, strategy_rules):
            filtered.append(ticket)
    return filtered
```

### Step 2：历史数据回测

```python
def backtest(historical_data, strategy_rules, n_simulations=10000):
    """用历史数据回测策略效果。"""
    results = []
    for period in historical_data:
        # 模拟按策略选号
        simulated_tickets = apply_strategy(period.all_possible_tickets, strategy_rules)
        # 计算撞号率
        collision_rate = compute_collision_rate(simulated_tickets, period.winning_numbers)
        results.append(collision_rate)
    return np.mean(results), np.std(results)
```

### Step 3：预期 vs 实际对比

```python
expected = 0.8  # 预期撞号率降低 20%
observed = backtest(...)
deviation = (observed - expected) / expected
```

---

## 2. 模拟的假设清单

**模拟必须显式列出假设**：

| 假设 | 说明 | 风险 |
|---|---|---|
| H1：彩民行为稳定 | 历史上的选号模式未来不变 | 彩民行为会变 |
| H2：号码均匀分布 | 每个组合被选中的概率相同（除了策略调整） | 实际不均匀 |
| H3：规则不变 | 模拟期间规则不改变 | 规则可能变 |

**置信度评级**：
- ★★★★★：假设全部成立，模拟可信
- ★★★☆☆：部分假设存疑，模拟仅作参考
- ★★☆☆☆：假设不成立，模拟不可用

---

## 3. 策略效果监控

模拟验证不是一次性的事，需要持续监控：

```python
def monitor(strategy_id, expected_effect, observed_effect, observed_se):
    """监控策略效果偏差。"""
    deviation = (observed_effect - expected_effect) / abs(expected_effect)
    z = (observed_effect - expected_effect) / observed_se

    if abs(deviation) < 0.1:
        return "OK"
    elif abs(deviation) < 0.3:
        return "WARNING"
    else:
        return "CRITICAL — 策略效果衰减，需要重新评估"
```

**监控频率**：
- 每 50 期检查一次
- 偏差超 30% → 报警
- 偏差超 50% → 策略下线重评

---

## 4. 本项目的模拟验证计划

| 策略 | 预期效果 | 模拟方法 | 状态 |
|---|---|---|---|
| R-001 避连号 | 撞号率降低 ~10% | 历史回测 | 待做 |
| R-003 避生日号区 | 撞号率降低 ~15% | 历史回测 | 待做 |
| R-005 冷门形态偏好 | 撞号率降低 ~5% | 历史回测 | 待做 |

**回测数据源**：`labs/lottery/studies/dlt/data/raw/dlt_full_2933.csv`（2933 期）

---

## 5. 边界声明

**模拟能做的**：
- 验证策略在历史数据上的预期效果
- 估计策略效果的不确定性（CI）

**模拟不能做的**：
- 预测未来（彩民行为会变）
- 保证未来效果和历史一致
- 替代真实市场测试
