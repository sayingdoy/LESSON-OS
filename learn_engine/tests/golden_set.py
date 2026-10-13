"""golden-set 验收脚本（ADR-0002 落地，P1-A1 第一单）。

目的：给内核变更提供**确定性回归网** —— 固定 items + 固定 `today` + 固定 `rng`，
对同一输入跑出**逐字节可比**的输出。改前 / 改后各跑一次，输出必须一致。

★ 铁律（ADR-0002 验收第 0 步）：
  **未固定 rng 时逐字节比对不成立。** 本脚本的 FIXED_SEED 是唯一随机源，
  任何测试都不得用 `Random(None)`。

用法：
  python -m learn_engine.tests.golden_set                 # 跑验收（打印摘要）
  python -m learn_engine.tests.golden_set --dump          # 打印 golden 输出（供比对）
  python -m learn_engine.tests.golden_set --save <path>   # 写 golden 基线（UTF-8/LF）

纯 stdlib `unittest`，不引 pytest（守零外部依赖铁律）。
"""
from __future__ import annotations

import datetime as dt
import json
import random
import re
import sys
import tempfile
import unittest
from pathlib import Path

from ..picker import WeightedPicker
from ..model import POOL_NEW, DEFAULT_LADDER, Item
from ..scheduler import is_due, next_schedule
from ..grader import (ExactMatchGrader, LetterSetGrader, TrueFalseGrader,
                      NumericGrader, KeywordGrader)
from ..vault import parse_front, write_front

# ── 固定常量（ADR-0002：不得临场改）────────────────────────────────────────
FIXED_SEED = 20261010
FIXED_TODAY = dt.date(2026, 10, 11)

# golden 场景的**注入数据**（固定；集中于此便于断言复用，勿散落到用例里）
GOLDEN_REVIEW_N, GOLDEN_NEW_N = 10, 12
GOLDEN_WEIGHTS = {"D1-组织开展": 10, "D2-过程管理": 7, "D5-测量": 22,
                  "D6-分析": 22, "D7-改进": 22}
GOLDEN_HIST = {"D5-测量": 30, "D6-分析": 10}


# ── 固化样本 items（golden-set 的"固定一批"）────────────────────────────────
def _golden_items() -> list[dict]:
    """确定性构造的样本池：覆盖 到期/未到期、真题/自建、九域、new/learning/lapsed。

    刻意不读真实题库 —— golden-set 要**稳定可控**，不随题库演进漂移。
    真实题库的端到端验收由 bb-prep 侧 `tests/selftest.py` 负责（点火验证）。
    """
    items: list[dict] = []
    domains = ["D1-组织开展", "D2-过程管理", "D5-测量", "D6-分析", "D7-改进"]

    # 到期复习题（learning / lapsed，due <= FIXED_TODAY）
    # ⚠️ 前 10 题**同日到期**：九域权重只在「同一到期日之间」起作用
    #    （due 是绝对第一键），所以样本必须含同日组，否则权重测不出来。
    for i in range(12):
        same_day = i < 10
        due = (FIXED_TODAY if same_day
               else FIXED_TODAY - dt.timedelta(days=1))
        items.append({
            "id": f"g-due-{i:02d}",
            "state": "lapsed" if i % 3 == 0 else "learning",
            "due": due.isoformat(),
            "domain": domains[i % len(domains)],
            "exam": (i % 2 == 0),
        })
    # 未到期复习题（不应被抽为到期复习）
    for i in range(4):
        items.append({
            "id": f"g-future-{i:02d}",
            "state": "review",
            "due": (FIXED_TODAY + dt.timedelta(days=3 + i)).isoformat(),
            "domain": domains[i % len(domains)],
            "exam": True,
        })
    # 新题（state=new）；其中一部分在近期窗口内
    for i in range(20):
        it = {
            "id": f"g-new-{i:02d}",
            "state": POOL_NEW,
            "due": "",
            "domain": domains[i % len(domains)],
            "exam": (i % 3 != 0),
        }
        items.append(it)
    return items


def _run_pick(items, review_n, new_n, recent, weighted=True):
    """跑一次出卷，返回可逐字节比对的纯数据。"""
    rng = random.Random(FIXED_SEED)          # ★ 唯一随机源
    picker = WeightedPicker()
    review, fresh = picker.pick(
        review_n, new_n, items, rng, FIXED_TODAY,
        exclude=set(), exam_first=True, weighted=weighted,
        recent=recent,
        history_counts=dict(GOLDEN_HIST),
        domain_weights=dict(GOLDEN_WEIGHTS),
        is_exam=lambda i: bool(i.get("exam")),
        ladder=DEFAULT_LADDER,
    )
    return {
        "review": [i["id"] for i in review],
        "fresh": [i["id"] for i in fresh],
        "review_states": [i["state"] for i in review],
    }


def golden_output() -> dict:
    """golden 输出（改前改后应逐字节一致）。"""
    items = _golden_items()
    recent = {"g-new-00", "g-new-01", "g-new-02", "g-due-00", "g-due-01"}
    return {
        "seed": FIXED_SEED,
        "today": FIXED_TODAY.isoformat(),
        "main": _run_pick(items, GOLDEN_REVIEW_N, GOLDEN_NEW_N, recent, weighted=True),
        "no_weight": _run_pick(items, GOLDEN_REVIEW_N, GOLDEN_NEW_N, recent,
                               weighted=False),
        "gap0": _run_pick(items, GOLDEN_REVIEW_N, GOLDEN_NEW_N, set(), weighted=True),
    }


# ── 测试 ────────────────────────────────────────────────────────────────────
class TestGoldenSet(unittest.TestCase):
    """golden-set 核心断言。"""

    def test_seed_is_fixed(self):
        """★ 验收第 0 步：随机源必须固定（FIXED_SEED 有值且非 None）。"""
        self.assertIsNotNone(FIXED_SEED, "FIXED_SEED 不得为 None —— 判据作废")
        self.assertIsInstance(FIXED_SEED, int)

    def test_determinism(self):
        """同一 seed 两次运行，输出逐字节一致。"""
        a = json.dumps(golden_output(), ensure_ascii=False, sort_keys=True)
        b = json.dumps(golden_output(), ensure_ascii=False, sort_keys=True)
        self.assertEqual(a, b, "固定 seed 下两次输出必须逐字节一致")

    def test_new_pool_excludes_recent(self):
        """近期窗口内的**新题**不得被抽中（去重生效）。"""
        out = golden_output()["main"]
        recent_new = {"g-new-00", "g-new-01", "g-new-02"}
        picked_new = [i for i in out["fresh"]]
        hit = recent_new & set(picked_new)
        self.assertEqual(hit, set(), f"新题档混入窗口内题：{hit}")

    def test_due_pool_fresh_first(self):
        """到期池 fresh 优先：窗口内的到期题只作回退。"""
        out = golden_output()["main"]
        recent_due = {"g-due-00", "g-due-01"}
        review = out["review"]
        # 到期 fresh 共 10 题（12 due − 2 in recent），需求 10 → 应全是 fresh
        self.assertEqual(set(recent_due) & set(review), set(),
                         "fresh 足够时不应回退窗口内到期题")

    def test_quantity(self):
        """题量符合请求（池足够时）。"""
        out = golden_output()["main"]
        self.assertEqual(len(out["review"]), 10)
        self.assertEqual(len(out["fresh"]), 12)

    def test_gap0_changes_result(self):
        """gap=0（关闭去重）应与开启时不同 —— 证明去重真的在起作用。"""
        g = golden_output()
        self.assertNotEqual(g["main"], g["gap0"],
                            "关闭去重后结果应变化（否则去重是空转的）")

    def test_weight_changes_result(self):
        """加权与不加权应不同 —— 证明九域权重真的在起作用（B2 核心）。"""
        g = golden_output()
        main_r = g["main"]["review"]
        nw_r = g["no_weight"]["review"]
        self.assertNotEqual(main_r, nw_r,
                            "加权/不加权结果应不同（否则权重是空转的）")


class TestNewPoolGreedy(unittest.TestCase):
    """A4：新题档「按域缺口贪心 + 温和上限 cap=⌈w/tot·n⌉+1」。

    真源：bb-prep `src/practice.py:181-217`（`pick_items` 的 weighted 分支）。
    这里用**极小合成样本**把两条性质分别钉死，避免 golden 场景里互相掩盖：
      ① 贪心：严重欠配的域即使目标权重极低，也必须被拉进新题档；
      ② 上限：它不得因此独占整卷 —— 触顶即让位。
    """

    @staticmethod
    def _items():
        out: list[dict] = []
        for dom, prefix in (("A", "a"), ("B", "b")):
            for i in range(20):
                out.append({"id": f"{prefix}-{i:02d}", "state": POOL_NEW,
                            "due": "", "domain": dom, "exam": True})
        return out

    def _pick(self, weights, hist, review_n, new_n):
        rng = random.Random(FIXED_SEED)
        review, fresh = WeightedPicker().pick(
            review_n, new_n, self._items(), rng, FIXED_TODAY,
            exclude=set(), exam_first=True, weighted=True, recent=set(),
            history_counts=hist, domain_weights=weights,
            is_exam=lambda i: bool(i.get("exam")),
            ladder=DEFAULT_LADDER)
        return review, fresh

    def test_cap_limits_dominant_domain(self):
        """贪心拉入欠配域 A，但 cap=⌈1/100·10⌉+1=2 把它截在 2 题。"""
        from collections import Counter
        # A 目标权重 1/100，历史累计 0 → 欠配 1.0；B 历史 100 → 超配 -1.0
        _, fresh = self._pick({"A": 1, "B": 99}, {"B": 100}, 0, 10)
        self.assertEqual(len(fresh), 10)
        c = Counter(i["domain"] for i in fresh)
        self.assertEqual(c["A"], 2,
                         "欠配域 A 应被贪心选中、且被温和上限截在 2（cap=2）")
        self.assertEqual(c["B"], 8)

    def test_greedy_not_naive_prefix(self):
        """加权的新题档不得等于 `new[:n]` 朴素前缀（否则 A4 是空转的）。"""
        g = golden_output()
        self.assertNotEqual(
            g["main"]["fresh"], g["no_weight"]["fresh"],
            "加权 / 不加权的新题档应不同 —— 若相同则贪心分支未生效（A4 回退）")

    def test_domain_cap_respected_in_golden(self):
        """golden 主场景：review+fresh 各域名额不超过 cap（复习题自带名额除外）。"""
        import math
        from collections import Counter
        byid = {i["id"]: i for i in _golden_items()}
        out = golden_output()["main"]
        tot = sum(GOLDEN_WEIGHTS.values())
        n_sheet = GOLDEN_REVIEW_N + GOLDEN_NEW_N
        cap = {d: max(1, math.ceil(w / tot * n_sheet) + 1)
               for d, w in GOLDEN_WEIGHTS.items()}
        c_rev = Counter(byid[i]["domain"] for i in out["review"])
        c_all = Counter(byid[i]["domain"] for i in out["review"] + out["fresh"])
        for d in GOLDEN_WEIGHTS:
            self.assertLessEqual(
                c_all[d], max(cap[d], c_rev[d]),
                f"{d} 超出温和上限：{c_all[d]} > cap={cap[d]}"
                f"（复习题已自带 {c_rev[d]}）")


class TestJudgeContract(unittest.TestCase):
    """B1：judge 返回字符串，对齐双源。"""

    def test_returns_str(self):
        g = ExactMatchGrader()
        self.assertEqual(g.judge("hello", "hello"), "correct")
        self.assertEqual(g.judge("world", "hello"), "wrong")
        self.assertEqual(g.judge("", "hello"), "wrong")
        self.assertIsInstance(g.judge("x", "y"), str,
                              "judge 必须返回 str，不得返回 bool（B1 裁决）")


# ── P1-B1：bb-prep 风格判分原语（9 个历史边界用例的回归）─────────────────────
# 真源：bb-prep `src/bbcore.py:364-453`；事故记录 `docs/变更记录/2026-10-06-判分器缺陷修复.md`。
# 四个原语一切**项目策略**均由消费方注入 —— 下面每类都带一条"注入不同策略 →
# 结果不同"的断言，证明内核**没有**把中文分隔符 / 词表写死。
SPLIT_BBPREP = re.compile(r"[；;。\n]|思路")     # bb-prep 真源分隔符
TF_TRUE = {"对", "正确", "是", "√", "t", "true", "y", "yes", "✓"}
TF_FALSE = {"错", "错误", "否", "×", "x", "f", "false", "n", "no", "✗"}
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


class TestLetterSetGrader(unittest.TestCase):
    """选项字母集。历史 bug ①（未 upper）与 ②（未截断思路）在此锁死。"""

    def setUp(self):
        self.g = LetterSetGrader(split_re=SPLIT_BBPREP)

    def test_lowercase_normalized(self):
        """bug ①：手打小写（c / ab）不得判错。10-06 的 10 题里 6 题因此误判。"""
        self.assertEqual(self.g.judge("c", "C"), "correct")
        self.assertEqual(self.g.judge("ab", "AB"), "correct")
        self.assertEqual(self.g.judge("a", "A"), "correct")

    def test_multichoice_unordered(self):
        self.assertEqual(self.g.judge("acde", "ACDE"), "correct")
        self.assertEqual(self.g.judge("dcae", "ACDE"), "correct")   # 顺序无关

    def test_truncates_chinese_reasoning(self):
        """bug ②：『B；思路：…XBARR 图…』的 A/B 不得被抓成选项。

        真源（10-05 第 5 题）：XBARR 的 X/B/A/R/R 里 A、B 在 A-H 内，
        不截断就会把已答对的 `B` 判成 `AB` → 误判。
        """
        raw = "B；思路：这题和 XBARR 图的差异我还没想清楚"
        self.assertEqual(self.g.letters(raw), "B")
        self.assertEqual(self.g.judge(raw, "B"), "correct")

    def test_partial_selection_is_wrong(self):
        """漏选直接判错（Jason 的多选薄弱点）。"""
        self.assertEqual(self.g.judge("A", "AB"), "wrong")
        self.assertEqual(self.g.judge("ABC", "AB"), "wrong")

    def test_blank_is_wrong(self):
        self.assertEqual(self.g.judge("", "AB"), "wrong")
        self.assertEqual(self.g.judge("   ", "AB"), "wrong")
        self.assertEqual(self.g.judge("不知道", "AB"), "wrong")

    def test_letters_dedup_and_sort(self):
        self.assertEqual(self.g.letters("bbaa"), "AB")
        self.assertEqual(self.g.letters("D.A.C"), "ACD")

    def test_split_re_is_injected(self):
        """★ 内核不预设中文分隔符：换一个 split_re，结果就变。"""
        g_no_split = LetterSetGrader(split_re=re.compile(r"(?!)"))   # 永不匹配
        raw = "B；思路：XBARR"
        self.assertEqual(self.g.judge(raw, "B"), "correct")
        self.assertEqual(g_no_split.judge(raw, "B"), "wrong",
                         "不截断时 A/B 被抓出 → 证明分隔符是注入的，非内核写死")

    def test_alphabet_is_injected(self):
        """★ 内核不预设只有 A–H：字母范围也可注入。"""
        narrow = LetterSetGrader(split_re=SPLIT_BBPREP, alphabet_re="A-Da-d")
        self.assertEqual(self.g.letters("E"), "E")
        self.assertEqual(narrow.letters("E"), "",
                         "窄表下 E 不合法 → 证明字母范围是注入的")


class TestTrueFalseGrader(unittest.TestCase):
    """判断题。只取第一个判断词（附注不得干扰）。"""

    def setUp(self):
        self.g = TrueFalseGrader(split_re=SPLIT_BBPREP,
                                 true_tokens=TF_TRUE, false_tokens=TF_FALSE)

    def test_basic(self):
        self.assertEqual(self.g.judge("对", "对"), "correct")
        self.assertEqual(self.g.judge("错", "对"), "wrong")
        self.assertEqual(self.g.judge("√", "对"), "correct")
        self.assertEqual(self.g.judge("×", "对"), "wrong")

    def test_first_token_wins_over_annotation(self):
        """『对，但……思路…』判对 —— 只认第一个判断词。"""
        self.assertEqual(self.g.judge("对，但我不确定思路对不对", "对"), "correct")
        self.assertEqual(self.g.judge("错；思路：我猜是错的", "错"), "correct")

    def test_offvocabulary_is_wrong(self):
        self.assertEqual(self.g.judge("不太清楚", "对"), "wrong")
        self.assertEqual(self.g.judge("", "对"), "wrong")

    def test_tokens_are_injected(self):
        """★ 真值词表是注入的：换成英文词表，中文『对』即失配。"""
        g_en = TrueFalseGrader(split_re=SPLIT_BBPREP,
                               true_tokens={"true", "t"}, false_tokens={"false", "f"})
        self.assertEqual(self.g.judge("对", "对"), "correct")
        self.assertEqual(g_en.judge("对", "对"), "wrong",
                         "英文词表下『对』不在表内 → 证明词表是注入的")


class TestNumericGrader(unittest.TestCase):
    """计算题：数值 + 绝对容差（含逐题 tol）。"""

    def setUp(self):
        self.g = NumericGrader(num_re=NUM_RE)

    def test_within_tolerance(self):
        self.assertEqual(self.g.judge("0.05", "0.05"), "correct")
        self.assertEqual(self.g.judge("0.055", "0.05"), "correct")   # 容差 0.01
        self.assertEqual(self.g.judge("0.07", "0.05"), "wrong")

    def test_thousands_separator_stripped(self):
        self.assertEqual(self.g.judge("1,234.5", "1234.5"), "correct")

    def test_per_item_tolerance(self):
        self.assertEqual(self.g.judge("0.06", {"answer": "0.05", "tol": 0.001}), "wrong")
        self.assertEqual(self.g.judge("0.0505", {"answer": "0.05", "tol": 0.001}), "correct")

    def test_tol_falsy_falls_back_to_default(self):
        """⚠️ 真源 `float(x or 0.01)`：tol 为 falsy（`0` / `""`）时**回退默认**，
        不当成"零容差"。逐字等价，不"顺手修"。"""
        self.assertEqual(self.g.judge("0.06", {"answer": "0.05", "tol": 0}), "correct")
        self.assertEqual(self.g.judge("0.06", {"answer": "0.05", "tol": ""}), "correct")

    def test_bad_key_is_wrong(self):
        self.assertEqual(self.g.judge("1", "无数字"), "wrong")

    def test_reasoning_numbers_also_compared(self):
        """⚠️ **真源既有语义，保持等价、不"顺手修"**：calc **不截断思路**，
        思路里出现的数字也参与比对。故「答案写错但思路里恰好算了正确值」会判对。
        """
        raw = "0.07；思路：我先算到 0.05 又改了口径"
        self.assertEqual(self.g.judge(raw, "0.05"), "correct",
                         "真源不截断 → 思路里的 0.05 也算命中（既有语义）")


class TestKeywordGrader(unittest.TestCase):
    """要点题：关键词全含。"""

    def setUp(self):
        self.g = KeywordGrader()

    def test_all_keywords_required(self):
        self.assertEqual(self.g.judge("先做 MSA 再评估过程能力", "MSA|过程能力"), "correct")
        self.assertEqual(self.g.judge("只做了 MSA", "MSA|过程能力"), "wrong")

    def test_whitespace_insensitive(self):
        self.assertEqual(self.g.judge("先做 M S A", "MSA"), "correct")

    def test_empty_keywords_is_wrong(self):
        self.assertEqual(self.g.judge("随便写点什么", ""), "wrong")

    def test_sep_is_injected(self):
        """★ 关键词分隔符是注入的。"""
        g_comma = KeywordGrader(sep_re=r",")
        self.assertEqual(self.g.judge("甲乙", "甲|乙"), "correct")   # 两个关键词都命中
        self.assertEqual(g_comma.judge("甲乙", "甲|乙"), "wrong",
                         "逗号分隔下『甲|乙』是一个整体词 → 证明分隔符注入")


class TestScheduleContract(unittest.TestCase):
    """状态机与 LADDER 注入。"""

    def test_ladder_injection(self):
        """LADDER 必须可注入（两项目不同）。"""
        short = [1, 2, 4]
        stage, state, gap = next_schedule(0, True, ladder=short)
        self.assertEqual((stage, state, gap), (1, "learning", 2))
        _, state2, _ = next_schedule(5, True, ladder=short)
        self.assertEqual(state2, "mastered")

    def test_wrong_lapses(self):
        stage, state, gap = next_schedule(3, False)
        self.assertEqual((stage, state, gap), (1, "lapsed", 1))
        stage0, state0, _ = next_schedule(1, False)
        self.assertEqual((stage0, state0), (0, "lapsed"))


class TestStateMachineBoundary(unittest.TestCase):
    """B4：`new` 是哨兵，不入状态机。"""

    def test_pool_new_not_in_states(self):
        from ..model import STATES
        self.assertNotIn(POOL_NEW, STATES,
                         "POOL_NEW 不得出现在 STATES（它是哨兵不是状态）")
        self.assertEqual(POOL_NEW, "new")


class TestFrontIOParse(unittest.TestCase):
    """frontmatter 解析（vault）。"""

    def test_parse(self):
        text = "---\nid: x-01\nstage: 2\nstate: review\ndue: 2026-10-11\n---\n正文"
        fm = parse_front(text)
        self.assertEqual(fm["id"], "x-01")
        self.assertEqual(fm["stage"], "2")
        self.assertEqual(fm["state"], "review")

    def test_no_front(self):
        self.assertEqual(parse_front("没有 frontmatter"), {})


class TestVaultWriteFront(unittest.TestCase):
    """A2：实装 `write_front` —— 只改已存在的键，正文一字不动。

    真源：bb-prep `src/bbcore.py:write_front`。验收判据（MVP-Backlog P1-A）：
    **改前 / 改后逐字节比对，正文零变化**。这里用固定样本把该判据钉成断言。
    """

    SAMPLE = ("---\n"
              "id: x-01\n"
              "stage: 2\n"
              "state: learning\n"
              "due: 2026-10-16\n"
              "reviews: 2\n"
              "correct: 2\n"
              "wrong: 0\n"
              "---\n"
              "## 题干\n"
              "\n"
              "正文第一行\n"
              "正文第二行\n")
    BODY = "## 题干\n\n正文第一行\n正文第二行\n"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lessonos_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.p = self.tmp / "x-01.md"
        self.p.write_text(self.SAMPLE, encoding="utf-8", newline="\n")

    # ── 核心判据：正文零变化 + 只改列出的键 ─────────────────────────────
    def test_body_untouched_and_only_listed_keys_change(self):
        write_front(self.p, {"stage": 3, "state": "review", "due": "2026-10-18",
                             "reviews": 3, "correct": 3, "wrong": 0})
        got = self.p.read_text(encoding="utf-8")
        want = ("---\n"
                "id: x-01\n"
                "stage: 3\n"
                "state: review\n"
                "due: 2026-10-18\n"
                "reviews: 3\n"
                "correct: 3\n"
                "wrong: 0\n"
                "---\n") + self.BODY
        self.assertEqual(got, want)
        # 正文逐字节零变化（独立断言，便于失败定位）
        self.assertEqual(got.split("---\n", 2)[2], self.BODY,
                         "正文必须一字不动")

    def test_unlisted_key_untouched(self):
        """未列入 updates 的键（id）必须原样保留。"""
        write_front(self.p, {"stage": 5})
        self.assertIn("\nid: x-01\n", self.p.read_text(encoding="utf-8"))

    # ── 行尾：强制 LF（仓库统一，见 .gitattributes）─────────────────────
    def test_lf_forced_no_cr(self):
        write_front(self.p, {"stage": 1})
        raw = self.p.read_bytes()
        self.assertNotIn(b"\r", raw, "不得写入 CR —— 仓库统一 LF")

    def test_lf_forced_when_source_has_crlf(self):
        """源文件是 CRLF 时，回写必须归一为 LF（否则每次写盘都产生假 diff）。"""
        self.p.write_bytes(self.SAMPLE.replace("\n", "\r\n").encode("utf-8"))
        write_front(self.p, {"stage": 4})
        self.assertNotIn(b"\r", self.p.read_bytes())

    # ── 新键：追加到末尾 ───────────────────────────────────────────────
    def test_appends_missing_key_at_end(self):
        write_front(self.p, {"note": "D5-测量/V.D.12-正态分布3σ法则"})
        got = self.p.read_text(encoding="utf-8")
        self.assertTrue(got.startswith(
            "---\nid: x-01\nstage: 2\nstate: learning\ndue: 2026-10-16\n"
            "reviews: 2\ncorrect: 2\nwrong: 0\n"
            "note: D5-测量/V.D.12-正态分布3σ法则\n---\n"), got)
        self.assertEqual(got.split("---\n", 2)[2], self.BODY)

    def test_missing_key_order_follows_updates(self):
        """多个新键按传入顺序追加（dict 保序）。"""
        write_front(self.p, {"b_key": "2", "a_key": "1"})
        tail = self.p.read_text(encoding="utf-8").split("wrong: 0\n", 1)[1]
        self.assertEqual(tail, "b_key: 2\na_key: 1\n---\n" + self.BODY)

    # ── 幂等：同参数重复调用不改变字节 ─────────────────────────────────
    def test_idempotent(self):
        upd = {"stage": 3, "state": "review"}
        write_front(self.p, upd)
        once = self.p.read_bytes()
        write_front(self.p, upd)
        self.assertEqual(once, self.p.read_bytes(), "重复写入必须幂等")

    # ── 键值写法：与真源逐字一致 ───────────────────────────────────────
    def test_value_format(self):
        write_front(self.p, {"stage": 3, "reviews": 0})
        got = self.p.read_text(encoding="utf-8")
        self.assertIn("\nstage: 3\n", got)
        self.assertIn("\nreviews: 0\n", got)

    # ── 异常路径：缺 frontmatter ───────────────────────────────────────
    def test_missing_frontmatter_raises(self):
        bad = self.tmp / "bad.md"
        bad.write_text("没有 frontmatter", encoding="utf-8")
        with self.assertRaises(ValueError):
            write_front(bad, {"stage": 1})


# ── 0.5.1：is_due 边界回归（PATCH，非 str/date 输入不得崩）──────────────────
class TestIsDueBoundary(unittest.TestCase):
    """`scheduler.is_due` 全边界回归（v0.5.1，Project Audit R1 已批）。

    判据 = **与两消费方本地 is_due 逐案一致**（bb-prep `bbcore.py:215`、
    vocab-app `review.py`，均经 as_date 归一：不可解析 → 到期）。
    dict 与 Item 两种输入形态都要覆盖（内核签名两者都吃）。
    """

    REF = dt.date(2026, 10, 13)

    def test_none_due(self):
        self.assertTrue(is_due({"due": None}, self.REF))

    def test_empty_string_due(self):
        self.assertTrue(is_due({"due": ""}, self.REF))

    def test_int_zero_due_not_crash(self):
        # 0.5.1 修复对象：此前 TypeError
        self.assertTrue(is_due({"due": 0}, self.REF))

    def test_bool_false_due_not_crash(self):
        self.assertTrue(is_due({"due": False}, self.REF))

    def test_int_nonzero_due_not_crash(self):
        self.assertTrue(is_due({"due": 1}, self.REF))

    def test_bad_string_due(self):
        self.assertTrue(is_due({"due": "garbage"}, self.REF))

    def test_past_string_due_is_due(self):
        # 语义核对：is_due = 「现在该复习了吗」—— 过去的到期日 = 已到期 = True
        self.assertTrue(is_due({"due": "2026-01-01"}, self.REF))

    def test_future_string_due_not_due(self):
        self.assertFalse(is_due({"due": "2099-01-01"}, self.REF))

    def test_past_date_object_is_due(self):
        self.assertTrue(is_due({"due": dt.date(2026, 1, 1)}, self.REF))

    def test_future_date_object_not_due(self):
        self.assertFalse(is_due({"due": dt.date(2099, 1, 1)}, self.REF))

    # ── Item（dataclass）形态：覆盖 `it.due` 属性路径（hasattr 分支）─────────
    # 审计 R1 指出原 10 例全为 dict、Item 路径零覆盖（docstring 自述不符）——
    # 此处补齐，使「dict 与 Item 两种输入形态都要覆盖」成为事实。
    def test_item_past_date_is_due(self):
        self.assertTrue(is_due(Item(id="t", due=dt.date(2026, 1, 1)), self.REF))

    def test_item_future_date_not_due(self):
        self.assertFalse(is_due(Item(id="t", due=dt.date(2099, 1, 1)), self.REF))

    def test_item_none_due(self):
        self.assertTrue(is_due(Item(id="t", due=None), self.REF))

    def test_item_int_due_not_crash(self):
        # 崩溃家族经属性路径再验一次（0.5.1 修复对象）
        self.assertTrue(is_due(Item(id="t", due=0), self.REF))


def main() -> None:
    if "--dump" in sys.argv:
        print(json.dumps(golden_output(), ensure_ascii=False, indent=2))
        return
    if "--save" in sys.argv:
        i = sys.argv.index("--save")
        path = sys.argv[i + 1] if len(sys.argv) > i + 1 else "golden.json"
        # 显式 UTF-8 + LF：Windows 下重定向 stdout 会走本地代码页，
        # 中文会变乱码；基线文件必须稳定可 diff。
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(golden_output(), ensure_ascii=False, indent=2) + "\n")
        print(f"golden 基线已写入 {path}")
        return
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print()
    if result.wasSuccessful():
        print(f"✅ golden-set 全部通过（seed={FIXED_SEED}, today={FIXED_TODAY}）")
    else:
        print("❌ golden-set 未通过 —— 内核行为已变化，须核对 ADR-0002")
        sys.exit(1)


if __name__ == "__main__":
    main()
