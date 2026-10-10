"""golden-set 验收脚本（ADR-0002 落地，P1-A1 第一单）。

目的：给内核变更提供**确定性回归网** —— 固定 items + 固定 `today` + 固定 `rng`，
对同一输入跑出**逐字节可比**的输出。改前 / 改后各跑一次，输出必须一致。

★ 铁律（ADR-0002 验收第 0 步）：
  **未固定 rng 时逐字节比对不成立。** 本脚本的 FIXED_SEED 是唯一随机源，
  任何测试都不得用 `Random(None)`。

用法：
  python -m learn_engine.tests.golden_set            # 跑验收（打印摘要）
  python -m learn_engine.tests.golden_set --dump     # 打印 golden 输出（供比对）

纯 stdlib `unittest`，不引 pytest（守零外部依赖铁律）。
"""
from __future__ import annotations

import datetime as dt
import json
import random
import sys
import unittest

from ..picker import WeightedPicker
from ..model import POOL_NEW, DEFAULT_LADDER
from ..scheduler import next_schedule
from ..grader import ExactMatchGrader
from ..vault import parse_front

# ── 固定常量（ADR-0002：不得临场改）────────────────────────────────────────
FIXED_SEED = 20261010
FIXED_TODAY = dt.date(2026, 10, 11)


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
        history_counts={"D5-测量": 30, "D6-分析": 10},
        domain_weights={"D1-组织开展": 10, "D2-过程管理": 7, "D5-测量": 22,
                        "D6-分析": 22, "D7-改进": 22},
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
        "main": _run_pick(items, 10, 12, recent, weighted=True),
        "no_weight": _run_pick(items, 10, 12, recent, weighted=False),
        "gap0": _run_pick(items, 10, 12, set(), weighted=True),
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


class TestJudgeContract(unittest.TestCase):
    """B1：judge 返回字符串，对齐双源。"""

    def test_returns_str(self):
        g = ExactMatchGrader()
        self.assertEqual(g.judge("hello", "hello"), "correct")
        self.assertEqual(g.judge("world", "hello"), "wrong")
        self.assertEqual(g.judge("", "hello"), "wrong")
        self.assertIsInstance(g.judge("x", "y"), str,
                              "judge 必须返回 str，不得返回 bool（B1 裁决）")


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


def main() -> None:
    if "--dump" in sys.argv:
        print(json.dumps(golden_output(), ensure_ascii=False, indent=2))
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
