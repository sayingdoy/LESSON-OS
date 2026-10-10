"""判定契约（确定性，模型不参与）。项目策略（adapter）。

判分纯代码、模型不参与 —— 真源：bb-prep `docs/契约/引擎与数据.md`（判分铁律）
（注：bb-prep `AGENTS.md` §4.3 的编号铁律是讲解纪律，判分约束全文在契约目录，
 `AGENTS.md:45-46` 明写「已移至」）。vocab-app 同构。

答案形态因项目而异 -> 用策略接口，不塞进内核。
返回值统一为字符串 "correct" / "wrong"（对齐 bb-prep `bbcore.judge` 与
vocab-app `review.judge` 两个真源；内核早期版本曾用 bool，属孤例，已纠正）。
"""
from __future__ import annotations

import re


class Grader:
    """策略接口：judge(raw, expected) -> "correct" | "wrong"。

    返回**字符串**而非 bool：两个消费方真源均返回字符串，且 bb-prep
    `judge_tf` 有 'blank'（空作答）语义 —— bool 无位可放，会丢信息。
    """

    def judge(self, raw: str, expected) -> str:
        raise NotImplementedError


class ExactMatchGrader(Grader):
    """vocab-app 风格：归一化（去空白、小写）后精确匹配（英文词）。

    对应 vocab-app src/review.py::judge(raw, word) -> "correct" | "wrong"。
    """

    @staticmethod
    def _norm(s: str) -> str:
        return re.sub(r"\s+", "", (s or "").strip().lower())

    def judge(self, raw: str, expected: str) -> str:
        a = self._norm(raw)
        return "correct" if a and a == self._norm(expected) else "wrong"


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
