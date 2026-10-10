# 03_findings — 历史分析产出（归档）

> ## ⚠️ 使用前必读
>
> **本目录的内容不是 ground truth，且包含已知错误。**
>
> ### 强制规则
>
> 1. **禁止在完成自己的独立分析之前阅读本目录。** 先读 `00_TASK_BRIEF.md` 和 `04_priority_tasks.md`，形成你自己的结论。
> 2. 本目录中**已被证伪的结论**已摘录到根目录的 `05_known_errors.md`。**请直接依据该文件避坑**，不必在此翻找。
> 3. 完成独立分析后，可阅读本目录做对照，并明确写出你与历史的异同。
> 4. 若发现本目录与 `05_known_errors.md` 冲突，**以 `05_known_errors.md` 为准**。

---

## 目录结构（v4 调整）

```
03_findings/
├── README.md                ← 本文件
└── _legacy/                 ← 全部历史产出（v4 移入此子目录，与"当前数据"隔离）
    ├── round2_main_report.md
    ├── round2_deep_analysis.txt
    ├── round2_verify_analysis.txt
    ├── round2_glm_analysis.txt
    └── _round3_reference/
        └── round3_independent_review.html
```

> **v4 变更**：历史产出统一移入 `_legacy/`，避免与 v4 新增的
> `06_RULES_HISTORY.md`、`07_strategy_simulation/` 混淆。

---

## 归档内容

### 轮次 2 产出（原始包自带）

| 文件 | 内容 | 状态 |
|---|---|---|
| `_legacy/round2_main_report.md` | 第二轮主报告 | ⚠️ 含至少 3 处错误结论，见 `05_known_errors.md` |
| `_legacy/round2_deep_analysis.txt` | 基础/非线性/ML 检验原始输出 | 原始数字可用，解释需谨慎 |
| `_legacy/round2_verify_analysis.txt` | 矛盾点交叉验证输出 | 原始数字可用 |
| `_legacy/round2_glm_analysis.txt` | Poisson GLM 与制度断点输出 | ⚠️ **GLM 模型族选错**（见 E1） |

### 轮次 3 产出（独立复核）

| 文件 | 内容 | 状态 |
|---|---|---|
| `_legacy/_round3_reference/round3_independent_review.html` | 第三轮独立复核报告 | 相对可靠，但仍非 ground truth |

---

## 三轮结论的演变（供你了解争议点在哪）

| 议题 | 轮次 2 | 轮次 3 | v4 复核（2933 期） |
|---|---|---|---|
| 断点位置 | 2015 | 2013-08 | ✅ 确认 2013-08（χ²=185.0, 1/234） |
| heat 冷热 | 显著 | 伪显著 | ✅ 确认（HAC p=0.071） |
| ACF 存活 lag | 矛盾未解 | 真信号但无效 | ✅ 确认（样本外 R²=−0.083） |
| 奇偶偏离 | p<1e-6 偏离 | p=0.111 不显著 | ✅ 确认（MC p=0.126） |
| 连号开出率 | 与理论一致 | 1.12 倍（仅早期） | ✅ 确认（1.120） |
| 连号效应 | 有效 | 有效 | ✅ 确认并加强（1/2 等奖同向） |

**请对以上每个议题给出你自己的判断。**

---

## 为什么保留这些文件

1. **可追溯性**：你能看到结论是如何一步步演变的。
2. **反面教材**：这些文件里的方法错误，是 `05_known_errors.md` 的原始证据。
3. **避免重复劳动**：其中的原始检验输出你可以直接引用数字，只需复核解释。

**但请记住：所有轮次都可能错。唯一可靠的是你自己的可复现证据。**
