"""SOMA comp-110 — CAPLADDER v2b (tightened knobs: floor+head 1200, min-run 5; structure-preserving interior compression; fixes f1km's salience defect).

f1km's salience matched nearly every line of source code (paths/line-numbers/test tokens appear
everywhere), so big interior file reads were returned UNCHANGED (net-reduction guard) and savings capped
low. v2 keeps STRUCTURE, drops BULK: ordinary indented code bodies, comments, docstrings and blank runs
are removed as CONTIGUOUS blocks (one approved marker per block, no marker menus), while every
structural / diagnostic line survives verbatim.

NEVER touched: system/developer/user messages; assistant messages (incl. tool_calls — structure intact);
the FRESH observation group (final message + newest contiguous run of tool messages anywhere in the
list); interior tool results <= FLOOR chars; search/grep-style outputs (hit lines are self-salient).

KEPT verbatim inside big old interior reads (generic rules only — NO task/oracle awareness):
imports, decorators, top-level and shallow class/def signatures (raw or numbered `N.` view form),
grep-style `path:line` hits, `File "...", line N` frames, Traceback/Error/Exception/FAILED/assert lines,
a verbatim HEAD (~2k chars) and small TAIL. Only contiguous non-salient runs of >= MIN_RUN lines are
dropped, each replaced by ONE approved omission marker carrying its exact 1-based source-line range.

WHOLE ORIGINAL LINES ONLY, byte-verbatim incl. terminators; emitted only on NET REDUCTION; deterministic;
position-independent (cache-stable); fail-open; stdlib only; input never mutated; no pin/dedupe/state.
Only added strings = the two approved omission marker templates (integers only).
"""
from __future__ import annotations

import re
from typing import Any

# ── knobs (fixed constants; runtime env cannot change behavior) ──
FLOOR = 1200
HEAD_BUDGET = 1200
TAIL_LINES = 3
MIN_RUN = 5

_TERM_RX = re.compile(r"(\r\n|\r|\n)$")

# structure/diagnostic salience — narrow anchors; `N.`-numbered view output handled via optional prefix
_NUM = r"(?:\s*\d+[.:]?\s+)?"
_SALIENT_RX = re.compile(
    r"""(?x)
      ^%(n)s(?:async\s+)?def\s+\w+            # function signatures (top-level or numbered)
    | ^%(n)sclass\s+\w+                       # class signatures
    | ^%(n)s@\w[\w.]*                         # decorators
    | ^%(n)s(?:from\s+[\w.]+\s+import|import)\s+\w  # imports
    | ^\s*[\w/.\\-]+\.\w{1,4}:\d+             # grep-style path:line hits
    | \bFile\s+"[^"]+",\s+line\s+\d+          # traceback frames
    | \b(?:Traceback|Error|Exception|FAILED|assert(?:ion)?\b)
    """ % {"n": _NUM},
)


def _omission_marker(start_1: int, end_1: int) -> str:
    if start_1 == end_1:
        return f"[[CMP]] source line {start_1} [[/CMP]]"
    return f"[[CMP]] source line {start_1} ~ source line {end_1} Omitted [[/CMP]]"


def _compress_text(text: str) -> str:
    if len(text) <= FLOOR:
        return text
    raw = text.splitlines(keepends=True)
    n = len(raw)
    if n < MIN_RUN + 4:
        return text
    content = [_TERM_RX.sub("", seg) for seg in raw]

    keep = [False] * n
    used = 0
    for i in range(n):                                   # verbatim head (whole lines)
        if used + len(raw[i]) > HEAD_BUDGET:
            break
        keep[i] = True
        used += len(raw[i])
    for i in range(n):                                   # structural / diagnostic lines
        if not keep[i] and _SALIENT_RX.search(content[i]):
            keep[i] = True
    for i in range(max(n - TAIL_LINES, 0), n):           # small tail
        keep[i] = True

    # re-keep short gaps: only CONTIGUOUS non-salient runs >= MIN_RUN are dropped (low marker count)
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
            out.append(raw[i])                            # whole original line, byte-verbatim
            i += 1
        else:
            j = i
            while j < n and not keep[j]:
                j += 1
            out.append(_omission_marker(i + 1, j) + "\n")
            i = j
    rendered = "".join(out)
    return rendered if len(rendered) < len(text) else text  # never a net increase


def _protected_indices(messages: list[Any]) -> set[int]:
    """Fresh observation group: final message + newest contiguous tool-run anywhere in the list."""
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


def compress_messages(
    messages: list[Any] | None = None,
    path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[Any]:
    del path, metadata
    if not isinstance(messages, list):
        return messages if isinstance(messages, list) else []
    try:
        return _pass(messages)
    except Exception:
        return messages


def _pass(messages: list[Any]) -> list[Any]:
    protected = _protected_indices(messages)
    out: list[Any] = []
    for idx, msg in enumerate(messages):
        if idx in protected or not isinstance(msg, dict) or msg.get("role") != "tool":
            out.append(msg)
            continue
        content = msg.get("content")
        if isinstance(content, str):
            new_content = _compress_text(content)
            if new_content != content:
                msg = dict(msg)
                msg["content"] = new_content
            out.append(msg)
        elif isinstance(content, list):
            new_parts, changed = [], False
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                    t = part["text"]
                    nt = _compress_text(t)
                    if nt != t:
                        part = dict(part)
                        part["text"] = nt
                        changed = True
                new_parts.append(part)
            if changed:
                msg = dict(msg)
                msg["content"] = new_parts
            out.append(msg)
        else:
            out.append(msg)
    return out
