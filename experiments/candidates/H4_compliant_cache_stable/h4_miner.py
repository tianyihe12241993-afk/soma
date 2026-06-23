#!/usr/bin/env python3
"""SOMA miner H4_compliant_cache_stable — NEXT-ROUND RULE-COMPLIANT derivative of H3.

WHAT H4 IS: H3's cache-stable compression engine, kept intact, with EVERY prompt-side
behavior-steering construct removed so the miner complies with miner/README_prompting.md.
The README permits exactly two prompt-edit categories next round:
  1) Compression markers — metadata wrappers that preserve instruction meaning, order,
     requirements, tool/safety/role policy and the output contract EXACTLY.
  2) Loop-detection guards — fire only on objective repeated/no-progress signals, fail
     fast with a clear loop reason, and never change strategy/reasoning/tool policy.

REMOVED vs H3 (all prompt-side, now illegal):
  - The entire injected coach message and the force-stop governor that told the agent
    to conclude. These steered the agent's workflow.
  - All behavior-steering directives that told the agent how/whether to proceed.
  - All custom/private bracketed markers H3 injected (its compressed-history digest,
    its note marker, and its prose elided markers). The dead digest/coach helpers
    and constants that produced them are removed too.

MARKERS USED (the ONLY allowed strings, from README sections 5.1/5.2):
  - The CMP start/end marker pair (aliased to the spelled-out start/end strings) wraps
    a masked / truncated region — see CMP_START / CMP_END / CMP_START_LONG below.
  - The BLOCK open/close marker pair labels the surviving latest copy of a duplicated /
    superseded view; the earlier copy becomes the allowed back-reference string built by
    same_response_ref().
  - Loop detection emits ONLY the two allowed loop-reason strings — see
    LOOP_REASON_ASSISTANT / LOOP_REASON_TOOLCALL below — nothing else.

KEPT vs H3 (the compression ENGINE, unchanged in spirit): cache-stable harvest (frozen
head / stable prefix), tool-result body masking, superseded file-view elision, sticky
keep-list, fragile guard, rich fallback, load-bearing allowlist, active-file
preservation, failing-test/assertion/traceback-tail preservation, tool-call/tool-result
pairing integrity, passthrough mode, orphan guard. The masking PRESERVES load-bearing
content (failing-test names, assertion lines, traceback tail, file paths, line numbers,
current patch/diff, active file) exactly as H3 did — the allowed markers merely WRAP it.

WHY (engine rationale, unchanged from H3): H1M's HARVEST path realizes only ~+8%
compression in a real eval because it REBUILDS the digest and RE-TRUNCATES the entire
history EVERY turn, and it INJECTS a GROWING digest into the FIRST user message. The
provider caches the prompt PREFIX (observed as large cache_read counts). Any byte change
to an early message invalidates the cache from that point on → every turn is a cache
MISS → it costs MORE tokens.

CACHE-STABLE HARVEST design (`compress_cache_stable`):
- FROZEN HEAD: the system message(s) + the FIRST user message (the task statement) are
  emitted BYTE-IDENTICAL. No digest is injected or grown in the first message.
- RECENT-INTACT TAIL: the last RICH_INTACT_MSGS messages are byte-intact.
- OLD MESSAGES (between head and tail): each is compressed as a PURE FUNCTION OF ITS OWN
  CONTENT — not of global state, not of position-from-end. So the same old message always
  compresses to the same bytes; as the trajectory grows by appending, already-compressed
  old messages stay byte-identical, and the cached prefix only changes at the ONE message
  that just crossed the tail boundary. That is the cache win.
- MASK TOOL-RESULT BODIES IN PLACE: never drop a tool message, never break
  tool_call/tool_result pairing. A stale tool-result body is wrapped in [[CMP]]…[[/CMP]]
  and PRESERVES command, exit/status, failing-test names, assertion lines, the traceback
  tail, file paths and line numbers (extracted with the existing helpers).
- SUPERSEDED FILE-VIEW ELISION: if the same path is read/shown again later, the LATEST
  view is labelled [[BLOCK N]]…[[/BLOCK N]] and an earlier full view of it is replaced by
  "Same response as in [[BLOCK N]]." (message envelope + tool_call_id kept).
- STICKY KEEP-LIST: load-bearing items (active file paths, failing-test names, assertion
  lines, traceback tails, current patch/diff) are ALWAYS preserved, regardless of depth.
- MINIMIZE PRUNE EVENTS: only drop oldest messages if, after masking/elision, the result
  still exceeds a HARD cap; prefer masking over dropping. Between prunes the head + old
  region stays byte-stable.

FRAGILE-GUARD HARDENING (general transcript signals only, NO task-id logic): borderline
error-dense / repeated-failure / large-still-failing transcripts fall back to the RICH
path EARLIER than h1m@deep (lower recent error-hit threshold, plus oscillating-failure
and large-still-failing detectors).

Profiles (env H3_PROFILE, default cache_safe) — control how aggressively masked bodies /
elided views are truncated; deeper = shorter kept head/tail. Kept-bytes monotonic:
ultra ⊆ king ⊆ safe.

Protocol (same as the reference): `python h4_miner.py assemble` with the connector
payload on stdin, a single JSON object on stdout. Stdlib only; tiktoken is used for the
reported token estimate when available. run_event / cli_main / plugin entry contract are
identical to H3/H1M so the existing driver can run this as `base_miner.py`.
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
STATE_VERSION = 4
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
# deciding rounds (flip). Coach stays loop+stop only (compliant). Ship rule:
# ship v11 only if Easy tokens improve without breaking v10's reliability, else v10.
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
# Char caps (head+tail truncation) applied progressively under budget pressure.
ABS_RESULT_CAP = 40_000
TAIL_RESULT_CAP = 16_000
MID_HEAD, MID_TAIL = 1_000, 400
MID2_HEAD, MID2_TAIL = 500, 200
ASSIST_HEAD, ASSIST_TAIL = 1_200, 300

# ===========================================================================
# H4 ALLOWED COMPRESSION MARKERS — the ONLY bracketed strings this miner emits.
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
    Empty/fully-elided regions become "[[CMP]][[/CMP]]". The kept head/tail/pinned
    load-bearing lines go BETWEEN the markers — the marker is metadata only."""
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
# H3 CACHE-STABLE HARVEST CONSTANTS.
# A masked old tool-result body keeps a HEAD + TAIL of its own text (so command
# echoes, leading diagnostics and the traceback tail survive) and replaces the
# stale middle with a deterministic, content-derived marker. These caps are a
# PURE FUNCTION OF THE PROFILE — never of position-from-end — so the same old
# message masks to the same bytes on every turn (the cache invariant).
HARD_CAP_TOKENS = 60_000       # only PRUNE (drop oldest) if masking still exceeds this
MASK_BODY_MAX = 1_400          # bodies shorter than this are never masked (cheap; keep intact)
SUPERSEDED_VIEW_MIN_CHARS = 400  # only elide superseded file views at least this large

# ---------------------------------------------------------------------------
# H3 PROFILE LAYER — selects masking/elision DEPTH for the cache-stable harvest.
# Kept-bytes are MONOTONIC: ultra ⊆ king ⊆ safe. Each field is a budget on the
# HEAD/TAIL of a masked tool-result body or a per-message stale cap; deeper
# profiles keep less. RICH path / GENTLE_PROTECTED_CAP / ERROR_MARKERS untouched.
# Select with env H3_PROFILE (default cache_safe). The real driver bakes the
# value into the file, so reading os.environ at import is sufficient.
import os as _os
_H3_PROFILES = {
    # (MASK_HEAD, MASK_TAIL, PROTECTED_MASK_HEAD, PROTECTED_MASK_TAIL,
    #  STALE_CAP, ASSIST_HEAD, ASSIST_TAIL, ERROR_GUARD_MIN_HITS)
    # MASK_*            : head/tail bytes kept around a masked stale (non-load-bearing) body
    # PROTECTED_MASK_*  : head/tail bytes kept when masking a LOAD-BEARING body (error/test/diff)
    #                     — never below what the sticky keep-list needs; bigger than MASK_*
    # STALE_CAP         : per-message extractive cap for stale bodies before masking kicks in
    # ASSIST_*          : head/tail bytes for old assistant prose
    # ERROR_GUARD_MIN_HITS: recent error-bearing results that route to RICH (lower = earlier bail)
    "cache_safe":  (520, 220, 1_400, 1_200, 9_000, 700, 220, 3),  # ~h1m@deep depth, cache-stable
    "cache_king":  (360, 150,   900,   800, 6_500, 520, 170, 2),  # king-like deeper
    "cache_ultra": (240, 100,   600,   520, 4_500, 360, 120, 2),  # over-push (locate break boundary)
}
H3_PROFILE = _os.environ.get("H3_PROFILE", "cache_safe").strip().lower()
if H3_PROFILE not in _H3_PROFILES:
    H3_PROFILE = "cache_safe"
(MASK_HEAD, MASK_TAIL, PROTECTED_MASK_HEAD, PROTECTED_MASK_TAIL,
 STALE_CAP, ASSIST_HEAD, ASSIST_TAIL, ERROR_GUARD_MIN_HITS) = _H3_PROFILES[H3_PROFILE]
# H4 routes only the cache-stable HARVEST path and the RICH (compress_gently) path;
# H3's drop-with-digest structural path and its digest machinery are removed (they
# injected a private compressed-history marker into the first user message, disallowed
# next round). The cache-stable harvest never injects a digest.


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
) -> None:
    _, session_id, session_key = resolve_session_identity(payload)
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
    extras = {
        "mode": (state.get("mode") if state else None) or "passthrough",
        "maxObservedTokens": int(state.get("maxObservedTokens") or 0) if state else 0,
        "cumulativeObserved": int(state.get("cumulativeObserved") or 0) if state else 0,
        "escalation": dict(state.get("escalation") or {}) if state else {},
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
# H3 FRAGILE-GUARD HARDENING — general transcript signals only, NO task-id logic.
# H1M rejected a fragile task (django-14493) the baseline kept; the fix is to make
# borderline error-dense / repeated-failure / large-still-failing transcripts fall
# back to the RICH (m7-like) path EARLIER. These are the extra signals layered on
# top of H1M's recent-error-window count.
# ---------------------------------------------------------------------------

# Tunables for the hardened guard (general signals; no instance ids anywhere).
OSCILLATION_WINDOW = 14        # recent tool results scanned for recurring failure signatures
OSCILLATION_MIN_REPEAT = 2     # a failing test/assertion recurring this many times = oscillating
LARGE_FAILING_MSGS = 60        # a transcript at least this deep that is STILL error-bearing -> rich
ERROR_DENSITY_WINDOW = 8       # recent tool results scanned for error density
ERROR_DENSITY_MIN_HITS = 4     # this many error-bearing in the recent (wider) window -> rich
_FAIL_SIG_PATTERN = re.compile(
    r"(?:FAILED|FAIL|ERROR)[: ]\s*(\S+)"          # FAILED path::test
    r"|(\S+\.py::\S+)"                              # pytest node id
    r"|(AssertionError[^\n]{0,120})",              # assertion text
    re.M,
)


def _failure_signatures(text: str) -> list[str]:
    """Stable signatures of what is failing: failing-test node ids and assertion
    lines. Used to detect the SAME failure recurring across rounds (oscillation)."""
    sigs: list[str] = []
    for m in _FAIL_SIG_PATTERN.finditer(text[:40_000]):
        sig = collapse_ws(next((g for g in m.groups() if g), "")).lower()
        if sig and len(sig) >= 4:
            sigs.append(clip(sig, 100))
    return sigs


def oscillating_failures(messages: list[Any], window: int = OSCILLATION_WINDOW) -> bool:
    """True if the SAME failing test / assertion recurs across multiple recent rounds.
    A bug that keeps producing the identical failure is not being resolved and needs
    rich context to flip — exactly the H1M break case. Generic; no task ids."""
    rounds: list[set[str]] = []
    seen = 0
    for message in reversed(messages):
        if not isinstance(message, dict) or normalize_role(message.get("role")) != "toolResult":
            continue
        if is_error_bearing(message):
            sigs = set(_failure_signatures(extract_text(message.get("content"))))
            if sigs:
                rounds.append(sigs)
        seen += 1
        if seen >= window:
            break
    counts: dict[str, int] = {}
    for sigs in rounds:
        for s in sigs:  # count distinct ROUNDS a signature appears in
            counts[s] = counts.get(s, 0) + 1
    return any(n >= OSCILLATION_MIN_REPEAT for n in counts.values())


def fragile_transcript(messages: list[Any], msg_depth: int) -> bool:
    """Hardened route-to-rich trigger (general signals). Fires EARLIER than
    h1m@deep's single recent-window count by also catching:
      - wider-window error density (still grinding errors recently),
      - oscillating failures (same failing test/assertion recurring),
      - large transcripts that are still error-bearing at the tail.
    NO instance-id logic."""
    if recent_errors(messages, ERROR_DENSITY_WINDOW) >= ERROR_DENSITY_MIN_HITS:
        return True
    if oscillating_failures(messages):
        return True
    if msg_depth >= LARGE_FAILING_MSGS and recent_errors(messages, 2) >= 1:
        return True
    return False


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
    unchanged. This is the entire prompt-side surface of H4 — no other text."""
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
    # v10 RICH+RELIABLE+HARVEST compression. NEVER drops a message and never
    # touches the recent working window or any load-bearing result. vs v9: the
    # stale-bulk cap is tighter (2k) and near-duplicate old results collapse to a
    # marker in addition to exact duplicates — both restricted to old,
    # non-load-bearing content, so reliability and hard flips are unaffected.
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


# ===========================================================================
# H3 CACHE-STABLE HARVEST — the central re-architecture vs H1M.
#
# The invariant: an OLD message (between the frozen head and the recent-intact
# tail) is compressed as a PURE FUNCTION OF ITS OWN CONTENT plus a small set of
# trajectory-wide, append-monotonic facts (the set of later-read file paths, and
# the global sticky keep-list). None of these depend on position-from-end or on a
# per-turn rebuilt digest, so as the trajectory grows by appending, an already-old
# message masks to the SAME bytes every turn → the cached prefix is stable up to
# the single message that just crossed the tail boundary.
# ===========================================================================

# Body lines that must NEVER be elided from a tool result, regardless of profile.
# (Command echoes, exit/status, failing tests, assertions, traceback frames,
# file:line refs, diff/patch lines.) These are extracted and pinned into the mask.
_CMD_ECHO_PATTERN = re.compile(
    r"^\s*(?:\$|#|>|PS[ >]|running:|cmd:|command:|exit(?:\s*code)?[:=]|status[:=]|"
    r"return\s*code[:=]).*$",
    re.M | re.I,
)
_TRACE_FRAME_PATTERN = re.compile(r'^\s*File "[^"]+", line \d+', re.M)
_LINE_REF_PATTERN = re.compile(r"\b[\w./-]+\.[A-Za-z]{1,4}:\d+\b")


def _pinned_lines(text: str) -> list[str]:
    """The load-bearing lines of a tool-result body, in original order: command
    echoes / exit codes, failing-test ids, assertion lines, traceback frames,
    file:line refs, diff lines, and error-marker lines. Pure function of text."""
    out: list[str] = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        low = s.lower()
        if (
            _CMD_ECHO_PATTERN.match(line)
            or TEST_LINE_PATTERN.search(line)
            or _TRACE_FRAME_PATTERN.match(line)
            or _DIFF_PATTERN.match(line)
            or _LINE_REF_PATTERN.search(line)
            or any(marker in low for marker in ERROR_MARKERS)
        ):
            out.append(s)
    # de-dup while preserving order (keep the mask deterministic + compact)
    seen: set[str] = set()
    uniq: list[str] = []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def mask_tool_body(text: str, head: int, tail: int, *, protected: bool) -> str:
    """Replace a stale tool-result BODY with a deterministic, content-derived form
    that PRESERVES the load-bearing lines (command, exit/status, failing tests,
    assertions, traceback tail, paths, line numbers). The elided middle is wrapped
    in the allowed [[CMP]]…[[/CMP]] markers; the kept HEAD and TAIL sit OUTSIDE the
    markers, and the load-bearing lines extracted from the elided middle are
    surfaced INSIDE them so no load-bearing content is lost. PURE function of
    (text, head, tail, protected) — no global state, no position info — so the
    same body always masks to the same bytes (the cache invariant)."""
    pinned = _pinned_lines(text)
    # Always keep a HEAD of the raw body (command echo + first diagnostics) and a
    # TAIL (the traceback tail / final assertion). Profile sets head/tail depth.
    head_text = text[:head].rstrip()
    tail_text = text[-tail:].lstrip() if tail else ""
    keep_pins = pinned if protected else pinned[: max(8, len(pinned) // 2 + 1)]
    # Surface only pins not already visible in head/tail (compact + stable bytes).
    extra = [p for p in keep_pins if p not in head_text and p not in tail_text]
    inner = "\n".join(extra)  # load-bearing lines recovered from the elided middle
    parts: list[str] = []
    if head_text:
        parts.append(head_text)
    parts.append(cmp_block(inner))  # empty inner -> "[[CMP]][[/CMP]]"
    if tail_text:
        parts.append(tail_text)
    return "\n".join(p for p in parts if p)


def _set_body_text(message: Any, new_text: str) -> Any:
    """Return a copy of `message` with its first string text field replaced by
    `new_text`. Preserves block structure / tool_call_id / role."""
    out = copy.deepcopy(message)
    content = out.get("content")
    if isinstance(content, str):
        out["content"] = new_text
        return out
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                for field in ("text", "content"):
                    if isinstance(block.get(field), str):
                        block[field] = new_text
                        return out
    return out


# File-view detection: a tool result that is predominantly a file's contents
# (associated with a path the agent read). We key superseding on the path.
def _result_file_path(message: Any, call_message: Any, call_id: str | None) -> str | None:
    """Best-effort path this tool result is a view OF: prefer the invoking
    tool-call's path arg, else a path on the first body line. Pure per-interaction."""
    if isinstance(call_message, dict) and call_id:
        for block in iter_tool_call_blocks(call_message):
            if block.get("id") != call_id:
                continue
            for field in ("arguments", "args", "input", "parameters"):
                if field in block:
                    args_text = extract_text(block[field])
                    m = re.search(r'["\']?(?:path|file|filename|filepath)["\']?\s*[:=]\s*["\']?([\w./-]+\.[A-Za-z]{1,5})', args_text)
                    if m:
                        return m.group(1)
                    found = PATH_PATTERN.findall(args_text)
                    if found:
                        return found[0].split(":")[0]
    return None


def superseded_view_ref(block_n: int) -> str:
    """An earlier file view superseded by a later read of the same path collapses to
    the allowed back-reference to the surviving (latest) view labelled [[BLOCK N]]."""
    return same_response_ref(block_n)


def _has_critical_content(message: Any) -> bool:
    """Genuine ground-truth content the agent patches against: error/test output or
    diff/patch lines. Unlike `_is_load_bearing`, this does NOT treat a mere
    active-path mention as protected — used for superseded views, whose path content
    is preserved by the LATEST (kept) view, so an earlier copy that only *mentions*
    the path is safe to elide. Error/diff/test content is still always protected."""
    if is_error_bearing(message):
        return True
    text = extract_text(message.get("content"))
    for line in text.split("\n"):
        if _DIFF_PATTERN.match(line) or TEST_LINE_PATTERN.search(line):
            return True
    return False


def compress_cache_stable(
    messages: list[Any], hard_cap_tokens: int = HARD_CAP_TOKENS
) -> tuple[list[Any], dict[str, Any]]:
    """Cache-stable HARVEST. Frozen head + recent-intact tail; old messages masked
    as a pure function of their own content; tool bodies masked in place (never
    dropped, pairing preserved); superseded file views elided; sticky keep-list
    always preserved; prune (drop) only as a last resort past a hard cap."""
    info: dict[str, Any] = {
        "maskedToolResults": 0,
        "elidedFileViews": 0,
        "pruneEvents": 0,
        "reason": "nothing_to_remove",
    }
    n = len(messages)
    if n == 0:
        return messages, {**info, "reason": "empty"}

    call_ids_cache = [extract_tool_call_ids(m) for m in messages]

    # ---- Frozen head: leading system message(s) + the FIRST user message. ----
    first_user_index = next(
        (i for i, m in enumerate(messages)
         if isinstance(m, dict) and normalize_role(m.get("role")) == "user"),
        None,
    )
    head_end = 0  # exclusive; messages[:head_end] are byte-frozen
    i = 0
    while i < n and isinstance(messages[i], dict) and normalize_role(messages[i].get("role")) == "system":
        i += 1
        head_end = i
    if first_user_index is not None:
        head_end = max(head_end, first_user_index + 1)

    # ---- Recent-intact tail: the last RICH_INTACT_MSGS messages. ----
    tail_start = max(head_end, n - RICH_INTACT_MSGS)

    # ---- Sticky keep-list (load-bearing, trajectory-wide). ----
    active = frozenset(active_paths(messages))

    # ---- Superseded file views: a path read/shown again LATER supersedes its
    #      earlier views. Computed once from the full trajectory (append-monotonic:
    #      a path's "later read" set only grows, and the LATEST view is the tail-most
    #      occurrence — so an old view's superseded status only ever flips ONCE). ----
    #   For each interaction, find the path it views; the LAST interaction for a
    #   path is authoritative (kept high-fidelity); earlier ones are superseded.
    result_path_at: dict[int, str] = {}
    last_view_index_for: dict[str, int] = {}
    for idx in range(n):
        msg = messages[idx]
        if not isinstance(msg, dict) or normalize_role(msg.get("role")) != "toolResult":
            continue
        rids = extract_tool_result_ids(msg)
        call_index = find_call_index(messages, idx, call_ids_cache)
        call_msg = messages[call_index] if call_index is not None else None
        call_id = next(iter(rids), None)
        path = _result_file_path(msg, call_msg, call_id)
        if path:
            result_path_at[idx] = path
            last_view_index_for[path] = idx

    # ---- Superseded-view block numbering. An OLD view (head_end <= idx < tail_start)
    #      whose path is read again LATER, that is large enough and carries no genuine
    #      ground-truth content, is "superseded" and will become the allowed back-ref
    #      "Same response as in [[BLOCK N]]." to the surviving LATEST view of that path.
    #      We map each superseded index -> survivor index, then assign deterministic
    #      [[BLOCK N]] numbers (by survivor document order) to referenced survivors and
    #      wrap them wherever they sit. Append-monotonic: a survivor's index for a path
    #      is the tail-most occurrence, so the numbering is stable turn over turn.
    superseded_ref: dict[int, int] = {}  # superseded old-view idx -> survivor idx
    for idx in range(head_end, tail_start):
        msg = messages[idx]
        if not isinstance(msg, dict) or normalize_role(msg.get("role")) != "toolResult":
            continue
        path = result_path_at.get(idx)
        body = extract_text(msg.get("content"))
        if (
            path
            and last_view_index_for.get(path, idx) > idx
            and len(body) >= SUPERSEDED_VIEW_MIN_CHARS
            and not _has_critical_content(msg)
        ):
            superseded_ref[idx] = last_view_index_for[path]
    sv_referenced = sorted(set(superseded_ref.values()))
    sv_block_number: dict[int, int] = {idx: n2 for n2, idx in enumerate(sv_referenced, 1)}

    output: list[Any] = []
    for idx, message in enumerate(messages):
        # Survivor of a superseded view: label it [[BLOCK N]]…[[/BLOCK N]] wherever it
        # sits (head, old region, or recent-intact tail) so the back-reference
        # resolves to an explicit, unambiguous block. The body between markers is
        # byte-identical to the original view.
        if idx in sv_block_number:
            output.append(_wrap_first_text_field(
                message, block_open(sv_block_number[idx]), block_close(sv_block_number[idx])
            ))
            continue
        if idx < head_end or idx >= tail_start:
            output.append(message)  # frozen head / recent-intact tail: byte-identical
            continue
        role = normalize_role(message.get("role")) if isinstance(message, dict) else ""
        if role != "toolResult":
            # Old assistant prose / interstitial user notes: assistant text trimmed
            # as a pure function of its own content (head/tail). Tool-call blocks
            # are NEVER stripped here (pairing preservation).
            if role == "assistant":
                new_msg, did = truncate_message(message, ASSIST_HEAD, ASSIST_TAIL)
                output.append(new_msg)
            else:
                output.append(message)
            continue

        body = extract_text(message.get("content"))

        # 1) Superseded file-view elision: an earlier full view of a path read again
        #    later → the allowed "Same response as in [[BLOCK N]]." back-reference to
        #    the surviving LATEST view (labelled [[BLOCK N]] above). The message
        #    envelope + tool_call_id are kept; only the body text changes.
        if idx in superseded_ref:
            ref = superseded_view_ref(sv_block_number[superseded_ref[idx]])
            output.append(_set_body_text(message, ref))
            info["elidedFileViews"] += 1
            continue

        # 2) Mask the stale body in place (message + tool_call_id kept). Small
        #    bodies are left intact (cheap, and avoids churn). Load-bearing bodies
        #    are masked with the deeper protected head/tail so all pinned lines
        #    survive; everything pinned is re-surfaced regardless.
        if len(body) <= MASK_BODY_MAX:
            output.append(message)
            continue
        protected = _is_load_bearing(message, active)
        if protected:
            new_body = mask_tool_body(body, PROTECTED_MASK_HEAD, PROTECTED_MASK_TAIL, protected=True)
        else:
            new_body = mask_tool_body(body, MASK_HEAD, MASK_TAIL, protected=False)
        if new_body != body:
            output.append(_set_body_text(message, new_body))
            info["maskedToolResults"] += 1
        else:
            output.append(message)

    # ---- Prune (drop oldest) ONLY if still over the hard cap after masking. ----
    #   Prefer masking over dropping; this keeps prune events at 0 under the cap and
    #   keeps the head+old region byte-stable between prunes. We drop oldest WHOLE
    #   interactions (toolCall block + its toolResult) so pairing is never broken.
    hard_cap_chars = hard_cap_tokens * CHARS_PER_TOKEN
    if sum(message_cost(m) for m in output) > hard_cap_chars:
        output, dropped = _prune_oldest_interactions(output, head_end, hard_cap_chars)
        info["pruneEvents"] = dropped

    if info["maskedToolResults"] or info["elidedFileViews"] or info["pruneEvents"]:
        info["reason"] = "cache_stable"
    info["headEnd"] = head_end
    info["tailStart"] = tail_start
    return output, info


def _prune_oldest_interactions(
    messages: list[Any], head_end: int, hard_cap_chars: int
) -> tuple[list[Any], int]:
    """Drop oldest whole (toolCall + toolResult) interactions past the frozen head
    until under the hard cap. Removes the toolResult AND strips the matching
    toolCall block from its assistant message, so no orphan is ever created."""
    call_ids_cache = [extract_tool_call_ids(m) for m in messages]
    result_indices = [
        i for i, m in enumerate(messages)
        if i >= head_end and isinstance(m, dict) and normalize_role(m.get("role")) == "toolResult"
    ]
    drop_result: set[int] = set()
    strip_by_call: dict[int, set[str]] = {}
    total = sum(message_cost(m) for m in messages)
    dropped = 0
    for ridx in result_indices:  # oldest first
        if total <= hard_cap_chars:
            break
        rids = extract_tool_result_ids(messages[ridx])
        cidx = find_call_index(messages, ridx, call_ids_cache)
        if not rids or cidx is None or cidx < head_end:
            continue  # un-droppable without breaking pairing/head → skip
        drop_result.add(ridx)
        strip_by_call.setdefault(cidx, set()).update(rids)
        total -= message_cost(messages[ridx])
        dropped += 1
    if not dropped:
        return messages, 0
    out: list[Any] = []
    for idx, message in enumerate(messages):
        if idx in drop_result:
            continue
        if idx in strip_by_call:
            message = strip_tool_call_blocks(message, strip_by_call[idx])
            if assistant_is_empty(message):
                continue
        out.append(message)
    return out, dropped


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


# ---------------------------------------------------------------------------
# Cache metrics: hash the emitted prefix up to the recent-tail boundary so we can
# verify offline that the cached prefix stays byte-stable turn over turn.
# ---------------------------------------------------------------------------

def prefix_boundary(messages: list[Any]) -> int:
    """Index where the recent-intact tail begins (the prefix is messages[:this]).
    Mirrors compress_cache_stable's tail_start."""
    n = len(messages)
    head_end = 0
    i = 0
    while i < n and isinstance(messages[i], dict) and normalize_role(messages[i].get("role")) == "system":
        i += 1
        head_end = i
    first_user_index = next(
        (j for j, m in enumerate(messages)
         if isinstance(m, dict) and normalize_role(m.get("role")) == "user"),
        None,
    )
    if first_user_index is not None:
        head_end = max(head_end, first_user_index + 1)
    return max(head_end, n - RICH_INTACT_MSGS)


def prefix_bytes(messages: list[Any]) -> bytes:
    """Canonical bytes of the cache-stable prefix (head + masked old region),
    excluding the recent-intact tail. The provider caches this region; we hash it
    to detect cache invalidation."""
    boundary = prefix_boundary(messages)
    return canonical_json(messages[:boundary]).encode("utf-8")


def prefix_hash(messages: list[Any]) -> str:
    return hashlib.sha256(prefix_bytes(messages)).hexdigest()


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
    prev_mode = extras.get("mode") or "passthrough"
    # v11: three modes, switched on conversation DEPTH (per-call context is
    # uniformly small ≤90k, so token size can't separate easy from hard; depth
    # can). Monotonic + sticky: passthrough -> harvest -> rich, never reverts.
    #   passthrough: tiny context, send native (cache-warm).
    #   harvest    : shallow -> v6 drop-with-digest (target 8k) -> pass-task bonus.
    #   rich       : deep    -> v9/v10 truncation-only rich skeleton -> hard flips.
    # Depth MUST be measured on raw_messages (the connector's full native
    # trajectory, monotonically growing) — NOT on `working`, which harvest itself
    # shrinks by dropping, which would pin the depth low and trap hard tasks in
    # harvest forever. Mode stickiness then keeps it rich once tripped.
    msg_depth = max(len(raw_messages), len(working))
    # Cumulative raw tokens processed this session (monotonic; secondary "large"
    # net for deep/wander tasks). estimate on raw input so harvest can't shrink it.
    cumulative_observed = int(extras.get("cumulativeObserved") or 0) + estimate_tokens(raw_messages)
    # Break guard (H1M): a task past a few rounds whose RECENT results are still
    # error-bearing is working hard and still failing — it needs rich context, not
    # the harvest. H3 HARDENS this with general signals (no task-id logic): wider-
    # window error density, oscillating failures (same failing test/assertion
    # recurring), and large transcripts still error-bearing at the tail. Borderline
    # fragile transcripts thus fall back to RICH (m7-like) EARLIER than h1m@deep.
    still_failing = (
        msg_depth >= ERROR_GUARD_MIN_MSGS
        and recent_errors(working) >= ERROR_GUARD_MIN_HITS
    )
    fragile = msg_depth >= ERROR_GUARD_MIN_MSGS and fragile_transcript(working, msg_depth)
    if (
        prev_mode == "rich"
        or msg_depth >= LARGE_THRESHOLD_MSGS
        or observed >= LARGE_THRESHOLD_TOKENS
        or cumulative_observed >= CUM_THRESHOLD
        or still_failing
        or fragile
    ):
        mode = "rich"
    elif prev_mode == "harvest" or observed >= PASS_THROUGH_TOKENS:
        mode = "harvest"
    else:
        mode = "passthrough"
    escalation = dict(extras.get("escalation") or {})

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
        # CACHE-STABLE harvest: frozen head (system + first user, byte-identical,
        # NO injected digest) + recent-intact tail; old messages masked as a PURE
        # FUNCTION OF THEIR OWN CONTENT (tool bodies masked in place with the allowed
        # CMP markers, never dropped; superseded file views become the allowed BLOCK
        # back-reference; sticky keep-list always preserved). Prunes only past a hard
        # cap. → the cached prefix stays byte-stable turn over turn. Orphan-guarded;
        # never ships pairing we broke ourselves.
        sanitized = working
        prefix_before = prefix_hash(working)
        result_messages, info = compress_cache_stable(working)
        pruned = info.get("pruneEvents", 0) > 0
        in_result_orphans, in_call_orphans = orphan_ids(sanitized)
        out_result_orphans, out_call_orphans = orphan_ids(result_messages)
        if not (out_result_orphans <= in_result_orphans and out_call_orphans <= in_call_orphans):
            result_messages = sanitized
            info = {"reason": "orphan_guard_fallback"}
            pruned = False
        if not result_messages:
            result_messages = raw_messages
            info = {"reason": "empty_output_fallback"}
            pruned = False
        # Cache metrics (offline inspection): prefix hash before/after, stable bytes.
        info["prefixHashBefore"] = prefix_before
        info["prefixHashAfter"] = prefix_hash(result_messages)
        info["stablePrefixBytes"] = len(prefix_bytes(result_messages))
        info.setdefault("pruneEvents", 0)
        info.setdefault("maskedToolResults", 0)
        info.setdefault("elidedFileViews", 0)
        # Compliant loop guard: appends ONLY an allowed loop-reason string, and only
        # when an objective repeated/no-progress loop is detected. No steering.
        result_messages = strip_loop_guard(result_messages)
        info["loopGuardFired"] = detect_loop_reason(result_messages) or None
        result_messages = append_loop_guard(result_messages)
        changed = fingerprint_messages(result_messages) != fingerprint_messages(raw_messages)
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
