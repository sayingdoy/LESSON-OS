# HANDOFF · LESSON-OS 跨项目学习内核分支

> 本对话总结，供下一 agent 接手「项目飞轮系统」开发。按 handoff 技能要求撰写：
> 引用其他产物用路径，不重复内容；含 suggested skills；已脱敏。

- **源对话**：2026-10-09 ~ 2026-10-10，bb-prep 备考 + 跨项目 OS 设计讨论
- **本工作区**：`D:\projects\LESSON-OS\`（已落盘，自包含，任何 agent 可接手）
- **规范说明**：handoff 技能默认存系统临时目录；按用户显式要求，此处将 handoff 与该分支产物
  同置于可复用工作区，便于任何 agent 直接接受并开发。

---

## 一、本对话做了什么（按时间）

### A. bb-prep 授课（主线 + 插单）
- **L13 · `VI.B.13` 非参数检验**（插单序 3）：建笔记卡 + 课次，靶心 `bb-0216`
  （把参数检验「方差齐性」套到非参 Mood 中位数）。Jason 作答 `1b 2c 3c` → **3/3 升 ✅**，序 3 清条。
- **L14 · `VI.B.9` 均值、方差和比率检验**（插单序 4，末条）：建卡 + 课次，挂链
  `bb-0190`/`bb-0213`/`bb-0174`（判据套错同源）。Jason 后作答 C/c/B → **3/3 升 ✅**，
  **插单 4 条全部清条**，下一课回主线部 II。
- 全部落盘经 `curriculum.py --verify` → 0 error。进度：已讲 14/108，已掌握 14。

### B. 出卷去重 + 扩量（引擎修复）
- **痛点**：9 日卷 vs 10 日卷重合 70%（cron 08:00 出卷时前一天卷未判分，12 题仍为 `state=new` 被新题池重抽）。
- **修复**（`D:\SixSigmaBlackBelt\src\practice.py`）：
  1. 新增 `--recent-gap N`（默认 3 天）近期去重窗口，读 `.keys/` 近 N 天题排除；
  2. 每日题量 `7+3` → `10+12`（基准 22，自适应封顶 30）；
  3. 顺手修加练卷 key（`-加练.txt`）漏判，改为 glob 全 key。
- **验证**：模拟 10-11 卷与 9/10 日卷 **0 重合**，实发 24 题。
- 成绩：9 日 75%、10 日 80%（cron 自动结算）。
- 变更记录：`D:\SixSigmaBlackBelt\docs\变更记录\2026-10-10-出卷去重与扩量.md`

### C. 跨项目 OS 设计讨论（本分支核心）
- 网络调研 5 类案例：FSRS/py-fsrs、Anki 三层、Quanta 引擎抽取、Monorepo、Prompt-as-Code。
- **盘点真实代码（消除假设）**：
  - vocab-app `src/` 与 bb-prep `src/` **结构同源**（`review.py≈bbcore.py`、`settle.py`、`practice.py`）。
  - ⚠️ **勘误**：早期误称「LADDER 逐字节相同」——实测 **不同**：
    bb-prep `[1,2,4,7,14,28,45]` @ `bbcore.py:28` vs vocab-app `[1,2,4,7,15,30,60,120]` @ `review.py:25`。
    状态机 *逻辑* 同源（`next_schedule` @ vocab `review.py:191`、bb `apply_result` @ `bbcore.py:430`）。
  - AI-KONGZHI `LearningOS` 的 Core Engine 明确「待实现」（绿地，可直接 adopt，零重构风险）。
- **FSRS 解释 + 专业判断**：FSRS 用每卡「稳定性 S + 难度 D」建模，比 LADDER 省 30–40% 复习量。
  **推荐起步不入核**（铁律「判分纯代码不能误伤」+ LADDER 已跑通 + FSRS 需历史冷启动）；
  内核先固化 LADDER 实现、`next_schedule` 留可插拔接口，FSRS 作 P2 后端。
- **两项分叉拍板**：
  - 资产形态 = **A+**（零外部依赖的 `learn_engine` Python 包 + semver 钉版本 + submodule 钉 commit + 交付整包拷贝）；
  - 内核边界 = **6 项共享 + LADDER 注入实现 + FSRS 留接口**。
- 把「专业决策须带分析 + 推荐」写入用户长期记忆。
- P0 手册落盘：`D:\Projects\LESSON-OS\PLAYBOOK.md`（SSOT schema + 版本闸门 + ADR 模板 + 路线图）。

---

## 二、当前状态（各项目）

| 项目 | 路径 | 状态 |
|---|---|---|
| bb-prep | `D:\SixSigmaBlackBelt\` | 14/108 课，引擎已去重扩量；`src/` 含可抽内核 |
| vocab-app | `D:\Projects\vocab-app\` | 已跑，引擎近同源，LADDER 不同（注入参数） |
| AI-KONGZHI | `D:\Projects\Project AI Kongzi\` | 绿地，Core Engine 待实现 |
| **LESSON-OS（本工作区）** | `D:\projects\LESSON-OS\` | P0 完成；`learn_engine` 骨架就位（占位待实装） |

---

## 三、下一步（交接给下一 agent）

1. **P1（抽代码，有重构风险，先小范围验证）**：把 `learn_engine/` 的 `NotImplementedError`
   占位落成真实实现（scheduler/vault 已可直写；grader/picker 接 bb-prep adapter），
   让 bb-prep 经 `import learn_engine` 继续跑、行为零中断。详见
   `D:\projects\LESSON-OS\Project Audit\v0.1.0_工作路径图与计划_R1_方案_tbd_LessonOS.md`。
2. **P2**：vocab-app / AI-KONGZHI 接入内核；把「教学判断与审美」沉淀为版本化 tutor 技能库。
3. **FSRS（P2 候选）**：在 `next_schedule` 接口下替换 LADDER，单独评估、单独升版本。
4. **改内核铁律**：bump `__version__` → 写 `Project Audit/` 方案+审计 → 归档 → 再编码（audit-os 硬闸门）。

---

## 四、关键约束（不要违反）

- **判分纯代码、模型不参与**（bb-prep AGENTS.md 铁律 6；vocab-app 同构）。
- **数字必须实测**，不许凭印象写进文档。
- **改动前先读受影响模块的调用者**（Karpathy R8）。
- **不要大爆炸重构**：内核抽离须原地 import、行为不变。
- **LADDER 注入，绝不硬编码**进内核（ADR-0001）。

---

## 五、Suggested Skills（下一 agent 应调用的技能）

- **`audit-os`** —— 任何内核方案/架构评审都走此工作流（方案_tbd → 审计_tbA → 终版_OK → 归档）。
- **`handoff`** —— 本轮结束再交接时用（本文件即范例）。
- **bb-prep 上下文**：读取 `D:\SixSigmaBlackBelt\AGENTS.md` 与 `.workbuddy/memory/MEMORY.md`
  （铁律索引）再动 `src/`。
- **vocab-app 上下文**：读取 `D:\Projects\vocab-app\AGENTS.md` / `CONTEXT.md` 再动其 `src/`。

---

## 六、引用产物（路径）

- 工作区：`D:\projects\LESSON-OS\`（README / PLAYBOOK / HANDOFF / learn_engine / ADR / Project Audit）
- bb-prep 变更记录：`D:\SixSigmaBlackBelt\docs\变更记录\2026-10-10-出卷去重与扩量.md`
- bb-prep 课次：`D:\SixSigmaBlackBelt\02-学习资料\学习计划\课次\2026-10-09-L13-...` / `...-L14-...`
- bb-prep 笔记：`D:\SixSigmaBlackBelt\02-学习资料\笔记\D6-分析\VI.B.13-非参数检验.md` /
  `VI.B.9-均值方差和比率检验.md`
- 内核参考源码：bb-prep `src/bbcore.py` `src/practice.py` `src/settle.py`；
  vocab-app `src/review.py` `src/settle.py` `src/practice.py`
