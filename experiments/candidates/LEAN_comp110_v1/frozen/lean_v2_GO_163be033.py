"""SOMA comp-110 (CoT-Compression-5) candidate: LEAN v2 — endurance-first extractive compressor.

Contract (verified against SOMA-benchmark src/compression_service/app/main.py + proxy.py):
the compression sidecar imports this file as a module (mounted at /app/miner/base_miner.py) and
calls `compress_messages(messages, path, metadata) -> list` on EVERY outgoing LLM request with the
OpenAI-style chat `messages` array; the returned list replaces `payload["messages"]`.
`metadata` is currently just {"path": path} — no task/mode info (verified 2026-07-07).

Design (evidence: reports/comp108_cap32pin_postmortem.md + reports/comp110_hard_strategy.md;
hardened per the Codex pre-upload audit, reports/codex_lean_v1_audit.md, 2026-07-07):
- ENDURANCE-FIRST: lean per-step context -> agent survives more steps -> flip consistency +
  explore savings. Depth target ~2.5x (the comp-108 M-winner's proven-compliant zone).
- COMPRESS ONLY GENERATED CONTEXT: `tool` outputs and non-final `assistant` reasoning (= the CoT).
  NEVER touch `system` / `developer` / `user` (instructions/task) — compressing those is prompt
  semantic deletion (README §3/§4; Codex audit fix #1). Never touch assistant tool_calls.
- RECENCY PROTECTION (SOMA_LEAN_RECENCY, default on): the FINAL message is left VERBATIM — it is
  the exact content the model answers next, and compressing a fresh file-read the agent is about to
  edit risks a break (Codex audit fix #4). HONEST TRADEOFF (Codex re-audit): this is the ONLY
  position-dependent rule; that final message compresses once it ages into the prefix next turn, so
  recency protection costs ~one message of cache re-read per turn (a bounded input-vs-cached-weight
  cost) in exchange for break-safety on the freshest content. Everything else is position-independent
  (pure content rules) → the deep history prefix stays byte-stable & cached. The tradeoff is
  A/B-measurable at the platform (SOMA_LEAN_RECENCY=0 disables it); break avoidance (−4) is expected
  to dominate the cache delta, but the platform is the arbiter.
- WHOLE-LINE EXTRACTION ONLY: markers wrap complete ORIGINAL lines (a subset of the source); no
  partial/truncated lines, no mid-content slicing (Codex audit fix #2 + the 5Fjms DQ). Content that
  can't be reduced by dropping whole lines (few giant lines, e.g. minified JSON) is left VERBATIM.
- TIERED CAP (ported from cap32): content <= mid-budget passes through; content up to the huge
  threshold (53k chars, proven boundary) compresses to mid-budget; larger compresses to huge-budget.
  A [[CMP]] block is emitted ONLY when it is a net reduction (Codex audit fix #3+#6).
- QUALITY FLOOR: file paths / line numbers / errors / tracebacks / failing tests / diff markers /
  imports / def-class signatures ALWAYS survive (explore quality = hit-rate - noise-rate; edit
  correctness needs locations).
- CACHE-STABLE: interior rules depend only on message content (never age/position/time), so a
  growing history re-compresses its shared prefix byte-identically -> stable prompt-cache prefix
  (weighted tokens: cached input costs 1/3). Recency protection lives only at the uncached tail.
- BREAK-AVERSE: fail-open (any internal error returns the ORIGINAL messages); message order / count
  / roles never change; input is never mutated in place.
- DETERMINISTIC: pure function of (messages, profile env); no randomness, clock, or network; stdlib.
- PIN (comp-108 _STRUCT_PATTERN import-pinning) NOT ported by default — Codex-verified net-negative.
  Isolated experiment flag SOMA_LEAN_PIN=1 for local A/B ONLY (documented determinism surface).

Profiles (env SOMA_LEAN_PROFILE = conservative | target | aggressive; default target):
  budgets are CHARACTER budgets per message-content block (chars ~= 4x tokens).

Compliance: emits ONLY README_prompting.md §5.1 allowed strings — [[CMP]] / [[/CMP]] — wrapping
extracted ORIGINAL lines. No prompt semantics changed; no instruction added/removed/reordered; no
loop injection; no descriptions/counts inside markers.
"""
from __future__ import annotations

import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# profiles / knobs   (mid_budget, huge_threshold, huge_budget) — char budgets
# ---------------------------------------------------------------------------

_PROFILES = {
    "conservative": (16_000, 53_000, 30_000),
    "target":       (10_000, 53_000, 18_000),
    "aggressive":   (6_000,  53_000, 10_000),
}
_PROFILE = os.getenv("SOMA_LEAN_PROFILE", "target").strip().lower()
if _PROFILE not in _PROFILES:
    _PROFILE = "target"
MID_BUDGET, HUGE_THRESHOLD, HUGE_BUDGET = _PROFILES[_PROFILE]

# EXPERIMENT ONLY (off by default; Codex-verified net-negative in comp-108 — never enable for upload).
_PIN_ENABLED = os.getenv("SOMA_LEAN_PIN", "0").strip() == "1"

# Recency protection ON by default; set 0 to A/B the break-safety-vs-cache tradeoff at the platform.
_RECENCY = os.getenv("SOMA_LEAN_RECENCY", "1").strip() != "0"

_HEAD_LINES = 25          # always keep the first N lines of a compressed block
_TAIL_LINES = 15          # and the last N lines
_MIN_LINES = _HEAD_LINES + _TAIL_LINES + 2   # fewer lines than this -> can't drop whole lines -> verbatim

CMP_START = "[[CMP]]"
CMP_END = "[[/CMP]]"
_MARKER_COST = len(CMP_START) + len(CMP_END) + 2   # newlines

# ---------------------------------------------------------------------------
# signal lines that must SURVIVE compression (the quality floor)
# ---------------------------------------------------------------------------

_KEEP_RX = re.compile(
    r"""(?x)
      (?: \bFile\s+"[^"]+",\s+line\s+\d+ )        # python traceback frames
    | (?: \b(?:Traceback|Error|Exception|error\[|E\s{3}|FAILED|PASSED|ERROR|WARNING|assert(?:ion)?\b) )
    | (?: \btests?[_/][\w./-]+ | \btest_\w+ )      # test files / test names
    | (?: ^[+\-@]{1,3}(?:\s|$) | ^diff\s|^index\s|^---\s|^\+\+\+\s )   # diff/patch markers
    | (?: ^\s*(?:def|class)\s+\w+ )                # signatures
    | (?: ^\s*(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*]+$ )   # imports
    | (?: [\w\-./]+\.(?:py|c|h|cpp|js|ts|tsx|json|yaml|yml|toml|cfg|ini|txt|rst|md|html|css|xml)\b )  # file paths
    | (?: \bline\s+\d+\b | :\d+:\d* )              # line-number references
    """,
    re.M,
)

_PIN_RX = re.compile(r"^\s*(?:@\w+|raise\b|except\b)", re.M)   # comp-108 pin extras (experiment only)


def _is_signal(line: str) -> bool:
    if _KEEP_RX.search(line):
        return True
    if _PIN_ENABLED and _PIN_RX.search(line):
        return True
    return False


# ---------------------------------------------------------------------------
# core block compressor (pure; content -> content). WHOLE LINES ONLY.
# ---------------------------------------------------------------------------

def _compress_text(text: str, budget: int) -> str:
    """Extractive head + signal-lines + tail within a char budget, dropping ONLY whole lines.
    The kept extraction is verbatim original lines (a subset), wrapped once in [[CMP]]/[[/CMP]].
    Returns the ORIGINAL text unchanged if it can't be reduced (too few lines, or no net gain)."""
    if len(text) <= budget:
        return text
    lines = text.splitlines()
    n = len(lines)
    if n < _MIN_LINES:
        return text                          # few giant lines: cannot drop whole lines -> verbatim

    keep = [False] * n
    for i in range(_HEAD_LINES):
        keep[i] = True
    for i in range(n - _TAIL_LINES, n):
        keep[i] = True
    used = sum(len(lines[i]) + 1 for i in range(n) if keep[i]) + _MARKER_COST

    for i in range(n):                       # pass 1: quality-floor signal lines, in order
        if keep[i] or not _is_signal(lines[i]):
            continue
        cost = len(lines[i]) + 1
        if used + cost > budget:
            continue
        keep[i] = True
        used += cost
    for i in range(n):                       # pass 2: fill remaining budget in document order
        if keep[i]:
            continue
        cost = len(lines[i]) + 1
        if used + cost > budget:
            continue
        keep[i] = True
        used += cost

    if all(keep):                            # nothing dropped -> no marker, verbatim
        return text
    extraction = "\n".join(lines[i] for i in range(n) if keep[i])
    out = CMP_START + "\n" + extraction + "\n" + CMP_END
    return out if len(out) < len(text) else text   # never emit a net increase


# ---------------------------------------------------------------------------
# message-array pass
# ---------------------------------------------------------------------------

def _budget_for(size: int) -> int | None:
    """Tiered cap. None = passthrough (only compress when the budget is below the content size)."""
    if size <= MID_BUDGET:
        return None
    if size <= HUGE_THRESHOLD:
        return MID_BUDGET
    return HUGE_BUDGET


def _compressible(msg: dict) -> bool:
    role = msg.get("role")
    if role == "tool":
        return True                          # tool outputs = the sanctioned compression target
    if role == "assistant" and not msg.get("tool_calls"):
        return True                          # assistant reasoning = the CoT; tool_calls untouched
    return False                             # system / developer / user = instructions -> never


def compress_messages(
    messages: list[Any] | None = None,
    path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[Any]:
    del path, metadata                       # only {"path": ...} today; unused (compliance-safe)
    if not isinstance(messages, list):
        return messages if isinstance(messages, list) else []
    try:
        return _pass(messages)
    except Exception:
        return messages                      # fail-open: NEVER break the run


def _protected_indices(messages: list[Any]) -> set[int]:
    """Recency guard: ONLY the final message (the true uncached tail = the exact content the model
    answers next) is left verbatim. This is the single position-dependent rule; every other message
    obeys pure content rules so the deep prefix stays byte-stable. Disable via SOMA_LEAN_RECENCY=0."""
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
            out.append(msg)                  # None / scalar / unknown: untouched
    return out


def _transform_text(text: str) -> str:
    budget = _budget_for(len(text))
    if budget is None:
        return text
    return _compress_text(text, budget)
