# ADR-0001 · LADDER 作为注入参数而非内核常量

- **状态**：已采纳
- **日期**：2026-10-10
- **决策人**：Jason + agent（LESSON-OS 分支）
- **背景**：核对真实源码发现 bb-prep 与 vocab-app 的间隔阶梯**并非逐字节相同**
  （早期对话误称「逐字节相同」，已勘误）：

  | 项目 | LADDER | 封顶 | 证据 |
  |---|---|---|---|
  | bb-prep | `[1, 2, 4, 7, 14, 28, 45]` | 45 天 | `D:\SixSigmaBlackBelt\src\bbcore.py:28` |
  | vocab-app | `[1, 2, 4, 7, 15, 30, 60, 120]` | 120 天 | `D:\Projects\vocab-app\src\review.py:25` |

  但两者的**状态机逻辑同源**（bb `apply_result` @ `bbcore.py:430` ≈ vocab
  `next_schedule` @ `review.py:191`）。差异源于项目目标不同：考试死线（2027-06）vs 长期语汇积累。

- **决策**：`learn_engine.scheduler` 的 `next_schedule` / `apply_result` 一律接收
  `ladder` 参数（默认 `None` → 取 `DEFAULT_LADDER`）；内核只提供 `DEFAULT_LADDER`
  = bb-prep 阶梯，`MASTER_STAGE = len(ladder) - 1` 随注入值变化。
- **理由**：
  - R2 简洁 + 不把项目参数塞进共享内核；
  - 逻辑同源、仅间隔长度因项目而异 → 注入即可共享逻辑，无需共享常量；
  - 与版本闸门自洽：vocab-app 传自己的 ladder，内核升级不动它的复习节奏。
- **影响**：
  - 正向：一份状态机服务两种节奏；消费方显式声明自己的节奏；
  - 负向 / 代价：每个消费方多一个参数的认知负担；`MASTER_STAGE` 不再是全局常量；
  - 受影响文件：`learn_engine/scheduler.py`、`learn_engine/model.py`、`PLAYBOOK.md` §0/§9。

- **备选方案**：
  - 方案 A：**硬编码单一 LADDER** —— 否决：会强制 vocab-app 改复习节奏，违背版本闸门；
  - 方案 B：**内核内按项目名分支** —— 否决：把项目耦合写进内核，违背共享边界。

- **后续**：FSRS 后端（P2 候选）在同一 `next_schedule` 签名下替换实现，
  单独评估、单独升版本（见 `PLAYBOOK.md` §10）。
