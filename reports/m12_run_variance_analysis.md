# m12 RUN-VARIANCE analysis (per-run, comp 108) — the lever we mis-scoped

_Source: keyless per-run scrape `data/raw/platform_results/2026-06-23/043021_swe_runs.json`
(getSweTaskRunsAction, comp 108, m12 hotkey 5Dz7JaCB, **50 tasks × 5 runs = 250 run rows**).
Triggered by the user's question: "in fail-pass cases it shows pass but score isn't a full 4, and inside,
2 of 3 runs failed — did you check them?" Answer: YES now, at per-run level. The concern is correct and
bigger than the m12 analysis assumed. Reconciles to mean 0.7382 / total 0.7685._

## The headline correction
The m12 analysis (`reports/m12_comp108_analysis.md`) called the **"7 flips" a strength to protect** and scoped
the drag as **"−9.0 of avoidable negatives."** Per-run data shows that was wrong on both counts. The real
story is **run-to-run variance**: the SAME task+miner passes on some of its 5 runs and fails on others, and
the displayed per-task score is the MEAN of the 5. Variance bleeds points from tasks that still look "passing."

**Empirical per-run score bands (observed, not assumed):** a flipping run = **+2.5…+4.3**; a clean pass-pass
run = **+0.7…+2.9**; a BREAK run (baseline passed, we failed) = **−2.3…−4.0**; a both-fail run ≈ **−0.1…0**.
So every run that flips-vs-fails is a **~+4 to +8 swing**. Failed runs cost far more than the "0" I assumed.

## A. The 7 "flips" are mostly PARTIAL (the user's exact point)
16 tasks have a failing baseline (flip candidates). Of the 7 the report counted as flips, only **2 are clean
5/5** (302, 303). The rest carry 1-2 failed runs:

| task | agg | runs flipped | score | if 5/5* | recoverable | per-run scores |
|------|-----|-------------|-------|---------|-------------|----------------|
| 296  | pass | **3/5** | 1.31 | 3.19 | +1.89 | [2.9, −1.5, 3.4, −1.5, 3.3] |
| 305  | pass | **4/5** | 1.79 | 2.65 | +0.86 | [2.6, 2.7, 2.8, 2.6, −1.7] |
| 280  | pass | **3/5** | 1.85 | 3.59 | +1.74 | [−0.8, 3.6, −0.8, 3.9, 3.3] |
| 311  | pass | **4/5** | 2.24 | 3.19 | +0.96 | [3.6, 3.0, 3.1, −1.6, 3.1] |
| 290  | pass | **3/5** | 2.56 | 4.23 | +1.66 | [4.2, 0.1, 4.2, 4.3, 0.1] |
| 302  | pass | 5/5 | 2.69 | 2.69 | 0 | [2.7, 2.6, 2.6, 2.5, 3.0] |
| 303  | pass | 5/5 | 3.01 | 3.01 | 0 | [3.0, 2.9, 3.0, 3.1, 3.0] |

Math proof it's run-variance, not low ratio: a flipping run scores **≥ 3.0** (formula floor 4 + 0.5·(−2)).
Six of seven flips score **below 3.0** → each necessarily contains failing runs. At +1.31, only ~1-2 of 5 flip.

**Plus 2 near-flips the report missed:** **306** (1/5, scored −/+0.94 → if reliable **+4.28**) and **310**
(1/5, scored −0.76 → **+2.75**). These found the fix on a single run. Highest-value flip targets: **+3.34 /
+3.51 each.** (The other 7 flip-candidates are 0/5 — genuine capability gaps, not variance; leave them.)

## B. The BIGGER leak: 17 pass-pass tasks BREAK on some runs
Baseline passes, our compression breaks it on 2-3 of 5 runs (each −2.3…−4.0). This drags winnable tasks down
and is mostly INVISIBLE in the "−9.0" figure because many stay net-positive (e.g. 267: should be ~+1.4,
scored **+0.29** — lost ~1.1 but never showed as a negative task). Worst:
- t270 [−4, −4, 1.1, −4, 1.0] = **−1.98** (3 of 5 runs broke a baseline-winnable task)
- t297 [−4, −4, 1.2, 1.6, −4] = −1.83 · t313 [−4, 1.4, 0.8, 0.7, −4] = −1.03 · t295/t292 similar

## C. Magnitude (upper bounds — NOT all attainable)
- Flip-reliability upside (realistic targets 306/310/296/280/290/311/305): **~+14**, capturing half ≈ **+7**.
- Pass-pass break elimination to clean 5/5: upper bound **~+30**.
- vs the never-inflate play the m12.1 plan led with (~10 inflated tasks): a few points.
**Run-variance is the dominant lever by a wide margin.** Even a modest break-rate cut is worth more than the
entire inflation fix. (Current positives total +42.2, so this is the same order of magnitude as our whole score.)

## D. Attribution — is the variance OURS or provider noise? (HONEST: partly unresolved)
Break runs vs their sibling pass-runs, same task:
- break-run tokens LOWER in **14/17** tasks (mean 749K vs 1,109K); several break runs hit **9-20× ratios** the
  pass runs never reach (t268 16.5×, t269 20.7×, t307 13.0×, t315 10.6×) → looks like aggressive compression
  stripping load-bearing context.
- BUT break runs are also SHORTER (40.7 vs 54.2 steps); per-step retention is only ~10% lower → the high ratio
  is PARTLY mechanical (a run that fails early is short → small token count → high base/compressed ratio).
- A run that merely fails early would keep a NORMAL ratio; a 16-20× ratio (keeping ~6% of context) cannot be
  just "short" — those outliers are very likely ours. The bulk is ambiguous and some is the agent/provider
  non-determinism already documented in DISCOVERIES (early-cutoff noise).
**Conclusion: the extreme-ratio break runs are ours and fixable; the rest is mixed. Can't fully attribute from
dashboard data — must measure on the Mac eval (run each task 5× for m12 vs candidate, compare break rate).**

## E. What this changes for m12.1b
Promote run-determinism from roadmap Phase 3 to a PRIMARY goal of m12.1b:
1. **never-inflate** (keep — unambiguous; fixes the <1× inflated breaks like t313/t281). Pure win.
2. **CAP per-call aggressiveness** (NEW, the key add): never let a single compression call exceed a safe
   ratio / always retain a load-bearing floor, so no run rolls a destructive 10-20× compression. Directly
   attacks the extreme break runs.
3. **deterministic compression** (NEW): same input → same output, so a task that CAN pass passes on all 5 runs
   instead of gambling per run. Reduces both break-variance and flip-variance.
4. gentle-routing on genuinely break-prone signals (keep, secondary).
**Validation (now feasible because the eval is parallel): run the break/flip regression tasks at RUNS=5 for
m12 vs m12.1b and measure break-RATE + 5/5 consistency, not just aggregate pass.** Gate: fewer break runs,
no Medium-compression leak, never-inflate verified.

## Caveats / honesty
- Task names are masked (anti-targeting) so we can't map task_id→instance; this is all by task_id + baseline.
- "if 5/5 / clean" columns are UPPER bounds (assume every run reaches the task's observed passing-run quality);
  real recoverable is a fraction — hard flips won't go 5/5, and some variance is irreducible provider noise.
- The −4 break floor and the −1.5…−3.2 negatives on "failed" runs show the live penalty is harsher than the
  flat-−4 model; avoiding a break run is worth even more than previously stated.
