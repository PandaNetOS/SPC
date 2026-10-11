# VERSIONING_DOCS.md — 文档与内容版本规则

> **版本**：`1.4` ｜ 轮次 `r14` ｜ 更新 2026-10-11 ｜ 权威源 `VERSION_INDEX.md`
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

### 2.1 版本号**不写进文件名**

文件名一律 `<名字>.md`，版本号只出现在两处：**文件头部的版本行** + **索引/目录页**。

> **为什么不做成 `STRATEGY_GUIDE_v1.0.md`**：
>
> | 代价 | 说明 |
> |---|---|
> | 链接全废 | 39 份文档互相引用、`VERSION_INDEX.md`、各 `INDEX.md` 全指向旧名 → 每次升版本都要全仓改链接 |
> | 历史断裂 | 改名后 `git log` 需 `--follow` 才勉强追踪，`git blame` 视觉上断成两截 |
> | 多版本并存歧义 | 会出现 `_v1.0` 与 `_v1.1` 两个文件同时在库里，**AI 该读哪个？** 反而制造新的不确定 |
>
> **替代方案（本仓库采用）**：在**索引页**标注版本 —— GitHub 上一眼可见，且不会失效。
>
> | 位置 | 形式 |
> |---|---|
> | 文件头部 | `> **版本**：\`1.0\` ｜ 轮次 \`r03\` ｜ 更新 … ｜ 权威源 \`VERSION_INDEX.md\`` |
> | `VERSION_INDEX.md` | 全量表格，每行带 `content_version` / `iteration` |
> | `README.md` 目录树 | 文件名后标 `v1.0` |
>
> README 的标注由 `cli/main.py versions` **自动校验**（写错或过期会报 error）。

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
# 1. 活文档轮次对齐（r14.2 新增；必须在渲染之前，见 §6.6）
python tools/bump_iteration.py --write --to rNN
# 2. 更新 versions.json（改 CONTENT_VERSIONS 或直接编辑 JSON）
# 3. 重新生成索引
python tools/render_version_index.py --write
# 4. 版本一致性检查
python cli/main.py versions
# 5. 全量校验（含版本检查）
python cli/main.py validate --all -v
```

> 实际收尾直接跑 `python tools/finish_round.py`，它已按
> `bump → render_* → inject → validate` 的正确顺序编排。

### 6.3 下游新鲜度：`consumes` 声明（r03 新增）

**版本号自洽 ≠ 内容跟得上结论。**

这是一个**真实踩过的坑**（r03）：`F-0015`（「1 亿封顶已触发」）被推翻后，
给普通用户看的 `STRATEGY_GUIDE.md` 仍在传播这个错误结论 ——
而当时**全部 106 项测试 + 41 项校验都是绿的**，因为旧校验只比对
「索引版本号 vs 文件内版本号」，两边都是 `1.0`，判定"一致"。

**机制**：让下游文档声明它**引用了哪些结论**。

```python
# tools/build_versions.py
CONSUMES: dict[str, list[str]] = {
    "games/dlt/strategy/STRATEGY_GUIDE.md": ["F-0001", "F-0003", ...],
    "games/dlt/strategy/strategy.json":     ["F-0001", "F-0003", ...],
}
```

构建时写入 `versions.json` 条目的 `consumes` 字段；校验器检查：

> 若某条目引用的 `F-xxxx` 在 `FACTS.jsonl` 里已 `status: superseded`
> → 报 **warning（下游沉默）**，提示确认内容已同步。

**为什么是 warning 而非 error**：引用 superseded 结论**未必是错的** ——
可能是「历史沿革」式正当引用（如"早期文档曾误判为已触发，现已更正"）。
但**必须让人看见**，不能沉默。

**维护纪律**：
1. 文档引用某条结论时，把编号填进 `CONSUMES`；引用关系消失时删掉
2. 若只是「提及历史」而非「依赖」，**不要列入** —— 否则永久告警（噪音）
3. 被 warning 命中时，二选一：① 同步内容并升 `content_version`；② 确认属沿革式引用，在文档内加显式存疑标记

### 6.4 速览表计数一致性（r03 新增）

**第二类下游漏洞**：`consumes` 管得住「引用某条结论」，却管不住
「表格里写的结论**总数**」。

真实案例：`games/INDEX.md` 写「结论数 15」、`AI_CONTEXT.md` 写
「FACTS.jsonl（15 条）」，而台账已 18 条 —— **两种情况下校验依然全绿**。

**机制**：校验器扫描指定的速览类文件，凡出现「N 条结论」字样，
`N` 必须等于台账实际条数（接受「全部条数」与「非 superseded 条数」两个口径）。

```python
_COUNT_LABEL_FILES = ("games/INDEX.md", "AI_CONTEXT.md", "README.md", "memory/INDEX.md")
# 命中： "18 条结论" / "FACTS.jsonl（18 条）"
```

**为什么用 error 而非 warning**：计数是**客观可验证**的量 ——
要么对要么错，不存在「历史沿革式正当引用」的辩解空间。

**维护纪律**：新增/推翻结论后，除了改 `FACTS.jsonl`，还要**全局搜一遍**
`条结论` 确认速览表同步（现在校验器会替你搜）。

### 6.5 禁止事项

| 禁止 | 后果 |
|---|---|
| 手改 `VERSION_INDEX.md` | 会被下次生成覆盖 |
| 手改 `versions.json` 而不改对应文件 | `cli versions` 报不一致 |
| **改内容但不升版本** | **索引记录的是错的 —— 比没有索引更坏** |
| **引用了结论却不写 `consumes`** | 上游结论被推翻时下游沉默，无人察觉（见 §6.3） |
| **速览表里的结论数不随台账更新** | 读者拿到过期计数（见 §6.4） |
| **先 render/inject、再改 versions.json 的轮次** | 旧轮次被刷进文件头并自洽化，校验全绿但头部仍过期（见 §6.6） |
| 把轮次编码进版本号 | 假升级（见 §2） |
| 给 D 级数据加版本号 | 与 SHA256 双重记账 |
| 版本行写成其他格式 | 正则提取失败，一致性检查失效 |

### 6.6 轮次停滞：`follows_current` 声明（r14.2 新增）

**版本号自洽 ≠ 轮次跟得上。** —— 与 §6.3 同族的**第二个**真实事故。

r14 实测：`README.md` 头部写 `轮次 r12`，而权威 `current_iteration = r14`，
**validate 104 项全绿**。原因不是检查写错，是**检查缺了一类判据**：

```
校验器只做「文件内版本行 ↔ versions.json 条目」的同源双向比对，
current_iteration 只作为 stats 打印、从不参与判定。
  条目停在 r12
    → inject_version_lines 照抄 r12 写进文件头
      → 两边一致 → 全绿
抓得住 A≠B，抓不住 A、B 一起过时。
```

**机制**：活文档在 `versions.json` 显式声明 `follows_current: true`，
校验器即要求其 `iteration` **必须等于** `current_iteration`，否则**报错**（不是 warning —— warning 可被忽略）。

| 该标 `true` | 不该标 |
|---|---|
| 入口 / 速览 / 索引 / 策略 / 事实库等**每轮必更或必复核**者：`README.md`、`AI_CONTEXT.md`、`AI_MAP.md`、`DEPENDENCY_MAP.md`、`FLYWHEEL_HEALTH.md`、`VERSION_INDEX.md`、`versions.json`、`OPEN_QUESTIONS.md`、`TODO.md`、`FACTS.jsonl`、`STRATEGY_GUIDE.md`、`strategy.json` | 轮次产物（`roundNN/*`）与 `memory/journal/` —— 它们的轮次**天生属于产出那一轮**，强制对齐会抹掉真实信息；长期稳定的文档 —— 标了会每轮被迫假升级 |

**为什么不做「落后 N 轮就告警」的泛化规则**：实测一次刷出 26 条（限 `.md` 时）
／69 条（含代码）**无操作价值**的告警，会淹没真正的错误信号
（本仓库常态仅十余条警告）。防停滞**只认显式声明**。

**修复端**：

```bash
python tools/bump_iteration.py --write            # 对齐到当前轮
python tools/bump_iteration.py --write --to r15   # 收尾时同时推进 current_iteration
```

⚠️ **顺序不可颠倒**：`bump_iteration → render_* → inject_version_lines → validate`。
颠倒会先把旧轮次刷进文件头、再改索引，旧值被自洽化后照样全绿 —— 正是本次事故的形态。
`tools/finish_round.py` 已按此顺序编排。

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
