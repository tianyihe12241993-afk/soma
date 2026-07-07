"""SOMA comp-110 (CoT-Compression-5) candidate: LEAN v3 — locatable-omission extractive compressor.

Same contract + compliance skeleton as LEAN v2 (upload_miner_lean_v1.py, Codex-GO sha256 163be033),
with ONE change: when it elides original lines from a code/tool/CoT block, it replaces each omitted
span with a SOURCE-LINE PROVENANCE marker instead of dropping it silently.

Why (evidence: reports/comp108_cap32pin_postmortem.md + comp110_hard_strategy.md + DISCOVERIES
2026-07-07): the DQ'd comp-108 king's Hard edge was line-number provenance — the agent knew where
kept/omitted code sat, so it edited the right lines (fewer breaks) and located fixes (more flips).
That was UNAPPROVED then. The comp-110 owners MERGED it into README §1 (2026-07-07): "when compressing
code, include a source line reference inside the marker so omitted lines remain locatable." LEAN v3
uses it. Verified allowed in the LIVE README §5.1 before building (all 15 strings; gate PASS).

Rendering (whole ORIGINAL lines kept verbatim; each maximal run of dropped lines i..j, 1-based
within the block, becomes a self-contained marker — the exact §5.1 template, numbers filled in):
  - single line:  `[[CMP]] source line N [[/CMP]]`
  - span N..M:     `[[CMP]] source line N ~ source line M Omitted [[/CMP]]`
Kept lines are NOT wrapped (they are unchanged original content); only omissions are marked. This is
cleaner than v2 (which wrapped the kept extraction) and directly matches "markers wrap omitted content".

Everything else is IDENTICAL to LEAN v2:
- Compress ONLY `tool` outputs + non-final `assistant` reasoning (the CoT). NEVER system/developer/user.
- Whole ORIGINAL lines only; content that can't be reduced by dropping whole lines is left VERBATIM.
- Quality floor: file paths / line numbers / errors / tracebacks / failing tests / diff markers /
  imports / def-class signatures ALWAYS survive.
- A marker block is emitted ONLY when the whole rendering is a NET REDUCTION vs the original.
- Tiered char budgets per profile (SOMA_LEAN_PROFILE = conservative | target | aggressive).
- Recency guard (SOMA_LEAN_RECENCY, default on): final message left verbatim. NOTE for v3: locatable
  omissions lower the break risk of compressing the freshest content, so recency MAY be reducible —
  kept toggleable for the A/B (deferred until after the first v3 smoke is reviewed).
- Deterministic (pure fn of messages+env), fail-open, NO pin, NO dedupe, stdlib only, input never mutated.

Compliance: emits ONLY README §5.1 allowed strings. The source-line markers are the exact §5.1
templates with N/M filled by real 1-based line numbers; no descriptions/counts/instructions.

⚠ COORDINATE SYSTEM (Codex audit CONCERN, documented — not fixable within the compliant template):
"source line N" is 1-based within THIS content block's own line sequence (its splitlines index), NOT
the underlying file's absolute line number. The §5.1 template is fixed and cannot be qualified with
"within block" without breaking exact-template compliance, so block-relative is the only compliant
convention. Whole-file-from-line-1 reads: block-relative == file line; partial/numbered/header'd
output diverges. This is the #1 thing to validate in the first real smoke (does the agent still
navigate + edit correctly?). Budgets are TARGETS, not hard caps (marker overhead is not pre-counted);
the net-reduction guard is the hard guarantee that output never exceeds the original.
"""
from __future__ import annotations

import os
import re
from typing import Any

_PROFILES = {
    "conservative": (16_000, 53_000, 30_000),
    "target":       (10_000, 53_000, 18_000),
    "aggressive":   (6_000,  53_000, 10_000),
}
_PROFILE = os.getenv("SOMA_LEAN_PROFILE", "target").strip().lower()
if _PROFILE not in _PROFILES:
    _PROFILE = "target"
MID_BUDGET, HUGE_THRESHOLD, HUGE_BUDGET = _PROFILES[_PROFILE]

_RECENCY = os.getenv("SOMA_LEAN_RECENCY", "1").strip() != "0"          # final-message guard; toggle for A/B
# NOTE: NO pin knob in v3 (Codex audit + user spec: "do not reintroduce pin"). "No pin" is absolute.

_HEAD_LINES = 25
_TAIL_LINES = 15
_MIN_LINES = _HEAD_LINES + _TAIL_LINES + 2

_KEEP_RX = re.compile(
    r"""(?x)
      (?: \bFile\s+"[^"]+",\s+line\s+\d+ )
    | (?: \b(?:Traceback|Error|Exception|error\[|E\s{3}|FAILED|PASSED|ERROR|WARNING|assert(?:ion)?\b) )
    | (?: \btests?[_/][\w./-]+ | \btest_\w+ )
    | (?: ^[+\-@]{1,3}(?:\s|$) | ^diff\s|^index\s|^---\s|^\+\+\+\s )
    | (?: ^\s*(?:def|class)\s+\w+ )
    | (?: ^\s*(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*]+$ )
    | (?: [\w\-./]+\.(?:py|c|h|cpp|js|ts|tsx|json|yaml|yml|toml|cfg|ini|txt|rst|md|html|css|xml)\b )
    | (?: \bline\s+\d+\b | :\d+:\d* )
    """,
    re.M,
)


def _is_signal(line: str) -> bool:
    return bool(_KEEP_RX.search(line))


def _omission_marker(start_1based: int, end_1based: int) -> str:
    """Exact README §5.1 template. Line numbers are 1-based, inclusive, within the block."""
    if start_1based == end_1based:
        return f"[[CMP]] source line {start_1based} [[/CMP]]"
    return f"[[CMP]] source line {start_1based} ~ source line {end_1based} Omitted [[/CMP]]"


def _compress_text(text: str, budget: int) -> str:
    """Keep head + quality-floor signal lines + tail within budget (dropping ONLY whole lines);
    render each dropped run as a locatable source-line omission marker. Verbatim if not reducible."""
    if len(text) <= budget:
        return text
    lines = text.splitlines()
    n = len(lines)
    if n < _MIN_LINES:
        return text

    keep = [False] * n
    for i in range(_HEAD_LINES):
        keep[i] = True
    for i in range(n - _TAIL_LINES, n):
        keep[i] = True
    used = sum(len(lines[i]) + 1 for i in range(n) if keep[i])

    for i in range(n):                        # pass 1: quality floor
        if keep[i] or not _is_signal(lines[i]):
            continue
        cost = len(lines[i]) + 1
        if used + cost > budget:
            continue
        keep[i] = True
        used += cost
    for i in range(n):                        # pass 2: fill remaining budget, document order
        if keep[i]:
            continue
        cost = len(lines[i]) + 1
        if used + cost > budget:
            continue
        keep[i] = True
        used += cost

    if all(keep):
        return text

    out: list[str] = []
    i = 0
    while i < n:
        if keep[i]:
            out.append(lines[i])
            i += 1
        else:
            j = i
            while j < n and not keep[j]:
                j += 1
            out.append(_omission_marker(i + 1, j))    # dropped run lines (i+1)..(j) 1-based inclusive
            i = j
    rendered = "\n".join(out)
    return rendered if len(rendered) < len(text) else text   # never a net increase


def _budget_for(size: int) -> int | None:
    if size <= MID_BUDGET:
        return None
    if size <= HUGE_THRESHOLD:
        return MID_BUDGET
    return HUGE_BUDGET


def _compressible(msg: dict) -> bool:
    role = msg.get("role")
    if role == "tool":
        return True
    if role == "assistant" and not msg.get("tool_calls"):
        return True
    return False


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


def _protected_indices(messages: list[Any]) -> set[int]:
    if _RECENCY and messages:
        return {len(messages) - 1}
    return set()


def _pass(messages: list[Any]) -> list[Any]:
    protected = _protected_indices(messages)
    out: list[Any] = []
    for idx, msg in enumerate(messages):
        if idx in protected or not isinstance(msg, dict) or not _compressible(msg):
            out.append(msg)
            continue
        content = msg.get("content")
        if isinstance(content, str):
            new_content = _transform_text(content)
            if new_content is not content:
                msg = dict(msg)
                msg["content"] = new_content
            out.append(msg)
        elif isinstance(content, list):
            new_parts, changed = [], False
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                    new_text = _transform_text(part["text"])
                    if new_text is not part["text"]:
                        part = dict(part)
                        part["text"] = new_text
                        changed = True
                new_parts.append(part)
            if changed:
                msg = dict(msg)
                msg["content"] = new_parts
            out.append(msg)
        else:
            out.append(msg)
    return out


def _transform_text(text: str) -> str:
    budget = _budget_for(len(text))
    if budget is None:
        return text
    return _compress_text(text, budget)
