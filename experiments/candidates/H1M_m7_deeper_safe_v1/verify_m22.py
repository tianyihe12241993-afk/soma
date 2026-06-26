#!/usr/bin/env python3
"""Offline structural verification for m22 vs m12.

Confirms the m22 design invariants the spec demands:
  HARD-SAFETY: per-harvest-turn output bytes <= m12's would-be harvest output (the
    invariant m21 violated). This is the guarantee that keeps Hard 0.919.
  RICH / PASSTHROUGH / ROUTER byte-identical to m12 (Hard routes to rich).
  SELECTOR: a would-be-DROPPED interaction with a buried changed-hunk + traceback
    that m12 blind-drops -> m22 RETAINS those lines (a tiny critical span).
  SELECTOR: a KEPT but blind-truncated result with a buried traceback in the middle
    that m12 cuts -> m22 RETAINS it.
  Pairing/orphan integrity, determinism, compliance.

NOTE: offline uses the TEXT char/token estimate; it CANNOT measure the platform's
cache / weighted Easy-inflation — efficacy needs the real comp-108 eval. This only
proves the mechanism + the safety invariants."""
import importlib.util, tempfile, sys, subprocess, os
from pathlib import Path

MINERS = Path("/Users/user/SOMA/miner/cot_compression")


def load(f, n):
    s = importlib.util.spec_from_file_location(n, MINERS / f)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


M12 = load("upload_miner_m7_compliant.py", "m12mod")
M22 = load("upload_miner_m22.py", "m22mod")
P, F = [], []


def ck(n, ok, d=""):
    (P if ok else F).append(n)
    print(f"  [{'PASS' if ok else 'FAIL'}] {n}{('  — ' + d) if d else ''}")


def lines(n, p):
    return "\n".join(f"{p} content row {i} token data value xyz" for i in range(n))


def pair(c, i, r):
    return [
        {"role": "assistant", "content": [{"type": "toolCall", "id": c, "name": "bash", "input": i}]},
        {"role": "toolResult", "toolCallId": c, "content": r},
    ]


USER = {"role": "user", "content": "TASK: fix the failing test. Repro: pytest tests/test_foo.py"}
ERR = ("Traceback (most recent call last):\n  File sympy/core/expr.py line 91\n"
       "AssertionError: 1 != 2\nFAILED tests/test_foo.py::test_bar")
HUNK = ("@@ -10,6 +10,8 @@ def simplify(expr):\n-    return expr\n+    return expr.doit()\n"
        "diff --git a/sympy/core/expr.py b/sympy/core/expr.py")


def run(mod, msgs, sess):
    return mod.handle_assemble({"params": {"messages": msgs, "sessionId": sess}, "pluginDir": tempfile.mkdtemp()})


def fp(mod, ms):
    return mod.fingerprint_messages(ms)


def total_chars(mod, ms):
    return sum(len(mod.extract_text(m.get("content"))) for m in ms if isinstance(m, dict))


def joined(mod, ms):
    return "\n".join(mod.extract_text(m.get("content")) for m in ms if isinstance(m, dict))


# ---- Fixtures ----
# A) Medium harvest task with DROPPABLE duplicate-read interactions that ALSO carry a
#    buried changed-hunk+traceback in one early interaction (the would-be-dropped span).
#    Big enough that the drop loop fires (oldest get dropped).
#    Kept small enough (per-result + total) to stay UNDER LARGE_THRESHOLD_TOKENS so
#    the router selects HARVEST (not rich) — but well above the 8k target so the drop
#    loop fires and the oldest droppable interactions are dropped.
#    The buried-span interaction carries a changed diff-hunk + signature + path but
#    NO error marker — so m12 classifies it as ordinary (droppable) boilerplate and
#    BLIND-DROPS it (error-bearing results are 'protected' and never dropped, so the
#    DROP-path fix specifically targets non-error results carrying a changed hunk).
#    Realistic Easy-task shape: many EXACT-DUPLICATE bulky reads (the drop loop's
#    cheap targets) PLUS a set of distinct moderate results that stay KEPT-and-
#    truncated (the reclaimable slack that funds the span — CHANGE 3). The buried
#    hunk lives in an EARLY duplicate-read clone, which m12 blind-drops.
SPAN = ("@@ -10,6 +10,8 @@ def simplify(expr):\n-    return expr\n+    return expr.doit()\n"
        "diff --git a/sympy/core/expr.py b/sympy/core/expr.py\n"
        "def doit(self, deep=True):  # signature the agent needs")
DUP = lines(140, "DUPBLOCK identical read output")
medA = [USER]
# 10 exact-duplicate bulky reads -> all but the survivor are droppable (cheap budget).
for i in range(10):
    body = DUP
    if i == 1:
        # buried changed-hunk in the MIDDLE of an early duplicate -> m12 blind-drops it
        body = lines(60, "noise") + "\n" + SPAN + "\n" + lines(60, "noise2")
    medA += pair(f"dup{i}", "cat foo.py", body)
# 8 distinct MODERATE results that stay kept-and-truncated (reclaimable slack).
for i in range(8):
    medA += pair(f"k{i}", f"grep bar{i}", lines(90, f"distinct content block {i}"))

# B) Hard/deep task (mode -> rich): must be byte-identical to m12.
medB = [USER]
for i in range(48):
    medB += pair(f"h{i}", f"deep {i}", lines(120, f"h{i}") + (("\n" + ERR) if i in (5, 20, 40) else ""))

# C) Passthrough (tiny): byte-identical / unchanged.
medC = [USER, *pair("c0", "echo hi", "hi there")]

# D) Harvest task where a KEPT (truncated) result has a buried traceback in the middle
#    of a long body (m12 blind head/tail would cut it).
medD = [USER]
for i in range(14):
    body = lines(300, f"line{i}")
    if i == 12:  # recent-ish, likely KEPT+truncated not dropped
        body = lines(300, "head") + "\n" + ERR + "\n" + HUNK + "\n" + lines(300, "tail")
    medD += pair(f"d{i}", f"run {i}", body)

print("=== HARD-SAFETY: m22 harvest output bytes <= m12 harvest output bytes (per turn) ===")
for nm, msgs in [("A-drop+span", medA), ("D-kept-trunc", medD)]:
    o12 = run(M12, msgs, f"12{nm}")
    o22 = run(M22, msgs, f"22{nm}")
    c12 = total_chars(M12, o12["messages"])
    c22 = total_chars(M22, o22["messages"])
    bm = o22["baseMiner"]
    ck(f"{nm}: m22 bytes <= m12 bytes", c22 <= c12,
       f"m12={c12} m22={c22} mode={bm['mode']} m22meta={bm.get('m22')}")

print("\n=== SELECTOR: would-be-DROPPED interaction's buried changed-hunk RETAINED ===")
o12 = run(M12, medA, "selA12")
o22 = run(M22, medA, "selA22")
j12 = joined(M12, o12["messages"])
j22 = joined(M22, o22["messages"])
bm = o22["baseMiner"]
# m12 BLIND-DROPS the early bulky a1 interaction (the changed-hunk gone). m22 must
# retain the hunk header + signature in a tiny span. Confirm m12 actually lost it.
ck("m12 BLIND-DROPS the buried hunk (control: gone from m12 output)",
   "@@ -10,6 +10,8 @@ def simplify(expr):" not in j12,
   "m12 hunk present? " + str("@@ -10,6 +10,8 @@ def simplify(expr):" in j12))
ck("m22 retains buried diff-hunk header (@@ -10,6 +10,8 @@)",
   "@@ -10,6 +10,8 @@ def simplify(expr):" in j22 or "diff --git a/sympy/core/expr.py" in j22,
   f"m22 rung={bm.get('m22')}")
ck("m22 retains the buried signature line", "def doit(self, deep=True)" in j22)
ck("m22 did NOT fully fall back to m12 (rung < 4) on the drop fixture",
   bm.get("m22", {}).get("rung", 4) < 4, f"rung={bm.get('m22',{}).get('rung')}")

print("\n=== SELECTOR: KEPT-but-truncated result's buried traceback RETAINED (medD) ===")
o22d = run(M22, medD, "selD22")
j22d = joined(M22, o22d["messages"])
ck("m22 retains buried traceback in a kept+truncated result",
   "FAILED tests/test_foo.py::test_bar" in j22d and "AssertionError: 1 != 2" in j22d)

print("\n=== RICH / PASSTHROUGH / ROUTER byte-identical to m12 ===")
o12, o22 = run(M12, medB, "rB"), run(M22, medB, "rB")
ck("Hard/deep (rich) byte-identical to m12", fp(M12, o12["messages"]) == fp(M22, o22["messages"]),
   f"m22mode={o22['baseMiner']['mode']}")
o12, o22 = run(M12, medC, "pC"), run(M22, medC, "pC")
ck("Passthrough byte-identical to m12", fp(M12, o12["messages"]) == fp(M22, o22["messages"]),
   f"m22mode={o22['baseMiner']['mode']}")
ck("m22 harvest fixture actually routed to harvest (not rich/passthrough)",
   run(M22, medA, "modeA")["baseMiner"]["mode"] == "harvest")

print("\n=== PAIRING: no orphan tool-calls/results in m22 harvest output ===")
o22 = run(M22, medA, "pairA")
orf, ocf = M22.orphan_ids(o22["messages"])
# m22 must not introduce orphans the input didn't have
in_orf, in_ocf = M22.orphan_ids(medA)
ck("no new orphan results", orf <= in_orf, f"out={len(orf)} in={len(in_orf)}")
ck("no new orphan calls", ocf <= in_ocf, f"out={len(ocf)} in={len(in_ocf)}")

print("\n=== ERROR-MARKER preservation on Hard fixture (rich path == m12) ===")
def em(mod, ms):
    t = joined(mod, ms)
    return sum(t.count(k) for k in ("AssertionError", "Traceback", "FAILED"))
o22 = run(M22, medB, "emB")
ck("error markers preserved (Hard)", em(M22, o22["messages"]) >= 9, f"markers={em(M22, o22['messages'])}")

print("\n=== COMPLIANCE scanner ===")
sc = subprocess.run(
    ["python3", "scripts/check_prompt_compliance.py", "miner/cot_compression/upload_miner_m22.py"],
    cwd="/Users/user/SOMA", capture_output=True, text=True,
)
ck("compliance scanner PASS", "PASS — compliant" in sc.stdout, sc.stdout.strip().splitlines()[-1] if sc.stdout.strip() else sc.stderr[-200:])

print("\n=== DETERMINISM across hash seeds (harvest path) ===")
det = '''
import importlib.util,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location("b",Path("/Users/user/SOMA/miner/cot_compression/upload_miner_m22.py"))
B=importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
def lines(n,p): return "\\n".join(f"{p} row {i} xyz value" for i in range(n))
def pair(c,i,r): return [{"role":"assistant","content":[{"type":"toolCall","id":c,"name":"bash","input":i}]},{"role":"toolResult","toolCallId":c,"content":r}]
ERR="Traceback (most recent call last):\\nAssertionError: x\\nFAILED tests/test_foo.py::test_bar"
m=[{"role":"user","content":"T"}]
for i in range(24):
    body=lines(400,f"r{i}")
    if i==1: body=lines(200,"n")+"\\n@@ -1,2 +1,3 @@\\n"+ERR+"\\n"+lines(200,"n2")
    m+=pair(f"a{i}",f"cat f{i}",body)
o=B.handle_assemble({"params":{"messages":m,"sessionId":"d"},"pluginDir":tempfile.mkdtemp()})
print(B.fingerprint_messages(o["messages"]))
'''
fps = {}
for s in ("0", "1", "99"):
    r = subprocess.run([sys.executable, "-c", det], capture_output=True, text=True, env=dict(os.environ, PYTHONHASHSEED=s))
    fps[s] = r.stdout.strip() or ("ERR:" + r.stderr[-120:])
ck("byte-identical across hash seeds", len(set(fps.values())) == 1, str({k: v[:12] for k, v in fps.items()}))

print(f"\n=== SUMMARY: {len(P)} PASS / {len(F)} FAIL ===")
if F:
    print("FAILED:", F)
    sys.exit(1)
print("ALL STRUCTURAL CHECKS PASS")
