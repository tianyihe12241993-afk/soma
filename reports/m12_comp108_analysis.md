# m12 (m7-compliant) — full analysis, CoT-Compression-4 / comp 108
_Scored 2026-06-22. hotkey 5Dz7JaCB. Solution = upload_miner_m7_compliant.py. Task names masked by the
platform ("available after uploads finish") — anti-problem-targeting — so per-task category/instance mapping
is not yet possible; per-task score/pass/ratio only._

## Headline
- **Status: SCORED, PASSED REVIEW** (our coach-free / `[[CMP]]`-marker compliant build is clean — no
  failed-review). **Total 0.768 → currently #1 among SCORED miners** in comp 108.
- Category: **Easy 0.412 · Medium 0.953 · Hard 0.919**.
- 50 tasks = 5 screeners + **45 scored**. Score math: positives sum **+42.2**, negatives sum **−9.0**,
  over 45 → mean **0.738** → total 0.768.

## What's working (the positives — don't lose these)
- **7 FLIPS** (baseline failed → m12 passes): scores **+1.31, +1.79, +1.85, +2.24, +2.56, +2.69, +3.01**.
  ⚠ **CORRECTION (2026-06-23, per-run scrape — see `reports/m12_run_variance_analysis.md`):** these are NOT
  clean wins. Only 2 of 7 flip on all 5 runs (302,303); the rest are 3/5 or 4/5 (a flipping run scores ≥3.0,
  so any flip <3.0 has failing runs). They're our biggest UNTAPPED lever (run-reliability), not just a
  strength to "protect." Plus 2 near-flips missed here (306,310 at 1/5 → +4.28/+2.75 if made reliable).
- **20 tasks score > +1** (strong); **34/45 positive**.
- Strong compression where it's safe: ratios up to ~4× on clean passes (e.g. +0.77@4.01×, +1.56@3.12×,
  +2.25@3.58×).

## What's dragging (the gaps)
**1. Easy is the weak category — 0.412** (≈half of Medium/Hard). Structural (same as old m7: short tasks,
wander/over-compression-prone). Likely where most breaks/inflation concentrate (can't confirm — names masked).

**2. 11 NEGATIVE-score tasks = the −9.0 drag.** Three kinds:
- **3 HARD BREAKS** (baseline PASSED → m12 FAILED): **−1.98, −1.83, −0.43**. Over-compression lost a winnable task.
- **4 run-variance negatives** (passed overall but some of the 5 runs broke): **−1.03, −1.02, −0.93, −0.16**.
- (these overlap with inflation below)

**3. 10 token-INFLATED tasks (ratio < 1× — we made the context BIGGER than baseline).** This is a fixable
inefficiency: even when the task passes, inflation **caps or negates** the token bonus. Examples: a passed
task at **0.66× → −1.03**, others at 0.51×/0.70×/0.87×/0.90×/0.95×. We should **never emit a compression
larger than the baseline** — pass through instead.

## Compression profile
- mean **1.75×**, median **1.60×** — modest (compliant/gentle + new PSET). Only **2** near-passthrough,
  but **10 INFLATED (<1×)**. So the distribution has a bad left tail (inflation) we can cut for free.

## Field comparison
- **#1 among scored.** #2 = 5GYxeJjd **0.661** (E0.117/M0.661/H0.569 — weaker on every category). Head-to-head
  per-task: **m12 wins 24 / loses 21** (closer than totals suggest) — we win via more compression (1.75× vs
  their 1.34×) where we don't break; we **lose the tasks we broke** because the rival is gentler and keeps the
  pass (e.g. task where m12 −1.02 vs rival +1.09).
- **Threat: 5CwZBKyL `in queue` total 1.062** — but only **5 screener tasks** done so far; provisional, not a
  finalized 45-task eval. Watch it.

## Levers (ranked by value × safety) → points to m12.1 (reliability-tuned), NOT deeper
1. **Kill the inflation (10 tasks):** hard "never inflate" guard — if compressed ≥ baseline tokens, pass
   through. Pure win, zero pass-risk; recovers capped bonus + some of the −9.0.
2. **Cut the hard breaks (3) + run-variance (4):** route break-prone / Easy / error-dense tasks gentler
   (more pass-through / rich), trading ratio for fewer −2 hits. The −9.0 is where the points are.
3. **Easy (0.412):** structural; addressed mostly by (1)+(2) since breaks/inflation likely cluster there.
4. **Protect the wins:** keep the 7 flips + strong compression on safe Medium/Hard. → **deeper (H4b) is the
   wrong move** — it would break MORE; the rival shows gentler-but-safe scores competitively.

**Conclusion:** m12 is a strong, review-clean #1-among-scored baseline whose total is held back almost
entirely by ~−9.0 of avoidable negatives (breaks + token inflation), concentrated in Easy. The fix is
**reliability tuning (never-inflate + gentler on break-prone tasks)**, not more depth.
