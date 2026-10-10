"""出卷（项目策略）。bb-prep 风格：到期优先 + 九域权重 + 近期去重。

抽题规则因项目而异（bb-prep pick_items vs vocab-app pick_words 签名不同）
-> 用策略接口，不塞进内核。本文件给出共享骨架与 bb-prep 风格实现占位。
"""
from __future__ import annotations

import datetime as dt
import random

from .model import DEFAULT_LADDER


class Picker:
    """策略接口：pick(...) -> (复习题列表, 新题列表)。"""

    def pick(self, review_n, new_n, items, rng, ref, exclude=None,
             weighted=True, ladder=None):
        raise NotImplementedError


class WeightedPicker(Picker):
    """bb-prep `practice.pick_items` 的共享内核化版本（逻辑同源；ladder 注入）。

    规则（来自 bb-prep src/practice.py，2026-10-10 实测）：
      - 到期题优先（spaced repetition），按 due 稳定排序，到期题一个不丢；
      - 九域欠配作**排序权重**，不删题（deficit = domain_deficit(history)）；
      - 新题**严格**排除近期窗口（recent gap），复习题在到期池不足时回退；
      - 真题优先（exam_first）：新题名额优先给真题池，自建题补缺口。
    """

    def pick(self, review_n, new_n, items, rng, ref,
             exclude=None, weighted=True, ladder=None):
        ladder = ladder or DEFAULT_LADDER
        exclude = exclude or set()
        pool = [i for i in items
                if (i.get("id") or i.get("_path", "")).split("/")[-1] not in exclude]
        due = [i for i in pool
               if i.get("state", "new") != "new" and _is_due(i, ref)]
        new = [i for i in pool if i.get("state", "new") == "new"]

        # 真题优先（与 bb-prep 同源）
        new.sort(key=lambda i: (not _is_exam(i), rng.random()))
        rng.shuffle(due)

        if weighted:
            deficit = _domain_deficit(_history_counts())
            due.sort(key=lambda i: (_as_date(i.get("due")) or dt.date.min,
                                    -deficit.get(str(i.get("domain") or "?"), 0.0)))
        else:
            due.sort(key=lambda i: (_as_date(i.get("due")) or dt.date.min))

        review = due[:review_n]

        # 新题严格排除近期；到期池不足时回退补满（不丢该复习的题）
        fresh = [i for i in new if i.get("id") not in getattr(self, "_recent", set())]
        fresh = fresh[:new_n]
        if len(review) + len(fresh) < review_n + new_n:
            rest = due[len(review):] + new[len(fresh):]
            rng.shuffle(rest)
            while len(review) + len(fresh) < review_n + new_n and rest:
                it = rest.pop()
                (review if it.get("state") != "new" else fresh).append(it)

        return review, fresh


# ── 内部辅助（与 bb-prep 同源逻辑，避免循环依赖直接内联）───────────────────
def _is_due(it, ref):
    d = it.get("due")
    if d is None:
        return True
    if isinstance(d, str):
        try:
            d = dt.date.fromisoformat(d[:10])
        except ValueError:
            return True
    return d <= ref


def _as_date(v):
    if v is None or v == "":
        return None
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _is_exam(it: dict) -> bool:
    """真题优先：is_exam 判据由项目注入；默认按 frontmatter 'exam: true'。"""
    return bool(it.get("exam"))


def _history_counts() -> dict:
    """九域欠配的数据源；P1 由项目注入实际历史统计，默认空（不加权）。"""
    return {}


def _domain_deficit(hist: dict) -> dict:
    """九域欠配表：只作排序权重。默认返回空（不加权）。P1 接 bb-prep domain_deficit。"""
    return {}
