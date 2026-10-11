# AGENTS.md —— SPC 操作规则（给 AI 的极简入口）

> **版本**：`1.0` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

SPC：彩票投注策略研究框架（自我迭代），研究结论输出为机器可读策略规则。
**深度入口先读 `AI_CONTEXT.md`**（约 10 分钟）；机器地图 `AI_MAP.md`；
给人看的总览 `README.md`；版本索引 `VERSION_INDEX.md`（机器镜像 `versions.json`）。

## 常用命令（在仓库根 `D:\PNOS\SPC` 运行）

```bash
python cli/main.py validate --all        # 全量校验（69+ 项，提交前必过）
python cli/main.py versions              # 版本一致性（文件版本行 ↔ versions.json ↔ VERSION_INDEX）
python cli/main.py index                 # 从 FACTS.jsonl 重生成 INDEX.md
python cli/main.py rehash --strategy     # 策略证据摘要重算（证据变更后）
python cli/main.py pick --game dlt -n 10 --seed 20261011   # 生成号码
python tools/count_tests.py              # 全量测试计数（自举，无需 pytest）
python tools/render_readme_tree.py --write   # 目录树写回（派生物）
python tools/render_ai_map.py --write        # AI_MAP 写回（派生物）
python tools/render_version_index.py --write # VERSION_INDEX 重渲染
```

## 测试

- 无需 pytest：`python tests/test_core.py` 等直接跑（退出码 0 = 全绿）
- 权威计数：`python tools/count_tests.py`（333+ 项）
- 新测试文件必须登记 `tools/count_tests.py` 的 TEST_FILES

## 目录结构与入口

| 路径 | 是什么 |
|---|---|
| `AI_CONTEXT.md` | ★ 单一深度入口（先读） |
| `AI_MAP.md` | 机器地图（派生物，勿手改） |
| `AGENTS.md` | 本文件（操作规则） |
| `spec/` | 契约层（JSON Schema + 版本规范） |
| `framework/` | 框架层（协议/方法论/工具/核心，彩种无关） |
| `memory/` | 记忆层（FACTS 台账 + lessons + journal + workbench） |
| `games/dlt/` | 彩种层（game.yaml + strategy.json + iterations） |
| `src/spc/` | 库代码（validate/versions/evidence/tree/ai_map/flywheel/depmap） |
| `cli/` `tools/` | 命令行入口与仓库维护脚本 |
| `tests/` | 测试（无需 pytest） |

## 边界（红线，违反即校验失败）

1. 任何结论不得声称改变中奖概率（`affects_win_probability` 恒 false）
2. 对外输出必须声明不提高中奖概率（`changes_win_probability` 恒 false）
3. 唯一可优化量是 `expected_bonus_given_win`（中奖时期望奖金）
4. 不预测号码、不推荐具体号码；长期期望恒为负（理性购彩）

## 版本纪律

- 改了文件内容 → 升该文件 `content_version` + 登记 versions.json + 重渲染
- 新增文件 → 必须登记 versions.json（validate 结构完整性强制）
- README 目录树 / AI_MAP / FLYWHEEL_HEALTH / DEPENDENCY_MAP 均为**派生物**，勿手改
- 引用任何内容前先确认版本（读 VERSION_INDEX.md §0）

## git 流程（用户红线）

- 仅 `main` 单分支，不建分支
- 提交/推送前：合规脚本 `D:\PNOS\check-compliance.ps1 -ProjectPath D:\PNOS\SPC` 全 PASS
- 提交/推送前**必须用户确认**；不 force push、不 reset --hard
- 涉及代码/配置/部署方案修改，先确认方案再动手
- 远程推送用直连：`git -c http.proxy= -c https.proxy= -c http.sslBackend=openssl push origin main`
