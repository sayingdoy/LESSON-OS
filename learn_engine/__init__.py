"""learn_engine — 跨项目共享学习内核 (LESSON-OS).

零外部依赖（仅 Python 标准库）。版本化单文件内核：各项目按 semver 钉版本复用，
形态为 git submodule 钉 commit 或 vendor/ 钉副本；交付时整文件拷贝脱离代码库。

共享边界（2026-10-10 对 bb-prep / vocab-app 真实源码核对）：
  - 状态机 + is_due + frontmatter IO：逻辑同源，LADDER 作为参数注入（两项目 LADDER 不同！）
  - 判定 / 出卷：项目策略（adapter），因答案形态与抽题规则不同

⚠️ 本文件是 P0/P1 骨架：scheduler/vault/model 的共享逻辑可直用；
   grader/picker 的 bb-prep 风格 adapter 与 apply_result/write_front 的 IO 落地为 P1 占位。

版本：
  0.1.0（2026-10-10）P0 骨架。
  0.2.0（2026-10-11）契约修正（R1 待裁决项落地）：
    - B1 `judge` 返回类型 bool → str（"correct"/"wrong"，对齐双源）
    - B2 `pick` 改为**显式注入**（recent/history_counts/domain_weights/is_exam），
      消除 getattr 与恒空 {} 的"假能力"；真实生效
    - B3 验收判据补「固定 rng 种子」（见 ADR-0002）
    - B4 新增 `POOL_NEW` 常量；`new` 明确为**哨兵**而非 SRS 状态
    - 新增 golden-set 验收脚本（固定 rng，可逐字节比对）
  0.3.0（2026-10-13）P1-A4 内核与 bb-prep 出卷行为对齐：
    - `WeightedPicker` 补齐真源的「新题按域缺口**贪心**取 + **温和上限**
      `cap = ⌈w/tot·n⌉ + 1`」（真源 bb-prep `src/practice.py:181-217`）。
      此前新题档为"排序后取前缀"，与 bb-prep 卷面九域分布不一致（B2 遗留债）。
    - golden-set 新增 3 项 A4 断言（贪心生效 / 上限约束 / 非朴素前缀），**共 16 项**
    - **⚠️ 行为变更**：同一 rng 下新题档与 0.2.0 **不同** →
      消费方升级后必须重跑验收（G3），并对齐 golden 基线。
    - 已知剩余差异：池不足时的**补位分支**语义（内核按 state 路由回 review/fresh
      两档；真源一律并入 fresh）—— 待 A3 前裁决。
  0.4.0（2026-10-13）P1-A2 实装 `vault.write_front`：
    - 占位（`NotImplementedError`）→ 实装（真源 bb-prep `src/bbcore.py:write_front`）：
      **只改已存在的键、新键追加末尾、正文一字不动、强制 LF 行尾**。
    - golden-set 新增 9 项字节级断言（正文零变化 / 仅列出的键变 / LF 归一 /
      新键追加 / 幂等 / 值写法 / 异常路径），**共 25 项**。
    - **选题行为未变**：golden 输出与 0.3.0 逐字节相同（`golden_v0.4.0.json`
      与 `golden_v0.3.0.json` 一致即证）。
  0.5.0（2026-10-13）P1-B1 判分原语（bb-prep 风格 adapter）：
    - 新增四个**领域无关判分原语**（真源 bb-prep `src/bbcore.py:364-453`）：
      `LetterSetGrader`（选项字母集）/ `TrueFalseGrader`（判断题）/
      `NumericGrader`（数值 + 逐题容差）/ `KeywordGrader`（要点题关键词全含）。
      一切**项目策略**（中文分隔符 `；思路：`、真值词表、字母范围、容差）由消费方
      **注入** —— 内核不预设中文习惯、不认识 qtype；**路由留消费方**。
    - `NumericGrader` 对齐真源的 `float(x or 0.01)`：**tol 为 falsy 即回退默认**
      （不把 `0` 当零容差）；calc **不截断思路**（思路里的数字也参与比对）——
      两处都是真源既有语义，**保持等价、不"顺手修"**。
    - golden-set 新增 21 项（4 类判决 + 每类一条"换注入 → 结果变"的参数化证明），
      **共 47 项**（commit message 原写 46，实测 47 —— 勘误同步全仓）。
    - ⚠️ 纯新增能力：既有 `ExactMatchGrader` 与选题/排期行为**完全未变**。
  0.5.1（2026-10-13）PATCH 修 `is_due` 边界崩溃：
    - `scheduler.is_due` 对非 str 非 date 的 due（int/bool，来自数值强转型
      frontmatter 的脏数据）此前直接 `d <= ref` 抛 **TypeError**；现按
      「不可解析 → 到期」处理，对齐两消费方本地实现（经 as_date 归一）语义。
    - **零调用方**（两消费方均保留本地 is_due）→ 零回归；签名不变、既有路径
     行为不变（None / str / date 三分支原样）。
    - golden-set 新增 14 例 `is_due` 边界断言（10 例 dict 形态 + 审计后补
      4 例 Item 属性形态），**共 61 项**；golden 输出（picker 场景）
      **逐字节不变**（基线 `golden_v0.5.1.json` 与 0.5.0 等价）。
    - 审计轮次：`Project Audit/Archive/v0.5.1_is_due边界修复_R1_方案_tbd`。
    - `picker._is_due` 同形状问题**不在本版范围** —— 归技术债 B6 一并收敛。
"""
__version__ = "0.5.1"

from .model import Item, DEFAULT_LADDER, MASTER_STAGE, STATES, POOL_NEW
from .scheduler import is_due, next_schedule, apply_result
from .vault import parse_front, write_front, as_date
from .grader import (Grader, ExactMatchGrader, LetterSetGrader, TrueFalseGrader,
                     NumericGrader, KeywordGrader)
from .picker import Picker, WeightedPicker

__all__ = [
    "Item", "DEFAULT_LADDER", "MASTER_STAGE", "STATES", "POOL_NEW",
    "is_due", "next_schedule", "apply_result",
    "parse_front", "write_front", "as_date",
    "Grader", "ExactMatchGrader",
    "LetterSetGrader", "TrueFalseGrader", "NumericGrader", "KeywordGrader",
    "Picker", "WeightedPicker",
]
