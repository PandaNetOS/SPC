# round13 日志（L3 规则搜索 v2 轮）

- **2026-10-11** 开轮：`render_task_brief --round 13 --top 3`（T-051 90 分首推 / T-044 / T-045）。
  - 坑①：TODO 里 T-051 曾命名为 `T-049b`（字母后缀），任务书生成器正则只认 `T-\d{3}` → 改名 T-051 后重新生成。
- **研究**：写 `scripts/t051_walkforward.py`（复用 t049_holdout 组合空间/规则谓词/含封顶奖金口径）。
  - 坑②：60 期评估窗下 R_new 命中不足 20 期 → cf 全部 None → 评估窗放大 150 期、判定门槛改"有效步 ≥4"。
- **结果**：5 步中 R_new 正增益 4/5（80%），中位增益约 +150 万元、累计约 +604 万元，met=True（F-0045）。
- **T-044**：build_versions.py `--write` 禁用 + 文件头降级声明（防 versions.json 回退）。
- **T-045**：count_tests --inject 核实已落地，销账。
- **入库**：FACTS 44→45（F-0045）；TODO T-051/T-044/T-045 → done，新增 T-052（R_new 落地待批准）。
- **收尾**：四件套 + versions.json 登记（r13）+ render 五件套 + inject + validate + count_tests + 合规 + commit + push。
