# tests/ — 测试

## 现状

**未实现。** 本目录为后续测试预留。

## 应当测什么

按重要性排序：

### 1. 红线测试（最高优先）

红线的存在意义就是"不能违反"。必须有意图违反的测试用例：

```python
def test_red_line_rejects_win_probability_claim():
    """试图写入 affects_win_probability=True 必须被拒。"""
    mem = Memory(repo_root)
    with pytest.raises(RedLineViolation):
        mem.add_fact({... "affects_win_probability": True ...})

def test_strategy_loader_rejects_bad_disclaimer():
    """changes_win_probability=True 的 strategy.json 必须拒绝解析。"""
```

### 2. 契约测试

| 测试 | 断言 |
|---|---|
| schema 校验 | 每个 schema 都能被 jsonschema 解析（schema 自身合法） |
| 红线恒值 | 现有 `strategy.json` 的四条红线全部合规 |
| 外键 | `evidence_refs` 全部存在于 `FACTS.jsonl` |
| 双向取代 | `supersedes` ↔ `superseded_by` 一致 |
| 文件存在 | `source` / `evidence.script` / `deliverables` 指向真实文件 |

### 3. 数学一致性测试

这是最容易出隐性错误的地方 —— **数值被抄错不会报错，只会静默给出错误结论**：

```python
def test_total_combinations():
    cfg = load_game_config("dlt")
    assert compute_space(cfg)["total_combinations"] == 21_425_712

def test_first_prize_probability():
    assert abs(compute_space(cfg)["first_prize_probability"] - 4.667289469773513e-08) < 1e-20

def test_fact_numbers_agree_with_game_config():
    """FACTS.jsonl 里的 T 与 p1 应与 game.yaml 重算结果一致。"""
    f1 = mem.fact("F-0001")
    assert f1["evidence"]["effect"]["total_combinations"] == 21_425_712
```

> **为什么这类测试重要**：`4.667e-08` 这个数字在仓库里出现在
> `FACTS.jsonl`、`strategy.json`、`game.yaml`、文档标题里。
> 若某处被改成 `4.67e-08`，没有任何校验会报警 —— 但它已经从"精确值"降级为"近似值"。
> 测试是唯一能捕获这种漂移的机制。

### 4. 聚类/AI 可读性测试

```python
def test_single_entry_exists():
    """单一入口 AI_CONTEXT.md 必须存在且被 README 引用。"""

def test_every_fact_has_source_file():
    """每条结论的 source 必须真实存在（可追溯性的底线）。"""

def test_every_caveat_is_actionable():
    """caveats 非空且长度 >= 10（防止写成 'N/A' 敷衍）。"""
```

### 5. 框架/彩种分离测试

```python
def test_framework_has_no_game_specifics():
    """framework/ 下的 .md 与 .py 不得出现具体彩种参数。"""
    forbidden = ["21425712", "21,425,712", "4.667e-08", "dlt", "大乐透"]
    for root, _, files in os.walk("framework"):
        for fn in files:
            if fn.endswith((".md", ".py")):
                text = open(os.path.join(root, fn), encoding="utf-8").read()
                for bad in forbidden:
                    assert bad not in text, f"{root}/{fn} 含彩种专属内容: {bad}"
```

## 为什么不现在写

**因为当前没有 CI，也没有第二个彩种。**

一个只有 5 个测试、手动运行的测试目录，比一个 50 个测试但从不运行的目录更有价值。
但反过来说：**红线测试现在就该写** —— 因为红线是"违反即严重错误"的那一类。

**启动时机**：接入第二个彩种时（`T-031`），或首次引入 CI 时。

## 运行方式（待实现后）

```bash
python -m pytest tests/ -v
# 或
python tests/run_all.py
```

## 当前可用的替代校验

CLI 已覆盖大部分契约检查：

```bash
python cli/main.py validate --all -v
```

它检查 28 项，含 SHH256 一致性与红线恒值。
**在测试目录实现之前，请把 `validate --all` 作为收轮的强制步骤**
（已写入 `framework/protocol/ITERATION_PROTOCOL.md` §6）。
