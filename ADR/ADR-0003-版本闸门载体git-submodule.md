# ADR-0003 · 版本闸门载体：git + submodule（非 vendor 副本）

- **状态**：已采纳
- **日期**：2026-10-10
- **决策人**：Jason + agent（LESSON-OS 分支）
- **背景**：盘点发现版本闸门**当前没有载体** —— 4 个路径里 3 个不是 git 仓库：

  | 路径 | git 状态 |
  |---|---|
  | `D:\SixSigmaBlackBelt`（bb-prep） | ✅ git，但 `remote -v` 为空（无远端） |
  | `D:\Projects\vocab-app` | ❌ 非 git |
  | `D:\Projects\Project AI Kongzi` | ❌ 非 git |
  | `D:\Projects\LESSON-OS` | ❌ 非 git |

  PLAYBOOK / README 反复写的「submodule 钉 commit」在多数路径上**根本装不上**。
  另有一处**我的误判需勘误**：我曾认为"引入 git 会破坏独立交付"，从而反对 git。

- **决策**：
  1. **4 个仓库全部 `git init`**（顺序：LESSON-OS → bb-prep → vocab-app → AI-Kongzi）；
  2. 消费项目以 **`git submodule`** 指向 LESSON-OS，**用 commit 当版本锚点**；
  3. `maturity` 与版本语义按 `PLAYBOOK.md` §11.5。

- **理由**：
  - 🔴 **勘误**：Jason 澄清 ——「独立交付」= **交付物与项目库隔离**
    （交付物干净、可独立运行），**不代表项目库要作为交付物整体拷贝**。
    故 git 进项目库**根本不碰交付物**，我原先的反对理由**是伪命题，作废**；
  - submodule 只存一个 commit 指针 → 符合 SSOT、避免文件重复的偏好；
  - vendor 会在 3 个消费仓库各留一份副本 = **3 份拷贝，迟早漂移**
    （正是本项目要消灭的病症）；
  - git init 顺序必须**内核在先**，否则消费项目无版本可钉。

- **影响**：
  - 正向：版本闸门有了真载体；精确复现成为可能；MAJOR bump 可追溯到消费方；
  - 代价：4 个仓库需各自维护；submodule 的 `.git` 文件若被同步盘（坚果云）扫描
    可能被污染 → **需在 `.gitignore` / 同步规则中排除**；
  - 🟡 **未解决风险**：4 个仓库目前**全无远端** → 单一真源只躺一块硬盘。
    "本地 bare 仓库"是伪备份（同盘挂一起没），需私有远端，退而 `git bundle` 单文件。
    **P1-C1 完成后必须解决，不可拖。**
  - 受影响文件：各仓库 `.git/`、`.gitmodules`、`.gitignore`

- **备选方案**：
  - 方案 A：**`vendor/` 钉副本** —— 否决：3 份拷贝必然漂移（见上），
    与 SSOT 目标直接冲突；
  - 方案 B：**`git subtree`** —— 否决：副本仍合进消费仓库，
    同样引入重复；且历史合并使回滚变复杂；
  - 方案 C：**不引 git，只用文件内 `__version__` 字符串** —— 否决：
    失去精确复现锚点（同版本号下代码可不同），且 Jason 已明确 Q5=A；
  - 方案 D：**只给 LESSON-OS 建 git** —— 否决：消费项目无 git 则无法 submodule。

- **后续**：Q8 备份策略待落地（私有远端 / bundle）；见 Backlog P1-C。
