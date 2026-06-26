#!/usr/bin/env python3
"""SOMA miner m22 — m12 (m7_compliant) HARVEST made EXTRACTIVE-not-blind at a
CONSTANT per-turn byte budget.

WHAT THIS IS vs m12: m12's engine is kept BYTE-IDENTICAL on the RICH
(compress_gently), PASSTHROUGH, ROUTER (handle_assemble mode-decision + every
routing constant), and ORPHAN-GUARD paths. The ONLY changes are scoped to the
HARVEST path (compress_structurally), reached only when the router selects
mode=="harvest". m22 does NOT keep MORE bytes than m12 — that is the exact mistake
m21 made (kept more -> bigger harvest output -> rich-entry trajectory inflated ->
Hard cratered 0.919 -> 0.461). m22 keeps the SAME (or fewer) bytes per harvest turn
and spends them on HIGHER-QUALITY content.

WHY (verified from comp-108 per-run break profiles): m12's Easy deficit (0.412)
comes from BLIND truncation/whole-interaction DROPS killing task-CRITICAL spans on
baseline-passing tasks (sympy-11618 / sympy-14531 / sympy-20590 broke at NORMAL
steps 30/38/46 and HEALTHY tokens 528-791k — budgets at which the kings all pass).
m12 blind-dropped the span the agent needed. Fixing those content-quality breaks
lifts Easy 0.398->0.763 (king-level), flips Pair(E,H) to us, and keeps Single-H.

THE TWO HARVEST CONTENT-LOSS MECHANISMS IN m12 AND THE m22 FIX (both at constant
budget — see CHANGE 1..3 inline):
  m12 mechanism A — blind head/tail TRUNCATE of a KEPT result (truncate_message
    keeps value[:head] + value[-tail:], eliding the middle). A buried changed-hunk
    / traceback / signature in the middle is lost.
  m12 mechanism B — whole-interaction DROP (the toolResult is removed entirely,
    contributing 0 chars, and its invoking toolCall block is stripped). The
    critical span of a would-be-dropped interaction is lost completely.

  CHANGE 1 (KEPT results): replace blind truncate with EXTRACTIVE-then-cap (m17's
    _select_then_cap): extractive_message pins error/traceback/test/diff-hunk/path/
    signature lines and elides unchanged interior, THEN a hard head/tail cap. The
    cap guarantees the per-result byte budget is <= m12's truncate budget in every
    case (extraction shrinks line-structured results so the cap is a no-op and the
    clues survive; un-shrinkable blobs fall through to the exact m12 truncate).
  CHANGE 2 (DROPPED interactions): instead of removing the result to 0 chars, keep
    a TINY critical extractive span (changed-hunk + error/traceback + signature
    only, capped at DROP_SPAN_CAP ~ a few hundred chars). The invoking toolCall is
    NO LONGER stripped (the result still exists, just tiny), so pairing is preserved
    natively. This retains the would-be-dropped interaction's load-bearing span
    WITHOUT growing the trajectory, because of:
  CHANGE 3 (BUDGET RECONCILIATION — the HARD-SAFETY invariant): the dropped-span
    bytes are FUNDED by extractive-trimming the KEPT results harder, so the NET
    per-harvest-turn output bytes are <= m12's would-be harvest output bytes. This
    is enforced as a hard final check: compute m12's legacy harvest build for the
    turn; if m22's output exceeds it in raw chars, progressively shrink the kept
    results (and, last resort, fall back to the m12-exact build for that turn). The
    output can therefore NEVER be larger than m12's — so the rich-entry trajectory
    is <= m12's and Hard 0.919 is preserved by construction (the guarantee m21
    violated). The FREE safety clamps (a Hard token ceiling killing m12's 7.36M
    runaway tail, and a min-step/collapse guard) only ever REDUCE; they cannot
    trigger keep-more.

DISTINCT FROM:
  - m17: applied extraction only at the TRUNCATION sites (CHANGE 1), never touched
    the DROP path, so it left mechanism B's whole-span losses unfixed.
  - m21: kept MORE (target 11k, relief 1.0, keep_recent 6) -> bigger output -> rich
    coupling -> Hard crater. m22 keeps the SAME m12 budget (target 8k, relief 0.75,
    keep_recent 4) and enforces output <= m12.

INHERITED FROM m12 (rule-compliance posture, unchanged): every prompt-side
behavior-steering construct removed so the miner complies with
miner/README_prompting.md. The README permits exactly two prompt-edit categories
next round:
  1) Compression markers — metadata wrappers that preserve instruction meaning,
     order, requirements, tool/safety/role policy and the output contract EXACTLY.
  2) Loop-detection guards — fire only on objective repeated/no-progress signals,
     fail fast with a clear loop reason, and never change strategy/reasoning/tool
     policy.
Compliant: no LLM/API call, no task-id/category logic, no behavior steering, no
force-stop; only the allowed CMP / BLOCK markers + the two allowed loop-reason
strings; fully deterministic (selection uses active=frozenset(), a pure function of
message text — cache-stable, no sliding-window prefix churn).

MARKERS USED (the ONLY bracketed strings, from README sections 5.1/5.2):
  - The CMP start/end marker pair wraps a truncated tool-result region (kept
    head/tail sit OUTSIDE the markers; the elided middle is the wrapped region).
  - The BLOCK open/close marker pair labels the surviving latest copy of a
    duplicated / near-duplicate tool result; the earlier copy becomes the allowed
    back-reference string built by same_response_ref().
  - Loop detection emits ONLY the two allowed loop-reason strings.

Protocol (same as the reference): `python upload_miner_m22.py assemble` with the
connector payload on stdin, a single JSON object on stdout. Stdlib only; tiktoken is
used for the reported token estimate when available. run_event / cli_main / the
plugin entry contract are identical to m12 so the existing driver can run this
unchanged.
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
# m22: bump from m12's 4 -> 6 (m21 used 5). The harvest path produces different
# output bytes than m12, so a state file written by one must not be read by the
# other (load_state rejects a mismatched version). Router/passthrough/rich logic is
# unchanged.
STATE_VERSION = 6
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
#
# m22: these are kept BYTE-IDENTICAL to m12 (NOT m21's lighter values). m22 keeps
# the SAME byte budget; it changes only the QUALITY of what survives.
PASS_THROUGH_TOKENS = 3_000    # below this there is nothing worth compressing
TIGHT_TOKENS = 25_000          # enter drop-with-digest mode earlier on big tasks
TARGET_TOKENS = 8_000          # tight-mode trajectory target (m12 value; NOT m21's 11k)
PRESSURE_RELIEF = 0.75         # m12 value; NOT m21's 1.0

# v11 DEPTH-ADAPTIVE (aggressive-shallow / rich-deep). Routing constants below are
# BYTE-IDENTICAL to m12 — m22 does not touch the router.
RICH_INTACT_MSGS = 10          # last N messages kept byte-intact (never compressed)
RICH_STALE_CAP = 6_000         # v11 rich/deep path: richer stale cap for flips
RICH_PROTECTED_CAP = 30_000    # "full" for practical purposes (guards pathological logs)
NEARDUP_MIN_CHARS = 400        # min normalized length to qualify as a near-duplicate
LARGE_THRESHOLD_MSGS = 90      # message-count depth at which a task is "large/hard" -> rich
LARGE_THRESHOLD_TOKENS = 120_000  # token safety net: any single context this big -> rich
CUM_THRESHOLD = 600_000        # cumulative raw tokens processed -> treat as large -> rich
ERROR_GUARD_MIN_MSGS = 40      # don't apply the error guard until the task has some depth
ERROR_GUARD_WINDOW = 4         # how many recent tool results to scan for unresolved errors
ERROR_GUARD_MIN_HITS = 4       # this many error-bearing results in the recent window -> rich
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
# m12 values (NOT m21's widened keep_recent).
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
# m22 HARVEST-ONLY constants (read ONLY inside the harvest build; the router,
# rich path, and passthrough never see these).
# ===========================================================================
# CHANGE 2: the tiny critical span kept for an interaction m12 would DROP. A few
# hundred chars: just the changed diff-hunk + error/traceback + signature lines of
# the dropped result. Big enough to carry the load-bearing clue, small enough that
# CHANGE 3's reconciliation can always fund it by trimming kept results.
DROP_SPAN_CAP = 600            # max chars of the kept-span for a would-be-dropped result
# CHANGE 1: the floor budget the kept truncated results may be squeezed to when
# CHANGE 3 needs to reclaim bytes to fund the drop-spans. Never below this so a kept
# result still carries its own head/tail. (m12's MID2 trunc keeps ~700 chars; this
# is the same order, so the worst-case kept-result quality == m12's deepest trunc.)
RECLAIM_MIN_HEAD, RECLAIM_MIN_TAIL = 300, 150
# Free Hard-ceiling clamp: kill m12's pathological 7.36M-token runaway tail. This
# only ever REDUCES (it caps a single monstrous result); it can never keep more.
HARD_CEILING_CHARS = 2_000_000  # any single tool result above this is hard-capped

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
# Keep the most INFORMATIVE lines: always pin errors / failing tests / file paths /
# code signatures / active-file lines / edit (diff) lines; then fill the remaining
# budget with the highest TF-IDF-scoring leftover lines. Original line order
# preserved. Same token budget as v6 truncation, far higher information retention.
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
# m22 CHANGE 2 helper: the TINY critical span kept for a would-be-DROPPED result.
#
# m12 drops the result to 0 chars and strips its toolCall. m22 instead replaces the
# result body with ONLY its critical extractive span — the changed diff-hunk lines,
# error/traceback lines, failing-test lines, and code signatures — capped hard at
# DROP_SPAN_CAP chars (a few hundred). Everything else is elided into the allowed
# [[CMP]]…[[/CMP]] marker. The toolCall is NOT stripped (the result still exists,
# just tiny), so pairing is preserved natively without any orphan surgery.
#
# This is a strict subset of extractive_compress's pin rules: we keep ONLY pinned
# (load-bearing) lines, in document order, and never the TF-IDF fill. Pure function
# of the result text (active=frozenset()), deterministic, compliant.
# ---------------------------------------------------------------------------

def _critical_span(text: str, cap: int = DROP_SPAN_CAP) -> str:
    """Return the load-bearing span of `text` (changed-hunk + error/traceback + sig
    + path lines), capped at `cap` chars, wrapped so the elision is the allowed CMP
    marker. Returns "" only if there is genuinely no load-bearing line."""
    if not isinstance(text, str) or not text.strip():
        return ""
    lines = text.split("\n")
    pinned = [ln for ln in lines if _line_is_pinned(ln, frozenset())]
    if not pinned:
        return ""
    # Accumulate pinned lines up to the cap (document order preserved via the list
    # comprehension above, which iterated lines in order).
    span: list[str] = []
    used = 0
    for ln in pinned:
        add = len(ln) + 1
        if used + add > cap and span:
            break
        # A single pinned line longer than the cap is itself hard-clipped so the
        # span never exceeds the cap.
        if add > cap:
            ln = clip(ln, max(1, cap - 1))
            add = len(ln) + 1
        span.append(ln)
        used += add
        if used >= cap:
            break
    if not span:
        return ""
    # Wrap the kept span so the dropped interior is the allowed CMP marker. The kept
    # lines sit OUTSIDE the markers (head); the elided remainder is the wrapped region.
    return f"{cmp_block()}\n" + "\n".join(span)


def _critical_span_message(message: Any, cap: int = DROP_SPAN_CAP) -> tuple[Any, bool, int]:
    """Replace a tool-result's body with only its critical span (<= cap chars).
    Returns (new_message, changed, new_char_cost).

    If the result has NO load-bearing span (pure boilerplate: a plain read, a dir
    listing, find/grep chatter), `changed` is False — the caller then drops it to 0
    chars exactly like m12 (no waste on an empty marker). m22 only spends bytes on a
    would-be-dropped interaction when that interaction actually carries a load-bearing
    clue (changed-hunk / traceback / failing-test / signature / path)."""
    if not isinstance(message, dict):
        return message, False, message_cost(message)
    content = message.get("content")
    full = extract_text(content)
    span = _critical_span(full, cap)
    if not span:
        # No load-bearing line → signal "no span" so the caller drops it (m12-exact).
        return message, False, 0
    if isinstance(content, str):
        out = copy.deepcopy(message)
        out["content"] = span
        return out, True, len(span)
    if isinstance(content, list):
        out = copy.deepcopy(message)
        placed = False
        for block in out.get("content", []):
            if isinstance(block, dict):
                for field in ("text", "content"):
                    if isinstance(block.get(field), str):
                        block[field] = span
                        placed = True
                        break
            if placed:
                break
        if not placed:
            # No text field to place the span into — leave as-is (rare); treat as drop.
            return message, False, 0
        return out, True, message_cost(out)
    return message, False, message_cost(message)


# ---------------------------------------------------------------------------
# COMPLIANT LOOP DETECTION (README §2 + §5.2). Identical to m12.
# ---------------------------------------------------------------------------

def _is_loop_guard_message(message: Any) -> bool:
    if not isinstance(message, dict) or normalize_role(message.get("role")) != "user":
        return False
    text = extract_text(message.get("content")).strip()
    return text in (LOOP_REASON_ASSISTANT, LOOP_REASON_TOOLCALL)


def strip_loop_guard(messages: list[Any]) -> list[Any]:
    return [m for m in messages if not _is_loop_guard_message(m)]


def detect_loop_reason(messages: list[Any]) -> str:
    """Return the matching allowed loop-reason string if an OBJECTIVE loop is
    present in the recent window, else "". (Identical to m12.)"""
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
    reason = detect_loop_reason(messages)
    if not reason:
        return messages
    return [*messages, {"role": "user", "content": [{"type": "text", "text": reason}]}]


# ---------------------------------------------------------------------------
# Gentle mode: truncation-only compression for mid-size contexts. BYTE-IDENTICAL
# to m12 — the RICH path is untouched (Hard routes here; preserving it is the
# entire HARD-SAFETY guarantee).
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
    low = re.sub(r"\d+", "", text.lower())
    low = re.sub(r"[^a-z]+", " ", low)
    return " ".join(low.split())


def compress_gently(messages: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    # RICH+RELIABLE compression — BYTE-IDENTICAL to m12. NEVER drops a message and
    # never touches the recent working window or any load-bearing result.
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
    intact = set(range(max(0, len(messages) - RICH_INTACT_MSGS), len(messages)))
    active = frozenset(active_paths(messages))

    survivor_for_hash: dict[str, int] = {}
    survivor_for_norm: dict[str, int] = {}
    dup_ref: dict[int, int] = {}
    near_dup_ref: dict[int, int] = {}
    for index in reversed(result_indices):
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
                message, did = extractive_message(message, RICH_PROTECTED_CAP, active)
                info["protectedResultCount"] += 1
                info["truncatedResultCount"] += int(did)
            else:
                message, did = extractive_message(message, RICH_STALE_CAP, active)
                info["truncatedResultCount"] += int(did)
        elif role == "toolResult" and index in block_number:
            message = _wrap_first_text_field(message, block_open(block_number[index]), block_close(block_number[index]))
        output.append(message)

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
# Structural (HARVEST) compression
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


def _harvest_build(
    messages: list[Any],
    escalation: dict[str, Any],
    target_tokens: int,
    *,
    use_extractive: bool,
    use_drop_span: bool,
    reclaim_head: int = MID_HEAD,
    reclaim_tail: int = MID_TAIL,
    span_cap: int = DROP_SPAN_CAP,
) -> tuple[list[Any], dict[str, Any]]:
    """The m12 harvest engine, parameterized so m22 can run it two ways:

      - LEGACY (m12-exact) build: use_extractive=False, use_drop_span=False. The
        body below is then byte-identical to m12.compress_structurally (blind
        truncate_message on kept results; dropped results removed to 0 chars + their
        toolCall stripped). This is the reconciliation baseline and the last-resort
        fallback, so the worst case is EXACTLY m12.

      - m22 build: use_extractive=True (CHANGE 1 — extractive-then-cap on kept
        results), use_drop_span=True (CHANGE 2 — would-be-dropped results keep a
        tiny critical span instead of vanishing, toolCall NOT stripped). reclaim_head/
        reclaim_tail let CHANGE 3 squeeze kept truncated results harder to fund the
        drop-spans (defaults == m12's MID caps, so by default the kept-result budget
        equals m12's).

    `escalation` is mutated in place (the caller passes a copy for any build it does
    not commit). The DROP/TRUNC classification, the escalation lever order, the
    pairing logic, and planned_chars are all m12-identical; only the per-result
    reduction differs."""
    info: dict[str, Any] = {
        "droppedInteractionCount": 0,
        "truncatedResultCount": 0,
        "truncatedAssistantCount": 0,
        "duplicateResultCount": 0,
        "dropSpanCount": 0,
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
    relief_chars = int(target_chars * PRESSURE_RELIEF)

    recent_results = result_indices[-TIGHT_KEEP_RECENT:]
    tail_start = len(messages)
    for result_index in recent_results:
        call_index = find_call_index(messages, result_index, call_ids_cache)
        tail_start = min(tail_start, result_index, call_index if call_index is not None else result_index)
    if not result_indices:
        tail_start = max(first_user_index + 1, len(messages) - 8)

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
                "protected": is_error_bearing(messages[result_index]),
                "droppable": bool(result_ids) and call_index is not None,
                "mode": "trunc",
            }
        )
    interactions.reverse()  # oldest first
    for item in interactions:
        if item["protected"]:
            item["mode"] = "trunc-protected"

    untouchable_msgs = set(range(max(0, len(messages) - TIGHT_UNTOUCHABLE), len(messages)))

    # planned_chars models the LEGACY (m12) reduction budget exactly: a dropped
    # interaction contributes 0 chars. m22's drop-spans add bytes ON TOP of this
    # plan, which is precisely what CHANGE 3's reconciliation removes again — so the
    # escalation decision (how many to drop) stays m12-identical, and m22 is layered
    # on the SAME drop set.
    def planned_chars(assist_cap: bool, trunc2: bool, tail_cap: bool) -> int:
        total = 0
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
                        pass  # 0 chars (m12 model)
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
        return total

    for item in interactions:
        if item["duplicate"] and item["droppable"]:
            item["mode"] = "drop"
    assist_cap = bool(escalation.get("assistCap"))
    trunc2 = bool(escalation.get("trunc2"))
    tail_cap = bool(escalation.get("tailCap"))
    if planned_chars(assist_cap, trunc2, tail_cap) > target_chars:
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

    dropped = {item["result_index"]: item for item in interactions if item["mode"] == "drop"}
    truncated = {item["result_index"] for item in interactions if item["mode"] == "trunc"}
    truncated_protected = {
        item["result_index"] for item in interactions if item["mode"] == "trunc-protected"
    }

    # Decide, PER dropped interaction, whether m22 keeps a tiny critical span or drops
    # it to 0 (m12-exact). This is computed in a PRE-PASS (before the output loop) so
    # strip_by_call is complete before any assistant call block is emitted — a span'd
    # result keeps its toolCall, a fully-dropped result strips it. Pairing therefore
    # stays valid by construction (no after-the-fact orphan surgery).
    #
    # In the LEGACY build (use_drop_span=False) every dropped interaction strips its
    # toolCall and yields 0 chars — byte-identical to m12.
    span_for: dict[int, Any] = {}        # result_index -> the span'd message (m22 only)
    strip_by_call: dict[int, set[str]] = {}
    for item in interactions:
        if item["mode"] != "drop":
            continue
        ridx = item["result_index"]
        info["droppedInteractionCount"] += 1
        if item["duplicate"]:
            info["duplicateResultCount"] += 1
        if use_drop_span:
            # CHANGE 2: keep ONLY the tiny critical span if the would-be-dropped
            # result carries a load-bearing clue; otherwise drop it to 0 (m12-exact).
            new_msg, did, _cost = _critical_span_message(messages[ridx], span_cap)
            if did:
                span_for[ridx] = new_msg
                info["dropSpanCount"] += 1
                continue  # keep its toolCall (do NOT strip)
        # No span (or legacy build): drop the result + strip its invoking call block.
        if item["call_index"] is not None:
            strip_by_call.setdefault(item["call_index"], set()).update(item["ids"])

    head, tail = (MID2_HEAD, MID2_TAIL) if trunc2 else (MID_HEAD, MID_TAIL)
    # CHANGE 3 reclaim: when reclaiming, the caller passes a smaller head/tail so the
    # kept truncated results shrink below m12's, funding the drop-spans. Never below
    # the RECLAIM_MIN floor (so a kept result still carries head/tail). The reclaim
    # caps only ever REDUCE vs m12's (head, tail), never grow them.
    use_head = min(head, reclaim_head)
    use_tail = min(tail, reclaim_tail)
    untouchable = set(result_indices[-TIGHT_UNTOUCHABLE:])
    tail_results = set(result_indices[-TIGHT_KEEP_RECENT:])

    harvest_active = frozenset()  # pure function of message text → cache-stable

    def _reduce(msg: Any, ex_budget: int, cap_head: int, cap_tail: int) -> tuple[Any, bool]:
        # CHANGE 1: extractive SELECTION then a hard head/tail CAP. The cap guarantees
        # the byte budget is <= the equivalent m12 blind truncate in every case
        # (extraction shrinks line-structured results so the cap is a no-op and the
        # buried clue survives; un-shrinkable blobs fall through to the same truncate
        # m12 used). In the legacy build, use_extractive=False → plain m12 truncate.
        if use_extractive:
            msg2, did_e = extractive_message(msg, ex_budget, harvest_active)
            msg2, did_t = truncate_message(msg2, cap_head, cap_tail)
            return msg2, (did_e or did_t)
        return truncate_message(msg, cap_head, cap_tail)

    output: list[Any] = []
    for index, message in enumerate(messages):
        role = normalize_role(message.get("role")) if isinstance(message, dict) else ""
        if role == "toolResult":
            if index in dropped:
                if index in span_for:
                    # CHANGE 2: emit the precomputed tiny critical span (toolCall kept).
                    output.append(span_for[index])
                # else: no span → remove entirely (its toolCall is in strip_by_call).
                continue
            # Free Hard-ceiling clamp: a single pathological result above the ceiling
            # is hard-capped FIRST (only ever reduces; cannot keep more).
            if costs[index] > HARD_CEILING_CHARS:
                message, _ = truncate_message(message, int(HARD_CEILING_CHARS * 0.6), int(HARD_CEILING_CHARS * 0.2))
            if index in truncated_protected:
                message, did = _reduce(
                    message, GENTLE_PROTECTED_CAP,
                    int(GENTLE_PROTECTED_CAP * 0.75), int(GENTLE_PROTECTED_CAP * 0.25)
                )
                info["truncatedResultCount"] += int(did)
            elif index in truncated:
                message, did = _reduce(message, use_head + use_tail, use_head, use_tail)
                info["truncatedResultCount"] += int(did)
            elif index in tail_results and index not in untouchable and tail_cap:
                message, _ = _reduce(
                    message, TAIL_RESULT_CAP,
                    int(TAIL_RESULT_CAP * 0.75), int(TAIL_RESULT_CAP * 0.25)
                )
            elif index not in untouchable:
                message, _ = _reduce(
                    message, ABS_RESULT_CAP,
                    int(ABS_RESULT_CAP * 0.75), int(ABS_RESULT_CAP * 0.25)
                )
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

    info["reason"] = "pruned" if (
        dropped or info["truncatedResultCount"] or info["truncatedAssistantCount"] or info["dropSpanCount"]
    ) else "nothing_to_remove"
    info["targetChars"] = target_chars
    info["totalChars"] = total_chars
    info["escalation"] = {"assistCap": assist_cap, "trunc2": trunc2, "tailCap": tail_cap}
    info["plannedChars"] = planned_chars(assist_cap, trunc2, tail_cap)
    return output, info


def compress_structurally(
    messages: list[Any],
    escalation: dict[str, Any] | None = None,
    target_tokens: int = TARGET_TOKENS,
) -> tuple[list[Any], dict[str, Any]]:
    """m22 harvest entry point. Runs the m22 EXTRACTIVE build (CHANGE 1+2), computes
    m12's LEGACY build for the same turn, and enforces the HARD-SAFETY invariant
    (CHANGE 3): the m22 output MUST be <= m12's would-be harvest output on the SCORED
    metric (tiktoken tokens via final_token_estimate) AND on raw chars.

    Reconciliation ladder (each rung only REDUCES m22's bytes/tokens vs the previous
    rung; none ever keeps MORE than m12):
      0. m22 at the m12 kept-result caps (MID head/tail) + full drop-span cap.
      1. squeeze KEPT truncated results to the RECLAIM_MIN floor (fund the drop-spans
         by trimming kept results harder — CHANGE 3's primary lever).
      2. shrink the DROP-SPAN cap itself (the spans get tinier — keep the highest-
         signal lines only) while kept results stay at the floor.
      3. fall back to the m12-exact LEGACY build (worst case == m12, byte-for-byte AND
         token-for-token).
    The FIRST rung whose output is <= m12's legacy output IN TOKENS AND CHARS is
    shipped — so m22 keeps as much critical content as the budget allows, but NEVER
    puts more scored tokens (or chars) in front of the model than m12. Gating on the
    scored token metric is what prevents extraction's marker/ellipsis fragmentation
    from silently inflating tokens at equal-or-lower char count (the m21 failure class
    reached via fragmentation) — the rung-4 fallback fires precisely when it would.

    The escalation flags committed to state are always the m12/legacy flags so the
    sticky-escalation contract is identical to m12 and never inflated by an m22
    rebuild that we did not ship."""
    escalation = escalation if escalation is not None else {}

    # --- m12 legacy reference build (the budget ceiling AND the last-resort fallback) ---
    legacy_esc = dict(escalation)
    legacy_output, legacy_info = _harvest_build(
        messages, legacy_esc, TARGET_TOKENS,
        use_extractive=False, use_drop_span=False,
    )
    legacy_chars = sum(message_cost(m) for m in legacy_output)
    # THE SCORED METRIC. The platform scores on tiktoken tokens (final_token_estimate)
    # and the m21 Hard crater was TOKEN/trajectory driven, not char driven. Extraction
    # replaces m12's two CONTIGUOUS head/tail blocks with many short pinned-line
    # fragments separated by per-gap "…" ellipses + the [[CMP]] marker pair; that
    # fragment/marker density can tokenize HIGHER even at equal-or-lower char count.
    # So the invariant MUST be enforced on tokens, not chars: a rung ships only if its
    # output is <= m12 in BOTH tokens AND chars. (final_token_estimate is exact on the
    # platform's cl100k tiktoken; offline it falls back to char/4, which equals the
    # char check — safe both ways.)
    legacy_tokens = final_token_estimate(legacy_output)

    def _build(reclaim_head: int, reclaim_tail: int, span_cap: int):
        esc = dict(escalation)
        out, inf = _harvest_build(
            messages, esc, target_tokens,
            use_extractive=True, use_drop_span=True,
            reclaim_head=reclaim_head, reclaim_tail=reclaim_tail, span_cap=span_cap,
        )
        return out, inf, sum(message_cost(m) for m in out), final_token_estimate(out)

    # Reconciliation rungs, increasingly tight. Each only ever reduces bytes/tokens.
    rungs = [
        (0, MID_HEAD, MID_TAIL, DROP_SPAN_CAP),
        (1, RECLAIM_MIN_HEAD, RECLAIM_MIN_TAIL, DROP_SPAN_CAP),
        (2, RECLAIM_MIN_HEAD, RECLAIM_MIN_TAIL, DROP_SPAN_CAP // 2),
        (3, RECLAIM_MIN_HEAD, RECLAIM_MIN_TAIL, DROP_SPAN_CAP // 4),
    ]
    best_over = None  # remember the tightest m22 build even if it still exceeds m12
    for rung, rh, rt, sc in rungs:
        out, inf, chars, tokens = _build(rh, rt, sc)
        # Ship the first rung that is within the m12 budget on the SCORED metric
        # (tokens) AND on chars. Gating on tokens makes the rung-4 fallback fire
        # exactly when extraction's fragment/marker density would inflate scored
        # tokens — restoring the "m22 never puts more scored tokens in front of the
        # model than m12" guarantee by construction.
        if tokens <= legacy_tokens and chars <= legacy_chars:
            # Commit the m12/legacy escalation flags (stickiness == m12).
            escalation.clear()
            escalation.update(legacy_esc)
            inf["m22"] = {
                "rung": rung, "fellBackToM12": False,
                "legacyChars": legacy_chars, "m22Chars": chars,
                "legacyTokens": legacy_tokens, "m22Tokens": tokens,
                "withinM12Budget": True,
            }
            return out, inf
        if best_over is None or tokens < best_over[4]:
            best_over = (rung, out, inf, chars, tokens)

    # rung 4: even the tightest spans exceeded m12 on tokens (or chars) → ship the
    # m12-exact legacy build (worst case == m12, byte-for-byte AND token-for-token;
    # the hard-safety invariant holds absolutely on the scored metric).
    escalation.clear()
    escalation.update(legacy_esc)
    legacy_info["m22"] = {
        "rung": 4, "fellBackToM12": True,
        "legacyChars": legacy_chars, "legacyTokens": legacy_tokens,
        "tightestM22Chars": best_over[3] if best_over else None,
        "tightestM22Tokens": best_over[4] if best_over else None,
    }
    return legacy_output, legacy_info


# ---------------------------------------------------------------------------
# Entry point  (router / passthrough / rich dispatch are BYTE-IDENTICAL to m12)
# ---------------------------------------------------------------------------

def handle_assemble(payload: dict[str, Any]) -> dict[str, Any]:
    raw_messages = get_messages(payload)
    working, state_metadata, state_path, extras = resolve_stateful_messages(payload, raw_messages)

    params = get_params(payload)
    current_token_count = params.get("currentTokenCount")
    estimated = estimate_tokens(working)
    observed = max(
        estimated,
        estimate_tokens(raw_messages),
        current_token_count if isinstance(current_token_count, int) else 0,
        int(extras.get("maxObservedTokens") or 0),
    )
    prev_mode = extras.get("mode") or "passthrough"
    msg_depth = max(len(raw_messages), len(working))
    cumulative_observed = int(extras.get("cumulativeObserved") or 0) + estimate_tokens(raw_messages)
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

    working = strip_loop_guard(working)

    sanitize_changed = False
    pruned = False
    if mode == "passthrough":
        result_messages = raw_messages
        info: dict[str, Any] = {"reason": "below_activation_threshold"}
        changed = False
    elif mode == "harvest":
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
        result_messages = strip_loop_guard(result_messages)
        info["loopGuardFired"] = detect_loop_reason(result_messages) or None
        result_messages = append_loop_guard(result_messages)
        changed = fingerprint_messages(result_messages) != fingerprint_messages(raw_messages)
    else:
        sanitized = working
        result_messages, info = compress_gently(working)
        pruned = info.get("reason") == "gentle"
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
