# MVP-Backlog — LESSON-OS 垂直切片工单

> 建立 2026-10-10 | Owner: Jason
> 切片原则：**每片都能独立验证、独立回滚**。不按"层"切（先写 schema 再写代码），
> 按**贯穿路径**切（一片打通一条端到端通路）。

---

## 现状

| 阶段 | 状态 |
|---|---|
| P0 手册 + SSOT schema + 路线图 + 骨架 | ✅ 完成 |
| **R1 契约修正（裁决 B1–B5 / A3余 / C1余）** | ✅ **完成 2026-10-11**（内核 → `0.2.0`） |
| **P1 抽代码（本 backlog）** | ⬜ 待启动 |
| P2 接入 + 技能库 | ⬜ 待启动 |
| FSRS 后端 | ⬜ P2 候选 |

**技术债清单**（P1 要还的）：
- `vault.write_front` → `NotImplementedError`
- `grader.Grader.judge` → 基类占位，bb-prep adapter 缺失
- `picker.WeightedPicker.pick` → **有新债**：真源的「新题贪心 + 温和上限
  `cap=⌈w/tot·n⌉+1`」未移入（B2 已知差距，必须 A 片补齐）
- `picker` / `scheduler` / `vault` 内部**四份同源日期解析**（B6，P1 收敛到一处）
- ✅ **已清**：`tests/` + golden-set 已建（2026-10-11）

> **R1 契约修正已完成**（2026-10-11，内核 `0.1.0 → 0.2.0`）：
> B1 `judge` → `str`；B2 `pick` 显式注入（去重/权重不再空转）；B3 ADR-0002 固定 `rng`
> （`FIXED_SEED=20261010`）；B4 `POOL_NEW` 常量；B5 引用改真源。
> 详见 `audit_log.md` 决策链。

---

## P1-A · 打通「排期写入」端到端（第一片，零风险）

**为什么先做这片**：`scheduler` 是纯函数状态机（无 I/O），`vault.write_front` 是唯一
写盘入口。这片打通后，「读入 → 排期 → 写回」形成闭环，且**行为可逐字节比对**。

| # | 工单 | 验收 |
|---|---|---|
| A1 | 建 `learn_engine/tests/` + golden-set 骨架 | ✅ **完成 2026-10-11**（13 项断言全过，基线存 `golden_v0.2.0.json`） |
| A2 | 实装 `vault.write_front`（只改已存在的 frontmatter 键，正文一字不动） | 单测：改前 / 改后逐字节比对，**正文零变化** |
| A3 | bb-prep `src/bbcore.py` 排期逻辑改为 `import learn_engine` | 改前 / 改后出卷**逐字节相同** |
| A4 | **补 `picker` 的新题贪心 + 温和上限**（B2 遗留） | 与 bb-prep `pick_items` 在同一 seed 下输出一致 |

**预登记（写死在前面，不许事后改）**：
> **P1-A 通过判据**：A2 单测全过 + A3 的 bb-prep 出卷输出与改前**逐字节一致**。
> **验收第 0 步**：`rng = random.Random(20261010)` 必须固定（ADR-0002）。
> **失败条款**：任一不过 ⇒ **不进入 P1-B**，先查差异来源。
> **LADDER 处理**：`bbcore.py:28` 的 `[1,2,4,7,14,28,45]` 与 `review.py:25` 的
> `[1,2,4,7,15,30,60,120]` **不同** → LADDER 作**注入参数**，内核只提供默认值（ADR-0001）。

---

## P1-B · 打通「判分」端到端（第二片，含 adapter）

| # | 工单 | 验收 |
|---|---|---|
| B1 | 实装 `grader` 的 bb-prep adapter（字母集 / 数值） | 大小写归一化 + 截断「；思路：」；对 `XBARR` 类输入不被误抓 |
| B2 | 补 `judge` 的回归测试（覆盖历史判分器 bug 场景） | 70% / 60% 那次真实正确率可复现 |
| B3 | bb-prep `src/` 判分改为 `import learn_engine` | 对同一批作答，改前 / 改后判定**完全一致** |

**预登记**：
> **P1-B 通过判据**：B1/B2 单测全过 + B3 判定与改前**完全一致**。
> ⚠️ **判分铁律不可破**：判分必须是**纯代码**，模型不参与（PLAYBOOK §5.1）。

---

## P1-C · 收尾：版本锚点与发布（小片）

| # | 工单 | 验收 |
|---|---|---|
| C1 | 各仓库 `git init`（顺序：LESSON-OS → bb-prep → vocab-app → AI-Kongzi） | ✅ **完成 2026-10-10**，4 仓库就绪 |
| C2 | 消费项目以 `git submodule` 钉 LESSON-OS commit | ✅ **完成**：bb-prep `vendor/LESSON-OS` @`620a334`，URL 指向远端 |
| C3 | 补 `__version__` bump 记录 + ADR 归档 | ⬜ 待做 |

> **备份已闭环**：4 仓库全部推送至 `ecs:/srv/git/`（自建裸库，异地）。
> 日常同步 `bash scripts/sync_all.sh`。详见 ADR-0003「备份闭环」。
> 残余风险：ECS 单点（无第三方托管）→ P2 可加 bundle 到网盘。

---

## P2 展望（本 backlog 不含，仅登记）

- vocab-app / AI-Kongzi 接入 `learn_engine`（届时 `maturity: planned → adopted`）
- `tutor-prompt-library` 技能库 + CI golden-set
- FSRS 可选后端（同 `next_schedule` 接口替换）
- `standard-lib-search` 独立 skill 串进 VCP 步骤 1

---

## 纪律（每片都适用）

1. **切片内不跨阶段**：A 片没验收完不动 B 片。
2. **预登记不改**：通过门槛在看数据前写死。
3. **点火验证**：改完必须跑一次**真实出卷**，不是只跑单测。
4. **部分通过就报部分通过**：说清差在哪。
