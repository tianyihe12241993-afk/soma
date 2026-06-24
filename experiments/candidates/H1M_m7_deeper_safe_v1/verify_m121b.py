#!/usr/bin/env python3
"""Offline verification suite for m12.1b_run_stability vs m12 (no eval $, no platform).
Covers the spec's offline checks: never-inflate (ratio>=1.0), determinism (byte-identical
across PYTHONHASHSEED), safe-Medium unchanged, aggressive-outlier capped, routing (repeated
failure -> rich; Medium -> harvest; shallow_small gone), no protection regression."""
import importlib.util, tempfile, os, sys, subprocess, json
from pathlib import Path

MINERS = Path("/Users/user/SOMA/miner/cot_compression")
def load(fname, name):
    spec = importlib.util.spec_from_file_location(name, MINERS / fname)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
M12 = load("upload_miner_m7_compliant.py", "m12mod")
B   = load("upload_miner_m12_1b.py", "m121bmod")

PASS, FAIL = [], []
def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{('  — ' + detail) if detail else ''}")

# ---- fixture builders ----
def lines(n, pfx): return "\n".join(f"{pfx} content row {i} token data value xyz" for i in range(n))
def pair(cid, inp, result):
    return [{"role":"assistant","content":[{"type":"toolCall","id":cid,"name":"bash","input":inp}]},
            {"role":"toolResult","toolCallId":cid,"content":result}]
USER = {"role":"user","content":"TASK: fix the failing test in module foo. Repro: pytest tests/test_foo.py"}

def run(mod, messages, session, current=None):
    """Drive handle_assemble with ISOLATED state (fresh temp pluginDir + unique session)."""
    d = tempfile.mkdtemp()
    params = {"messages": messages, "sessionId": session}
    if current is not None: params["currentTokenCount"] = current
    out = mod.handle_assemble({"params": params, "pluginDir": d})
    return out
def toks(mod, messages): return mod.final_token_estimate(messages)
def ratio(raw_t, out_t): return raw_t / out_t if out_t else 0.0

# real error markers so is_error_bearing() fires (protection test must be non-vacuous)
ERRBLOB = "Traceback (most recent call last):\n  File foo.py line 9\nAssertionError: expected 1 got 2\nFAILED tests/test_foo.py::test_bar"

# === FIXTURE A: safe Medium (compressible, ~67k tok, no RECENT errors/repeat) — cap must NOT bind ===
# OLD results (i<6) are genuinely error-bearing (protected, preserved); recent window is clean
# so recent_errors stays 0 and the task stays in harvest (not rich).
medA = [USER]
for i in range(20):
    body = lines(300, f"r{i}") + (("\n" + ERRBLOB) if i < 6 else "")
    medA += pair(f"a{i}", f"run step {i}", body)
# two exact-duplicate old results (dedup target)
medA += pair("adup1", "dup", lines(300, "DUP")); medA += pair("adup2", "dup", lines(300, "DUP"))

# === FIXTURE B: aggressive outlier (~100k tok, in HARVEST: <120k & depth<90) — cap MUST bind ===
# big UNIQUE old bulk (harvest drops/truncates it toward 8k) + SMALL recent window (low untouchable
# floor) so m12 reaches >8x and m12.1b's cap floor (input/8) clearly widens retention. Some old
# results error-bearing for a meaningful protection check.
medB = [USER]
for i in range(16):                                   # old bulk: ~16 * 625 lines ~= 100k tok
    body = lines(625, f"B{i}uniq") + (("\n" + ERRBLOB) if i in (2, 5, 9) else "")
    medB += pair(f"b{i}", f"big step {i}", body)
for i in range(4):                                    # small recent window (kept intact)
    medB += pair(f"br{i}", f"recent {i}", lines(10, f"br{i}"))

# === FIXTURE C: near-incompressible small harvest (~4k tok) — never-inflate should hold ===
medC = [USER]
for i in range(6):
    medC += pair(f"c{i}", f"s{i}", lines(40, f"c{i}"))

# === FIXTURE D: repeated-failure, deep (depth>=24, same FAILED line x3 in recent window) ===
FAILLINE = "FAILED tests/test_foo.py::test_bar - AssertionError: 1 != 2"
medD = [USER]
for i in range(14):  # depth padding (28 msgs) with benign results
    medD += pair(f"d{i}", f"explore {i}", lines(50, f"d{i}"))
for i in range(4):   # recent window: same failure recurring
    medD += pair(f"df{i}", f"pytest run {i}", f"collected 3 items\n{FAILLINE}\n1 failed in 0.2s")

# === FIXTURE E: shallow + small (m12.1 would route to RICH; m12/m12.1b must NOT) ===
medE = [USER]
for i in range(4):
    medE += pair(f"e{i}", f"step {i}", lines(120, f"e{i}"))   # depth ~9, ~small tokens

print("=== 1. NEVER-INFLATE: m12.1b output ratio >= 1.0 on every fixture ===")
allok = True
for nm, msgs in [("A-medium",medA),("B-outlier",medB),("C-incompressible",medC),("D-repeatfail",medD),("E-shallow",medE)]:
    o = run(B, msgs, f"ni-{nm}")
    rt = toks(B, msgs); ot = o["estimatedTokens"]; r = ratio(rt, ot)
    ok = ot <= rt + 1  # ratio >= 1.0 (allow rounding)
    allok &= ok
    print(f"     {nm:<16} raw={rt:>7} out={ot:>7} ratio={r:>5.2f}x  neverInflate={o['baseMiner'].get('neverInflateTriggered')}")
check("never-inflate ratio>=1.0 on all fixtures", allok)

print("\n=== 2. SAFE MEDIUM unchanged: m12 vs m12.1b byte-identical (cap inactive, same routing) ===")
o12 = run(M12, medA, "med-12"); ob = run(B, medA, "med-b")
fp12 = M12.fingerprint_messages(o12["messages"]); fpb = B.fingerprint_messages(ob["messages"])
t12, tb = o12["estimatedTokens"], ob["estimatedTokens"]
check("Medium output byte-identical to m12", fp12 == fpb, f"m12={t12}tok m12.1b={tb}tok mode={ob['baseMiner']['mode']}")
check("Medium actually compressed (ratio>1)", tb < toks(B, medA), f"ratio={ratio(toks(B,medA),tb):.2f}x")
dtokpct = 100*abs(tb-t12)/t12 if t12 else 0
check("Medium tok within 3-5% of m12", dtokpct <= 5.0, f"Δ={dtokpct:.2f}%")

print("\n=== 3. AGGRESSIVE OUTLIER capped: m12 hits >8x, m12.1b capped ~<=8x and retains MORE ===")
o12 = run(M12, medB, "out-12"); ob = run(B, medB, "out-b")
rt = toks(B, medB); r12 = ratio(rt, o12["estimatedTokens"]); rb = ratio(rt, ob["estimatedTokens"])
check("m12 over-compresses outlier (>8x)", r12 > 8.0, f"m12 ratio={r12:.2f}x")
check("m12.1b ratio capped (<= ~8x + slack)", rb <= 9.0, f"m12.1b ratio={rb:.2f}x")
check("m12.1b retains MORE than m12 (widened)", ob["estimatedTokens"] > o12["estimatedTokens"],
      f"m12={o12['estimatedTokens']}tok < m12.1b={ob['estimatedTokens']}tok")

print("\n=== 4. DETERMINISM: same input -> byte-identical output across PYTHONHASHSEED (fresh process each) ===")
det_script = '''
import importlib.util, tempfile, sys
from pathlib import Path
MINERS = Path("/Users/user/SOMA/miner/cot_compression")
spec = importlib.util.spec_from_file_location("b", MINERS/"upload_miner_m12_1b.py")
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
def lines(n,pfx): return "\\n".join(f"{pfx} content row {i} token data value xyz" for i in range(n))
def pair(cid,inp,r): return [{"role":"assistant","content":[{"type":"toolCall","id":cid,"name":"bash","input":inp}]},{"role":"toolResult","toolCallId":cid,"content":r}]
msgs=[{"role":"user","content":"TASK"}]
for i in range(16): msgs+=pair(f"b{i}",f"big {i}",lines(625,f"B{i}uniq"))
for i in range(4): msgs+=pair(f"br{i}",f"recent {i}",lines(10,f"br{i}"))
d=tempfile.mkdtemp()
o=B.handle_assemble({"params":{"messages":msgs,"sessionId":"det"},"pluginDir":d})
print(B.fingerprint_messages(o["messages"]))
'''
fps = {}
for seed in ("0", "1", "12345"):
    env = dict(os.environ, PYTHONHASHSEED=seed)
    r = subprocess.run([sys.executable, "-c", det_script], capture_output=True, text=True, env=env)
    fps[seed] = r.stdout.strip() or f"ERR:{r.stderr[-200:]}"
uniq = set(fps.values())
check("byte-identical across hash seeds 0/1/12345", len(uniq) == 1, f"fingerprints={ {k:v[:12] for k,v in fps.items()} }")

print("\n=== 5. ROUTING (tightened): repeated-failure->rich; Medium->harvest; shallow_small GONE ===")
oD = run(B, medD, "route-D")
check("repeated-failure routes to RICH", oD["baseMiner"]["mode"] == "rich",
      f"mode={oD['baseMiner']['mode']} repeatedFailure={oD['baseMiner'].get('repeatedFailure')}")
oA = run(B, medA, "route-A")
check("normal Medium stays HARVEST (no over-route)", oA["baseMiner"]["mode"] == "harvest", f"mode={oA['baseMiner']['mode']}")
oE12 = run(M12, medE, "route-E12"); oEb = run(B, medE, "route-Eb")
check("shallow_small routes SAME as m12 (route dropped)", oE12["baseMiner"]["mode"] == oEb["baseMiner"]["mode"],
      f"m12={oE12['baseMiner']['mode']} m12.1b={oEb['baseMiner']['mode']}")
check("shallow_small NOT forced to rich", oEb["baseMiner"]["mode"] != "rich", f"mode={oEb['baseMiner']['mode']}")

print("\n=== 6. NO PROTECTION REGRESSION: error markers + frozen head preserved >= m12 ===")
def errmarkers(messages):
    txt = "\n".join(M12.extract_text(m.get("content")) for m in messages if isinstance(m, dict))
    return sum(txt.count(k) for k in ("AssertionError", "Traceback", "FAILED"))
o12 = run(M12, medA, "prot-12"); ob = run(B, medA, "prot-b")
check("Medium: m12.1b error markers >= m12", errmarkers(ob["messages"]) >= errmarkers(o12["messages"]),
      f"m12={errmarkers(o12['messages'])} m12.1b={errmarkers(ob['messages'])}")
check("frozen head (task statement) byte-identical", ob["messages"][0] == medA[0])
# outlier: rich-fallback retains MORE, so error markers must be preserved >= m12
o12B = run(M12, medB, "protB-12"); obB = run(B, medB, "protB-b")
check("outlier: m12.1b error markers >= m12", errmarkers(obB["messages"]) >= errmarkers(o12B["messages"]),
      f"m12={errmarkers(o12B['messages'])} m12.1b={errmarkers(obB['messages'])}")

print(f"\n=== SUMMARY: {len(PASS)} PASS / {len(FAIL)} FAIL ===")
if FAIL:
    print("FAILED:", FAIL); sys.exit(1)
print("ALL OFFLINE CHECKS PASS")
