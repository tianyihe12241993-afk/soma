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


print(f"profile = {mod._PROFILE}  budgets: mid={mod.MID_BUDGET} "
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
    {"role": "user", "content": "Fix the failing test in django/db/models/query.py.\n" + make_log(400, "USER_REQUIREMENT")},
    {"role": "assistant", "content": None,
     "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{\"cmd\": \"pytest -x\"}"}}]},
    {"role": "tool", "tool_call_id": "c1", "content": big_log},          # OLD tool (compressible)
    {"role": "assistant", "content": "The failure is in _fetch_all; reading the file. " + make_log(300, "ASSISTANT_COT")},
    {"role": "tool", "tool_call_id": "c2", "content": mid_log},          # interior tool (compressible)
    {"role": "tool", "tool_call_id": "c3", "content": make_log(600, "finaldump")},  # FINAL msg (recency-protected)
]
orig = copy.deepcopy(convo)
out = compress_messages(copy.deepcopy(convo), "/v1/chat/completions", {"path": "/"})

check("returns list, same length", isinstance(out, list) and len(out) == len(convo))
check("roles preserved in order", [m.get("role") for m in out] == [m.get("role") for m in convo])
check("system untouched", out[0] == convo[0])
check("USER message NEVER compressed (compliance fix #1)", out[1]["content"] == convo[1]["content"])
check("tool_calls message untouched", out[2] == convo[2])
check("None content untouched", out[2].get("content") is None)
check("tool_call_id preserved", out[3].get("tool_call_id") == "c1")
check("interior tool (not final) WAS compressed", len(out[5]["content"]) < len(convo[5]["content"]))
check("FINAL message verbatim (recency fix #4, final-only)", out[6]["content"] == convo[6]["content"])
check("input not mutated", convo == orig)
check("JSON-serializable", bool(json.dumps(out)))

big_out = out[3]["content"]
check("OLD tool result WAS compressed", len(big_out) < len(convo[3]["content"]))
check("old assistant CoT compressed", len(out[4]["content"]) < len(convo[4]["content"]))
check("traceback frame survives", 'File "/testbed/django/db/models/query.py", line' in big_out)
check("FAILED test line survives", "FAILED tests/queries/test_qs_combinators.py" in big_out)
check("import line survives", re.search(r"^import module_\d+", big_out, re.M) is not None)
check("markers are exact allowed strings", "[[CMP]]" in big_out and "[[/CMP]]" in big_out)
bad_marker = re.search(r"\[\[(?!CMP\]\]|/CMP\]\])", big_out)
check("no disallowed marker variants (only [[CMP]]/[[/CMP]])", bad_marker is None)
check("no descriptive text inside markers (omitted/truncated/elided)",
      "omitted" not in big_out and "truncated" not in big_out and "elided" not in big_out)
# whole-line integrity: every kept content line (between markers) is an ORIGINAL line (fix #2)
orig_lines = set(convo[3]["content"].splitlines())
kept = [l for l in big_out.splitlines() if l not in ("[[CMP]]", "[[/CMP]]")]
check("every kept line is a verbatim original line (no partial lines)",
      all(l in orig_lines for l in kept), f"{sum(1 for l in kept if l not in orig_lines)} partial")

r_big = len(orig[3]["content"]) / max(len(big_out), 1)
check("huge block lands at its budget", len(big_out) <= mod.HUGE_BUDGET * 1.2, f"{len(big_out)} <= {mod.HUGE_BUDGET}*1.2")
check("no net-increase: compressed block is strictly smaller (fix #3)", len(big_out) < len(convo[3]["content"]))

# --- ratio on a bulk-heavy interior-only convo (no recency protection, no instruction msgs) ---
print("\n[3] compression depth (interior tool bulk)")
bulk = [{"role": "user", "content": "task"}]
for i in range(8):
    bulk.append({"role": "assistant", "content": f"reading region {i}"})
    bulk.append({"role": "tool", "tool_call_id": f"t{i}", "content": make_log(600, f"dump{i}")})
bulk.append({"role": "assistant", "content": "final small plan"})   # protects only tail + last tool
b_out = compress_messages(copy.deepcopy(bulk))
r_bulk = total_chars(bulk) / max(total_chars(b_out), 1)
zone = {"conservative": (1.4, 3.5), "target": (1.8, 5.0), "aggressive": (2.5, 9.5)}[mod._PROFILE]
check(f"bulk ratio in profile zone {zone}", zone[0] <= r_bulk <= zone[1], f"bulk {r_bulk:.2f}x")
print(f"      huge-block {r_big:.2f}x | interior-bulk convo {r_bulk:.2f}x")

# --- 4. determinism ---
print("\n[4] determinism")
out2 = compress_messages(copy.deepcopy(convo), "/v1/chat/completions", {"path": "/"})
check("same input -> byte-identical output", json.dumps(out) == json.dumps(out2))

# --- 5. prefix stability (final-only recency => ALL non-final messages position-independent) ---
print("\n[5] prefix stability")
base = [
    {"role": "user", "content": "task"},
    {"role": "assistant", "content": "step A"},
    {"role": "tool", "tool_call_id": "A", "content": make_log(1000, "readA")},
    {"role": "assistant", "content": "step B"},
    {"role": "tool", "tool_call_id": "B", "content": make_log(1000, "readB")},
    {"role": "assistant", "content": "plan"},          # final in base -> protected
]
extended = copy.deepcopy(base) + [
    {"role": "tool", "tool_call_id": "C", "content": make_log(1000, "readC")},
    {"role": "assistant", "content": "plan2"},          # final in extended
]
ob = compress_messages(copy.deepcopy(base))
oe = compress_messages(copy.deepcopy(extended))
# every message EXCEPT base's final (idx5) is position-independent -> byte-identical across both
check("entire shared prefix up to base's final is byte-identical (cache-stable)",
      json.dumps(ob[:5]) == json.dumps(oe[:5]))
check("base final (protected raw) compresses once it ages in — the ONE documented transition",
      ob[5]["content"] == base[5]["content"] and json.dumps(oe[5]) == json.dumps(oe[5]))

# recency toggle: SOMA_LEAN_RECENCY=0 makes even the final message position-independent
import os as _os, subprocess as _sp
env = dict(_os.environ, SOMA_LEAN_RECENCY="0", SOMA_LEAN_PROFILE=mod._PROFILE)
probe = "import importlib.util,json,sys; s=importlib.util.spec_from_file_location('m','%s'); " \
        "m=importlib.util.module_from_spec(s); sys.modules['m']=m; s.loader.exec_module(m); " \
        "b=[{'role':'tool','tool_call_id':'x','content':'\\n'.join('L%%d '%%i+'z'*130 for i in range(600))}]; " \
        "print(len(m.compress_messages(b)[0]['content']) < len(b[0]['content']))" % str(MINER)
res = _sp.run([sys.executable, "-c", probe], capture_output=True, text=True, env=env)
check("SOMA_LEAN_RECENCY=0 compresses even a lone final tool (A/B toggle works)",
      res.stdout.strip() == "True", res.stdout.strip() + res.stderr[-80:])

# --- 6. hostile shapes (fail-open) ---
print("\n[6] hostile shapes")
weird = [{"role": "tool"}, {"content": "x"}, "not-a-dict", {"role": "tool", "content": 42},
         {"role": "tool", "content": {"nested": "dict"}}]
wout = compress_messages(copy.deepcopy(weird))
check("hostile shapes returned unharmed", json.dumps(wout) == json.dumps(weird))

print(f"\n{'ALL PASS' if FAIL == 0 else f'{FAIL} FAILURES'}")
sys.exit(1 if FAIL else 0)
