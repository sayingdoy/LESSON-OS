---
kind: kernel
domain: learning
maturity: planned
version: 0.3.0
---

# LESSON-OS · 跨项目共享学习内核手册（PLAYBOOK）

> 版本 0.3 | 建立 2026-10-10 | Owner: Jason
> 本文件是 **bb-prep / vocab-app / AI-Kongzi（LearningOS）** 三个学习类项目的
> **单一真源（SSOT）**：沉淀"学习 + 复习 + 错题复盘"循环的共性经验与优化点，
> 让每次开发都能复用、复用滚雪球，且核心更新不误伤其他项目、交付可整包脱离代码库。

---

## 0. 为什么存在（背景与证据）

三个项目共享同一套"学习 → 间隔复习 → 考试 → 错题复盘"闭环。2026-10-10 盘点真实源码，
确认重叠是**结构性同源、非感觉**：

| 能力 | bb-prep | vocab-app | AI-Kongzi | 证据 |
|---|---|---|---|---|
| frontmatter 读写 | `bbcore.parse_front/write_front` | `review.parse_front/write_front` | frontmatter 规范 | 同一套逻辑 |
| SRS 调度 | `is_due` + `LADDER [1,2,4,7,14,28,45]` | `is_due` + `LADDER [1,2,4,7,15,30,60,120]` | Core Engine 待实现 | 状态机**逻辑**同源；**阶梯常量不同**（`bbcore.py:28` / `review.py:25`）→ LADDER 作**注入参数**（ADR-0001） |
| 判定契约 | `settle.grade` | `review.judge` | `mkt check` | 同一契约，答案形态不同 |
| 出卷 | `practice.pick_items` | `practice.pick_words` | pending | 同构 |
| 密钥/判分隔离 | `.keys/<date>.txt` + judged 账本 | `.keys/<账户>/<date>.txt` + judged 账本 | — | 同一铁律（ADR-0006/0008） |
| 独立交付 | `sheets/` 可整体搬走 | `交付成果/` 硬约束"纯 md、整体复制" | 交付物 | 用户需求早已实现 |
| 错题复盘 | `04-复盘/` | pending | `modules/错题整理系统/` | 概念同源 |

> **勘误（2026-10-10）**：本表早期版本将两项目的 LADDER 记为同一常量
> `[1,2,4,7,15,30,60,120]` 并称「逐字节相同」——**该结论错误**。经对照真实源码实测：
> bb-prep `[1,2,4,7,14,28,45]`（`D:\SixSigmaBlackBelt\src\bbcore.py:28`，考试型，封顶 45 天）、
> vocab-app `[1,2,4,7,15,30,60,120]`（`D:\Projects\vocab-app\src\review.py:25`，封顶 120 天）。
> 二者**仅状态机逻辑同源，间隔长度不同** → 内核据此将 LADDER 改为**注入参数**（ADR-0001）。
> 证据存档：`Project Audit/v0.1.0_工作路径图与计划_R1_审计_tbA_LessonOS.md`。

**复利漏点（当前痛点）**：bb-prep 与 vocab-app 引擎近克隆，但各自改 bug 不同步
（例：2026-10-10 bb-prep 修的"近期去重窗口"，vocab-app 没有）。本手册 + `learn_engine`
内核要解决这个漂移。

---

## 1. 三层共享资产架构

| 层 | 是什么 | 形态 | 消费方式 |
|---|---|---|---|
| **learn_engine** | 代码内核：题模 / 调度 / 出卷 / 判分 | 零**外部**依赖 Python 包，semver | `import learn_engine` |
| **tutor-prompt-library** | 判断与审美：教学契约 / 讲评风 / 复盘格式 | 版本化技能 / 模板文件 | 引用或拷贝 |
| **LESSON-OS playbook**（本手册） | 约定与 ADR：SSOT schema / 评审纪律 | Markdown 文档 | 人读 + 机器参考 |

差异化内容（题/词/概念、题型、领域权重、账户/学生模型）**留在各项目内**，不抽。

---

## 2. 资产形态与版本闸门（已定：方案 A+）

- **learn_engine = 零外部依赖的 Python 包**，`__init__.py` 带 `__version__ = "x.y.z"`（语义版本）。
- 各项目通过 **git submodule 钉 commit** 引用同一份（**已定：submodule，非 vendor**，见 ADR-0003）。
- **版本闸门**：改核心只 bump 版本号；消费项目**不主动升级就不受影响** → 治"核心更新误伤其他项目"。
- **独立交付**：内核纯 stdlib，交付时拷进交付物；`src` 本就不进交付物
  （bb-prep / vocab-app 早有此硬约束）。
  > **澄清**：「独立交付」= **交付物与项目库隔离**（交付物干净、可独立运行），
  > **不代表项目库要作为交付物整体拷贝**。

升级流程：改核心 → bump 版本 → 各项目主动升级 → 不主动升级 = 旧行为不变。

---

## 3. SSOT 元数据 Schema（共享 frontmatter 字段）

所有"学习条目"统一以下字段（Markdown + frontmatter，纯文本可移植）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | str | ✅ | 全局唯一，按来源身份发（如 `bb-00NN` / `Word` / `ex-001`），**绝不按位置** |
| `type` | str | ✅ | 条目类型（`question` / `word` / `mistake`） |
| `state` | enum | ✅ | `new` / `learning` / `review` / `lapsed` / `mastered`（见下方注） |
| `stage` | int | ✅ | 间隔阶梯阶数（0–`MASTER_STAGE`） |
| `due` | date | ✅ | 下次到期日（ISO） |
| `correct` / `wrong` / `reviews` | int | ✅ | 累计统计 |
| `difficulty` | float | ⚠️ | 难度（LADDER 下可省略；FSRS 后端启用时由 S/D 派生） |
| `domain` / `tags` | list | ⚠️ | 领域/标签（bb-prep 九域、vocab-app 账户、Kongzi 科目） |
| `note` | str | — | Obsidian 双链，指向原子笔记（如 `[[VI.B.9-均值方差和比率检验]]`） |

> **注（`state` 的两类取值，2026-10-11 裁决 B4）**：
> - **`new` = pool 分流哨兵**，表示「尚未建卡」——两真源均为 `setdefault("state","new")`，
>   卡片一旦进入调度就再也不会是 `new`。**它不是 SRS 状态。**
> - **`learning` / `review` / `mastered` / `lapsed` = 状态机合法态**（= 内核 `model.STATES`）。
> - 内核以 `model.POOL_NEW` 常量表达哨兵（不硬编码字面量）。
>   **不得把 `new` 并入 `STATES`** —— 会让 `next_schedule` 的合法输入域模糊。
| `history` | list | — | 回顾日志（FSRS 调参用，可选） |
| `S` / `D` | float | — | **引擎保留字段**：FSRS 后端启用时填充（稳定性 / 难度），LADDER 下留空 |

**各项目可加自有字段**（不冲突即允许）：vocab-app 的 `word/meaning/image/quote_zh`；
Kongzi 的 `student/subject/topic/reason`。共有字段语义必须一致。

---

## 4. 共享内核 API 契约（learn_engine 必须实现）

```python
# 文件读写：只改 frontmatter 中已存在的键，正文一字不动
parse_front(text) -> dict
write_front(path, updates: dict) -> None

# 调度：LADDER 为默认实现；FSRS 可作为同接口后端（P2）
is_due(card: dict, today: date) -> bool
next_schedule(old_stage: int, correct: bool) -> (stage, state, gap_days)   # 纯函数，唯一事实来源

# 出卷：到期优先 + 九域/账户权重 + 近期去重窗口
pick_session(pool, n_review, n_new, opts) -> (review_items, fresh_items)

# 判定：确定性，模型不参与
normalize(s) -> str                      # 大小写/空白归一化
judge(raw: str, answer: str) -> "correct" | "wrong"

# 隔离与幂等：密钥在交付物之外；judged 账本保证可反复扫描幂等
load_key(note) / load_judged(note) / save_judged(note, nos)
```

**独立交付硬约束**（三项目通用）：`src` 不得被交付物引用；交付物纯 Markdown 可整体复制；
密钥/答案绝不进交付物。

---

## 5. 判定契约（铁律，三项目通用）

1. 判分**纯代码、模型不参与**。
2. 作答做**大小写归一化 + 截断"；思路："后的说明**（防 `XBARR` 被误抓成选项）。
3. **密钥缺失拒绝结算、绝不猜测**。
4. **幂等**：已判过的题以成绩单/账本题号为账，不重复判 → 可反复扫描。
5. 成绩单与实际作答矛盾时**先怀疑判分器**，不直接下"水平差"结论。

---

## 6. ADR 约定（`ADR/` 目录，一决策一文件）

**载体**：`ADR/` 目录下独立文件，命名 `ADR-NNNN-<短标题>.md`（如
`ADR-0002-golden-set验收法.md`）。**不使用单文件集中管理**（早期 §6 曾写「单文件
`adr.md`」，与仓库实际不符，2026-10-11 纠正）。

**模板**：唯一模板是 `ADR/ADR-template.md`（**禁止在别处内联副本** —— 防双 SSOT）。

**硬约束**：
- 正文引用的 ADR 编号**必须有实体文件**；无实体的编号不得引用（曾出现 0006/0008 被引用
  但无文件的情况，2026-10-11 已补）。
- 一决策一文件，不合并；废弃不删档，改「状态：废弃」并写明被谁取代。

**条目格式**（见 `ADR-template.md`）：

```
## ADR-NNNN <标题>
- 状态：提议 / 接受 / 废弃
- 背景：为什么现在要决策
- 决策：我们做了什么
- 备选：考虑过什么、为何不选
- 后果：正向 / 负向（含对其他项目的影响）
```

---

## 7. 错题复盘约定（共用闭环）

录入 → 分析（归纳同类错误共性）→ 出题验证（AI 出同类题，答对才算"已复习"）→ 已复习。
AI-Kongzi `modules/错题整理系统/` 已建此闭环，可作参考实现；bb-prep `04-复盘/` 同构。

---

## 8. 路线图

- **P0（进行中）**：本手册 + 三项目源码盘点（证据见 §0）。低风险、零代码改动。
- **P1（抽代码）**：从 bb-prep `src/` 重构成 `learn_engine` 包（原地重构，bb-prep 经 `import` 继续跑、行为不变）；FSRS 留接口不入核。
- **P2（复用 + 技能化）**：vocab-app / AI-Kongzi 接入 `learn_engine`；FSRS 可选后端（同 `next_schedule` 接口替换）；建 `tutor-prompt-library` 技能库（CI golden-set 测试）。

---

## 9. 已知差异（留在各项目，不抽）

| 维度 | bb-prep | vocab-app | AI-Kongzi |
|---|---|---|---|
| 条目类型 | 考试题（选择/计算） | 英文词 | 学生错题 |
| 答案形态 | 字母集 / 数值 | 英文词 exact-match | 正确旗 `--correct` |
| 领域权重 | 九域配额倾斜 | 账户维度 | 科目/知识点 |
| 间隔阶梯 LADDER | `[1,2,4,7,14,28,45]`（封顶 45 天） | `[1,2,4,7,15,30,60,120]`（封顶 120 天） | 待定（Core Engine 未实现） |
| 特殊机制 | 配图依赖、双链笔记 | 线索渐隐（A/B/C 题型） | AI 生成同类题 |

---

## 10. 飞轮触发协议（SSOT）

> 本节回答：**什么时候**该把项目里的一处改动沉淀回内核。
> `AGENTS.md` 只放指针，本节是判据全文。

### 10.1 三个入口（触发点各不相同）

| 入口 | 触发时机 | 触发点（强制问句） | 稳定性 |
|---|---|---|---|
| **A · 新项目立项** | 开新项目 | README 第一句必答：「本项目消费 LESSON-OS 吗？钉哪个版本？」 | **高**（立项仪式） |
| **B · 排优化工单** | 写工单时 | 每个工单必答：「这是**共性**还是**特性**？」 | **中高**（模板强制） |
| **C · 运行中发现** | 干活途中 | agent 察觉「这个缺陷大概是共性」 | **中**（靠纪律，需兜底） |

### 10.2 入口 C 的三段式（**明令禁止当场改内核**）

1. **先修项目** —— 绝不为等内核而阻塞生产（bb-prep 每天要出卷，停一天是真损失）
2. **同时留一行标记** —— 在项目 `SEDIMENT.md` 追加：
   `2026-10-10 | 出卷近期去重缺失 | 疑共性 | bb-prep.src/practice.py`
3. **归因推迟到阶段边界** —— 批量处理，届时才走闸门

> 第 3 条是关键：当场判归因 = 中断主任务 + 换上下文，成本远高于批量处理。

### 10.3 诚实边界：「发现」无法机械检测

- **「发现共性」本身无法机械检测** —— 没有 linter 能判断"agent 是否想到了某个共性问题"。
  它只能靠本文档 + `AGENTS.md` 的约束和 agent 的纪律。**这是真正的判断题。**
- **「上报 / 留标记」可以机械化** —— 命中 VCP 步骤 6 硬规则：
  "机械性违规一律做成确定性检查，到此为止。"

**兜底机制（必需）**：即使入口 C 漏报，也要在**阶段边界**做一次「内核 vs 各项目」对账，
把漏掉的共性缺陷捞回来。**飞轮不能只靠正推，必须有反向扫描。**

### 10.4 归因闸门（唯一的模型判定点）

| 项 | 值 |
|---|---|
| 问句 | 「这个缺陷换成 vocab-app / Kongzi 的场景，是否同样会发生？」 |
| 工具 | 候选用 JEV `noul`（`D:\Projects\jev-gate`），**当前状态：未测** |
| 阈值 | ⚠️ **必须重测，不可抄 `0.30`** —— 那是"内容在未来仍成立吗"这一条的实测值，**换问句即失效** |
| 措辞 | ⚠️ **必须固定并写进本文档** —— JEV §3 实测同一句加前缀 0.660→0.42（**0.25 量级抖动**） |
| 启动条件 | 累计 **≥16–20 条归因记录**后，才做预登记 + 重测阈值 |

**⚠️ 适用范围硬边界（德企合规）**：JEV 生产路由 OpenRouter 是**美国节点**。
- 个人学习项目（LESSON-OS / bb-prep）→ ✅ 可行
- **BOS 工厂 AI 应用（EOP / 设备维护 / 工单）→ ❌ 不可用**（数据出境）
  且本地 Laya 已判废对中文不可用 → **这条路目前是断的**。

### 10.5 风险与成本

| 风险 | 后果 | 缓解 |
|---|---|---|
| 漏报（共性当特性） | 漂移复发 | 阶段边界对账（§10.3） |
| 滥报（特性当共性） | 内核变缝合怪 | 归因闸门 + ADR 强制写**排除理由** |
| 当场改内核 | 阻塞生产 + 误伤三项目 | 铁律：先修项目，后沉淀（§10.2） |
| 仪式过重 → 绕过 | 飞轮空转 | 三档成本，别用大炮打蚊子 |

| 档位 | 动作 | 单次成本 | 适用判据 |
|---|---|---|---|
| **L1** | 只留一行标记 | ~1 分钟 | 拿不准是否共性 |
| **L2** | 改内核 + bump + ADR | ~30 分钟 | 确认共性，影响面 ≤ 1 函数/契约 |
| **L3** | L2 + 一轮 audit-os | ~60 分钟 | 触及架构 / 版本闸门 / API 契约 |

**盈亏平衡**：单次完整沉淀 ≈ **45 分钟**；不沉淀 = 每个后续项目**重复排查 ~90 分钟**。
→ **预计重现次数 ≥ 2 即正收益**。飞轮内有 3 个项目，N=3 稳稳覆盖。

> **成本非线性**：L1 几乎免费 → **宁滥勿缺地留标记**是对的，
> 因为筛选发生在 L2 闸门，不在 L1。

### 10.6 改内核铁律（引自 JEV §8，已被 13 天线上数据检验）

| 纪律 | 落到改内核流程 |
|---|---|
| **预登记** | 看数据**前**把通过门槛写进独立 dated 文件，之后**不许改** |
| **点火验证** | 改完跑一次**真实出卷**（不是只跑单测），确认新分支被触发、日志查得到 |
| **失败条款前置** | 「P1-A 不过 ⇒ 不进入 P1-B」写在前面 |
| **部分通过就报部分通过** | 说清差在哪，不粉饰 |

---

## 11. 标准库注册规范（SSOT）

> 本节定义：**什么样的资产配进「标准库」**，以及标签怎么写。
> 注册表本体在 `D:\Projects\LIBGOV\registry\REGISTRY.md`。

### 11.1 入库门槛（三条，全中才入库）

| # | 门槛 | 判据 |
|---|---|---|
| ① | **已被 ≥2 个项目复用** | 有**真实**消费方，不是"打算复用" |
| ② | **有 SSOT 手册** | PLAYBOOK / README / AGENTS 写明契约 |
| ③ | **有版本载体** | 代码有 `__version__` 或等价常量 |

> **门槛本身就是信噪比过滤器** —— 注册表一旦退化成"所有项目清单"，检索结果全是噪音。
> **门槛①按事实记，不按计划记。**（LESSON-OS 当前记 `planned` 正因此）

### 11.2 标签 Schema（写在各库 frontmatter）

```yaml
---
kind: kernel          # kernel | prompt-library | playbook | index
domain: learning      # learning | agent-judgment | investment | factory | doc
maturity: planned     # planned | skeleton | implemented | adopted
version: 0.1.0
---
```

`maturity` 四档判据 **= 门槛三中三**（让标签自带判据）：

| 档 | 含义 |
|---|---|
| `planned` | 设计上确定要复用，**尚无真实消费方**（骨架期引进来是负债） |
| `skeleton` | 骨架已立，消费方 0 |
| `implemented` | 自身实现完整、测试通过，消费方 < 2 |
| `adopted` | **已被 ≥2 项目真实复用** |

### 11.3 双轨原则（防双 SSOT）

- **各库 frontmatter = 真源**（人读入口）
- **`LIBGOV/registry/REGISTRY.md` = 生成物**（`build_registry.py` 扫描产出，**明令禁止手改**）

### 11.4 检索入口

独立 skill **`standard-lib-search`**（可独立调用），并作为 **VCP 步骤 1 的第 4 路并行**支路。
**硬闸门**：无检索结论不得进 VCP 步骤 3。
**降级路径合法**：「检索无命中 → 从零构建」本身是一条有效结论。

### 11.5 版本语义与 bump 授权

| 级别 | 定义 | 授权 |
|---|---|---|
| PATCH | 只改 bug，签名不变 | agent 自主 |
| MINOR | 新增带默认值参数 / 新增导出符号 | agent 自主 |
| MAJOR | 改签名 / 改默认行为 / 改 frontmatter 语义 / **改阈值** | **必须人工确认**（会动消费方） |

### 11.6 不在本注册表范围

- `Audit OS` —— 本质是**技能**，真源属技能库（`~/.agents/skills/audit-os`），归 `skills-index` 管
- `skills-index` —— 生成器工具，非被复用库

---

_本手册是种子文件，后续 `learn_engine` 与 `tutor-prompt-library` 落地后在此追加索引。_
