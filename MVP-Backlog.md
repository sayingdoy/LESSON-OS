# MVP-Backlog — LESSON-OS 垂直切片工单

> 建立 2026-10-10 | Owner: Jason
> 切片原则：**每片都能独立验证、独立回滚**。不按"层"切（先写 schema 再写代码），
> 按**贯穿路径**切（一片打通一条端到端通路）。

---

## 现状

| 阶段 | 状态 |
|---|---|
| P0 手册 + SSOT schema + 路线图 + 骨架 | ✅ 完成 |
| **R1 契约修正（裁决 B1–B5 / A3余 / C1余）** | ✅ **完成 2026-10-11**（内核 → `0.2.0`） |
| **P1 抽代码（本 backlog）** | ✅ **完成 2026-10-13**：A1 ✅ / A2 ✅ / A3 ✅ / A4 ✅ / B1 ✅ / B2 ✅ / B3 ✅ |
| **P1-C 收尾（版本锚点）** | ✅ **完成 2026-10-13**：C1 ✅ / C2 ✅ / C3 ✅ |
| **P2 接入 + 技能库** | 🔄 **进行中 2026-10-13**：vocab-app ✅ 已接入（maturity→adopted）；AI-Kongzi 映射分析＝暂不接入（指针已保鲜）；tutor-prompt-library 待启动 |
| **技术债 B7（版本引用机械检查）** | ✅ **完成 2026-10-13**（LIBGOV 侧实装，见下方清单） |
| 技术债 B6（四份日期解析收敛） | ⬜ 待启动 |
| P2 接入 + 技能库 | ⬜ 待启动 |
| FSRS 后端 | ⬜ P2 候选 |

**技术债清单**（P1 要还的）：
- ✅ **已清（B7）—— 版本引用机械检查（2026-10-13 18:18 实装，LIBGOV 仓）**：
  `build_registry.py` 新增 `scan_doc_versions()` + `version_audit()`，版本引用扫描
  从「只取 `DOC_CANDIDATES` 首命中」扩到**全量** —— frontmatter 版本 ≠ `__version__`
  → **硬失败**（`--check` 退出码 1）；跨文档 frontmatter 不一致 → 硬失败；
  散文「版本 X.Y.Z」不符 → **警告**（只报不改，G5 原则）。两段式手册版
  （「版本 0.4」）不匹配以防误报。实跑确认 `AGENTS.md:6` 散文引用首次进入
  机械检查范围（此前零覆盖）；单测 6/6 + 实仓集成通过。
  **残余**：散文层为警告级，过渡期仍须人工复扫（见 C3 附带修复节）；
  彻底收敛走 SSOT 规则（版本只在 PLAYBOOK frontmatter 出现一次）——
  建议留待下次内核 bump 时一并做，可立 ADR-0009 记录分级判据。
- `picker` / `scheduler` / `vault` 内部**四份同源日期解析**（B6，P1 收敛到一处）
- ✅ **已清**：`grader.Grader.judge` 基类占位 / bb-prep adapter 缺失 → **实装**
  （2026-10-13，**P1-B1**，内核 `0.5.0`；4 个判分原语 + 策略全注入；断言 25 → **47** 项）
- ✅ **已清**：`vault.write_front` 占位 → **实装**（2026-10-13，**A2**，内核 `0.4.0`；断言 16 → **25** 项）
- ✅ **已清**：`tests/` + golden-set 已建（2026-10-11，13 项）
- ✅ **已清**：`picker` 新题贪心 + 温和上限已移入（2026-10-13，A4，断言 16 项）
- ✅ **已裁决（2026-10-13，A3 取 ②）**：`picker` 的**补位分支**与真源语义不同 ——
  内核把候选题按 `item["state"]` **路由回** `review`/`fresh` 两档；真源 `pick_items`
  收尾是 `fresh += rest[:need]`（**一律并入 `fresh`**）。**仅在候选池不足时触发**。
  裁决 **②**：内核保留自身语义，**bb-prep 不调用内核补位**（补位仍留
  `practice.main()`）。池充足时两路径一致 → 出卷逐字节相同（**已实测**）。

> **R1 契约修正已完成**（2026-10-11，内核 `0.1.0 → 0.2.0`）：
> B1 `judge` → `str`；B2 `pick` 显式注入（去重/权重不再空转）；B3 ADR-0002 固定 `rng`
> （`FIXED_SEED=20261010`）；B4 `POOL_NEW` 常量；B5 引用改真源。
> 详见 `audit_log.md` 决策链。

---

## P1-A · 打通「排期写入」端到端（第一片，零风险）

**为什么先做这片**：`scheduler` 是纯函数状态机（无 I/O），`vault.write_front` 是唯一
写盘入口。这片打通后，「读入 → 排期 → 写回」形成闭环，且**行为可逐字节比对**。

| # | 工单 | 验收 |
|---|---|---|
| A1 | 建 `learn_engine/tests/` + golden-set 骨架 | ✅ **完成 2026-10-11**（13 项断言全过，基线存 `golden_v0.2.0.json`） |
| A2 | 实装 `vault.write_front`（只改已存在的 frontmatter 键，正文一字不动） | ✅ **完成 2026-10-13**（内核 → `0.4.0`；新增 9 项字节级断言，共 25 项） |
| A3 | bb-prep 排期逻辑改为 `import learn_engine` | ✅ **完成 2026-10-13**（**选题 + 阶梯双委托**；出卷**逐字节相同**：sha256 `d92b0fbb…` / key `df9d4426…`） |
| A4 | **补 `picker` 的新题贪心 + 温和上限**（B2 遗留） | ✅ **完成 2026-10-13**（内核 → `0.3.0`；断言 16 项全过；与真源 `src/practice.py:181-217` 同源） |

> **✅ A3 前置裁决项（2026-10-13 已裁决 → 取 ②）**：内核 `pick()` 的**补位分支**
> 按 `state` 路由回 `review`/`fresh`；真源 `pick_items` 一律并入 `fresh`。
> 该差异**只在候选池不足时触发**，golden-set 不覆盖。
> 三选一：① 内核改为与真源一致；**② 内核保留现状，bb-prep 侧不调用内核补位**（只取
> 纯排期结果，补位仍留 `main()`）；③ `pick()` 增参数 `fallback`。
>
> **裁决 = ②（Jason 2026-10-13）**。落地：内核**一行未改**；bb-prep 只在**池充足**
> 路径上委托，`practice.main()` 的「泄漏剔除后补足」原样保留。实测 528 题/需求 22 题
> 条件下补位分支**根本不触发**，故出卷逐字节相同。
>
> **A3 落地范围（2026-10-13，比 backlog 原始措辞稍宽）**：backlog 原文只写「`bbcore.py`
> 排期逻辑」，实际落地为**两处** ——
>   · `bbcore.apply_result` → 委托 `learn_engine.scheduler.apply_result`（**阶梯/状态机**）
>   · `practice.pick_items` → 委托 `learn_engine.picker.WeightedPicker`（**选题排期**）
> 后者才是「出卷逐字节相同」判据的检验对象；前者另做等价性核对（204 组，0 差异）。

**预登记（写死在前面，不许事后改）**：
> **P1-A 通过判据**：A2 单测全过 + A3 的 bb-prep 出卷输出与改前**逐字节一致**。
> **验收第 0 步**：`rng = random.Random(20261010)` 必须固定（ADR-0002）。
> **失败条款**：任一不过 ⇒ **不进入 P1-B**，先查差异来源。
> **LADDER 处理**：`bbcore.py:28` 的 `[1,2,4,7,14,28,45]` 与 `review.py:25` 的
> `[1,2,4,7,15,30,60,120]` **不同** → LADDER 作**注入参数**，内核只提供默认值（ADR-0001）。

---

## P1-B · 打通「判分」端到端（第二片，含 adapter）

| # | 工单 | 验收 |
|---|---|---|
| B1 | 实装 `grader` 的 bb-prep adapter（字母集 / 数值） | ✅ **完成 2026-10-13**（内核 → `0.5.0`；4 个判分原语，策略全注入；golden **47 项**全过） |
| B2 | 补 `judge` 的回归测试（覆盖历史判分器 bug 场景） | ✅ **完成**：21 项新断言覆盖 2026-10-06 全部边界（小写/多选/带思路/XBARR 陷阱/漏选/放弃）+ **真实数据复现 10-05=60% / 10-06=70%** |
| B3 | bb-prep `src/` 判分改为 `import learn_engine` | ✅ **完成**：`letters`/`judge_tf`/`judge` 三符号委托内核；**88 条真实作答 0 差异** |

> **P1-B 通过判据：B1/B2 单测全过 + B3 判定与改前完全一致** → ✅ **全部达成**。
> ⚠️ **判分铁律不可破**：判分必须是**纯代码**，模型不参与（PLAYBOOK §5.1）。
>
> **B1 落地形态（比 backlog 原始措辞更明确）**：内核只提供**领域无关的判分原语**
> （`LetterSetGrader` / `TrueFalseGrader` / `NumericGrader` / `KeywordGrader`），
> 一切**项目策略**（中文分隔符 `；思路：`、真值词表、字母范围 A-H、容差）由 bb-prep
> **显式注入**；**按 qtype 的路由留在 bb-prep**（qtype 词表是项目策略，内核不认识）。
>
> **B2 的真实数据基底**：`03-题库/sheets/` 全部历史卷共 **88 条真实作答**
> （mc 60 / ms 21 / judge 5 / calc 2），基线存于
> `D:\p1a3-backup-20261013\p1b-baseline\judge-baseline.json`。
>
> **附带纠正**：`judge_tf` 原 docstring 称"作答为空返回 'blank'"——与实际代码
> 不符（各分支都返回 `correct`/`wrong`，无 `blank`）。已随委托一并纠正。

---

## P1-C · 收尾：版本锚点与发布（小片）

| # | 工单 | 验收 |
|---|---|---|
| C1 | 各仓库 `git init`（顺序：LESSON-OS → bb-prep → vocab-app → AI-Kongzi） | ✅ **完成 2026-10-10**，4 仓库就绪 |
| C2 | 消费项目以 `git submodule` 钉 LESSON-OS commit | ✅ **完成**：bb-prep `vendor/LESSON-OS` @`948b419`（＝内核 `0.5.0`），URL 指向远端 |
| C3 | 补 `__version__` bump 记录 + ADR 归档 | ✅ **完成 2026-10-13**：① 新建 `CHANGELOG.md`（0.1.0→0.5.0 逐版本，含 BREAKING 标记 + 「版本 × 消费方对照」表）；② 新建 `ADR/README.md` 索引（6 条实体 + 空洞号 0005/0007 显式登记 + 跨项目编号空间说明）；③ 修 3 份陈旧文档（见下） |

> **C3 附带修复 —— 陈旧文档**（三份都指向过时状态，agent 读了会误判）：
> - `AGENTS.md`（**执行宪法，最严重**）：版本 `0.1.0`→`0.5.0`；状态 `planned`／「尚无真实消费方」
>   → `implemented`；目录地图「`write_front` 待实装 / adapter 待补 / 基类占位」→ 全部实装
> - `README.md`：P1「待启动」→ 完成；状态板「骨架（占位待实现）」→ 内核 0.5.0
> - `PLAYBOOK.md`：§11.1 消费面 `0.4.0` 双委托 → `0.5.0` 三委托（补判分）；
>   §11.5 补「bump 三处同步」与版本漂移实录
> - 根因：**生成器只扫 `PLAYBOOK.md`**（`DOC_CANDIDATES` 优先级），其余文档的版本引用
>   无机械检查 → 漂移不可见。已记入技术债（**B7**）。

> **备份已闭环**：4 仓库全部推送至 `ecs:/srv/git/`（自建裸库，异地）。
> 日常同步 `bash scripts/sync_all.sh`。详见 ADR-0003「备份闭环」。
> 残余风险：ECS 单点（无第三方托管）→ P2 可加 bundle 到网盘。

---

## P2 进展（2026-10-13 启动）

- ✅ **vocab-app 接入**（`a7d7848`）：submodule 钉 `948b419`＝0.5.0；`review.py`
  四处委托（判分/排期/结算计算/日期解析）；**1162 项 + 端到端 0 差异**；
  保留本地四个（is_due 边界差异 / parse_front 类型强转 / write_front 语义 /
  pick_words 算法）逐条记录于 vocab-app ADR-0012。
  → 消费方达 2 个，`maturity: implemented → adopted`（ADR-0009 同期立档）。
- ⛔ **AI-Kongzi 映射分析结论＝暂不强行接入**（`0e1c16b`，仅指针升级
  v0.1.0→v0.5.0 保鲜，零运行时影响）：
  | 内核能力 | AI-Kongzi 对应物 | 判定 |
  |---|---|---|
  | `grader` 四原语 | 无代码判分 —— CLI 人工 `--correct/--wrong` 置 `passed` | ❌ 无委托对象 |
  | `scheduler` 阶梯状态机 | topic 级掌握度 + 固定 7 天复测（`judge_mastery`） | ❌ 模型不同，委托即改行为 |
  | `vault.parse_front/write_front` | `_parse_frontmatter` 返回 `(fields, body)` 元组；`_build_frontmatter` 全量重建 | ❌ 契约不同 |
  | `vault.as_date` | 2 处 inline `fromisoformat`（`recommend` 因子 1/5） | ⚠️ 可委托但零去重价值（无重复解析器） |
  纪律依据：A3 先例（`pick_words` 留本地）+「不为凑数而委托」—— 消费方按**事实**记。
  **Sprint 2B 建议**：Core Engine 实装时若把 7 天复测升级为 SRS 阶梯，
  `scheduler` 可直接用（LADDER 注入）；判题保持人判；frontmatter 统一形状再议。
- ⬜ `tutor-prompt-library` 技能库 + CI golden-set
- ⬜ FSRS 可选后端（同 `next_schedule` 接口替换）
- ⬜ `standard-lib-search` 独立 skill 串进 VCP 步骤 1

---

## 纪律（每片都适用）

1. **切片内不跨阶段**：A 片没验收完不动 B 片。
2. **预登记不改**：通过门槛在看数据前写死。
3. **点火验证**：改完必须跑一次**真实出卷**，不是只跑单测。
4. **部分通过就报部分通过**：说清差在哪。
