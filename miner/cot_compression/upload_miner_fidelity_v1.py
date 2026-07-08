"""SOMA comp-110 (CoT-Compression-5) — FIDELITY v1 (output/trajectory-lever redesign).

WHY THIS EXISTS (see reports/comp110_local_eval_findings.md + state/CURRENT.md LATEST-3): the screener
scores WEIGHTED tokens = 1·input + 0.1·cached + 3·output. Byte-compressing cached history (SKELETON's
lever) is 0.1-weighted and, worse, our rewriting BUSTS CACHE (shifts tokens to 1.0-weight input) → net
~0 weighted savings. The dashboard qualifier clears 20% via LOWER OUTPUT (fewer/tighter agent turns) +
CACHE-STABILITY, not byte volume. This redesign targets those two levers instead of raw compression:

  (1) FULL CACHE-STABILITY — compression is a PURE, POSITION-INDEPENDENT function of a message's own
      content. Unlike SKELETON/LEAN there is NO recency exemption (that exemption made the previous-final
      message flip verbatim→compressed each turn = a rolling cache-bust). Here message X compresses to the
      SAME bytes on every turn regardless of position ⇒ the emitted prefix is byte-stable ⇒ stays cached
      (weight 0.1) instead of leaking into input (weight 1.0). This is the concrete, locally-verifiable win
      (scripts/prefix_stability.py / the offline prefix check).
  (2) FEWER TURNS via QUALITY PRESERVATION — keep ALL actionable content (code, errors, paths, defs,
      imports, diffs, structure) so the agent never has to RE-READ (re-reads = extra turns = extra output
      ×3, which is what erased SKELETON's savings). Only NOISE is removed (ANSI, trailing WS, blank-line
      and separator runs, consecutive duplicate lines) — zero information loss, zero re-read risk. When a
      genuinely huge low-signal bulk span is dropped, a PRECISE source-line marker lets the agent re-read
      exactly that span in ONE targeted turn instead of exploring — turning a potential turn-inflator into a
      bounded one-turn cost. The bet (only measurable on the platform): a cleaner, fully-preserved,
      cache-stable context makes the agent decide in fewer turns → less output → lower weighted total.

INVARIANTS (carried from the LEAN/SKELETON audited lineage):
- Compress ONLY `tool` outputs + `assistant` messages WITHOUT tool_calls. NEVER system/developer/user,
  never assistant tool_calls.
- WHOLE ORIGINAL LINES ONLY, emitted BYTE-VERBATIM incl. original terminators (splitlines(keepends=True)).
- A block is emitted only on NET REDUCTION; any error → original messages (fail-open); stdlib only; input
  never mutated; deterministic.
- Compliance: emits ONLY the CURRENT-live README §5.1 allowed strings — `[[CMP]] source line N [[/CMP]]`
  and `[[CMP]] source line N ~ source line M Omitted [[/CMP]]`. No steering, no injected text, no LLM calls,
  no task/category awareness. PR#176 marker switch = the documented one-liner in `_omission_marker`.
"""
from __future__ import annotations

import os
import re
from typing import Any

# ── gentleness KNOBS (this compressor is deliberately HIGH-FIDELITY; bulk-drop only kicks in on huge spans) ──
# profile = (min_compress_chars, head_lines, tail_lines, bulk_budget_chars, min_drop_run_lines)
_PROFILES = {
    "fidelity": (2000, 24, 12, 6000, 40),   # very gentle: only huge outputs trimmed, generous keep
    "balanced": (1200, 16, 8, 3000, 24),    # moderate
    "lean":     (800, 10, 5, 1600, 16),     # more reduction (still fidelity-first, still cache-stable)
}
_PROFILE = os.getenv("SOMA_FID_PROFILE", "balanced").strip().lower()
if _PROFILE not in _PROFILES:
    _PROFILE = "balanced"
MIN_COMPRESS, HEAD_LINES, TAIL_LINES, BULK_BUDGET, MIN_DROP_RUN = _PROFILES[_PROFILE]

_TERM_RX = re.compile(r"(\r\n|\r|\n)$")
_ANSI_RX = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")          # CSI escape sequences (terminal color/control)
_TRAIL_WS_RX = re.compile(r"[ \t]+(\r\n|\r|\n|$)")

# lines worth keeping VERBATIM even inside a huge output (actionable signal → no re-read needed)
_SIGNAL_RX = re.compile(
    r"""(?x)
      (?: \bFile\s+"[^"]+",\s+line\s+\d+ )
    | (?: \b(?:Traceback|Error|Exception|error\[|FAILED|PASSED|ERROR|WARNING|assert(?:ion)?\b) )
    | (?: \btests?[_/][\w./-]+ | \btest_\w+ )
    | (?: ^\s*[+\-@]{1,3}(?:\s|$) | ^\s*diff\s | ^\s*index\s | ^\s*---\s | ^\s*\+\+\+\s )
    | (?: ^\s*(?:async\s+)?def\s+\w+ | ^\s*class\s+\w+ | ^\s*@\w[\w.]* )
    | (?: ^\s*(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*()]+ )
    | (?: [\w\-./]+\.(?:py|c|h|cpp|cc|js|ts|tsx|go|rs|java|rb|json|yaml|yml|toml|cfg|ini|txt|rst|md|html|css|xml)\b )
    | (?: \bline\s+\d+\b | :\d+:\d* )
    | (?: ^\s*(?:if|for|while|return|raise|with|try|except|elif|else|yield)\b )
    """,
    re.M,
)


def _omission_marker(start_1: int, end_1: int) -> str:
    """CURRENT-live §5.1 template; block-relative 1-based inclusive line numbers.
    PR#176 switch (documented, deliberate — no not-yet-allowed literal kept in source): if PR #176 merges,
    wrap the range return with its omission tags in place of [[CMP]]/[[/CMP]], then re-gate + re-audit."""
    if start_1 == end_1:
        return f"[[CMP]] source line {start_1} [[/CMP]]"
    return f"[[CMP]] source line {start_1} ~ source line {end_1} Omitted [[/CMP]]"


def _denoise_line(seg: str) -> str:
    """Strip pure NOISE from ONE line-with-terminator, preserving its terminator byte-exactly.
    Zero information loss: ANSI control codes + trailing whitespace only."""
    m = _TERM_RX.search(seg)
    term = m.group(1) if m else ""
    body = seg[: len(seg) - len(term)] if term else seg
    body = _ANSI_RX.sub("", body)
    body = body.rstrip(" \t")
    return body + term


def _compress_text(text: str) -> str:
    if len(text) <= MIN_COMPRESS:
        # still cheap noise-strip on smaller blocks (cache-stable, lossless) if it helps
        if "\x1b[" not in text and not _TRAIL_WS_RX.search(text):
            return text
    raw = text.splitlines(keepends=True)
    n = len(raw)
    if n == 0:
        return text

    # 1) lossless denoise every line (ANSI + trailing WS). position-independent.
    lines = [_denoise_line(s) for s in raw]
    content = [_TERM_RX.sub("", s) for s in lines]

    # 2) collapse runs of blank lines (>=3 -> 1) and consecutive identical lines (>=4 -> 2 + marker),
    #    and huge low-signal bulk spans beyond the budget -> precise marker. All whole-line, verbatim keeps.
    keep = [True] * n

    # 2a) blank-line runs
    i = 0
    while i < n:
        if content[i].strip() == "":
            j = i
            while j < n and content[j].strip() == "":
                j += 1
            if j - i >= 3:
                for k in range(i + 1, j):
                    keep[k] = False
            i = j
        else:
            i += 1

    # 2b) consecutive identical non-blank lines (repeated separators / spinner noise)
    i = 0
    while i < n:
        if keep[i] and content[i].strip():
            j = i + 1
            while j < n and content[j] == content[i]:
                j += 1
            if j - i >= 4:
                for k in range(i + 2, j):
                    keep[k] = False
            i = j
        else:
            i += 1

    # 2c) huge low-signal bulk: only for big blocks, drop long runs of NON-signal lines beyond head/tail,
    #     but keep the budget generous (fidelity-first). Precise marker so a re-read is one targeted turn.
    if len(text) > MIN_COMPRESS and n > HEAD_LINES + TAIL_LINES + MIN_DROP_RUN:
        protected = set(range(min(HEAD_LINES, n))) | set(range(max(n - TAIL_LINES, 0), n))
        budget = BULK_BUDGET
        used = 0
        # walk interior; drop only long contiguous runs of non-signal, non-protected lines past budget
        i = HEAD_LINES
        end = n - TAIL_LINES
        while i < end:
            if (i in protected) or _SIGNAL_RX.search(content[i]) or content[i].strip() == "":
                used += len(lines[i]); i += 1; continue
            j = i
            while j < end and not (j in protected) and not _SIGNAL_RX.search(content[j]) and content[j].strip() != "":
                j += 1
            run_bytes = sum(len(lines[k]) for k in range(i, j))
            if (j - i) >= MIN_DROP_RUN and used > budget:
                for k in range(i, j):
                    keep[k] = False           # drop this low-signal bulk run (marker emitted below)
            else:
                used += run_bytes
            i = j

    if all(keep):
        rendered = "".join(lines)                              # denoise-only result
        return rendered if len(rendered) < len(text) else text

    out: list[str] = []
    i = 0
    while i < n:
        if keep[i]:
            out.append(lines[i]); i += 1
        else:
            j = i
            while j < n and not keep[j]:
                j += 1
            out.append(_omission_marker(i + 1, j) + "\n")
            i = j
    rendered = "".join(out)
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
        return messages


def _pass(messages: list[Any]) -> list[Any]:
    # NO recency exemption: every compressible message is compressed by the SAME pure function of its own
    # content regardless of position → emitted prefix is byte-stable across turns → cache-stable.
    out: list[Any] = []
    for msg in messages:
        if not isinstance(msg, dict) or not _compressible(msg):
            out.append(msg)
            continue
        content = msg.get("content")
        if isinstance(content, str):
            new = _compress_text(content)
            if new != content:
                msg = dict(msg); msg["content"] = new
            out.append(msg)
        elif isinstance(content, list):
            parts = []; changed = False
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                    t = part["text"]; nt = _compress_text(t)
                    if nt != t:
                        part = dict(part); part["text"] = nt; changed = True
                parts.append(part)
            if changed:
                msg = dict(msg); msg["content"] = parts
            out.append(msg)
        else:
            out.append(msg)
    return out
