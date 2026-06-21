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

# v9 RICH+RELIABLE: the 3 top miners all share near-zero broken passes; flips
# come from RICH context, not aggression. So: keep the agent's recent working
# window byte-intact, keep everything load-bearing FULL (errors, tests, active
# files, recent edits), and only remove exact duplicates + lightly trim clearly
# stale, unrelated old bulk. Trajectories stay rich (~600k-1M); savings come
# from dedup + stale-trim, enough to clear the 20% gate without breaking runs.
RICH_INTACT_MSGS = 10          # last N messages kept byte-intact (never compressed)
RICH_STALE_CAP = 6_000         # generous cap for old, non-protected, stale bulk
RICH_PROTECTED_CAP = 30_000    # "full" for practical purposes (guards pathological logs)
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

# Tight-mode coach, COMPLIANT with the CoT-Compression-3 organizer ruling
# (2026-06-12): only the three explicitly-permitted classes are used —
# (a) context-management notes ("here is a summary"), (b) loop detection,
# (c) forced stopping at a clear stopping condition. The earlier generic
# behavioral directives ("edit the real file", "delete scratch files", etc.)
# were dropped: they are neither loop-detection nor forced-stopping, so under
# the ruling's catch-all they count as disallowed "other prompt injection".
# Appended always-last so only its own tokens re-bill (cache-cheap).
COACH_MARKER = "[SOMA CONTEXT NOTE]"
COACH_HEADER = "[SOMA CONTEXT NOTE]"
# v5: dynamic coach — surface the concrete failing tests from the latest test
# output (flip conversion is the scoreboard lever: 2-of-5-run flips need to
# become 4-of-5), and a conclude-now governor once a session has burned enough
# tokens that further grinding feeds the per-category token penalty instead of
# the pass rate.
GOVERNOR_TOKENS = 150_000
GOVERNOR_TARGET_TOKENS = 6_000
TEST_STATUS_MAX_LINES = 5
TEST_STATUS_LINE_CLIP = 130
# v5.1: re-state the original issue at end-of-context (attention there beats
# position-1 on 100k contexts), and break do-nothing loops (same tool call
# with identical output repeating = the wandering that loses partial flips).
ISSUE_REINJECT_CLIP = 1_500
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


def is_error_bearing(message: Any) -> bool:
    text = extract_text(message.get("content"))[:20_000].lower() if isinstance(message, dict) else ""
    return any(marker in text for marker in ERROR_MARKERS)


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


def is_coach_message(message: Any) -> bool:
    if not isinstance(message, dict) or normalize_role(message.get("role")) != "user":
        return False
    return extract_text(message.get("content")).startswith(COACH_MARKER)


def strip_coach(messages: list[Any]) -> list[Any]:
    return [m for m in messages if not is_coach_message(m)]


def extract_test_status(messages: list[Any]) -> str:
    """Failing-test lines from the most recent error-bearing tool result."""
    for message in reversed(messages):
        if not isinstance(message, dict) or normalize_role(message.get("role")) != "toolResult":
            continue
        if not is_error_bearing(message):
            continue
        text = extract_text(message.get("content"))[-30_000:]
        lines: list[str] = []
        for match in TEST_LINE_PATTERN.finditer(text):
            line = collapse_ws(match.group(0))
            if line and line not in lines:
                lines.append(clip(line, TEST_STATUS_LINE_CLIP))
            if len(lines) >= TEST_STATUS_MAX_LINES:
                break
        return "\n".join(lines)
    return ""


def extract_issue_text(messages: list[Any]) -> str:
    """The original task statement (first user message, digest stripped)."""
    for message in messages:
        if isinstance(message, dict) and normalize_role(message.get("role")) == "user":
            if is_coach_message(message):
                continue
            text = extract_text(message.get("content"))
            cut = text.find(DIGEST_BEGIN)
            if cut >= 0:
                text = text[:cut]
            text = text.strip()
            if len(text) > ISSUE_REINJECT_CLIP:
                head = int(ISSUE_REINJECT_CLIP * 0.8)
                tail = ISSUE_REINJECT_CLIP - head
                text = f"{text[:head]}\n…\n{text[-tail:]}"
            return text
    return ""


def detect_loop(messages: list[Any]) -> str:
    """Same tool call producing the identical result LOOP_THRESHOLD+ times in
    the recent window — repetition that yields no new information."""
    result_hash: dict[str, str] = {}
    for message in messages:
        ids = extract_tool_result_ids(message)
        if ids:
            digest = hashlib.sha256(
                collapse_ws(extract_text(message.get("content"))).encode("utf-8")
            ).hexdigest()
            for rid in ids:
                result_hash[rid] = digest
    recent: list[tuple[str, str]] = []  # (signature, args preview)
    for message in messages:
        for block in iter_tool_call_blocks(message):
            call_id = (block.get("id") or "").strip()
            if call_id not in result_hash:
                continue
            name = block.get("name") or block.get("toolName") or "tool"
            args = clip(collapse_ws(extract_text(
                block.get("arguments") or block.get("args") or block.get("input") or ""
            )), LOOP_SIG_ARGS_CLIP)
            recent.append((f"{name}|{args}|{result_hash[call_id]}", f"{name}({args})"))
    recent = recent[-LOOP_WINDOW:]
    counts: dict[str, int] = {}
    preview: dict[str, str] = {}
    for sig, prev in recent:
        counts[sig] = counts.get(sig, 0) + 1
        preview[sig] = prev
    for sig, n in counts.items():
        if n >= LOOP_THRESHOLD:
            return preview[sig]
    return ""


def build_coach_text(messages: list[Any], *, governor: bool) -> str:
    # v6-clean: STRICTLY the two permitted techniques only — loop detection and
    # forced stopping. No task restatement, no failing-test naming, no
    # minimal-change/source-file framing — all of which the organizers ruled
    # out as steering workflow / going beyond context compression (2026-06-13).
    parts = [COACH_HEADER]

    # Loop detection.
    loop = detect_loop(messages)
    if loop:
        parts.append(
            f"Loop detected: you have repeated the same action with an identical "
            f"result multiple times ({loop}). Repeating it will not produce new "
            f"information — change your approach."
        )

    # Forced stopping (generic; no goal-steering content).
    parts.append(
        "If your change is complete and the tests pass, stop and return your final "
        "answer instead of continuing to explore."
    )
    if governor:
        parts.append(
            "You have spent substantial effort already. If the tests pass, STOP NOW "
            "and return the final answer; do not explore further."
        )
    return "\n".join(parts)


def append_coach(messages: list[Any], *, governor: bool = False) -> list[Any]:
    text = build_coach_text(messages, governor=governor)
    return [*messages, {"role": "user", "content": [{"type": "text", "text": text}]}]


# ---------------------------------------------------------------------------
# Gentle mode: truncation-only compression for mid-size contexts.
# Never drops a message, never touches user/system/assistant content, keeps
# toolCall/toolResult pairing untouched by construction. Old bulky tool
# results get head+tail truncation (error-bearing ones keep larger budgets);
# exact-duplicate old results collapse to a one-line marker.
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


def compress_gently(messages: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    # v9 RICH+RELIABLE compression. NEVER drops a message and never touches the
    # recent working window — only dedups exact-duplicate old results and lightly
    # trims old, non-load-bearing, stale bulk to a generous cap.
    info: dict[str, Any] = {
        "truncatedResultCount": 0,
        "duplicateResultCount": 0,
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

    # Newest-first hash registry so older exact duplicates collapse to a marker.
    seen_hashes: set[str] = set()
    duplicate_indices: set[int] = set()
    for index in reversed(result_indices):
        digest = hashlib.sha256(
            collapse_ws(extract_text(messages[index].get("content"))).encode("utf-8")
        ).hexdigest()
        if digest in seen_hashes and index not in intact:
            duplicate_indices.add(index)
        seen_hashes.add(digest)

    output: list[Any] = []
    for index, message in enumerate(messages):
        role = normalize_role(message.get("role")) if isinstance(message, dict) else ""
        if role == "toolResult" and index not in intact:
            if index in duplicate_indices:
                message = _replace_text_fields(
                    message, "[soma: identical to a later tool result in this session]"
                )
                info["duplicateResultCount"] += 1
            elif _is_load_bearing(message, active):
                # keep full (guard only against pathological size)
                message, did = extractive_message(message, RICH_PROTECTED_CAP, active)
                info["protectedResultCount"] += 1
                info["truncatedResultCount"] += int(did)
            else:
                # clearly stale, unrelated bulk → light extractive trim, generous cap
                message, did = extractive_message(message, RICH_STALE_CAP, active)
                info["truncatedResultCount"] += int(did)
        output.append(message)

    if info["truncatedResultCount"] or info["duplicateResultCount"]:
        info["reason"] = "gentle"
    return output, info


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
        # rstrip: extraction strips lines, so the written form must match the
        # re-extracted form byte-for-byte or the digest flaps across rounds.
        digest_entries.append(f"- {call_text} -> {snippet}".rstrip())
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
    # v9: two modes only — passthrough (small) or rich (everything else, sticky).
    # No drop-with-digest mode at all; rich is truncation-only, never drops a
    # message, so it cannot break tool pairing or strand the agent.
    if prev_mode == "rich" or observed >= PASS_THROUGH_TOKENS:
        mode = "rich"
    else:
        mode = "passthrough"
    escalation = dict(extras.get("escalation") or {})

    # Our coach message from previous rounds rides in via state; remove it so
    # compression never sees it, and re-append at the end (rich mode only).
    working = strip_coach(working)

    sanitize_changed = False
    pruned = False
    if mode == "passthrough":
        # Below the budget: returning changed=False lets OpenClaw send its
        # native context untouched, preserving the provider's prompt cache
        # exactly like a no-plugin run.
        result_messages = raw_messages
        info: dict[str, Any] = {"reason": "below_activation_threshold"}
        changed = False
    else:
        # Rich mode: byte-identical except dedup + light stale-trim of old bulk.
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
        result_messages = append_coach(
            strip_coach(result_messages), governor=observed >= GOVERNOR_TOKENS
        )
        changed = fingerprint_messages(result_messages) != fingerprint_messages(raw_messages)

    metadata = {
        **state_metadata,
        **info,
        "changed": changed,
        "pruned": pruned,
        "sanitized": sanitize_changed,
        "mode": mode,
        "observedTokens": observed,
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
