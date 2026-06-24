# King (5DFvymSeEw) vs m12 — why the king wins Easy (comp-108, real task set)

_2026-06-23. Scrapes: m12 172813, king 175208 (both comp-108, 50 tasks×5 runs). Easy-proxy = the 15
smallest-context baseline-PASS tasks (platform Easy = low loss_ratio + low tokens). Goal: copy the king's
Easy behavior WITHOUT its weak Hard. Do NOT build/submit yet._

## 1. Totals (leaderboard)
| | total | Easy | Medium | Hard |
|---|---|---|---|---|
| king 5DFvymSeEw | 0.780 | **0.812** | 0.934 | 0.596 |
| m12 (us) | 0.768 | **0.412** | 0.953 | **0.919** |
King wins Easy +0.40; we win Hard +0.32; Medium ~tie. The whole gap is Easy.

## 2-3. Easy-proxy per-task — the pattern
- **m12 INFLATES 6/15 small tasks (ratio<1); king inflates only 1/15.** m12: sympy-15349 0.66×, django-12155
  0.51×, django-15161 0.70×, sympy-20590 0.90×, sympy-13647 0.87×, sympy-22456 0.95×. King keeps ratio ≥1 on
  14/15 (light positive ~1.0-1.8×).
- **4 tasks m12 breaks but king passes:** sympy-15349 (3/5→4/5), **django-13810 (2/5→5/5)**, sympy-20590
  (4/5→5/5), sympy-11618 (4/5→5/5). These are the score swings (e.g. django-13810: m12 −1.98 → king +1.16).

## 4. Run consistency
- Easy-proxy: m12 {5/5: 9, 4/5: 2, ≤3/5: 4}  vs  king {5/5: **11**, 4/5: 2, ≤3/5: **2**} — king breaks less.
- ALL 45: m12 {5/5: 14, 4/5: 9, ≤3/5: 22}  vs  king {5/5: **18**, 4/5: 5, ≤3/5: 22} — king more clean 5/5.

## 5-6. Compression ratio (the surprise)
- Easy-proxy mean: m12 **1.55×**, king **1.51×** — ~SAME.   ALL 45: m12 **1.75×**, king **1.77×** — ~SAME.
- Easy-proxy INFLATED (ratio<1): m12 **6/15**, king **1/15**.
- ⇒ The king does NOT compress lighter on average. The difference is the SHAPE: m12's small-context
  compression is erratic (6 inflate, a couple over-compress to 3×+); the king's is **uniform light positive
  compression (never inflates, never extreme).**

## 7. Lighter, fewer breaks, or both? → **FEWER BREAKS + NO INFLATION** (not lighter overall)
Average compression is identical (1.77 vs 1.75). The king wins Easy via (a) **fewer broken runs on small
contexts** (more 5/5) and (b) **near-zero inflation** (1/15 vs 6/15) — i.e. RELIABILITY + non-inflation, not
less compression.

## 8. Does the king stay qualified? YES.
King is status=scored (qualified). Avg ratio 1.77× (~43% raw savings) overall, 1.51× (~34%) on Easy-proxy —
well above the ≥10% weighted-savings gate. Crucially it achieves this with **light POSITIVE compression
(ratio >1)**, not pass-through — so it keeps savings AND avoids the inflation penalty. This is the needle
never-inflate misses (never-inflate → ratio 1.0 = 0 savings = gate risk).

## 9. Candidate-design implication (Easy-reliability miner) — DO NOT BUILD YET
The Easy lever is a **small-context-scoped path** that:
- **Never inflates** small contexts (m12's 6/15 inflation → penalty). But NOT by reverting to pass-through
  (that's 0 savings / gate risk) — instead emit **light POSITIVE compression (ratio ~1.1-1.5)** so savings
  stay above the gate, like the king.
- **Never breaks** small contexts (m12's 2/5, 3/5 small-task breaks are the bigger killer). Robust, minimal,
  stable compression on the Easy band.
- Target the ~6 inflated + ~4 broken small tasks → recover ~+0.3-0.4 Easy toward the king's 0.812.

## TOKEN-SHAPE INVESTIGATION (2026-06-23) — the king's Easy edge is AGENT DECISIVENESS, not compression
Scrape exposes per-run total tokens + agent_steps + time (NOT the cached/input/output split). Distinguishing
WANDER (more steps) vs CACHE-BUST (more tokens/step) on the 15 Easy-proxy tasks:
- **tokens/step IDENTICAL: m12 17,222 vs king 17,457** → NOT cache (m12 isn't re-processing more per step).
- **agent_steps: m12 44.2 vs king 38.9** → m12's agent takes MORE steps.
- **tokens/run: m12 807,791 vs king 689,939** → m12 burns more total tokens (more steps × same tok/step).
- **All 6 m12-inflated tasks: m12 has MORE steps than king at similar tok/step** (sympy-15349 52 vs 27;
  django-12155 51 vs 29; sympy-13647 52 vs 34; etc.). So m12's "inflation" (ratio<1) = the agent WANDERING
  (more steps → more cumulative tokens > baseline), NOT cache-busting, NOT compression depth.
⇒ **The king wins Easy because its agent is more DECISIVE (fewer steps), not because it compresses better.**
This re-confirms the comp-107 finding (Easy = decisiveness, "unreachable via our compression lever"). Two hard
constraints: (1) we CANNOT add a decisiveness/stop nudge (behavior steering is BANNED by the prompt policy);
(2) compression ratio/cache is NOT the lever (identical tok/step). The ONLY possible indirect lever: if m12's
ERRATIC small-context compression (inflate/drop/marker-noise) is what CONFUSES the agent into wandering, then a
CLEANER small-context context (e.g. m16's rich path) might reduce steps. UNPROVEN (could be agent/provider
variance) — measurable ONLY on the real comp-108 eval via agent_steps, not offline. So m16 is NOT a dead-end on
this framing: it's worth ONE cheap real-eval test measuring STEPS + breaks (not token ratio) on Easy tasks.

## 10. Explicitly protect m12's Hard/Medium harvest
- **Do NOT copy the king's Hard behavior** — king wins only 5/16 flip-candidates (avg flip-score 0.65) vs m12
  **7/16 (0.93)**. m12's aggressive harvest is BETTER on Hard/flips; the king is weak there.
- ⇒ The Easy fix must be **SCOPED to the small/Easy context band ONLY**, leaving the M/H harvest BYTE-IDENTICAL
  (the m13 mistake was a GLOBAL change that collapsed H+M). Small-context detection + light-safe compression;
  everything above the Easy band stays exactly as m12.
