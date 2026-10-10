"""出卷（项目策略）。bb-prep 风格：到期优先 + 九域权重 + 近期去重 + 真题优先。

抽题规则因项目而异（bb-prep `pick_items` vs vocab-app `pick_words` 签名不同）
-> 用策略接口，不塞进内核。本文件给出共享骨架与 bb-prep 风格实现。

⚠️ 全部「项目数据」一律**显式注入**（形参），内核不读项目文件、不含隐式默认。
   这是 2026-10-11 裁决 B2 的结果：早期版本用 `getattr(self, "_recent", set())`
   与恒返回 `{}` 的 `_history_counts()`，导致「去重/权重」是空转的假能力。
"""
from __future__ import annotations

import datetime as dt
import random

from .model import DEFAULT_LADDER, POOL_NEW


class Picker:
    """策略接口：pick(...) -> (复习题列表, 新题列表)。

    数据注入约定（全部可选，缺省 = 不启用该特性）：
      - `exclude`          : 已排除的题 id（如加练卷排除当日已出）
      - `recent`           : 近期窗口内出过的题 id（→ 新题严格剔除；见下）
      - `history_counts`   : 九域历史累计计数 {domain: n}（→ 算欠配权重）
      - `domain_weights`   : 九域目标权重 {domain: w}（→ 算欠配权重）
      - `is_exam`          : 判"是否真题"的谓词，默认按 `item["exam"]`
      - `ladder`           : 间隔阶梯（**必须注入**，两项目不同；ADR-0001）
    """

    def pick(self, review_n, new_n, items, rng, ref, *,
             exclude=None, exam_first=True, weighted=True,
             recent=None, history_counts=None, domain_weights=None,
             is_exam=None, ladder=None):
        raise NotImplementedError


class WeightedPicker(Picker):
    """bb-prep `practice.pick_items` 的共享内核化版本（逻辑同源；参数注入）。

    规则（真源：bb-prep `src/practice.py`，2026-10-11 复核）：
      - **到期题一个不丢**（spaced repetition 优先），按 due 稳定排序；
      - **近期去重**（recent gap）：`recent` 内的题**不得进新题档**；
        到期池拆 fresh/recent，**fresh 优先**，不够才回退 recent；
      - **九域欠配**作排序权重，不删题（deficit = 期望累计 − 实际累计）；
      - **真题优先**（exam_first）：新题名额优先给真题池，自建题补缺口。

    ⚠️ 已知与真源的差距（**P1-A 待补**，见 MVP-Backlog 与 audit_log B2）：
      真源的「新题贪心取 + 温和上限 `cap=⌈w/tot·n⌉+1`」尚未移入本骨架；
      当前仅按注入的 `recent`/`weighted` 过滤 + 排序。P1-A 必须补齐，
      否则卷面九域分布会与 bb-prep 现行为不同。
    """

    def pick(self, review_n, new_n, items, rng, ref, *,
             exclude=None, exam_first=True, weighted=True,
             recent=None, history_counts=None, domain_weights=None,
             is_exam=None, ladder=None):
        ladder = ladder or DEFAULT_LADDER
        exclude = exclude or set()
        recent = recent or set()
        is_exam = is_exam or _is_exam_default

        def _key(i) -> str:
            return i.get("id") or i.get("_path", "").split("/")[-1]

        pool = [i for i in items if _key(i) not in exclude]

        # 到期池拆 fresh/recent；新题池严格剔除 recent。
        _due = [i for i in pool if i.get("state", POOL_NEW) != POOL_NEW
                and _is_due(i, ref)]
        due_fresh = [i for i in _due if _key(i) not in recent]
        due_recent = [i for i in _due if _key(i) in recent]
        due = due_fresh + due_recent

        new = [i for i in pool
               if i.get("state", POOL_NEW) == POOL_NEW and _key(i) not in recent]

        # 真题优先（真源教训：此处排序后**绝不可再 shuffle(new)**，
        # 否则会把真题优先彻底冲掉 —— bb-prep practice.py 2026-10-07 实测踩坑）。
        if exam_first:
            new.sort(key=lambda i: (not is_exam(i), rng.random()))
        rng.shuffle(due)

        # 九域欠配表：只作排序权重，不删任何题。
        deficit = (_domain_deficit(history_counts or {}, domain_weights or {})
                   if weighted else {})

        def _dom(i) -> str:
            return str(i.get("domain") or "?")

        # 排序键：先「是否在近期窗口内」（fresh 优先），再 due 日期，再域欠配。
        # ⚠️ 近期去重必须作**首键** —— 否则 due 排序会覆盖 fresh 的区分。
        if weighted:
            due.sort(key=lambda i: (_key(i) in recent,
                                    _as_date(i.get("due")) or dt.date.min,
                                    -deficit.get(_dom(i), 0.0)))
        else:
            due.sort(key=lambda i: (_key(i) in recent,
                                    _as_date(i.get("due")) or dt.date.min))
        review = due[:review_n]

        fresh = new[:new_n]

        # 补位：回退池同样排除 recent 的**新题**（防"剔除后又从补位塞回"），
        # 但**到期复习题允许回退**（spaced repetition 优先于去重）。
        if len(review) + len(fresh) < review_n + new_n:
            rest = ([i for i in due[len(review):]]
                    + [i for i in new[len(fresh):] if _key(i) not in recent])
            rng.shuffle(rest)
            if exam_first:
                # 打乱后再排：同优先级内随机，同时保住真题优先。
                if weighted:
                    rest.sort(key=lambda i: (not is_exam(i),
                                             -deficit.get(_dom(i), 0.0),
                                             rng.random()))
                else:
                    rest.sort(key=lambda i: (not is_exam(i), rng.random()))
            while len(review) + len(fresh) < review_n + new_n and rest:
                it = rest.pop()
                (review if it.get("state", POOL_NEW) != POOL_NEW
                 else fresh).append(it)

        return review, fresh


# ── 内部辅助 ────────────────────────────────────────────────────────────────
# 注：日期解析已统一复用 scheduler 的语义（B6 待收敛；此处暂保持本地实现，
#     P1 会把 `_is_due` / `_as_date` 统一到一处，消除内核内四份同源实现）。
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


def _is_exam_default(it: dict) -> bool:
    """默认真题判据：frontmatter `exam: true`。项目可注入自己的谓词覆盖。"""
    return bool(it.get("exam"))


def _domain_deficit(hist: dict, weights: dict) -> dict:
    """九域欠配表 = 按权重的期望累计 − 实际累计（正数 = 欠配）。

    与 bb-prep `practice.domain_deficit` 同源。**全部由注入的数据计算**：
      - `hist`    : {domain: 已出题数}
      - `weights` : {domain: 目标权重}
    `weights` 为空 → 返回空（不加权），不猜默认权重。
    """
    if not weights:
        return {}
    n = sum(hist.values())
    t = sum(weights.values())
    if not t:
        return {}
    return {d: n * w / t - hist.get(d, 0) for d, w in weights.items()}
