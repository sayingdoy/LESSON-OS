# Project Audit · 审计日志（LESSON-OS）

> 所有审计轮次决策链记录。每轮终版归档后追加一行。

---

## 2026-10-10 · v0.1.0 工作路径图与计划（R1）

- **主题**：跨项目共享学习内核的架构（工作路径图）+ 下一步计划（P0/P1/P2）
- **执行方**：agent（LESSON-OS 分支）
- **审核方**：agent（同决策者简化审计，audit-os §6.5）
- **轮次文件**：
  - `v0.1.0_工作路径图与计划_R1_方案_tbd_LessonOS.md`
  - `v0.1.0_工作路径图与计划_R1_审计_tbA_LessonOS.md`
- **Verdict**：🟡 有条件通过（1 处 🟡 事实勘误：LADDER 非逐字节相同，已据真实源码核对，
  内核设计已自愈为「LADDER 注入参数」ADR-0001）
- **决策**：采纳方案。P1 抽代码时显式勘误 PLAYBOOK/HANDOFF；内核边界与版本闸门不变。
- **事实核对**：全部主张已对照 bb-prep `src/bbcore.py`、vocab-app `src/review.py` 实测。
- **状态**：✅ 已归档（**校正 2026-10-11**：归档动作实际在 2026-10-11 补做——独立重审 A1 发现当时并无
  `Archive/` 目录，记录早于事实。见文末「R1 独立重审」节）

### R1 收尾补充（2026-10-10）

R1 的 1 处 🟡 待修项（LADDER 非逐字节相同）**已于本轮闭环**：

| 项 | 处置 |
|---|---|
| PLAYBOOK §0 表格 + §9 | 已改真实 LADDER，并加「勘误（2026-10-10）」引用块 |
| 「零依赖**单文件**」措辞 | 已全库改为「零**外部**依赖的 Python 包」（README / PLAYBOOK / HANDOFF） |

**VCP 步骤 3 产出（本轮新增）**：
- `AGENTS.md` —— 执行宪法（五条铁律 + 目录地图 + 干活前必查）
- `PLAYBOOK.md` §10 —— 飞轮触发协议（SSOT 正文）
- `PLAYBOOK.md` §11 —— 标准库注册规范（SSOT 正文）
- `MVP-Backlog.md` —— P1 切成三片垂直切片（A 排期 / B 判分 / C 版本锚点）
- `ADR-0002` —— golden-set 逐字节比对验收法
- `ADR-0003` —— 版本闸门载体 = git + submodule（含我对 git 的误判勘误）
- `ADR-0004` —— 归因闸门候选用 JEV `noul`（状态：**未测，不得启用**）

**旁路产出（标准库体系）**：
- `D:\Projects\lib-index\` —— `REGISTRY.md`（生成物）+ `build_registry.py`（只读扫描器）
- `jev-gate` 补 `__version__ = "0.1.0"` → 入库（`maturity: adopted`）
- `LESSON-OS` 入库（`maturity: planned` —— 尚无真实消费方）

---

## 决策链摘要（跨会话）

| 日期 | 决策 | 依据 |
|------|------|------|
| 2026-10-10 | 资产形态 = A+（stdlib 单文件 + semver + submodule/vendor + 整文件交付） | 满足复用/版本闸门/独立交付三需求 |
| 2026-10-10 | 内核边界 = 6 项共享 + LADDER 注入 + FSRS 留接口 | 真实源码核对 + 铁律「判分纯代码不能误伤」 |
| 2026-10-10 | LADDER 作注入参数（ADR-0001） | bb-prep/vocab-app LADDER 实测不同 |
| 2026-10-10 | FSRS 暂不入核 | 冷启动条件不成熟 + 风险隔离 |
| 2026-10-10 | 版本闸门载体 = git + submodule（ADR-0003） | Jason 澄清「独立交付」含义，原 vendor 方案作废 |
| 2026-10-10 | golden-set 逐字节比对为验收法（ADR-0002） | JEV §8 预登记纪律迁移，可机械化判据 |
| 2026-10-10 | 归因闸门 JEV `noul` 暂不启用（ADR-0004） | 阈值未测 + 样本不足（n<16） |
| 2026-10-10 | 标准库三门槛 + 双轨注册（PLAYBOOK §11） | 防双 SSOT + 信噪比过滤 |
| 2026-10-11 | **B1 `judge` 返回类型 = `str`**（`"correct"`/`"wrong"`） | 双源 100% 一致（`bbcore.py:401`/`review.py:137`），内核 bool 是孤例；`settle.py:154` 证明字符串是有意设计 |
| 2026-10-11 | **B2 `pick` 改显式注入**（`recent`/`history_counts`/`domain_weights`/`is_exam`） | 消除 `getattr` 与恒空 `{}` 的"假能力"；去重/权重曾空转 |
| 2026-10-11 | **B3 验收第 0 步 = 固定 `rng`**（`FIXED_SEED=20261010`） | 不固定则逐字节比对不成立；bb-prep 早有 `--seed` 钩子 |
| 2026-10-11 | **B4 `new` 是 pool 哨兵，不入 `STATES`**；新增 `POOL_NEW` 常量 | `new` 是 `setdefault` 默认值，非 SRS 状态；入 STATES 会模糊状态机输入域 |
| 2026-10-11 | **B5 内核引用改真源**（`docs/契约/引擎与数据.md`） | "铁律 21" 全库零命中；按错误编号核对会得相反结论 |
| 2026-10-11 | **C1余 补 `ADR-0006`/`0008` 实体** | 引用密度高，留档比外链稳 |
| 2026-10-11 | **A3余 PLAYBOOK §6 改 `ADR/` 目录约定** | 原"单文件 `adr.md`"与仓库实际冲突（R7） |

---

## 2026-10-11 · R1 独立重审（Owner 指派同一 agent 的授权例外）

- **主题**：v0.1.0 工作路径图与计划 — Round 1 **独立重审**（取代 2026-10-10 同决策者简化版）
- **审计方**：Hermes（Owner 明确指派；独立性披露写在报告首部——**非异构独立审核**）
- **Verdict**：🟡 有条件通过（方案本体通过；执行层 🔴 P0 ×1）
- **报告**：`v0.1.0_工作路径图与计划_R1_审计_tbA_Hermes.md`
- **简化格式效力被量化**：旧自审只报 1 项实质问题；独立重审新增 **11 项**（合计 13 项）

### 本轮发现（13 项，详见报告）

| 组 | 项 | 严重度 |
|---|:---:|:---:|
| A 闭环治理 | A1 R1 未真正归档 + `audit_log` 记录早于事实 | 🔴 P0（已处置） |
| A 闭环治理 | A2 `ADR-0003`/`MVP-Backlog` 未提交、`scripts/sync_all.sh` 未跟踪 | 🟡 P2（**Owner 自行提交 `32bdc58` 闭环**） |
| A 闭环治理 | A3 README 文件树过期 + PLAYBOOK §6 的 ADR 约定与仓库冲突 | 🟡 P2（README 已修；§6 待裁） |
| A 闭环治理 | A4 工作日志「4 仓库无远端」未回写（ADR-0003 已闭环） | 🟢 P3（已处置） |
| A 闭环治理 | A5 审计窗口内存在并发写入者（非本会话提交 `32bdc58`/`6820843`）→ 无锁、快照会漂移 | 🟡 P2（登记为环境事实） |
| B 契约一致性 | B1 `judge` 返回类型四方不一致（SSOT 字符串 / 方案+实现 bool / 真源字符串） | 🟠 P1 **待裁决** |
| B 契约一致性 | B2 `pick` 丢 `recent`/`exam_first`/九域统计三个注入点（去重与权重当前空转） | 🟠 P1 **待裁决** |
| B 契约一致性 | B3 ADR-0002 验收判据未固定 `rng`（bb-prep 实有 `--seed`） | 🟠 P1 **待裁决** |
| B 契约一致性 | B4 `model.STATES` 缺 `new`（SSOT 与 picker 均按 `new` 分池） | 🟠 P1 **待裁决** |
| B 契约一致性 | B5 引「bb-prep AGENTS.md 铁律 6 / 铁律 21」编号不实 | 🟠 P1 **待裁决** |
| B 契约一致性 | B6 内核内四份同源日期解析（picker「避免循环依赖」理由不成立） | 🟡 P2 |
| B 契约一致性 | B7 方案 §一 数据流「write_front 注入 writer」与实现不符 | 🟡 P2 |
| B 契约一致性 | B8 P1 未声明目标版本号（新增导出符号 → MINOR） | 🟡 P2 |
| C 证据链 | C1 `ADR-0001`/`0006`/`0008` 无实体文件 | 🟡 P2（0001 已补） |

### Owner 授权收尾（执行方动作，2026-10-11）

| 对应 | 动作 |
|---|---|
| A1 | 建 `Project Audit/Archive/`，R1 全套（方案 + 旧审计 + 新审计）移入 |
| C1 | 补 `ADR/ADR-0001-LADDER作注入参数.md` 实体文件；`ADR-template.md` 删除内联副本（防双 SSOT） |
| A3 | README §七 文件树按实际补齐（ADR 全量 / `scripts/` / `Archive/`） |
| A2 | 提交 `ADR-0003`、`MVP-Backlog.md`、新增 `scripts/` |

### P1 前置待裁决项（Owner 裁决后方可进入 P1 编码）

| # | 待裁决 | 为何必须先裁（PLAYBOOK §11.5） |
|:---:|---|---|
| B1 | `judge` 契约取字符串还是 bool | 改签名 = MAJOR，动消费方 |
| B2 | `pick` 是否把 `recent`/`exam_first`/九域统计改为显式注入参数 | 改签名 = MAJOR；不裁则 P1-A 会静默丢掉 bb-prep 刚修的近期去重 |
| B3 | ADR-0002 是否补「固定 rng 种子」为验收前提 | 改验收判据 = MAJOR；不裁则 P1-A 通过门槛不可复现 |
| B4 | `new` 是否进 `model.STATES` | 改 schema 语义 = MAJOR |
| B5 | 内核引用是否改用真源位置（`docs/契约/引擎与数据.md`） | 证据链正确性 |
| C1 余 | `ADR-0006`/`0008` 补实体文件或改引用 | 决策链可解析率 |
| A3 余 | PLAYBOOK §6「单文件 `adr.md`」改为 `ADR/` 目录约定 | R7 模式冲突消解 |

---

## 2026-10-11 · R1 待裁决项全部裁决并落地（内核 → `0.2.0`）

- **裁决方**：Jason（Owner），指示「七项裁决，开始」
- **执行方**：agent（workbuddy）
- **建议依据**：`v0.1.0_工作路径图与计划_R1_待裁决项_建议_tbd_LessonOS.md`（Planner 实测）
  + `..._审计_tbA_Hermes.md`（Auditor 复核，6/7 成立）
- **Verdict**：✅ **全部 7 项已落地并验收**

### 落地清单

| # | 裁决结果 | 落地动作 | 验收 |
|:---:|---|---|:---:|
| B1 | 取 `str` | `grader.py` 基类 + `ExactMatchGrader` 返回 `"correct"`/`"wrong"` | ✅ 单测 |
| B2 | 显式注入 | `picker.py` 重写：消除 `getattr`/恒空 `{}`；签名含 `recent`/`history_counts`/`domain_weights`/`is_exam` | ✅ 权重/去重生效可测 |
| B3 | 补固定 rng | `ADR-0002` 加「验收第 0 步」+ `FIXED_SEED=20261010` | ✅ 写死 |
| B4 | 不入 `STATES` | `model.py` 加 `POOL_NEW`；`Item.state` 默认改 `POOL_NEW`（对齐双源 `setdefault`） | ✅ 单测 |
| B5 | 改真源 | 4 处（`grader.py`/`vault.py`/`HANDOFF.md`×2） | ✅ 全库零残留 |
| C1余 | 补实体 | 新增 `ADR-0006-密钥与判分隔离.md`、`ADR-0008-判分账本幂等.md` | ✅ 编号全可解析 |
| A3余 | 改目录约定 | `PLAYBOOK.md` §6 重写；删内联模板 | ✅ |

### 附带产出（B8 版本锚点 + P1-A1 工单）

- `learn_engine/tests/` + `golden_set.py`（**13 项断言全过**）：
  固定 `seed=20261010` / `today=2026-10-11`；断言含去重生效、权重生效、`judge` 返 str、
  `POOL_NEW∉STATES`、LADDER 注入、状态机边界。
- golden 基线存 `learn_engine/tests/golden_v0.2.0.json`。
- **版本 bump `0.1.0 → 0.2.0`**（新增导出符号 `POOL_NEW`/`STATES` = MINOR，对应 B8）。
- `MVP-Backlog` 更新：R1 修正标记完成；新增 **P1-A4**（补 picker 贪心+上限，B2 遗留）。

### 待办（进入 P1-A 前）

- P1-A4 是**新增必要条件**：内核 picker 与 bb-prep `pick_items` 输出要在同 seed 下一致，
  否则 A3 的「逐字节相同」判据必失败（真源的贪心+上限尚未移入）。
