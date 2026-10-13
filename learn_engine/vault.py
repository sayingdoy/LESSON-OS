"""frontmatter 读写（stdlib-only，regex 解析，与两项目格式一致）。

bb-prep / vocab-app 各自已有等价实现（均用正则而非 yaml 库）；本文件是抽出的共享版。
P1-A2 已落地：`write_front` 由占位转为实装（真源 bb-prep `src/bbcore.py:write_front`），
保持**按键名定位**（不写死下标）、**正文一字不动**、**强制 LF 行尾**。
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

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
    """原地更新 frontmatter 字段（P1-A2 实装）。

    真源：bb-prep `src/bbcore.py:write_front`（2026-10-13 逐行核对，逻辑同源；
    vocab-app `src/review.py` 为同形实现）。规则：

      - **只改已存在的键**（按键名定位，**不写死行下标** —— 字段列数会演进）；
      - `updates` 里**新增的键追加到 frontmatter 末尾**（顺序 = 传入 dict 序）；
      - **正文一字不动**：`text[m.end():]` 原样回写，不污染题干/选项/解析；
      - 行尾**强制 LF**（`newline="\\n"`）。Windows 文本模式会把 `\\n` 写成
        `\\r\\n`，而仓库统一 LF（bb-prep `.gitattributes`）；不固定行尾会让每次
        挂链/挂图都把整个文件标记成「已修改」，真实 diff 被噪声淹没。
      - 键值写法与真源**逐字一致**：`f"{key}: {value}"`。

    ⚠️ 与真源的**唯一差异**：缺 frontmatter 时本函数抛 `ValueError`（库语义，
       可被调用方捕获）；真源抛 `SystemExit`（脚本语义）。该路径为异常路径，
       正常调用（文件必含 frontmatter）不触发。
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        raise ValueError(f"文件缺少 frontmatter: {p}")
    lines = m.group(1).splitlines()
    seen = set()
    for i, line in enumerate(lines):
        if ":" not in line or line.startswith(" "):
            continue
        key = line.split(":", 1)[0].strip()
        if key in updates:
            lines[i] = f"{key}: {updates[key]}"
            seen.add(key)
    for key, val in updates.items():
        if key not in seen:
            lines.append(f"{key}: {val}")
    p.write_text("---\n" + "\n".join(lines) + "\n---\n" + text[m.end():],
                 encoding="utf-8", newline="\n")


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
