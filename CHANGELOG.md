# CHANGELOG — learn_engine

> **内核版本变更记录。** 真源是 `learn_engine/__init__.py` 的 `__version__`；
> 本文件是**人读的 bump 记录**（谁在什么时候、为什么改了版本号）。
>
> 版本语义（PLAYBOOK §5 / §11.5）：
> **PATCH** = 改 bug、签名不变 ｜ **MINOR** = 加带默认值参数 / 新导出符号 ｜
> **MAJOR** = 改签名 / 改默认行为 / 改 frontmatter 语义 / 改阈值（**须人工确认**）。
>
> ⚠️ 消费方**不主动升级就不受影响** —— 版本闸门载体是 `git submodule`（钉 commit，ADR-0003）。

---

## [未发布]

（无）

---

## [0.5.1] — 2026-10-13 · PATCH · `is_due` 边界崩溃修复

**PATCH**（改 bug、签名不变）｜ 审计轮次文件族：
`Project Audit/Archive/v0.5.1_is_due边界修复_R1_方案_tbd` +
`..._R1_审计_tbA_auditor` + `..._R1_终版_OK`（verdict 🟡 有条件通过，
6 项处置结论见终版）

- **问题**：`scheduler.is_due` 对非 str 非 None 的 due 值（int/bool，来自数值强转
  型 frontmatter 解析器的脏数据，如 `due: 0`）直接 `d <= ref` → **TypeError**。
- **修法**：增加第三条输入路 —— 不可解析值按「到期」处理（`return True`），
  对齐两消费方本地实现「经 `as_date` 归一」的真源语义；不引 `vault`
  （避免模块耦合）、不改签名、既有三分支（None/str/date）行为原样。
- **回归风险 ≈ 0**：内核 `is_due` **零调用方**（bb-prep / vocab-app 均保留本地
  `is_due`，grep 实证）→ 无消费方受影响；**消费方无需联动升级**。
- **测试**：golden-set 新增 14 例 `is_due` 边界断言（10 例 dict 形态 + 4 例
  Item 属性形态，后者为审计 R1 指出零覆盖后补）→ **47 → 61 项**；picker 场景
  golden 输出**逐字节不变**（`golden_v0.5.1.json` 与 0.5.0 基线等价，随版本分发）。
- **不在本版范围**：`picker._is_due` 同形状问题 —— 归技术债 **B6**（四份日期
  解析收敛）一并处理，不扩大本 PATCH 爆炸面。
- **已知边界复述**：消费方**重新委托** `is_due` 是各自 P2+ 决策，本版只保证
  内核侧可安全委托。

---

## [0.5.0] — 2026-10-13 · `948b419`

**P1-B1 判分原语（bb-prep 风格 adapter）** ｜ MINOR

新增四个**领域无关的判分原语**，真源 bb-prep `src/bbcore.py:364-453`：

- `LetterSetGrader` —— 选项字母集（单选/多选）：截断分隔符 + 提字母 + 去重排序大写
- `TrueFalseGrader` —— 判断题：归一真假，**只取第一个判断词**（附注不得干扰）
- `NumericGrader` —— 计算题：数值 + **逐题**容差
- `KeywordGrader` —— 要点题：关键词全含

**分层原则（关键）**：内核只给机制，消费方给策略。中文分隔符、真值词表、
字母范围、容差**全部注入**；内核**不预设中文习惯**、**不认识 `qtype`**；
**按 `qtype` 的路由留在消费方**。golden-set 每类都带一条「换注入 → 结果就变」
的参数化断言，把这条原则钉死为**可执行断言**。

两处「照抄真源、不顺手修」（均加断言锁死）：
- `tol` 为 falsy（`0` / `""`）时**回退默认 `0.01`** —— 真源 `float(x or 0.01)` 语义，
  不把 `0` 当「零容差」；
- calc **不截断思路** —— 思路里的数字也参与比对（既有语义，保持等价）。

附带纠正：`judge_tf` 原 docstring 称「作答为空返回 `blank`」，**与实际代码不符**
（各分支只返回 `correct`/`wrong`）。已随委托纠正。

**验收**：golden-set 25 → **47 项**全过；`golden_v0.5.0.json` 与 `golden_v0.4.0.json`
**逐字节一致**（sha256 `fde8b715…`）→ 证**未改变选题行为**（纯新增能力）。

> 📌 **勘误**：`948b419` 的 commit message 写「25 → **46** 项」——**实为 47 项**
> （`grep -c "def test_"` 与 `unittest` 实跑均为 47）。commit 已推送，不改写历史，
> 以本文件为准。

**消费方**：bb-prep 判分改为委托内核（同批提交 `88495cd`），88 条真实作答 **0 差异**。

---

## [0.4.0] — 2026-10-13 · `1b37ed0`

**P1-A2 实装 `vault.write_front`** ｜ MINOR

`write_front` 由占位（`NotImplementedError`）转为实装，真源 bb-prep
`src/bbcore.py:write_front`（逐行核对，逻辑同源）：

- **只改已存在的键**（按**键名**定位，不写死行下标 —— 字段列数会演进）
- 新键**追加到 frontmatter 末尾**（顺序 = 传入 dict 序）
- **正文一字不动**（`text[m.end():]` 原样回写，不污染题干/选项/解析）
- 行尾**强制 LF**（`newline="\n"`）—— 不固定行尾会让每次挂链/挂图都把整文件
  标记成「已修改」，真实 diff 被噪声淹没

⚠️ 唯一差异：缺 frontmatter 时抛 `ValueError`（库语义）vs 真源 `SystemExit`
（脚本语义）。异常路径，正常调用不触发。

**验收**：golden-set 16 → **25 项**（新增 9 项字节级断言：正文零变化 / 仅列出的键变 /
LF 归一（含 CRLF 源）/ 新键追加与顺序 / 幂等 / 值写法 / 异常路径）；
`golden_v0.4.0.json` 与 `golden_v0.3.0.json` **逐字节一致**（sha256 `fde8b715…`）
→ 证 A2 未改变选题行为。

**里程碑**：bb-prep 经 `vendor/LESSON-OS` submodule 接入 → `maturity`
`planned` → **`implemented`**（消费方 1 个，未达 ≥2）。B-1「无真实消费方」解除。

---

## [0.3.0] — 2026-10-13 · `926265b`

**P1-A4 新题贪心 + 温和上限（对齐 bb-prep）** ｜ ⚠️ **BREAKING**

内核 `WeightedPicker.pick` 补齐真源 `src/practice.py:181-217` 的
「新题按域缺口**贪心**取 + **温和上限** `cap=⌈w/tot·n⌉+1`」，**逐行同构**：

- 先在上限内挑「域欠配最多」；全部触顶才放开上限（宁可覆盖不足，也不留空位）
- 已入选的复习题**先计入** `cur`，避免复习题已覆盖的域被重复倾斜
- rng 消耗顺序严格保持：`exam_first` 排序 → `shuffle(due)` → 贪心循环
- `weighted=False` 分支不变（退回旧行为）

⚠️ **行为变更**：同一 rng 下新题档与 0.2.0 **不同** → 消费方升级须重跑验收（G3）。

**验收**：golden-set 13 → **16 项**；新基线 `golden_v0.3.0.json`。

**附带**：`PLAYBOOK.md` frontmatter `version` 0.1.0 → 0.3.0（此前**滞后**，
注册表因此静默记旧值）；`AGENTS.md` 注册表路径 `lib-index` → `LIBGOV/registry`。

---

## [0.2.0] — 2026-10-11 · `4a05108`

**R1 七项待裁决全部落地** ｜ ⚠️ **BREAKING**

契约修正（对应 `audit_log` R1 裁决）：

- **B1** `judge` 返回类型 `bool` → `str`（`"correct"`/`"wrong"`），对齐 bb-prep / vocab-app 双源
- **B2** `pick` 改**显式注入**：消除 `getattr` / `_recent` 与恒空 `{}` 的假能力；
  新增 `recent` / `history_counts` / `domain_weights` / `is_exam` 形参；近期去重作排序首键
- **B3** ADR-0002 补「验收第 0 步：固定 rng」+ `FIXED_SEED=20261010`
- **B4** 新增 `POOL_NEW` 常量；`new` 明确为 **pool 哨兵**，**不入 `STATES`**；
  `Item.state` 默认与 `from_front` 兜底改 `POOL_NEW`（对齐双源 `setdefault`）
- **B5** 内核引用改真源 `docs/契约/引擎与数据.md`（4 处）
- **C1 余** 新增 `ADR-0006` / `ADR-0008` 实体文件
- **A3 余** `PLAYBOOK.md` §6 改 `ADR/` 目录约定，**删内联模板**

**里程碑**：`learn_engine/tests/` + `golden_set.py` 建立（**13 项**全过，
固定 seed / today）→ golden-set 验收法（ADR-0002）首次实装。
R1 续篇归档至 `Project Audit/Archive/`。

---

## [0.1.0] — 2026-10-10 · `620a334`

**骨架落成** ｜ 初始版本 · `maturity: planned`

- `PLAYBOOK.md` SSOT：§0 勘误 + §10 飞轮触发协议 + §11 标准库注册规范
- `AGENTS.md` 执行宪法（五条铁律）
- `MVP-Backlog.md`：P1 三片垂直切片（A 排期 / B 判分 / C 版本锚点）
- ADR-0002 golden-set 验收 / ADR-0003 git+submodule / ADR-0004 JEV 候选（未测）
- `learn_engine` 内核骨架：`model` / `scheduler` / `vault` / `grader` / `picker`；
  `vault.write_front`、`grader` adapter、`picker` adapter **三处 `NotImplementedError`**

---

## 版本 × 消费方对照

| 内核版本 | commit | 日期 | bb-prep 钉的版本 | 备注 |
|---|---|---|---|---|
| 0.1.0 | `620a334` | 2026-10-10 | — | 骨架，无消费方 |
| 0.2.0 | `4a05108` | 2026-10-11 | — | 契约修正（BREAKING） |
| 0.3.0 | `926265b` | 2026-10-13 | — | 贪心+上限（BREAKING） |
| 0.4.0 | `1b37ed0` | 2026-10-13 | `1b37ed0` | **首个真实消费方接入** → `implemented` |
| 0.5.0 | `948b419` | 2026-10-13 | `948b419` | 判分原语 + 判分委托 |

> 消费方钉版本 = `vendor/LESSON-OS` submodule 指针（`git ls-tree HEAD vendor/LESSON-OS`）。
