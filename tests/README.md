# tests/ — 测试

> **版本**：`1.2` ｜ 轮次 `r03` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 现状

| 文件 | 项数 | 覆盖 |
|---|---|---|
| `test_core.py` | **113**（全绿） | 红线 / 原语 / Ticket / DSL / 作用域 / 数学 / 端到端 / 声明静态检查 |
| `test_cross_scope.py` | **62**（全绿） | ★ 跨注层：跨注原语 / `Portfolio` / `evaluate_cross` / `judge_cross` / 三路切分 / 端到端 / 铁律扫描 |
| `test_claim_type.py` | **43**（全绿） | ★ 证据类型：五类约束**真的会拦** / schema 与 Python 双通道一致 / 分类自洽 |
| `test_evidence_anchor.py` | **32**（全绿） | ★ 证据锚定：漂移真能检出 / 该敏感的要敏感、该迟钝的要迟钝 / 重基线幂等 |

无需 pytest、无需任何第三方测试框架 —— 直接用 Python 跑：

```bash
python tests/test_core.py
python tests/test_cross_scope.py
python tests/test_claim_type.py
python tests/test_evidence_anchor.py
```

退出码 0 = 全绿。失败项会在末尾单独列出（`✗` 打头 + 汇总表）。

## test_core.py 覆盖什么

按优先级排序（与本文档剩余的「应当测什么」一致）：

| # | 段 | 项数 | 内容 |
|---|---|---|---|
| 1 | **红线测试** | 4+ | 最高优先。特征名不含 `win_probability`；`disclaimer` 两个恒值；`optimizable_target` 只能是 `expected_bonus_given_win`；`sum_affects_numbers` 恒 false |
| 2 | **原语单测** | 30 | 21 个原语对固定输入给固定输出；连号专项（12-13 = 1 对，12-13-14 = 2 对，1-2-3-4-5 = 4 对）；参数缺失 / 未知原语 / 重复元素输入**必须报错** |
| 3 | **Ticket 校验** | 15 | 越界 / 少号 / 多号 / 重复 / 缺区 / 多区 全部被拒；可哈希可比较；`render()` 格式；单区彩种兼容 |
| 4 | **predicate DSL** | 14 | 6 个合法表达式通过；6 个非法（括号 / 混用 and-or / 右侧非字面量 / 取反 / 未知算子）明确报错 |
| 5 | **作用域切分** | 8 | ★ `R-001` → single，`R-002` → cross（附原因）；**跨注规则不被静默忽略** |
| 6 | **数学一致性** | 6 | `T = 21,425,712`；`T = C(35,5) × C(12,2)`；`p1 = 4.667289469773513e-08`；`p1 = 1/T`；选号不改概率；两注不同号码概率相同 |
| 7 | **端到端** | 9+ | 生成 20 注全部合规；注间唯一；单注求值**恰好**覆盖 11 个 `single` 特征、且**不含**任何 `cross` 特征；**同种子可复现**；不过滤时违规率 ≈ 理论值 8.9%；自相矛盾规则集报错 |
| 8 | **features 声明静态检查** | 6 | 真实 `game.yaml` 0 错；不存在的 primitive / 缺必需参数 / 引用不存在的区 / 重复 key 全部被检出 |

## test_cross_scope.py 覆盖什么

2.1 新增。核心命题：**跨注层不能再是"上报即完事"，必须真的能执行**。

| # | 段 | 内容 |
|---|---|---|
| 1 | 跨注原语是纯数学 | 对固定输入给固定输出；间隔向量同构判定（`gaps(1,3,5) == gaps(2,4,6)`） |
| 2 | `Portfolio` | 构造 / 校验 / 区集合一致性；**单注不包一层必须报错** |
| 3 | `evaluate_cross` | 整组上下文求值；对非 `cross` 特征**报错** |
| 4 | 结构性拒收混用 | `scope: cross` 挂单注原语（及反之）必须报错 —— 用 `deepcopy` 变异真实 `game.yaml` |
| 5 | `judge_cross` 真执行 R-002 | 同构组命中（权重 0.5）vs 多样组不命中（1.0） |
| 6 | `classify_rules` 三路切分 | 拼错的特征进 `undeclared`，**不**混进 `cross` |
| 7 | 端到端 `sample_batch` | 断言 `stats["cross_scope_evaluated"]` **存在**且真的执行过 |
| 8 | 铁律扫描 | `framework/core/` 无彩种常量 —— **AST 剥掉 docstring 与注释后再扫** |

> 第 8 段为什么要剥 docstring：`portfolio.py` 的 docstring 里**正列举着被禁止的字符串**
> （`"dlt"` / `"front"` / `大乐透`）。朴素全文本扫描会把"禁令清单"本身判成违规
> —— **会误报的检查比没有检查更坏**。

## 为什么不用 pytest

两个理由：

1. **零依赖**。本仓库要求 `pip install pyyaml jsonschema` 即可跑全部功能，
   引入 pytest 会让"跑一下测试"变成需要额外安装的动作。
2. **测试本身是文档**。`check(cond, label)` 的 label 直接就是断言的可读说明，
   失败时打印的是**一句中文结论**而不是 `AssertionError: assert 2 == 3`。

自建断言器只有 3 个：`check()` / `check_raises()` / `section()`。

## 尚未实现的部分（原计划中，暂缓）

以下是本目录最初设计里列出、但因「没有 CI + 只有一个彩种」而**暂缓**的测试。
它们不是不重要，是**性价比排序靠后**：

| 项 | 状态 | 启动时机 |
|---|---|---|
| 契约测试（schema 自合法 / 外键 / 双向取代 / source 存真） | ⚠️ 由 `cli/main.py validate --all` 覆盖（33 项） | 已由 CLI 承担 |
| `framework/` 无彩种专属内容扫描 | ⬜ 未实现 | 接入第二个彩种时 |
| 记忆层可读性（单一入口存在 / caveats 非空且 ≥10 字） | ⬜ 未实现 | 首次引入 CI 时 |
| 结论数字与 `game.yaml` 重算结果一致 | ⬜ 未实现 | 数据版本变更时 |

> **为什么这类测试重要**：`4.667e-08` 这个数字在仓库里出现在
> `FACTS.jsonl`、`strategy.json`、`game.yaml`、文档标题里。
> 若某处被改成 `4.67e-08`，现有校验**不会报警** ——
> 但它已经从"精确值"降级为"近似值"。

## 运行方式

```bash
# 核心测试（113 项）
python tests/test_core.py

# 跨注层测试（62 项）
python tests/test_cross_scope.py

# 证据类型测试（43 项）
python tests/test_claim_type.py

# 证据锚定测试（32 项）
python tests/test_evidence_anchor.py

# 契约校验（48 项，含 SHA256 一致性 / 证据锚定漂移 / 红线恒值）
python cli/main.py validate --all -v
```

**收轮时的强制步骤**：跑上面两条，都全绿才算完成
（已写入 `framework/protocol/ITERATION_PROTOCOL.md` §6）。

## 写新测试的风格约定

```python
def test_something() -> None:
    section("N. 段名")

    check(actual == expected, "中文断言说明（失败时直接可读）")
    check_raises(lambda: bad_call(), SpecificError, "某个非法输入必须报错")
```

三条规则：

1. **断言说明必须写"为什么"**，不要写 `"test 1"`。
2. **每个断言只测一件事**，失败时能立刻定位。
3. **"必须报错"的测试用 `check_raises` 并指定具体异常类型** ——
   `Exception` 太宽，会掩盖真正的 bug 类型。
