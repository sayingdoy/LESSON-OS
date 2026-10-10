# LESSON-OS 项目级长期记忆

## 目录/架构约定
- **Project Audit 文件命名**：`<版本>_<轮次主题>_<类型>_tbd/tbA_<项目>.md`；类型只有四类
  （`方案` / `审计` / `异议` / `终版`）——**不得新造类型名**（如"建议"）。
- **归档语义**：`Project Audit/` 根目录**只放进行中轮次**；已终版轮次全套移入 `Archive/`。
- **ADR**：`ADR/` 目录，一决策一文件；`ADR-template.md` 是唯一模板（**禁止内联副本**）。
- ADR 引用编号必须**有实体文件**（曾出现 0006/0008 无实体、0001 只作内联示例）。

## 🔴 血的教训（2026-10-11 事故，必须遵守）
**`git filter-repo` 的强制 checkout 会静默覆盖未提交的工作区改动。**
bb-prep `src/practice.py` 2026-10-10 的全部改动（`--recent-gap` 去重 + 扩量 10+12
+ glob key 修复）在 2026-10-11 00:39 被本 agent 的 filter-repo 清空，**无法恢复**
（改动从未 commit；`src/` 又被 `.nutignore` 排除，坚果云也无副本）。
**这是同一坑的第二次踩**（第一次删了 17 个 PDF，靠 `.git` + bundle 救回）。

**强制操作规程**（执行任何历史重写 / 强制 checkout / `git reset --hard` 前）：
1. 先 `git status --porcelain` **逐文件列全部未提交改动**，交 Owner 确认后才动手；
2. `git bundle create <name>.bundle --all` 备份并**验证可解**，**当轮不清理**；
3. 操作后**逐文件**验证工作区（不只看目标文件）。

## 已定技术决策（摘要）
- LADDER **作注入参数**（bb-prep `[1,2,4,7,14,28,45]` ≠ vocab `[1,2,4,7,15,30,60,120]`），ADR-0001。
- 内核判分**返回字符串** `"correct"`/`"wrong"`（对齐双源，内核 bool 是孤例）。
- `new` 是 **pool 分流哨兵**，**不入** `model.STATES`（状态机不接受 `new` 输入）。
- 验收门槛必须**固定 rng 种子**（bb-prep 有 `--seed`），列为第 0 步。
- 版本闸门载体 = git submodule（非 vendor），ADR-0003；MAJOR 须人工确认。
- 内核边界：scheduler/vault/model 共享；grader/picker 走 adapter；FSRS 留接口不入核。
