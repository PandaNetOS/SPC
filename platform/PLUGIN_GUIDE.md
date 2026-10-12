# PLUGIN_GUIDE.md — 插件开发指南

> 新实验室类型只需实现以下接口，就能挂到底座平台上。

---

## 插件接口

每个实验室类型（如彩票/股票/医学）需要实现：

### 1. 问题定义接口

```python
class LabPlugin:
    """实验室插件基类。"""

    # 实验室名
    name = "lottery"

    # 描述
    description = "彩票实验室"

    def get_problem_definition(self) -> dict:
        """返回问题定义。"""
        return {
            "type": "lottery",
            "has_strategy": True,       # 有没有策略规则
            "has_collision": True,      # 有没有撞号概念
            "data_format": "csv",       # 数据格式
        }

    def validate_config(self, config: dict) -> list:
        """校验研究组配置，返回错误列表。"""
        errors = []
        # 示例：检查号码池大小
        if "machine" not in config:
            errors.append("缺少 machine 配置")
        return errors

    def get_required_fields(self) -> list:
        """返回该实验室类型必填的配置字段。"""
        return ["machine"]
```

---

## 现有实验室类型

| 实验室 | 插件类 | 说明 |
|---|---|---|
| lottery | LotteryLabPlugin | 彩票（大乐透/双色球） |
| stock | StockLabPlugin（待开发） | 股票/ETF |
| medical | MedicalLabPlugin（待开发） | 医学实验 |

---

## 如何新增实验室类型

1. 在 `labs/<lab>/` 下建目录
2. 写 `problem.yaml` 定义问题类型
3. 实现 `LabPlugin` 接口
4. 用 `tools/new_study.py <lab> <study>` 创建研究组

---

## 示例：彩票实验室插件

```python
class LotteryLabPlugin:
    name = "lottery"
    description = "彩票实验室（含彩民行为分析）"

    def get_problem_definition(self):
        return {
            "type": "lottery",
            "has_strategy": True,
            "has_collision": True,
            "data_format": "csv",
            "features_scope": ["single", "cross"],
        }

    def validate_config(self, config):
        errors = []
        machine = config.get("machine", {})
        if "zones" not in machine:
            errors.append("彩票实验室需要 machine.zones 配置")
        return errors
```
