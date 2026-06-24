# New king 5DAh2rUM — how it wins (2026-06-24)

_Scrape: data/raw/platform_results/2026-06-24/065650 (king) + 065917 (m12), same comp-108 50-task set, same
scrape window. King total **0.887** (#1), m12 0.768 (#3). **⚠️ King is review/eval = EVALUATING — provisional,
not finalized, not review-passed.** Per our discipline, treat the number as unsettled._

## The headline: the king is NOT a compression play
| metric | 5DAh2rUM (king) | m12 (us) |
|---|---|---|
| avg compression ratio (TokA/TokB) | **1.41×** | **1.75×** |
| tasks that INFLATE (<1×) | 12/45 | 10/45 |
| baseline pass | 29/45 | 29/45 |
| their pass (with compression) | 32/45 | **33/45** |
| flips (fail→pass) | 6 | **7** |
| breaks (pass→fail, task-level) | 3 | 3 |
| avg per-task platform_score | **0.878** | 0.738 |
| category E / M / H | **0.853** / 0.976 / 0.776 | 0.412 / 0.953 / **0.919** |

**The king compresses LESS than us, passes FEWER tasks, flips FEWER — yet scores higher.** So ratio is
definitively NOT the lever (we already compress harder). m12 even beats the king on many individual Medium/Hard
tasks (m12 +2.50 where the king broke django-13158). m12's Hard 0.919 >> king 0.776.

## The actual differentiator: RUN-VARIANCE (reliability across the 5 runs)
The leaderboard "total" ≈ mean(E,M,H). m12 is bimodal — elite M/H (0.95/0.92), cratered E (0.41). The king is
balanced. The Easy gap (0.41 vs 0.85 = +0.44) dwarfs the Hard gap (0.92 vs 0.78 = +0.14) → king wins the average.
**But m12's low Easy is NOT decisiveness — it's run-variance breaking pass-pass tasks.** Per-run detail on the
tasks the king wins:

| task | m12's 5 runs (score) | king's 5 runs |
|---|---|---|
| django-14122 | +1.18, **−4**, +0.79, +0.96, **−4** (mean −1.02) | +1.13,+1.37,+1.21,+1.34,+1.10 (all pass) |
| sympy-15349 | **−4**,+1.39,+0.77,+0.67,**−4** (mean −1.03) | all 5 pass (0.84–1.46) |
| django-11740 | +0.83,**−4**,+1.25,+1.29,**−4** (mean −0.93) | all 5 pass (0.98–1.33) |
| django-13810 | **−4,−4**,+1.11,**−4**,+1.01 (mean −1.98) | all 5 pass (0.74–1.16) |

m12 breaks on **2–3 of 5 runs** on these tasks (each break = −4 = a −5 swing vs a +1 pass). The king passes
all 5 consistently, with lighter compression. **This is the entire gap**, and it matches comp108_headroom's
"run-variance is the biggest leak (~17.6 pts)."

## The big confound (do NOT skip): cross-window
This is a CROSS-window comparison — the king is being evaluated NOW; m12 was scored days ago in a different
provider window. The platform is temporally noisy (Hard swings ±0.3 by window). So part of the gap could be
window luck, not our compression. **Two things push back on pure-window-luck:**
- The variance is WITHIN-task and WITHIN-window: m12 gets 3 passes AND 2 breaks on the SAME task in the SAME
  window. A bad provider window would sink all 5 together; instead m12's compression tips ~40% of trajectories
  into failure. That's at least partly intrinsic to m12's (aggressive) compression, not just timing.
- BUT our one SAME-window test (EXP-1b, 6 Medium/Hard break tasks, RUNS=3) found LIGHTER compression broke MORE,
  not less. So "just go lighter" is not obviously right; the depth↔reliability relation looks task-dependent.

## What this means (revised strategic read)
1. **The lever is RELIABILITY (run-to-run consistency), not ratio, not Easy-decisiveness, not depth.** m12 leaves
   huge points on the table by breaking 2–3 of 5 runs on pass-pass tasks. The king is the existence proof that
   ~5/5 consistency is achievable (and worth ~+0.12 total).
2. This is NOT the "Easy is agent-decisiveness-bound, dead" story. m12's Easy is low because m12 BREAKS easy
   pass-pass tasks under its own compression — a reliability problem, potentially ours to fix.
3. **m17 / depth / content-selection were all the wrong target** — they perturbed the agent (more wander, more
   breaks). The right target is the OPPOSITE: minimize run-to-run breaks (a safer / lighter / more
   cache-stable compression that keeps borderline trajectories on the pass path).
4. **Unresolved + must be settled same-window:** whether m12's run-variance is fixable-by-us (lighter/safer
   compression) or irreducible agent/provider noise. Cross-window king data is suggestive, not proof; EXP-1b
   (same-window, narrow) pointed the other way. The clean test = a SAME-window m12-vs-reliability-variant A/B on
   a BROAD task set (incl. easy/pass-likely), RUNS=5, scored on per-run break-rate — NOT the 6 break-task subset.
5. **Hard moat intact:** m12 0.919 vs king 0.776. Defend it. Don't sacrifice M/H chasing reliability.

## Caveats / status
- King is EVALUATING — its 0.887 and its clean 5/5 consistency may partly reflect its current (favorable?)
  window and may shift on finalization + review. Re-scrape when it hits `scored`.
- m17 A/B (running, MAXJOBS=3) is confirmed failing the same way as depth (agent-wander) — let it finish for the
  record; it does NOT address reliability.
