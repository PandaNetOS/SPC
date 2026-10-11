# FINDINGS —— round15（轮次号与待办状态双源治理轮）

> **版本**：`1.0` ｜ 轮次 `r15` ｜ 更新 2026-10-12 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **性质**：治理轮（governance round），非研究轮。**不新增 F-xxxx**，不触碰策略变更红线。
> 本轮任务书输出 **0 个可执行任务**（待办池已被收尾轮消耗殆尽，见 §1），
> 实际工作来自开轮侦察中发现的 4 个**同源**缺陷 —— 它们与 r14.2 的
> README 版本行滞后属同一病族：**每一处单独看都自洽，合起来让飞轮跑在错误的轮号上**。

---

## 1. 开轮侦察：待办池已枯竭

`render_task_brief --score` 全库仅剩 3 个 `- [ ]`：

| 任务 | 状态 | 资源约束 |
|---|---|---|
| T-052 | **已落地**（r14.1，R-004 在 strategy.json）但漏勾 | 无 |
| T-025 | 待外部数据（三至七等奖实发额） | `external-data` |
| T-032 | 摇奖设备数据不可得 | `unverifiable` |

即：**自动化任务书下一步只会推出一个早已完成的任务**。
待办池是 `render_task_brief` 的唯一输入源，它失真 = 飞轮输入失真。

---

## 2. 四个缺陷与根治

### D1 · dry-run 有副作用（T-057）

`tools/render_task_brief.py` 的 `os.makedirs` 写在 `--write` 判断**之前**：

```python
out = os.path.join(..., f"round{rnd:02d}", "TASK_BRIEF.md")
os.makedirs(os.path.dirname(out), exist_ok=True)   # ← 无条件
if "--write" in sys.argv:
    open(out, "w", ...).write(brief)
```

只跑预览也会建出 `roundNN/` 空目录。实测两次 dry-run → 凭空出现 `round15/`、`round16/`。
**根治**：`makedirs` 移入 `--write` 分支。

### D2 · 轮次号由「目录存在」推断（T-058）

`_next_round`（render_task_brief）与 `current_iteration_round`（validate:279）
都按 `roundNN` 目录名取 max。与 D1 叠加成**自激回路**：

```
dry-run 建空目录 → 目录 max +1 → 下一轮号 +1 → validate 报「当前 round16」
```

而 versions.json 的权威 `current_iteration` 仍是 `r14`。后果可见：
F-0016/F-0017/F-0022/F-0023 的重校准警告由真实的 **5 轮**虚增为 **7 轮**。

**根治**：新增 `delivered_round_dirs()`，判据改为**含 `manifest.json`**（收尾轮判据）。

### D3 · 轮次号两个真源互不看（T-059）

r14.2 刚把 versions.json 立为权威源，但目录扫描那一路**无人校验**，
两边各自自洽、静默分叉 —— 这正是「同源双向比对盲区」的又一次变形。

**根治**：新增校验项 ★R `_check_iteration_counter_sync`：
`current_iteration` 必须等于最新已收尾轮，否则报错。
不删任何一边，而是把两边**绑成可校验关系**（权威源 = versions.json，目录扫描降级为被校验方）。

### D4 · 待办状态滞后（T-060）

T-052 在 r14.1 经用户批准后已实际落地，TODO 仍是 `- [ ]`。

**根治**：新增校验项 ★T `_check_todo_landed_sync`：已 delivered 轮 manifest 的
`outputs.strategy_landed` 中出现的 T-nnn，在 TODO 不得仍是 `- [ ]`。

**只扫 `strategy_landed`，不扫 `actual_updates`**：后者既有完成记录，
也有 `round08` 里「T-025 external-data 前置降备选」这类**提及**，
泛化扫描会误报（实测会误伤 T-025/T-032/T-099）。护栏宁可窄而准，不要宽而噪。

### D5 · 附带发现：降级路径违背 Z 协议（T-061）

修 D4 后可执行候选归零，暴露 `_render_brief` 的隐藏降级：

```python
top = executable[:top_n] if executable else items[:top_n]   # ← 旧
```

`items[:top_n]` 会把 `external-data` / `unverifiable` 任务**提升为必做**，
正面违背 Z 协议（资源缺口型不占轮次预算）。该路径此前从未被走到
（待办池恒有可执行项），T-052 勾选后才首次触发。
**根治**：无可执行候选时如实输出 0 个，并给出处置建议。

---

## 3. 与 r14.2 的关系

| 轮次 | 症状 | 病灶 |
|---|---|---|
| r11.1 | 策略文档漏更新 | 护栏由**清单**驱动（硬编码 2 个路径） |
| r14.2 | README 头部版本行滞后 | 只做同源双向比对，抓不住 A、B 一起过时 |
| **r15** | 轮号虚增 / 待办滞后 | 状态由**自身派生物**推断（目录由自己创建） |

三次的共同点：**护栏检查的是「两个都从同一处派生的值」**。
r15 的解法与前两次一致 —— 把派生方与被派生方绑成可校验关系，而非删掉一边。

---

## 4. 不做的事

- **不新增 F-xxxx**：本轮无新经验结论，只有机制修复。
- **不碰策略红线**：`strategy.json` / `STRATEGY_GUIDE` 本轮零改动。
- **不改 T-020 勾选状态**：见 §5。
