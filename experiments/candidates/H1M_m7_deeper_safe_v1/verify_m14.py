#!/usr/bin/env python3
"""Offline verification for m14_never_inflate_only vs m12. The ONLY allowed difference is the
never-inflate guard firing where m12 would inflate (output>=raw). Everywhere else m14 MUST be
byte-identical to m12 (harvest/rich/routing untouched)."""
import importlib.util, tempfile, sys
from pathlib import Path
MINERS = Path("/Users/user/SOMA/miner/cot_compression")
def load(f, n):
    s = importlib.util.spec_from_file_location(n, MINERS / f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
M12 = load("upload_miner_m7_compliant.py", "m12mod")
M14 = load("upload_miner_m14.py", "m14mod")

PASS, FAIL = [], []
def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name); print(f"  [{'PASS' if ok else 'FAIL'}] {name}{('  — ' + detail) if detail else ''}")

def lines(n, p): return "\n".join(f"{p} content row {i} token data value xyz" for i in range(n))
def pair(cid, inp, result):
    return [{"role": "assistant", "content": [{"type": "toolCall", "id": cid, "name": "bash", "input": inp}]},
            {"role": "toolResult", "toolCallId": cid, "content": result}]
USER = {"role": "user", "content": "TASK: fix the failing test. Repro: pytest tests/test_foo.py"}
ERR = "Traceback (most recent call last):\n  File foo.py line 9\nAssertionError: 1 != 2\nFAILED tests/test_foo.py::test_bar"

def run(mod, messages, session):
    out = mod.handle_assemble({"params": {"messages": messages, "sessionId": session}, "pluginDir": tempfile.mkdtemp()})
    return out
def fp(mod, msgs): return mod.fingerprint_messages(msgs)
def rt(mod, msgs): return mod.final_token_estimate(msgs)

# A: Medium (compressible harvest) — must be byte-identical to m12
medA = [USER]
for i in range(20):
    body = lines(300, f"r{i}") + (("\n" + ERR) if i < 6 else "")
    medA += pair(f"a{i}", f"run step {i}", body)
medA += pair("adup1", "dup", lines(300, "DUP")); medA += pair("adup2", "dup", lines(300, "DUP"))

# B: Hard/deep (depth>=90 -> rich) — must be byte-identical to m12
medB = [USER]
for i in range(48):
    body = lines(120, f"h{i}") + (("\n" + ERR) if i in (5, 20, 40) else "")
    medB += pair(f"h{i}", f"deep step {i}", body)

# C: inflation fixture — small harvest context, incompressible short results + a repeated
# tool-call loop (loop guard appends a msg). Harvest can't shrink it, so output>=raw -> m12
# inflates (ratio<1) and m14's guard reverts to pass-through.
medC = [USER]
for i in range(34):
    medC += pair(f"c{i}", f"unique cmd {i}", lines(9, f"c{i}"))  # short, under trunc cap, unique
for i in range(4):  # repeated identical tool-call -> triggers loop guard
    medC += pair(f"loop{i}", "pytest tests/test_foo.py", "no output")

print("=== 1. never-inflate INVARIANT: m14 ratio >= 1.0 on every fixture ===")
inv = True
for nm, msgs in [("A-medium", medA), ("B-hard-deep", medB), ("C-inflation", medC)]:
    o = run(M14, msgs, f"inv-{nm}"); rti = rt(M14, msgs); oti = o["estimatedTokens"]
    ok = oti <= rti + 1; inv &= ok
    print(f"     {nm:<14} raw={rti:>6} out={oti:>6} ratio={(rti/oti if oti else 0):>5.2f}x neverInflate={o['baseMiner'].get('neverInflateTriggered')} mode={o['baseMiner'].get('mode')}")
check("m14 ratio >= 1.0 on all fixtures", inv)

print("\n=== 2. SAFE MEDIUM byte-identical to m12 (guard must NOT fire) ===")
o12, o14 = run(M12, medA, "m-12"), run(M14, medA, "m-14")
check("Medium m14 == m12 (byte-identical)", fp(M12, o12["messages"]) == fp(M14, o14["messages"]),
      f"m12={o12['estimatedTokens']}tok m14={o14['estimatedTokens']}tok mode={o14['baseMiner']['mode']}")
check("Medium actually compressed (ratio>1, guard inert)", o14["estimatedTokens"] < rt(M14, medA))

print("\n=== 3. SAFE HARD/DEEP byte-identical to m12 ===")
o12, o14 = run(M12, medB, "h-12"), run(M14, medB, "h-14")
check("Hard m14 == m12 (byte-identical)", fp(M12, o12["messages"]) == fp(M14, o14["messages"]),
      f"m12={o12['estimatedTokens']}tok m14={o14['estimatedTokens']}tok mode={o14['baseMiner']['mode']}")

print("\n=== 4. INFLATION fixture: m12 inflates (ratio<1), m14 reverts to pass-through (ratio=1.0) ===")
o12, o14 = run(M12, medC, "c-12"), run(M14, medC, "c-14")
r12 = rt(M12, medC) / o12["estimatedTokens"] if o12["estimatedTokens"] else 0
r14 = rt(M14, medC) / o14["estimatedTokens"] if o14["estimatedTokens"] else 0
print(f"     m12: ratio={r12:.3f}x out={o12['estimatedTokens']} mode={o12['baseMiner']['mode']} changed={o12['baseMiner'].get('changed')}")
print(f"     m14: ratio={r14:.3f}x out={o14['estimatedTokens']} mode={o14['baseMiner']['mode']} neverInflate={o14['baseMiner'].get('neverInflateTriggered')}")
if r12 < 1.0:
    check("m12 inflated here AND m14 fixed it (ratio>=1.0)", r14 >= 1.0 and o14["baseMiner"].get("neverInflateTriggered"), "guard fired")
else:
    # if m12 didn't inflate on this fixture, the key guarantee still holds: m14>=1.0 and m14==m12 (no inflation to fix)
    check("no inflation here -> m14 == m12 (guard correctly inert)", fp(M12, o12["messages"]) == fp(M14, o14["messages"]),
          f"m12 ratio={r12:.3f} (>=1, nothing to fix)")

print("\n=== 5. characterization: m14 differs from m12 ONLY when m12 inflated ===")
allok = True
for nm, msgs in [("A-medium", medA), ("B-hard", medB), ("C-inflation", medC)]:
    a, b = run(M12, msgs, f"x12-{nm}"), run(M14, msgs, f"x14-{nm}")
    m12r = rt(M12, msgs) / a["estimatedTokens"] if a["estimatedTokens"] else 0
    identical = fp(M12, a["messages"]) == fp(M14, b["messages"])
    expect_identical = m12r >= 1.0  # m14 should equal m12 unless m12 inflated
    ok = (identical == expect_identical)
    allok &= ok
    print(f"     {nm:<14} m12_ratio={m12r:.3f} identical={identical} expect_identical={expect_identical} {'ok' if ok else 'MISMATCH'}")
check("m14 == m12 exactly where m12 didn't inflate", allok)

print("\n=== 6. NO PROTECTION REGRESSION: error markers preserved >= m12 ===")
def em(msgs):
    t = "\n".join(M12.extract_text(m.get("content")) for m in msgs if isinstance(m, dict))
    return sum(t.count(k) for k in ("AssertionError", "Traceback", "FAILED"))
for nm, msgs in [("Medium", medA), ("Hard", medB)]:
    a, b = run(M12, msgs, f"p12-{nm}"), run(M14, msgs, f"p14-{nm}")
    check(f"{nm}: m14 error markers >= m12", em(b["messages"]) >= em(a["messages"]), f"m12={em(a['messages'])} m14={em(b['messages'])}")

print(f"\n=== SUMMARY: {len(PASS)} PASS / {len(FAIL)} FAIL ===")
if FAIL: print("FAILED:", FAIL); sys.exit(1)
print("ALL OFFLINE CHECKS PASS")
