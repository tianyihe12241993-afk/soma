"""SOMA comp-110 (CoT-Compression-5) — SKELETON v2 (consolidated candidate).

Consolidates the winning SKELETON design (budgeted structural skeleton with path-priority) with LEAN
v3's verified-safe primitives, applies the two Codex GO-WITH-CHANGES fixes, and future-proofs the
marker syntax. Formula-dependent aggressiveness is exposed as KNOBS (profiles/env) so we tune-and-ship
the hour the (in-flux) score formula lands — WITHOUT re-architecting. See:
reports/comp110_scoring_rederivation.md (current constants) and DISCOVERIES 2026-07-07 (team said the
score formula is actively changing → do NOT hard-tune to today's 20% gate / cached-1/10; tune the knobs
when the watcher flags the change, then re-run experiments/.../retune_harness.py).

STRATEGY (team-confirmed intent, formula-invariant): reduce INPUT/context tokens while MAINTAINING
QUALITY. Transmit a navigable SKELETON of each observation — file-PATH lines (top-priority for the
explore hit_file_rate) + other structural signal + a minimal head, hard-capped at a budget — and mark
every omitted span with a source-line marker so the agent can re-read the exact region it needs.

INVARIANTS (verified-safe primitives — carried from LEAN v3):
- Compress ONLY `tool` outputs + non-final `assistant` reasoning (the CoT). NEVER system/developer/user
  (instructions) and never assistant `tool_calls`.
- WHOLE ORIGINAL LINES ONLY, emitted BYTE-VERBATIM incl. their original line terminators (Codex fix:
  splitlines(keepends=True) — no CRLF/lone-CR normalization, no dropped terminal newline). Content that
  can't net-reduce → returned verbatim.
- A block is emitted only on NET REDUCTION.
- CACHE-SAFE: interior compression is a pure function of the message's OWN content (position-independent),
  so the re-sent history is byte-stable and stays cached. Only the final message is position-dependent
  (recency, below) and it sits at the uncached tail (its transition busts nothing downstream).
- RECENCY (SOMA_SKEL_RECENCY, default on): final message left verbatim (freshest read the agent acts on).
- Deterministic, fail-open (any error → original messages), stdlib only, input never mutated. NO pin, NO dedupe.

QUALITY floor / priority (Codex fix: this is priority-within-budget, NOT unconditional keep): always
keep a minimal head + tail; then FILL the budget by priority — FILE PATHS first (the explore signal),
then other structural signal (errors/tests/defs/decorators/imports/line-refs), then any remaining lines,
all in document order. Beyond the budget, lines are dropped to source-line markers. Paths get first
claim so file-level explore quality (hit_file_rate − noise_file_rate) is protected even under aggression.

Compliance: emits ONLY the CURRENT-live README §5.1 allowed strings —
`[[CMP]] source line N [[/CMP]]` (single) and `[[CMP]] source line N ~ source line M Omitted [[/CMP]]`
(range) — wrapping omitted spans; integers-only, no injected text. PR#176-PROOFING is a documented
ONE-LINE switch in `_omission_marker` (NOT a pre-embedded literal / live knob — see that function),
so if PR #176's omission-tag change merges we flip one line + re-gate + re-audit. The source is kept
free of any not-yet-allowed string.
"""
from __future__ import annotations

import os
import re
from typing import Any

# ── formula-dependent KNOBS (tune when the score formula lands; do NOT hard-tune to today's numbers) ──
# profile = (min_compress_chars, head_lines, tail_lines, budget_chars)
_PROFILES = {
    "gentle": (2000, 30, 15, 4000),  # recency-off first-test default: small reads (<2000) pass through;
                                     # big reads kept to ~4000 chars of signal (Codex GO-WITH-CHANGES:
                                     # "prove safe" on the freshest read → correctness-first, still ~88% cut).
    "safe":   (700, 5, 2, 900),
    "target": (500, 3, 1, 550),
    "deep":   (400, 2, 1, 380),
}
# env does NOT reach the compression container → the DEFAULT here is what actually runs.
_PROFILE = os.getenv("SOMA_SKEL_PROFILE", "gentle").strip().lower()
if _PROFILE not in _PROFILES:
    _PROFILE = "gentle"
MIN_COMPRESS, HEAD_LINES, TAIL_LINES, BUDGET = _PROFILES[_PROFILE]
MIN_LINES = HEAD_LINES + TAIL_LINES + 2

# ── compliance / behavior knobs ──
# FRESH-INPUT TEST VARIANT: recency FORCED OFF (compress the fresh tool result too = the weight-1.0 input).
# env does NOT reach the compression container, so this must be a code default, not SOMA_SKEL_RECENCY.
_RECENCY = False

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
    """Exact CURRENT-live §5.1 template; 1-based inclusive line numbers within THIS block's own line seq.
    NOTE (Codex CONCERN, documented): block-relative, not file-absolute — the template is fixed and
    cannot be qualified without breaking exact-string compliance; validate agent navigation in the smoke.

    ⚠ PR#176-PROOFING (deliberate compliance choice): we emit ONLY the currently-allowed strings and do
    NOT pre-embed the proposed alternative range template, because carrying a not-yet-allowed string in
    source trips compliance scanners and risks a non-compliant emit. When the watcher reports PR #176
    merged (README allowed-set change), make the ONE-LINE switch on the range return below: wrap it with
    PR #176's omission tags in place of the CMP tags (single-line form is unchanged by that PR), then
    re-run the rules gate + harness + Codex re-audit."""
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
    content = [_TERM_RX.sub("", seg) for seg in raw]              # terminator-stripped content for decisions

    head_tail = set(range(min(HEAD_LINES, n))) | set(range(max(n - TAIL_LINES, 0), n))

    def _priority(i: int) -> int:
        if i in head_tail:
            return 0                                             # minimal head/tail context (highest priority)
        if _PATH_RX.search(content[i]):
            return 1                                             # file paths — the explore hit-rate signal
        if _is_signal(content[i]):
            return 2                                             # other structural signal
        return 3                                                 # bulk

    # Fill the BUDGET by priority, document order. EVERY kept line is budget-checked (incl. head/tail),
    # so total kept content <= BUDGET — a true cap (Codex v2 fix: head/tail were previously unconditional).
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
            out.append(raw[i])                                    # verbatim (terminator preserved)
            i += 1
        else:
            j = i
            while j < n and not keep[j]:
                j += 1
            out.append(_omission_marker(i + 1, j) + "\n")         # dropped original lines (i+1)..(j)
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
