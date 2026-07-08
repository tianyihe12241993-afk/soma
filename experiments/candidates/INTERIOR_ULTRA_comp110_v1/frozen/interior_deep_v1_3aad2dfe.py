"""SOMA comp-110 (CoT-Compression-5) — INTERIOR-DEEP v1 (oracle iteration: ultra-250 crushed Medium → deep-380).

DESIGN (informed by the platform screener result of our prior recency-off test, which broke
baseline-pass tasks by compressing the fresh read the agent was acting on): this compressor
NEVER touches the content the agent is about to act on, and aggressively compresses ONLY the
OLDER INTERIOR HISTORY — tool results (and assistant text without tool_calls) that the agent has
already consumed on previous turns.

RULES OF OPERATION:
- NEVER compress system / developer / user messages (instructions are preserved exactly — no
  instruction is added, removed, reordered, or rewritten).
- NEVER compress assistant messages that carry tool_calls.
- NEVER compress the FRESH tail: the final message, and, when the request ends in tool results,
  the entire trailing run of consecutive `tool` messages (parallel tool calls) — the newest reads
  the agent is acting on stay byte-verbatim.
- Older interior `tool` outputs and interior assistant text are reduced to a compact structural
  skeleton under a hard character budget: file paths first, then errors / tests / tracebacks /
  imports / signatures / diff and line-location markers, in original document order. Every omitted
  span is replaced by an approved omission marker giving its exact 1-based source-line range within
  that message, so the region remains locatable.
- WHOLE ORIGINAL LINES ONLY, kept byte-verbatim including their original line terminators
  (splitlines(keepends=True); no CRLF/CR normalization, no partial lines).
- A compressed form is emitted only on NET REDUCTION; otherwise the original text is returned.
- Interior compression is a pure function of each message's own content (position-independent),
  so a given message compresses to identical bytes on every request — the re-sent history is
  byte-stable. Deterministic; fail-open (any error returns the original messages); stdlib only;
  the input is never mutated. No pinning, no deduplication, no loop detection, no state.

COMPLIANCE: the only strings this module ever adds are the approved omission markers
`[[CMP]] source line N [[/CMP]]` and `[[CMP]] source line N ~ source line M Omitted [[/CMP]]`
(integers only). No other text is injected; no steering; no task/category/benchmark awareness;
no network or LLM calls.
"""
from __future__ import annotations

import os
import re
from typing import Any

# profile = (min_compress_chars, head_lines, tail_lines, budget_chars) — applied to INTERIOR history only.
_PROFILES = {
    "ultra":  (300, 1, 1, 250),
    "deep":   (400, 2, 1, 380),   # DEFAULT (oracle loop: ultra-250 broke Medium → loosen)
    "target": (500, 3, 1, 550),
    "safe":   (700, 5, 2, 900),
}
# FIXED profile (Codex audit: no env knob — the runtime environment must not be able to change behavior).
_PROFILE = "deep"
MIN_COMPRESS, HEAD_LINES, TAIL_LINES, BUDGET = _PROFILES[_PROFILE]
MIN_LINES = HEAD_LINES + TAIL_LINES + 2

_TERM_RX = re.compile(r"(\r\n|\r|\n)$")

_KEEP_RX = re.compile(
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
_PATH_RX = re.compile(
    r"[\w\-./]+\.(?:py|c|h|cpp|cc|js|ts|tsx|go|rs|java|rb|json|yaml|yml|toml|cfg|ini|txt|rst|md|html|css|xml)\b"
)


def _is_signal(line: str) -> bool:
    return bool(_KEEP_RX.search(line))


def _omission_marker(start_1: int, end_1: int) -> str:
    """Approved omission templates only; 1-based inclusive line numbers within THIS message."""
    if start_1 == end_1:
        return f"[[CMP]] source line {start_1} [[/CMP]]"
    return f"[[CMP]] source line {start_1} ~ source line {end_1} Omitted [[/CMP]]"


def _skeletonize(text: str) -> str:
    if len(text) <= MIN_COMPRESS:
        return text
    raw = text.splitlines(keepends=True)                          # byte-verbatim segments incl. terminators
    n = len(raw)
    if n < MIN_LINES:
        return text
    content = [_TERM_RX.sub("", seg) for seg in raw]              # terminator-stripped copies for decisions

    head_tail = set(range(min(HEAD_LINES, n))) | set(range(max(n - TAIL_LINES, 0), n))

    def _priority(i: int) -> int:
        if i in head_tail:
            return 0
        if _PATH_RX.search(content[i]):
            return 1                                             # file paths — highest-value signal
        if _is_signal(content[i]):
            return 2                                             # errors/tests/imports/signatures/locations
        return 3                                                 # bulk

    # Fill the BUDGET by priority, in document order. EVERY kept line is budget-checked → true cap.
    keep = [False] * n
    used = 0
    for tier in (0, 1, 2, 3):
        if used >= BUDGET:
            break
        for i in range(n):
            if keep[i] or _priority(i) != tier:
                continue
            cost = len(raw[i])
            if used + cost > BUDGET:
                continue
            keep[i] = True
            used += cost

    if all(keep):
        return text

    out: list[str] = []
    i = 0
    while i < n:
        if keep[i]:
            out.append(raw[i])                                    # whole original line, verbatim
            i += 1
        else:
            j = i
            while j < n and not keep[j]:
                j += 1
            out.append(_omission_marker(i + 1, j) + "\n")         # omitted original lines (i+1)..(j)
            i = j
    rendered = "".join(out)
    return rendered if len(rendered) < len(text) else text        # never a net increase


def _compressible(msg: dict) -> bool:
    role = msg.get("role")
    if role == "tool":
        return True
    if role == "assistant" and not msg.get("tool_calls"):
        return True
    return False


def _protected_indices(messages: list[Any]) -> set[int]:
    """The FRESH observation group is never compressed (Codex audit fix): the final message always,
    PLUS the NEWEST contiguous run of `tool` messages wherever it sits — so orderings like
    [..., tool(fresh), assistant] cannot expose the fresh read to compression."""
    protected: set[int] = set()
    n = len(messages)
    if not n:
        return protected
    protected.add(n - 1)
    # locate the newest tool message anywhere in the list
    last_tool = -1
    for i in range(n - 1, -1, -1):
        if isinstance(messages[i], dict) and messages[i].get("role") == "tool":
            last_tool = i
            break
    # protect its entire contiguous tool-run (parallel tool results)
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
            new_content = _skeletonize(content) if len(content) > MIN_COMPRESS else content
            if new_content != content:
                msg = dict(msg)
                msg["content"] = new_content
            out.append(msg)
        elif isinstance(content, list):
            new_parts, changed = [], False
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                    t = part["text"]
                    nt = _skeletonize(t) if len(t) > MIN_COMPRESS else t
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
