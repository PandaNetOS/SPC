# games/ —— 彩种索引

> **版本**：`1.2` ｜ 轮次 `r04` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 已接入彩种

| id | 名称 | 号码空间 T | 一等奖概率 | 返奖率 | 结论数 | 轮次 | 策略 |
|---|---|---|---|---|---|---|---|
| `dlt` | 超级大乐透 | 21,425,712 | 4.667289469773513e-08 | 51% | 32 | round05 ✅ | `dlt/strategy/strategy.json` |

> 上表是**手工维护的速览**。权威数据源：
> - 结论数 → `python cli/main.py info`
> - 号码空间 → `python cli/main.py games`
> - 策略文件 → `games/<id>/strategy/strategy.json`

## 待接入彩种

暂无。接入方法见下。

## 接入一个新彩种

```bash
python cli/main.py new-game <game_id>
```

然后按 `labs/lottery/studies/_template/README.md` 的 4 步走。

**唯一硬标准**：加入这个彩种时，是否需要改 `platform/` 或 `src/` 的任何一行？

- 不需要 → ✅ 框架分离成立
- 需要 → ⚠️ **停下**。这是框架缺了抽象，不是彩种的锅。补进框架，并记入
  `memory/lessons/LESSONS.md`。

## 各彩种目录速览

```
games/
├── _template/            # 新彩种骨架（CLI new-game 的来源）
└── dlt/                  # 超级大乐透
    ├── game.yaml         #   彩种声明（受 spec/game_config.schema.json 约束）
    ├── data/             #   数据层
    │   ├── raw/          #     原始开奖（只读 + SHA256）
    │   ├── derived/      #     派生数据集（可由 build_scripts 重建）
    │   ├── tools/        #     分析脚本
    │   └── build_scripts/#     重建脚本 + 包校验
    ├── iterations/       #   轮次
    │   ├── round02/      #     已完成：FINDINGS / HANDOFF / manifest / legacy_findings
    │   ├── round03/      #     已完成：复核轮（FINDINGS / HANDOFF / manifest）
    │   ├── round04/      #     已完成：归因轮（FINDINGS / HANDOFF / manifest + 5 脚本 + 3 JSON）
    │   ├── round05/      #     已完成：投注方式 + 时间因素（FINDINGS / HANDOFF / manifest + 3 脚本 + 2 JSON）
│   └── round06/      #     计划中：TASK_BRIEF（前段数据取证，r06 首推）
    ├── strategy/         #   对外输出
    │   ├── strategy.json #     唯一稳定契约
    │   └── strategy_simulation.py + simulation_results.json
    ├── rules_history.md  #   规则变更史（6 次调整 + 现行规则）
    └── manifest_v4_source.json   # v4 分析包原始 manifest（溯源用）
```

## 彩种之间共享什么

| 共享 | 不共享 |
|---|---|
| `spec/` 五份契约 | `game.yaml` 的 `machine` / `features` / `prize_model` |
| `platform/` 协议、方法论、工具 | `data/` 全部内容 |
| `memory/` 的全局结论（`game: "global"`） | 该彩种专属结论（`game: "<id>"`） |
| `src/` + `cli/` 全部代码 | `iterations/` 与 `strategy/` |

`memory/facts/FACTS.jsonl` 里的 `game` 字段区分归属：

- `"global"` —— 跨彩种成立的结论（如 F-0001 概率不可变）
- `"dlt"` —— 仅对该彩种成立的结论（如 F-0003 连号人群更密）

引用外彩种结论时**必须确认 `game` 字段**，不要拿别的彩种的观测当自己的证据。
