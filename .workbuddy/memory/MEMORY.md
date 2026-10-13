# LESSON-OS 项目级长期记忆

## 目录/架构约定
- **Project Audit 文件命名**：`<版本>_<轮次主题>_<类型>_tbd/tbA_<项目>.md`；类型只有四类
  （`方案` / `审计` / `异议` / `终版`）——**不得新造类型名**（如"建议"）。
- **归档语义**：`Project Audit/` 根目录**只放进行中轮次**；已终版轮次全套移入 `Archive/`。
- **ADR**：`ADR/` 目录，一决策一文件；`ADR-template.md` 是唯一模板（**禁止内联副本**）。
- ADR 引用编号必须**有实体文件**（曾出现 0006/0008 无实体、0001 只作内联示例）。
- 🔴 **ADR 编号是「跨项目共享空间」，不是本地序号** —— `0006`/`0008` 实际定于
  2026-10-06/07（bb-prep 侧），10-11 才补档进本仓 → **编号沿用不重排**。
  空洞号 `0005`/`0007`（全库零引用零实体）**保留、不回收**（回收会造成「同号异义」）。
  新 ADR 取**当前最大号 + 1**（现 `0009`），索引在 `ADR/README.md`。
- **`CHANGELOG.md`** = 内核 bump 的人读记录（0.1.0→0.5.0，含 BREAKING 标记 + 消费方对照表）。

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

## 依赖与消费关系（2026-10-13 起）
- **依赖方向固定**：消费方 → `bbcore` → `learn_engine`。**内核不得反向依赖任何项目**
  （内核不读项目文件；项目数据一律**显式注入**形参 —— 裁决 B2）。
- **bb-prep 已接入**（首个真实消费方）：`vendor/LESSON-OS` 为 git submodule（钉 commit），
  入口在 `src/bbcore.py` 顶部（`_KERNEL_DIR` 按 `__file__` 解析、**不用 BB_ROOT**）。
  `practice.pick_items` → `picker.WeightedPicker`；`bbcore.apply_result` → `scheduler`。
  **判分**（2026-10-13 P1-B3）：`bbcore.judge` → `grader` 四原语，**策略全注入**。
  → `maturity: implemented`（消费方 1 个 < 2）；**B-1「无真实消费方」已解除**。
  **消费面已是 3 处**：选题 / 阶梯 / 判分。
- **A3 补位分支裁决 ②**：内核按 `state` 路由回 review/fresh、真源一律并入 fresh ——
  **内核不改**，补位留 `practice.main()`（池充足时差异不触发）。
- 🔴 **陷阱：任何路径换算函数不得依赖 CWD**（`Path(p).resolve()` 是错的；用 `(ROOT / p)`）。
  这类缺陷只在"临时副本 / CWD≠ROOT"时暴露 —— selftest 因此红了很久。

## 已定技术决策（摘要）
- LADDER **作注入参数**（bb-prep `[1,2,4,7,14,28,45]` ≠ vocab `[1,2,4,7,15,30,60,120]`），ADR-0001。
- 内核判分**返回字符串** `"correct"`/`"wrong"`（对齐双源，内核 bool 是孤例）。
- `new` 是 **pool 分流哨兵**，**不入** `model.STATES`（状态机不接受 `new` 输入）。
- 验收门槛必须**固定 rng 种子**（bb-prep 有 `--seed`），列为第 0 步。
- 版本闸门载体 = git submodule（非 vendor），ADR-0003；MAJOR 须人工确认。
- 内核边界：scheduler/vault/model 共享；grader/picker 走 adapter；FSRS 留接口不入核。

## 版本管理（**bump 三处同步**，缺一即漂移）
1. `learn_engine/__init__.py` 的 `__version__`（**唯一真源**，现 `0.5.0`）
2. `PLAYBOOK.md` frontmatter `version`（注册表 `build_registry.py` 读它）
3. `CHANGELOG.md` 补一条（谁在何时、为何 bump）

> 实测踩过：内核已 0.3.0，PLAYBOOK 仍写 0.2.0 → 注册表**静默记旧值**。
> 生成器已带漂移检测（frontmatter ≠ `__version__` 时**只报不改**，符合 G5）。

## 🔴 教训（2026-10-13 新增）
- **数字必须实测，不许凭印象**：0.5.0 的 golden-set 各方都写「46 项」，实跑 **47**。
  `948b419` 的 commit message 就是错的。核实法：`grep -c "def test_"` +
  `unittest` 实跑**双向对照**。各版本实测：0.2.0=13 / 0.3.0=16 / 0.4.0=25 / 0.5.0=47。
- **生成器只扫 `PLAYBOOK.md`**（`DOC_CANDIDATES` 取第一个命中）→ `AGENTS.md` /
  `README.md` 的**版本与状态引用无机械检查**，可静默落后 4 个版本（实况：
  `AGENTS.md` 停在 `0.1.0` + `planned`，而它是 agent 的**执行宪法**→ 误判代价最高）。
  技术债 **B7**：扩扫描范围，或立「版本只在 PLAYBOOK frontmatter 出现一次、
  其余文档只链接不写值」的 SSOT 规则。**改内核后要人工复扫这三份文档。**
- **历史快照文档（`HANDOFF.md`）不篡改历史** —— 加**时效声明**指向最新状态即可。
