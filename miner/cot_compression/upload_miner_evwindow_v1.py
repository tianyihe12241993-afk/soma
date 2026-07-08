"""SOMA comp-110 — EVIDENCE-WINDOW v1 (from-scratch architecture; not in-place content compression).

DESIGN: the agent's own assistant narrative carries its conclusions; OLD tool evidence it has already
acted on is the bulk of re-sent history. This miner keeps the conversation structure intact but reduces
each OLD INTERIOR tool result to a single approved omission marker line ("stub"), while everything the
agent is actively using stays byte-verbatim:
- system / developer / user messages: NEVER touched (no instruction added, removed, or reordered).
- assistant messages (with or without tool_calls): NEVER touched (the reasoning narrative + call
  structure survive; API tool_call<->tool pairing remains valid because no message is dropped).
- the FRESH observation group: the final message plus the newest contiguous run of tool messages
  anywhere in the list — byte-verbatim.
- small tool results (<= FLOOR chars): byte-verbatim (not worth a stub).
- all OTHER interior tool results: content replaced by ONE approved marker line spanning the whole
  message ("[[CMP]] source line 1 ~ source line N Omitted [[/CMP]]", N = original line count) —
  no partial fragments, no per-gap marker menus.

Deterministic; position-independent (a message's stub depends only on its own content → byte-stable
across requests → cache-safe); fail-open; stdlib only; input never mutated; net reduction guaranteed
by FLOOR > stub length; no pin, no dedupe, no state, no steering, no task awareness.
Only added strings = the two approved omission marker templates (integers only).
"""
from __future__ import annotations

import re
from typing import Any

FLOOR = 400   # interior tool results <= FLOOR chars stay verbatim (a stub line is ~55 chars)

_NL_RX = re.compile(r"\r\n|\r|\n")


def _stub(text: str) -> str:
    n = len(_NL_RX.split(text))
    if n <= 1:
        return "[[CMP]] source line 1 [[/CMP]]\n"
    return f"[[CMP]] source line 1 ~ source line {n} Omitted [[/CMP]]\n"


def _compress_text(text: str) -> str:
    if len(text) <= FLOOR:
        return text
    s = _stub(text)
    return s if len(s) < len(text) else text


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
        # ONLY interior tool results are ever touched; every other role/message passes through as-is.
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
            joined = "".join(p.get("text", "") for p in content if isinstance(p, dict) and isinstance(p.get("text"), str))
            if len(joined) > FLOOR:
                msg = dict(msg)
                msg["content"] = _stub(joined)
            out.append(msg)
        else:
            out.append(msg)
    return out
