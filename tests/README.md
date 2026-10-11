# tests/ — 测试

> **版本**：`1.5` ｜ 轮次 `r06` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

## 现状

| 文件 | 项数 | 覆盖 |
|---|---|---|
| `tests/test_core.py` | **117**（全绿） | 红线 / 原语 / Ticket / DSL / 作用域 / 数学 / 端到端 / 声明静态检查 |
| `tests/test_cross_scope.py` | **64**（全绿） | ★ 跨注层：跨注原语 / `Portfolio` / `evaluate_cross` / `judge_cross` / 三路切分 / 端到端 / 铁律扫描 |
| `tests/test_claim_type.py` | **43**（全绿） | ★ 证据类型：五类约束**真的会拦** / schema 与 Python 双通道一致 / 分类自洽 |
| `tests/test_evidence_anchor.py` | **32**（全绿） | ★ 证据锚定：漂移真能检出 / 该敏感的要敏感、该迟钝的要迟钝 / 重基线幂等 |
| `tests/test_shadow_game.py` | **69**（全绿） | ★ 影子彩种：第二彩种全链路跑通 + 铁律扫描（`framework/` 与 `src/` 无 dlt 痕迹）+ 扫描器自检 |
| `tests/test_structure.py` | **8**（全绿） | ★ 结构完整性（P1-2 根治）：目录树 = 派生物防手改 / 双向登记真的会拦 / 裁剪不误伤 / scripts 聚合 |
| `tests/test_flywheel.py` | **20**（全绿） | ★ r06 飞轮升级：K 健康度统计 / D1 置信度校准 / D2 矛盾检测（方向+范畴）/ C 依赖图 / F 增量校验冒烟 |
| `tests/test_ai_readability.py` | **30**（全绿） | ★ r06 AI 可读性：P1 机器地图派生物 / P2 入口完整性 / B 任务书评分 / H 交接模板 / I 压缩到期 |
| `tests/test_consumes_completeness.py` | **6**（全绿） | ★ 下游声明完整性：逆向检查（正文引用未声明即拦截）真的会拦 |
| `tests/test_meta_variables.py` | **44**（全绿） | ★ schema 1.3 元数据：convenience/experience/psychology 结构 + 红线恒值 + CLI 展示 |
| `tests/test_open_questions_consistency.py` | **12**（全绿） | ★ Q 状态一致性：解析归一化 / 头部计数滞后 / 标题缺 ✅ / 优先级表 active 含已清偿 / 状态词非法 |
| `tests/test_research_lib.py` | **18**（全绿） | ★ 研究资本化（Y）：bootstrap/比率/Wilson 原语已知分布验证 + 分期稳健性判定 + 样本不足不硬报 |
| **合计** | **463**（全绿） | 无需 pytest，直接 `python tests/test_*.py` |

**计数自举