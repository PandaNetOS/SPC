# SOP_OVERVIEW.md — SPC 标准操作流程总览

> **版本**：1.0 ｜ 更新 2026-10-12 ｜ 适用范围：整个 SPC 项目

---

## 一、研究迭代 SOP（核心生命周期）

**一轮 = 一个 `games/<game>/iterations/roundNN/` 目录的完整生命周期。**

| 阶段 | 动作 | 产出 | 给谁看 |
|---|---|---|---|
| **开轮** | 写任务书：要做什么、验收判据、陷阱提醒 | `TASK_BRIEF.md` | 本轮执行者 |
| **执行** | 跑分析、写脚本、记录数字 | `scripts/*.py` + 结果 JSON | 本轮执行者 |
| **记录** | 每条结论带证据、数字、CI | `FINDINGS.md` | 评审/复核者 |
| **交接** | 遗留什么、下轮从哪开始、风险提示 | `HANDOFF.md` | 下一轮执行者 |
| **收尾** | 结构化索引（受 schema 约束） | `manifest.json` | 机器/validate |
| **版本** | `current_iteration` → rNN+1 | `versions.json` | 全局 |

**四件套强制**：TASK_BRIEF / FINDINGS / HANDOFF / manifest，缺一不可（validate 自动检查）。

---

## 二、证据入库 SOP（三闸门）

新结论进 `FACTS.jsonl` 前必须逐闸过检：

| 闸门 | 检查内容 | 失败处理 |
|---|---|---|
| **G1 schema** | 格式合规（claim / confidence / source_sha256 / claim_type） | 拒绝入库 |
| **G2 矛盾检测** | 与已有结论是否冲突 | 冲突 → 降 tentative 或拒绝 |
| **G3 锚定** | source 文件 SHA256 锚定，内容漂移可检出 | 漂移 → 报警 |

**原子操作（禁止整段重写）**：
- **Add**：新增 F-XXXX（编号永不复用）
- **Modify**：修订 active F 的字段
- **Supersede**：旧 F 标 superseded + superseded_by，新 F 立
- **Merge**：多条同主题 F 合成一条，被并入条标 superseded

**禁止**：删除 F 条目；重用 F 编号；跳过 supersedes/superseded_by 双向声明。

---

## 三、记忆分层 SOP（L0 / L1 / L2）

| 层 | 内容 | 生命周期 | 引用规则 |
|---|---|---|---|
| **L0 锚点** | 数据文件哈希、后段切点（F-0006）、统一种子、规则 epoch | 不可变（变更即新版本） | 任何人不得修改 |
| **L1 观测结论** | `FACTS.jsonl`（claim + claim_type + confidence + source_sha256） | 可 superseded / refuted（保留台账） | L2 只能引用 active 的 L1 |
| **L2 策略规则** | `strategy.json`（R-xxx + avoid_list） | 需用户批准门 | 无有效 L1 支撑 → validate 报错 |

**核心纪律**：L2 不得引用 status ∈ {superseded, refuted} 的 L1（INV2）。

---

## 四、策略落地 SOP

从"发现一个效应"到"落地为机器可执行规则"的完整路径：

```
1. 宽筛发现形态/效应
   ↓
2. Bootstrap 95% CI + 分期稳健性（前后半段方向一致）
   ↓
3. 置换检验 max|r| 多重比较校正（防假阳性）
   ↓
4. 重尾稳健复核（中位数比 + 截尾均值，替代均值比）
   ↓
5. 时序 hold-out 样本外验证（时间切割，非随机切割）
   ↓
6. 用户批准（红线：未经批准不得落地）
   ↓
7. 写入 strategy.json，带 effectiveness_grade 档位
```

**有效性档位（三档标准）**：

| 档位 | 含义 | 判定要求 | 当前规则 |
|---|---|---|---|
| **A 数学恒真** | 解析可证，无模型假设 | 公式推导成立 | R-002（同号 K 注自我摊薄） |
| **B 统计确立** | 观测数据 + 样本外验证 | 后段观测显著 + 时序 hold-out 方向一致 | R-001 / R-003 / R-004 |
| **C 模型估计/探索性** | 依赖模型假设或样本有限 | 明确标注假设与置信度 | R-005（冷门形态偏好） |

---

## 五、合规检查 SOP（提交前必过）

提交 / push 前必须跑 `.\check-compliance.ps1`，26 项检查：

| 类别 | 检查项 |
|---|---|
| **代码质量** | cargo fmt / clippy / test / release 编译 |
| **架构合规** | 统一依赖 pnos / 运行时注册 / 独立进程 / 应用场景定位 |
| **编码规范** | 不硬编码参数 / 配置向后兼容 / 策略执行分离 / 原子能力暴露 |
| **工作目录** | WorkDir 统一 / ensure_dirs / 文件命名规范 |
| **安全** | 无密钥泄露 / 远程节点保护 / 无越权删除 |
| **文档** | AGENTS.md 同步 / commit message 规范 / 分支保护 |

**例外**：文档-only 变更走快速通道（跳过编译/测试，静态合规项仍全检）。

---

## 六、收轮 SOP（validate 自动校验）

收轮时 validate 自动检查以下项，全部通过才能 commit：

| 检查项 | 判据 |
|---|---|
| 四件套完整 | 有 manifest.json 必须有 FINDINGS.md / TASK_BRIEF.md / HANDOFF.md |
| HANDOFF 结构化 | 至少 4 个 ## 段，命中 3/6 关键词（结论/遗留/下轮/建议/风险） |
| deliverables 存在 | manifest 声明的文件路径实际存在 |
| 策略文档同步 | `strategy_updated=true` 的轮次，STRATEGY_GUIDE.md / strategy.json 登记轮次 ≥ 该轮 |
| 轮次号对账 | `current_iteration` == 最新已收尾轮（含 manifest.json 的 roundNN） |
| 目录轮次护栏 | 目录最大轮次 > current_iteration → ERROR（漏收轮拦截） |

**收轮辅助脚本**：`tools/finalize_round.ps1`
- 从 `git diff` 自动列出本轮改动文件
- 自动检测 `strategy_updated`（改了 strategy 文件就标 true）
- 自动生成 deliverables 草稿
- 人工补 title 后改名 manifest.json

---

## 七、版本管理 SOP

| 规则 | 说明 |
|---|---|
| 权威源 | `versions.json` + `VERSION_INDEX.md` |
| 版本号格式 | `vX.Y` = 该文件 content_version |
| 轮次格式 | `rNN`（两位数，如 r19） |
| 登记要求 | 新增文件必须登记到 versions.json entries |
| follows_current | 标记为 true 的文件必须始终跟当前轮次对齐 |

---

## 八、红线（任何 SOP 不得违反）

1. **选号不改变中奖概率**（各奖级概率恒定）—— 所有策略不得声称提高中奖率
2. **负期望游戏** —— 长期期望回报为负，策略只影响"中奖时分多少"
3. **未经用户批准不得落地策略规则**
4. **未经用户确认不得 push 远程**
5. **远程节点（192.168.30.51）数据不得删除**
6. **测试/运行数据必须在 D:\test\ 下，不得污染仓库目录**

---

> 本文件由 AI 整理，随项目演进持续更新。最后更新：2026-10-12（round19）
