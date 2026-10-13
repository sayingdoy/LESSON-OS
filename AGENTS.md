# AGENTS.md — LESSON-OS 执行宪法

> 给在这个仓库里干活的 agent。**这一屏是全部必须立刻知道的东西**；
> 判据全文在 `PLAYBOOK.md`（领域 SSOT），本文件**只放指针，不复刻**。
>
> 建立 2026-10-10 | Owner: Jason | 版本 0.5.0

---

## 1. 这是什么

LESSON-OS 是 bb-prep / vocab-app / AI-Kongzi **共享的学习内核**：把
「学习 → 间隔复习 → 考试 → 错题复盘」闭环中**结构性同源**的部分，
抽成零外部依赖、semver 版本化的**单一真源**。

**不做**：不做具体 App（题面 / 答案形态 / 领域权重留在各项目）；
不做框架、服务、UI；**不引入 FSRS**（留可插拔接口，P2 候选）。

**当前状态**：`implemented`（2026-10-13 起）—— 骨架完整、测试通过，
**已有 1 个真实消费方**（bb-prep 经 `vendor/LESSON-OS` submodule 接入），
未达入库门槛①的 **≥2 项目**。
P1-A（排期）/ P1-B（判分）**已完成**，三处占位**全部实装**：
`vault.write_front`（0.4.0）/ `grader` adapter（0.5.0）/ `picker` adapter（0.3.0）。
版本变更史见 `CHANGELOG.md`。

---

## 2. 五条铁律（违反即停）

1. **先修项目，后沉淀内核** —— 绝不为等内核而阻塞生产。运行中发现问题，
   在项目 `SEDIMENT.md` 留一行标记，归因**推迟到阶段边界**（PLAYBOOK §10.2）。
2. **不改交付物** —— `src` 不得被交付物引用；交付物纯 Markdown 可整体复制；
   密钥 / 答案绝不进交付物。
3. **内核零外部依赖** —— 只用 Python 标准库。测试用 `unittest`，**不引 pytest**。
4. **判分纯代码、模型不参与** —— 见 PLAYBOOK §5。成绩单与实际作答矛盾时，
   **先怀疑判分器**，不要直接下「水平差」结论。
5. **MAJOR 变更必须人工确认** —— 改签名 / 改默认行为 / 改 frontmatter 语义 / 改阈值，
   都会动消费方，**agent 不得自主执行**。

---

## 3. 目录地图

```
learn_engine/          ← 内核（零外部依赖 Python 包）
  __init__.py          ← __version__ 在此
  model.py             ← Item + DEFAULT_LADDER + MASTER_STAGE
  scheduler.py         ← is_due / next_schedule / apply_result（纯函数状态机）
  vault.py             ← parse_front / as_date ✅ ；write_front ✅ 已实装（0.4.0）
  grader.py            ← Grader 接口 + 4 个判分原语 ✅（0.5.0，策略全注入）
  picker.py            ← Picker 接口 + WeightedPicker ✅（0.3.0 贪心 + 温和上限）
  tests/               ← golden-set（纯 stdlib unittest，**47 项**）—— P1 建立
PLAYBOOK.md            ← 领域 SSOT（schema / API 契约 / 触发协议 / 差异清单）
CHANGELOG.md           ← 内核版本变更记录（谁在何时、为何 bump）
ADR/                   ← 架构决策记录（索引见 `ADR/README.md`）
Project Audit/         ← R1 方案与审计归档
.workbuddy/memory/     ← 工作日志（append-only）
```

---

## 4. 干活前必查

| 场景 | 去读 |
|---|---|
| 改 API / 契约 | `PLAYBOOK.md` §4（API 契约）+ §5（判定铁律） |
| 碰到「这该不该抽进内核」 | `PLAYBOOK.md` §10（触发协议）+ §9（已知差异，**留在项目别抽**） |
| 新建 / 登记标准库 | `PLAYBOOK.md` §11 + `D:\Projects\LIBGOV\registry\REGISTRY.md` |
| 开新项目 | 必答：「本项目消费 LESSON-OS 吗？钉哪个版本？」（§10.1 入口 A） |
| bump 版本 | §11.5 语义表 |

---

## 5. 版本与发布

- 版本载体：`learn_engine/__init__.py` 的 `__version__`（当前 `0.5.0`）
- 变更记录：`CHANGELOG.md`（**bump 版本必须同步补一条**，否则生成器 / 消费方对不上）
- 语义：PATCH=改 bug 签名不变；MINOR=加带默认值参数 / 新导出符号；
  **MAJOR=改签名 / 改默认行为 / 改 frontmatter 语义 / 改阈值**
- 消费方钉版本：`git submodule` 指向本仓库（**commit 即版本锚点**）
- **金标准验收**：固定一批 items + 固定 `today`，改前 / 改后各跑一次出卷，
  **逐字节比对输出**（预登记通过门槛，见 §10.6）

---

## 6. 沉淀判据（一句话版）

> 先问：**「换到 vocab-app 会不会同样发生？」**
> 会 → 走 §10 闸门；不确定 → 留一行标记；不会 → 留在项目，
> 并在 ADR / 工单里**写明排除理由**。

**飞轮的成本非线性**：留标记（L1）几乎免费 → **宁滥勿缺地留**，
筛选发生在 L2 闸门。
