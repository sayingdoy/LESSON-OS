"""出卷（项目策略）。bb-prep 风格：到期优先 + 九域权重 + 近期去重 + 真题优先。

抽题规则因项目而异（bb-prep `pick_items` vs vocab-app `pick_words` 签名不同）
-> 用策略接口，不塞进内核。本文件给出共享骨架与 bb-prep 风格实现。

⚠️ 全部「项目数据」一律**显式注入**（形参），内核不读项目文件、不含隐式默认。
   这是 2026-10-11 裁决 B2 的结果：早期版本用 `getattr(self, "_recent", set())`
   与恒返回 `{}` 的 `_history_counts()`，导致「去重/权重」是空转的假能力。
"""
from __future__ import annotations

import datetime as dt
import math
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

    ✅ **A4 已补（2026-10-13）**：真源的「**新题按域缺口贪心取 + 温和上限
       `cap = ⌈w/tot·n⌉ + 1`**」已移入（真源 `src/practice.py:181-217`，
       `pick_items` 的 `weighted` 分支），本类与 bb-prep 在此项上**行为同源**。

    ⚠️ **与真源的剩余已知差异**（A3 前须裁决；见 MVP-Backlog）：
       池不足时的**补位分支**语义不同 ——
       内核按 `item["state"]` 把候选题**路由回** `review`/`fresh` 两档；
       真源 `pick_items` 的收尾是 `fresh += rest[:need]`（**一律并入 `fresh`**）。
       该差异**仅在候选池不足时触发**，golden-set 不覆盖此路径。
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

        # ── 新题档：按域缺口贪心取 + 温和上限（A4，2026-10-13）────────────────
        # 真源：bb-prep `src/practice.py:181-217`（`pick_items` 的 weighted 分支）。
        #
        # 为什么「贪心」和「上限」必须并用（真源实测教训，勿删）：
        #   · 纯随机取新题 → 长期出题分布与官方大纲脱节（实测 D2-过程管理一次都没出过）；
        #   · 只按欠配贪心 → 某个长期欠练的域会在**单卷**里独占（实测单卷 D6 占 41.7%）；
        #   故：先在上限内挑「欠配最多」的域，**全部触顶才放开上限**
        #       （宁可覆盖不足，也不留空位）。
        # 上限 = ⌈目标占比 × 本卷题量⌉ + 1；**已入选的复习题先计入 `cur`**，
        # 避免复习题已经覆盖的域再被重复倾斜。
        #
        # ⚠️ rng 消耗顺序必须与真源严格一致（A3 逐字节比对的前提）：
        #    exam_first 排序 → `shuffle(due)` → 本循环（每次候选比较各取一次 random）。
        if weighted:
            n_sheet = review_n + new_n
            tot = sum((domain_weights or {}).values())
            cap = ({d: max(1, math.ceil(w / tot * n_sheet) + 1)
                    for d, w in (domain_weights or {}).items()} if tot else {})
            run = dict(deficit)               # 运行中的欠配量（复习题入选即扣减）
            cur: dict[str, int] = {}          # 运行中的各域已占名额
            for i in review:
                d = _dom(i)
                run[d] = run.get(d, 0.0) - 1.0
                cur[d] = cur.get(d, 0) + 1
            chosen: list[dict] = []
            used: set[str] = set()
            for _ in range(new_n):
                cand = [i for i in new if _key(i) not in used]
                if not cand:
                    break
                # 先在上限内挑；全部触顶就去掉上限（宁可覆盖不足也不留空位）
                pool_c = [i for i in cand
                          if cur.get(_dom(i), 0) < cap.get(_dom(i), 99)]
                best = max(pool_c or cand,
                           key=lambda i: (run.get(_dom(i), 0.0),
                                          bool(is_exam(i)), rng.random()))
                chosen.append(best)
                used.add(_key(best))
                d = _dom(best)
                run[d] = run.get(d, 0.0) - 1.0
                cur[d] = cur.get(d, 0) + 1
            fresh = chosen
        else:
            # 不加权：退回旧行为（保持 `new` 的「真题优先」前缀，**不得再 shuffle**）
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
