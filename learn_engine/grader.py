"""判定契约（确定性，模型不参与）。项目策略（adapter）。

判分纯代码、模型不参与 —— 真源：bb-prep `docs/契约/引擎与数据.md`（判分铁律）
（注：bb-prep `AGENTS.md` §4.3 的编号铁律是讲解纪律，判分约束全文在契约目录，
 `AGENTS.md:45-46` 明写「已移至」）。vocab-app 同构。

答案形态因项目而异 -> 用策略接口，不塞进内核。
返回值统一为字符串 "correct" / "wrong"（对齐 bb-prep `bbcore.judge` 与
vocab-app `review.judge` 两个真源；内核早期版本曾用 bool，属孤例，已纠正）。

**分层（0.5.0 起）**：
  · `Grader`             —— 接口，只有 `judge(raw, expected) -> str`
  · `ExactMatchGrader`   —— 通用：归一后精确匹配（vocab-app 用）
  · 四个**判分原语**：`LetterSetGrader` / `TrueFalseGrader` / `NumericGrader` /
    `KeywordGrader`（bb-prep 用）。它们只实现**领域无关的判分形态**，
    一切**项目策略**（中文分隔符、真值别名表、字母范围、容差）都由消费方**注入** ——
    内核不预设「；思路：」这类中文习惯，也不认识 qtype 名。
  · **路由（按 qtype 分派）留在消费方** —— qtype 词表是项目策略。
"""
from __future__ import annotations

import re


def _norm(s: str) -> str:
    """去全部空白 + 小写。真源：bb-prep `bbcore.normalize`。"""
    return re.sub(r"\s+", "", (s or "").strip().lower())


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
        return _norm(s)

    def judge(self, raw: str, expected: str) -> str:
        a = self._norm(raw)
        return "correct" if a and a == self._norm(expected) else "wrong"


# ── 判分原语（bb-prep 风格；差异点走**注入**，不塞进内核）───────────────────
class LetterSetGrader(Grader):
    """选项字母集判分（单选 / 多选）。

    真源：bb-prep `bbcore.letters()`。两处处理均为实际踩坑所得（2026-10-06）：

      1. **截断到分隔符之前** —— 作答常带中文思路，如
         「B；思路：……与 XBARR 图的差异……」，其中 XBARR 的 A、B 会被
         误抓成选项字母，导致**已答对的题被判错**；
      2. **`.upper()` 不可省** —— 手打小写（`c` / `ab`）而 answer 是大写，
         不统一大小写则小写作答永远判错（当日 10 题里 9 题因此误判）。

    `split_re`（分隔符正则）与 `alphabet_re`（字母字符类内容）都是**项目策略**，
    由消费方注入 —— 内核不预设中文分隔符，也不预设只有 A–H。
    """

    def __init__(self, *, split_re: re.Pattern, alphabet_re: str = "A-Ha-h"):
        self._split = split_re
        self._alphabet = re.compile(f"[{alphabet_re}]")

    def letters(self, s: str) -> str:
        """→ 大写、去重、升序的选项字母串（如 'ABD'）。逐字对齐真源。"""
        head = self._split.split(s or "", 1)[0]
        return "".join(sorted(set(self._alphabet.findall(head)))).upper()

    def judge(self, raw: str, expected: str) -> str:
        got, want = self.letters(raw), self.letters(expected)
        return "correct" if got and got == want else "wrong"


class TrueFalseGrader(Grader):
    """判断题：把作答与标准答案都归一到真/假再比较。

    真源：bb-prep `bbcore.judge_tf()` —— **只取作答里出现的第一个判断词**
    （避免「对，但……思路」这类附注干扰）；词表未命中一律判错。

    `true_tokens` / `false_tokens`（中文「对/错」+ 符号 + 英文别名）是项目策略，
    由消费方注入。
    """

    def __init__(self, *, split_re: re.Pattern,
                 true_tokens, false_tokens):
        self._split = split_re
        self._true = {_norm(t) for t in true_tokens}
        self._false = {_norm(t) for t in false_tokens}

    @staticmethod
    def _scan(head: str, want_set: set[str], other_set: set[str]) -> str:
        wants = {t[0] for t in want_set if t}
        others = {t[0] for t in other_set if t}
        for ch in head:
            if ch in wants:
                return "correct"
            if ch in others:
                return "wrong"
        return "wrong"

    def judge(self, raw: str, expected: str) -> str:
        head = _norm(self._split.split(raw or "", 1)[0])
        want = _norm(expected)
        if want in self._true:
            return self._scan(head, self._true, self._false)
        if want in self._false:
            return self._scan(head, self._false, self._true)
        return "wrong"


class NumericGrader(Grader):
    """计算题：填数值，按**绝对容差**比对。

    真源：bb-prep `bbcore.judge()` 的 `calc` 分支。

    ⚠️ 真源**不截断思路** —— 思路里的数字也参与比对（已知特性，保持等价，
    不"顺手修"）。`expected` 可为 `str`，或 `{"answer": str, "tol": float}`
    以支持**逐题容差**（真源的 `item["tol"]`，默认 0.01）。
    """

    def __init__(self, *, num_re: re.Pattern, tol: float = 0.01):
        self._num = num_re
        self._tol = tol

    def judge(self, raw: str, expected) -> str:
        if isinstance(expected, dict):
            key = str(expected.get("answer", ""))
            tol = expected.get("tol")
            # 真源是 `float(item.get("tol", 0.01) or 0.01)` —— **falsy 即回退默认**
            # （含 `0` / `""` / `None`）。逐字等价，不"顺手"把 0 当合法容差。
            tol = self._tol if not tol else float(tol)
        else:
            key, tol = str(expected), self._tol
        try:
            want_v = float(self._num.search(key.replace(",", "")).group())
        except (TypeError, AttributeError, ValueError):
            return "wrong"          # key 本身坏 —— 判错，由结算侧报 warning
        nums = self._num.findall(str(raw).replace(",", ""))
        return "correct" if any(
            abs(float(n) - want_v) <= tol for n in nums) else "wrong"


class KeywordGrader(Grader):
    """要点题：关键词**全含**才算对。

    真源：bb-prep `bbcore.judge()` 的 `short` 分支（`|` / `｜` 分隔关键词）。
    关键词为空 ⇒ 判错（真源 `kws and all(...)` 的短路语义）。
    """

    def __init__(self, *, sep_re: str = r"[|｜]"):
        self._sep = re.compile(sep_re)

    def judge(self, raw: str, expected) -> str:
        kws = [k for k in self._sep.split(str(expected)) if k.strip()]
        ans = _norm(raw)
        return "correct" if kws and all(_norm(k) in ans for k in kws) else "wrong"


# 路由（按 qtype 分派到原语）**留在消费方** —— qtype 词表是项目策略，
# 每个项目的题型命名不同，塞进内核会让内核不认识自己的输入。

