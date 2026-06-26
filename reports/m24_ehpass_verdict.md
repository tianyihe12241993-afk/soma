# EH-passthrough specialist — OFFLINE VALIDATOR VERDICT

_Date: 2026-06-25. Offline, read-only. Candidate = m12 with ONLY PASS_THROUGH_TOKENS raised, on a SEPARATE hotkey
(never built/uploaded — validated by parameterized replay first, per the gate-before-spend discipline)._

## VERDICT: **NO-GO for an element win.** The token-threshold passthrough lever cannot separate Easy from Hard.

The lever rescues the Easy tasks that don't need it and misses the ones that do, because the threshold needed to
rescue break-prone (deep) Easy tasks craters Hard routing — the exact Easy↔Hard token-size overlap that forced m12
to route on DEPTH, not size. No threshold satisfies all three gates (Hard-routing == m12 AND savings ≥10% AND
material Easy lift), and the safe-window Easy lift is far too small to win Pair(E,H) (need E>0.731) or Single-E (>0.923).

## Method
Parameterized connector-rewrite replay (`/tmp/m24_ehpass_validator.py`) using m12's ACTUAL code, over real comp-108
m12 trajectories: 6 Easy + 3 Medium + 6 Hard tasks (per the APPROXIMATE category map). Swept PASS_THROUGH_TOKENS and
measured the three synthesis gates per threshold. Caveat: local replay is faithful for ROUTING + SAVINGS (mechanical);
it does not reproduce break OUTCOMES, and the E/M/H map is approximate (django-14122's Hard label is disputed → shown
both ways via the excl-14122 column).

## Result (sweep)
```
PASS_THRU  HardRouteDiffs  savings%   Easy_PT%(m12->cand)   verdict
   3000          0          79.4%      6.4 -> 6.4           baseline (m12)
   3500          0          79.4%      6.4 -> 6.9           FAIL: no Easy gain
   4000          3*         79.4%      6.4 -> 8.7           FAIL: Hard route (*only django-14122; excl=0)
   6000          5*         79.3%      6.4 -> 14.0          FAIL: Hard route (*only 14122; excl=0)
  10000          9*         78.3%      6.4 -> 26.4          FAIL: Hard route (*only 14122; excl=0)
  15000         26          76.2%      6.4 -> 39.2          FAIL: Hard route (14122 + sympy-24661; excl=17)
  20000        507          69.4%      6.4 -> 53.6          FAIL: Hard route (6 Hard tasks; excl=449)
```
- **Binding constraint = Hard routing, not savings** (savings stayed ≥34% even at 80k). Any threshold >3500 re-routes
  at least the disputed django-14122; ≥15k re-routes undisputed Hard (sympy-24661); ≥20k re-routes 6 Hard tasks.
- **Even in the most generous reading** (django-14122 not Hard → safe up to ~10k), the Easy passthrough lift reaches
  only ~26%, and the per-Easy-task breakdown shows WHY that doesn't help the score:

```
Per-EASY-task passthrough @ PASS_THROUGH=10000:
  django-12039   92.0% STILL harvest/rich  <- deep, break-EXPOSED, NOT rescued
  sympy-14976    92.7% STILL harvest        <- not rescued
  sympy-24066    67.4% STILL harvest        <- mostly not rescued
  django-12155   37.0% still harvest        <- small task, mostly passthrough now
  django-13820   25.5% still harvest        <- small task
  sympy-20590    43.3% still harvest        <- small task
```
The break-prone deep Easy tasks (which drag Easy to 0.412) stay in harvest at the safe threshold; only the small
tasks m12 rarely breaks get rescued. To rescue the deep Easy tasks you need ≥20k, which craters Hard routing.

## Why it cannot win an element
- **Pair(E,H)** needs (E+H)/2 > 5DtEz's 0.825 → with H≈0.919, E must exceed 0.731 (+0.32 over 0.412). The Hard-safe
  passthrough lift rescues only small already-passing Easy tasks → Easy moves a little, nowhere near +0.32.
- **Single-E** needs > 0.923 (the new rival 5GCWaCnb ceiling) → +0.51. Out of reach.
- The synthesis's ~20% end-to-end estimate was optimistic; the validator shows the Easy magnitude is the binding wall,
  same as every prior Easy attempt (m13/m15/m16/m22). The lever is real but sub-element-threshold.

## What this does NOT close (honest)
- A **DEPTH-gated passthrough** (passthrough while shallow, compress once deep — mirroring m12's depth-based
  harvest→rich split) is a DIFFERENT mechanism not tested here. It might separate shallow-Easy from deep-Hard better
  than a token threshold — BUT it still changes Hard tasks' EARLY routing (shallow Hard turns → passthrough), so it
  carries the same m13 crater risk, and its OUTCOME is platform-only (not locally validatable). A possible future probe,
  not a clear win.
- The **insurance twin** (defense) and the **passive Pair(M,H)** upside (free, exogenous, via the king's volatile Hard)
  are unaffected by this verdict and remain the reliable position-improving moves.

## Recommendation
Do not build/ship the EH-passthrough specialist (no element win). The reliable move that actually changes our position
is the **byte-identical insurance twin**: it protects the 4.76% Single-Hard against the king's volatile Hard (which drew
0.981 > our 0.919 in one window) and holds us in passive position to capture Pair(M,H) (+9.52% → ~14.3%) whenever the
king re-draws a low Hard. Optionally probe the loop-detection-threshold sweep (the last compliant non-content stone).

## Artifacts
`/tmp/m24_ehpass_validator.py` (sweep + per-Easy breakdown). No miner file written; m12 LIVE untouched/git-clean.
