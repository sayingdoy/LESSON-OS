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

- **后续**：Q8 备份策略**已于 2026-10-10 闭环**（见下「备份闭环」）。

---

## 备份闭环（2026-10-10 完成）✅

**远端载体 = 自建裸库（阿里云 ECS）**，四个仓库全部推送完成：

| 本地仓库 | 远端 | 体积 | 提交数 |
|---|---|---|---|
| `D:\Projects\LESSON-OS` | `ecs:/srv/git/LESSON-OS.git` | 400K | 2 |
| `D:\SixSigmaBlackBelt` | `ecs:/srv/git/SixSigmaBlackBelt.git` | 122M | 44 |
| `D:\Projects\vocab-app` | `ecs:/srv/git/vocab-app.git` | 280K | 1 |
| `D:\Projects\Project AI Kongzi` | `ecs:/srv/git/Project-AI-Kongzi.git` | 9.9M | 1 |

**关键收尾：submodule URL 必须改指远端**（这是本次发现的隐藏缺陷）
- 原 `.gitmodules` 的 url = `D:/Projects/LESSON-OS` —— **本机绝对路径**，
  换机 / 换目录即失效，等于没有版本锚点。
- 已改为 `ecs:/srv/git/LESSON-OS.git`（bb-prep commit `cb28793`），并 `git submodule sync`。
- **验证**：从远端全新克隆 LESSON-OS → 20 文件、`__version__ = "0.1.0"` ✅；
  在 ECS 本地克隆 bb-prep → 44 提交、`.gitmodules` 指向远端 ✅。

**日常同步**：`bash D:\Projects\LESSON-OS\scripts\sync_all.sh`（`--dry` 只看不推）。

**恢复方式**：`git clone ecs:/srv/git/<name>.git`

> ⚠️ **残余风险（低于原「单点故障」）**：远在阿里云，但**无第三方托管**——
> ECS 实例本身挂了就没有第二份。若要彻底闭环，P2 可加 `git bundle` 定期导出到网盘。
> 当前状态已从 🔴「只躺一块硬盘」降为 🟡「异地单点」。

---

## 执行记录（2026-10-10 完成）

| 仓库 | 分支 | 首次/相关提交 |
|---|---|---|
| `D:\Projects\LESSON-OS` | `main` | `620a334` init v0.1.0 (planned) |
| `D:\SixSigmaBlackBelt` | `master` | `d146401` 钉 submodule |
| `D:\Projects\vocab-app` | `main` | `fa772c5` init |
| `D:\Projects\Project AI Kongzi` | `main` | `27c72de` init |

**submodule 落地**：bb-prep `.gitmodules` → `vendor/LESSON-OS` @ `620a334`；
已验证 `import learn_engine` 返回 `__version__ = 0.1.0`。

**关键落地细节（同步盘防污染）**：
- 三个仓库的 `.gitignore` 均排除 **`.git/`** —— 这些目录被坚果云 / Obsidian 同步，
  而 submodule 的 `.git` 是**文件**（`gitdir: ../../.git/modules/vendor/LESSON-OS`）
  不是目录，同步盘搬运会污染。
- vocab-app 额外排除 `交付成果/` / `.keys/` / `.voided/`（交付物与密钥必须隔离）。
- AI-Kongzi 额外排除 `.obsidian/plugins/` / `themes/`（vendored 第三方二进制，同 bb-prep 惯例）。

> ⚠️ **本 ADR 的「未解决风险」条依然成立**：4 仓库无远端 = 单点故障，未闭环。
