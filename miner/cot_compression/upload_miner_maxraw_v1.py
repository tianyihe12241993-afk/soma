"""SOMA comp-110 — MAXRAW v1 (position-dependent aggression; score = RAW-savings driven).

Insight (verified from upstream scoring.py): the swebench SCORE = mean of per-task
1 + 0.5·trim(ln(RAW_baseline / RAW_miner)) — monotonic in RAW token savings up to ~86%, and CACHE-STABILITY
is irrelevant to the score (it only matters for the qualify GATE, which we already clear). So the two
levers are (1) maximize raw savings, (2) zero per-run breaks. Prior candidates were position-INDEPENDENT
to protect the cache — unnecessary. This candidate is POSITION-DEPENDENT: keep the agent's RECENT working
set full (no break risk) and CRUSH the OLD stale interior history hard (max raw savings).

NEVER touched: system/developer/user; assistant messages (incl. tool_calls); the FRESH observation group
(final message + newest contiguous tool-run anywhere).
RECENT window: the newest RECENT_TOOLS interior tool results are kept at a LIGHT floor (working set intact).
OLD interior tool results: compressed HARD to a structural skeleton (imports/defs/classes/decorators/
tracebacks/errors/paths/line-refs + a tiny head/tail), contiguous non-salient runs dropped to one approved
marker each. Grep/search outputs (self-salient path:line hits) preserved.

WHOLE ORIGINAL LINES ONLY, byte-verbatim incl. terminators; emitted only on NET REDUCTION; deterministic
(pure function of the message list + positions); fail-open (non-list/errors return input untouched);
stdlib only; input never mutated; no pin/dedupe/state. Only added strings = the two approved [[CMP]] templates.
"""
from __future__ import annotations

import re
from typing import Any

RECENT_TOOLS = 4          # newest N interior tool results kept LIGHT (agent's active working set)
LIGHT_FLOOR = 1200        # recent interior reads <= this pass verbatim; larger kept mostly intact
LIGHT_HEAD = 1200
OLD_FLOOR = 350           # OLD interior reads <= this pass verbatim (a marker line is ~55 chars)
OLD_HEAD = 300            # verbatim head on crushed old reads
TAIL_LINES = 2
MIN_RUN = 4

_TERM_RX = re.compile(r"(\r\n|\r|\n)$")
_SALIENT_RX = re.compile(
    r"""(?x)
      ^(?:\s*\d+[.:]?\s+)?(?:async\s+)?def\s+\w+
    | ^(?:\s*\d+[.:]?\s+)?class\s+\w+
    | ^(?:\s*\d+[.:]?\s+)?@\w[\w.]*
    | ^(?:\s*\d+[.:]?\s+)?(?:from\s+[\w.]+\s+import|import)\s+\w
    | ^\s*[\w/.\\-]+\.\w{1,4}:\d+
    | \bFile\s+"[^"]+",\s+line\s+\d+
    | \b(?:Traceback|Error|Exception|FAILED|assert(?:ion)?\b)
    """,
)


def _omission_marker(a: int, b: int) -> str:
    return f"[[CMP]] source line {a} [[/CMP]]" if a == b else f"[[CMP]] source line {a} ~ source line {b} Omitted [[/CMP]]"


def _compress(text: str, floor: int, head: int) -> str:
    if len(text) <= floor:
        return text
    raw = text.splitlines(keepends=True)
    n = len(raw)
    if n < MIN_RUN + 3:
        return text
    content = [_TERM_RX.sub("", s) for s in raw]
    keep = [False] * n
    used = 0
    for i in range(n):
        if used + len(raw[i]) > head:
            break
        keep[i] = True
        used += len(raw[i])
    for i in range(n):
        if not keep[i] and _SALIENT_RX.search(content[i]):
            keep[i] = True
    for i in range(max(n - TAIL_LINES, 0), n):
        keep[i] = True
    i = 0
    while i < n:
        if keep[i]:
            i += 1
            continue
        j = i
        while j < n and not keep[j]:
            j += 1
        if j - i < MIN_RUN:
            for k in range(i, j):
                keep[k] = True
        i = j
    if all(keep):
        return text
    out: list[str] = []
    i = 0
    while i < n:
        if keep[i]:
            out.append(raw[i]); i += 1
        else:
            j = i
            while j < n and not keep[j]:
                j += 1
            out.append(_omission_marker(i + 1, j) + "\n")
            i = j
    r = "".join(out)
    return r if len(r) < len(text) else text


def _protected_indices(messages: list[Any]) -> set[int]:
    protected: set[int] = set()
    n = len(messages)
    if not n:
        return protected
    protected.add(n - 1)
    last_tool = -1
    for i in range(n - 1, -1, -1):
        if isinstance(messages[i], dict) and messages[i].get("role") == "tool":
            last_tool = i
            break
    i = last_tool
    while i >= 0 and isinstance(messages[i], dict) and messages[i].get("role") == "tool":
        protected.add(i)
        i -= 1
    return protected


def compress_messages(messages: list[Any] | None = None, path: str | None = None, metadata: dict[str, Any] | None = None) -> list[Any]:
    del path, metadata
    if not isinstance(messages, list):
        return messages
    try:
        return _pass(messages)
    except Exception:
        return messages


def _pass(messages: list[Any]) -> list[Any]:
    protected = _protected_indices(messages)
    # index interior tool messages newest->oldest; the newest RECENT_TOOLS get the LIGHT profile
    tool_idxs = [i for i, m in enumerate(messages)
                 if i not in protected and isinstance(m, dict) and m.get("role") == "tool"]
    recent = set(tool_idxs[-RECENT_TOOLS:]) if RECENT_TOOLS else set()
    out: list[Any] = []
    for idx, msg in enumerate(messages):
        if idx in protected or not isinstance(msg, dict) or msg.get("role") != "tool":
            out.append(msg)
            continue
        floor, head = (LIGHT_FLOOR, LIGHT_HEAD) if idx in recent else (OLD_FLOOR, OLD_HEAD)
        content = msg.get("content")
        if isinstance(content, str):
            nc = _compress(content, floor, head)
            if nc != content:
                msg = dict(msg); msg["content"] = nc
            out.append(msg)
        elif isinstance(content, list):
            parts, changed = [], False
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                    t = part["text"]; nt = _compress(t, floor, head)
                    if nt != t:
                        part = dict(part); part["text"] = nt; changed = True
                parts.append(part)
            if changed:
                msg = dict(msg); msg["content"] = parts
            out.append(msg)
        else:
            out.append(msg)
    return out
