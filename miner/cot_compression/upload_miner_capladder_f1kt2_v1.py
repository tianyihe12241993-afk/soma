"""SOMA comp-110 (CoT-Compression-5) — INTERIOR-CAP ladder — f1kt2 (floor 700, salience budget 1000).

Philosophy (comp-108 champion cap32+pin, adapted): LIGHT-TOUCH. Small/medium tool results pass through
VERBATIM below a floor; only OVERSIZED INTERIOR history is trimmed, salience-preserving — never
skeletonized to a tiny budget. The content the agent is actively acting on is never touched.

RULES:
- NEVER compress system / developer / user messages (no instruction is added, removed, reordered,
  or rewritten). NEVER compress assistant messages carrying tool_calls.
- NEVER compress the FRESH observation group: the final message, plus the newest contiguous run of
  `tool` messages wherever it sits (parallel tool results) — the reads the agent is acting on stay
  byte-verbatim.
- Interior tool results (and interior assistant text) with len <= FLOOR pass through VERBATIM.
- Oversized interior content keeps: a verbatim HEAD run of whole lines up to FLOOR chars, then ALL
  salient lines (file paths, errors, failing tests, tracebacks, imports, function/class signatures,
  decorators, diffs, line/location references), then a small verbatim TAIL. Every omitted span is
  replaced by an approved omission marker with its exact 1-based source-line range in this message.
- WHOLE ORIGINAL LINES ONLY, byte-verbatim incl. original terminators (no CRLF/CR normalization,
  no partial lines). Emitted only on NET REDUCTION. Deterministic; position-independent (a message
  compresses to identical bytes on every request → re-sent history is byte-stable/cache-safe);
  fail-open; stdlib only; input never mutated. No pin, no dedupe, no state, no loop detection.

COMPLIANCE: the only strings ever added are the approved omission markers
`[[CMP]] source line N [[/CMP]]` and `[[CMP]] source line N ~ source line M Omitted [[/CMP]]`
(integers only). No steering, no task/category/benchmark awareness, no network or LLM calls.
"""
from __future__ import annotations

import re
from typing import Any

# ── ladder knob (fixed constant; the runtime environment cannot change behavior) ──
FLOOR = 700
SALIENT_BUDGET = 1000  # tight2: salience keeps capped (document order)
TAIL_LINES = 3        # small verbatim tail kept on trimmed oversized content

_TERM_RX = re.compile(r"(\r\n|\r|\n)$")

_SALIENT_RX = re.compile(
    r"""(?x)
      (?: \bFile\s+"[^"]+",\s+line\s+\d+ )
    | (?: \b(?:Traceback|Error|Exception|error\[|E\s{3,}|FAILED|PASSED|ERROR|WARNING|assert(?:ion)?\b) )
    | (?: \btests?[_/][\w./-]+ | \btest_\w+ )
    | (?: ^\s*[+\-@]{1,3}(?:\s|$) | ^\s*diff\s | ^\s*index\s | ^\s*---\s | ^\s*\+\+\+\s )
    | (?: ^\s*(?:async\s+)?def\s+\w+ | ^\s*class\s+\w+ | ^\s*@\w[\w.]* )
    | (?: ^\s*(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*()]+ )
    | (?: [\w\-./]+\.(?:py|c|h|cpp|cc|js|ts|tsx|go|rs|java|rb|json|yaml|yml|toml|cfg|ini|txt|rst|md|html|css|xml)\b )
    | (?: \bline\s+\d+\b | :\d+:\d* )
    """,
    re.M,
)


def _omission_marker(start_1: int, end_1: int) -> str:
    """Approved omission templates only; 1-based inclusive line numbers within THIS message."""
    if start_1 == end_1:
        return f"[[CMP]] source line {start_1} [[/CMP]]"
    return f"[[CMP]] source line {start_1} ~ source line {end_1} Omitted [[/CMP]]"


def _cap_interior(text: str) -> str:
    """Champion-style trim for OVERSIZED interior content: verbatim head run up to FLOOR chars,
    then all salient lines, then a small tail; omitted spans -> exact line-range markers."""
    if len(text) <= FLOOR:
        return text
    raw = text.splitlines(keepends=True)
    n = len(raw)
    if n < 4:
        return text
    content = [_TERM_RX.sub("", seg) for seg in raw]

    keep = [False] * n
    used = 0
    for i in range(n):                          # verbatim HEAD run (whole lines) up to FLOOR chars
        cost = len(raw[i])
        if used + cost > FLOOR:
            break
        keep[i] = True
        used += cost
    sal_used = 0                                # salient lines survive up to SALIENT_BUDGET (document order)
    for i in range(n):
        if keep[i] or not _SALIENT_RX.search(content[i]):
            continue
        cost = len(raw[i])
        if sal_used + cost > SALIENT_BUDGET:
            continue
        keep[i] = True
        sal_used += cost
    for i in range(max(n - TAIL_LINES, 0), n):  # small verbatim tail
        keep[i] = True

    if all(keep):
        return text

    out: list[str] = []
    i = 0
    while i < n:
        if keep[i]:
            out.append(raw[i])                  # whole original line, byte-verbatim
            i += 1
        else:
            j = i
            while j < n and not keep[j]:
                j += 1
            out.append(_omission_marker(i + 1, j) + "\n")
            i = j
    rendered = "".join(out)
    return rendered if len(rendered) < len(text) else text      # never a net increase


def _compressible(msg: dict) -> bool:
    role = msg.get("role")
    if role == "tool":
        return True
    if role == "assistant" and not msg.get("tool_calls"):
        return True
    return False


def _protected_indices(messages: list[Any]) -> set[int]:
    """The FRESH observation group is never compressed: the final message always, PLUS the newest
    contiguous run of `tool` messages wherever it sits (covers [..., tool(fresh), assistant])."""
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
        if idx in protected or not isinstance(msg, dict) or not _compressible(msg):
            out.append(msg)
            continue
        content = msg.get("content")
        if isinstance(content, str):
            new_content = _cap_interior(content)
            if new_content != content:
                msg = dict(msg)
                msg["content"] = new_content
            out.append(msg)
        elif isinstance(content, list):
            new_parts, changed = [], False
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                    t = part["text"]
                    nt = _cap_interior(t)
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
