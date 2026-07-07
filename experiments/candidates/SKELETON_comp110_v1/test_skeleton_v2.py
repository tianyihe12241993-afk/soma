#!/usr/bin/env python3
"""Verification harness for upload_miner_skeleton_v2 (consolidated comp-110 candidate). Stdlib only.
Run: [SOMA_SKEL_PROFILE=deep] [SOMA_SKEL_OMIT_STYLE=omitted] python3 .../test_skeleton_v2.py"""
from __future__ import annotations
import copy, importlib.util, json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MINER = ROOT / "miner" / "cot_compression" / "upload_miner_skeleton_v2.py"

def load():
    sys.modules.pop("skel2", None)
    spec = importlib.util.spec_from_file_location("skel2", MINER)
    m = importlib.util.module_from_spec(spec); sys.modules["skel2"] = m; spec.loader.exec_module(m)
    return m

mod = load(); cm = mod.compress_messages
FAIL = 0
def check(name, cond, d=""):
    global FAIL
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{d}]" if d else ""))
    if not cond: FAIL += 1

def mklog(n, w="line", term="\n"):
    out = []
    for i in range(n):
        if i % 40 == 0: out.append(f'  File "/testbed/django/db/models/expressions.py", line {i}, in resolve')
        elif i % 33 == 0: out.append(f"FAILED tests/expressions/test_q.py::test_{i}")
        elif i % 25 == 0: out.append(f"import django.db.models.sql.query_{i}")
        elif i % 20 == 0: out.append(f"    def method_{i}(self, arg):")
        else: out.append(f"{w} {i} " + "x"*90)
    return term.join(out) + term

CMP_SPAN=re.compile(r"^\[\[CMP\]\] source line (\d+) ~ source line (\d+) Omitted \[\[/CMP\]\]$")
OMIT_SPAN=re.compile(r"^\[\[Omitted\]\] source line (\d+) ~ source line (\d+) Omitted \[\[/Omitted\]\]$")
SINGLE=re.compile(r"^\[\[CMP\]\] source line (\d+) \[\[/CMP\]\]$")
def is_marker(l): return bool(CMP_SPAN.match(l) or OMIT_SPAN.match(l) or SINGLE.match(l))
def span_of(l):
    m = CMP_SPAN.match(l) or OMIT_SPAN.match(l)
    return (int(m.group(1)), int(m.group(2))) if m else None

def reconstruct_ok(original, compressed):
    orig = [re.sub(r'(\r\n|\r|\n)$','',x) for x in original.splitlines(keepends=True)]
    n = len(orig); cur = 0
    for ln in compressed.splitlines():   # splitlines handles mixed terminators
        sp = span_of(ln); si = SINGLE.match(ln)
        if sp:
            N, M = sp
            if N != cur+1 or M < N or M > n: return False
            cur = M
        elif si:
            if int(si.group(1)) != cur+1: return False
            cur = int(si.group(1))
        else:
            if cur >= n or ln != orig[cur]: return False
            cur += 1
    return cur == n

print(f"profile={mod._PROFILE} min={mod.MIN_COMPRESS} h/t={mod.HEAD_LINES}/{mod.TAIL_LINES} budget={mod.BUDGET} recency={mod._RECENCY}")
check("no [[Omitted]] literal anywhere in source (comments included)", "[[Omitted]]" not in MINER.read_text())

# 1 contract
check("empty->[]", cm([], "/", {})==[]); check("None->[]", cm(None)==[])

# 2 structure / roles / recency
big = mklog(400)
convo=[{"role":"system","content":"You are Copilot CLI.\n"+mklog(300,"SYS")},
       {"role":"user","content":"Fix it.\n"+mklog(200,"USERREQ")},
       {"role":"assistant","content":None,"tool_calls":[{"id":"c1","type":"function","function":{"name":"bash","arguments":"{}"}}]},
       {"role":"tool","tool_call_id":"c1","content":big},
       {"role":"assistant","content":"reading "+mklog(150,"COT")},
       {"role":"tool","tool_call_id":"c2","content":mklog(350,"final")}]
orig=copy.deepcopy(convo); out=cm(copy.deepcopy(convo))
check("len+roles preserved",[m.get("role") for m in out]==[m.get("role") for m in convo])
check("system NEVER compressed", out[0]["content"]==convo[0]["content"])
check("user NEVER compressed", out[1]["content"]==convo[1]["content"])
check("tool_calls msg untouched", out[2]==convo[2])
check("final msg verbatim (recency)", out[5]["content"]==convo[5]["content"])
check("input not mutated", convo==orig)
check("JSON-serializable", bool(json.dumps(out)))
skel=out[3]["content"]
check("interior tool skeletonized (net reduction)", len(skel)<len(big))

# 3 markers exact + range accuracy
markers=[l for l in skel.splitlines() if l.startswith("[[")]
check("markers present", len(markers)>0)
check("all markers exact template (current style)", all(is_marker(l) for l in markers), next((l for l in markers if not is_marker(l)),""))
check("RANGE ACCURACY reconstructs original exactly", reconstruct_ok(big, skel))
bad=re.search(r"\[\[(?!CMP\]\]|/CMP\]\]|Omitted\]\]|/Omitted\]\])", skel); check("no disallowed marker variants", bad is None, bad.group(0) if bad else "")
check("no descriptive junk in markers", not any(w in skel for w in ("truncated","elided","chars omit")))

# 4 quality floor (path top-priority)
check("file path survives (explore signal)", 'expressions.py' in skel)
check("some structural signal survives", any(x in skel for x in ("def method_","import django","FAILED tests")))

# 5 Codex fix — BYTE-VERBATIM line endings (CRLF) + terminal newline
crlf_head='KEEPME /a/b/keepme.py line 1'
crlf_text=crlf_head+"\r\n"+"\r\n".join(f"bulk {i} "+"z"*80 for i in range(200))+"\r\n"
co=mod._skeletonize(crlf_text)
check("CRLF kept line preserved byte-verbatim", (crlf_head+"\r\n") in co)
check("CRLF not normalized to bare \\n on kept line", (crlf_head+"\n") not in co.replace(crlf_head+"\r\n",""))
noeol_text="KEEP /x/p.py line 1"+"\n"+"\n".join(f"b {i} "+"y"*80 for i in range(200))+"\n"+"LASTLINE_NO_TERMINATOR"
no=mod._skeletonize(noeol_text)
check("terminal no-newline preserved (last kept line has no added terminator)", no.endswith("LASTLINE_NO_TERMINATOR"))

# 5b Codex v2 BLOCKING fix — BUDGET is a TRUE cap even with oversized head/tail lines
huge = "\n".join("BIGHEAD " + "q"*2000 for _ in range(5)) + "\n" + "\n".join(f"x {i}" for i in range(150)) + "\n"
ho = mod._skeletonize(huge)
kept_content = sum(len(l) for l in ho.splitlines() if not l.startswith("[["))
check("BUDGET is a true cap (kept content <= BUDGET even w/ oversized head)", kept_content <= mod.BUDGET,
      f"kept={kept_content} budget={mod.BUDGET}")

# 6 determinism + cache-safe interior
check("deterministic", json.dumps(cm(copy.deepcopy(convo)))==json.dumps(out))
base=[{"role":"user","content":"t"},{"role":"tool","tool_call_id":"A","content":mklog(300,"A")},{"role":"assistant","content":"p"}]
ext=copy.deepcopy(base)+[{"role":"tool","tool_call_id":"B","content":mklog(300,"B")},{"role":"assistant","content":"p2"}]
ob,oe=cm(copy.deepcopy(base)),cm(copy.deepcopy(ext))
check("interior msg byte-identical as history grows (cache-safe)", json.dumps(ob[1])==json.dumps(oe[1]))

# 7 small passthrough + hostile shapes
check("small passthrough", cm([{"role":"tool","tool_call_id":"s","content":"tiny"},{"role":"assistant","content":"x"}])[0]["content"]=="tiny")
weird=[{"role":"tool"},{"content":"x"},"nope",{"role":"tool","content":42}]
check("hostile shapes fail-open", json.dumps(cm(copy.deepcopy(weird)))==json.dumps(weird))

print(f"\n{'ALL PASS' if FAIL==0 else f'{FAIL} FAILURES'}"); sys.exit(1 if FAIL else 0)
