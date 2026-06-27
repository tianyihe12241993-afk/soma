# Top-miner dissection under the WEIGHTED-TOKEN regime — approach + how to break them (2026-06-26)

_Scraped each top miner's comp-108 detail page (per-task token splits + scores), via scripts/dissect_top_miners.py.
weighted = 1·input + (1/3)·cached + 3·output. snap 164607._

## 1. The data (45 non-screener tasks each)
| miner | rawRatio | cache% | out% | wtd/rawW | meanSc | #score>1 | #score<0 | flips | #inflate(<1×) |
|---|---|---|---|---|---|---|---|---|---|
| 5DCnA57 (#1, 0.697) | 1.18× | 91.1% | 0.9% | 0.410 | 0.664 | 22 | **6** | 5 | 11 |
| king 5Ggq (#2, 0.673) | 1.64× | 85.5% | 1.2% | 0.454 | 0.605 | 21 | 9 | 6 | 5 |
| 5DFvym (#3, 0.556) | 1.73× | 87.9% | 1.1% | 0.436 | 0.489 | 18 | 9 | 5 | 4 |
| 5HdTr7 (#4, 0.551) | 1.07× | 94.1% | 0.8% | 0.389 | 0.505 | 15 | 14 | 4 | 18 |
| 5H6919 (#5, 0.537) | 1.79× | 87.8% | 1.1% | 0.437 | 0.438 | 17 | 12 | 3 | 4 |
| 5EkCiY (#6, 0.509) | 1.54× | 86.4% | 1.2% | 0.447 | 0.452 | 19 | 13 | 4 | 5 |
| m25 (OURS) | 1.61× | 83.7% | 1.1% | 0.464 | 0.401 | 16 | 12 | 4 | 5 |
| m12 (OURS, LIVE) | 1.62× | **53.9%** | 1.1% | 0.662 | 0.294 | 13 | 16 | 7 | 10 |

## 2. How they approached it (inferred)
- **EVERY top miner is cache-stable: cache% 85-94%.** m12 (54%) is the lone outlier → exactly why it cratered. Cache% is THE
  discriminator; the leaders all keep a byte-stable prefix (don't rewrite old turns) so it caches at 1/3 weight (wtd/rawW ~0.39-0.46).
- **They compress LIGHTLY** (raw ratio 1.07-1.8×) — near-passthrough to mild. Output is ~1% for all (the 3× weight is moot in aggregate).
- **The ranking is driven by CONSISTENCY (fewest negative/breaking tasks), not by compression.** #1 has the FEWEST negatives (6);
  rank degrades as negatives rise (king 9 → … → m12 16). More compression did NOT help: king compresses 1.64× (more ratio bonus)
  but has 9 negatives vs #1's 6 → king scores LOWER. The marginal trade "compress more → +ratio bonus but +breaks" is net-negative.
- **There is an OPTIMAL lightness.** 5HdTr7 (#4) is the lightest (1.07×, 94% cache) but **inflates on 18 tasks** (ratio<1× = output
  bigger than native) → 14 negatives → only #4. **5DCnA57 (#1) sits at the sweet spot: 1.18× — light enough for max cache+consistency,
  compressed enough to NOT inflate** (only 11 inflate, 6 neg). Too light (inflate) trips the savings/inflation penalty; too aggressive
  (king) trips breaks. #1 threads it.

**Approach summary: near-passthrough + stable prefix (high cache) + just enough compression to avoid inflation + minimal disruption
(→ consistency). 5DCnA57 = the cleanest expression (lightest non-inflating).**

## 3. How to break them — honest read
The top is a TIGHT cluster (wtd/rawW 0.39-0.46, cache 85-94%, mean 0.44-0.66) that has converged on near-passthrough+cache-stable.
The separating variable is CONSISTENCY (#negatives), which is LARGELY AGENT-SIDE (same qwen3-coder; lighter compression = less
disruption = fewer breaks, but residual break variance is sampling). So beating #1 deterministically is hard. The levers:
1. **Be the lightest NON-inflating cache-stable miner (match 5DCnA57's 1.18× / 91% / no-inflate).** This is the highest-consistency
   point. Our np1 (m26) is near-passthrough; tune NP_RESULT_CAP so it lands ~1.2× (light but NOT inflating like 5HdTr7). This alone
   should JOIN the top cluster (~0.5-0.7), a huge jump from our m25 0.449 / m12 0.130.
2. **Cache-stable LOSSLESS dedup (the under-exploited edge).** The leaders compress LIGHTLY and do NOT appear to dedup hard
   (5DCnA57 1.18× = barely). Exact-repeated blocks (re-read files, re-run tests) can be replaced by `[[BLOCK N]]` back-refs —
   LOSSLESS (agent loses no info → NO new breaks) yet reduces tokens → MORE ratio bonus that king pays for with breaks but dedup
   does NOT. CAVEAT: under weighted tokens, repeated content sitting in the stable prefix is ALREADY cached (1/3), so dedup's
   weighted gain is MODEST (you save 1/3-weight tokens), and the dedup must be DETERMINISTIC or it busts the very cache it rides.
   Net: a real but modest edge — get the ratio bonus the leaders forgo, without their break cost. Worth prototyping for np2.
3. **Consistency lottery** — not a lever (agent-side); don't chase it.

**Verdict: realistic goal = JOIN the top cluster via near-passthrough+cache-stable (np1/m26 should). Beating #1 specifically needs
the lossless-dedup ratio edge (modest, cache-discounted) on TOP of #1's lightness+consistency. m26's scored result calibrates the
cap; np2 = m26 + cache-stable deterministic lossless dedup, IF m26 confirms the cluster.** (Strategy to Codex-red-team at the np2 build fork.)

## 4. Where WE stand
m12 (54% cache) is the cratered outlier. m25 (84% cache, 1.61×) is ALREADY near the leaders' profile but with 12 negatives (mean
0.401) — it compresses like king but with our extra breaks. **m26 (np1, near-passthrough, screening) is built to be the lightest
cache-stable one** — the right shape. The open platform questions (m26 scored): does it land at ~1.2× non-inflating (vs 5HdTr7's
over-light inflate trap), and how many negatives (consistency)?
