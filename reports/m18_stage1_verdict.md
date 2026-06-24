# m18 Stage-1 live gate — VERDICT: REJECT (2026-06-24)

Run `experiments/runs/2026-06-24_073745_H1M_pbatch` — m12 vs m18, 5 tasks × RUNS=3 = 30 solves, MAXJOBS=3,
same key/window. 30/30 complete, 0 FAILED, 0 429s. (Driver exited 1 on a benign end-of-script grep under `set -e`
AFTER all solves finished + cleanup ran — data is complete/valid.)

## Evidence
| task | type | m12 res | m18 res | m12 brk | m18 brk | m12 tok | m18 tok | m12 calls | m18 calls |
|---|---|---|---|---|---|---|---|---|---|
| django-14122 | small | 3/3 | 3/3 | 0 | 0 | 1.01M | 1.23M (+21%) | 45.7 | 57 |
| django-12039 | small | 1/3 | 1/3 | 0 | 0 | 1.08M | 1.04M | 58 | 53.7 |
| django-12050 | small | 3/3 | 3/3 | 0 | 0 | 443k | 786k (+77%) | 31 | 42.7 |
| **django-13158** | CONTROL | **3/3** | **0/3** | 0 | 0 | 1.73M | 805k | 71 | **33.7** |
| sympy-18698 | CONTROL | 1/3 | 0/3 | 1 | 1 | 1.9M | 1.04M | 46 | 35 |

## Risk findings (the three we set out to test)
1. **Ultralight fires:** YES (inferred from token retention — m18 > m12 on small targets; and from the
   regressions on controls). NOTE: could not read mode directly — the per-solve plugin state is deleted after
   each solve, and grepping solve dirs for "ultralight"/"harvest" is CONTAMINATED by the baked source file. Mode
   must be inferred from behavior (token/step deltas).
2. **HARD-MOAT REGRESSION: REALIZED — decisive reject.** django-13158 (m12 3/3, +2.50 on platform) → **m18 0/3**,
   same window, m18 taking HALF the steps (33.7 vs 71). sympy-18698 1/3 → 0/3. m18's early-ultralight turns (fired
   while the hard task was still shallow) perturbed the trajectory → agent went down a failing, shorter path.
3. **m17-style perturbation: REALIZED** — the regressions are perturbation-driven (fewer steps, agent off-track),
   plus +21%/+77% tokens and +25% calls on the clean small tasks. Same failure family as depth & m17.

## Why the thesis was untestable here (the window-noise trap)
m12 broke NONE of the 3 small targets locally this window (django-14122 3/3, django-12050 3/3, django-12039 1/3
with 0 breaks). The whole premise — "m18 recovers m12's easy-breaks" — needs m12 to break those tasks in the eval
window, but its run-variance is window-dependent (django-14122 breaks on the PLATFORM, ran clean LOCALLY). So
m18 had no breaks to recover and only added token cost on the clean tasks.

## The fundamental flaw (kills the size-gated approach, not just these thresholds)
A hard task STARTS shallow. m18's gate fires ultralight on its early small/shallow turns — indistinguishable from
an easy task's turns — perturbing the trajectory BEFORE the task deepens enough to escalate to rich. By the time
cumulative/depth crosses the thresholds, the early light turns have already sent the agent off-track. **No
threshold fixes this:** tighten it and ultralight stops firing at all (m18≡m12, no experiment); loosen it and more
hard tasks get damaged. Easy and early-hard contexts are not separable by any structural signal the miner legally
has. So "revise thresholds" cannot rescue m18 — REJECT outright.

## Verdict: REJECT m18
Stage-1 reject criteria hit: hard control REGRESSED (3/3→0/3), no break improvement on small targets, tokens/calls
increased materially, m17-style perturbation. Do NOT proceed to Stage 2. m18 = reference-only; m12 stays LIVE.

## Strategic consequence
Four compliant levers now empirically dead, all the same failure (agent destabilizes under context perturbation):
depth (EXP-1b), content-selection (m17), uniform-light (king's Hard collapse), size-gated-adaptive-light (m18).
The Easy↔Hard tension is STRUCTURAL: easy wants light compression, hard wants aggressive, and they are
indistinguishable early — so a single compliant miner cannot win both. m12 wins Hard+Medium and sacrifices Easy;
that is a defensible local optimum. **HOLD m12.** The remaining real lever is the in-flux upstream scoring layer
(not a miner change). Easy is confirmed not reachable for us without sacrificing the Hard moat.
