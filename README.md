# LESSON-OS · 项目飞轮系统

> 跨项目共享的「学习 + 复习 + 错题复盘」内核。让 bb-prep / vocab-app / AI-KONGZHI
> 三个项目复用同一套**调度、出卷、判定、独立交付**逻辑，且核心更新不互相误伤。

**它是一个「飞轮」**：每修一处内核 bug / 优化一处判据，三个项目同时受益；
沉淀越久，复用复利越高。本仓库是飞轮的**单一真源种子**（P0 已完成，P1 待实现）。

---

## 一、这是什么 / 不是什么

| ✅ 是 | ❌ 不是 |
|---|---|
| 三个项目共享的**代码内核 + 提示/审美库 + 约定手册** | 一个具体备考/背词 App（那在各自仓库） |
| 零**外部**依赖、版本化、可整包导出的 `learn_engine` | 需要复杂框架/服务 |
| 通过 semver + submodule/vendor 做**版本闸门** | 复制粘贴各项目各留一份（会分叉） |

---

## 二、三层共享资产（喂给三个项目）

```
                 LESSON-OS 项目飞轮系统（共享学习内核）
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
  [代码内核]            [提示 / 审美库]          [约定手册]
  learn_engine          tutor 技能(版本化)       PLAYBOOK.md
  (stdlib · semver)     (教学契约/讲评风)        (SSOT schema / ADR)
        │                     │                     │
        └──────────┬──────────┘─────────────────────┘
                   ▼
        版本闸门：submodule 钉 commit / vendor 钉副本
                   │
   ┌───────────────┼────────────────┐
   ▼               ▼                ▼
 bb-prep        vocab-app       AI-KONGZHI
 (527题,已跑)    (已跑,近同源)   (绿地,待接)
   差异化内容：题面 / 答案形态 / 题型 / LADDER 参数
```

**关键结论（2026-10-10 对真实源码核对）**：
- 状态机 + `is_due` + frontmatter IO **逻辑同源** → 真共享。
- 但 **LADDER 不是逐字节相同**：bb-prep `[1,2,4,7,14,28,45]`、vocab-app `[1,2,4,7,15,30,60,120]`。
  → 内核把 LADDER 设计为**注入参数**，绝不硬编码。
- 判定（judge）与出卷（pick）**答案形态/抽题规则不同** → 设计为**项目 adapter**（策略模式），不塞进内核。

---

## 三、资产形态与版本闸门

- **形态** = 零**外部**依赖的 `learn_engine` **Python 包**（仅 Python 标准库） + semver 钉版本 + 各项目
  `git submodule` 钉 commit（见 ADR-0003）。
- **版本闸门**：`learn_engine/__init__.py` 的 `__version__ = "x.y.z"`。你改核心只 bump 号，其他项目**不主动升级就不受影响**
  → 治「核心更新误伤其他项目」。
- **独立交付**：内核纯 stdlib，交付时拷进 `交付成果/`（两项目早有「纯 md、整体复制」硬约束）。
  > 注：**交付物与项目库隔离** —— 交付物干净可独立运行，不代表项目库整体拷贝。

---

## 四、内核共享边界（终版，2026-10-10 拍板）

**6 项共享** + **LADDER 作注入参数实现** + **FSRS 留可插拔接口（暂不入核）**：

1. frontmatter 读写（SSOT 元数据模型）
2. SRS 调度：`is_due` + 状态机 `next_schedule`（LADDER 注入）
3. 判定契约：确定性、模型不参与（答案形态走 adapter）
4. 出卷：`到期优先 + 九域权重 + 近期去重窗口`（抽题规则走 adapter）
5. `.keys/<date>.txt` + `judged` 账本隔离（判分纯代码铁律）
6. 独立交付硬约束

> **FSRS 不入核的理由**（专业判断）：你铁律「判分纯代码、数字实测、不能误伤」；
> LADDER 已跑通且有 ADR；FSRS 需历史日志冷启动（vocab-app 未必够）。
> 内核先固化 LADDER 实现，`next_schedule` 留可插拔接口，FSRS 作 P2 可选后端。

---

## 五、任何 agent 如何接手并开发

1. **读 `PLAYBOOK.md`** —— 系统宪法、SSOT schema、API 契约、ADR 模板、路线图（单一真源）。
2. **读 `learn_engine/__init__.py`** —— 当前公开 API 与版本号，立即知道能 import 什么。
3. **读 `Project Audit/`** —— 所有架构/方案决策与审计报告（含本分支的「工作路径图 + 计划」审计）。
4. **P1 任务** = 把 `learn_engine/` 的 `NotImplementedError` 占位落成真实实现，并让 bb-prep
   经 `import learn_engine` 继续跑、行为零中断（见 `Project Audit/` 方案文件）。
5. **改内核必走**：bump `__version__` → 写 `Project Audit/` 方案+审计 → 归档 → 再编码（audit-os 硬闸门）。

**状态板**
| 项 | 状态 |
|---|---|
| P0 手册 + SSOT schema + 路线图 | ✅ 完成 |
| `learn_engine` 骨架（API 契约 + 共享逻辑 + adapter 接口） | ✅ 完成（占位待实现） |
| P1 抽代码：bb-prep `src/` → `learn_engine` 实装 | ⬜ 待启动 |
| P2 vocab-app / AI-KONGZHI 接入 + tutor 技能库 | ⬜ 待启动 |
| FSRS 后端 | ⬜ P2 候选 |

---

## 六、关联项目（真实路径）

- `D:\SixSigmaBlackBelt\` —— bb-prep（六西格玛备考，527 题，已跑）
- `D:\Projects\vocab-app\` —— 背单词 App（已跑，引擎近同源）
- `D:\Projects\Project AI Kongzi\` —— AI-KONGZHI（LearningOS，绿地待接）

## 七、本仓库文件

```
LESSON-OS/
├── README.md                 ← 你正在读（接手入口）
├── PLAYBOOK.md               ← SSOT：宪法 + schema + API + ADR + 路线图
├── HANDOFF.md                ← 本分支对话总结（handoff 格式，给下一 agent）
├── learn_engine/             ← 共享内核骨架（stdlib, semver）
│   ├── __init__.py           ← __version__ + 公开 API
│   ├── model.py              ← SSOT 元数据 Item + DEFAULT_LADDER(注入)
│   ├── scheduler.py          ← is_due + next_schedule(状态机) + apply_result
│   ├── vault.py              ← frontmatter 读写（stdlib regex）
│   ├── grader.py             ← 判定策略接口 + ExactMatchGrader(vocab 风格)
│   └── picker.py             ← 出卷策略接口 + WeightedPicker(bb 风格)
├── ADR/
│   └── ADR-template.md       ← 架构决策记录模板
└── Project Audit/            ← audit-os 审计（工作路径图 + 下一个计划）
    ├── audit_log.md
    ├── v0.1.0_工作路径图与计划_R1_方案_tbd_LessonOS.md
    └── v0.1.0_工作路径图与计划_R1_审计_tbA_LessonOS.md
```
