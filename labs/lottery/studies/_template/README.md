# games/_template —— 新彩种骨架

这是**新彩种模板**。不要直接在这里做分析 —— 用 CLI 复制一份：

```bash
python cli/main.py new-game <game_id>
```

之后：

1. 编辑 `games/<game_id>/game.yaml`（`machine` / `features` / `prize_model` / `data`）
2. 放数据到 `games/<game_id>/data/raw/` 并算 SHA256，写入 `game.yaml` 的 `data.raw`
3. 建 `games/<game_id>/iterations/round01/TASK_BRIEF.md`（用 `platform/protocol/templates/TASK_BRIEF.template.md`）
4. 跑 `python cli/main.py validate --game <game_id>`

## ⚠️ 唯一的硬标准

**加入这个彩种时，是否需要改 `platform/` 或 `src/` 的任何一行？**

- 不需要 → 框架分离是成功的，继续。
- 需要 → **停下来**。不是"绕过"，而是框架缺了一处抽象。记进 `labs/lottery/studies/dlt/memory/lessons/LESSONS.md`，
  并在下一轮 `framework_revision` 里提出。

## 目录约定

```
games/<id>/
├── game.yaml              # 彩种声明（受 spec/game_config.schema.json 约束）
├── data/
│   ├── raw/               # 原始开奖数据（只读，附 SHA256）
│   ├── derived/           # 派生数据集（可由 build_scripts/ 重建）
│   ├── tools/             # 该彩种专用的分析脚本
│   └── build_scripts/     # 从 raw 重建 derived
├── iterations/
│   └── round01/           # 每轮一个目录
│       ├── TASK_BRIEF.md      # 开轮写（反锚定）
│       ├── FINDINGS.md        # 做分析时写
│       ├── HANDOFF.md         # 收轮写
│       └── manifest.json      # 收轮写（受 spec/iteration.schema.json 约束）
└── strategy/
    └── strategy.json      # 对外输出（受 spec/strategy.schema.json 约束）
```

## 不要做的事

- ❌ 不要往 `game.yaml` 里塞"分析结论" —— 结论进 `labs/lottery/studies/dlt/memory/facts/FACTS.jsonl`
- ❌ 不要在 `platform/` 里写彩种专属分支（`if game == "xxx"`）
- ❌ 不要手写 `strategy.json` 的 `boundary` —— 用 `python cli/main.py strategy --game <id>` 重算
- ❌ 不要跳过 `iterations/roundNN/TASK_BRIEF.md` 直接产出结论 —— 违反反锚定协议
