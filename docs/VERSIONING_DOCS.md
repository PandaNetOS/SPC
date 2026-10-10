# VERSIONING_DOCS.md — 文档与内容版本规则

> **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

> **本文件与 `spec/VERSIONING.md` 的关系：**
>
> | 文件 | 管什么 | 版本号 |
> |---|---|---|
> | `spec/VERSIONING.md` | **机器契约**（JSON 数据的结构） | `schema_version` / `config_version` |
> | **本文件** | **文档与内容**（`.md` / 人读内容） | `content_version` / `framework_version` |
>
> 两者**互补，不重叠**。前者答"程序能不能解析"，后者答"人读到的是第几版"。

---

## 0. 为什么需要它

本仓库的核心价值是**结论的可追溯性**。但此前有一个盲区：

> 打开 `LESSONS.md`，看不出 L1–L9 是哪一轮加的、之后改过几次。
> 打开 `OPEN_QUESTIONS.md`，看不出 Q-001 是哪轮提的。
> 引用某个数字时，**无法确认引用的是不是当前版本**。

**版本号就是给「引用」定锚点。**
一份内容若无法被引用者确认"我读的是哪一版"，它就已经在无人察觉的情况下开始漂移。

---

## 1. 五个版本号的分工

| 版本号 | 答什么问题 | 谁拥有 | 字段名 | 范围 |
|---|---|---|---|---|
| `schema_version` | 契约**结构**长什么样 | `spec/` | `strategy.json.schema_version` | 对外契约 |
| `config_version` | 彩种**参数**是什么版本 | `games/<id>/` | `game.yaml.config_version` | 彩种配置 |
| `data_version` | 用了**哪份数据** | `data/raw/` | `game.yaml` / `manifest.inputs` | 数据 |
| **`content_version`** ★ | **这份内容改过几版** | **每份内容自己** | 文件内版本行 | 文档 / 结论 / 教训 |
| **`framework_version`** ★ | **框架层改过几版** | `framework/` | `versions.json` | 研究框架 |

★ = 2026-10-11 新引入。

**它们不冲突**。实例：

```jsonc
// strategy.json
{
  "schema_version": "1.0",     // 契约结构：没动
  "config_version": "2.0",     // 彩种参数：features 原语化过了
  // content_version: "1.1"    // 内容：规则幅度改了 → 在 VERSION_INDEX.md 里
}
```

契约结构没动（`schema_version` 不变），但规则幅度改了（`content_version` 升）。
**三个号各说各的事，缺一个就有一类变更被隐藏。**

---

## 2. 版本号格式

```
<主>.<次>        例：1.0  /  1.1  /  2.0
```

| 段 | 何时 +1 | 例子 |
|---|---|---|
| **主** | 结构变更 / 立场变更 / 破坏性变更 | `LESSONS.md` 从"9 条禁令"改成"禁令 + 检查清单两段式" |
| **次** | 内容增补 / 结论新增 / 幅度修正 | `FACTS.jsonl` 新增一条结论 |

**轮次不编码进版本号**，记在独立的 `iteration` 字段（`r01`/`r02`/…）。

> **为什么**：同一版本可能跨多轮才定稿。若编码成 `1.0.r02` → `1.0.r03`，
> 会让人误以为内容升级了，实际只是**归属轮次变了**。这是假升级。

---

## 3. 四级分区

**不是所有文件都需要版本号。** 分级依据是「这份内容重复写错的代价有多高」。

| 级别 | 名称 | 版本化 | 写入方式 | 判据 |
|---|---|---|---|---|
| **A** | 结论性内容 | ✅ | 文件内版本行 + 索引 | 会随轮次演化，**重复写错代价最高** |
| **B** | 结构性文档 / 框架与库代码 | ✅ | `.md` 加版本行；`.py` 只登记索引 | 随框架演进，但无"结论"性质 |
| **C** | 机器契约 | ❌ | 索引**镜像**其既有版本字段 | 已有 `schema_version`/`config_version`/`data_version`，再加一层是冗余 |
| **D** | 纯数据 / 分析脚本 | ❌ | 索引只登记 SHA256 | `data/raw` 的 SHA256 是**比版本号更强的保证** |

### 3.1 为什么 D 级（数据）不版本化

版本号只能告诉你"变了"，**SHA256 能告诉你"具体哪里变了"**。
给数据加版本号是双重记账，且弱于已有机制。

### 3.2 为什么 B 级的 `.py` 不写文件内版本行

代码的版本信息由 `git blame` 提供，且远比手写版本行精确。
在代码里加注释版本行是纯噪音 —— 还会引入"代码改了忘改版本行"的新漂移源。

### 3.3 为什么 C 级不重复加版本

`spec/*.schema.json` **自己不声明版本**（它只约束别人的 `schema_version`）。
若给它再加一个 `content_version`，会出现两个"版本"指同一件事。
索引**镜像**它约束的字段值即可。

---

## 4. 文件内版本行

### 4.1 格式（固定，不得变体）

```markdown
# 文件名 — 标题

> **版本**：`1.0` ｜ 轮次 `r02` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
> 版本规则见 `docs/VERSIONING_DOCS.md`

（正文开始）
```

**位置**：**紧跟 H1 标题之后**，空一行。

**为什么固定位置**：让 AI 与工具可以用同一个正则提取，无需理解文档结构。

### 4.2 幂等更新

`python tools/inject_version_lines.py --write` 会：
- 已存在版本行 → **原地更新**（不重复插入）
- 不存在 → 在 H1 后插入

所以可以反复跑，不会产生多行。

### 4.3 不改版本行的文件

| 文件 | 原因 |
|---|---|
| `VERSION_INDEX.md` | 自身就是索引，头部已有全局版本信息 |
| `memory/facts/INDEX.md` | 由 `cli index` 生成，版本在生成器里加 |
| 所有 `.py` | 见 §3.2 |
| `spec/*.schema.json` | 见 §3.3 |

---

## 5. 索引机制

**权威源唯一**：`versions.json`（受 `spec/version_index.schema.json` 约束）。

```
versions.json  ──生成──>  VERSION_INDEX.md   （人读，claude 用）
     │
     └──校验──>  cli/main.py versions
                    └── 比对：文件内版本行 ↔ versions.json ↔ VERSION_INDEX.md
```

| 文件 | 性质 | 能否手改 |
|---|---|---|
| `versions.json` | **权威源** | ✅ 可改（但改完要跑校验） |
| `VERSION_INDEX.md` | **派生物** | ❌ 禁止（会被下次生成覆盖） |
| 各文件的版本行 | **从属** | ✅ 可改（用 `inject_version_lines.py` 或手工，格式须一致） |

**为什么权威源是 JSON 而非 Markdown**：AI 与工具可以直接 `json.load`，
无需解析 markdown 表格。`VERSION_INDEX.md` 是为了**人能快速扫**。

---

## 6. 操作手册

### 6.1 改内容时（谁改谁升）

| 你做了什么 | 版本怎么动 | 还要做 |
|---|---|---|
| 新增一条结论 | `FACTS.jsonl` 次版本 +1 | 跑 `cli index` |
| 新增一条教训 | `LESSONS.md` 次版本 +1 | — |
| 改了策略规则幅度 | `strategy.json` 的 `content_version` 次版本 +1 | `schema_version` **不动** |
| 改了 `game.yaml` 玩法/特征 | `config_version` 次版本 +1 | 跑 `validate --game` |
| 改了框架协议 / 方法论 / core | `framework_version` 视情况 +1 | 结构变更升**主**版本 |
| 新增一轮迭代 | 新目录，各文件 `content_version` 从 `1.0` 起 | `iteration` 记新轮次 |
| 改了某份文档的表述 | 该文档次版本 +1 | **禁止静默改** |

### 6.2 一轮迭代结束时的固定动作

```bash
# 1. 更新 versions.json（改 CONTENT_VERSIONS 或直接编辑 JSON）
# 2. 重新生成索引
python tools/render_version_index.py --write
# 3. 版本一致性检查
python cli/main.py versions
# 4. 全量校验（含版本检查）
python cli/main.py validate --all -v
```

### 6.3 禁止事项

| 禁止 | 后果 |
|---|---|
| 手改 `VERSION_INDEX.md` | 会被下次生成覆盖 |
| 手改 `versions.json` 而不改对应文件 | `cli versions` 报不一致 |
| **改内容但不升版本** | **索引记录的是错的 —— 比没有索引更坏** |
| 把轮次编码进版本号 | 假升级（见 §2） |
| 给 D 级数据加版本号 | 与 SHA256 双重记账 |
| 版本行写成其他格式 | 正则提取失败，一致性检查失效 |

---

## 7. 与迭代协议的关系

`framework/protocol/ITERATION_PROTOCOL.md` §4「收轮」现已包含**升版本**步骤：

```
收轮时（在写完 HANDOFF.md 之后）：
  ...
  + 升版本 → 更新 versions.json → render_version_index.py --write
  + 跑 cli/main.py versions
```

**这是"可追溯性"链条上新增的一环**：
此前只能追溯"结论 → 脚本 → 数据"，
现在还能追溯"**结论 → 它的版本 → 何时被改过**"。

---

## 8. 最后一条

> **版本号不是给文件贴标签，是给「引用」定锚点。**
>
> 一份内容若无法被引用者确认"我读的是哪一版"，
> 它就已经在无人察觉的情况下开始漂移 —— 这正是本文件要防的事。
