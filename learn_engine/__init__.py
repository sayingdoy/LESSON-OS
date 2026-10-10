"""learn_engine — 跨项目共享学习内核 (LESSON-OS).

零外部依赖（仅 Python 标准库）。版本化单文件内核：各项目按 semver 钉版本复用，
形态为 git submodule 钉 commit 或 vendor/ 钉副本；交付时整文件拷贝脱离代码库。

共享边界（2026-10-10 对 bb-prep / vocab-app 真实源码核对）：
  - 状态机 + is_due + frontmatter IO：逻辑同源，LADDER 作为参数注入（两项目 LADDER 不同！）
  - 判定 / 出卷：项目策略（adapter），因答案形态与抽题规则不同

⚠️ 本文件是 P0/P1 骨架：scheduler/vault/model 的共享逻辑可直用；
   grader/picker 的 bb-prep 风格 adapter 与 apply_result/write_front 的 IO 落地为 P1 占位。
"""
__version__ = "0.1.0"

from .model import Item, DEFAULT_LADDER, MASTER_STAGE
from .scheduler import is_due, next_schedule, apply_result
from .vault import parse_front, write_front, as_date
from .grader import Grader, ExactMatchGrader
from .picker import Picker, WeightedPicker

__all__ = [
    "Item", "DEFAULT_LADDER", "MASTER_STAGE",
    "is_due", "next_schedule", "apply_result",
    "parse_front", "write_front", "as_date",
    "Grader", "ExactMatchGrader",
    "Picker", "WeightedPicker",
]
