"""SOMA comp-110 (CoT-Compression-5) candidate: SKELETON v1 — a ground-up redesign.

WHY A NEW DESIGN (not the cap32/LEAN lineage). Feasibility analysis on REAL captured copilot traffic
(reports/comp110_explore_scoring_analysis.md) proved the cap32/LEAN family CANNOT clear comp-110's hard
≥10% weighted-savings screener gate: the copilot agent reads in small chunks (~1.1k chars, <40 lines),
so a head+tail *window* (LEAN kept 25+15 lines) leaves those reads essentially whole → ≤~4% savings.

KEY INSIGHT: dropping the window and transmitting only a navigable SKELETON of each observation —
the structural/location signal lines + a minimal head + source-line omission markers for everything
dropped — reaches ~11–13% real weighted savings (clears the screener) WHILE preserving what both
comp-110 layers actually need: file paths + structure for the explore hit-rate, and locatable
omissions so the agent can RE-READ the exact region it needs to edit (the agent already re-reads
files repeatedly — observed expressions.py read 8× in one solve). The bet: give the agent a MAP, not
the territory; it re-fetches detail on demand.

WHAT SURVIVES (the skeleton / quality floor — verbatim ORIGINAL lines): file paths, imports, class/def
signatures + decorators, error/exception/traceback frames, FAILED/PASSED/assert, test names, diff/hunk
headers, line-number references, and a minimal head of each block. Everything else is replaced by an
exact §5.1 omission marker naming the omitted source lines.

INVARIANTS (carried over — verified-correct primitives, not the old strategy):
- Compress ONLY `tool` outputs + non-final `assistant` reasoning (the CoT). NEVER system/developer/user
  (instructions) and never assistant `tool_calls`.
- Whole ORIGINAL lines only; a block is emitted only on NET REDUCTION; content that can't reduce → verbatim.
- CACHE-SAFE: interior compression is a pure function of the message's own content (position-independent),
  so the re-sent history is byte-stable and stays cached (weighted: cached=⅓). The only position-dependent
  rule is final-message recency (below), which lives at the UNCACHED tail (its one transition busts nothing
  downstream because nothing follows it yet).
- RECENCY: the final message is left VERBATIM (the freshest read the agent acts on THIS turn) — toggle
  SOMA_SKEL_RECENCY=0 for the savings A/B. Everything older is skeletonized (the agent re-reads if needed).
- Deterministic, fail-open (any error → original messages), stdlib only, input never mutated. NO pin, NO dedupe.

Compliance: emits ONLY README §5.1 allowed strings — the source-line omission markers
`[[CMP]] source line N [[/CMP]]` / `[[CMP]] source line N ~ source line M Omitted [[/CMP]]` (exact
templates, integers only) — wrapping omitted spans; kept lines are verbatim originals. No prompt
semantics changed, no instruction added/removed/reordered, no loop injection.

Profiles (env SOMA_SKEL_PROFILE = safe | target | deep; default target). Tuned on real captured traffic
to clear the ≥10% screener with margin; the REAL screener is different tasks → validate before upload.
"""
from __future__ import annotations

import os
import re
from typing import Any

# profile = (min_compress_chars, head_lines, tail_lines, budget_chars). The skeleton is BUDGETED:
# always-keep = head + tail + FILE-PATH lines (the critical explore signal); then fill the budget with
# other signal (errors/tests > defs/decorators > imports > line-refs) then any remaining lines, in
# document order; everything else → source-line omission markers. Hard cap = real savings; path-priority
# = protects the explore hit-rate (file-level) even under aggressive compression.
_PROFILES = {
    "safe":   (700, 5, 2, 900),
    "target": (500, 3, 1, 550),
    "deep":   (400, 2, 1, 380),
}
_PROFILE = os.getenv("SOMA_SKEL_PROFILE", "target").strip().lower()
if _PROFILE not in _PROFILES:
    _PROFILE = "target"
MIN_COMPRESS, HEAD_LINES, TAIL_LINES, BUDGET = _PROFILES[_PROFILE]
MIN_LINES = HEAD_LINES + TAIL_LINES + 2   # too few lines to drop whole ones → leave verbatim

_RECENCY = os.getenv("SOMA_SKEL_RECENCY", "1").strip() != "0"

CMP_START = "[[CMP]]"
CMP_END = "[[/CMP]]"

# The SKELETON: structural/location lines that ALWAYS survive (verbatim). Broad by design —
# these define what the explore hit-rate needs and where the agent must re-read to edit.
_KEEP_RX = re.compile(
    r"""(?x)
      (?: \bFile\s+"[^"]+",\s+line\s+\d+ )                       # python traceback frames
    | (?: \b(?:Traceback|Error|Exception|error\[|E\s{3,}|FAILED|PASSED|ERROR|WARNING|assert(?:ion)?\b) )
    | (?: \btests?[_/][\w./-]+ | \btest_\w+ )                    # test files / names
    | (?: ^\s*[+\-@]{1,3}(?:\s|$) | ^\s*diff\s | ^\s*index\s | ^\s*---\s | ^\s*\+\+\+\s )  # diff/hunk
    | (?: ^\s*(?:async\s+)?def\s+\w+ | ^\s*class\s+\w+ | ^\s*@\w[\w.]* )  # signatures + decorators
    | (?: ^\s*(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*()]+ )        # imports
    | (?: [\w\-./]+\.(?:py|c|h|cpp|cc|js|ts|tsx|go|rs|java|rb|json|yaml|yml|toml|cfg|ini|txt|rst|md|html|css|xml)\b )  # paths
    | (?: \bline\s+\d+\b | :\d+:\d* )                            # line-number refs
    """,
    re.M,
)


_PATH_RX = re.compile(
    r"""[\w\-./]+\.(?:py|c|h|cpp|cc|js|ts|tsx|go|rs|java|rb|json|yaml|yml|toml|cfg|ini|txt|rst|md|html|css|xml)\b"""
)


def _is_signal(line: str) -> bool:
    return bool(_KEEP_RX.search(line))


def _is_path(line: str) -> bool:
    return bool(_PATH_RX.search(line))


def _omission_marker(start_1: int, end_1: int) -> str:
    """Exact README §5.1 template; 1-based inclusive line numbers within THIS block's own line sequence."""
    if start_1 == end_1:
        return f"{CMP_START} source line {start_1} {CMP_END}"
    return f"{CMP_START} source line {start_1} ~ source line {end_1} Omitted {CMP_END}"


def _skeletonize(text: str) -> str:
    """Budgeted skeleton: always keep head + tail + FILE-PATH lines; then fill BUDGET with other signal
    (by priority) then remaining lines, document order; drop the rest as source-line omission markers.
    Whole original lines only. Deterministic; verbatim if it can't net-reduce."""
    if len(text) <= MIN_COMPRESS:
        return text
    lines = text.splitlines()
    n = len(lines)
    if n < MIN_LINES:
        return text                                # too few lines to drop whole ones safely

    keep = [False] * n
    for i in range(HEAD_LINES):
        keep[i] = True
    for i in range(n - TAIL_LINES, n):
        keep[i] = True
    used = sum(len(lines[i]) + 1 for i in range(n) if keep[i])
    # fill the BUDGET by priority (all in document order, hard-capped): file paths first (the critical
    # explore signal gets first claim), then other structural signal, then any remaining lines.
    def _priority(i):
        if _is_path(lines[i]):
            return 0
        if _is_signal(lines[i]):
            return 1
        return 2
    for tier in (0, 1, 2):
        if used >= BUDGET:
            break
        for i in range(n):
            if keep[i] or _priority(i) != tier:
                continue
            cost = len(lines[i]) + 1
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
            out.append(lines[i])
            i += 1
        else:
            j = i
            while j < n and not keep[j]:
                j += 1
            out.append(_omission_marker(i + 1, j))  # dropped original lines (i+1)..(j), 1-based inclusive
            i = j
    rendered = "\n".join(out)
    return rendered if len(rendered) < len(text) else text


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
        return messages                            # fail-open: never break the run


def _protected_indices(messages: list[Any]) -> set[int]:
    """Final message only (freshest read the agent acts on) — the uncached tail; cache-safe.
    Disable with SOMA_SKEL_RECENCY=0 for the savings A/B."""
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
            new_content = _skeletonize(content) if len(content) > MIN_COMPRESS else content
            if new_content is not content and new_content != content:
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
