#!/usr/bin/env python3
"""SOMA improved miner: structure-preserving trajectory compression.

Strategy vs the reference baseline (which keeps only the first user message and
the last 4 tool results):

- Keep ALL user/system messages verbatim (task statement + follow-up instructions).
- Keep assistant text everywhere (the agent's plan and findings), truncating only
  old, long text under budget pressure.
- Keep recent tool interactions intact; head+tail-truncate older tool results
  instead of deleting them; fully drop only the oldest interactions, and only
  when the token budget requires it.
- Every fully dropped interaction leaves a one-line digest (tool + args + result
  snippet) inside a sentinel-marked block appended to the first user message, so
  discovered facts (paths, line numbers, error strings) survive compression.
  The digest is parsed back out and regenerated on later rounds (no nesting).
- Exact-duplicate tool results (same file read twice) are dropped first.
- toolCall/toolResult pairing is preserved by construction: a result is dropped
  if and only if its invoking toolCall block is stripped in the same step. A
  final orphan check falls back to sanitize-only output if pairing ever breaks.

Protocol (same as the reference): `python improved_miner.py assemble` with the
connector payload on stdin, a single JSON object on stdout. Stdlib only;
tiktoken is used for the reported token estimate when available.
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
STATE_VERSION = 3
STATE_DIR_NAME = "state"

CHARS_PER_TOKEN = 4
# Absolute trajectory budget. Below it (and before first activation) we pass
# through unchanged so the provider's prompt cache keeps working; once over it
# we compress down to PRESSURE_RELIEF of the budget and then leave the output
# byte-stable (pure appends) until the budget is exceeded again. Cache-stable
# stretches between pressure rounds are the point: a ratio-based target would
# re-prune every round and invalidate the prefix cache on every call.
ACTIVATION_TOKENS = 8_000
TARGET_TOKENS = 8_000
PRESSURE_RELIEF = 0.75

# The newest tool interactions stay intact; the very newest are never modified.
KEEP_RECENT_FULL = 4
UNTOUCHABLE_RECENT = 2
# Char caps (head+tail truncation) applied progressively under budget pressure.
ABS_RESULT_CAP = 40_000
TAIL_RESULT_CAP = 16_000
MID_HEAD, MID_TAIL = 1_000, 400
MID2_HEAD, MID2_TAIL = 500, 200
ASSIST_HEAD, ASSIST_TAIL = 1_200, 300

DIGEST_BEGIN = "[SOMA COMPRESSED HISTORY"
DIGEST_HEADER = (
    "[SOMA COMPRESSED HISTORY v1 — earlier agent steps were removed to save "
    "context; one-line summaries below, oldest first]"
)
DIGEST_END = "[/SOMA COMPRESSED HISTORY]"
DIGEST_ARGS_CHARS = 110
DIGEST_RESULT_CHARS = 150
DIGEST_MAX_ENTRIES = 40
DIGEST_ENTRY_EST_CHARS = 320
DIGEST_MAX_PATHS = 6

# Paths like /a/b/c.py, django/utils/html.py:236 — the facts agents rediscover.
PATH_PATTERN = re.compile(r"(?:/)?[\w.-]+(?:/[\w.-]+)+\.[A-Za-z]{1,4}(?::\d+)?")


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
    activated: bool = False,
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
        "activated": bool(activated),
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
        "activated": bool(state.get("activated")) if state else False,
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


def describe_tool_call(message: Any, call_id: str) -> str:
    for block in iter_tool_call_blocks(message):
        if block.get("id") != call_id:
            continue
        name = block.get("name") or block.get("toolName")
        if not name and isinstance(block.get("function"), dict):
            name = block["function"].get("name")
        args = None
        for field in ("arguments", "args", "input", "parameters"):
            if field in block:
                args = block[field]
                break
        if args is None and isinstance(block.get("function"), dict):
            args = block["function"].get("arguments")
        args_text = clip(collapse_ws(extract_text(args)), DIGEST_ARGS_CHARS)
        return f"{name or 'tool'}({args_text})"
    return "tool(?)"


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
    trimmed = len(value) - head - tail
    return f"{value[:head]}\n…[soma: trimmed {trimmed} chars]…\n{value[-tail:] if tail else ''}"


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


# ---------------------------------------------------------------------------
# Digest block (lives inside the first user message, sentinel delimited)
# ---------------------------------------------------------------------------

def _split_digest(text: str) -> tuple[str, list[str]]:
    begin = text.find(DIGEST_BEGIN)
    if begin < 0:
        return text, []
    end = text.find(DIGEST_END, begin)
    segment = text[begin : end + len(DIGEST_END)] if end >= 0 else text[begin:]
    entries = [line.strip() for line in segment.splitlines() if line.strip().startswith("- ")]
    cleaned = (text[:begin] + (text[end + len(DIGEST_END) :] if end >= 0 else "")).rstrip()
    return cleaned, entries


def extract_existing_digest(message: Any) -> tuple[Any, list[str]]:
    if not isinstance(message, dict):
        return message, []
    content = message.get("content")
    if isinstance(content, str):
        if DIGEST_BEGIN not in content:
            return message, []
        cleaned_text, entries = _split_digest(content)
        cleaned = copy.deepcopy(message)
        cleaned["content"] = cleaned_text
        return cleaned, entries
    if isinstance(content, list):
        entries: list[str] = []
        new_blocks: list[Any] = []
        changed = False
        for block in content:
            text = block.get("text") if isinstance(block, dict) else None
            if isinstance(text, str) and DIGEST_BEGIN in text:
                cleaned_text, block_entries = _split_digest(text)
                entries.extend(block_entries)
                changed = True
                if cleaned_text.strip():
                    new_block = copy.deepcopy(block)
                    new_block["text"] = cleaned_text
                    new_blocks.append(new_block)
                continue
            new_blocks.append(block)
        if not changed:
            return message, []
        cleaned = copy.deepcopy(message)
        cleaned["content"] = new_blocks
        return cleaned, entries
    return message, []


def inject_digest(message: Any, entries: list[str]) -> Any:
    if not entries or not isinstance(message, dict):
        return message
    digest_text = "\n".join([DIGEST_HEADER, *entries[-DIGEST_MAX_ENTRIES:], DIGEST_END])
    content = message.get("content")
    out = copy.deepcopy(message)
    if isinstance(content, str):
        out["content"] = f"{content.rstrip()}\n\n{digest_text}"
        return out
    if isinstance(content, list):
        out["content"] = [*content, {"type": "text", "text": digest_text}]
        return out
    return message


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
    messages: list[Any], escalation: dict[str, Any] | None = None
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
    target_chars = TARGET_TOKENS * CHARS_PER_TOKEN
    # Under pressure, prune past the target so following rounds are pure
    # appends (byte-stable prefix → provider cache hits) until pressure returns.
    relief_chars = int(target_chars * PRESSURE_RELIEF)

    # Tail zone: the invoking call of the KEEP_RECENT_FULL-th newest result onward.
    recent_results = result_indices[-KEEP_RECENT_FULL:]
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
                # Drops require a strippable call block; otherwise truncate only.
                "droppable": bool(result_ids) and call_index is not None,
                "mode": "trunc",
            }
        )
    interactions.reverse()  # oldest first

    # The newest few messages are never modified (the agent needs them intact).
    untouchable_msgs = set(range(max(0, len(messages) - 3), len(messages)))

    def planned_chars(assist_cap: bool, trunc2: bool, tail_cap: bool) -> int:
        total = 0
        dropped_count = 0
        tail_result_set = set(result_indices[-KEEP_RECENT_FULL:])
        untouchable = set(result_indices[-UNTOUCHABLE_RECENT:])
        modes = {item["result_index"]: item["mode"] for item in interactions}
        for index, message in enumerate(messages):
            role = normalize_role(message.get("role")) if isinstance(message, dict) else ""
            cost = costs[index]
            if role == "toolResult":
                if index in modes:
                    mode = modes[index]
                    if mode == "drop":
                        dropped_count += 1
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
        # The rendered digest is capped at DIGEST_MAX_ENTRIES regardless of
        # how many interactions were dropped.
        total += min(dropped_count, DIGEST_MAX_ENTRIES) * DIGEST_ENTRY_EST_CHARS
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
        for item in interactions:
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
    strip_by_call: dict[int, set[str]] = {}
    digest_entries: list[str] = []
    for item in interactions:
        if item["mode"] != "drop":
            continue
        call_index = item["call_index"]
        strip_by_call.setdefault(call_index, set()).update(item["ids"])
        call_id = next(iter(item["ids"]))
        call_text = describe_tool_call(messages[call_index], call_id)
        if item["duplicate"]:
            snippet = "[duplicate of a later identical result]"
        else:
            result_text = collapse_ws(extract_text(messages[item["result_index"]].get("content")))
            snippet = clip(result_text, DIGEST_RESULT_CHARS)
            paths = list(dict.fromkeys(PATH_PATTERN.findall(result_text)))
            unseen = [p for p in paths if p not in snippet][:DIGEST_MAX_PATHS]
            if unseen:
                snippet += " | files: " + ", ".join(clip(p, 80) for p in unseen)
        digest_entries.append(f"- {call_text} -> {snippet}")
        info["droppedInteractionCount"] += 1
        if item["duplicate"]:
            info["duplicateResultCount"] += 1

    head, tail = (MID2_HEAD, MID2_TAIL) if trunc2 else (MID_HEAD, MID_TAIL)
    untouchable = set(result_indices[-UNTOUCHABLE_RECENT:])
    tail_results = set(result_indices[-KEEP_RECENT_FULL:])
    output: list[Any] = []
    for index, message in enumerate(messages):
        role = normalize_role(message.get("role")) if isinstance(message, dict) else ""
        if role == "toolResult":
            if index in dropped:
                continue
            if index in truncated:
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

    # Carry forward + inject the digest into the first user message.
    for index, message in enumerate(output):
        if isinstance(message, dict) and normalize_role(message.get("role")) == "user":
            cleaned, previous_entries = extract_existing_digest(message)
            output[index] = inject_digest(cleaned, [*previous_entries, *digest_entries])
            break

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
    activation_estimate = max(
        estimated, current_token_count if isinstance(current_token_count, int) else 0
    )
    # Hysteresis: once a session crosses the budget we keep managing its
    # context every round, so each round extends the previous compressed
    # output instead of flapping between compressed and raw shapes.
    activated = bool(extras.get("activated")) or activation_estimate >= ACTIVATION_TOKENS
    escalation = dict(extras.get("escalation") or {})

    sanitize_changed = False
    if not activated:
        # Pure pass-through below the budget: returning changed=False lets
        # OpenClaw send its native context untouched, preserving the
        # provider's prompt cache exactly like a no-plugin run.
        result_messages = raw_messages
        info: dict[str, Any] = {"reason": "below_activation_threshold"}
        pruned = False
        changed = False
    else:
        sanitized, sanitize_changed = sanitize_messages(working)
        result_messages, info = compress_structurally(sanitized, escalation)
        pruned = info.get("reason") == "pruned"
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
        changed = fingerprint_messages(result_messages) != fingerprint_messages(raw_messages)

    metadata = {
        **state_metadata,
        **info,
        "changed": changed,
        "pruned": pruned,
        "sanitized": sanitize_changed,
        "activated": activated,
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
            activated=activated,
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
