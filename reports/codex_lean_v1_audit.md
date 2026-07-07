Reading additional input from stdin...
OpenAI Codex v0.142.5
--------
workdir: /Users/eric.xiao/joshua-work/soma
model: gpt-5.5
provider: openai
approval: never
sandbox: read-only
reasoning effort: high
reasoning summaries: none
session id: 019f3b45-988f-7140-8fbc-6b0471d5cce8
--------
user
You are the independent verifier in a dual-agent protocol — PRE-UPLOAD MINER AUDIT (gate #1). Your mandate: try to find reasons this candidate must NOT be uploaded (NO-GO), adversarially. Do not trust the author's claims — verify from code.

CANDIDATE: miner/cot_compression/upload_miner_lean_v1.py (this repo)
It is a comp-110 (CoT-Compression-5) SOMA miner: imported as a module by the compression sidecar and called as compress_messages(messages, path, metadata) -> list on EVERY outgoing LLM request (OpenAI chat messages). Returned list replaces payload['messages'].
CONTRACT CODE (absolute paths, read them): /Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/main.py (module loading + invocation) and /Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/proxy.py (what payload/messages contain).
RULES (read them): miner/README_prompting.md — §5.1/§5.2 exact allowed strings; markers must wrap original content, never descriptions/counts; no prompt semantic changes; no new instructions; no loop-forcing.
TEST HARNESS: experiments/candidates/LEAN_comp110_v1/test_lean_miner.py

AUDIT DIMENSIONS — for each, verdict PASS / CONCERN / BLOCKING with evidence (file:line):
1. STRUCTURAL SAFETY: any input shape that yields malformed output (parts lists, tool_calls, None/int/dict content, missing keys, unicode, nested parts)? Any path that mutates input dicts in place? Any way the function raises OUTSIDE the fail-open try/except?
2. COMPLIANCE: every string the module can EMIT at runtime vs the §5.1 allowed set (check f-strings carefully). Markers wrap extracted ORIGINAL lines only? System/developer never modified? Any semantic description, count, or instruction that could fail review (comp-108 DQ pattern: descriptive text inside markers)?
3. DETERMINISM & CACHE-STABILITY: pure function of (messages, env profile)? Does a growing history (same prefix + appended messages) re-compress its shared prefix byte-identically — INCLUDING dedupe [[BLOCK n]] numbering (seen_blocks ordering)? Counterexample if any.
4. BREAK-RISK: ways this could make an agent run FAIL — compressing the newest tool result the agent must act on; the head+tail slice on few-giant-line content cutting mid-JSON/mid-diff; dedupe references the model can't resolve; budget interactions.
5. PERFORMANCE: per-request CPU on multi-MB arrays (author measured ~60ms/13.6MB — sanity-check the complexity).
6. LOGIC BUGS: _budget_for boundaries; _MAX_LINE truncation interactions; _DEDUPE_MIN(2000) vs MIN_COMPRESS(6000) interplay — blocks 2000..6000 chars get [[BLOCK]]-wrapped but NOT compressed: is that wrapping a net token INCREASE risk?; profile env handling; the few-giant-lines branch (n <= HEAD+TAIL+2) using raw text while lines were _MAX_LINE-truncated.

OUTPUT: a table (dimension | verdict | evidence), then REQUIRED fixes vs RECOMMENDED improvements, then final line: VERDICT: GO or NO-GO or GO-WITH-CHANGES (changes enumerated).
codex
I’ll audit from the actual files and contract paths first, then cross-check emitted strings against the README rules and harness. I’m constrained to read-only here, so I’ll verify and report rather than patch.
exec
/bin/zsh -lc "sed -n '1,260p' miner/cot_compression/upload_miner_lean_v1.py" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
"""SOMA comp-110 (CoT-Compression-5) candidate: LEAN v1 — endurance-first extractive compressor.

Contract (verified against SOMA-benchmark src/compression_service/app/main.py + proxy.py):
the compression sidecar imports this file as a module (mounted at /app/miner/base_miner.py) and
calls `compress_messages(messages, path, metadata) -> list` on EVERY outgoing LLM request with the
OpenAI-style chat `messages` array; the returned list replaces `payload["messages"]`.
`metadata` is currently just {"path": path} — no task/mode info (verified 2026-07-07).

Design (evidence: reports/comp108_cap32pin_postmortem.md + reports/comp110_hard_strategy.md):
- ENDURANCE-FIRST: lean per-step context -> agent survives more steps -> flip consistency +
  explore savings. Depth target ~2.5x (the comp-108 M-winner's proven-compliant zone).
- TIERED CAP (ported from cap32): small content passes through; mid content is line-extracted to a
  budget; huge content (>53k chars, the proven boundary) gets head+signal+tail to a larger budget.
- QUALITY FLOOR: lines carrying file paths / line numbers / errors / tracebacks / failing tests /
  diff markers / imports / def-class signatures are ALWAYS kept (explore quality = hit-rate minus
  noise-rate; swebench edit correctness needs locations).
- CACHE-STABLE: rules depend only on message content (never on position/age/time), so a growing
  history re-compresses its shared prefix byte-identically -> stable prompt-cache prefix
  (weighted tokens: cached input costs 1/3).
- BREAK-AVERSE: whole pass is fail-open (any internal error returns the ORIGINAL messages);
  system/developer messages, tool_calls, non-text parts, and message order/count/roles are never
  touched; markers wrap EXTRACTED ORIGINAL LINES only (never descriptions/counts — the 5Fjms DQ).
- DETERMINISTIC: pure function of (messages, profile); no randomness, no clock, no network, stdlib only.
- PIN (comp-108 _STRUCT_PATTERN import-pinning) is NOT ported by default — Codex-verified
  net-negative. An isolated experiment flag exists (SOMA_LEAN_PIN=1) for local A/B ONLY.

Profiles (env SOMA_LEAN_PROFILE = conservative | target | aggressive; default target):
  budgets are CHARACTER budgets per message-content block (chars ~= 4x tokens).

Compliance: emits ONLY README_prompting.md §5.1 allowed strings: [[CMP]] / [[/CMP]] /
[[BLOCK X]] / [[/BLOCK X]] / "Same response as in [[BLOCK X]]." — wrapping original content.
No prompt semantics changed, no instructions added/removed/reordered, no loop injection.
"""
from __future__ import annotations

import hashlib
import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# profiles / knobs
# ---------------------------------------------------------------------------

_PROFILES = {
    #                 min_compress  mid_budget  huge_threshold  huge_budget
    "conservative": (9_000,        16_000,     53_000,         30_000),
    "target":       (6_000,        10_000,     53_000,         18_000),
    "aggressive":   (4_000,         6_000,     53_000,         10_000),
}
_PROFILE = os.getenv("SOMA_LEAN_PROFILE", "target").strip().lower()
if _PROFILE not in _PROFILES:
    _PROFILE = "target"
MIN_COMPRESS, MID_BUDGET, HUGE_THRESHOLD, HUGE_BUDGET = _PROFILES[_PROFILE]

# EXPERIMENT ONLY (off by default; Codex-verified net-negative in comp-108 — do not enable for upload)
_PIN_ENABLED = os.getenv("SOMA_LEAN_PIN", "0").strip() == "1"

_HEAD_LINES = 25          # always keep the first N lines of a compressed block
_TAIL_LINES = 15          # and the last N lines
_DEDUPE_MIN = 2_000       # blocks >= this size are eligible for [[BLOCK X]] dedupe

CMP_START = "[[CMP]]"
CMP_END = "[[/CMP]]"

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
    | (?: ^\s*(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*]+$ )   # imports (kept: 1-line cost, location signal)
    | (?: [\w\-./]+\.(?:py|c|h|cpp|js|ts|tsx|json|yaml|yml|toml|cfg|ini|txt|rst|md|html|css|xml)\b )  # file paths
    | (?: \bline\s+\d+\b | :\d+:\d* )              # line-number references
    """,
    re.M,
)

_PIN_RX = re.compile(r"^\s*(?:@\w+|raise\b|except\b)", re.M)   # the comp-108 pin extras (experiment only)


def _is_signal(line: str) -> bool:
    if _KEEP_RX.search(line):
        return True
    if _PIN_ENABLED and _PIN_RX.search(line):
        return True
    return False


# ---------------------------------------------------------------------------
# core block compressor (pure; content -> content)
# ---------------------------------------------------------------------------

_MAX_LINE = 2_000         # deterministic per-line cap inside an extraction (bounds head/tail cost)


def _compress_text(text: str, budget: int) -> str:
    """Extractive head + signal-lines + tail within a char budget. Deterministic.
    The KEPT EXTRACTION (original lines, a subset of the source) is wrapped in [[CMP]]/[[/CMP]] —
    the comp-108 champion's verified-compliant pattern (never descriptions/counts inside markers)."""
    if len(text) <= budget:
        return text
    lines = [l if len(l) <= _MAX_LINE else l[:_MAX_LINE] for l in text.splitlines()]
    n = len(lines)
    if n <= _HEAD_LINES + _TAIL_LINES + 2:
        # few giant lines: hard head/tail slice of the raw text
        keep = max(budget // 2, 256)
        extraction = text[:keep] + "\n" + text[-keep:]
        return CMP_START + "\n" + extraction + "\n" + CMP_END

    keep_flags = [False] * n
    for i in range(min(_HEAD_LINES, n)):
        keep_flags[i] = True
    for i in range(max(n - _TAIL_LINES, 0), n):
        keep_flags[i] = True

    used = sum(len(lines[i]) + 1 for i in range(n) if keep_flags[i])
    # pass 1: signal lines (the quality floor), in document order
    for i in range(n):
        if keep_flags[i] or not _is_signal(lines[i]):
            continue
        cost = len(lines[i]) + 1
        if used + cost > budget:
            continue
        keep_flags[i] = True
        used += cost
    # pass 2: fill remaining budget in document order (deterministic, locally coherent)
    for i in range(n):
        if keep_flags[i]:
            continue
        cost = len(lines[i]) + 1
        if used + cost > budget:
            continue
        keep_flags[i] = True
        used += cost

    extraction = "\n".join(lines[i] for i in range(n) if keep_flags[i])
    return CMP_START + "\n" + extraction + "\n" + CMP_END


# ---------------------------------------------------------------------------
# message-array pass
# ---------------------------------------------------------------------------

def _budget_for(size: int) -> int | None:
    """Tiered cap: None = passthrough."""
    if size <= MIN_COMPRESS:
        return None
    if size <= HUGE_THRESHOLD:
        return MID_BUDGET
    return HUGE_BUDGET


def _compressible(msg: dict) -> bool:
    role = msg.get("role")
    if role in ("system", "developer"):
        return False                        # never touch instructions
    if role == "assistant" and msg.get("tool_calls"):
        return False                        # never risk tool-call JSON
    return role in ("tool", "user", "assistant")


def _content_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()


def compress_messages(
    messages: list[Any] | None = None,
    path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[Any]:
    del path, metadata                       # currently only {"path": ...}; unused (compliance-safe)
    if not isinstance(messages, list):
        return messages if isinstance(messages, list) else []
    try:
        return _pass(messages)
    except Exception:
        return messages                      # fail-open: NEVER break the run


def _pass(messages: list[Any]) -> list[Any]:
    seen_blocks: dict[str, int] = {}        # content-hash -> block number (first occurrence order)
    out: list[Any] = []
    for msg in messages:
        if not isinstance(msg, dict) or not _compressible(msg):
            out.append(msg)
            continue
        content = msg.get("content")

        if isinstance(content, str):
            new_content = _transform_text(content, seen_blocks)
            if new_content is not content:
                msg = dict(msg)
                msg["content"] = new_content
            out.append(msg)
        elif isinstance(content, list):
            new_parts, changed = [], False
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                    new_text = _transform_text(part["text"], seen_blocks)
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
            out.append(msg)                  # None / unknown shape: untouched
    return out


def _transform_text(text: str, seen_blocks: dict[str, int]) -> str:
    size = len(text)
    # dedupe first: an identical large block already emitted earlier in THIS history
    if size >= _DEDUPE_MIN:
        h = _content_hash(text)
        if h in seen_blocks:
            return f"Same response as in [[BLOCK {seen_blocks[h]}]]."
        budget = _budget_for(size)
        if budget is None:
            seen_blocks[h] = len(seen_blocks) + 1
            n = seen_blocks[h]
            return f"[[BLOCK {n}]]\n{text}\n[[/BLOCK {n}]]"
        compressed = _compress_text(text, budget)
        seen_blocks[h] = len(seen_blocks) + 1
        n = seen_blocks[h]
        return f"[[BLOCK {n}]]\n{compressed}\n[[/BLOCK {n}]]"
    budget = _budget_for(size)
    if budget is None:
        return text
    return _compress_text(text, budget)

exec
/bin/zsh -lc "pwd && rg --files -g 'upload_miner_lean_v1.py' -g 'README_prompting.md' -g 'test_lean_miner.py'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
/Users/eric.xiao/joshua-work/soma
miner/README_prompting.md
miner/cot_compression/upload_miner_lean_v1.py
experiments/candidates/LEAN_comp110_v1/test_lean_miner.py

exec
/bin/zsh -lc "sed -n '1,320p' experiments/candidates/LEAN_comp110_v1/test_lean_miner.py" in /Users/eric.xiao/joshua-work/soma
exec
/bin/zsh -lc "sed -n '1,260p' miner/README_prompting.md" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
# Miner Prompt Editing Rules

This document defines what prompt edits are allowed in miner submissions.

Goal: allow token optimizations and loop safety without changing agent behavior.

## Hard Rule

Only these two categories are allowed:

1. Compression markers.
2. Loop detection guards.

Everything else is disallowed.

---

## 1) Compression Marker Definitions

Compression markers are metadata wrappers around existing prompt content.

Allowed marker behavior:

- Preserve the original instruction meaning exactly.
- Preserve instruction order.
- Preserve all requirements.
- Preserve tool policy, safety policy, role policy, and output contract.
- Use clear marker boundaries such as `Compressed text starts here` and `Compressed text ends here`.
- Marker aliases may be defined once and reused; `[[CMP]]` is the start marker and `[[/CMP]]` is the end marker.
- `Same response as in ...` references are allowed only when the referenced block is explicit and unambiguous.

Not allowed for markers:

- Rewriting, weakening, strengthening, or deleting instructions.
- Adding new behavior constraints.
- Changing output format/schema requirements.
- Ambiguous references such as `Same response as above` without a unique target.

---

## 2) Loop Detection Definitions

Loop detection is a runtime safety guard that terminates repeated no-progress behavior.

Allowed loop guard behavior:

- Trigger only on objective repeated/no-progress conditions.
- Keep normal successful execution behavior unchanged.
- Do not alter scoring logic.
- Do not alter final-output criteria.
- Fail fast with a clear loop reason when a loop is detected.

Not allowed for loop guards:

- Prompt edits that change strategy, reasoning policy, or tool-use policy.
- Prompt edits that force shortcuts to reduce token usage.
- Any change that affects non-loop successful behavior.

---

## 3) Global Disallowed Changes

The following are disallowed under this policy:

- Any prompt semantic change beyond marker metadata.
- Any new instruction that changes agent behavior.
- Any reordering or removal of policy blocks.
- Any schema/contract change for outputs.
- Any safety or tool-policy change.

---

## 4) Submission Definition Checklist

A compliant submission satisfies all of the following:

1. Prompt meaning is unchanged except metadata markers.
2. No instruction was added, removed, or reordered.
3. Loop detection only targets repeated/no-progress cycles.
4. Non-loop successful behavior is unchanged.
5. Output format contract is unchanged.
6. Safety and tool-use policies are unchanged.

---

## 5) Allowed Prompts

If miners want to use any prompt format or exact string outside this list, they should discuss it first on the public channel.

### 5.1 Markers

Allowed exact strings:

- `Compressed text starts here`
- `Compressed text ends here`
- `[[CMP]]`
- `[[/CMP]]`
- `[[BLOCK X]]`
- `[[/BLOCK X]]`
- `Same response as in [[BLOCK X]].`

### 5.2 Loop Detection

Allowed exact loop-detection reason strings:

- `loop_detected: repeated assistant response`
- `loop_detected: repeated tool call signature`

 succeeded in 0ms:
#!/usr/bin/env python3
"""Standalone verification harness for upload_miner_lean_v1 (comp-110 candidate). Stdlib only.

Run:  python3 experiments/candidates/LEAN_comp110_v1/test_lean_miner.py
      SOMA_LEAN_PROFILE=aggressive python3 ...   (profile A/B)
Checks: import/contract, structural safety, quality floor, ratio zone, small-msg passthrough,
determinism, parts/tool_calls/None handling, dedupe, growing-history prefix stability, marker set.
"""
from __future__ import annotations
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MINER = ROOT / "miner" / "cot_compression" / "upload_miner_lean_v1.py"

spec = importlib.util.spec_from_file_location("lean_v1", MINER)
mod = importlib.util.module_from_spec(spec)
sys.modules["lean_v1"] = mod
spec.loader.exec_module(mod)
compress_messages = mod.compress_messages

FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
    if not cond:
        FAIL += 1


def make_log(n_lines=1200, seed_word="chatter"):
    lines = []
    for i in range(n_lines):
        if i % 97 == 0:
            lines.append(f'  File "/testbed/django/db/models/query.py", line {100+i}, in _fetch_all')
        elif i % 89 == 0:
            lines.append(f"FAILED tests/queries/test_qs_combinators.py::test_union_{i} - AssertionError")
        elif i % 83 == 0:
            lines.append(f"import module_{i}.submodule")
        else:
            lines.append(f"{seed_word} {i} " + "x" * 120)
    return "\n".join(lines)


def total_chars(msgs):
    tot = 0
    for m in msgs:
        c = m.get("content")
        if isinstance(c, str):
            tot += len(c)
        elif isinstance(c, list):
            tot += sum(len(p.get("text", "")) for p in c if isinstance(p, dict))
    return tot


print(f"profile = {mod._PROFILE}  budgets: min={mod.MIN_COMPRESS} mid={mod.MID_BUDGET} "
      f"huge_thr={mod.HUGE_THRESHOLD} huge={mod.HUGE_BUDGET}  pin={mod._PIN_ENABLED}")

# --- 1. contract ---
print("\n[1] contract")
out = compress_messages([], "/", {})
check("empty list -> list", out == [])
check("None -> []", compress_messages(None) == [])
check("kwargs signature (messages/path/metadata)", True)

# --- 2/3/4. realistic conversation ---
print("\n[2] structure, quality floor, ratio")
big_log = make_log(1200)                            # ~150k chars -> HUGE tier
mid_log = make_log(250, "info")                     # ~32k chars  -> MID tier
convo = [
    {"role": "system", "content": "You are Copilot CLI. Follow the task instructions exactly."},
    {"role": "user", "content": "Fix the failing test in django/db/models/query.py."},
    {"role": "assistant", "content": None,
     "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{\"cmd\": \"pytest -x\"}"}}]},
    {"role": "tool", "tool_call_id": "c1", "content": big_log},
    {"role": "assistant", "content": "The failure is in _fetch_all; reading the file."},
    {"role": "tool", "tool_call_id": "c2", "content": mid_log},
    {"role": "user", "content": [{"type": "text", "text": make_log(400, "partstext")},
                                  {"type": "image_url", "image_url": {"url": "data:x"}}]},
    {"role": "user", "content": "short trailing question?"},
]
orig = copy.deepcopy(convo)
out = compress_messages(copy.deepcopy(convo), "/v1/chat/completions", {"path": "/"})

check("returns list, same length", isinstance(out, list) and len(out) == len(convo))
check("roles preserved in order", [m.get("role") for m in out] == [m.get("role") for m in convo])
check("system untouched", out[0] == convo[0])
check("tool_calls message untouched", out[2] == convo[2])
check("None content untouched", out[2].get("content") is None)
check("non-text part untouched", out[6]["content"][1] == convo[6]["content"][1])
check("tool_call_id preserved", out[3].get("tool_call_id") == "c1")
check("short trailing message byte-identical", out[7]["content"] == convo[7]["content"])
check("input not mutated", convo == orig)
check("JSON-serializable", bool(json.dumps(out)))

big_out = out[3]["content"]
check("traceback frame survives", 'File "/testbed/django/db/models/query.py", line' in big_out)
check("FAILED test line survives", "FAILED tests/queries/test_qs_combinators.py" in big_out)
check("import line survives", re.search(r"^import module_\d+", big_out, re.M) is not None)
check("markers are exact allowed strings", "[[CMP]]" in big_out and "[[/CMP]]" in big_out)
bad_marker = re.search(r"\[\[(?!CMP\]\]|/CMP\]\]|BLOCK \d+\]\]|/BLOCK \d+\]\])", big_out)
check("no disallowed marker variants", bad_marker is None)
check("no descriptive text inside empty markers (chars omitted etc.)",
      "omitted" not in big_out and "truncated" not in big_out and "elided" not in big_out)

r_all = total_chars(orig) / max(total_chars(out), 1)
r_big = len(orig[3]["content"]) / max(len(big_out), 1)
# Budgets are the offline-calibratable contract; the ~2.5x RUN-LEVEL token zone can only be
# measured in real eval (task tokens_without/tokens_with), so here: tier budgets + deep-enough.
check("huge block lands at its budget", len(big_out) <= mod.HUGE_BUDGET * 1.2, f"{len(big_out)} <= {mod.HUGE_BUDGET}*1.2")
check("mid block lands at its budget", len(out[5]["content"]) <= mod.MID_BUDGET * 1.2)
check("bulk-heavy convo compresses deep (>=2x)", r_all >= 2.0, f"overall {r_all:.2f}x")
print(f"      ratios (bulk-heavy synthetic): overall {r_all:.2f}x | huge-block {r_big:.2f}x | mid-block "
      f"{len(orig[5]['content'])/max(len(out[5]['content']),1):.2f}x")

# realistic mix: mostly small turns + one huge read + one mid log -> expect ~2-4x
mix = [{"role": "system", "content": "You are Copilot CLI."}]
for i in range(14):
    mix.append({"role": "assistant", "content": f"step {i}: inspecting the code region near the failure." + " detail" * 40})
    mix.append({"role": "tool", "tool_call_id": f"t{i}", "content": f"$ cmd-{i} ok\n" + ("out " * 300)})  # ~1.2k, passthrough
mix.append({"role": "tool", "tool_call_id": "big", "content": make_log(1200, "filedump")})
mix.append({"role": "tool", "tool_call_id": "mid", "content": make_log(250, "pytestlog")})
mix_out = compress_messages(copy.deepcopy(mix))
r_mix = total_chars(mix) / max(total_chars(mix_out), 1)
zone = {"conservative": (1.5, 4.0), "target": (2.0, 4.8), "aggressive": (3.5, 8.0)}[mod._PROFILE]
check(f"realistic-mix ratio in profile zone {zone}", zone[0] <= r_mix <= zone[1], f"mix {r_mix:.2f}x")

# --- 5. determinism ---
print("\n[3] determinism")
out2 = compress_messages(copy.deepcopy(convo), "/v1/chat/completions", {"path": "/"})
check("same input -> byte-identical output", json.dumps(out) == json.dumps(out2))

# --- 6. dedupe ---
print("\n[4] dedupe")
dup = make_log(300, "dupread")
msgs = [{"role": "user", "content": "read it"},
        {"role": "tool", "tool_call_id": "a", "content": dup},
        {"role": "assistant", "content": "again"},
        {"role": "tool", "tool_call_id": "b", "content": dup}]
dout = compress_messages(copy.deepcopy(msgs))
check("first occurrence carries [[BLOCK n]]", re.search(r"\[\[BLOCK \d+\]\]", dout[1]["content"] or "") is not None)
check("repeat replaced by Same-response reference",
      re.fullmatch(r"Same response as in \[\[BLOCK \d+\]\]\.", dout[3]["content"] or "") is not None)

# --- 7. growing-history prefix stability (cache-safety proxy) ---
print("\n[5] prefix stability")
hist1 = copy.deepcopy(convo[:5])
hist2 = copy.deepcopy(convo)                 # same first 5 + 3 more
o1 = compress_messages(copy.deepcopy(hist1))
o2 = compress_messages(copy.deepcopy(hist2))
check("shared history prefix compresses byte-identically",
      json.dumps(o1[:5]) == json.dumps(o2[:5]))

# --- 8. hostile shapes (fail-open) ---
print("\n[6] hostile shapes")
weird = [{"role": "tool"}, {"content": "x"}, "not-a-dict", {"role": "tool", "content": 42},
         {"role": "tool", "content": {"nested": "dict"}}]
wout = compress_messages(copy.deepcopy(weird))
check("hostile shapes returned unharmed", json.dumps(wout) == json.dumps(weird))

print(f"\n{'ALL PASS' if FAIL == 0 else f'{FAIL} FAILURES'}")
sys.exit(1 if FAIL else 0)

exec
/bin/zsh -lc "sed -n '1,260p' /Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/main.py && sed -n '1,260p' /Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/proxy.py" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
from __future__ import annotations

import importlib.util
import inspect
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

COMPRESSOR_CANDIDATE_NAMES = (
    "compress_messages",
    "compress_payload",
    "process_request",
    "transform_payload",
)

app = FastAPI(title="SOMA Compression Service", version="0.3.0")


class TransformRequest(BaseModel):
    path: str = "/"
    query: str = ""
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class TransformResponse(BaseModel):
    payload: dict[str, Any]


def _coerce_bool(raw_value: Any, *, default: bool = False) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        value = raw_value.strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        if value in {"0", "false", "no", "off"}:
            return False
    return default


def _extract_messages(payload: dict[str, Any]) -> list[Any]:
    messages = payload.get("messages")
    if isinstance(messages, list):
        return messages
    return []


def _emit_message_event(*, request_id: str, stage: str, path: str, query: str, payload: dict[str, Any]) -> None:
    marker = f"[compression-service][messages.{stage}]"
    entry = {
        "request_id": request_id,
        "path": path,
        "query": query,
        "model": payload.get("model"),
        "messages": _extract_messages(payload),
    }
    print(f"{marker} {json.dumps(entry, ensure_ascii=False)}", flush=True)


def _load_compressor_module() -> ModuleType | None:
    module_path_raw = os.getenv("MINER_MODULE_PATH", "").strip()
    if not module_path_raw:
        return None
    module_path = Path(module_path_raw).expanduser().resolve()
    if not module_path.is_file():
        return None

    spec = importlib.util.spec_from_file_location("soma_compressor_miner", str(module_path))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    # Ensure decorators/type resolution that rely on sys.modules can find the module during import.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module

def _resolve_compressor_callable(module: ModuleType | None) -> Callable[..., Any] | None:
    if module is None:
        return None
    for name in COMPRESSOR_CANDIDATE_NAMES:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate
    return None


_COMPRESSOR_MODULE = _load_compressor_module()
_COMPRESSOR_FN = _resolve_compressor_callable(_COMPRESSOR_MODULE)


def _invoke_compressor(payload: dict[str, Any], *, path: str) -> dict[str, Any]:
    if _COMPRESSOR_FN is None:
        return payload

    mutate = _coerce_bool(os.getenv("COMPRESSION_MUTATE_REQUEST", "true"), default=True)
    input_messages = _extract_messages(payload)
    try:
        signature = inspect.signature(_COMPRESSOR_FN)
    except (TypeError, ValueError):
        signature = None

    kwargs: dict[str, Any] = {}
    if signature is not None:
        parameters = signature.parameters
        if "messages" in parameters:
            kwargs["messages"] = input_messages
        if "path" in parameters:
            kwargs["path"] = path
        if "metadata" in parameters:
            kwargs["metadata"] = {"path": path}

    result: Any
    if kwargs:
        result = _COMPRESSOR_FN(**kwargs)
    else:
        result = _COMPRESSOR_FN(input_messages)

    if mutate:
        if isinstance(result, list):
            mutated_payload = dict(payload)
            mutated_payload["messages"] = result
            return mutated_payload
        if isinstance(result, dict):
            if isinstance(result.get("messages"), list):
                mutated_payload = dict(payload)
                mutated_payload["messages"] = result["messages"]
                return mutated_payload
            return result
    return payload


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "compressor_loaded": _COMPRESSOR_FN is not None,
            "mutate_enabled": _coerce_bool(os.getenv("COMPRESSION_MUTATE_REQUEST", "true"), default=True),
            "mode": "transform-only",
        }
    )


@app.post("/transform", response_model=TransformResponse)
def transform_payload(request: TransformRequest) -> TransformResponse:
    if not isinstance(request.payload, dict):
        raise HTTPException(status_code=400, detail="payload must be an object")

    request_id = (request.request_id or "").strip() or "no-request-id"
    _emit_message_event(
        request_id=request_id,
        stage="in",
        path=request.path,
        query=request.query,
        payload=request.payload,
    )

    try:
        transformed = _invoke_compressor(request.payload, path=request.path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"compressor error: {exc}") from exc

    if not isinstance(transformed, dict):
        raise HTTPException(status_code=500, detail="compressor returned unsupported payload type")

    _emit_message_event(
        request_id=request_id,
        stage="out",
        path=request.path,
        query=request.query,
        payload=transformed,
    )
    return TransformResponse(payload=transformed)
from __future__ import annotations

import asyncio
import gzip
import json
import os
import uuid
import zlib
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 120.0
DEFAULT_COMPRESSION_TIMEOUT_SECONDS = 30.0
DEFAULT_COMPRESSION_BASE_URL = "http://compression-service:8000/"
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

app = FastAPI(title="SOMA Copilot Custom Proxy", version="0.1.0")

_token_lock = asyncio.Lock()
_token_totals: dict[str, int] = {
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read_tokens": 0,
    "cache_creation_tokens": 0,
}

TOKEN_USAGE_LOG_MARKER = "[proxy][token-usage] "


def _decompress_for_parsing(body: bytes, content_encoding: str) -> bytes:
    """Best-effort decompression of `body` for local usage-extraction only.

    Standalone runs talk to the upstream LLM directly (no gateway in between to
    absorb `Content-Encoding` the way `SOMA/gateway`'s httpx client does), so a
    compressed response body reaches us as-is. Never raises — a decode failure
    falls back to the original bytes, which downstream json.loads() rejects the
    same way it already does for any other unparseable payload.
    """
    encoding = (content_encoding or "").strip().lower()
    try:
        if encoding == "gzip" or encoding == "x-gzip":
            return gzip.decompress(body)
        if encoding == "deflate":
            try:
                return zlib.decompress(body)
            except zlib.error:
                # Some servers send raw deflate without the zlib header.
                return zlib.decompress(body, -zlib.MAX_WBITS)
    except Exception:
        return body
    return body


def _extract_usage_from_response(response_body: bytes, content_encoding: str = "") -> dict | None:
    decoded_body = _decompress_for_parsing(response_body, content_encoding)
    try:
        data = json.loads(decoded_body)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return None
    return usage


async def _accumulate_token_usage(usage: dict) -> None:
    prompt_details = usage.get("prompt_tokens_details")
    if not isinstance(prompt_details, dict):
        prompt_details = {}

    # Anthropic format: input_tokens = non-cached only, cache_read_input_tokens = cached
    # OpenAI/Qwen format: prompt_tokens = total (includes cached), cached_tokens = subset
    # Normalize to Anthropic semantics so total = input + cached + output (no double-count)
    if "input_tokens" in usage:
        raw_input = usage["input_tokens"]
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_write = usage.get("cache_creation_input_tokens", 0)
    else:
        raw_prompt = usage.get("prompt_tokens") or 0
        cache_read = prompt_details.get("cached_tokens") or 0
        cache_write = prompt_details.get("cache_write_tokens") or 0
        raw_input = raw_prompt - cache_read  # non-cached portion only

    async with _token_lock:
        _token_totals["input_tokens"] += max(raw_input, 0)
        _token_totals["output_tokens"] += (
            usage.get("output_tokens") or usage.get("completion_tokens") or 0
        )
        _token_totals["cache_read_tokens"] += cache_read
        _token_totals["cache_creation_tokens"] += cache_write
        snapshot = dict(_token_totals)
    print(f"{TOKEN_USAGE_LOG_MARKER}{json.dumps(snapshot)}", flush=True)


def _coerce_bool(raw_value: Any, *, default: bool = False) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        value = raw_value.strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        if value in {"0", "false", "no", "off"}:
            return False
    return default


def _normalize_base_url(raw_url: str, *, error_label: str) -> str:
    parsed = urlsplit(raw_url)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(f"{error_label} must be absolute http(s). Received: {raw_url!r}")
    path = parsed.path or "/"
    if not path.endswith("/"):
        path = f"{path}/"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _resolve_upstream_base_url() -> str:
    for env_name in (
        "PROXY_UPSTREAM_BASE_URL",
        "COMPACT_BENCH_LLM_BASE_URL",
    ):
        candidate = os.getenv(env_name, "").strip()
        if candidate:
            return _normalize_base_url(candidate, error_label=env_name)
    raise RuntimeError("Proxy upstream base URL is not configured. Set PROXY_UPSTREAM_BASE_URL.")


# Resolve upstream URL once at module load — never changes at runtime. Defined AFTER
# the resolver so the module-level call is not a forward reference (was a NameError).
_UPSTREAM_BASE_URL: str = _resolve_upstream_base_url()
_UPSTREAM_NETLOC: str = urlsplit(_UPSTREAM_BASE_URL).netloc


def _resolve_compression_base_url() -> str:
    candidate = os.getenv("PROXY_COMPRESSION_BASE_URL", DEFAULT_COMPRESSION_BASE_URL).strip() or DEFAULT_COMPRESSION_BASE_URL
    return _normalize_base_url(candidate, error_label="PROXY_COMPRESSION_BASE_URL")


def _resolve_compression_route_map() -> dict[str, str]:
    raw = os.getenv("PROXY_COMPRESSION_ROUTE_MAP", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("PROXY_COMPRESSION_ROUTE_MAP must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("PROXY_COMPRESSION_ROUTE_MAP must be a JSON object of run_id to base URL")

    normalized: dict[str, str] = {}
    for key, value in parsed.items():
        run_id = str(key).strip()
        if not run_id:
            continue
        if not isinstance(value, str) or not value.strip():
            continue
        normalized[run_id] = _normalize_base_url(value.strip(), error_label=f"PROXY_COMPRESSION_ROUTE_MAP[{run_id}]")
    return normalized


def _resolve_compression_base_url_template() -> str:
    return os.getenv("PROXY_COMPRESSION_BASE_URL_TEMPLATE", "").strip()


def _resolve_timeout_seconds(env_name: str, default: float) -> float:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _resolve_upstream_timeout_seconds() -> float:
    return _resolve_timeout_seconds("PROXY_UPSTREAM_TIMEOUT_SECONDS", DEFAULT_UPSTREAM_TIMEOUT_SECONDS)


def _resolve_compression_timeout_seconds() -> float:
    return _resolve_timeout_seconds("PROXY_COMPRESSION_TIMEOUT_SECONDS", DEFAULT_COMPRESSION_TIMEOUT_SECONDS)


def _resolve_provider_api_key_override() -> str:
    return os.getenv("PROXY_PROVIDER_API_KEY", "").strip()


def _extract_run_id_from_bearer_token(token: str) -> str:
    normalized = token.strip()
    if normalized.lower().startswith("bearer "):
        normalized = normalized[7:].strip()
    return normalized


def _resolve_run_id_for_routing(request: Request, *, override_api_key: str) -> str:
    raw_auth = request.headers.get("authorization", "")
    if isinstance(raw_auth, str) and raw_auth.strip():
        return _extract_run_id_from_bearer_token(raw_auth)
    if override_api_key:
        return _extract_run_id_from_bearer_token(override_api_key)
    return ""


def _resolve_compression_base_url_for_run(*, run_id: str) -> str:
    route_map = _resolve_compression_route_map()
    if run_id and run_id in route_map:
        return route_map[run_id]

    template = _resolve_compression_base_url_template()
    if run_id and template:
        candidate = template.replace("{run_id}", run_id)
        return _normalize_base_url(candidate, error_label="PROXY_COMPRESSION_BASE_URL_TEMPLATE")

    return _resolve_compression_base_url()


def _resolve_run_id_header_value() -> str:
    return os.getenv("PROXY_RUN_ID_HEADER_VALUE", "").strip()


def _resolve_compression_enabled() -> bool:
    return _coerce_bool(os.getenv("PROXY_COMPRESSION_ENABLED", "true"), default=True)


def _build_upstream_url(*, base_url: str, path: str, query: str) -> str:
    base = urlsplit(base_url)
    base_path = base.path if base.path else "/"
    if not base_path.endswith("/"):
        base_path = f"{base_path}/"
    normalized_path = path.lstrip("/")
    full_path = f"{base_path}{normalized_path}" if normalized_path else base_path
    return urlunsplit((base.scheme, base.netloc, full_path, query, ""))


def _forwardable_headers(request: Request) -> dict[str, str]:
    payload: dict[str, str] = {}
    for key, value in request.headers.items():
        if key.lower() in HOP_BY_HOP_HEADERS:
            continue
        payload[key] = value
    return payload

codex
The candidate’s core behavior is small enough to audit directly. Next I’m pulling numbered references and probing edge cases the harness does not cover, especially dedupe stability, emitted strings, and “few giant lines” compression.
exec
/bin/zsh -lc "nl -ba miner/cot_compression/upload_miner_lean_v1.py | sed -n '1,260p'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
     1	"""SOMA comp-110 (CoT-Compression-5) candidate: LEAN v1 — endurance-first extractive compressor.
     2	
     3	Contract (verified against SOMA-benchmark src/compression_service/app/main.py + proxy.py):
     4	the compression sidecar imports this file as a module (mounted at /app/miner/base_miner.py) and
     5	calls `compress_messages(messages, path, metadata) -> list` on EVERY outgoing LLM request with the
     6	OpenAI-style chat `messages` array; the returned list replaces `payload["messages"]`.
     7	`metadata` is currently just {"path": path} — no task/mode info (verified 2026-07-07).
     8	
     9	Design (evidence: reports/comp108_cap32pin_postmortem.md + reports/comp110_hard_strategy.md):
    10	- ENDURANCE-FIRST: lean per-step context -> agent survives more steps -> flip consistency +
    11	  explore savings. Depth target ~2.5x (the comp-108 M-winner's proven-compliant zone).
    12	- TIERED CAP (ported from cap32): small content passes through; mid content is line-extracted to a
    13	  budget; huge content (>53k chars, the proven boundary) gets head+signal+tail to a larger budget.
    14	- QUALITY FLOOR: lines carrying file paths / line numbers / errors / tracebacks / failing tests /
    15	  diff markers / imports / def-class signatures are ALWAYS kept (explore quality = hit-rate minus
    16	  noise-rate; swebench edit correctness needs locations).
    17	- CACHE-STABLE: rules depend only on message content (never on position/age/time), so a growing
    18	  history re-compresses its shared prefix byte-identically -> stable prompt-cache prefix
    19	  (weighted tokens: cached input costs 1/3).
    20	- BREAK-AVERSE: whole pass is fail-open (any internal error returns the ORIGINAL messages);
    21	  system/developer messages, tool_calls, non-text parts, and message order/count/roles are never
    22	  touched; markers wrap EXTRACTED ORIGINAL LINES only (never descriptions/counts — the 5Fjms DQ).
    23	- DETERMINISTIC: pure function of (messages, profile); no randomness, no clock, no network, stdlib only.
    24	- PIN (comp-108 _STRUCT_PATTERN import-pinning) is NOT ported by default — Codex-verified
    25	  net-negative. An isolated experiment flag exists (SOMA_LEAN_PIN=1) for local A/B ONLY.
    26	
    27	Profiles (env SOMA_LEAN_PROFILE = conservative | target | aggressive; default target):
    28	  budgets are CHARACTER budgets per message-content block (chars ~= 4x tokens).
    29	
    30	Compliance: emits ONLY README_prompting.md §5.1 allowed strings: [[CMP]] / [[/CMP]] /
    31	[[BLOCK X]] / [[/BLOCK X]] / "Same response as in [[BLOCK X]]." — wrapping original content.
    32	No prompt semantics changed, no instructions added/removed/reordered, no loop injection.
    33	"""
    34	from __future__ import annotations
    35	
    36	import hashlib
    37	import os
    38	import re
    39	from typing import Any
    40	
    41	# ---------------------------------------------------------------------------
    42	# profiles / knobs
    43	# ---------------------------------------------------------------------------
    44	
    45	_PROFILES = {
    46	    #                 min_compress  mid_budget  huge_threshold  huge_budget
    47	    "conservative": (9_000,        16_000,     53_000,         30_000),
    48	    "target":       (6_000,        10_000,     53_000,         18_000),
    49	    "aggressive":   (4_000,         6_000,     53_000,         10_000),
    50	}
    51	_PROFILE = os.getenv("SOMA_LEAN_PROFILE", "target").strip().lower()
    52	if _PROFILE not in _PROFILES:
    53	    _PROFILE = "target"
    54	MIN_COMPRESS, MID_BUDGET, HUGE_THRESHOLD, HUGE_BUDGET = _PROFILES[_PROFILE]
    55	
    56	# EXPERIMENT ONLY (off by default; Codex-verified net-negative in comp-108 — do not enable for upload)
    57	_PIN_ENABLED = os.getenv("SOMA_LEAN_PIN", "0").strip() == "1"
    58	
    59	_HEAD_LINES = 25          # always keep the first N lines of a compressed block
    60	_TAIL_LINES = 15          # and the last N lines
    61	_DEDUPE_MIN = 2_000       # blocks >= this size are eligible for [[BLOCK X]] dedupe
    62	
    63	CMP_START = "[[CMP]]"
    64	CMP_END = "[[/CMP]]"
    65	
    66	# ---------------------------------------------------------------------------
    67	# signal lines that must SURVIVE compression (the quality floor)
    68	# ---------------------------------------------------------------------------
    69	
    70	_KEEP_RX = re.compile(
    71	    r"""(?x)
    72	      (?: \bFile\s+"[^"]+",\s+line\s+\d+ )        # python traceback frames
    73	    | (?: \b(?:Traceback|Error|Exception|error\[|E\s{3}|FAILED|PASSED|ERROR|WARNING|assert(?:ion)?\b) )
    74	    | (?: \btests?[_/][\w./-]+ | \btest_\w+ )      # test files / test names
    75	    | (?: ^[+\-@]{1,3}(?:\s|$) | ^diff\s|^index\s|^---\s|^\+\+\+\s )   # diff/patch markers
    76	    | (?: ^\s*(?:def|class)\s+\w+ )                # signatures
    77	    | (?: ^\s*(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*]+$ )   # imports (kept: 1-line cost, location signal)
    78	    | (?: [\w\-./]+\.(?:py|c|h|cpp|js|ts|tsx|json|yaml|yml|toml|cfg|ini|txt|rst|md|html|css|xml)\b )  # file paths
    79	    | (?: \bline\s+\d+\b | :\d+:\d* )              # line-number references
    80	    """,
    81	    re.M,
    82	)
    83	
    84	_PIN_RX = re.compile(r"^\s*(?:@\w+|raise\b|except\b)", re.M)   # the comp-108 pin extras (experiment only)
    85	
    86	
    87	def _is_signal(line: str) -> bool:
    88	    if _KEEP_RX.search(line):
    89	        return True
    90	    if _PIN_ENABLED and _PIN_RX.search(line):
    91	        return True
    92	    return False
    93	
    94	
    95	# ---------------------------------------------------------------------------
    96	# core block compressor (pure; content -> content)
    97	# ---------------------------------------------------------------------------
    98	
    99	_MAX_LINE = 2_000         # deterministic per-line cap inside an extraction (bounds head/tail cost)
   100	
   101	
   102	def _compress_text(text: str, budget: int) -> str:
   103	    """Extractive head + signal-lines + tail within a char budget. Deterministic.
   104	    The KEPT EXTRACTION (original lines, a subset of the source) is wrapped in [[CMP]]/[[/CMP]] —
   105	    the comp-108 champion's verified-compliant pattern (never descriptions/counts inside markers)."""
   106	    if len(text) <= budget:
   107	        return text
   108	    lines = [l if len(l) <= _MAX_LINE else l[:_MAX_LINE] for l in text.splitlines()]
   109	    n = len(lines)
   110	    if n <= _HEAD_LINES + _TAIL_LINES + 2:
   111	        # few giant lines: hard head/tail slice of the raw text
   112	        keep = max(budget // 2, 256)
   113	        extraction = text[:keep] + "\n" + text[-keep:]
   114	        return CMP_START + "\n" + extraction + "\n" + CMP_END
   115	
   116	    keep_flags = [False] * n
   117	    for i in range(min(_HEAD_LINES, n)):
   118	        keep_flags[i] = True
   119	    for i in range(max(n - _TAIL_LINES, 0), n):
   120	        keep_flags[i] = True
   121	
   122	    used = sum(len(lines[i]) + 1 for i in range(n) if keep_flags[i])
   123	    # pass 1: signal lines (the quality floor), in document order
   124	    for i in range(n):
   125	        if keep_flags[i] or not _is_signal(lines[i]):
   126	            continue
   127	        cost = len(lines[i]) + 1
   128	        if used + cost > budget:
   129	            continue
   130	        keep_flags[i] = True
   131	        used += cost
   132	    # pass 2: fill remaining budget in document order (deterministic, locally coherent)
   133	    for i in range(n):
   134	        if keep_flags[i]:
   135	            continue
   136	        cost = len(lines[i]) + 1
   137	        if used + cost > budget:
   138	            continue
   139	        keep_flags[i] = True
   140	        used += cost
   141	
   142	    extraction = "\n".join(lines[i] for i in range(n) if keep_flags[i])
   143	    return CMP_START + "\n" + extraction + "\n" + CMP_END
   144	
   145	
   146	# ---------------------------------------------------------------------------
   147	# message-array pass
   148	# ---------------------------------------------------------------------------
   149	
   150	def _budget_for(size: int) -> int | None:
   151	    """Tiered cap: None = passthrough."""
   152	    if size <= MIN_COMPRESS:
   153	        return None
   154	    if size <= HUGE_THRESHOLD:
   155	        return MID_BUDGET
   156	    return HUGE_BUDGET
   157	
   158	
   159	def _compressible(msg: dict) -> bool:
   160	    role = msg.get("role")
   161	    if role in ("system", "developer"):
   162	        return False                        # never touch instructions
   163	    if role == "assistant" and msg.get("tool_calls"):
   164	        return False                        # never risk tool-call JSON
   165	    return role in ("tool", "user", "assistant")
   166	
   167	
   168	def _content_hash(text: str) -> str:
   169	    return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()
   170	
   171	
   172	def compress_messages(
   173	    messages: list[Any] | None = None,
   174	    path: str | None = None,
   175	    metadata: dict[str, Any] | None = None,
   176	) -> list[Any]:
   177	    del path, metadata                       # currently only {"path": ...}; unused (compliance-safe)
   178	    if not isinstance(messages, list):
   179	        return messages if isinstance(messages, list) else []
   180	    try:
   181	        return _pass(messages)
   182	    except Exception:
   183	        return messages                      # fail-open: NEVER break the run
   184	
   185	
   186	def _pass(messages: list[Any]) -> list[Any]:
   187	    seen_blocks: dict[str, int] = {}        # content-hash -> block number (first occurrence order)
   188	    out: list[Any] = []
   189	    for msg in messages:
   190	        if not isinstance(msg, dict) or not _compressible(msg):
   191	            out.append(msg)
   192	            continue
   193	        content = msg.get("content")
   194	
   195	        if isinstance(content, str):
   196	            new_content = _transform_text(content, seen_blocks)
   197	            if new_content is not content:
   198	                msg = dict(msg)
   199	                msg["content"] = new_content
   200	            out.append(msg)
   201	        elif isinstance(content, list):
   202	            new_parts, changed = [], False
   203	            for part in content:
   204	                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
   205	                    new_text = _transform_text(part["text"], seen_blocks)
   206	                    if new_text is not part["text"]:
   207	                        part = dict(part)
   208	                        part["text"] = new_text
   209	                        changed = True
   210	                new_parts.append(part)
   211	            if changed:
   212	                msg = dict(msg)
   213	                msg["content"] = new_parts
   214	            out.append(msg)
   215	        else:
   216	            out.append(msg)                  # None / unknown shape: untouched
   217	    return out
   218	
   219	
   220	def _transform_text(text: str, seen_blocks: dict[str, int]) -> str:
   221	    size = len(text)
   222	    # dedupe first: an identical large block already emitted earlier in THIS history
   223	    if size >= _DEDUPE_MIN:
   224	        h = _content_hash(text)
   225	        if h in seen_blocks:
   226	            return f"Same response as in [[BLOCK {seen_blocks[h]}]]."
   227	        budget = _budget_for(size)
   228	        if budget is None:
   229	            seen_blocks[h] = len(seen_blocks) + 1
   230	            n = seen_blocks[h]
   231	            return f"[[BLOCK {n}]]\n{text}\n[[/BLOCK {n}]]"
   232	        compressed = _compress_text(text, budget)
   233	        seen_blocks[h] = len(seen_blocks) + 1
   234	        n = seen_blocks[h]
   235	        return f"[[BLOCK {n}]]\n{compressed}\n[[/BLOCK {n}]]"
   236	    budget = _budget_for(size)
   237	    if budget is None:
   238	        return text
   239	    return _compress_text(text, budget)

exec
/bin/zsh -lc "nl -ba experiments/candidates/LEAN_comp110_v1/test_lean_miner.py | sed -n '1,260p'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Standalone verification harness for upload_miner_lean_v1 (comp-110 candidate). Stdlib only.
     3	
     4	Run:  python3 experiments/candidates/LEAN_comp110_v1/test_lean_miner.py
     5	      SOMA_LEAN_PROFILE=aggressive python3 ...   (profile A/B)
     6	Checks: import/contract, structural safety, quality floor, ratio zone, small-msg passthrough,
     7	determinism, parts/tool_calls/None handling, dedupe, growing-history prefix stability, marker set.
     8	"""
     9	from __future__ import annotations
    10	import copy
    11	import importlib.util
    12	import json
    13	import re
    14	import sys
    15	from pathlib import Path
    16	
    17	ROOT = Path(__file__).resolve().parents[3]
    18	MINER = ROOT / "miner" / "cot_compression" / "upload_miner_lean_v1.py"
    19	
    20	spec = importlib.util.spec_from_file_location("lean_v1", MINER)
    21	mod = importlib.util.module_from_spec(spec)
    22	sys.modules["lean_v1"] = mod
    23	spec.loader.exec_module(mod)
    24	compress_messages = mod.compress_messages
    25	
    26	FAIL = 0
    27	
    28	
    29	def check(name, cond, detail=""):
    30	    global FAIL
    31	    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
    32	    if not cond:
    33	        FAIL += 1
    34	
    35	
    36	def make_log(n_lines=1200, seed_word="chatter"):
    37	    lines = []
    38	    for i in range(n_lines):
    39	        if i % 97 == 0:
    40	            lines.append(f'  File "/testbed/django/db/models/query.py", line {100+i}, in _fetch_all')
    41	        elif i % 89 == 0:
    42	            lines.append(f"FAILED tests/queries/test_qs_combinators.py::test_union_{i} - AssertionError")
    43	        elif i % 83 == 0:
    44	            lines.append(f"import module_{i}.submodule")
    45	        else:
    46	            lines.append(f"{seed_word} {i} " + "x" * 120)
    47	    return "\n".join(lines)
    48	
    49	
    50	def total_chars(msgs):
    51	    tot = 0
    52	    for m in msgs:
    53	        c = m.get("content")
    54	        if isinstance(c, str):
    55	            tot += len(c)
    56	        elif isinstance(c, list):
    57	            tot += sum(len(p.get("text", "")) for p in c if isinstance(p, dict))
    58	    return tot
    59	
    60	
    61	print(f"profile = {mod._PROFILE}  budgets: min={mod.MIN_COMPRESS} mid={mod.MID_BUDGET} "
    62	      f"huge_thr={mod.HUGE_THRESHOLD} huge={mod.HUGE_BUDGET}  pin={mod._PIN_ENABLED}")
    63	
    64	# --- 1. contract ---
    65	print("\n[1] contract")
    66	out = compress_messages([], "/", {})
    67	check("empty list -> list", out == [])
    68	check("None -> []", compress_messages(None) == [])
    69	check("kwargs signature (messages/path/metadata)", True)
    70	
    71	# --- 2/3/4. realistic conversation ---
    72	print("\n[2] structure, quality floor, ratio")
    73	big_log = make_log(1200)                            # ~150k chars -> HUGE tier
    74	mid_log = make_log(250, "info")                     # ~32k chars  -> MID tier
    75	convo = [
    76	    {"role": "system", "content": "You are Copilot CLI. Follow the task instructions exactly."},
    77	    {"role": "user", "content": "Fix the failing test in django/db/models/query.py."},
    78	    {"role": "assistant", "content": None,
    79	     "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{\"cmd\": \"pytest -x\"}"}}]},
    80	    {"role": "tool", "tool_call_id": "c1", "content": big_log},
    81	    {"role": "assistant", "content": "The failure is in _fetch_all; reading the file."},
    82	    {"role": "tool", "tool_call_id": "c2", "content": mid_log},
    83	    {"role": "user", "content": [{"type": "text", "text": make_log(400, "partstext")},
    84	                                  {"type": "image_url", "image_url": {"url": "data:x"}}]},
    85	    {"role": "user", "content": "short trailing question?"},
    86	]
    87	orig = copy.deepcopy(convo)
    88	out = compress_messages(copy.deepcopy(convo), "/v1/chat/completions", {"path": "/"})
    89	
    90	check("returns list, same length", isinstance(out, list) and len(out) == len(convo))
    91	check("roles preserved in order", [m.get("role") for m in out] == [m.get("role") for m in convo])
    92	check("system untouched", out[0] == convo[0])
    93	check("tool_calls message untouched", out[2] == convo[2])
    94	check("None content untouched", out[2].get("content") is None)
    95	check("non-text part untouched", out[6]["content"][1] == convo[6]["content"][1])
    96	check("tool_call_id preserved", out[3].get("tool_call_id") == "c1")
    97	check("short trailing message byte-identical", out[7]["content"] == convo[7]["content"])
    98	check("input not mutated", convo == orig)
    99	check("JSON-serializable", bool(json.dumps(out)))
   100	
   101	big_out = out[3]["content"]
   102	check("traceback frame survives", 'File "/testbed/django/db/models/query.py", line' in big_out)
   103	check("FAILED test line survives", "FAILED tests/queries/test_qs_combinators.py" in big_out)
   104	check("import line survives", re.search(r"^import module_\d+", big_out, re.M) is not None)
   105	check("markers are exact allowed strings", "[[CMP]]" in big_out and "[[/CMP]]" in big_out)
   106	bad_marker = re.search(r"\[\[(?!CMP\]\]|/CMP\]\]|BLOCK \d+\]\]|/BLOCK \d+\]\])", big_out)
   107	check("no disallowed marker variants", bad_marker is None)
   108	check("no descriptive text inside empty markers (chars omitted etc.)",
   109	      "omitted" not in big_out and "truncated" not in big_out and "elided" not in big_out)
   110	
   111	r_all = total_chars(orig) / max(total_chars(out), 1)
   112	r_big = len(orig[3]["content"]) / max(len(big_out), 1)
   113	# Budgets are the offline-calibratable contract; the ~2.5x RUN-LEVEL token zone can only be
   114	# measured in real eval (task tokens_without/tokens_with), so here: tier budgets + deep-enough.
   115	check("huge block lands at its budget", len(big_out) <= mod.HUGE_BUDGET * 1.2, f"{len(big_out)} <= {mod.HUGE_BUDGET}*1.2")
   116	check("mid block lands at its budget", len(out[5]["content"]) <= mod.MID_BUDGET * 1.2)
   117	check("bulk-heavy convo compresses deep (>=2x)", r_all >= 2.0, f"overall {r_all:.2f}x")
   118	print(f"      ratios (bulk-heavy synthetic): overall {r_all:.2f}x | huge-block {r_big:.2f}x | mid-block "
   119	      f"{len(orig[5]['content'])/max(len(out[5]['content']),1):.2f}x")
   120	
   121	# realistic mix: mostly small turns + one huge read + one mid log -> expect ~2-4x
   122	mix = [{"role": "system", "content": "You are Copilot CLI."}]
   123	for i in range(14):
   124	    mix.append({"role": "assistant", "content": f"step {i}: inspecting the code region near the failure." + " detail" * 40})
   125	    mix.append({"role": "tool", "tool_call_id": f"t{i}", "content": f"$ cmd-{i} ok\n" + ("out " * 300)})  # ~1.2k, passthrough
   126	mix.append({"role": "tool", "tool_call_id": "big", "content": make_log(1200, "filedump")})
   127	mix.append({"role": "tool", "tool_call_id": "mid", "content": make_log(250, "pytestlog")})
   128	mix_out = compress_messages(copy.deepcopy(mix))
   129	r_mix = total_chars(mix) / max(total_chars(mix_out), 1)
   130	zone = {"conservative": (1.5, 4.0), "target": (2.0, 4.8), "aggressive": (3.5, 8.0)}[mod._PROFILE]
   131	check(f"realistic-mix ratio in profile zone {zone}", zone[0] <= r_mix <= zone[1], f"mix {r_mix:.2f}x")
   132	
   133	# --- 5. determinism ---
   134	print("\n[3] determinism")
   135	out2 = compress_messages(copy.deepcopy(convo), "/v1/chat/completions", {"path": "/"})
   136	check("same input -> byte-identical output", json.dumps(out) == json.dumps(out2))
   137	
   138	# --- 6. dedupe ---
   139	print("\n[4] dedupe")
   140	dup = make_log(300, "dupread")
   141	msgs = [{"role": "user", "content": "read it"},
   142	        {"role": "tool", "tool_call_id": "a", "content": dup},
   143	        {"role": "assistant", "content": "again"},
   144	        {"role": "tool", "tool_call_id": "b", "content": dup}]
   145	dout = compress_messages(copy.deepcopy(msgs))
   146	check("first occurrence carries [[BLOCK n]]", re.search(r"\[\[BLOCK \d+\]\]", dout[1]["content"] or "") is not None)
   147	check("repeat replaced by Same-response reference",
   148	      re.fullmatch(r"Same response as in \[\[BLOCK \d+\]\]\.", dout[3]["content"] or "") is not None)
   149	
   150	# --- 7. growing-history prefix stability (cache-safety proxy) ---
   151	print("\n[5] prefix stability")
   152	hist1 = copy.deepcopy(convo[:5])
   153	hist2 = copy.deepcopy(convo)                 # same first 5 + 3 more
   154	o1 = compress_messages(copy.deepcopy(hist1))
   155	o2 = compress_messages(copy.deepcopy(hist2))
   156	check("shared history prefix compresses byte-identically",
   157	      json.dumps(o1[:5]) == json.dumps(o2[:5]))
   158	
   159	# --- 8. hostile shapes (fail-open) ---
   160	print("\n[6] hostile shapes")
   161	weird = [{"role": "tool"}, {"content": "x"}, "not-a-dict", {"role": "tool", "content": 42},
   162	         {"role": "tool", "content": {"nested": "dict"}}]
   163	wout = compress_messages(copy.deepcopy(weird))
   164	check("hostile shapes returned unharmed", json.dumps(wout) == json.dumps(weird))
   165	
   166	print(f"\n{'ALL PASS' if FAIL == 0 else f'{FAIL} FAILURES'}")
   167	sys.exit(1 if FAIL else 0)

exec
/bin/zsh -lc "nl -ba miner/README_prompting.md | sed -n '1,180p'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
     1	# Miner Prompt Editing Rules
     2	
     3	This document defines what prompt edits are allowed in miner submissions.
     4	
     5	Goal: allow token optimizations and loop safety without changing agent behavior.
     6	
     7	## Hard Rule
     8	
     9	Only these two categories are allowed:
    10	
    11	1. Compression markers.
    12	2. Loop detection guards.
    13	
    14	Everything else is disallowed.
    15	
    16	---
    17	
    18	## 1) Compression Marker Definitions
    19	
    20	Compression markers are metadata wrappers around existing prompt content.
    21	
    22	Allowed marker behavior:
    23	
    24	- Preserve the original instruction meaning exactly.
    25	- Preserve instruction order.
    26	- Preserve all requirements.
    27	- Preserve tool policy, safety policy, role policy, and output contract.
    28	- Use clear marker boundaries such as `Compressed text starts here` and `Compressed text ends here`.
    29	- Marker aliases may be defined once and reused; `[[CMP]]` is the start marker and `[[/CMP]]` is the end marker.
    30	- `Same response as in ...` references are allowed only when the referenced block is explicit and unambiguous.
    31	
    32	Not allowed for markers:
    33	
    34	- Rewriting, weakening, strengthening, or deleting instructions.
    35	- Adding new behavior constraints.
    36	- Changing output format/schema requirements.
    37	- Ambiguous references such as `Same response as above` without a unique target.
    38	
    39	---
    40	
    41	## 2) Loop Detection Definitions
    42	
    43	Loop detection is a runtime safety guard that terminates repeated no-progress behavior.
    44	
    45	Allowed loop guard behavior:
    46	
    47	- Trigger only on objective repeated/no-progress conditions.
    48	- Keep normal successful execution behavior unchanged.
    49	- Do not alter scoring logic.
    50	- Do not alter final-output criteria.
    51	- Fail fast with a clear loop reason when a loop is detected.
    52	
    53	Not allowed for loop guards:
    54	
    55	- Prompt edits that change strategy, reasoning policy, or tool-use policy.
    56	- Prompt edits that force shortcuts to reduce token usage.
    57	- Any change that affects non-loop successful behavior.
    58	
    59	---
    60	
    61	## 3) Global Disallowed Changes
    62	
    63	The following are disallowed under this policy:
    64	
    65	- Any prompt semantic change beyond marker metadata.
    66	- Any new instruction that changes agent behavior.
    67	- Any reordering or removal of policy blocks.
    68	- Any schema/contract change for outputs.
    69	- Any safety or tool-policy change.
    70	
    71	---
    72	
    73	## 4) Submission Definition Checklist
    74	
    75	A compliant submission satisfies all of the following:
    76	
    77	1. Prompt meaning is unchanged except metadata markers.
    78	2. No instruction was added, removed, or reordered.
    79	3. Loop detection only targets repeated/no-progress cycles.
    80	4. Non-loop successful behavior is unchanged.
    81	5. Output format contract is unchanged.
    82	6. Safety and tool-use policies are unchanged.
    83	
    84	---
    85	
    86	## 5) Allowed Prompts
    87	
    88	If miners want to use any prompt format or exact string outside this list, they should discuss it first on the public channel.
    89	
    90	### 5.1 Markers
    91	
    92	Allowed exact strings:
    93	
    94	- `Compressed text starts here`
    95	- `Compressed text ends here`
    96	- `[[CMP]]`
    97	- `[[/CMP]]`
    98	- `[[BLOCK X]]`
    99	- `[[/BLOCK X]]`
   100	- `Same response as in [[BLOCK X]].`
   101	
   102	### 5.2 Loop Detection
   103	
   104	Allowed exact loop-detection reason strings:
   105	
   106	- `loop_detected: repeated assistant response`
   107	- `loop_detected: repeated tool call signature`

exec
/bin/zsh -lc "nl -ba /Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/main.py | sed -n '1,180p'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import importlib.util
     4	import inspect
     5	import json
     6	import os
     7	import sys
     8	from pathlib import Path
     9	from types import ModuleType
    10	from typing import Any, Callable
    11	from fastapi import FastAPI, HTTPException
    12	from fastapi.responses import JSONResponse
    13	from pydantic import BaseModel, Field
    14	
    15	COMPRESSOR_CANDIDATE_NAMES = (
    16	    "compress_messages",
    17	    "compress_payload",
    18	    "process_request",
    19	    "transform_payload",
    20	)
    21	
    22	app = FastAPI(title="SOMA Compression Service", version="0.3.0")
    23	
    24	
    25	class TransformRequest(BaseModel):
    26	    path: str = "/"
    27	    query: str = ""
    28	    request_id: str | None = None
    29	    payload: dict[str, Any] = Field(default_factory=dict)
    30	
    31	
    32	class TransformResponse(BaseModel):
    33	    payload: dict[str, Any]
    34	
    35	
    36	def _coerce_bool(raw_value: Any, *, default: bool = False) -> bool:
    37	    if isinstance(raw_value, bool):
    38	        return raw_value
    39	    if isinstance(raw_value, str):
    40	        value = raw_value.strip().lower()
    41	        if value in {"1", "true", "yes", "on"}:
    42	            return True
    43	        if value in {"0", "false", "no", "off"}:
    44	            return False
    45	    return default
    46	
    47	
    48	def _extract_messages(payload: dict[str, Any]) -> list[Any]:
    49	    messages = payload.get("messages")
    50	    if isinstance(messages, list):
    51	        return messages
    52	    return []
    53	
    54	
    55	def _emit_message_event(*, request_id: str, stage: str, path: str, query: str, payload: dict[str, Any]) -> None:
    56	    marker = f"[compression-service][messages.{stage}]"
    57	    entry = {
    58	        "request_id": request_id,
    59	        "path": path,
    60	        "query": query,
    61	        "model": payload.get("model"),
    62	        "messages": _extract_messages(payload),
    63	    }
    64	    print(f"{marker} {json.dumps(entry, ensure_ascii=False)}", flush=True)
    65	
    66	
    67	def _load_compressor_module() -> ModuleType | None:
    68	    module_path_raw = os.getenv("MINER_MODULE_PATH", "").strip()
    69	    if not module_path_raw:
    70	        return None
    71	    module_path = Path(module_path_raw).expanduser().resolve()
    72	    if not module_path.is_file():
    73	        return None
    74	
    75	    spec = importlib.util.spec_from_file_location("soma_compressor_miner", str(module_path))
    76	    if spec is None or spec.loader is None:
    77	        return None
    78	    module = importlib.util.module_from_spec(spec)
    79	    # Ensure decorators/type resolution that rely on sys.modules can find the module during import.
    80	    sys.modules[spec.name] = module
    81	    try:
    82	        spec.loader.exec_module(module)
    83	    except Exception:
    84	        sys.modules.pop(spec.name, None)
    85	        raise
    86	    return module
    87	
    88	def _resolve_compressor_callable(module: ModuleType | None) -> Callable[..., Any] | None:
    89	    if module is None:
    90	        return None
    91	    for name in COMPRESSOR_CANDIDATE_NAMES:
    92	        candidate = getattr(module, name, None)
    93	        if callable(candidate):
    94	            return candidate
    95	    return None
    96	
    97	
    98	_COMPRESSOR_MODULE = _load_compressor_module()
    99	_COMPRESSOR_FN = _resolve_compressor_callable(_COMPRESSOR_MODULE)
   100	
   101	
   102	def _invoke_compressor(payload: dict[str, Any], *, path: str) -> dict[str, Any]:
   103	    if _COMPRESSOR_FN is None:
   104	        return payload
   105	
   106	    mutate = _coerce_bool(os.getenv("COMPRESSION_MUTATE_REQUEST", "true"), default=True)
   107	    input_messages = _extract_messages(payload)
   108	    try:
   109	        signature = inspect.signature(_COMPRESSOR_FN)
   110	    except (TypeError, ValueError):
   111	        signature = None
   112	
   113	    kwargs: dict[str, Any] = {}
   114	    if signature is not None:
   115	        parameters = signature.parameters
   116	        if "messages" in parameters:
   117	            kwargs["messages"] = input_messages
   118	        if "path" in parameters:
   119	            kwargs["path"] = path
   120	        if "metadata" in parameters:
   121	            kwargs["metadata"] = {"path": path}
   122	
   123	    result: Any
   124	    if kwargs:
   125	        result = _COMPRESSOR_FN(**kwargs)
   126	    else:
   127	        result = _COMPRESSOR_FN(input_messages)
   128	
   129	    if mutate:
   130	        if isinstance(result, list):
   131	            mutated_payload = dict(payload)
   132	            mutated_payload["messages"] = result
   133	            return mutated_payload
   134	        if isinstance(result, dict):
   135	            if isinstance(result.get("messages"), list):
   136	                mutated_payload = dict(payload)
   137	                mutated_payload["messages"] = result["messages"]
   138	                return mutated_payload
   139	            return result
   140	    return payload
   141	
   142	
   143	@app.get("/health")
   144	def health() -> JSONResponse:
   145	    return JSONResponse(
   146	        {
   147	            "status": "ok",
   148	            "compressor_loaded": _COMPRESSOR_FN is not None,
   149	            "mutate_enabled": _coerce_bool(os.getenv("COMPRESSION_MUTATE_REQUEST", "true"), default=True),
   150	            "mode": "transform-only",
   151	        }
   152	    )
   153	
   154	
   155	@app.post("/transform", response_model=TransformResponse)
   156	def transform_payload(request: TransformRequest) -> TransformResponse:
   157	    if not isinstance(request.payload, dict):
   158	        raise HTTPException(status_code=400, detail="payload must be an object")
   159	
   160	    request_id = (request.request_id or "").strip() or "no-request-id"
   161	    _emit_message_event(
   162	        request_id=request_id,
   163	        stage="in",
   164	        path=request.path,
   165	        query=request.query,
   166	        payload=request.payload,
   167	    )
   168	
   169	    try:
   170	        transformed = _invoke_compressor(request.payload, path=request.path)
   171	    except Exception as exc:  # noqa: BLE001
   172	        raise HTTPException(status_code=500, detail=f"compressor error: {exc}") from exc
   173	
   174	    if not isinstance(transformed, dict):
   175	        raise HTTPException(status_code=500, detail="compressor returned unsupported payload type")
   176	
   177	    _emit_message_event(
   178	        request_id=request_id,
   179	        stage="out",
   180	        path=request.path,

exec
/bin/zsh -lc 'rg -n "transform|messages|payload|compression" /Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/proxy.py' in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
20:DEFAULT_COMPRESSION_BASE_URL = "http://compression-service:8000/"
48:    """Best-effort decompression of `body` for local usage-extraction only.
54:    same way it already does for any other unparseable payload.
153:def _resolve_compression_base_url() -> str:
158:def _resolve_compression_route_map() -> dict[str, str]:
180:def _resolve_compression_base_url_template() -> str:
199:def _resolve_compression_timeout_seconds() -> float:
223:def _resolve_compression_base_url_for_run(*, run_id: str) -> str:
224:    route_map = _resolve_compression_route_map()
228:    template = _resolve_compression_base_url_template()
233:    return _resolve_compression_base_url()
240:def _resolve_compression_enabled() -> bool:
255:    payload: dict[str, str] = {}
259:        payload[key] = value
260:    return payload
264:    payload: dict[str, str] = {}
268:        payload[key] = value
269:    return payload
272:def _transform_payload_via_compression_service(
276:    payload: dict[str, Any],
278:    compression_base_url: str,
280:    transform_url = _build_upstream_url(base_url=compression_base_url, path="transform", query="")
285:            "payload": payload,
290:    compression_request = UrlRequest(
291:        transform_url,
296:    with urlopen(compression_request, timeout=_resolve_compression_timeout_seconds()) as response:
299:    transformed = parsed.get("payload") if isinstance(parsed, dict) else None
300:    if not isinstance(transformed, dict):
301:        raise RuntimeError("Compression service returned invalid payload shape; expected object payload.")
302:    return transformed
311:            "compression_base_url": _resolve_compression_base_url(),
312:            "compression_enabled": _resolve_compression_enabled(),
333:    compression_base_url = _resolve_compression_base_url_for_run(run_id=run_id_for_routing)
334:    if _resolve_compression_enabled() and body and "application/json" in content_type.lower():
336:            parsed_payload = json.loads(body)
338:            parsed_payload = None
340:        if isinstance(parsed_payload, dict):
341:            transformed_payload = _transform_payload_via_compression_service(
344:                payload=parsed_payload,
346:                compression_base_url=compression_base_url,
348:            forwarded_body = json.dumps(transformed_payload, ensure_ascii=False).encode("utf-8")

codex
Two high-risk findings are emerging: this wraps uncompressed 2k-6k messages in block markers, and dedupe block numbering is prefix-stable only when no earlier duplicate is appended ahead of a previously unique shared block. I’m running concrete counterexamples now so the verdict is evidence-based.
exec
/bin/zsh -lc "nl -ba /Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/proxy.py | sed -n '260,370p'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
   260	    return payload
   261	
   262	
   263	def _response_headers_from_upstream(headers: list[tuple[str, str]]) -> dict[str, str]:
   264	    payload: dict[str, str] = {}
   265	    for key, value in headers:
   266	        if key.lower() in HOP_BY_HOP_HEADERS:
   267	            continue
   268	        payload[key] = value
   269	    return payload
   270	
   271	
   272	def _transform_payload_via_compression_service(
   273	    *,
   274	    path: str,
   275	    query: str,
   276	    payload: dict[str, Any],
   277	    request_id: str,
   278	    compression_base_url: str,
   279	) -> dict[str, Any]:
   280	    transform_url = _build_upstream_url(base_url=compression_base_url, path="transform", query="")
   281	    request_body = json.dumps(
   282	        {
   283	            "path": f"/{path}" if path else "/",
   284	            "query": query,
   285	            "payload": payload,
   286	            "request_id": request_id,
   287	        },
   288	        ensure_ascii=False,
   289	    ).encode("utf-8")
   290	    compression_request = UrlRequest(
   291	        transform_url,
   292	        data=request_body,
   293	        headers={"content-type": "application/json"},
   294	        method="POST",
   295	    )
   296	    with urlopen(compression_request, timeout=_resolve_compression_timeout_seconds()) as response:
   297	        raw = response.read()
   298	    parsed = json.loads(raw)
   299	    transformed = parsed.get("payload") if isinstance(parsed, dict) else None
   300	    if not isinstance(transformed, dict):
   301	        raise RuntimeError("Compression service returned invalid payload shape; expected object payload.")
   302	    return transformed
   303	
   304	
   305	@app.get("/health")
   306	def health() -> JSONResponse:
   307	    return JSONResponse(
   308	        {
   309	            "status": "ok",
   310	            "upstream": _UPSTREAM_BASE_URL,
   311	            "compression_base_url": _resolve_compression_base_url(),
   312	            "compression_enabled": _resolve_compression_enabled(),
   313	            "api_key_override_enabled": bool(_resolve_provider_api_key_override()),
   314	            "run_id_header_enabled": bool(_resolve_run_id_header_value()),
   315	        }
   316	    )
   317	
   318	
   319	@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
   320	async def proxy_passthrough(path: str, request: Request) -> Response:
   321	    request_id = uuid.uuid4().hex
   322	    upstream_url = _build_upstream_url(base_url=_UPSTREAM_BASE_URL, path=path, query=request.url.query)
   323	    if urlsplit(upstream_url).netloc != _UPSTREAM_NETLOC:
   324	        raise HTTPException(status_code=400, detail="Upstream host mismatch — only configured host is allowed")
   325	
   326	    method = request.method.upper()
   327	    body = await request.body()
   328	    content_type = request.headers.get("content-type", "")
   329	
   330	    forwarded_body = body
   331	    override_api_key = _resolve_provider_api_key_override()
   332	    run_id_for_routing = _resolve_run_id_for_routing(request, override_api_key=override_api_key)
   333	    compression_base_url = _resolve_compression_base_url_for_run(run_id=run_id_for_routing)
   334	    if _resolve_compression_enabled() and body and "application/json" in content_type.lower():
   335	        try:
   336	            parsed_payload = json.loads(body)
   337	        except json.JSONDecodeError:
   338	            parsed_payload = None
   339	
   340	        if isinstance(parsed_payload, dict):
   341	            transformed_payload = _transform_payload_via_compression_service(
   342	                path=path,
   343	                query=request.url.query,
   344	                payload=parsed_payload,
   345	                request_id=request_id,
   346	                compression_base_url=compression_base_url,
   347	            )
   348	            forwarded_body = json.dumps(transformed_payload, ensure_ascii=False).encode("utf-8")
   349	
   350	    forwarded_headers = _forwardable_headers(request)
   351	    run_id_header_value = _resolve_run_id_header_value()
   352	    if run_id_header_value:
   353	        forwarded_headers["X-Run-Id"] = run_id_header_value
   354	    if override_api_key:
   355	        forwarded_headers["Authorization"] = f"Bearer {override_api_key}"
   356	
   357	    upstream_request = UrlRequest(
   358	        upstream_url,
   359	        data=forwarded_body if method in {"POST", "PUT", "PATCH", "DELETE"} else None,
   360	        headers=forwarded_headers,
   361	        method=method,
   362	    )
   363	
   364	    try:
   365	        with urlopen(upstream_request, timeout=_resolve_upstream_timeout_seconds()) as upstream_response:
   366	            response_body = upstream_response.read()
   367	            response_headers = _response_headers_from_upstream(list(upstream_response.headers.items()))
   368	            content_type = upstream_response.headers.get("content-type", "")
   369	            if "application/json" in content_type:
   370	                content_encoding = upstream_response.headers.get("content-encoding", "")

exec
/bin/zsh -lc 'python3 experiments/candidates/LEAN_comp110_v1/test_lean_miner.py' in /Users/eric.xiao/joshua-work/soma
 succeeded in 319ms:
profile = target  budgets: min=6000 mid=10000 huge_thr=53000 huge=18000  pin=False

[1] contract
  PASS  empty list -> list
  PASS  None -> []
  PASS  kwargs signature (messages/path/metadata)

[2] structure, quality floor, ratio
  PASS  returns list, same length
  PASS  roles preserved in order
  PASS  system untouched
  PASS  tool_calls message untouched
  PASS  None content untouched
  PASS  non-text part untouched
  PASS  tool_call_id preserved
  PASS  short trailing message byte-identical
  PASS  input not mutated
  PASS  JSON-serializable
  PASS  traceback frame survives
  PASS  FAILED test line survives
  PASS  import line survives
  PASS  markers are exact allowed strings
  PASS  no disallowed marker variants
  PASS  no descriptive text inside empty markers (chars omitted etc.)
  PASS  huge block lands at its budget  [17940 <= 18000*1.2]
  PASS  mid block lands at its budget
  PASS  bulk-heavy convo compresses deep (>=2x)  [overall 6.34x]
      ratios (bulk-heavy synthetic): overall 6.34x | huge-block 8.73x | mid-block 3.17x
  PASS  realistic-mix ratio in profile zone (2.0, 4.8)  [mix 4.29x]

[3] determinism
  PASS  same input -> byte-identical output

[4] dedupe
  PASS  first occurrence carries [[BLOCK n]]
  PASS  repeat replaced by Same-response reference

[5] prefix stability
  PASS  shared history prefix compresses byte-identically

[6] hostile shapes
  PASS  hostile shapes returned unharmed

ALL PASS

codex
The provided harness passes, but it misses adversarial histories where a new duplicate appears before an older shared message. I also need one more local probe because the shell cannot create heredoc temp files in this read-only sandbox; I’ll use inline Python instead.
exec
/bin/zsh -lc "PYTHONDONTWRITEBYTECODE=1 python3 -c '
import copy, importlib.util, sys, time
from pathlib import Path
p=Path(\"miner/cot_compression/upload_miner_lean_v1.py\").resolve()
spec=importlib.util.spec_from_file_location(\"m\", p)
m=importlib.util.module_from_spec(spec); sys.modules[\"m\"]=m; spec.loader.exec_module(m)
def cm(msgs): return m.compress_messages(copy.deepcopy(msgs))
s=\"x\"*2000
out=cm([{\"role\":\"tool\",\"content\":s}])[0][\"content\"]
print(\"wrap_2000_len\", len(s), len(out), repr(out[:25]), repr(out[-25:]))
A=\"A\"*7000; B=\"B\"*7000
hist1=[{\"role\":\"tool\",\"content\":A},{\"role\":\"assistant\",\"content\":\"mid\"},{\"role\":\"tool\",\"content\":B}]
hist2=[{\"role\":\"tool\",\"content\":A},{\"role\":\"tool\",\"content\":A},{\"role\":\"assistant\",\"content\":\"mid\"},{\"role\":\"tool\",\"content\":B}]
o1=cm(hist1); o2=cm(hist2)
print(\"shared_first_stable\", o1[0]==o2[0])
print(\"B_stable_hist1_2_vs_hist2_3\", o1[2][\"content\"]==o2[3][\"content\"])
print(\"hist1_B_start\", repr(o1[2][\"content\"][:45]))
print(\"hist2_B_start\", repr(o2[3][\"content\"][:45]))
G=\"a\"*60000
go=cm([{\"role\":\"tool\",\"content\":G}])[0][\"content\"]
print(\"giant_one_line_in_out_budget\", len(G), len(go), \"huge_budget\", m.HUGE_BUDGET)
lines=[]
for i in range(100000): lines.append(f\"line {i} /tmp/file_{i}.py:1:2 \" + \"x\"*100)
big=\"\\n\".join(lines)
t0=time.perf_counter(); cm([{\"role\":\"tool\",\"content\":big}]); dt=(time.perf_counter()-t0)*1000
print(\"perf_chars_ms\", len(big), f\"{dt:.1f}\")
'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
python3: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
python3: error: couldn't create cache file '/tmp/xcrun_db-Tm1MjbP7' (errno=Operation not permitted)
python3: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
python3: error: couldn't create cache file '/tmp/xcrun_db-fQi08GyR' (errno=Operation not permitted)
wrap_2000_len 2000 2025 '[[BLOCK 1]]\nxxxxxxxxxxxxx' 'xxxxxxxxxxxx\n[[/BLOCK 1]]'
shared_first_stable True
B_stable_hist1_2_vs_hist2_3 True
hist1_B_start '[[BLOCK 2]]\nBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB'
hist2_B_start '[[BLOCK 2]]\nBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB'
giant_one_line_in_out_budget 60000 18043 huge_budget 18000
perf_chars_ms 13477779 64.4

exec
/bin/zsh -lc "PYTHONDONTWRITEBYTECODE=1 python3 -c '
import copy, importlib.util, sys
from pathlib import Path
p=Path(\"miner/cot_compression/upload_miner_lean_v1.py\").resolve(); spec=importlib.util.spec_from_file_location(\"m\", p); m=importlib.util.module_from_spec(spec); sys.modules[\"m\"]=m; spec.loader.exec_module(m)
lines=[f\"REQUIREMENT_{i}: preserve this exact user instruction and constraint \" + (\"x\"*80) for i in range(250)]
text=\"\\n\".join(lines)
out=m.compress_messages([{\"role\":\"user\",\"content\":text}])[0][\"content\"]
print(\"orig_len\", len(text), \"out_len\", len(out), \"has_cmp\", \"[[CMP]]\" in out)
for needle in [\"REQUIREMENT_0\", \"REQUIREMENT_50\", \"REQUIREMENT_120\", \"REQUIREMENT_249\"]:
    print(needle, needle in out)
'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
python3: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
python3: error: couldn't create cache file '/tmp/xcrun_db-2mS4futU' (errno=Operation not permitted)
python3: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
python3: error: couldn't create cache file '/tmp/xcrun_db-25cga8eN' (errno=Operation not permitted)
orig_len 37389 out_len 10029 has_cmp True
REQUIREMENT_0 True
REQUIREMENT_50 True
REQUIREMENT_120 False
REQUIREMENT_249 True

codex
| Dimension | Verdict | Evidence |
|---|---:|---|
| 1. Structural Safety | PASS | Contract invokes `compress_messages(messages, path, metadata)` and replaces `payload["messages"]` only when result is a list: [main.py:113](/Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/main.py:113), [main.py:129](/Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/main.py:129). Candidate handles non-list, non-dict, missing content, `None`, scalar/dict content, parts lists, and assistant `tool_calls`: [upload_miner_lean_v1.py:178](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:178), [upload_miner_lean_v1.py:190](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:190), [upload_miner_lean_v1.py:201](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:201). Changed messages/parts are copied before edit, so no observed in-place mutation: [upload_miner_lean_v1.py:198](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:198), [upload_miner_lean_v1.py:207](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:207). |
| 2. Compliance | BLOCKING | It compresses `user` messages: [upload_miner_lean_v1.py:165](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:165). A 37,389-char user message of numbered requirements was reduced to 10,029 chars and dropped `REQUIREMENT_120`, which is prompt semantic deletion, forbidden by [README_prompting.md:65](/Users/eric.xiao/joshua-work/soma/miner/README_prompting.md:65) and [README_prompting.md:77](/Users/eric.xiao/joshua-work/soma/miner/README_prompting.md:77). It also truncates long lines with `l[:_MAX_LINE]`, so markers can wrap partial lines, not extracted original lines: [upload_miner_lean_v1.py:108](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:108). Few-giant-lines path slices raw text mid-line/mid-JSON: [upload_miner_lean_v1.py:110](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:110). Emitted marker strings are only the allowed marker family, but the content they wrap is not always compliant. |
| 3. Determinism & Cache Stability | CONCERN | Append-only shared prefixes are byte-stable: `seen_blocks` is local per call and block numbering is first-occurrence order: [upload_miner_lean_v1.py:187](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:187), [upload_miner_lean_v1.py:229](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:229). However output is not just a function of `(messages, env profile)`: hidden `SOMA_LEAN_PIN` changes signal retention: [upload_miner_lean_v1.py:57](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:57), [upload_miner_lean_v1.py:90](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:90). |
| 4. Break Risk | BLOCKING | The pass compresses every compressible message in order, including the newest tool result the agent may need next: [upload_miner_lean_v1.py:189](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:189), [upload_miner_lean_v1.py:165](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:165). Head/tail extraction and fill can omit middle JSON/diffs/logs without schema awareness: [upload_miner_lean_v1.py:116](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:116), [upload_miner_lean_v1.py:132](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:132). Few-giant-lines raw slicing can cut mid-JSON or mid-diff hunk: [upload_miner_lean_v1.py:113](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:113). |
| 5. Performance | PASS | Complexity is linear-ish per content block: hash/encode, splitlines, then several line scans with regex checks: [upload_miner_lean_v1.py:168](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:168), [upload_miner_lean_v1.py:108](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:108), [upload_miner_lean_v1.py:124](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:124). Local sanity probe: ~13.48 MB processed in 64.4 ms, consistent with author’s ~60 ms/13.6 MB claim. |
| 6. Logic Bugs | BLOCKING | `_DEDUPE_MIN=2000` is below `MIN_COMPRESS=6000`, and dedupe runs before budget, so 2k-6k blocks are wrapped with `[[BLOCK n]]` but not compressed: [upload_miner_lean_v1.py:61](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:61), [upload_miner_lean_v1.py:223](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:223), [upload_miner_lean_v1.py:228](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:228). Probe: 2,000 chars became 2,025 chars. Also, content between `MIN_COMPRESS+1` and `MID_BUDGET` can be block-wrapped without compression because `_compress_text` returns raw text when `len(text) <= budget`: [upload_miner_lean_v1.py:106](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:106). |

**Required Fixes**
1. Do not compress `user` messages unless there is a strict, review-approved classifier proving the content is non-instructional. Safer upload fix: only compress `tool` outputs, possibly older assistant text if explicitly allowed.
2. Remove partial-line output. No `l[:_MAX_LINE]` inside emitted content, and no raw head/tail slicing that cuts mid-line. Markers should wrap whole original lines only.
3. Do not wrap uncompressed blocks. Only emit `[[BLOCK n]]...[[/BLOCK n]]` when there is a net reduction or when dedupe will actually replace a later duplicate in the same request.
4. Add recency protection: leave the newest user/tool/assistant content untouched, especially latest tool output.
5. Remove or hard-disable `SOMA_LEAN_PIN` for upload, or include it in the declared deterministic profile surface.

**Recommended Improvements**
- Add harness cases for long user instructions, long single-line JSON, long diff hunks, 2k-10k no-compression wrapping, and latest-tool-result preservation.
- Make budget checks include marker overhead.
- Prefer JSON/diff-aware preservation for structured tool outputs.

VERDICT: NO-GO. Blocking changes required: stop compressing semantic user prompts, stop emitting partial/truncated lines inside markers, avoid net-increasing block wrappers, and protect the newest actionable message.
tokens used
77,736
| Dimension | Verdict | Evidence |
|---|---:|---|
| 1. Structural Safety | PASS | Contract invokes `compress_messages(messages, path, metadata)` and replaces `payload["messages"]` only when result is a list: [main.py:113](/Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/main.py:113), [main.py:129](/Users/eric.xiao/joshua-work/SOMA-benchmark/src/compression_service/app/main.py:129). Candidate handles non-list, non-dict, missing content, `None`, scalar/dict content, parts lists, and assistant `tool_calls`: [upload_miner_lean_v1.py:178](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:178), [upload_miner_lean_v1.py:190](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:190), [upload_miner_lean_v1.py:201](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:201). Changed messages/parts are copied before edit, so no observed in-place mutation: [upload_miner_lean_v1.py:198](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:198), [upload_miner_lean_v1.py:207](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:207). |
| 2. Compliance | BLOCKING | It compresses `user` messages: [upload_miner_lean_v1.py:165](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:165). A 37,389-char user message of numbered requirements was reduced to 10,029 chars and dropped `REQUIREMENT_120`, which is prompt semantic deletion, forbidden by [README_prompting.md:65](/Users/eric.xiao/joshua-work/soma/miner/README_prompting.md:65) and [README_prompting.md:77](/Users/eric.xiao/joshua-work/soma/miner/README_prompting.md:77). It also truncates long lines with `l[:_MAX_LINE]`, so markers can wrap partial lines, not extracted original lines: [upload_miner_lean_v1.py:108](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:108). Few-giant-lines path slices raw text mid-line/mid-JSON: [upload_miner_lean_v1.py:110](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:110). Emitted marker strings are only the allowed marker family, but the content they wrap is not always compliant. |
| 3. Determinism & Cache Stability | CONCERN | Append-only shared prefixes are byte-stable: `seen_blocks` is local per call and block numbering is first-occurrence order: [upload_miner_lean_v1.py:187](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:187), [upload_miner_lean_v1.py:229](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:229). However output is not just a function of `(messages, env profile)`: hidden `SOMA_LEAN_PIN` changes signal retention: [upload_miner_lean_v1.py:57](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:57), [upload_miner_lean_v1.py:90](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:90). |
| 4. Break Risk | BLOCKING | The pass compresses every compressible message in order, including the newest tool result the agent may need next: [upload_miner_lean_v1.py:189](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:189), [upload_miner_lean_v1.py:165](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:165). Head/tail extraction and fill can omit middle JSON/diffs/logs without schema awareness: [upload_miner_lean_v1.py:116](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:116), [upload_miner_lean_v1.py:132](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:132). Few-giant-lines raw slicing can cut mid-JSON or mid-diff hunk: [upload_miner_lean_v1.py:113](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:113). |
| 5. Performance | PASS | Complexity is linear-ish per content block: hash/encode, splitlines, then several line scans with regex checks: [upload_miner_lean_v1.py:168](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:168), [upload_miner_lean_v1.py:108](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:108), [upload_miner_lean_v1.py:124](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:124). Local sanity probe: ~13.48 MB processed in 64.4 ms, consistent with author’s ~60 ms/13.6 MB claim. |
| 6. Logic Bugs | BLOCKING | `_DEDUPE_MIN=2000` is below `MIN_COMPRESS=6000`, and dedupe runs before budget, so 2k-6k blocks are wrapped with `[[BLOCK n]]` but not compressed: [upload_miner_lean_v1.py:61](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:61), [upload_miner_lean_v1.py:223](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:223), [upload_miner_lean_v1.py:228](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:228). Probe: 2,000 chars became 2,025 chars. Also, content between `MIN_COMPRESS+1` and `MID_BUDGET` can be block-wrapped without compression because `_compress_text` returns raw text when `len(text) <= budget`: [upload_miner_lean_v1.py:106](/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py:106). |

**Required Fixes**
1. Do not compress `user` messages unless there is a strict, review-approved classifier proving the content is non-instructional. Safer upload fix: only compress `tool` outputs, possibly older assistant text if explicitly allowed.
2. Remove partial-line output. No `l[:_MAX_LINE]` inside emitted content, and no raw head/tail slicing that cuts mid-line. Markers should wrap whole original lines only.
3. Do not wrap uncompressed blocks. Only emit `[[BLOCK n]]...[[/BLOCK n]]` when there is a net reduction or when dedupe will actually replace a later duplicate in the same request.
4. Add recency protection: leave the newest user/tool/assistant content untouched, especially latest tool output.
5. Remove or hard-disable `SOMA_LEAN_PIN` for upload, or include it in the declared deterministic profile surface.

**Recommended Improvements**
- Add harness cases for long user instructions, long single-line JSON, long diff hunks, 2k-10k no-compression wrapping, and latest-tool-result preservation.
- Make budget checks include marker overhead.
- Prefer JSON/diff-aware preservation for structured tool outputs.

VERDICT: NO-GO. Blocking changes required: stop compressing semantic user prompts, stop emitting partial/truncated lines inside markers, avoid net-increasing block wrappers, and protect the newest actionable message.
AUDIT EXIT=0
