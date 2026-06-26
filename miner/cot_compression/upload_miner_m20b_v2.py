#!/usr/bin/env python3
"""SOMA miner m20b-v2 — m20-BLIND + CONSERVATIVE superseded gating (recency + frequency).

m20b-v2 vs m20-BLIND: the superseded-view collapse now (1) only fires on files read
>= SUPERSEDE_MIN_VIEWS (3) times [FREQUENCY GATE], and (2) keeps the SUPERSEDE_KEEP_RECENT
(2) NEWEST views of each path full, collapsing only OLDER ones [RECENCY GUARD]. This
addresses the m20b A/B regressions (django-13158 2/3->1/3 + wander): m20b collapsed some
still-needed recent views; v2 retains the agent's current working views and only drops
genuinely-stale, clearly-repeatedly-read ones. error/test/diff content still never collapsed.

--- m20-BLIND docstring below ---
SOMA miner m20-BLIND — m20 with superseded views BLIND-truncated (real ratio gain).

m20-BLIND vs m20: the superseded file-view collapse uses BLIND head/tail truncation
(SUPERSEDED_HEAD/TAIL, drops the middle code) instead of extractive (which pins code
signatures -> zero shrink). This actually reduces tokens on superseded views -> raises
the per-task ratio bonus on passing tasks. RISK (A/B-tested, not offline-provable): an
old superseded non-critical view's dropped middle might be content the agent still
needs -> the proven wander/break family, scoped to the narrowest case (old, superseded,
same-file, non-anchor views; latest view + error/test/diff always kept). GATED EXPERIMENT.

--- m20 docstring below ---
SOMA miner m20 — m12 (m7_compliant) + SUPERSEDED-FILE-VIEW dedup (ratio-bonus lever).

m20 SINGLE-VARIABLE CHANGE vs m12: in the RICH path (compress_gently), a tool result
that is a file-VIEW of a path which is read AGAIN in a LATER result is SUPERSEDED ->
collapsed hard (RICH_SUPERSEDED_CAP=600) instead of the generous RICH_STALE_CAP. The
LATEST view of each path is kept full, and any error/test/diff content is NEVER
collapsed (_has_critical_content). This is pure-REDUNDANCY removal (delta-debugging /
trace-simplification spirit, anchor-preserving) — it removes no information the agent
still needs, so it does NOT perturb the agent (unlike depth/m17/m18 which compressed
NEEDED content -> wander -> breaks).

WHY: per-task score = base + 0.5*clamp(ln(ratio),-2,2) for pass-pass(+1)/flip(+4).
m12 sits at ratio ~1.75x => bonus only +0.28 (max is +1.0 at ~7.4x). The agent re-reads
the same file many times (observed up to 14x), leaving redundant superseded copies in
context. Collapsing them raises the ratio bonus on tasks we ALREADY PASS — concentrated
in large/deep (Hard/Medium) tasks where re-reads pile up. Since Overall = mean(E,M,H),
lifting our strongest categories' pass scores raises the mean toward #1 WITHOUT needing
Easy or fixing the (unfixable, sampling-driven) breaks.

Harvest path, passthrough, dedup, loop guard, markers = byte-for-byte m12. Compliant:
deterministic; no LLM/API; no task-id/category logic; only allowed CMP/BLOCK markers +
loop-reason strings. GATED EXPERIMENT — NOT submitted; m12 stays LIVE.

--- m12 base docstring below ---
SOMA miner m7_compliant — NEXT-ROUND RULE-COMPLIANT derivative of m7 (v11).

WHAT THIS IS: m7's proven compression ENGINE kept intact, with every prompt-side
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
# deciding rounds (flip). The only prompt-side surface is the compliant loop guard
# (an allowed loop-reason string, appended only on an objective loop) — there is no
# coach / governor / history-digest injection in this compliant derivative.
RICH_INTACT_MSGS = 10          # last N messages kept byte-intact (never compressed)
RICH_STALE_CAP = 6_000         # v11 rich/deep path: richer stale cap for flips (v9 value; v10 used 2k)
RICH_SUPERSEDED_CAP = 600      # m20: a file-view re-read LATER is SUPERSEDED -> collapse hard (latest view kept full). Frees budget -> higher ratio bonus on pass tasks; only applied to NON-critical (no error/test/diff) views.
SUPERSEDED_HEAD, SUPERSEDED_TAIL = 400, 200   # m20-BLIND: superseded views are BLIND head/tail truncated (drops middle code) so they actually shrink (extractive pins code sigs -> no shrink). Keeps file header (head) + end (tail).
SUPERSEDE_MIN_VIEWS = 3       # m20b-v2 frequency gate: only collapse old views of a file read >=3 times
SUPERSEDE_KEEP_RECENT = 2     # m20b-v2 recency guard: keep the 2 NEWEST views of each path full; collapse only older
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


def _result_dominant_path(message: Any) -> str | None:
    """m20: the file path this tool result is predominantly a VIEW of (the most
    frequent path token), or None. Used to detect superseded file re-reads. Pure
    per-message; no global state."""
    text = extract_text(message.get("content"))
    found = PATH_PATTERN.findall(text)
    if not found:
        return None
    norm = [p.split(":")[0] for p in found]
    counts: dict[str, int] = {}
    for p in norm:
        counts[p] = counts.get(p, 0) + 1
    top = max(counts, key=counts.get)
    return top if counts[top] >= 1 else None


def _has_critical_content(message: Any) -> bool:
    """m20: genuine ground-truth the agent patches against — error/test output or
    diff/patch lines. A superseded earlier view is collapsed ONLY if it carries
    NONE of this (the latest view preserves the file's current content; but an
    earlier view that shows an error/test/diff the later one doesn't must be kept)."""
    if is_error_bearing(message):
        return True
    text = extract_text(message.get("content"))
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

    # m20b-v2: CONSERVATIVE superseded-file-view detection. Same idea (an old view of a
    # re-read file is redundant -> collapse to free budget for a higher per-task ratio
    # bonus on PASSING tasks), but with two guards added after the m20b A/B showed it
    # collapsed some still-needed views (regressions/wander):
    #   FREQUENCY GATE  — only act on files read >= SUPERSEDE_MIN_VIEWS times (clearly
    #                     repeatedly-read; a file read only twice may still need both).
    #   RECENCY GUARD   — keep the SUPERSEDE_KEEP_RECENT NEWEST views of each path FULL;
    #                     collapse only older ones (the agent always retains its current
    #                     working views). error/test/diff content is never collapsed.
    views_by_path: dict[str, list[int]] = {}
    path_of: dict[int, str] = {}
    for idx in result_indices:
        p = _result_dominant_path(messages[idx])
        if p:
            path_of[idx] = p
            views_by_path.setdefault(p, []).append(idx)  # ascending order
    superseded: set[int] = set()
    for p, idxs in views_by_path.items():
        if len(idxs) < SUPERSEDE_MIN_VIEWS:              # frequency gate
            continue
        for idx in idxs[:-SUPERSEDE_KEEP_RECENT]:        # all but the newest KEEP_RECENT
            if (
                idx not in intact
                and not _has_critical_content(messages[idx])  # never collapse error/test/diff
                and idx not in dup_ref and idx not in near_dup_ref
            ):
                superseded.add(idx)

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
            elif index in superseded:
                # m20-BLIND: superseded file-view -> BLIND head/tail truncate (drops the
                # middle code) so it ACTUALLY shrinks. extractive pins code signatures ->
                # no shrink; the latest view of this path (kept full elsewhere) is current,
                # and error/test/diff views are excluded from `superseded`, so dropping the
                # middle of an OLD superseded non-critical view is the (A/B-tested) bet.
                # truncate_message wraps the elided middle in the allowed [[CMP]] marker.
                message, did = truncate_message(message, SUPERSEDED_HEAD, SUPERSEDED_TAIL)
                info["truncatedResultCount"] += int(did)
                info["supersededViewCount"] = info.get("supersededViewCount", 0) + 1
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
        result_messages, info = compress_structurally(
            working, escalation, target_tokens=TARGET_TOKENS
        )
        pruned = info.get("reason") == "pruned"
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
