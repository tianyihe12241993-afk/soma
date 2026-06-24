# m12.1b_run_stability — full regression result (comp 108 research)

_Eval: `experiments/runs/2026-06-23_050906_H1M_pbatch` (parallel driver, RUNS=5, MAXJOBS=3, 10 tasks =
4 fragile + 4 Medium + 2 Easy = 100 solves, 100/100 ok, 0 FAILED, 0 collisions, 1 transient 429 the agent
retried). m12 = live submission; m12_1b = candidate. **Local resolved/5 is OUR head-to-head reference — the
local eval has no no-compression baseline, so "break/flip" = m12_1b vs m12 on identical tasks, not vs platform
baseline.** Compression metadata is not persisted by OpenClaw, so per-call ratio<1.0 / outliers are taken from
the OFFLINE structural proof (never-inflate → ratio≥1.0 by construction; cap → no harvest>8x), not re-measured._

## Per-task resolved/5 (the run-consistency signal)
| task | cat | m12 | m12_1b | Δ |
|------|-----|-----|--------|---|
| django-14493 | HardFragile | 1/5 | **5/5** | **+4** (partial→clean flip — the target win) |
| django-11239 | HardFragile | 0/5 | 1/5 | +1 |
| sympy-16766  | HardFragile | 2/5 | 1/5 | **−1** |
| sympy-17139  | HardFragile | 3/5 | 2/5 | **−1** |
| django-15851 | Medium | 4/5 | 5/5 | +1 |
| django-11119 | Medium | 4/5 | 4/5 | 0 |
| django-14580 | Medium | 5/5 | 5/5 | 0 |
| sympy-24539  | Medium | 4/5 | 4/5 | 0 |
| django-13741 | Easy | 5/5 | 3/5 | **−2** |
| django-16255 | Easy | 5/5 | 4/5 | **−1** |

## Per-category aggregate
| cat | m12 resolved | m12_1b resolved | m12 tok/call | m12_1b tok/call | Δ tok/call | (in+out)/call m12→m12_1b |
|-----|------|------|------|------|------|------|
| **HardFragile** | 6/20 | **9/20 (+3)** | 14909 | 14952 | +0.3% | 2229 → 2943 |
| **Medium** | 17/20 | **18/20 (+1)** | 15076 | 15221 | +1.0% | 3987 → **3286 (−18%)** |
| **Easy** | 10/10 | **7/10 (−3)** | 15562 | 15965 | +2.6% | 2259 → 2346 |
| **TOTAL** | 33/50 | 34/50 (+1) | 15096 | 15245 | +1.0% | 2819 → 2923 |

## Read against the acceptance gate
- **Medium compression preserved — PASS.** Medium tok/call Δ=**+1.0%** (gate ≤3-5%); (in+out)/call actually
  DROPPED −18% (m12_1b compressed Medium working-tokens slightly *more*). No Medium leak. ✓
- **Ratio<1.0 count = 0 — PASS (structural).** never-inflate guarantees it; offline-proven byte-exactly.
- **Extreme 10-20x outliers reduced — PASS (structural).** cap → harvest>8x falls back to gentle rich;
  offline 17.89x→3.93x. (Not re-measurable in eval output — metadata not persisted.)
- **Compliance — PASS.** scanner clean.
- **Fragile/flip consistency — IMPROVED NET (+3), but MIXED.** django-14493 **1/5→5/5** is the textbook
  partial-flip→consistent-flip win the candidate was built for; django-11239 +1. BUT sympy-16766 (2→1) and
  sympy-17139 (3→2) each REGRESSED by one run.
- **Total resolved ≥ m12 — marginally (34 vs 33).** Essentially a TIE (+1 of 50 = noise level).
- **Easy — REGRESSED 10/10 → 7/10. This trips the spec's "Easy gets worse → reject."**

## Is the Easy regression real or agent noise? (honest)
m12_1b's changes are **near-inert on Easy**: cap never fires (tiny contexts, never >8x), shallow_small route
is DROPPED so Easy routes identically to m12 (offline-verified), repeated_failure is depth-gated (≥24 msgs,
Easy is shallower), and never-inflate only makes Easy *gentler* (more passthrough). Easy compression matched
m12 within ~3% (tok/call +2.6%). So there is **no mechanism by which m12_1b should hurt Easy** → the 10→7 is
most consistent with **agent/provider run-variance on a ceiling baseline** (m12 was 10/10; it can only move
down via noise). BUT n=10 (2 tasks × 5) is too small to PROVE it's noise — at p≈0.9, P(≤7/10)≈0.07.
The two sympy fragile regressions (±1 run) are likewise within 5-run noise.

## Verdict: **NO-SUBMIT. Keep m12 live.**
m12_1b is ~TIED with m12 overall, with a promising and on-target fragile/flip run-consistency gain (+3,
incl a clean 1/5→5/5) and fully preserved Medium — but it does **not cleanly clear the gate**: Easy regressed
(the explicit reject trigger) and 2 fragile tasks slipped, and the 5-run sample can't separate a real ±1-3 run
move from agent noise. Replacing the live #2 submission on an ambiguous wash is not justified.

## Recommended next step (before any submit decision)
**Targeted higher-power re-eval: RUNS=10, m12 vs m12_1b, on the decisive/noisy tasks only** — the 2 Easy +
the 4 fragile (6 tasks × 2 × 10 = 120 solves). This resolves: (a) does the fragile gain (esp. django-14493
5/5 and the sympy regressions) hold, and (b) is the Easy drop noise (recovers to ~parity) or real. If fragile
holds AND Easy recovers → accept + submit to a fresh hotkey. If Easy genuinely regresses → investigate the
routing/never-inflate interaction on short Easy tasks before any submit. Medium is already validated (preserved).
