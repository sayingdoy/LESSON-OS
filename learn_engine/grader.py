"""判定契约（确定性，模型不参与）。项目策略（adapter）。

bb-prep AGENTS.md 铁律 6 / vocab-app 同构：判分纯代码，模型不参与。
答案形态因项目而异 -> 用策略接口，不塞进内核。
"""
from __future__ import annotations

import re


class Grader:
    """策略接口：judge(raw, expected) -> bool。各项目实现自己的答案形态。"""

    def judge(self, raw: str, expected) -> bool:
        raise NotImplementedError


class ExactMatchGrader(Grader):
    """vocab-app 风格：归一化（去空白、小写）后精确匹配（英文词）。

    对应 vocab-app src/review.py::judge(raw, word)。
    """

    @staticmethod
    def _norm(s: str) -> str:
        return re.sub(r"\s+", "", (s or "").strip().lower())

    def judge(self, raw: str, expected: str) -> bool:
        a = self._norm(raw)
        return bool(a) and a == self._norm(expected)


# ── bb-prep 风格 adapter（P1 实现）──────────────────────────────────────────
# 差异点（不得塞进内核，走 adapter）：
#   - 大小写归一化 + 截断「；思路：」后中文说明（Jason 手打习惯）
#   - 多选：选项字母连写（acde）与答案集合比对
#   - 计算题：填数值，容差/单位处理
# 实现示例：
#   class MultiChoiceGrader(Grader):
#       def judge(self, raw, expected_set): ...
#   class NumericGrader(Grader):
#       def judge(self, raw, expected_value, tol=...): ...
