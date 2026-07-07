# cap32+pin comp-108 postmortem — pros, cons, and what transfers to comp-110

_2026-07-07. **Interpretation layer** — every number below comes from the generated data section
(`comp108_cap32pin_postmortem_data.md`, script `scripts/analyze_cap32pin_comp108.py`, snapshot
`data/raw/platform_results/2026-07-07/045717_swe_runs.json`: 13 miners × 50 tasks × 5 runs,
source:platform). Categories = solved from the 39 board constraints (validation table matches every
miner to ±0.02). Savings ratios are RAW-token approximations (platform used weighted)._

## Executive verdict
cap32+pin won on **profile shape + compliance + a favorable draw** — NOT on the pin, and NOT on
compression power. The win decomposes into: (1) lowest-tier break rate (7.6%) among Overall
contenders, (2) best-in-field cache share (90.9%, the DeepInfra+Venice routing), (3) the cap32
fuller-keep genuinely buying Hard without selling Easy, (4) every higher-raw rival being DQ'd, and
(5) a 0.0025 margin over the #2 that is pure run-variance luck.

## PROS (validated, keep for comp-110)
1. **The CAP concept worked exactly as designed.** cap32+pin vs np2 (same 16k behavior on small
   results): H **+0.108**, M +0.057, E −0.048 → the >53k→32k fuller-keep bought Hard nearly for free.
   vs np3 (28k flat): E **+0.188**, M +0.021, H −0.088 → kept np2's Easy while approaching np3's Hard.
   The "combined-Overall" middle point is real. **Port the tiered/proportional cap to comp-110.**
2. **Break avoidance was the actual differentiator at the top.** Our 7.6% break-runs vs M-winner
   10.0% / H-winner 10.4%. In a −4-per-break regime, 2.4pp of breaks ≈ the whole winning margin.
   The conservative harvest discipline (protect structure, never over-compress mid-tier results) is
   the thing to preserve.
3. **Routing/cache edge was real and nobody else had both.** 90.9% cache with clean breaks; M-winner
   85.8%, H-winner 84.3%, E-winner 72.1%. Weighted tokens (cached=⅓) made this a standing score
   subsidy. comp-110 keeps weighted tokens → **provider/cache hygiene stays a first-class lever**
   (now DeepSeek-forced, so the lever = prompt-prefix byte-stability, not provider choice).
4. **Compliance as strategy is confirmed, brutally.** 23 higher-raw miners failed review; the two
   kings (0.852, 0.825) profiled as *better* than us on the board (lower breaks / deeper keep) and
   still earned 0%. Rule-rigor beat cleverness.

## CONS (things comp-108 state got wrong or oversold — correct the record)
1. **The pin never proved value on-platform; both isolation A/Bs are NEGATIVE.**
   np2+pin − np2: E −0.348 / M −0.137 / H −0.018. np3+pin − np3: E −0.103 / M −0.012 / H −0.019.
   And the pin's core thesis (pin imports → fewer breaks) is REFUTED at run level: np2+pin broke
   *more* (10.4% vs 7.2%), np3+pin too (9.2% vs 7.6%). cap32+pin's own low break rate matches the
   *bases'* rate, not a pin improvement. With one Easy screener disaster shared by both pin variants
   (`django-15375`: −2.17 / −1.41) this reads as pin-composition risk + bad draws, not pin value.
   **⇒ For comp-110: the salience pin is UNPROVEN-AT-BEST; do not port it by default. If ported,
   it must re-earn its place behind an A/B.**
2. **"Compliant frontier ≈ 0.76 / compression is at its ceiling" was WRONG.** M-winner passed
   review at **2.58× keep with M 0.969** (vs our 1.45× / 0.862) and finished 0.0025 behind us.
   Legit deep compression coexisted with top Medium. Our miner was **savings-light**; we won despite
   compression depth, not because of it. **⇒ comp-110's explore layer pays log2(savings) directly —
   the M-winner direction (deep + quality-preserving) is now the scoring-favored one. Study it.**
3. **The crown margin was luck-sized.** Top-5 clean totals: 0.7228 / 0.7203 / 0.7102 / 0.6965 /
   0.6842. Our per-attempt pseudo-draw totals span **0.381–0.885**; task-score std ~0.73. Any
   single-draw ordering inside that cluster is noise. The strategy earned "top cluster + not DQ'd";
   the #1 slot specifically was variance. **⇒ Don't tune to <0.05 deltas; enter the comp-110 cluster
   with the safest profile and (as before) hold multiple hotkeys for the corners.**
4. **Hard was and stayed our structural weakness.** H 0.281 vs H-winner 0.718 (−0.437/task,
   biggest: sympy-16792 −2.56, sympy-20801 −1.44, sympy-14976 −1.32). H-winner's recipe: more flips
   (15.6% vs 11.2%) at moderate keep (1.54×) — flip production, not fuller context alone. We never
   cracked it in 108; carrying the same approach into comp-110's swebench layer forfeits Hard again
   (if a Hard-like layer exists under the new task-type scheme).
5. **np2+pin / np3+pin burned two hotkeys on a lever that was net-negative** — the "pin can only
   add" upload logic ignored that a worse draw + worse composition could land (and did: 0.516, 0.636
   both below their bases). Cheap lesson for comp-110's tighter one-week window: every upload slot
   must pass an isolation-tested mechanism, not a plausible one.

## What this means for the comp-110 port (design inputs, USER decides)
- **Port**: tiered cap (small=passthrough-ish, mid=conservative, huge=capped-full-keep) + the break-
  averse discipline + byte-stable prefix for cache. **Hold back**: the salience pin (A/B it locally
  first — the new stack can actually verify firing).
- **New**: an explore-mode strategy is mandatory (passthrough = 0 there). The safest shape consistent
  with our comp-108 evidence: compress aggressively on *bulk* content while never dropping file-path/
  location-bearing lines (quality gate = hit_file_rate − noise_file_rate).
- **Honest unknowns**: DeepSeek V4 Pro behavior, copilot CLI trajectory shape, per-task-type layer
  weights, hidden tasks. Re-derive knobs from the first screener feedback; don't assume 16k/32k
  numbers transfer.
