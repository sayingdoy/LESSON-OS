# HANDOFF · P1 收尾与双远端

> **本文件路径**：`D:\Projects\LESSON-OS\HANDOFF-P1收尾与双远端.md`
> （写入**项目目录**而非系统临时目录 —— 本机有**多个 checkout tree**（五仓），
> 临时路径无法告知下一个 agent 文件在哪；且临时目录会被清理。）
> **日期**：2026-10-13 17:48（取自系统时钟 `date`，非凭记忆）
> **承接**：`HANDOFF.md`（2026-10-10 的历史快照，顶部已加**时效声明**）之后的进展。
> **本对话主题**：① P1-B 判分委托内核 ② P1-C3 版本锚点收尾 ③ LIBGOV 建 GitHub 私有仓 + 双远端。

---

## 一、本对话做了什么（三项）

### ① P1-B：bb-prep 判分改为委托内核

**原则**：内核只给**机制**（4 个领域无关判分原语），消费方给**策略**
（中文分隔符 / 真值词表 / 字母范围 / 数值容差全部**显式注入**）——
对齐裁决 B2「内核不读项目文件，项目数据一律显式注入形参」。
按 `qtype` 的路由**留在 bb-prep 侧**（qtype 词表是项目策略，内核不认识）。

- 内核：`learn_engine/grader.py` 新增 `LetterSetGrader` / `TrueFalseGrader` /
  `NumericGrader` / `KeywordGrader`；版本 `0.4.0 → 0.5.0`（commit `948b419`）
- 消费方：`D:\SixSigmaBlackBelt\src\bbcore.py` 四个分支改委托；公开符号
  （`letters` / `judge_tf` / `judge`）**全部保留**，不破坏调用方
- 变更记录：`D:\SixSigmaBlackBelt\docs\变更记录\2026-10-13-判分委托内核.md`
- submodule 指针：`vendor/LESSON-OS` → `948b419`

**验收（预登记判据，全部在 submodule 0.5.0 实路径下重跑）**：

| 判据 | 结果 | 复现命令 |
|---|---|---|
| 88 条真实作答，改前/改后判定完全一致 | **0 差异** | bb-prep 侧一致性脚本 |
| 历史正确率复现 | 2026-10-05 = 60%、2026-10-06 = 70% | 同上 |
| 内核 golden-set | **47/47** | `python -m learn_engine.tests.golden_set` |
| `golden_v0.5.0.json` vs `0.4.0` | **逐字节一致** | `python -m learn_engine.tests.golden_set --dump \| diff - <基线>` |

> ⚠️ **数字勘误**：`948b419` 的 commit message 写「25 → 46 项」，**实为 47**。
> 双向核实法：`grep -c "def test_" learn_engine/tests/golden_set.py` 与
> `unittest` 实跑 `Ran 47 tests`。全仓已统一为 47。
> 各版本实测：**0.2.0=13 / 0.3.0=16 / 0.4.0=25 / 0.5.0=47**。

### ② P1-C3：版本锚点收尾（P1-C 全绿）

**新增**：
- `CHANGELOG.md` —— 0.1.0→0.5.0 逐版本 bump 记录（BREAKING 标记 + 版本×消费方对照表）
- `ADR/README.md` —— ADR 索引 + 引用自查命令

**修复 3 份陈旧文档**（都指向过时状态，agent 读了会误判）：
`AGENTS.md`（**最严重**：停在 `0.1.0` + `planned`，而它是**执行宪法**）、
`README.md`、`PLAYBOOK.md`；另 `HANDOFF.md` 加时效声明、`MVP-Backlog.md` 状态更新。

**两个实质发现**：
1. **ADR 编号是跨项目共享空间，不是本地序号** —— `0006`/`0008` 实际定于
   2026-10-06/07（bb-prep 侧），10-11 才补档进本仓。空洞号 `0005`/`0007`
   全库零引用零实体 → 定策**保留不回收**（回收会造成「同号异义」）。
   新 ADR 取**当前最大号 + 1**（现 `0009`）。
2. **根因：生成器只扫 `PLAYBOOK.md`** —— `build_registry.py` 的 `DOC_CANDIDATES`
   只取**第一个命中**的文档，`AGENTS.md` / `README.md` 的版本与状态引用
   **无任何机械检查** → 可静默落后 4 个版本。**已登记技术债 B7**。

### ③ LIBGOV 建 GitHub 私有仓 + `sync_all.sh` 双远端

- Owner 确认可见性后 `gh repo create sayingdoy/LIBGOV --private`，推送并设上游。
  核验命令：`gh repo view sayingdoy/LIBGOV --json visibility,isPrivate` → `PRIVATE / true`
- **`sync_all.sh` 改造**（`42f3215`）：原脚本**只推 `origin`、不推 `github`** ——
  正是它自己号称要防的「静默漂移」。顺带修两个真缺陷：
  - 🔴 `git push ... | head` 的退出码取自 `head`（**恒 0**）→ push 失败被静默吞掉
  - `ahead=0` 早退只看单一上游（`@{u}`）→ github 落后时被跳过
  - 改为对每个远端**幂等推送**；未配置的远端跳过

---

## 二、当前状态

### 仓库（五仓 × 双远端，落后 = 0）

| 仓 | 路径 | 分支 | HEAD | 双远端 |
|---|---|---|---|---|
| LESSON-OS（内核） | `D:\Projects\LESSON-OS` | `main` | `6e4ad22` | ✅ 双 |
| LIBGOV（治理层） | `D:\Projects\LIBGOV` | `main` | `253f80d` | ✅ 双（github **私有**） |
| bb-prep（消费方） | `D:\SixSigmaBlackBelt` | `master` | `7e7b270` | ✅ 双 |
| vocab-app | `D:\Projects\vocab-app` | `main` | — | ✅ 双（**待接入内核**） |
| Project AI Kongzi | `D:\Projects\Project AI Kongzi` | `main` | — | ✅ 双（有 **8 项未提交**，既存） |

- 远端：`origin` = `ecs:/srv/git/<name>.git`（异地主）；`github` = `github.com/sayingdoy/<name>`（**私有**，异地次）
- 一键同步：`bash D:\Projects\LESSON-OS\scripts\sync_all.sh`（`--dry` 只看不推）
- **ADR-0003 原登记的「ECS 单点」残余风险已消除**

### 内核

- `learn_engine` 版本 **`0.5.0`**，`maturity: implemented`（消费方 **1** 个 < 2）
- **消费面 3 处**：选题（`picker.WeightedPicker`）/ 阶梯（`scheduler.apply_result`）/ 判分（`grader` 四原语）

### 验收命令（可直接复跑）

```bash
cd D:/Projects/LESSON-OS
python -m learn_engine.tests.golden_set          # 期望 47/47 全过
python ../LIBGOV/registry/build_registry.py --check   # 期望退出码 0、无版本漂移
```

---

## 三、下一步（交接给下一 agent）

1. **B6** —— `picker` / `scheduler` / `vault` 内部**四份同源日期解析**收敛到一处（技术债）。
2. **B7** —— **版本引用机械检查**：把 `build_registry.py` 的扫描扩到
   `DOC_CANDIDATES` 全量，或立「版本只在 PLAYBOOK frontmatter 出现一次、
   其余文档只链接不写值」的 SSOT 规则。
   > **过渡期纪律**：**每次改内核后，人工复扫 `AGENTS.md` / `README.md` / `PLAYBOOK.md`。**
3. **P2** —— vocab-app / AI-Kongzi 接入 `learn_engine` → 门槛①达标（≥2）→
   `maturity: implemented → adopted`；并沉淀 `tutor-prompt-library` 技能库。
4. **待 Owner 复核** —— bb-prep `L15`（`II.A.1`，`judged: false`）**已开课未判**，
   当前**未计入**「已讲 = 14」。
5. **次要** —— `Project AI Kongzi` 有 8 项未提交（既存，非本对话产生，未擅自处理）。

---

## 四、关键约束（不要违反）

- 🔴 **10-11 铁律**：任何历史重写 / 强制 checkout / `reset --hard` 前，必须
  ① `git status --porcelain` **逐文件列全部未提交改动**交 Owner 确认；
  ② `git bundle create` 备份并**验证可解**，**当轮不清理**；③ 操作后**逐文件**验证。
  （背景：`git filter-repo` 曾静默清空从未 commit 的工作区改动，**永久丢失**。）
- 🔴 **判分纯代码、模型不参与**。成绩单与实际作答矛盾时，**先怀疑判分器**。
- 🔴 **内核不得反向依赖任何项目**；项目数据一律**显式注入**形参。
- 🔴 **bump 三处同步**（缺一即漂移）：`learn_engine/__init__.py` 的 `__version__`（唯一真源）
  + `PLAYBOOK.md` frontmatter `version` + `CHANGELOG.md` 补一条。**MAJOR 须人工确认**。
- 🔴 **任何路径换算函数不得依赖 CWD**（`Path(p).resolve()` 是错的；用 `(ROOT / p)`）。
- 🔴 **判 push 成败必须用命令替换**（`out="$(git push ... 2>&1)"`），
  **不能走管道** —— `| head` 的退出码取自 `head`（恒 0），失败会被吞掉。
- ⚠️ **「未推」可能是刻意设计** —— LIBGOV 的 `github` 曾长期「仅配置、未推」，
  原因是该层文档含内部项目名与本地路径、须 Owner 确认可见性。
  **此类情况不要当成故障擅自补推**。
- ⚠️ **数字必须实测**，不许凭印象写进文档（本对话已抓到一处 46/47 的错）。
- ⚠️ **历史快照文档（`HANDOFF.md`）不篡改历史** —— 加时效声明指向最新状态即可。
- ⚠️ **改内核铁律**：bump `__version__` → 写 `Project Audit/` 方案+审计 → 归档 → 再编码。

---

## 五、Suggested Skills

下一个 agent 应按需 `Skill` 调用：

- **`audit-os`** —— 任何内核方案 / 架构评审走此工作流（`方案_tbd` → `审计_tbA` → `终版_OK` → 归档）。
- **`standard-lib-search`** —— 新项目立项 / 判断「要不要消费 LESSON-OS」时先检索注册表；
  硬闸门：**无检索结论不得进 VCP 步骤 3**。
- **`handoff`** —— 下次交接时再生成一份（本文件即范例）。
- **`vibe-coding-preflight`** —— 涉及动内核代码时的前置检查。

---

## 六、引用产物（路径）

**本仓（`D:\Projects\LESSON-OS`）**
- `CHANGELOG.md` —— 版本变更记录（0.1.0→0.5.0）
- `MVP-Backlog.md` —— 工单状态（P1 全绿、技术债 B6/B7）
- `ADR/README.md` —— ADR 索引（含空洞号说明）
- `PLAYBOOK.md` —— 领域 SSOT；`AGENTS.md` —— 执行宪法
- `scripts/sync_all.sh` —— 五仓双远端一键同步
- `HANDOFF.md` —— **2026-10-10 历史快照**（已加时效声明，勿当作最新状态）
- `.workbuddy/memory/2026-10-13.md` —— 本日工作日志
- `.workbuddy/memory/MEMORY.md` —— 项目级长期记忆

**治理层（`D:\Projects\LIBGOV`）**
- `README.md` §备份与远端；`LIBGOV.md` §决策台账
- `registry/REGISTRY.md`（生成物）+ `registry/build_registry.py`（生成器）

**消费方（`D:\SixSigmaBlackBelt`）**
- `docs/变更记录/2026-10-13-判分委托内核.md`
- `src/bbcore.py`（委托入口）；`vendor/LESSON-OS`（submodule，钉 `948b419`）
- `AGENTS.md` + `docs/契约/`（判分 / 提取 / 一致性约束全文）

---

_本文件生成于 2026-10-13 17:48。_
