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
- **状态**：✅ 已归档 → 启动 P1（VCP 步骤 3 产出已就位，见下）

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
