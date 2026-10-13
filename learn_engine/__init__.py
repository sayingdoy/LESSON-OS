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
"""
__version__ = "0.4.0"

from .model import Item, DEFAULT_LADDER, MASTER_STAGE, STATES, POOL_NEW
from .scheduler import is_due, next_schedule, apply_result
from .vault import parse_front, write_front, as_date
from .grader import Grader, ExactMatchGrader
from .picker import Picker, WeightedPicker

__all__ = [
    "Item", "DEFAULT_LADDER", "MASTER_STAGE", "STATES", "POOL_NEW",
    "is_due", "next_schedule", "apply_result",
    "parse_front", "write_front", "as_date",
    "Grader", "ExactMatchGrader",
    "Picker", "WeightedPicker",
]
