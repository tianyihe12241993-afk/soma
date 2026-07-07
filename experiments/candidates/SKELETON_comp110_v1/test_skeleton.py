#!/usr/bin/env python3
"""Verification harness for upload_miner_skeleton_v1 (comp-110 SKELETON candidate). Stdlib only.
Run: [SOMA_SKEL_PROFILE=deep] python3 experiments/candidates/SKELETON_comp110_v1/test_skeleton.py"""
from __future__ import annotations
import copy, importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MINER = ROOT / "miner" / "cot_compression" / "upload_miner_skeleton_v1.py"
spec = importlib.util.spec_from_file_location("skel", MINER)
mod = importlib.util.module_from_spec(spec); sys.modules["skel"] = mod; spec.loader.exec_module(mod)
cm = mod.compress_messages
FAIL = 0
def check(name, cond, d=""):
    global FAIL
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{d}]" if d else ""))
    if not cond: FAIL += 1

def mklog(n, w="line"):
    out=[]
    for i in range(n):
        if i%40==0: out.append(f'  File "/testbed/django/db/models/expressions.py", line {i}, in resolve')
        elif i%33==0: out.append(f"FAILED tests/expressions/test_q.py::test_{i}")
        elif i%25==0: out.append(f"import django.db.models.sql.query_{i}")
        elif i%20==0: out.append(f"    def method_{i}(self, arg):")
        else: out.append(f"{w} {i} " + "x"*90)
    return "\n".join(out)

SPAN=re.compile(r"^\[\[CMP\]\] source line (\d+) ~ source line (\d+) Omitted \[\[/CMP\]\]$")
SINGLE=re.compile(r"^\[\[CMP\]\] source line (\d+) \[\[/CMP\]\]$")

def reconstruct_ok(original, compressed):
    orig=original.splitlines(); n=len(orig); cur=0
    for ln in compressed.splitlines():
        s=SPAN.match(ln); si=SINGLE.match(ln)
        if s:
            N,M=int(s.group(1)),int(s.group(2))
            if N!=cur+1 or M<N or M>n: return False
            cur=M
        elif si:
            N=int(si.group(1))
            if N!=cur+1: return False
            cur=N
        else:
            if cur>=n or ln!=orig[cur]: return False
            cur+=1
    return cur==n

print(f"profile={mod._PROFILE} min={mod.MIN_COMPRESS} head/tail={mod.HEAD_LINES}/{mod.TAIL_LINES} budget={mod.BUDGET} recency={mod._RECENCY}")

# contract
check("empty->[]", cm([], "/", {})==[]); check("None->[]", cm(None)==[])

# structure / roles
big=mklog(400)
convo=[{"role":"system","content":"You are Copilot CLI.\n"+mklog(300,"SYS")},
       {"role":"user","content":"Fix it.\n"+mklog(200,"USERREQ")},
       {"role":"assistant","content":None,"tool_calls":[{"id":"c1","type":"function","function":{"name":"bash","arguments":"{}"}}]},
       {"role":"tool","tool_call_id":"c1","content":big},               # interior -> skeletonized
       {"role":"assistant","content":"reading "+mklog(150,"COT")},      # assistant CoT -> skeletonized
       {"role":"tool","tool_call_id":"c2","content":mklog(350,"final")}]# FINAL -> recency verbatim
orig=copy.deepcopy(convo); out=cm(copy.deepcopy(convo))
check("len+roles preserved",[m.get("role") for m in out]==[m.get("role") for m in convo])
check("system NEVER compressed", out[0]["content"]==convo[0]["content"])
check("user NEVER compressed", out[1]["content"]==convo[1]["content"])
check("tool_calls msg untouched", out[2]==convo[2])
check("final msg verbatim (recency)", out[5]["content"]==convo[5]["content"])
check("input not mutated", convo==orig)
check("JSON-serializable", bool(json.dumps(out)))

skel=out[3]["content"]
check("interior tool WAS skeletonized (net reduction)", len(skel)<len(big))
markers=[l for l in skel.splitlines() if l.startswith("[[")]
check("markers present", len(markers)>0)
check("all markers exact template", all(SPAN.match(x) or SINGLE.match(x) for x in markers), next((x for x in markers if not(SPAN.match(x) or SINGLE.match(x))),""))
check("RANGE ACCURACY: reconstructs original exactly", reconstruct_ok(big, skel))
orig_lines=set(big.splitlines()); kept=[l for l in skel.splitlines() if not l.startswith("[[")]
check("no partial lines (kept lines verbatim)", all(l in orig_lines for l in kept))
bad=re.search(r"\[\[(?!CMP\]\]|/CMP\]\])", skel); check("no disallowed marker variants", bad is None)
check("no descriptive junk in markers", not any(w in skel for w in ("omitted chars","truncated","elided","chars omitted")))
# quality floor under a hard budget: PATHS are top-priority and must survive (the explore hit-rate
# signal). Lower-tier signal (defs/imports) fills the remaining budget → partial by design (that is
# how the savings gate is cleared); assert paths + that structural signal is represented, not exhaustive.
check("file path survives (top-priority explore signal)", 'expressions.py' in skel)
check("some structural signal survives (def/import/FAILED)",
      any(x in skel for x in ("def method_", "import django", "FAILED tests/expressions")))

# determinism
check("deterministic", json.dumps(cm(copy.deepcopy(convo)))==json.dumps(out))

# interior cache-stability: a non-final message compresses identically regardless of later messages
base=[{"role":"user","content":"t"},{"role":"tool","tool_call_id":"A","content":mklog(300,"A")},{"role":"assistant","content":"p"}]
ext=copy.deepcopy(base)+[{"role":"tool","tool_call_id":"B","content":mklog(300,"B")},{"role":"assistant","content":"p2"}]
ob,oe=cm(copy.deepcopy(base)),cm(copy.deepcopy(ext))
check("interior msg byte-identical as history grows (cache-safe)", json.dumps(ob[1])==json.dumps(oe[1]))

# small content passthrough + hostile shapes
small=cm([{"role":"tool","tool_call_id":"s","content":"tiny"},{"role":"assistant","content":"x"}])
check("small passthrough", small[0]["content"]=="tiny")
weird=[{"role":"tool"},{"content":"x"},"nope",{"role":"tool","content":42}]
check("hostile shapes fail-open", json.dumps(cm(copy.deepcopy(weird)))==json.dumps(weird))

print(f"\n{'ALL PASS' if FAIL==0 else f'{FAIL} FAILURES'}"); sys.exit(1 if FAIL else 0)
