"""frontmatter 读写（stdlib-only，regex 解析，与两项目格式一致）。

bb-prep / vocab-app 各自已有等价实现（均用正则而非 yaml 库）；本文件是抽出的共享版。
P1 落地：合并两项目既有 writer 进内核，保持字段定位按表头名（不写死下标）。
"""
from __future__ import annotations

import datetime as dt
import re

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_front(text: str) -> dict:
    """解析 YAML frontmatter 为 dict。列表值 [a, b] -> list；空值 -> ''。"""
    m = FM_RE.match(text)
    if not m:
        return {}
    data: dict = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            data[k] = [x.strip() for x in inner.split(",")] if inner else []
        else:
            data[k] = v
    return data


def write_front(path, updates: dict) -> None:
    """原地更新 frontmatter 字段。

    ⚠️ P1 占位：bb-prep/vocab-app 已有等价实现，合并进内核时须：
      - 按表头名定位字段（列数会演进，禁止写死下标）；
      - 保留显式 LF 行尾（bb-prep 铁律 21）；
      - 不触碰正文、不污染题干/选项/解析。
    未注入具体 writer 前抛 NotImplemented，保持内核零依赖。
    """
    raise NotImplementedError(
        "write_front 为 P1 占位：请注入项目既有 frontmatter writer "
        "（bb-prep src/bbcore.py write_front / vocab-app src/review.py write_front）。"
    )


def as_date(v):
    """宽松解析日期：None/空 -> None；date -> 原样；str -> 取前 10 位 ISO。"""
    if v is None or v == "":
        return None
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None
