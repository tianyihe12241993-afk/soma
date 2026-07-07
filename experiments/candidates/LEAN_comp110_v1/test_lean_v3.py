#!/usr/bin/env python3
"""Verification harness for upload_miner_lean_v3 (comp-110, source-line omission markers). Stdlib.

Run:  python3 experiments/candidates/LEAN_comp110_v1/test_lean_v3.py
      SOMA_LEAN_PROFILE=aggressive python3 ...
Adds to the v2 checks: source-line RANGE ACCURACY (reconstruct original from kept lines + markers),
exact-template markers, kept lines verbatim, no partial lines.
"""
from __future__ import annotations
import copy, importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MINER = ROOT / "miner" / "cot_compression" / "upload_miner_lean_v3.py"
spec = importlib.util.spec_from_file_location("lean_v3", MINER)
mod = importlib.util.module_from_spec(spec); sys.modules["lean_v3"] = mod; spec.loader.exec_module(mod)
compress_messages = mod.compress_messages

FAIL = 0
def check(name, cond, detail=""):
    global FAIL
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
    if not cond: FAIL += 1

def make_log(n, w="line"):
    out = []
    for i in range(n):
        if i % 97 == 0: out.append(f'  File "/testbed/django/db/models/query.py", line {100+i}, in _fetch_all')
        elif i % 89 == 0: out.append(f"FAILED tests/queries/test_qs.py::test_union_{i} - AssertionError")
        elif i % 83 == 0: out.append(f"import module_{i}.submodule")
        else: out.append(f"{w} {i} " + "x"*120)
    return "\n".join(out)

SINGLE = re.compile(r"^\[\[CMP\]\] source line (\d+) \[\[/CMP\]\]$")
SPAN = re.compile(r"^\[\[CMP\]\] source line (\d+) ~ source line (\d+) Omitted \[\[/CMP\]\]$")

def verify_reconstruction(original: str, compressed: str):
    """Walk compressed output; kept lines must equal original lines in order, markers must name the
    EXACT contiguous omitted spans. Returns (ok, msg). This is the range-accuracy guarantee."""
    orig = original.splitlines()
    n = len(orig)
    cursor = 0  # 0-based index into orig of the next expected original line
    for line in compressed.splitlines():
        m1, m2 = SINGLE.match(line), SPAN.match(line)
        if m2:
            N, M = int(m2.group(1)), int(m2.group(2))
            if N != cursor + 1: return False, f"span start {N} != expected {cursor+1}"
            if M < N or M > n: return False, f"span end {M} out of range"
            cursor = M  # skip omitted lines N..M (1-based) => advance to index M
        elif m1:
            N = int(m1.group(1))
            if N != cursor + 1: return False, f"single {N} != expected {cursor+1}"
            cursor = N
        else:
            if cursor >= n: return False, "extra kept line past original end"
            if line != orig[cursor]: return False, f"kept line mismatch at {cursor+1}"
            cursor += 1
    if cursor != n: return False, f"reconstruction ended at {cursor}, expected {n}"
    return True, "ok"

print(f"profile={mod._PROFILE} budgets mid={mod.MID_BUDGET} huge={mod.HUGE_BUDGET} recency={mod._RECENCY} (no pin knob)")
check("pin knob removed (no pin, absolute)", not hasattr(mod, "_PIN_ENABLED"))

# 1. contract
print("\n[1] contract")
check("empty->[]", compress_messages([], "/", {}) == [])
check("None->[]", compress_messages(None) == [])

# 2. structure + roles
print("\n[2] structure / roles")
big = make_log(1200)
convo = [
    {"role":"system","content":"You are Copilot CLI."},
    {"role":"user","content":"Fix it.\n"+make_log(400,"USER_REQ")},
    {"role":"assistant","content":None,"tool_calls":[{"id":"c1","type":"function","function":{"name":"bash","arguments":"{}"}}]},
    {"role":"tool","tool_call_id":"c1","content":big},                 # interior tool -> compressed
    {"role":"assistant","content":"analysis "+make_log(300,"COT")},    # assistant CoT -> compressed
    {"role":"tool","tool_call_id":"c2","content":make_log(600,"final")},# FINAL -> recency protected
]
orig = copy.deepcopy(convo)
out = compress_messages(copy.deepcopy(convo))
check("same length + roles", [m.get("role") for m in out]==[m.get("role") for m in convo])
check("system untouched", out[0]==convo[0])
check("USER never compressed", out[1]["content"]==convo[1]["content"])
check("tool_calls msg untouched", out[2]==convo[2])
check("final msg verbatim (recency)", out[5]["content"]==convo[5]["content"])
check("input not mutated", convo==orig)
check("JSON-serializable", bool(json.dumps(out)))

big_out = out[3]["content"]
check("interior tool compressed", len(big_out) < len(convo[3]["content"]))

# 3. source-line markers: exact template + RANGE ACCURACY
print("\n[3] source-line markers")
markers = [l for l in big_out.splitlines() if l.startswith("[[")]
check("at least one omission marker emitted", len(markers) > 0, f"{len(markers)} markers")
check("every marker is an exact source-line template",
      all(SINGLE.match(m) or SPAN.match(m) for m in markers),
      next((m for m in markers if not (SINGLE.match(m) or SPAN.match(m))), ""))
ok, msg = verify_reconstruction(convo[3]["content"], big_out)
check("RANGE ACCURACY: kept lines + omitted ranges reconstruct the original exactly", ok, msg)
# no partial lines: every non-marker output line is a verbatim original line
orig_lines = set(convo[3]["content"].splitlines())
kept = [l for l in big_out.splitlines() if not l.startswith("[[")]
check("no partial lines (all kept lines verbatim originals)", all(l in orig_lines for l in kept))

# 4. quality floor
print("\n[4] quality floor")
check("traceback frame survives", 'File "/testbed/django/db/models/query.py", line' in big_out)
check("FAILED test survives", "FAILED tests/queries/test_qs.py" in big_out)
check("import survives", re.search(r"^import module_\d+", big_out, re.M) is not None)

# 5. determinism + net reduction + no bare disallowed markers
print("\n[5] determinism / net-reduction / markers")
out2 = compress_messages(copy.deepcopy(convo))
check("deterministic (byte-identical)", json.dumps(out)==json.dumps(out2))
check("net reduction (compressed < original)", len(big_out) < len(convo[3]["content"]))
bad = re.search(r"\[\[(?!CMP\]\]|/CMP\]\]|Omitted\]\]|/Omitted\]\]|deleted\]\]|/deleted\]\]|BLOCK)", big_out)
check("no disallowed marker variants", bad is None, bad.group(0) if bad else "")
check("no descriptive junk inside markers", not any(w in big_out for w in ("truncated","elided","chars")))

# 6. interior prefix stability (all non-final msgs position-independent)
print("\n[6] prefix stability")
base = [{"role":"user","content":"t"},{"role":"tool","tool_call_id":"A","content":make_log(1000,"A")},
        {"role":"assistant","content":"p"}]
ext = copy.deepcopy(base)+[{"role":"tool","tool_call_id":"B","content":make_log(1000,"B")},{"role":"assistant","content":"p2"}]
ob, oe = compress_messages(copy.deepcopy(base)), compress_messages(copy.deepcopy(ext))
check("shared prefix byte-identical as history grows", json.dumps(ob[:2])==json.dumps(oe[:2]))

# 7. few-giant-lines verbatim + small passthrough
print("\n[7] edge cases")
giant = '{"d":['+",".join(f'{{"i":{i}}}' for i in range(6000))+']}'  # one huge line
gout = compress_messages([{"role":"tool","tool_call_id":"g","content":giant},{"role":"assistant","content":"x"}])
check("giant single-line left verbatim (no mid-cut)", gout[0]["content"]==giant)
small = compress_messages([{"role":"tool","tool_call_id":"s","content":"tiny output"},{"role":"assistant","content":"x"}])
check("small content passthrough", small[0]["content"]=="tiny output")

# 8. ratio (interior bulk)
print("\n[8] depth")
bulk = [{"role":"user","content":"task"}]
for i in range(8):
    bulk.append({"role":"assistant","content":f"read {i}"}); bulk.append({"role":"tool","tool_call_id":f"t{i}","content":make_log(600,f"d{i}")})
bulk.append({"role":"assistant","content":"final"})
b_out = compress_messages(copy.deepcopy(bulk))
tot = lambda ms: sum(len(m.get("content") or "") for m in ms if isinstance(m.get("content"),str))
r = tot(bulk)/max(tot(b_out),1)
zone = {"conservative":(1.3,3.5),"target":(1.6,5.0),"aggressive":(2.2,9.5)}[mod._PROFILE]
check(f"bulk ratio in profile zone {zone}", zone[0]<=r<=zone[1], f"{r:.2f}x")

# 9. hostile shapes fail-open
print("\n[9] hostile shapes")
weird=[{"role":"tool"},{"content":"x"},"nope",{"role":"tool","content":42},{"role":"tool","content":{"n":"d"}}]
check("hostile shapes unharmed", json.dumps(compress_messages(copy.deepcopy(weird)))==json.dumps(weird))

print(f"\n{'ALL PASS' if FAIL==0 else f'{FAIL} FAILURES'}")
sys.exit(1 if FAIL else 0)
