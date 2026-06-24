# Comp-108 algorithmic headroom — why scores are <1, and the research program (2026-06-23)

_Prompted by the user: 107 scores were all >1, 108 all <1 → big headroom; and m12 flips poorly → algorithmic.
Decomposition of m12's 108 tasks (scrape 172813). CORRECTS the earlier "m12 is at our ceiling" defeatism._

## Where m12 leaks points on the 108 tasks
1. **Run-variance on pass-pass — ~17.6 pts (BIGGEST).** 29 pass-pass tasks score mean **0.633** vs a clean
   baseline `1 + 0.5·ln(ratio)` ≈ **1.24**. **17/29 break on ≥1 of 5 runs.** A break run (baseline passes, we
   fail) = −4 vs +1 = a −5 swing. Recovering toward baseline would lift Medium + Easy hugely.
2. **Low compression ratio — ~+0.27/task across ~38 pass/flip tasks (~+10 raw).** m12 averages **1.75×** vs
   m7@107's **2.99×**; **31/45 tasks under 2.0×, 19/45 under 1.5×.** The `0.5·ln(ratio)` bonus is cross-category
   (lifts E, M, H). m12 is UNDER-compressing 108 — and the 107 "deeper breaks / at ceiling" verdict is MOOT
   (different tasks, never re-tested on 108).
3. **Weak flips — 7 won / 2 partial / 7 fail-fail.** Each flip ≈ +4. fail-fails have LOWER ratio (1.38× vs
   won 1.73×) → NOT over-compressed → likely capability-bound (model can't solve). The 2 partials (1–2/5) are
   the realistically convertible ones (run-variance, not capability).

## Why this beats the king (if we capture even a fraction)
m12 mean ≈0.74. Lifting pass-pass toward baseline + ratio toward ~2.5–3× could push the mean toward ~1.0+ —
cross-category (M, H, AND E), NOT the agent-bound Easy-decisiveness trap. That wins Overall (57%) outright.

## Honest caveats (what the research must resolve)
- **Run-variance may be largely AGENT/provider noise, not our compression** (each of the 5 runs is a different
  agent trajectory; the miner compresses each deterministically). The 17.6 is an UPPER bound. We CANNOT tell
  from existing data whether a break is "our over-compression broke a winnable task" vs "that trajectory
  would've failed anyway" — only a same-window A/B (m12 vs a variant) reveals it.
- **Depth ↔ breaks is a FRONTIER:** pushing ratio for more bonus may CAUSE more breaks. The research maps it.
- **Platform is temporally noisy** → only SAME-WINDOW local A/B on the real 108 tasks is trustworthy.

## Research program (same-window local A/B on comp-108, the only trustworthy eval)
- **EXP-1 (frontier map, highest value):** 3-way same-window A/B — **m12 vs m12-DEEPER (lower harvest target,
  e.g. TARGET_TOKENS 8k→4k) vs m12-LIGHTER (8k→16k)** — on a scoped set: the 17 breaking pass-pass + the 2
  partial flips + a few clean controls (~20 tasks), RUNS=5. Measures, per variant: ratio (bonus), break-rate
  (cost), resolved. Outcomes: DEEPER lifts ratio with NO extra breaks → free points (push depth). DEEPER adds
  breaks → frontier limit. LIGHTER cuts breaks → m12 was over-compressing (run-variance is ours, fixable).
  LIGHTER doesn't cut breaks → run-variance is agent noise (irreducible; stop chasing it).
- **EXP-2 (flip context):** for the 7 fail-fails + 2 partials, does preserving MORE flip-relevant context
  (error/diff/hypothesis) convert any? Same-window m12 vs a flip-preservation variant. (Lower priority —
  fail-fails likely capability-bound.)
- **Discipline:** hold M/H byte-identical-or-better (never regress the moat); hold key/window constant;
  compliant-only; ship only what nets positive same-window AND clears the savings gate.

## Reframe of the strategy
NOT "defend m12, nudge Easy." Instead: **attack the under-compression + run-variance on 108** (cross-category,
algorithmic, our lever) — this is where the <1 scores and the king-beating headroom actually are. Easy-via-
decisiveness stays a dead lever; this is different (compression depth + reliability, which IS our domain).
