#!/usr/bin/env python3
"""SOMA miner aow_bet — CACHE BET (harvest-only freeze-on-emit) on m12.

WHAT THIS IS: a STRICT, OPT-IN enhancement of m12's HARVEST path only. m12
(upload_miner_m7_compliant.py) re-derives its whole compressed history every harvest
turn (compress_structurally re-runs over the entire 'working' set with STICKY
escalation), and m12's harvest DROPS the oldest interactions to hit an 8k target — so
the emitted prefix CHURNS turn-to-turn (each drop-turn rewrites the front) and the
provider prompt-cache misses on those bytes. aow_bet makes m12's stated intent EXPLICIT:
it compresses each turn's content ONCE when it ages out of a recent verbatim window,
FREEZES those exact output bytes, and REUSES them verbatim on later turns so the emitted
prefix is byte-IDENTICAL turn-to-turn and the provider caches it. The compression ENGINE
is m12's, untouched.

THE BET (vs aow_lite, which degraded to byte-exact m12 = no gain): the verification
PROVED the cache win requires shipping a prefix that is nominally LARGER than m12's ~8k
aggressive prune but byte-STABLE turn-to-turn (so the provider caches it at ~0.37x
weighted) — exactly the king's profile (85% cache) and m20b-v2's (83% cache; m20b-v2
only lost because it STUBBED content, which we do NOT do). aow_lite shipped m12's exact
bytes for two reasons, both fixed here:
  1) HEAD-REQUIREMENT BUG: compress_structurally locates the first user message in its
     input and no-ops if there is none. aow_lite fed it working[frozen_count:] (no head),
     so it no-op'd whenever anything was frozen. FIX: PREPEND a byte-identical copy of the
     head (messages up to and INCLUDING the first user message) before compressing the
     live region, then STRIP exactly those prepended head messages off the front of the
     output. The head appears exactly once (inside the frozen prefix); never duplicated.
  2) BOUNDARY CAPS: aow_lite capped the freeze boundary at first_user_index AND at the
     common-prefix-with-m12 length, which forced the frozen region to == m12's stable
     head (nothing meaningful froze) and reverted on every drop. FIX: REMOVE both caps;
     advance the boundary by the recent verbatim WINDOW only (snapped to a tool-call
     boundary, monotonic). REPLACE the m12-nominal ratio watchdog with a SAVINGS_CEIL
     guard vs the ORIGINAL RAW (>=15% nominal savings), which ALLOWS the frozen-plus-live
     result to be nominally larger than m12 while still guaranteeing positive savings —
     that larger-but-stable content IS the cache bet.

SAFETY PRINCIPLE (overriding): in ANY ambiguous/edge/uncertain case aow_bet falls back
to producing the BYTE-EXACT output m12 would produce. The freeze applies ONLY in harvest
mode, ONLY before the session has ever shown rich depth (everTouchedRich gate), and ONLY
when our verified previous output is a byte-identical prefix of the working set. Any
prefix mismatch, orphan, savings-ceiling breach, or rich-depth signal reverts the turn
(and from then on the session) to m12's exact harvest path. compress_gently (RICH path),
passthrough, and compress_structurally bodies are UNCHANGED; we only change WHAT we feed
compress_structurally in harvest (the prepended-head live region) and how we assemble its
output around a frozen prefix.

WHAT THIS IS (m12 lineage): m7's proven compression ENGINE kept intact, with every prompt-side
behavior-steering construct removed so the miner complies with
miner/README_prompting.md. The README permits exactly two prompt-edit categories
next round:
  1) Compression markers — metadata wrappers that preserve instruction meaning,
     order, requirements, tool/safety/role policy and the output contract EXACTLY.
  2) Loop-detection guards — fire only on objective repeated/no-progress signals,
     fail fast with a clear loop reason, and never change strategy/reasoning/tool
     policy.

REMOVED vs m7 (all prompt-side, now illegal):
  - The entire injected coach message and the force-stop governor that told the
    agent how/whether to proceed (the conclude-now/halt governor, the approach-
    changing steering, the failing-test restatement). These steered the agent's
    workflow and are now gone.
  - The first-user-message HISTORY DIGEST injection. m7's harvest path appended a
    growing one-line digest of dropped interactions, wrapped in a private marker,
    INTO the first user message — which both used a banned private marker and
    changed the first message's content. The digest injection/parse/regenerate
    machinery is removed; the frozen head (system + first user message) is now
    emitted byte-identical. The harvest engine still drops the oldest interactions
    for the token win, it simply no longer leaves a private-marker trail.
  - All custom/private bracketed markers m7 emitted (the compressed-history digest
    sentinels, the context-note marker, and the prose soma-prefixed elided/dedup
    markers). The dead digest/coach helpers and constants that produced them are
    removed too.

MARKERS USED (the ONLY allowed strings, from README sections 5.1/5.2):
  - The CMP start/end marker pair (aliased once to the spelled-out start/end
    strings) wraps a truncated tool-result region — see CMP_START / CMP_END below.
    The kept head/tail sit OUTSIDE the markers; the elided middle is the wrapped
    region (metadata only — no instruction meaning changes).
  - The BLOCK open/close marker pair labels the surviving latest copy of a
    duplicated / near-duplicate tool result; the earlier copy becomes the allowed
    back-reference string built by same_response_ref().
  - Loop detection emits ONLY the two allowed loop-reason strings — see
    LOOP_REASON_ASSISTANT / LOOP_REASON_TOOLCALL — nothing else.

KEPT vs m7 (the compression ENGINE, unchanged): depth-adaptive
passthrough/harvest/rich routing, the v6 HARVEST structural drop+truncate path
(compress_structurally), the RICH skeleton (compress_gently), the fragile/error
guards, the load-bearing allowlist, error markers, active-file preservation,
recent-intact window, extractive content-preservation of bulky tool output,
tool-call/tool-result pairing integrity, the orphan guard, and passthrough. The
truncation/dedup PRESERVES load-bearing content (failing-test names, assertion
lines, traceback tail, file paths, line numbers, current patch/diff, active file)
exactly as m7 did — the allowed markers merely WRAP it.

Protocol (same as the reference): `python upload_miner_m7_compliant.py assemble`
with the connector payload on stdin, a single JSON object on stdout. Stdlib only;
tiktoken is used for the reported token estimate when available. run_event /
cli_main / the plugin entry contract are identical to m7 so the existing driver
can run this unchanged.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Optional


EVENT_NAMES = frozenset({"assemble"})
# Bumped to 7 (m12=4, aow_lite=5, aow_bet-v1=6): aow_bet persists the same freeze fields
# (frozenPrefix / frozenCount / everTouchedRich) PLUS a NEW nativeTokens field, AND the
# freeze-vs-revert decision changed meaning — the savings ceiling is now measured against
# the TRUE native trajectory size (tracked in nativeTokens), not against the rewritten/
# already-compressed raw input. The previous aow_bet (version 6) oscillated the frozen
# count 0->n->0 every turn because its ceiling fired on the small rewritten input; a state
# file from that build must NOT be reused under the new rules (its frozen prefix and the
# absent nativeTokens would mislead the accumulating freeze). A distinct version guarantees
# an aow_bet state file is never read by m12, aow_lite, OR the broken aow_bet-v1, and none
# of theirs by this build (load_state rejects a version mismatch -> returns None -> fresh
# start -> exact m12 first-turn behavior, no freeze). Cross-contamination is impossible by
# construction; an old frozen prefix can never be reused under the new boundary/ceiling rules.
STATE_VERSION = 7
STATE_DIR_NAME = "state"

CHARS_PER_TOKEN = 4
# v6 HARVEST budget. The 1.376 king proved the dominant lever is the pass/pass
# token bonus (score = 1.0 + 0.5*ln(TokB/TokA)): compress hard on EVERY task
# (incl. easy/medium) to cut TokA ~2-3x while keeping the pass, and the
# easy/medium scores jump from ~1.0 to ~1.4. Our old pass-through-below-12k
# forfeited this. So: compress almost everything, aggressively truncate stale
# tool output (the expendable bulk), but keep the safe-aggression rule —
# protect recent interactions + error output + every user/assistant message,
# and never drop a message in harvest mode (truncate only).
PASS_THROUGH_TOKENS = 3_000    # below this there is nothing worth compressing
TIGHT_TOKENS = 25_000          # enter drop-with-digest mode earlier on big tasks
TARGET_TOKENS = 8_000          # tight-mode trajectory target
PRESSURE_RELIEF = 0.75

# v11 DEPTH-ADAPTIVE (aggressive-shallow / rich-deep). The king (1.386) is
# adaptive: tiny tokens on pass-likely tasks (bonus) + huge rich context on
# fail-likely tasks (flips). But the captured trajectories show per-call context
# is uniformly SMALL across all bands (easy peaks 6-58k, hard peaks 14-85k) —
# token SIZE can't tell easy from hard. What separates them is conversation
# DEPTH: easy ends shallow, hard runs deep. So v11 switches on depth:
#   - SHALLOW (msg count < LARGE_THRESHOLD_MSGS): v6-style HARVEST (compress_
#     structurally, target 8k, drop-with-digest) → recover the pass-task token
#     bonus we forfeited by going rich-everywhere in v9/v10.
#   - DEEP   (msg count >= LARGE_THRESHOLD_MSGS, sticky): v9/v10 RICH skeleton
#     with the RICHER stale cap (6k, not v10's 2k) → maximum context for flips.
# Monotonic: passthrough -> harvest -> rich, never reverts. A task that ends
# shallow was harvested throughout (bonus); one that goes deep gets rich for the
# deciding rounds (flip). The only prompt-side surface is the compliant loop guard
# (an allowed loop-reason string, appended only on an objective loop) — there is no
# coach / governor / history-digest injection in this compliant derivative.
RICH_INTACT_MSGS = 10          # last N messages kept byte-intact (never compressed)
RICH_STALE_CAP = 6_000         # v11 rich/deep path: richer stale cap for flips (v9 value; v10 used 2k)
RICH_PROTECTED_CAP = 30_000    # "full" for practical purposes (guards pathological logs)
NEARDUP_MIN_CHARS = 400        # min normalized length to qualify as a near-duplicate (avoids collapsing tiny results)
# Depth threshold: switch HARVEST -> RICH once the conversation is this deep.
# Tuned so normal easy/medium/both-pass stay harvested (bonus) while the deep
# flip tasks tip into rich (14539 median 125 msgs vs easy/medium ~67-83).
LARGE_THRESHOLD_MSGS = 90      # message-count depth at which a task is "large/hard" -> rich
LARGE_THRESHOLD_TOKENS = 120_000  # token safety net: any single context this big -> rich regardless of depth
# v11.1 break guard. sympy (hard-both-pass) broke under harvest because it ran
# SHALLOW (so depth missed it) yet needed rich context for the precise fix; its
# size/depth/cumulative all OVERLAP medium (which harvests fine), so no static
# size signal separates them. What DOES separate them is behavior: sympy keeps
# hitting the same error round after round (the bug isn't solved until the real
# fix), while easy/medium RESOLVE (recent results go clean). So switch to rich
# (sticky) once the task is past a few rounds AND its recent tool results are
# still error-bearing — i.e. a task that is working hard and still failing needs
# the full context to flip/solve, not the harvest. Cumulative is a secondary
# net for deep/wander cases.
CUM_THRESHOLD = 600_000        # cumulative raw tokens processed -> treat as large -> rich
ERROR_GUARD_MIN_MSGS = 40      # don't apply the error guard until the task has some depth (~12 rounds)
ERROR_GUARD_WINDOW = 4         # how many of the most recent tool results to scan for unresolved errors
ERROR_GUARD_MIN_HITS = 4       # this many error-bearing results in the recent window = "still failing" -> rich
GENTLE_RESULT_CAP = 1_200      # (legacy, unused in v9)
GENTLE_PROTECTED_CAP = 5_000   # (legacy, unused in v9)
# Tool results carrying these markers are the ground truth the agent patches
# against; protect them with larger budgets in every mode.
ERROR_MARKERS = (
    "traceback (most recent call last)",
    "assertionerror",
    "error:",
    "exception:",
    "failed",
    "failures=",
    "errors=",
    "fatal:",
)

# The newest tool interactions stay intact; the very newest are never modified.
# v6: keep the recent-full window tight (4) so older results age into the
# aggressive-truncation zone quickly — that is where the token harvest comes
# from — while the untouchable newest 3 protect the agent's active state.
GENTLE_KEEP_RECENT = 4
GENTLE_UNTOUCHABLE = 3
TIGHT_KEEP_RECENT = 4
TIGHT_UNTOUCHABLE = 2

# aow_bet recent verbatim window. The HOLD boundary for NEXT turn keeps the last
# WINDOW_MSGS *messages* of `working` verbatim-live (the live tail to compress) and HOLDS
# everything older verbatim: hold_boundary = max(frozen_count, len(working) - WINDOW_MSGS),
# computed on `working` (the full input), NOT on the re-pruned result.
#
# WINDOW_MSGS=8 matches m12's untouched recent tail: m12 protects the last
# TIGHT_KEEP_RECENT(=4) results plus their invoking tool-calls ≈ 8 messages. Keeping
# exactly that tail live means the live tail aow recompresses is the SAME small region m12
# treats as fresh, while everything OLDER (the content m12 RE-PRUNES every turn, churning
# its emitted prefix) is HELD VERBATIM by aow. The held prefix then ACCUMULATES across turns
# (reused verbatim from `working`, never re-pruned), growing nominally larger than m12's
# per-turn prune while staying byte-stable turn-to-turn: the bet. The boundary is snapped
# BACK to a tool-call boundary (find_call_index) so a call/result pair is never split, and
# clamped monotonic (>= frozen_count) so the held region never shrinks.
WINDOW_MSGS = 8
# CACHE BET savings ceiling (the core of aow_bet's bet). aow_lite reverted to byte-exact
# m12 whenever the frozen-plus-live result was NOMINALLY larger than m12's ~8k aggressive
# prune (RATIO_MARGIN, +0.5% over m12). That nominal guard is exactly what forced aow_lite
# == m12: a stable frozen prefix is, by construction, looser/larger than m12's freshly
# re-pruned front, so the guard fired on every drop-turn. aow_bet DELETES that guard.
#
# THE REFERENCE FIX (vs the first aow_bet attempt, which ALSO degraded to m12): the ceiling
# must be measured against the TRUE UNCOMPRESSED NATIVE TRAJECTORY size, NOT against
# estimate_tokens(raw_messages). Under the connector's session-rewrite path the next raw
# input is our PREVIOUS COMPRESSED OUTPUT plus a few new turns (~7-8k) — small — so a ceiling
# vs raw_messages fired on every turn that froze real fidelity, re-seeding the freeze each
# turn (the aow_lite failure, reproduced via the ceiling). We track the native size
# monotonically in state (nativeTokens, grown by the bytes of the new native turns each turn)
# and guard: result must stay at or below SAVINGS_CEIL * native_tokens (>= 15% nominal savings
# vs the native trajectory). This keeps the global savings multiplier healthy WHILE allowing
# the full-fidelity frozen prefix to persist and grow nominally larger than m12's ~8k prune —
# that larger-but-byte-stable prefix is what the provider caches at ~0.37x weighted (the bet).
#
# INFLATION-CEILING semantics (the second half of the fix). The guard's job per the task is
# the single safety invariant "NEVER inflate past the TRUE original native trajectory." It is
# NOT a >=15%-savings gate: requiring result to be >=15% SMALLER than native made the ceiling
# fire on exactly the EARLY no-prune turns where result==native==raw (nothing dropped yet) —
# which is precisely when the freeze must FIRST engage to capture the front at full fidelity
# AHEAD of m12's drop frontier. Blocking those turns forced the freeze to start only AFTER m12
# had already churned the front, so aow inherited m12's drops and degraded to m12 (the residual
# bug under the rewrite model). SAVINGS_CEIL is therefore an INFLATION multiplier (>= 1.0): the
# result may be as large as the true native trajectory (a full-fidelity frozen prefix is <=
# native by construction — it is a prefix of a prior output that was itself <= native), and we
# revert ONLY on genuine pathological inflation past native*SAVINGS_CEIL. 1.02 allows ~2% slack
# for token-estimation noise between the additive native accumulator and the per-turn estimate,
# so a stable full-fidelity prefix never trips the guard, while real inflation still reverts to
# byte-exact m12 and re-seeds. The global token-savings multiplier stays healthy because the
# ACTUAL emitted result is always <= native (the head/middle still get m12's structural prune
# in the live region; only the verbatim frozen prefix is held, and it was already <= native).
SAVINGS_CEIL = 1.02
# Char caps (head+tail truncation) applied progressively under budget pressure.
ABS_RESULT_CAP = 40_000
TAIL_RESULT_CAP = 16_000
MID_HEAD, MID_TAIL = 1_000, 400
MID2_HEAD, MID2_TAIL = 500, 200
ASSIST_HEAD, ASSIST_TAIL = 1_200, 300

# Paths like /a/b/c.py, django/utils/html.py:236 — the facts agents rediscover.
PATH_PATTERN = re.compile(r"(?:/)?[\w.-]+(?:/[\w.-]+)+\.[A-Za-z]{1,4}(?::\d+)?")

# Objective loop detection (compliant): identical repeated assistant response, or
# identical repeated tool-call signature, within a recent window. Detection only —
# the ONLY emitted text is one of the two allowed LOOP_REASON_* strings.
LOOP_WINDOW = 12
LOOP_THRESHOLD = 3
LOOP_SIG_ARGS_CLIP = 120
TEST_LINE_PATTERN = re.compile(
    r"^\s*(?:FAILED|ERROR|FAIL|XFAIL)[: ]\S.*$"
    r"|^\s*\S+\.py::\S+.*$"
    r"|^\s*(?:FAIL|ERROR): test\S* \(.*\).*$"
    r"|^.*\bAssertionError\b.*$",
    re.M,
)

# ===========================================================================
# ALLOWED COMPRESSION MARKERS — the ONLY bracketed strings this miner emits.
# Per miner/README_prompting.md §5.1 these are metadata wrappers; they preserve
# instruction meaning/order/requirements/tool-policy/safety/role-policy/output-
# contract exactly. We alias [[CMP]]/[[/CMP]] to the spelled-out start/end markers
# ONCE (allowed by the README) so the two forms are interchangeable downstream.
# ===========================================================================
CMP_START = "[[CMP]]"            # alias of "Compressed text starts here"
CMP_END = "[[/CMP]]"             # alias of "Compressed text ends here"
CMP_START_LONG = "Compressed text starts here"
CMP_END_LONG = "Compressed text ends here"


def cmp_block(inner: str = "") -> str:
    """Wrap a compressed/truncated region in the allowed [[CMP]]…[[/CMP]] markers.
    Empty/fully-elided regions become "[[CMP]][[/CMP]]". The kept head/tail lines go
    OUTSIDE the markers; only the elided middle is wrapped — the marker is metadata
    only and changes no instruction meaning."""
    inner = inner.strip("\n")
    if not inner:
        return f"{CMP_START}{CMP_END}"
    return f"{CMP_START}\n{inner}\n{CMP_END}"


def block_open(n: int) -> str:
    return f"[[BLOCK {n}]]"


def block_close(n: int) -> str:
    return f"[[/BLOCK {n}]]"


def same_response_ref(n: int) -> str:
    """The literal allowed back-reference string for a deduped/superseded copy."""
    return f"Same response as in [[BLOCK {n}]]."


# Allowed loop-detection reason strings (README §5.2). These are the ONLY strings
# the loop guard may emit — nothing else, no steering, no task restatement.
LOOP_REASON_ASSISTANT = "loop_detected: repeated assistant response"
LOOP_REASON_TOOLCALL = "loop_detected: repeated tool call signature"


# ---------------------------------------------------------------------------
# Generic helpers (shapes proven against the connector by the reference miner)
# ---------------------------------------------------------------------------

def normalize_role(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    lowered = value.strip().lower().replace("_", "").replace("-", "")
    if lowered == "toolresult":
        return "toolResult"
    return lowered


def extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(extract_text(item) for item in value)
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        if isinstance(value.get("content"), str):
            return value["content"]
        return "\n".join(extract_text(item) for item in value.values())
    return str(value)


def collapse_ws(value: str) -> str:
    return " ".join(value.split())


def clip(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: max(0, limit - 1)] + "…"


def estimate_tokens(messages: list[Any]) -> int:
    total_chars = sum(
        len(extract_text(message.get("content")))
        for message in messages
        if isinstance(message, dict)
    )
    return max(1, math.ceil(total_chars / CHARS_PER_TOKEN)) if messages else 0


def final_token_estimate(messages: list[Any]) -> int:
    try:
        import tiktoken  # available in the compression-service image, cached offline

        encoder = tiktoken.get_encoding("cl100k_base")
        joined = "\n".join(
            extract_text(message.get("content"))
            for message in messages
            if isinstance(message, dict)
        )
        return len(encoder.encode(joined, disallowed_special=()))
    except Exception:
        return estimate_tokens(messages)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_file_part(value: Any, fallback: str = "session") -> str:
    raw = value.strip() if isinstance(value, str) and value.strip() else fallback
    normalized = "".join(char if char.isalnum() or char in "_.-" else "-" for char in raw)
    normalized = normalized.strip("-")
    return (normalized or fallback)[:120]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def fingerprint_messages(messages: list[Any]) -> str:
    return hashlib.sha256(canonical_json(messages).encode("utf-8")).hexdigest()


def get_params(payload: dict[str, Any]) -> dict[str, Any]:
    params = payload.get("params")
    return params if isinstance(params, dict) else payload


def get_messages(payload: dict[str, Any]) -> list[Any]:
    messages = get_params(payload).get("messages")
    return messages if isinstance(messages, list) else []


def resolve_plugin_dir(payload: dict[str, Any]) -> Path:
    value = payload.get("pluginDir")
    if isinstance(value, str) and value.strip():
        return Path(value.strip())
    return Path(__file__).resolve().parent


def resolve_session_identity(payload: dict[str, Any]) -> tuple[str, str | None, str | None]:
    params = get_params(payload)
    session_id = params.get("sessionId") if isinstance(params.get("sessionId"), str) else None
    session_key = params.get("sessionKey") if isinstance(params.get("sessionKey"), str) else None
    identity = session_id or session_key or "session"
    return safe_file_part(identity), session_id, session_key


# ---------------------------------------------------------------------------
# Incremental state (dual fingerprint: previous raw input OR previous output)
# ---------------------------------------------------------------------------

def resolve_state_path(payload: dict[str, Any]) -> Path:
    session_part, _, _ = resolve_session_identity(payload)
    return resolve_plugin_dir(payload) / "logs" / STATE_DIR_NAME / f"{session_part}.json"


def load_state(state_path: Path) -> dict[str, Any] | None:
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(state, dict) or state.get("version") != STATE_VERSION:
        return None
    if not isinstance(state.get("messages"), list):
        return None
    return state


def save_state(
    state_path: Path,
    payload: dict[str, Any],
    raw_messages: list[Any],
    output_messages: list[Any],
    *,
    mode: str = "passthrough",
    max_observed: int = 0,
    cumulative_observed: int = 0,
    escalation: dict[str, Any] | None = None,
    frozen_prefix: list[Any] | None = None,
    ever_touched_rich: bool = False,
    native_tokens: int = 0,
) -> None:
    _, session_id, session_key = resolve_session_identity(payload)
    # AOW-lite freeze state (NEW). frozenPrefix is the byte-exact, already-compressed
    # output messages at the FRONT of this turn's output that we will reuse verbatim
    # next turn; frozenCount is its length; everTouchedRich is sticky once the session
    # has ever entered rich mode (after which the freeze is permanently disabled and
    # this miner behaves exactly like m12). All default safely so a fresh/old state
    # reproduces m12's behavior with no freeze.
    frozen_prefix = list(frozen_prefix or [])
    state = {
        "version": STATE_VERSION,
        "updatedAt": utc_now(),
        "sessionId": session_id,
        "sessionKey": session_key,
        "sourceMessageCount": len(raw_messages),
        "sourceFingerprint": fingerprint_messages(raw_messages),
        "outputMessageCount": len(output_messages),
        "outputFingerprint": fingerprint_messages(output_messages),
        "messageCount": len(output_messages),
        "mode": mode,
        "maxObservedTokens": int(max_observed),
        "cumulativeObserved": int(cumulative_observed),
        "escalation": dict(escalation or {}),
        "frozenPrefix": frozen_prefix,
        "frozenCount": len(frozen_prefix),
        "everTouchedRich": bool(ever_touched_rich),
        # nativeTokens (NEW — the savings-ceiling reference fix). The TRUE size of the
        # UNCOMPRESSED native trajectory the connector would have built absent this miner,
        # tracked MONOTONICALLY in state. Under the connector's session-rewrite path the
        # next raw input is our PREVIOUS COMPRESSED OUTPUT + newly appended native turns,
        # so estimate_tokens(raw_messages) is the SMALL already-compressed feedback, NOT
        # the native size. Measuring the savings ceiling against that small value forced
        # aow_bet to revert on every turn that froze real fidelity (aow_lite's failure
        # reproduced via the ceiling). We instead persist the native size and grow it by
        # the bytes of the NEW native turns each turn (raw_messages[matched_count:] are
        # byte-exact native appends). The savings ceiling then guards aow_tokens against
        # this TRUE native size, allowing a stable full-fidelity frozen prefix to persist.
        "nativeTokens": int(native_tokens),
        "messages": output_messages,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = state_path.with_suffix(f"{state_path.suffix}.tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False) + "\n", encoding="utf-8")
    temp_path.replace(state_path)


def resolve_stateful_messages(
    payload: dict[str, Any], raw_messages: list[Any]
) -> tuple[list[Any], dict[str, Any], Path, dict[str, Any]]:
    state_path = resolve_state_path(payload)
    state = load_state(state_path)
    # AOW-lite freeze fields are read with safe defaults: a missing/old state yields
    # an empty frozenPrefix, frozenCount 0, everTouchedRich False -> the harvest path
    # then runs m12's exact code (compress the whole working set, no freeze) on turn 1.
    _frozen = state.get("frozenPrefix") if state else None
    if not isinstance(_frozen, list):
        _frozen = []
    extras = {
        "mode": (state.get("mode") if state else None) or "passthrough",
        "maxObservedTokens": int(state.get("maxObservedTokens") or 0) if state else 0,
        "cumulativeObserved": int(state.get("cumulativeObserved") or 0) if state else 0,
        "escalation": dict(state.get("escalation") or {}) if state else {},
        "frozenPrefix": _frozen,
        "frozenCount": len(_frozen),
        "everTouchedRich": bool(state.get("everTouchedRich")) if state else False,
        # nativeTokens carries the monotonically-tracked TRUE native trajectory size
        # (defaults to 0 on a fresh/old state -> first turn seeds it from raw_messages).
        "nativeTokens": int(state.get("nativeTokens") or 0) if state else 0,
    }
    metadata: dict[str, Any] = {
        "statePath": str(state_path),
        "stateLoaded": False,
        "stateResetReason": None,
        "rawInputMessageCount": len(raw_messages),
        "newMessageCount": len(raw_messages),
        "workingMessageCount": len(raw_messages),
    }
    if state is None:
        return raw_messages, metadata, state_path, extras

    # The session file rewrite makes the next raw input start with our previous
    # output; without the rewrite it starts with the previous raw input. Accept
    # either prefix, preferring whichever matches.
    candidates = []
    for count_key, fp_key in (
        ("outputMessageCount", "outputFingerprint"),
        ("sourceMessageCount", "sourceFingerprint"),
    ):
        count = state.get(count_key)
        fingerprint = state.get(fp_key)
        if isinstance(count, int) and 0 <= count <= len(raw_messages) and isinstance(fingerprint, str):
            candidates.append((count, fingerprint, count_key))

    for count, fingerprint, count_key in candidates:
        if fingerprint_messages(raw_messages[:count]) == fingerprint:
            new_messages = raw_messages[count:]
            working = [*state["messages"], *new_messages] if count_key == "sourceMessageCount" else raw_messages
            metadata.update(
                {
                    "stateLoaded": True,
                    "stateMatchedPrefix": count_key,
                    "newMessageCount": len(new_messages),
                    "workingMessageCount": len(working),
                }
            )
            return working, metadata, state_path, extras

    metadata["stateResetReason"] = "no_prefix_match"
    return raw_messages, metadata, state_path, extras


# ---------------------------------------------------------------------------
# Sanitization (same rules as the reference miner)
# ---------------------------------------------------------------------------

def sanitize_content(content: Any) -> tuple[Any, bool]:
    if not isinstance(content, list):
        return content, False
    sanitized: list[Any] = []
    changed = False
    for block in content:
        if isinstance(block, dict) and block.get("type") == "thinking":
            changed = True
            continue
        sanitized.append(block)
    return sanitized, changed


def has_runtime_content(content: Any) -> bool:
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, (list, dict)):
        return bool(content)
    return content is not None


def is_failed_assistant_placeholder(message: Any) -> bool:
    if not isinstance(message, dict) or normalize_role(message.get("role")) != "assistant":
        return False
    if not isinstance(message.get("errorMessage"), str):
        return False
    content = message.get("content")
    return content in (None, "") or content == []


def sanitize_messages(messages: list[Any]) -> tuple[list[Any], bool]:
    sanitized: list[Any] = []
    changed = False
    for message in messages:
        if is_failed_assistant_placeholder(message):
            changed = True
            continue
        if not isinstance(message, dict):
            sanitized.append(message)
            continue
        next_message = message
        next_content, content_changed = sanitize_content(message.get("content"))
        if content_changed:
            next_message = copy.deepcopy(message)
            next_message["content"] = next_content
            changed = True
        if (
            normalize_role(next_message.get("role")) != "toolResult"
            and not has_runtime_content(next_message.get("content"))
        ):
            changed = True
            continue
        sanitized.append(next_message)
    return (sanitized if changed else messages), changed


# ---------------------------------------------------------------------------
# Tool call / tool result plumbing
# ---------------------------------------------------------------------------

def extract_tool_result_ids(message: Any) -> set[str]:
    if not isinstance(message, dict) or normalize_role(message.get("role")) != "toolResult":
        return set()
    ids: set[str] = set()
    for field in ("toolCallId", "toolUseId", "id"):
        value = message.get(field)
        if isinstance(value, str) and value.strip():
            ids.add(value.strip())
    return ids


def iter_tool_call_blocks(message: Any) -> list[dict[str, Any]]:
    if not isinstance(message, dict) or normalize_role(message.get("role")) != "assistant":
        return []
    blocks: list[dict[str, Any]] = []
    content = message.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "toolCall":
                blocks.append(block)
    for field in ("toolCalls", "tool_calls"):
        tool_calls = message.get(field)
        if isinstance(tool_calls, list):
            for tool_call in tool_calls:
                if isinstance(tool_call, dict):
                    blocks.append(tool_call)
    return blocks


def extract_tool_call_ids(message: Any) -> set[str]:
    ids: set[str] = set()
    for block in iter_tool_call_blocks(message):
        value = block.get("id")
        if isinstance(value, str) and value.strip():
            ids.add(value.strip())
    return ids


def strip_tool_call_blocks(message: Any, remove_ids: set[str]) -> Any:
    """Remove the toolCall blocks for `remove_ids`, keeping everything else."""
    if not isinstance(message, dict) or not remove_ids:
        return message
    stripped = copy.deepcopy(message)
    content = stripped.get("content")
    if isinstance(content, list):
        stripped["content"] = [
            block
            for block in content
            if not (
                isinstance(block, dict)
                and block.get("type") == "toolCall"
                and isinstance(block.get("id"), str)
                and block["id"].strip() in remove_ids
            )
        ]
    for field in ("toolCalls", "tool_calls"):
        tool_calls = stripped.get(field)
        if isinstance(tool_calls, list):
            stripped[field] = [
                tool_call
                for tool_call in tool_calls
                if not (
                    isinstance(tool_call, dict)
                    and isinstance(tool_call.get("id"), str)
                    and tool_call["id"].strip() in remove_ids
                )
            ]
    return stripped


def assistant_is_empty(message: Any) -> bool:
    if not isinstance(message, dict):
        return False
    if iter_tool_call_blocks(message):
        return False
    return not collapse_ws(extract_text(message.get("content")))


def orphan_ids(messages: list[Any]) -> tuple[set[str], set[str]]:
    """Return (result ids without a call, call ids without a result)."""
    call_ids: set[str] = set()
    result_ids: set[str] = set()
    for message in messages:
        call_ids.update(extract_tool_call_ids(message))
        result_ids.update(extract_tool_result_ids(message))
    return result_ids - call_ids, call_ids - result_ids


# ---------------------------------------------------------------------------
# Truncation (shape preserving: edits text fields in place, never block types)
# ---------------------------------------------------------------------------

def truncate_text(value: str, head: int, tail: int) -> str:
    if len(value) <= head + tail + 80:
        return value
    # Kept head/tail sit OUTSIDE the markers; the elided middle is the compressed
    # region, wrapped in the allowed empty [[CMP]][[/CMP]] marker (metadata only).
    return f"{value[:head]}\n{cmp_block()}\n{value[-tail:] if tail else ''}"


def truncate_message(message: Any, head: int, tail: int) -> tuple[Any, bool]:
    if not isinstance(message, dict):
        return message, False
    content = message.get("content")
    if isinstance(content, str):
        truncated = truncate_text(content, head, tail)
        if truncated == content:
            return message, False
        out = copy.deepcopy(message)
        out["content"] = truncated
        return out, True
    if isinstance(content, list):
        changed = False
        new_blocks: list[Any] = []
        for block in content:
            if isinstance(block, dict):
                new_block = block
                for field in ("text", "content"):
                    value = block.get(field)
                    if isinstance(value, str):
                        truncated = truncate_text(value, head, tail)
                        if truncated != value:
                            new_block = copy.deepcopy(block)
                            new_block[field] = truncated
                            changed = True
                        break
                new_blocks.append(new_block)
            else:
                new_blocks.append(block)
        if not changed:
            return message, False
        out = copy.deepcopy(message)
        out["content"] = new_blocks
        return out, True
    return message, False


def is_error_bearing(message: Any) -> bool:
    text = extract_text(message.get("content"))[:20_000].lower() if isinstance(message, dict) else ""
    return any(marker in text for marker in ERROR_MARKERS)


def recent_errors(messages: list[Any], window: int = ERROR_GUARD_WINDOW) -> int:
    """Count error-bearing tool results among the most recent `window` results.
    A task whose recent results are still error-bearing is working hard and still
    failing — it needs rich context to flip/solve, not the harvest. (Easy/medium
    tasks RESOLVE: their recent results go clean once the fix lands.)"""
    hits = 0
    seen = 0
    for message in reversed(messages):
        if not isinstance(message, dict) or normalize_role(message.get("role")) != "toolResult":
            continue
        seen += 1
        if is_error_bearing(message):
            hits += 1
        if seen >= window:
            break
    return hits


# ---------------------------------------------------------------------------
# v8: rule-first extractive summarization of bulky tool outputs.
# Instead of blind head/tail truncation, keep the most INFORMATIVE lines:
# always pin errors / failing tests / file paths / code signatures /
# active-file lines / edit (diff) lines; then fill the remaining budget with
# the highest TF-IDF-scoring leftover lines. Original line order preserved.
# Same token budget as v6 truncation, far higher information retention →
# the agent keeps the clues that drive hard-flips and avoids breaks.
# ---------------------------------------------------------------------------

_SIG_PATTERN = re.compile(r"\b(?:def|class)\s+\w+|\bfunction\s+\w+|=>\s*\{|\b\w+\s*\([^)]*\)\s*:")
_DIFF_PATTERN = re.compile(r"^\s*(?:[+\-]|@@|diff --git|---|\+\+\+)")


def _basenames(paths: set[str]) -> set[str]:
    out: set[str] = set()
    for p in paths:
        p = p.split(":")[0]
        out.add(p)
        out.add(p.rsplit("/", 1)[-1])
    return {b for b in out if len(b) >= 4}


def active_paths(messages: list[Any], window: int = 10) -> set[str]:
    """File paths the agent is currently working (mentioned in recent messages
    and recent tool-call args)."""
    paths: set[str] = set()
    for message in messages[-window:]:
        if not isinstance(message, dict):
            continue
        text = extract_text(message.get("content"))
        for block in iter_tool_call_blocks(message):
            for field in ("arguments", "args", "input"):
                if field in block:
                    text += "\n" + extract_text(block[field])
        paths.update(PATH_PATTERN.findall(text))
    return _basenames(paths)


def _line_is_pinned(line: str, active: frozenset) -> bool:
    if not line.strip():
        return False
    low = line.lower()
    if any(marker in low for marker in ERROR_MARKERS):
        return True
    if TEST_LINE_PATTERN.search(line):
        return True
    if _SIG_PATTERN.search(line):
        return True
    if _DIFF_PATTERN.match(line):
        return True
    found = PATH_PATTERN.findall(line)
    if found:
        if not active:
            return True  # any file path is signal
        if _basenames(set(found)) & active:
            return True
        return True  # paths are cheap signal; keep them
    return False


def _line_scores(lines: list[str]) -> list[float]:
    """Informativeness per line via TF-IDF; graceful fallback if unavailable."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        docs = [l if l.strip() else " " for l in lines]
        matrix = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", max_features=4000).fit_transform(docs)
        return matrix.sum(axis=1).A1.tolist()
    except Exception:
        # fallback: distinct-token count (favors content-rich lines over boilerplate)
        return [len(set(re.findall(r"\w+", l))) for l in lines]


def extractive_compress(text: str, target_chars: int, active: frozenset = frozenset()) -> tuple[str, bool]:
    if not isinstance(text, str) or len(text) <= target_chars:
        return text, False
    lines = text.split("\n")
    n = len(lines)
    keep = {i for i in range(n) if _line_is_pinned(lines[i], active)}
    used = sum(len(lines[i]) + 1 for i in keep)
    remaining = [i for i in range(n) if i not in keep and lines[i].strip()]
    if used < target_chars and remaining:
        scores = _line_scores([lines[i] for i in remaining])
        for idx, _ in sorted(zip(remaining, scores), key=lambda x: (-x[1], x[0])):
            if used >= target_chars:
                break
            keep.add(idx)
            used += len(lines[idx]) + 1
    if len(keep) >= n:
        return text, False
    out: list[str] = []
    prev = -1
    for i in sorted(keep):
        if i > prev + 1:
            out.append("…")
        out.append(lines[i])
        prev = i
    if prev < n - 1:
        out.append("…")
    result = "\n".join(out)
    if len(result) >= len(text):  # extraction didn't help → fall back to truncation
        return truncate_text(text, int(target_chars * 0.75), int(target_chars * 0.25)), True
    return result, True


def extractive_message(message: Any, target_chars: int, active: frozenset) -> tuple[Any, bool]:
    if not isinstance(message, dict):
        return message, False
    content = message.get("content")
    if isinstance(content, str):
        new, changed = extractive_compress(content, target_chars, active)
        if not changed:
            return message, False
        out = copy.deepcopy(message)
        out["content"] = new
        return out, True
    if isinstance(content, list):
        changed = False
        new_blocks: list[Any] = []
        for block in content:
            if isinstance(block, dict):
                new_block = block
                for field in ("text", "content"):
                    value = block.get(field)
                    if isinstance(value, str):
                        new, ch = extractive_compress(value, target_chars, active)
                        if ch:
                            new_block = copy.deepcopy(block)
                            new_block[field] = new
                            changed = True
                        break
                new_blocks.append(new_block)
            else:
                new_blocks.append(block)
        if not changed:
            return message, False
        out = copy.deepcopy(message)
        out["content"] = new_blocks
        return out, True
    return message, False


# ---------------------------------------------------------------------------
# COMPLIANT LOOP DETECTION (README §2 + §5.2).
# Detection is purely OBJECTIVE and the ONLY emitted text is one of the two
# allowed reason strings. There is NO steering, NO task restatement, NO forced
# completion, NO strategy/tool-policy change. A loop-guard user message carries
# nothing but the matching allowed LOOP_REASON_* string, so successful (non-loop)
# behavior is left entirely unchanged. The guard is OPTIONAL — it appends a
# message only when an objective loop is detected.
# ---------------------------------------------------------------------------

def _is_loop_guard_message(message: Any) -> bool:
    """A loop-guard message we appended on a prior turn: a user message whose text
    is exactly one of the allowed loop-reason strings. Identified so we can strip
    our own prior guard before re-deciding (idempotent across turns)."""
    if not isinstance(message, dict) or normalize_role(message.get("role")) != "user":
        return False
    text = extract_text(message.get("content")).strip()
    return text in (LOOP_REASON_ASSISTANT, LOOP_REASON_TOOLCALL)


def strip_loop_guard(messages: list[Any]) -> list[Any]:
    return [m for m in messages if not _is_loop_guard_message(m)]


def detect_loop_reason(messages: list[Any]) -> str:
    """Return the matching allowed loop-reason string if an OBJECTIVE loop is
    present in the recent window, else "". Two objective signals:
      - repeated ASSISTANT response: an identical assistant message (same
        normalized text + tool-call signatures) recurs >= LOOP_THRESHOLD times;
      - repeated TOOL-CALL signature: the same tool name+args (regardless of
        result) recurs >= LOOP_THRESHOLD times.
    No content beyond the recurrence count drives the decision; nothing about the
    task, strategy, or desired outcome is considered."""
    # ---- repeated assistant response ----
    assistant_sigs: list[str] = []
    for message in messages:
        if not isinstance(message, dict) or normalize_role(message.get("role")) != "assistant":
            continue
        text = collapse_ws(extract_text(message.get("content")))
        call_sig = "|".join(sorted(
            f"{(b.get('name') or b.get('toolName') or 'tool')}"
            f"({clip(collapse_ws(extract_text(b.get('arguments') or b.get('args') or b.get('input') or '')), LOOP_SIG_ARGS_CLIP)})"
            for b in iter_tool_call_blocks(message)
        ))
        digest = hashlib.sha256(f"{text}#{call_sig}".encode("utf-8")).hexdigest()
        assistant_sigs.append(digest)
    recent_assist = assistant_sigs[-LOOP_WINDOW:]
    acounts: dict[str, int] = {}
    for sig in recent_assist:
        acounts[sig] = acounts.get(sig, 0) + 1
    if any(n >= LOOP_THRESHOLD for n in acounts.values()):
        return LOOP_REASON_ASSISTANT

    # ---- repeated tool-call signature ----
    call_sigs: list[str] = []
    for message in messages:
        for block in iter_tool_call_blocks(message):
            name = block.get("name") or block.get("toolName") or "tool"
            args = clip(collapse_ws(extract_text(
                block.get("arguments") or block.get("args") or block.get("input") or ""
            )), LOOP_SIG_ARGS_CLIP)
            call_sigs.append(f"{name}|{args}")
    recent_calls = call_sigs[-LOOP_WINDOW:]
    ccounts: dict[str, int] = {}
    for sig in recent_calls:
        ccounts[sig] = ccounts.get(sig, 0) + 1
    if any(n >= LOOP_THRESHOLD for n in ccounts.values()):
        return LOOP_REASON_TOOLCALL

    return ""


def append_loop_guard(messages: list[Any]) -> list[Any]:
    """If an objective loop is detected, append a user message whose ONLY content
    is the matching allowed loop-reason string. Otherwise return messages
    unchanged. This is the entire prompt-side surface of the miner — no other text."""
    reason = detect_loop_reason(messages)
    if not reason:
        return messages
    return [*messages, {"role": "user", "content": [{"type": "text", "text": reason}]}]


# ---------------------------------------------------------------------------
# Gentle mode: truncation-only compression for mid-size contexts.
# Never drops a message, never touches user/system/assistant content, keeps
# toolCall/toolResult pairing untouched by construction. Old bulky tool
# results get head+tail truncation (error-bearing ones keep larger budgets);
# exact-duplicate / near-duplicate old results are replaced with the allowed
# "Same response as in [[BLOCK N]]." back-reference to the surviving latest copy,
# which is labelled [[BLOCK N]]…[[/BLOCK N]]. The message envelope + tool_call_id
# are always kept — only the body/content text changes.
# ---------------------------------------------------------------------------

def _replace_text_fields(message: Any, marker: str) -> Any:
    out = copy.deepcopy(message)
    content = out.get("content")
    if isinstance(content, str):
        out["content"] = marker
        return out
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                for field in ("text", "content"):
                    if isinstance(block.get(field), str):
                        block[field] = marker
                        break
    return out


def _wrap_first_text_field(message: Any, open_str: str, close_str: str) -> Any:
    """Wrap the FIRST string text field of a message in open_str…close_str without
    changing the field's content. Used to label a surviving copy [[BLOCK N]]…
    [[/BLOCK N]]; the body between the markers is byte-identical to the original."""
    out = copy.deepcopy(message)
    content = out.get("content")
    if isinstance(content, str):
        out["content"] = f"{open_str}\n{content}\n{close_str}"
        return out
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                for field in ("text", "content"):
                    if isinstance(block.get(field), str):
                        block[field] = f"{open_str}\n{block[field]}\n{close_str}"
                        return out
    return out


def _is_load_bearing(message: Any, active: frozenset) -> bool:
    """A tool result we must keep FULL: errors/tests, the agent's active files,
    or content with edit/diff lines. Everything else is candidate for trimming.
    Active-file match is a substring test (a file's own content rarely repeats
    its slashed path) — deliberately inclusive: over-keeping is the safe error."""
    if is_error_bearing(message):
        return True
    text = extract_text(message.get("content"))
    if active and any(b in text for b in active):
        return True
    for line in text.split("\n"):
        if _DIFF_PATTERN.match(line) or TEST_LINE_PATTERN.search(line):
            return True
    return False


def _norm_for_neardup(text: str) -> str:
    """Aggressive normalization for near-duplicate detection: lowercase, drop
    digits (line numbers / counts / timestamps), collapse every non-letter run to
    a single space. Two tool results that differ only in incidental numbering or
    punctuation normalize to the identical string and hash the same."""
    low = re.sub(r"\d+", "", text.lower())
    low = re.sub(r"[^a-z]+", " ", low)
    return " ".join(low.split())


def compress_gently(messages: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    # RICH+RELIABLE compression. NEVER drops a message and never touches the recent
    # working window or any load-bearing result. Exact-duplicate AND near-duplicate
    # old, non-load-bearing tool results are replaced with the allowed
    # "Same response as in [[BLOCK N]]." back-reference to the surviving latest copy
    # (labelled [[BLOCK N]]…[[/BLOCK N]]). Everything else is preserved or lightly
    # extractive-trimmed — reliability and hard flips are unaffected.
    info: dict[str, Any] = {
        "truncatedResultCount": 0,
        "duplicateResultCount": 0,
        "nearDuplicateResultCount": 0,
        "protectedResultCount": 0,
        "reason": "nothing_to_remove",
    }
    result_indices = [
        index
        for index, message in enumerate(messages)
        if isinstance(message, dict) and normalize_role(message.get("role")) == "toolResult"
    ]
    # Last RICH_INTACT_MSGS messages stay byte-intact (the agent's working set).
    intact = set(range(max(0, len(messages) - RICH_INTACT_MSGS), len(messages)))
    active = frozenset(active_paths(messages))

    # Newest-first registries: exact-duplicate hash plus a normalized near-duplicate
    # hash. Older copies become a "Same response as in [[BLOCK N]]." back-reference;
    # the newest (latest) copy is the SURVIVOR, labelled [[BLOCK N]]…[[/BLOCK N]].
    # Exact-dup back-ref is safe for any result (an identical later copy survives);
    # near-dup back-ref is restricted to old, non-load-bearing content (the copies
    # are NOT identical, so we must not collapse one the agent needs). We map each
    # duplicate index -> the survivor index it references, then number survivors.
    survivor_for_hash: dict[str, int] = {}      # exact-dup hash -> survivor index
    survivor_for_norm: dict[str, int] = {}      # near-dup hash  -> survivor index
    dup_ref: dict[int, int] = {}                # duplicate index -> survivor index
    near_dup_ref: dict[int, int] = {}           # near-dup index  -> survivor index
    for index in reversed(result_indices):      # newest first → first seen is survivor
        text = collapse_ws(extract_text(messages[index].get("content")))
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        norm = _norm_for_neardup(text)
        norm_hash = (
            hashlib.sha256(norm.encode("utf-8")).hexdigest()
            if len(norm) >= NEARDUP_MIN_CHARS
            else ""
        )
        if digest in survivor_for_hash and index not in intact:
            dup_ref[index] = survivor_for_hash[digest]
        elif (
            norm_hash
            and norm_hash in survivor_for_norm
            and index not in intact
            and not _is_load_bearing(messages[index], active)
        ):
            near_dup_ref[index] = survivor_for_norm[norm_hash]
        survivor_for_hash.setdefault(digest, index)
        if norm_hash:
            survivor_for_norm.setdefault(norm_hash, index)

    # Assign a stable [[BLOCK N]] number to each survivor that is actually
    # referenced by at least one earlier copy (numbered by document order so the
    # label is deterministic). Survivors with no referrer are left untouched.
    referenced_survivors = sorted(set(dup_ref.values()) | set(near_dup_ref.values()))
    block_number: dict[int, int] = {idx: n for n, idx in enumerate(referenced_survivors, 1)}

    output: list[Any] = []
    for index, message in enumerate(messages):
        role = normalize_role(message.get("role")) if isinstance(message, dict) else ""
        if role == "toolResult" and index not in intact:
            if index in dup_ref:
                n = block_number[dup_ref[index]]
                message = _replace_text_fields(message, same_response_ref(n))
                info["duplicateResultCount"] += 1
            elif index in near_dup_ref:
                n = block_number[near_dup_ref[index]]
                message = _replace_text_fields(message, same_response_ref(n))
                info["nearDuplicateResultCount"] += 1
            elif _is_load_bearing(message, active):
                # keep full (guard only against pathological size)
                message, did = extractive_message(message, RICH_PROTECTED_CAP, active)
                info["protectedResultCount"] += 1
                info["truncatedResultCount"] += int(did)
            else:
                # clearly stale, unrelated bulk → light extractive trim, generous cap
                message, did = extractive_message(message, RICH_STALE_CAP, active)
                info["truncatedResultCount"] += int(did)
        elif role == "toolResult" and index in block_number:
            # Survivor copy referenced by an earlier duplicate (and in the intact
            # tail): label it [[BLOCK N]]…[[/BLOCK N]] so the back-reference resolves.
            message = _wrap_first_text_field(message, block_open(block_number[index]), block_close(block_number[index]))
        output.append(message)

    # Survivors NOT in the intact tail also need their [[BLOCK N]] label. The branch
    # above only labels intact-tail survivors; label the rest here (the non-intact
    # survivors fell through to extractive trim, which we must wrap, not skip).
    for index in referenced_survivors:
        if index in intact:
            continue
        msg = output[index]
        if isinstance(msg, dict) and normalize_role(msg.get("role")) == "toolResult":
            output[index] = _wrap_first_text_field(msg, block_open(block_number[index]), block_close(block_number[index]))

    if (
        info["truncatedResultCount"]
        or info["duplicateResultCount"]
        or info["nearDuplicateResultCount"]
    ):
        info["reason"] = "gentle"
    return output, info


# ---------------------------------------------------------------------------
# Structural compression
# ---------------------------------------------------------------------------

def message_cost(message: Any) -> int:
    return len(extract_text(message.get("content"))) if isinstance(message, dict) else 0


def find_call_index(messages: list[Any], result_index: int, call_ids_cache: list[set[str]]) -> Optional[int]:
    wanted = extract_tool_result_ids(messages[result_index])
    if wanted:
        for index in range(result_index - 1, -1, -1):
            if call_ids_cache[index] & wanted:
                return index
    for index in range(result_index - 1, -1, -1):
        if call_ids_cache[index]:
            return index
    return None


def compress_structurally(
    messages: list[Any],
    escalation: dict[str, Any] | None = None,
    target_tokens: int = TARGET_TOKENS,
) -> tuple[list[Any], dict[str, Any]]:
    escalation = escalation if escalation is not None else {}
    info: dict[str, Any] = {
        "droppedInteractionCount": 0,
        "truncatedResultCount": 0,
        "truncatedAssistantCount": 0,
        "duplicateResultCount": 0,
    }
    first_user_index = next(
        (
            index
            for index, message in enumerate(messages)
            if isinstance(message, dict) and normalize_role(message.get("role")) == "user"
        ),
        None,
    )
    if first_user_index is None:
        return messages, {**info, "reason": "missing_first_user_message"}

    call_ids_cache = [extract_tool_call_ids(message) for message in messages]
    result_indices = [
        index
        for index, message in enumerate(messages)
        if isinstance(message, dict) and normalize_role(message.get("role")) == "toolResult"
    ]
    costs = [message_cost(message) for message in messages]
    total_chars = sum(costs)
    target_chars = target_tokens * CHARS_PER_TOKEN
    # Under pressure, prune past the target so following rounds are pure
    # appends (byte-stable prefix → provider cache hits) until pressure returns.
    relief_chars = int(target_chars * PRESSURE_RELIEF)

    # Tail zone: the invoking call of the TIGHT_KEEP_RECENT-th newest result onward.
    recent_results = result_indices[-TIGHT_KEEP_RECENT:]
    tail_start = len(messages)
    for result_index in recent_results:
        call_index = find_call_index(messages, result_index, call_ids_cache)
        tail_start = min(tail_start, result_index, call_index if call_index is not None else result_index)
    if not result_indices:
        tail_start = max(first_user_index + 1, len(messages) - 8)

    # Classify pre-tail interactions, oldest first.
    interactions: list[dict[str, Any]] = []
    seen_hashes: dict[str, int] = {}
    for result_index in reversed([i for i in result_indices if i < tail_start]):
        result_ids = extract_tool_result_ids(messages[result_index])
        call_index = find_call_index(messages, result_index, call_ids_cache)
        digest_hash = hashlib.sha256(
            collapse_ws(extract_text(messages[result_index].get("content"))).encode("utf-8")
        ).hexdigest()
        duplicate_of = seen_hashes.get(digest_hash)
        seen_hashes.setdefault(digest_hash, result_index)
        interactions.append(
            {
                "result_index": result_index,
                "call_index": call_index,
                "ids": result_ids,
                "cost": costs[result_index],
                "duplicate": duplicate_of is not None,
                # Error/test output is what the agent patches against — keep
                # it longer and sacrifice it last.
                "protected": is_error_bearing(messages[result_index]),
                # Drops require a strippable call block; otherwise truncate only.
                "droppable": bool(result_ids) and call_index is not None,
                "mode": "trunc",
            }
        )
    interactions.reverse()  # oldest first
    for item in interactions:
        if item["protected"]:
            item["mode"] = "trunc-protected"

    # The newest few messages are never modified (the agent needs them intact).
    untouchable_msgs = set(range(max(0, len(messages) - TIGHT_UNTOUCHABLE), len(messages)))

    def planned_chars(assist_cap: bool, trunc2: bool, tail_cap: bool) -> int:
        total = 0
        dropped_count = 0
        tail_result_set = set(result_indices[-TIGHT_KEEP_RECENT:])
        untouchable = set(result_indices[-TIGHT_UNTOUCHABLE:])
        modes = {item["result_index"]: item["mode"] for item in interactions}
        for index, message in enumerate(messages):
            role = normalize_role(message.get("role")) if isinstance(message, dict) else ""
            cost = costs[index]
            if role == "toolResult":
                if index in modes:
                    mode = modes[index]
                    if mode == "drop":
                        dropped_count += 1
                    elif mode == "trunc-protected":
                        total += min(cost, GENTLE_PROTECTED_CAP + 80)
                    elif trunc2:
                        total += min(cost, MID2_HEAD + MID2_TAIL + 80)
                    else:
                        total += min(cost, MID_HEAD + MID_TAIL + 80)
                elif index in tail_result_set and index not in untouchable and tail_cap:
                    total += min(cost, TAIL_RESULT_CAP)
                else:
                    total += min(cost, ABS_RESULT_CAP)
            elif role == "assistant" and (
                (assist_cap and index < tail_start) or (tail_cap and index not in untouchable_msgs)
            ):
                total += min(cost, ASSIST_HEAD + ASSIST_TAIL + 80)
            else:
                total += cost
        # Dropped interactions now leave NO trace (no digest is injected — the
        # private history-digest marker is banned next round), so a dropped
        # interaction contributes 0 chars. dropped_count is tracked only for info.
        _ = dropped_count
        return total

    # Budget levers, applied in order of increasing risk. Escalation flags are
    # sticky across rounds (persisted in state) so truncation depth never
    # flaps; mode escalation is monotonic by construction in the incremental
    # path because dropped/truncated content arrives already reduced.
    for item in interactions:
        if item["duplicate"] and item["droppable"]:
            item["mode"] = "drop"
    assist_cap = bool(escalation.get("assistCap"))
    trunc2 = bool(escalation.get("trunc2"))
    tail_cap = bool(escalation.get("tailCap"))
    if planned_chars(assist_cap, trunc2, tail_cap) > target_chars:
        # Sacrifice unprotected interactions first (oldest first), protected
        # (error/test output) only if the budget still demands it.
        for item in sorted(interactions, key=lambda it: (it["protected"], it["result_index"])):
            if planned_chars(assist_cap, trunc2, tail_cap) <= relief_chars:
                break
            if item["droppable"]:
                item["mode"] = "drop"
    if planned_chars(assist_cap, trunc2, tail_cap) > target_chars:
        trunc2 = True
    if planned_chars(assist_cap, trunc2, tail_cap) > target_chars:
        assist_cap = True
    if planned_chars(assist_cap, trunc2, tail_cap) > target_chars:
        tail_cap = True
    escalation["assistCap"] = assist_cap
    escalation["trunc2"] = trunc2
    escalation["tailCap"] = tail_cap

    # Build the output.
    dropped = {item["result_index"]: item for item in interactions if item["mode"] == "drop"}
    truncated = {item["result_index"] for item in interactions if item["mode"] == "trunc"}
    truncated_protected = {
        item["result_index"] for item in interactions if item["mode"] == "trunc-protected"
    }
    # Determine which call blocks to strip for each dropped interaction. No digest
    # is built or injected (the private history-digest marker is banned next round):
    # the frozen head (first user message) is left byte-identical. A dropped
    # interaction's toolResult is removed and its invoking toolCall block stripped,
    # so pairing is preserved and the dropped facts simply leave no marker trail.
    strip_by_call: dict[int, set[str]] = {}
    for item in interactions:
        if item["mode"] != "drop":
            continue
        call_index = item["call_index"]
        strip_by_call.setdefault(call_index, set()).update(item["ids"])
        info["droppedInteractionCount"] += 1
        if item["duplicate"]:
            info["duplicateResultCount"] += 1

    head, tail = (MID2_HEAD, MID2_TAIL) if trunc2 else (MID_HEAD, MID_TAIL)
    untouchable = set(result_indices[-TIGHT_UNTOUCHABLE:])
    tail_results = set(result_indices[-TIGHT_KEEP_RECENT:])
    output: list[Any] = []
    for index, message in enumerate(messages):
        role = normalize_role(message.get("role")) if isinstance(message, dict) else ""
        if role == "toolResult":
            if index in dropped:
                continue
            if index in truncated_protected:
                message, did = truncate_message(
                    message, int(GENTLE_PROTECTED_CAP * 0.75), int(GENTLE_PROTECTED_CAP * 0.25)
                )
                info["truncatedResultCount"] += int(did)
            elif index in truncated:
                message, did = truncate_message(message, head, tail)
                info["truncatedResultCount"] += int(did)
            elif index in tail_results and index not in untouchable and tail_cap:
                message, _ = truncate_message(message, int(TAIL_RESULT_CAP * 0.75), int(TAIL_RESULT_CAP * 0.25))
            elif index not in untouchable:
                message, _ = truncate_message(message, int(ABS_RESULT_CAP * 0.75), int(ABS_RESULT_CAP * 0.25))
            output.append(message)
            continue
        if role == "assistant":
            if index in strip_by_call:
                message = strip_tool_call_blocks(message, strip_by_call[index])
                if assistant_is_empty(message):
                    continue
            if (assist_cap and index < tail_start) or (tail_cap and index not in untouchable_msgs):
                message, did = truncate_message(message, ASSIST_HEAD, ASSIST_TAIL)
                info["truncatedAssistantCount"] += int(did)
            output.append(message)
            continue
        output.append(message)

    # NOTE: no digest is injected into the first user message — the frozen head
    # stays byte-identical (the private history-digest marker is banned next round).

    info["reason"] = "pruned" if (dropped or info["truncatedResultCount"] or info["truncatedAssistantCount"]) else "nothing_to_remove"
    info["targetChars"] = target_chars
    info["totalChars"] = total_chars
    info["escalation"] = {"assistCap": assist_cap, "trunc2": trunc2, "tailCap": tail_cap}
    info["plannedChars"] = planned_chars(assist_cap, trunc2, tail_cap)
    return output, info


# ---------------------------------------------------------------------------
# aow_bet: CACHE-BET harvest-only freeze-on-emit assembly (NEW).
#
# Engages ONLY when the everTouchedRich gate (handle_assemble) allows it AND our
# verified previous output is a byte-identical prefix of `working`. The HOLD boundary
# (hold_boundary) is computed on `working` (NOT on the re-pruned result): we HOLD
# working[:hold_boundary] VERBATIM and NEVER recompress it — that is the cache property.
# Only the live tail (working[hold_boundary:]) is compressed, with the UNMODIFIED
# compress_structurally. Because compress_structurally needs the leading head + first user
# message in its input or it no-ops, we PREPEND a byte-identical copy of the head (the
# messages of the held prefix up to and INCLUDING its first user message) to the live tail,
# compress [*head, *live_tail], then STRIP exactly the prepended head messages from the
# front of the output. The head therefore appears exactly ONCE — inside the held prefix —
# and result = [*working[:hold_boundary], *compressed_live]. On a re-seed (hold_boundary==0)
# the live tail already contains the head, so no prepend.
#
# CRUX (the cache win): m12 re-runs compress_structurally over the WHOLE working set every
# turn, so it re-drops / re-truncates even the already-stable FRONT — that is why m12's
# emitted prefix CHURNS turn-to-turn and misses the provider cache. aow HOLDS working's front
# verbatim and compresses only the newly-aged tail, so the emitted prefix is byte-IDENTICAL
# turn-to-turn (the connector feeds back our previous output, whose front IS this held region)
# and the provider caches it. (The prior aow_bet froze result_messages[:boundary] — the
# RE-PRUNED front — which reproduced m12's drops byte-for-byte; holding from `working` is the
# fix.) The hold boundary keeps the last WINDOW_MSGS messages of working live, freezes
# everything older: hold_boundary = max(frozenCount, len(working) - WINDOW_MSGS), snapped
# BACK to a tool-call boundary (find_call_index) so no call/result pair is split, and clamped
# monotonic (>= frozenCount, never regresses). The aow_lite caps (first_user_index and
# common-prefix-with-m12) are REMOVED. The held prefix extends past the first user message
# into the content m12 would prune: it is nominally LARGER than m12's ~8k prune but byte-
# STABLE turn-to-turn, so the provider caches it (the bet). It can NEVER inflate past the
# native trajectory: held_prefix ⊆ working and the live tail only shrinks, so result <=
# working <= native by construction.
#
# Two guards fall back to the byte-exact m12 output (`m12_native`) for the turn and
# re-seed an empty freeze: (a) prefix mismatch, (b) orphan introduction. A third guard
# (savings ceiling) replaces aow_lite's m12-nominal ratio watchdog: it guards ONLY against
# losing positive savings vs the TRUE NATIVE TRAJECTORY size (`native_tokens`, tracked
# monotonically in state) — result must stay <= SAVINGS_CEIL * native_tokens (>= 15% nominal
# savings vs native). It does NOT compare against m12, and it does NOT compare against the
# rewritten/already-compressed raw_messages (doing so was the first aow_bet attempt's bug:
# under the rewrite path raw_messages is tiny, so the ceiling fired every turn and the freeze
# re-seeded — degrading to m12). A stable frozen prefix that is nominally larger than m12 is
# ALLOWED (the cache bet); it only reverts if the result would inflate past 0.85*native.
# ---------------------------------------------------------------------------


def _snap_freeze_boundary(messages: list[Any], boundary: int) -> int:
    """Snap `boundary` (an exclusive cut index into `messages`) BACK so the freeze
    never splits a tool-call from its tool-result. If messages[boundary] is a
    toolResult whose invoking toolCall sits at/after the cut would be inside the
    frozen region while the result stays live (or vice versa), walk the boundary
    back to the invoking call so the call/result pair lands entirely on one side.
    Reuses m12's find_call_index logic. Returns a boundary in [0, len(messages)]."""
    boundary = max(0, min(boundary, len(messages)))
    if boundary <= 0 or boundary >= len(messages):
        return boundary
    call_ids_cache = [extract_tool_call_ids(m) for m in messages]
    # Walk back while the message JUST AFTER the cut (first live message) is a
    # toolResult whose invoking call would be frozen (index < boundary): move the
    # boundary to that call so the whole pair is live. Bounded by message count.
    guard = 0
    while 0 < boundary < len(messages) and guard <= len(messages):
        guard += 1
        first_live = messages[boundary]
        if not (isinstance(first_live, dict) and normalize_role(first_live.get("role")) == "toolResult"):
            break
        call_index = find_call_index(messages, boundary, call_ids_cache)
        if call_index is None or call_index >= boundary:
            break
        boundary = call_index
    return boundary


def _head_len_through_first_user(messages: list[Any]) -> int:
    """Length of the leading HEAD: the messages up to and INCLUDING the first user
    message. compress_structurally requires this head in its input (it locates the
    first user message and no-ops without one), so when we compress only the live
    region we PREPEND a byte-identical copy of this head and strip exactly these many
    messages back off the output. Returns 0 if there is no user message (no valid head
    to prepend -> caller falls back to m12)."""
    for i, m in enumerate(messages):
        if isinstance(m, dict) and normalize_role(m.get("role")) == "user":
            return i + 1
    return 0


def assemble_aow_harvest(
    working: list[Any],
    escalation: dict[str, Any],
    frozen_prefix: list[Any],
    frozen_count: int,
    raw_messages: list[Any],
    m12_native: list[Any],
    m12_info: dict[str, Any],
    native_tokens: int,
) -> tuple[list[Any], dict[str, Any], list[Any], bool]:
    """Return (result_messages, info, next_frozen_prefix, engaged).

    `m12_native`/`m12_info` are the byte-exact m12 harvest output for this turn,
    computed by the caller (with the REAL, sticky escalation). `raw_messages` is the
    ORIGINAL connector input this turn. `native_tokens` is the TRUE size of the
    uncompressed native trajectory (tracked monotonically in state by the caller) — it
    is the CORRECT savings-ceiling reference under the connector's session-rewrite path,
    where raw_messages is the small already-compressed feedback, NOT the native size. On
    any guard failure this function returns exactly (m12_native, m12_info, [], False) — a
    one-turn fallback that ships exactly what m12 would, and re-seeds an empty freeze."""
    aow_info: dict[str, Any] = {"aowEngaged": False}

    # GUARD (a): prefix check. The freeze may engage ONLY when our previous output is
    # a byte-identical prefix of `working`. Compare via fingerprint (byte-exact). Any
    # mismatch (rewrite path, reset, count drift) => fall back to m12 and re-seed.
    if frozen_count <= 0 or frozen_count > len(working):
        prefix_ok = (frozen_count == 0)
    else:
        prefix_ok = (
            len(frozen_prefix) == frozen_count
            and fingerprint_messages(working[:frozen_count])
            == fingerprint_messages(frozen_prefix)
        )
    if not prefix_ok:
        aow_info["aowFallback"] = "prefix_mismatch"
        return m12_native, {**m12_info, **aow_info}, [], False

    # ---- HOLD BOUNDARY: the crux of the cache bet ------------------------------------
    # We emit result = [*working[:hold_boundary] HELD VERBATIM, *compress(working[hold_
    # boundary:])]. The held region is taken from `working` (NOT from a re-pruned result):
    # m12 re-runs compress_structurally over the WHOLE working set every turn, so it re-
    # drops / re-truncates even the already-stable FRONT — that is why m12's emitted prefix
    # CHURNS turn-to-turn and misses the provider cache. aow instead HOLDS working's front
    # verbatim and only compresses the newly-aged tail, so the emitted prefix is byte-
    # IDENTICAL turn-to-turn (the connector feeds back our previous output, whose front IS
    # this held region) and the provider caches it.
    #
    # `working` under the rewrite path = [*OUR previous emitted output, *new native turns].
    # working[:frozen_count] was already verified byte-identical to frozen_prefix (GUARD a),
    # so holding working[:hold_boundary] with hold_boundary >= frozen_count EXTENDS the held
    # region monotonically over content that is aging out of the recent window — exactly the
    # content m12 would re-prune. The boundary keeps the last WINDOW_MSGS messages of working
    # live, freezes everything older, snaps BACK to a tool-call boundary so no call/result
    # pair is split, and is clamped monotonic (>= frozen_count) so the held prefix never
    # shrinks. (The OLD code froze result_messages[:boundary] — the re-pruned front — which
    # reproduced m12's drops byte-for-byte and was the residual reason aow == m12.)
    window_boundary = len(working) - WINDOW_MSGS
    raw_boundary = max(frozen_count, window_boundary)
    raw_boundary = max(0, min(raw_boundary, len(working)))
    hold_boundary = _snap_freeze_boundary(working, raw_boundary)
    hold_boundary = max(frozen_count, hold_boundary)
    hold_boundary = max(0, min(hold_boundary, len(working)))

    # Compress ONLY the live tail working[hold_boundary:] with the UNMODIFIED
    # compress_structurally, holding working[:hold_boundary] verbatim. compress_structurally
    # needs the leading head + first user message in its input or it no-ops
    # ("missing_first_user_message"), so when we hold a non-empty prefix (hold_boundary > 0)
    # we PREPEND a byte-identical copy of the head (working[:head_len] up to and INCLUDING
    # the first user message — the head lives inside the held prefix), compress
    # [*head, *live_tail], then STRIP exactly the prepended head messages off the front of
    # the output. The head therefore appears exactly ONCE — inside the held prefix. On a
    # re-seed (hold_boundary == 0) the live tail already contains the head, so no prepend is
    # needed and this is m12's normal whole-working compress.
    held_prefix = working[:hold_boundary]
    live_tail = working[hold_boundary:]
    if hold_boundary > 0:
        head_len = _head_len_through_first_user(held_prefix)
        if head_len <= 0:
            # No first-user head available to prepend -> cannot safely compress the live
            # tail with the unmodified engine. Fall back to m12 and re-seed.
            aow_info["aowFallback"] = "no_head"
            return m12_native, {**m12_info, **aow_info}, [], False
        head = held_prefix[:head_len]
        prepend_input = [*head, *live_tail]
        compressed_with_head, live_info = compress_structurally(
            prepend_input, escalation, target_tokens=TARGET_TOKENS
        )
        # STRIP exactly the prepended head: require the engine to have kept the head
        # byte-identical at the front of its output (it never prunes the leading head),
        # then drop those messages. If the front is NOT byte-identical to the head we
        # prepended (defensive — should never happen), fall back to m12 and re-seed
        # rather than risk a duplicated or mangled head.
        if (
            len(compressed_with_head) < head_len
            or fingerprint_messages(compressed_with_head[:head_len])
            != fingerprint_messages(head)
        ):
            aow_info["aowFallback"] = "head_strip_mismatch"
            return m12_native, {**m12_info, **aow_info}, [], False
        compressed_live = compressed_with_head[head_len:]
    else:
        compressed_live, live_info = compress_structurally(
            live_tail, escalation, target_tokens=TARGET_TOKENS
        )
    result_messages = [*held_prefix, *compressed_live]

    # CACHE-PROPERTY ASSERTIONS: the held region is reused VERBATIM from working (the head
    # appears exactly once, no duplication). result[:hold_boundary] == working[:hold_boundary]
    # byte-for-byte — this is the property that makes the prefix provider-cacheable. (It also
    # implies result[:frozen_count] == frozen_prefix, since hold_boundary >= frozen_count and
    # working[:frozen_count] == frozen_prefix was verified by GUARD a.)
    if hold_boundary > 0 and not (
        len(result_messages) >= hold_boundary
        and fingerprint_messages(result_messages[:hold_boundary])
        == fingerprint_messages(held_prefix)
    ):
        aow_info["aowFallback"] = "frozen_region_not_verbatim"
        return m12_native, {**m12_info, **aow_info}, [], False

    # GUARD (b): orphan check against `working` as the sanitized baseline (same test
    # m12's harvest runs). If we introduced orphans not already present in working,
    # fall back to m12 and re-seed.
    in_result_orphans, in_call_orphans = orphan_ids(working)
    out_result_orphans, out_call_orphans = orphan_ids(result_messages)
    if not (out_result_orphans <= in_result_orphans and out_call_orphans <= in_call_orphans):
        aow_info["aowFallback"] = "orphan_guard"
        return m12_native, {**m12_info, **aow_info}, [], False

    # GUARD (c): INFLATION CEILING vs the TRUE NATIVE TRAJECTORY (the core of the bet, and
    # the FIX for the failure where aow_bet degraded to m12). The progression of failed guards:
    #   - aow_lite reverted whenever the result was nominally larger than m12_native (the
    #     m12-nominal watchdog), forcing aow_bet's stable-but-larger frozen prefix to == m12
    #     every drop-turn. DELETED.
    #   - the first aow_bet attempt used a ceiling vs estimate_tokens(raw_messages) — but under
    #     the rewrite path raw_messages is our PREVIOUS COMPRESSED OUTPUT plus a few new turns
    #     (~7-8k), so the ceiling fired every turn and re-seeded the freeze (aow_lite's failure
    #     reproduced via the ceiling). FIXED by baselining against the true native size.
    #   - a SAVINGS ceiling (result <= 0.85*native, ">=15% savings") then STILL degraded to m12
    #     under the rewrite model: on the EARLY no-prune turns result==native==raw (nothing has
    #     been dropped yet), so demanding result be 15% SMALLER than native fired on exactly the
    #     turns where the freeze must FIRST engage to capture the front at full fidelity AHEAD
    #     of m12's drop frontier. The freeze then started only AFTER m12 dropped the front, so
    #     aow inherited m12's drops. FIXED here.
    # The guard's true job per the task is the single safety invariant "NEVER inflate past the
    # TRUE original native trajectory." So it is now an INFLATION ceiling: the result may be as
    # large as native (SAVINGS_CEIL is an inflation multiplier >= 1.0), and we revert ONLY on
    # genuine pathological inflation past native*SAVINGS_CEIL. A full-fidelity frozen prefix is
    # <= native by construction (it is a prefix of a prior emitted output that was itself <=
    # native), so it CLEARS every turn — including the early no-prune turns — letting the freeze
    # engage immediately and ACCUMULATE. native_tokens is the monotonic high-water mark of the
    # true native size (max of the additive new-native-turns total, estimate(raw_messages), and
    # `observed`/currentTokenCount), so the ceiling is anchored to the real context size, not to
    # the small rewritten feedback. We do NOT compare against m12. On a breach (genuine growth
    # past native) we ship m12_native and re-seed, so we never INFLATE past the native trajectory.
    aow_tokens = estimate_tokens(result_messages)
    m12_tokens = estimate_tokens(m12_native)
    raw_tokens = estimate_tokens(raw_messages)
    ceiling_ref = max(int(native_tokens), raw_tokens)
    if aow_tokens > ceiling_ref * SAVINGS_CEIL:
        aow_info["aowFallback"] = "savings_ceiling"
        aow_info["aowTokens"] = aow_tokens
        aow_info["m12Tokens"] = m12_tokens
        aow_info["rawTokens"] = raw_tokens
        aow_info["nativeTokens"] = int(native_tokens)
        return m12_native, {**m12_info, **aow_info}, [], False

    # Engaged. The freeze for NEXT turn is exactly the held prefix we emitted verbatim:
    # next_frozen_prefix = held_prefix = working[:hold_boundary] == result_messages[:hold_
    # boundary] (asserted above). It was computed from `working` (the held-verbatim front),
    # NOT from the re-pruned result, snapped to a tool-call boundary and clamped monotonic
    # (>= frozen_count) so the cached prefix only ever grows and never splits a call/result
    # pair. The connector feeds back our emitted output next turn, so working[:hold_boundary]
    # will again equal this prefix byte-for-byte (GUARD a re-verifies), letting the hold
    # extend further as more content ages out. This is what makes aow's emitted prefix byte-
    # stable while m12's churns — the cache bet.
    next_frozen_prefix = held_prefix

    aow_info.update(
        {
            "aowEngaged": True,
            "aowFrozenCountIn": frozen_count,
            "aowFrozenCountOut": hold_boundary,
            "aowLiveRegionLen": len(live_tail),
            "aowTokens": aow_tokens,
            "m12Tokens": m12_tokens,
            "rawTokens": raw_tokens,
            "nativeTokens": int(native_tokens),
        }
    )
    return result_messages, {**live_info, **aow_info}, next_frozen_prefix, True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def handle_assemble(payload: dict[str, Any]) -> dict[str, Any]:
    raw_messages = get_messages(payload)
    working, state_metadata, state_path, extras = resolve_stateful_messages(payload, raw_messages)

    params = get_params(payload)
    current_token_count = params.get("currentTokenCount")
    estimated = estimate_tokens(working)
    # Observed-size ratchet: the largest context this session has ever shown.
    # raw input grows monotonically (no session rewrite) so this captures true
    # task size even after compression shrinks the working set; modes only
    # ever escalate (passthrough -> gentle -> tight), never revert.
    observed = max(
        estimated,
        estimate_tokens(raw_messages),
        current_token_count if isinstance(current_token_count, int) else 0,
        int(extras.get("maxObservedTokens") or 0),
    )
    # ---- TRUE native-trajectory size (NEW — the savings-ceiling reference fix) ----
    # The connector's session-rewrite path feeds us our PREVIOUS COMPRESSED OUTPUT plus
    # newly appended native turns, so estimate_tokens(raw_messages) is the SMALL already-
    # compressed feedback — useless as a savings reference (it forced aow_lite's failure
    # to recur). We instead track the TRUE native size MONOTONICALLY: the NEW native turns
    # this turn are raw_messages[-newMessageCount:] (byte-exact native appends under either
    # the rewrite or the no-rewrite path; on a fresh/reset turn newMessageCount == the whole
    # input, which is native). Add their tokens to the persisted running total, and also
    # take the max with estimate_tokens(raw_messages) (covers the no-rewrite path, where
    # raw_messages already IS the full native trajectory) — both candidates are lower bounds
    # on the true native size, and the running ADD captures growth the rewrite path hides.
    # Clamped monotonic so the reference never shrinks (a shrinking ceiling could spuriously
    # revert a stable freeze). A LARGER native estimate only ever LOOSENS the inflation ceiling
    # (more willing to keep the freeze engaged); it never lets us inflate, because the ceiling
    # caps aow_tokens at the TRUE native trajectory size and the frozen prefix is a prefix of a
    # prior output that was itself <= native at the time.
    #
    # We seed the native size from EVERY lower bound on the true native trajectory available
    # this turn — the running additive total of new native turns, the rewritten raw input, AND
    # `observed` (which already maxes estimate(working), estimate(raw), currentTokenCount, and
    # the persisted maxObservedTokens high-water mark). Including `observed`/currentTokenCount
    # is the critical part of the fix: on the EARLY turns (before the connector starts rewriting
    # / before m12 starts pruning) the rewritten raw input still EQUALS the un-pruned result, so
    # a ceiling that demanded result be < native would fire on exactly the no-prune turns where
    # the freeze must FIRST engage to capture the front at full fidelity (ahead of m12's drop
    # frontier). currentTokenCount reports the agent's true native context size, which already
    # exceeds the (about-to-be-pruned) result, so it lets the freeze start on turn 1.
    new_msg_count = int(state_metadata.get("newMessageCount") or len(raw_messages))
    new_msg_count = max(0, min(new_msg_count, len(raw_messages)))
    new_native_turns = raw_messages[len(raw_messages) - new_msg_count:] if new_msg_count else []
    prev_native_tokens = int(extras.get("nativeTokens") or 0)
    native_tokens = max(
        prev_native_tokens + estimate_tokens(new_native_turns),
        estimate_tokens(raw_messages),
        prev_native_tokens,
        observed,
    )

    prev_mode = extras.get("mode") or "passthrough"
    # v11: three modes, switched on conversation DEPTH (per-call context is
    # uniformly small ≤90k, so token size can't separate easy from hard; depth
    # can). Monotonic + sticky: passthrough -> harvest -> rich, never reverts.
    #   passthrough: tiny context, send native (cache-warm).
    #   harvest    : shallow -> v6 drop+truncate (target 8k) -> pass-task bonus.
    #   rich       : deep    -> v9/v10 truncation-only rich skeleton -> hard flips.
    # Depth MUST be measured on raw_messages (the connector's full native
    # trajectory, monotonically growing) — NOT on `working`, which harvest itself
    # shrinks by dropping, which would pin the depth low and trap hard tasks in
    # harvest forever. Mode stickiness then keeps it rich once tripped.
    msg_depth = max(len(raw_messages), len(working))
    # Cumulative raw tokens processed this session (monotonic; secondary "large"
    # net for deep/wander tasks). estimate on raw input so harvest can't shrink it.
    cumulative_observed = int(extras.get("cumulativeObserved") or 0) + estimate_tokens(raw_messages)
    # Break guard: a task past a few rounds whose RECENT results are still
    # error-bearing is working hard and still failing (e.g. sympy's dimension
    # error) — it needs rich context, not the harvest. This is the only signal
    # that separates hard-but-shallow tasks from harvest-safe medium tasks.
    still_failing = (
        msg_depth >= ERROR_GUARD_MIN_MSGS
        and recent_errors(working) >= ERROR_GUARD_MIN_HITS
    )
    if (
        prev_mode == "rich"
        or msg_depth >= LARGE_THRESHOLD_MSGS
        or observed >= LARGE_THRESHOLD_TOKENS
        or cumulative_observed >= CUM_THRESHOLD
        or still_failing
    ):
        mode = "rich"
    elif prev_mode == "harvest" or observed >= PASS_THROUGH_TOKENS:
        mode = "harvest"
    else:
        mode = "passthrough"
    escalation = dict(extras.get("escalation") or {})

    # ---- AOW-lite freeze state + gate (NEW) ----------------------------------
    # everTouchedRich is sticky: once the session has EVER been in rich mode it stays
    # True forever and the freeze is HARD-DISABLED for the rest of the session. We set
    # it True the instant this turn is rich (or it was already True from state). The
    # freeze applies ONLY when mode == 'harvest' AND everTouchedRich is False AND the
    # previous mode was not 'rich'. In every other case the harvest branch runs m12's
    # exact original code path (no freeze) — see the harvest branch below.
    frozen_prefix = extras.get("frozenPrefix") or []
    if not isinstance(frozen_prefix, list):
        frozen_prefix = []
    frozen_count = int(extras.get("frozenCount") or 0)
    ever_touched_rich = bool(extras.get("everTouchedRich"))
    # Sticky update: any rich turn (now or historically) latches it on for good.
    ever_touched_rich = ever_touched_rich or (mode == "rich") or (prev_mode == "rich")
    freeze_allowed = (
        mode == "harvest"
        and not ever_touched_rich
        and prev_mode != "rich"
    )
    # Defaults carried into save_state; the engaged AOW path overwrites the prefix.
    next_frozen_prefix: list[Any] = []

    # A loop-guard message we appended on a prior turn may ride in via state; remove
    # it so compression never sees it, then re-decide and re-append (if an objective
    # loop is still present) at the end. The guard carries ONLY an allowed loop-reason
    # string — never steering — so stripping/re-adding it is purely idempotent.
    working = strip_loop_guard(working)

    sanitize_changed = False
    pruned = False
    if mode == "passthrough":
        # Below the budget: returning changed=False lets OpenClaw send its
        # native context untouched, preserving the provider's prompt cache
        # exactly like a no-plugin run.
        result_messages = raw_messages
        info: dict[str, Any] = {"reason": "below_activation_threshold"}
        changed = False
    elif mode == "harvest":
        # v6-style aggressive drop+truncate: compress the trajectory toward an 8k
        # target by truncating old tool output (wrapped in the allowed [[CMP]]…[[/CMP]]
        # markers) and dropping the oldest interactions, recovering the pass-task token
        # bonus on shallow tasks. The frozen head (first user message) stays
        # byte-identical — NO history-digest injection. Orphan-guarded; never ships
        # pairing we broke ourselves.
        sanitized = working
        # AOW-lite (NEW): when the gate allows, freeze the aged-out prefix and reuse
        # it verbatim. Otherwise run m12's EXACT harvest path below. We ALWAYS compute
        # m12_native first (with the REAL sticky escalation) so escalation is persisted
        # identically to m12, and so it is available as the byte-exact fallback for the
        # AOW guards (prefix/orphan/ratio). When freeze is disabled, m12_native IS the
        # result and the code path is byte-for-byte m12.
        m12_native, m12_info = compress_structurally(
            working, escalation, target_tokens=TARGET_TOKENS
        )
        if freeze_allowed:
            # Pass a COPY of escalation into the live-region compress so it doesn't
            # double-mutate the sticky escalation already advanced by m12_native.
            result_messages, info, aow_next_prefix, aow_engaged = assemble_aow_harvest(
                working,
                dict(escalation),
                frozen_prefix,
                frozen_count,
                raw_messages,
                m12_native,
                m12_info,
                native_tokens,
            )
            if aow_engaged:
                next_frozen_prefix = aow_next_prefix
            # If not engaged, assemble_aow_harvest already returned m12_native and an
            # empty prefix (re-seed): next_frozen_prefix stays [] from its default.
        else:
            # Freeze hard-disabled (rich-touched or gate closed): m12's exact output.
            result_messages, info = m12_native, m12_info
        pruned = info.get("reason") == "pruned"
        in_result_orphans, in_call_orphans = orphan_ids(sanitized)
        out_result_orphans, out_call_orphans = orphan_ids(result_messages)
        if not (out_result_orphans <= in_result_orphans and out_call_orphans <= in_call_orphans):
            result_messages = sanitized
            info = {"reason": "orphan_guard_fallback"}
            pruned = False
            next_frozen_prefix = []
        if not result_messages:
            result_messages = raw_messages
            info = {"reason": "empty_output_fallback"}
            pruned = False
            next_frozen_prefix = []
        # Compliant loop guard: appends ONLY an allowed loop-reason string, and only
        # when an objective repeated/no-progress loop is detected. No steering.
        result_messages = strip_loop_guard(result_messages)
        info["loopGuardFired"] = detect_loop_reason(result_messages) or None
        result_messages = append_loop_guard(result_messages)
        changed = fingerprint_messages(result_messages) != fingerprint_messages(raw_messages)
        # AOW-lite final invariant (defensive): the frozen prefix we persist MUST be a
        # byte-exact prefix of what we actually ship after the loop-guard strip/append.
        # If anything broke that (it shouldn't — guards live in the tail, prefix is the
        # older front), drop the freeze so next turn re-seeds from scratch. This makes
        # the worst case provably == m12.
        if next_frozen_prefix and not (
            len(result_messages) >= len(next_frozen_prefix)
            and fingerprint_messages(result_messages[: len(next_frozen_prefix)])
            == fingerprint_messages(next_frozen_prefix)
        ):
            next_frozen_prefix = []
    else:
        # Rich mode: byte-identical except dedup (allowed BLOCK back-reference) +
        # light stale-trim of old bulk.
        sanitized = working
        result_messages, info = compress_gently(working)
        pruned = info.get("reason") == "gentle"
        in_result_orphans, in_call_orphans = orphan_ids(sanitized)
        out_result_orphans, out_call_orphans = orphan_ids(result_messages)
        if not (out_result_orphans <= in_result_orphans and out_call_orphans <= in_call_orphans):
            # Never ship a trajectory with pairing we broke ourselves.
            result_messages = sanitized
            info = {"reason": "orphan_guard_fallback"}
            pruned = False
        if not result_messages:
            result_messages = raw_messages
            info = {"reason": "empty_output_fallback"}
            pruned = False
        # Compliant loop guard: appends ONLY an allowed loop-reason string, and only
        # when an objective repeated/no-progress loop is detected. No steering.
        result_messages = strip_loop_guard(result_messages)
        info["loopGuardFired"] = detect_loop_reason(result_messages) or None
        result_messages = append_loop_guard(result_messages)
        changed = fingerprint_messages(result_messages) != fingerprint_messages(raw_messages)

    metadata = {
        **state_metadata,
        **info,
        "changed": changed,
        "pruned": pruned,
        "sanitized": sanitize_changed,
        "mode": mode,
        "observedTokens": observed,
        "cumulativeObserved": cumulative_observed,
        "stillFailing": still_failing,
        "msgDepth": msg_depth,
        "originalMessageCount": len(raw_messages),
        "messageCount": len(result_messages),
        "estimatedInputTokens": estimated,
        "aowEverTouchedRich": ever_touched_rich,
        "aowFrozenCountOut": len(next_frozen_prefix),
        "nativeTokens": native_tokens,
    }
    try:
        save_state(
            state_path,
            payload,
            raw_messages,
            result_messages,
            mode=mode,
            max_observed=observed,
            cumulative_observed=cumulative_observed,
            escalation=escalation,
            frozen_prefix=next_frozen_prefix,
            ever_touched_rich=ever_touched_rich,
            native_tokens=native_tokens,
        )
        metadata["stateSaved"] = True
    except Exception as error:
        metadata["stateSaved"] = False
        metadata["stateError"] = str(error)

    return {
        "assembled": True,
        "messages": result_messages,
        "estimatedTokens": final_token_estimate(result_messages),
        "baseMiner": metadata,
    }


def run_event(event_name: str) -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            raise ValueError("Connector payload must be a JSON object")
        if event_name not in EVENT_NAMES:
            raise ValueError(f"Unknown miner event: {event_name}")
        response = {"ok": True, "result": handle_assemble(payload)}
    except Exception as error:
        response = {"ok": False, "error": str(error), "errorType": error.__class__.__name__}
    sys.stdout.write(json.dumps(response, ensure_ascii=False))
    return 0


def cli_main(argv: list[str]) -> int:
    return run_event(argv[0] if argv else "assemble")


if __name__ == "__main__":
    raise SystemExit(cli_main(sys.argv[1:]))
