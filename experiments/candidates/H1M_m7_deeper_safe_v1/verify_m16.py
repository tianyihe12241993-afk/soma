#!/usr/bin/env python3
"""Offline structural verification for m16 vs m12. Confirms: M/H byte-identical (rescue never fires there),
rescue fires only on harvest-non-save, output never inflates, determinism, preservation. NOTE: offline uses
TEXT token-estimate; it CANNOT measure the platform's cache/weighted Easy-inflation — efficacy needs the real
comp-108 eval."""
import importlib.util, tempfile, sys
from pathlib import Path
MINERS = Path("/Users/user/SOMA/miner/cot_compression")
def load(f,n):
    s=importlib.util.spec_from_file_location(n,MINERS/f); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
M12=load("upload_miner_m7_compliant.py","m12mod"); M16=load("upload_miner_m16.py","m16mod")
P,F=[],[]
def ck(n,ok,d=""): (P if ok else F).append(n); print(f"  [{'PASS' if ok else 'FAIL'}] {n}{('  — '+d) if d else ''}")
def lines(n,p): return "\n".join(f"{p} content row {i} token data value xyz" for i in range(n))
def pair(c,i,r): return [{"role":"assistant","content":[{"type":"toolCall","id":c,"name":"bash","input":i}]},{"role":"toolResult","toolCallId":c,"content":r}]
USER={"role":"user","content":"TASK: fix the failing test. Repro: pytest tests/test_foo.py"}
ERR="Traceback (most recent call last):\n  File foo.py line 9\nAssertionError: 1 != 2\nFAILED tests/test_foo.py::test_bar"
def run(mod,msgs,sess): return mod.handle_assemble({"params":{"messages":msgs,"sessionId":sess},"pluginDir":tempfile.mkdtemp()})
def fp(mod,ms): return mod.fingerprint_messages(ms)
def rt(mod,ms): return mod.final_token_estimate(ms)

# Medium (compressible harvest, saves -> rescue must NOT fire) -> byte-identical
medA=[USER]
for i in range(20):
    medA+=pair(f"a{i}",f"run step {i}", lines(300,f"r{i}")+(("\n"+ERR) if i<6 else ""))
medA+=pair("ad1","dup",lines(300,"DUP")); medA+=pair("ad2","dup",lines(300,"DUP"))
# Hard/deep (mode=rich, rescue is harvest-only) -> byte-identical
medB=[USER]
for i in range(48):
    medB+=pair(f"h{i}",f"deep {i}", lines(120,f"h{i}")+(("\n"+ERR) if i in (5,20,40) else ""))
# Small-context that text-inflates: short unique results + a repeated tool-call loop (loop guard append)
medC=[USER]
for i in range(34): medC+=pair(f"c{i}",f"uniq {i}",lines(9,f"c{i}"))
for i in range(4): medC+=pair(f"lp{i}","pytest tests/test_foo.py","no output")
# Small-context with REDUNDANCY (near-dup stale results) above passthrough -> rich can dedup (light-positive)
medD=[USER]
for i in range(20): medD+=pair(f"d{i}","read foo.py", lines(40,"SAME stale tool output block")+f"\n# call {i}")

print("=== 3-4. M/H byte-identical to m12 (rescue must not fire) ===")
o12,o16=run(M12,medA,"mA"),run(M16,medA,"mA")
ck("Medium byte-identical to m12", fp(M12,o12["messages"])==fp(M16,o16["messages"]),
   f"m12={o12['estimatedTokens']} m16={o16['estimatedTokens']} mode={o16['baseMiner']['mode']} rescue={o16['baseMiner'].get('smallContextRescue')}")
o12,o16=run(M12,medB,"hB"),run(M16,medB,"hB")
ck("Hard/deep byte-identical to m12", fp(M12,o12["messages"])==fp(M16,o16["messages"]),
   f"mode={o16['baseMiner']['mode']}")

print("\n=== 5-6. small-context: rescue behavior (never inflate; light-positive or last-resort raw) ===")
for nm,msgs in [("C-textinflate",medC),("D-redundant",medD)]:
    o12,o16=run(M12,msgs,f"x12{nm}"),run(M16,msgs,f"x16{nm}")
    r12=rt(M12,msgs)/o12["estimatedTokens"] if o12["estimatedTokens"] else 0
    r16=rt(M16,msgs)/o16["estimatedTokens"] if o16["estimatedTokens"] else 0
    print(f"  {nm:<14} m12 ratio={r12:.3f} (mode {o12['baseMiner']['mode']}) | m16 ratio={r16:.3f} mode={o16['baseMiner']['mode']} rescue={o16['baseMiner'].get('smallContextRescue')}")
    ck(f"{nm}: m16 never inflates (ratio>=1)", r16>=0.999)

print("\n=== 1-2. compliance + rejected constructs (code) ===")
import subprocess
sc=subprocess.run(["python3","scripts/check_prompt_compliance.py","miner/cot_compression/upload_miner_m16.py"],cwd="/Users/user/SOMA",capture_output=True,text=True)
ck("compliance scanner PASS", "PASS — compliant" in sc.stdout)

print("\n=== 7-8. preservation (error markers + pairing) on Hard fixture ===")
def em(ms):
    t="\n".join(M12.extract_text(m.get("content")) for m in ms if isinstance(m,dict)); return sum(t.count(k) for k in ("AssertionError","Traceback","FAILED"))
o16=run(M16,medB,"pB")
ck("error markers preserved (Hard)", em(o16["messages"])>=9, f"markers={em(o16['messages'])}")
orf,ocf=M16.orphan_ids(o16["messages"])
ck("no orphan tool-calls/results (pairing intact)", len(orf)==0 and len(ocf)==0)

print("\n=== 9. determinism across hash seeds (harvest path) ===")
import os
det='''
import importlib.util,tempfile
from pathlib import Path
B=importlib.util.module_from_spec(importlib.util.spec_from_file_location("b",Path("/Users/user/SOMA/miner/cot_compression/upload_miner_m16.py")))
importlib.util.spec_from_file_location("b",Path("/Users/user/SOMA/miner/cot_compression/upload_miner_m16.py")).loader.exec_module(B)
def lines(n,p): return "\\n".join(f"{p} row {i} xyz" for i in range(n))
def pair(c,i,r): return [{"role":"assistant","content":[{"type":"toolCall","id":c,"name":"bash","input":i}]},{"role":"toolResult","toolCallId":c,"content":r}]
m=[{"role":"user","content":"T"}]
for i in range(20): m+=pair(f"a{i}",f"s{i}",lines(300,f"r{i}"))
o=B.handle_assemble({"params":{"messages":m,"sessionId":"d"},"pluginDir":tempfile.mkdtemp()})
print(B.fingerprint_messages(o["messages"]))
'''
fps={}
for s in ("0","1","99"):
    r=subprocess.run([sys.executable,"-c",det],capture_output=True,text=True,env=dict(os.environ,PYTHONHASHSEED=s))
    fps[s]=r.stdout.strip() or r.stderr[-100:]
ck("byte-identical across hash seeds", len(set(fps.values()))==1, str({k:v[:10] for k,v in fps.items()}))

print(f"\n=== SUMMARY: {len(P)} PASS / {len(F)} FAIL ===")
if F: print("FAILED:",F); sys.exit(1)
print("ALL STRUCTURAL CHECKS PASS")
