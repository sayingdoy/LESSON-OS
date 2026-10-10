"""SSOT 元数据模型：题 / 词 / 概念统一为 Item。

frontmatter 字段是三个项目的单一真源 schema（见 PLAYBOOK.md §SSOT）。
LADDER 作为**注入参数**，绝不硬编码（ADR-0001：bb-prep 与 vocab-app 的 LADDER 不同）。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

# bb-prep 默认阶梯（考试 2027-06，长间隔无意义，封顶 45 天）。
# vocab-app 用 [1, 2, 4, 7, 15, 30, 60, 120]（封顶 120 天）。
DEFAULT_LADDER = [1, 2, 4, 7, 14, 28, 45]
MASTER_STAGE = len(DEFAULT_LADDER) - 1

# 状态集合（与 bb-prep / vocab-app 同源）。
# ⚠️ 只含**能进状态机的态** —— next_schedule 的合法输出/输入域。
# 不含 "new"：那是「尚未建卡」的**哨兵**，不是 SRS 状态（见 POOL_NEW）。
STATES = ("learning", "review", "mastered", "lapsed")

# pool 分流哨兵（**不是** SRS 状态，不入 STATES）。
#
# 为什么单列：两个真源都是 `fm.setdefault("state", "new")` —— "new" 是
# 未建卡的**默认值**，卡片一旦进入调度就再也不会是 "new"。
# 但出卷要按它分池（`state == new` → 新题池；否则 → 到期复习池），
# 所以 picker 需要一个**具名常量**而非硬编码字面量（单一真源）。
#
# ⚠️ 不得把 "new" 塞进 STATES：那会让 next_schedule 的合法输入域模糊
# （传 state="new" 进状态机会得到无意义结果）。
POOL_NEW = "new"


@dataclass
class Item:
    id: str
    stage: int = 0
    state: str = POOL_NEW          # POOL_NEW(未建卡) | learning | review | mastered | lapsed
    due: Optional[dt.date] = None
    domain: str = "?"
    reviews: int = 0
    correct: int = 0
    wrong: int = 0
    extra: dict = field(default_factory=dict)   # 项目专属字段（答案形态、题型等）

    @classmethod
    def from_front(cls, fm: dict) -> "Item":
        d = fm.get("due")
        due = None
        if isinstance(d, str) and d:
            try:
                due = dt.date.fromisoformat(d[:10])
            except ValueError:
                due = None
        return cls(
            id=str(fm.get("id") or ""),
            stage=int(fm.get("stage") or 0),
            state=str(fm.get("state") or POOL_NEW),
            due=due,
            domain=str(fm.get("domain") or "?"),
            reviews=int(fm.get("reviews") or 0),
            correct=int(fm.get("correct") or 0),
            wrong=int(fm.get("wrong") or 0),
            extra={k: v for k, v in fm.items()
                   if k not in {"id", "stage", "state", "due", "domain",
                                "reviews", "correct", "wrong"}},
        )

    def to_front(self) -> dict:
        out = {
            "id": self.id,
            "stage": self.stage,
            "state": self.state,
            "due": self.due.isoformat() if self.due else "",
            "domain": self.domain,
            "reviews": self.reviews,
            "correct": self.correct,
            "wrong": self.wrong,
        }
        out.update(self.extra)
        return out
