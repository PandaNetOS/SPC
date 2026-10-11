# round15 执行日志 —— 轮次号与待办状态双源治理轮

**2026-10-12** 开轮：`render_task_brief --round 15`，任务书输出 **0 个可执行任务**
（待办池仅剩 T-025 `external-data` / T-032 `unverifiable`，T-052 已落地却漏勾）。

## 开轮侦察发现的四个同源缺陷

侦察阶段两次 dry-run 意外造出空的 `round15/`、`round16/` 目录 ——
这不是手误，是工具的真实行为，顺着它挖出整条链：

1. `render_task_brief.py` 的 `makedirs` 早于 `--write` → dry-run 也建目录（T-057）
2. `_next_round` / `current_iteration_round` 按目录名取 max → 空目录推高轮号（T-058）
3. 权威源（versions.json `r14`）与目录源（`round16`）互不看 → 静默分叉（T-059）
4. T-052 已落地但 TODO 未勾 → 任务书会重复推出已完成任务（T-060）

修完第 4 条后可执行候选归零，又暴露第 5 条：`_render_brief` 的降级路径
`items[:top_n]` 会把资源缺口型提升为必做，违背 Z 协议（T-061）。

## 教训

- **状态不得由自身派生物推断**。工具自己建的目录，不能反过来当「已存在几轮」的依据。
- **护栏要窄而准**。★T 只扫 `strategy_landed`，不扫 `actual_updates`
  （后者含「T-025 external-data 前置降备选」这类提及，泛化会误报）。
- **修一个 bug 常常是下一个 bug 的触发器**。候选归零才让隐藏的降级路径首次执行。

## 与 r14.2 的连续性

r11.1（清单驱动护栏）→ r14.2（同源双向比对）→ r15（派生自指）。
三次形态不同，病灶相同：**检查的是两个都从同一处派生的值**。

## 收尾数字

- validate：104 → **106 项**，错误 0（新增 ★R / ★T 两条 OK）
- 测试：456 → **464**（`test_round_counter_sync.py` 11 项全过）
- 连带修好 `test_ai_readability` 2 项（夹具改为真收尾轮）、还原 `test_flywheel` 1 项
- 轮号：round16 → **round14**；重校准警告 7 轮 → **真实的 5 轮**

## 未裁定

T-020：`[x]` 但无产出记录、Q-006 仍 open、round08 内 HANDOFF 与 manifest 互相矛盾。
本轮只标注，等用户裁定「回退为未勾选」还是「补 F-xxxx 入库」。
