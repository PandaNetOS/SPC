# HANDOFF.md — roundNN 交接（模板）

> **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **使用方式**：复制到 `games/<game>/iterations/roundNN/HANDOFF.md`。
>
> **最重要的要求**：本文件的「遗留问题」+「下轮建议」
> **必须转写为下一轮的 `TASK_BRIEF.md`**。不做这一步，迭代链就断了。

---

# HANDOFF.md — roundNN → roundNN+1

| 项 | 内容 |
|---|---|
| **完成轮次** | `roundNN` |
| **彩种** | `<game_id>` |
| **日期** | `YYYY-MM-DD` |
| **状态** | `delivered` / `in_progress`（未完成时说明卡在哪） |
| **数据版本** | `<data_version>` |

---

## 1. 本轮结论清单

### 1.1 新增

| id | 结论 | 状态 | 置信度 | 引用类别 |
|---|---|---|---|---|
| `F-00xx` | 〈一句话〉 | `established` | ★★★★☆ | 观测 |
| `F-00yy` | 〈一句话〉 | `tentative` | ★★☆☆☆ | 模型估计 |

### 1.2 更新

| id | 改了什么 | 原因 |
|---|---|---|
| `F-00zz` | `caveats` 增加第 n 条 | 分期稳健性检验发现… |

### 1.3 取代 / 推翻

| 旧 id | 新 id | 原因 |
|---|---|---|
| `F-00ww` | `F-00vv` | 旧结论口径错误 |

> 别忘了**双向**填写 `supersedes` / `superseded_by`。

---

## 2. 遗留问题（按优先级）

| 优先级 | 问题 | 关联 | 建议脚本 | 为什么重要 |
|---|---|---|---|---|
| **P0** | `Q-0xx`：〈...〉 | `F-00xx` caveat #1 | `scripts/xxx.py` | 〈...〉 |
| **P1** | `Q-0yy`：〈...〉 | `H-00x` | `scripts/yyy.py` | 〈...〉 |
| **P2** | `Q-0zz`：〈...〉 | — | 〈...〉 | 〈...〉 |

**P0 的定义**：不做会**导致现有对外输出错误**，或**阻塞后续工作**。

---

## 3. 下轮建议（明确推荐）

**建议 roundNN+1 优先攻**：

1. **`Q-0xx`**（P0）
   理由：〈...〉
   预计产出：〈结论 id 范围〉

2. **`Q-0yy`**（P0）
   理由：〈...〉

3. **`Q-0zz`**（P1）
   理由：〈...〉

**不建议本轮做的**：〈列出并说明为什么现在不做〉

---

## 4. 框架改进建议（自我迭代的元层面产出）

> 这是"每轮 AI 给出更好的研究框架"的具体落地。
> 提案进入 `workbench/TODO.md` 的 P4 段，由后续轮次评审。

| # | 建议 | 理由 | 影响面 |
|---|---|---|---|
| R-1 | 〈对 schema / 协议 / 流程的改进〉 | 〈为什么〉 | 〈哪些文件要改〉 |
| R-2 | 〈...〉 | 〈...〉 | 〈...〉 |

**评审规则**：`accepted` 的提案须记入 `spec/VERSIONING.md` 变更日志；
`rejected` 的也要记录（保留"曾经这么想过"）。

---

## 5. 本轮踩的坑（→ LESSONS）

| 新教训 | 症状 | 检测方法 | 是否已追加到 `LESSONS.md` |
|---|---|---|---|
| `L〈n〉`：〈...〉 | 〈...〉 | 〈...〉 | ✅ / ❌ |

> **若本轮踩了一个新坑但没写进 LESSONS，下轮会再踩一次。**
> 这是本仓库最不可接受的遗漏。

---

## 6. 给下轮执行者的提醒

### 6.1 最容易被误用的结论

| 结论 | 误用方式 | 正确用法 |
|---|---|---|
| `F-00xx` | 〈...〉 | 〈...〉 |

### 6.2 最不该信的推断

〈明确指出哪条结论的强度被高估了，以及为什么。〉

### 6.3 环境/路径注意事项

- 数据读取：`encoding="utf-8-sig"` + `dtype={"draw_num": str}`
- 〈其它坑〉

### 6.4 若时间/精力有限，只做这一件事

〈指一个 20% 投入能带来 80% 价值的具体动作。〉

---

## 7. 本轮工作记忆变化

| 文件 | 变化 |
|---|---|
| `memory/facts/FACTS.jsonl` | +n 条，改 m 条 |
| `memory/lessons/LESSONS.md` | +n 条（`L<sub>id</sub>`） |
| `memory/workbench/OPEN_QUESTIONS.md` | +n 问，`Q-0xx` 标 answered |
| `memory/workbench/HYPOTHESES.md` | `H-00x` 标 verified / refuted |
| `memory/workbench/TODO.md` | 清 n 项，新增 m 项 |
| `memory/journal/roundNN.md` | 新建 |

---

## 8. 校验状态

```bash
python cli/main.py validate --all
```

结果：〈✅ 通过 / ❌ 有 n 项报错：列出〉

> **校验不通过 = 本轮未完成**，`status` 不得标 `delivered`。

---

## 9. 下一轮 TASK_BRIEF 已生成

- [ ] 已创建 `games/<game>/iterations/roundNN+1/TASK_BRIEF.md`
- [ ] 已填入：目标 + 验收判据 + 陷阱提醒（可从本文件第 2、3、6 节直接转写）
- [ ] 已创建 `games/<game>/iterations/roundNN+1/manifest.json`（`status: planned`）

> **这三项是本协议最重要的一条。缺了它，迭代链断裂。**

---

## 10. 交付物清单

| 路径 | 说明 |
|---|---|
| `games/<game>/iterations/roundNN/TASK_BRIEF.md` | 任务书 |
| `games/<game>/iterations/roundNN/FINDINGS.md` | 发现与证据 |
| `games/<game>/iterations/roundNN/HANDOFF.md` | 本文件 |
| `games/<game>/iterations/roundNN/manifest.json` | 机器可读索引 |
| `games/<game>/iterations/roundNN/scripts/*.py` | 复现脚本 |
| `memory/facts/FACTS.jsonl` | 更新 |
| `memory/lessons/LESSONS.md` | 更新 |
| `memory/journal/roundNN.md` | 新建 |
| `games/<game>/strategy/strategy.json` | 若策略变化则更新 |

---

*交接的本质：让下一轮执行者**不需要读你的 FINDINGS 全文**就能知道从哪开始。*
*如果做不到这一点，说明遗留问题记录得不够具体。*
