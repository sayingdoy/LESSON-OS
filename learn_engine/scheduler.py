"""SRS 调度：状态机 + is_due。LADDER 注入，FSRS 留可插拔接口。

逻辑与 bb-prep `bbcore.apply_result` / vocab-app `review.next_schedule` 同源
（2026-10-10 核对），唯一差异是间隔长度由注入的 ladder 决定。
"""
from __future__ import annotations

import datetime as dt

from .model import DEFAULT_LADDER, MASTER_STAGE


def is_due(it, ref: dt.date) -> bool:
    """到期判定（与 bb-prep/vocab-app 同名同形）。due 为空或 <= ref 即到期。"""
    d = it.due if hasattr(it, "due") else it.get("due")
    if d is None:
        return True
    if isinstance(d, str):
        try:
            d = dt.date.fromisoformat(d[:10])
        except ValueError:
            return True
    return d <= ref


def next_schedule(old_stage: int, correct: bool, ladder=None) -> tuple[int, str, int]:
    """纯函数状态机（与两项目同源逻辑）。

    correct -> min(stage+1, MS); state = mastered if >=MS else (review if >=3 else learning)
    wrong   -> max(0, stage-2), 'lapsed', gap=1
    ladder 必须注入（两项目不同）。返回 (new_stage, new_state, gap_days)。
    """
    ladder = ladder or DEFAULT_LADDER
    ms = len(ladder) - 1
    if correct:
        stage = min(old_stage + 1, ms)
        state = "mastered" if stage >= ms else ("review" if stage >= 3 else "learning")
        gap = ladder[min(stage, ms)]
    else:
        stage = max(0, old_stage - 2)
        state = "lapsed"
        gap = 1
    return stage, state, gap


def apply_result(item: dict, correct: bool, ladder=None, *,
                 write_front=None, today: dt.date | None = None) -> dict:
    """更新某条目 frontmatter 的 stage/state/due（纯逻辑 + 可选 IO）。

    - item: 含 stage/correct/wrong/reviews/due 的 dict（调用方从文件读取）
    - write_front: 注入的写入器 (updates: dict) -> None；为 None 则只返回更新 dict，不写盘
      （保持内核零依赖、不假定项目文件布局；bb-prep/vocab-app 各自实现后注入）
    - today: 注入「今天」，便于测试；默认 dt.date.today()

    返回更新后的字段 dict。P1 落 IO 时接 bb-prep/vocab-app 的 write_front。
    """
    ladder = ladder or DEFAULT_LADDER
    _today = today or dt.date.today()
    old = int(item.get("stage") or 0)
    c = int(item.get("correct") or 0) + (1 if correct else 0)
    x = int(item.get("wrong") or 0) + (0 if correct else 1)
    stage, state, gap = next_schedule(old, correct, ladder)
    nxt = _today + dt.timedelta(days=gap)
    upd = {
        "stage": stage,
        "state": state,
        "due": nxt.isoformat(),
        "reviews": int(item.get("reviews") or 0) + 1,
        "correct": c,
        "wrong": x,
    }
    if write_front is not None:
        write_front(upd)
    return upd


# ── FSRS 后端预留接口（P2 候选，暂不入核）────────────────────────────────────
# 未来实现：class FSRSBackend: def next_schedule(self, stability, difficulty, ...) -> (due, state)
# 在同一 next_schedule 签名下替换 LADDER 实现，单独评估、单独升版本。
