# m20-BLIND gated A/B — VERDICT: REJECT (2026-06-24)

m12 vs m20-blind, 6 large/deep tasks x RUNS=3 = 36 solves (run 2026-06-24_165843), MAXJOBS=3, same window.
36/36 complete, 0 FAILED, 0 429s (driver exit-1 = benign end-of-script grep, data valid).

## Result: the ratio thesis BACKFIRED
| task | m12 res | m20b res | m12 tok | m20b tok | steps m12->m20b |
|---|---|---|---|---|---|
| sympy-18698 | 1/3 | 3/3 | 1.20M | 1.45M (+21%) | 48->57 |
| django-13158 | 2/3 | 1/3 | 1.14M | 1.14M | 53->49 |
| django-13810 | 2/3 | 2/3 | 847k | 729k (-14%) | 48->44 |
| django-14122 | 1/3 | 2/3 | 1.77M | 2.32M (+31%) | 64->88 |
| sympy-23262 | 0/3 | 1/3 | 1.46M | 2.54M (+74%) | 78->106 |
| sympy-24661 | 3/3 | 2/3 | 983k | 1.12M (+14%) | 59->55 |

- **RATIO WENT DOWN, not up**: m20b uses MORE tokens on 4/6 (up to +74%) with MORE steps. Dropping superseded
  file-view middles removed content the agent NEEDED -> it WANDERED to recover -> more turns -> higher cumulative
  tokens -> LOWER per-task ratio -> LESS bonus + less savings-multiplier headroom. The core thesis (raise ratio)
  failed; this is the depth/m17/m18 wander mechanism.
- Breaks ~equal (m12 1, m20b 1). Resolved nominally higher (m20b 11/18 vs m12 9/18) but that's n=3 run-variance
  on capability-bound flips (sympy-18698 1/3->3/3; dropping old file views has no mechanistic reason to aid
  flipping) and is swamped by the consistent token/step blow-up. Not worth a larger A/B (wander precedes breaks).

## Accept gate: FAILS (ratio up = NO). REJECT m20-blind.

## What it definitively settles
The A/B was the oracle offline lacked. Even the NARROWEST cut (old/superseded/non-anchor/same-file views) is
content the agent needs -> wander. So the entire compress-harder family is closed: depth, m17 (selection), m18
(adaptive-light), m20-extractive (no gain), m20-blind (wander). The per-task ratio-bonus headroom is REAL in the
formula but NOT capturable -- m12 already keeps exactly the content the agent needs; anything beyond its dedup
makes the agent wander. m12 is at the true compliant ceiling. HOLD m12; defense = the M+H moat; growth = portfolio
specialist (2nd hotkey) or a favorable re-eval window. m20_blind sha 328fdcfa = reference-only; m12 LIVE.
