# Cross-miner compression-ratio reference (comp-108)

_Recorded 2026-06-26. Source: per-task/per-run platform JSONs under data/raw/platform_results/ + /tmp/5DCnA57_comp108_detail.json.
Ratio = sum(tokens_without_compression) / sum(tokens_with_compression) over the 50 (45 non-screener for 5DCnA57) tasks.
savings = 1 − with/without. inflate# = tasks where the miner used MORE tokens than baseline (ratio < 1)._

## VERDICT: ratio is a SOLVED axis for us — do NOT upgrade. m12 ties the king (1.61×) exactly.
The king's lead over m12 is 100% pass/break/flip + consistency, NOT compression. Both directions off m12's ratio are
closed: harder = wander/break trap (m17/m18/m20b); lighter = savings PENALTY (5DCnA57 live proof). m12 sits in the
optimal safe band (~1.6×, ~38% savings) — above the ~20% penalty floor, below the over-compression break zone.

## Apples-to-apples cohort (SAME ~80.9M baseline — directly comparable)
| miner | agg ratio | median | mean | savings | inflate# | E / M / H | total |
|---|---|---|---|---|---|---|---|
| **m12 (OURS, LIVE)** | **1.61×** | 1.62 | 1.75 | **37.9%** | 10 | 0.412 / 0.953 / 0.919 | 0.768 |
| king 5Ggq | 1.61× | 1.65 | 1.64 | 37.8% | 5 | 0.858 / 1.281 / 0.727 | **0.957** |
| old-king 5DFvym | 1.71× | 1.65 | 1.74 | 41.6% | 4 | 0.812 / 0.596 / 0.934 | 0.780 |
| 5DtEz | 1.79× | 1.75 | 1.84 | 44.3% | 6 | 0.837 / 0.499 / 0.813 | 0.714 |

**Reads:** (1) **m12 === king on ratio (1.61×).** We are not behind. (2) The HARDER compressors (5DtEz 1.79×, old-king
1.71×) score the LOWEST totals (0.714, 0.780) — more ratio did not help them win. (3) The ratio term is minor:
1.61×→1.79× is worth only `0.5·ln(1.79/1.61) ≈ +0.05/task`, below the ~0.25 measurability gate and ~4× short of the
+0.189 gap to the king. Score is dominated by base outcomes (pass-pass +1, FLIP +4, BREAK −4, fail-fail 0).

## Non-comparable cohort (ballooned/penalized baselines — DO NOT read the ratio as "harder compression")
| miner | agg ratio | savings | baseTok | note |
|---|---|---|---|---|
| 5CwZBKyL | 3.39× | 70.5% | 404.6M | **ARTIFACT** — agent WANDERED to a 404M-token native trajectory → inflated denominator. The wander signature, not real compression. Rejected candidate. |
| m22 (ours) | 1.55× | 35.4% | 404.6M | ballooned baseline (m22's agent ran longer); ratio not comparable to the 80.9M cohort. |
| 5DCnA57 (new cand) | 1.18× | 15.6% | 377.4M | near-PASSTHROUGH light compressor (inflates 11/45) → eats a savings PENALTY (Easy −0.435, Hard −0.581) → effective total 0.701 < m12. Live proof the "go light" lever is penalty-capped. |

## Method caveat
`tokens_without_compression` (the baseline) is NOT uniform across miners — it tracks each miner's own agent-trajectory
length, which varies because the compressed context changes what the agent does. So **cross-miner agg-ratio is only
apples-to-apples within a shared-baseline cohort** (the 80.9M group above). The SCORE uses each run's own
`ln(without/with)`, so for OUR decisions m12's own baseline is the relevant one. The 80.9M cohort is the trustworthy comparison.

## Bottom line
m12's compression ratio is field-leading-competitive (ties the king) and in the safe band. **No ratio upgrade is
warranted** — it is negative-EV in both directions and immaterial to the score vs pass/break/flip. Any future share
growth comes from pass/break/flip behavior (m25 coin-flip) or board reshuffling, never from ratio.
