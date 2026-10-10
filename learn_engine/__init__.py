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
"""
__version__ = "0.2.0"

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
