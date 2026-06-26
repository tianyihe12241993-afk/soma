# m20b-v2 SCORED verdict + unified gap theory (2026-06-24)

## Verdict: m20b-v2 = 0.715, REJECTED (worse than m12 0.768 on ALL three)
E 0.172 (vs 0.412), M 0.650 (vs 0.953), H 0.808 (vs 0.919). Dented our moat (Hard). m12 stays LIVE.
m20b-v2 = m12 + aggressive superseded-view BLIND collapse + recency guard + freq gate. snapshot:
data/raw/platform_results/2026-06-24/m20bv2_5DADz_perrun.json.

## The paradox: it achieved BOTH proposed fixes yet lost
| | mean | break-runs | cache | weighted-ratio | fresh-input |
|---|---|---|---|---|---|
| m12 | 0.768 | 17 | 55% | 2.96x | 429k |
| m20b-v2 | 0.715 | 10 | 83% | 3.54x | 175k |
| king 5Ggq | 0.957 | 6 | 85% | 3.61x | 132k |
m20b-v2 cut breaks 17->10, raised cache 55->83%, nearly MATCHED king's full token profile
(fresh input 175k vs 132k; weighted 501k vs 454k). Still scored 0.24 BELOW king and below m12.

## Why it lost (raw-run classification): content-loss
Regressions = flip-loss 1, new-break 4, pass-degrade 11. The collapse is BLIND content removal,
right ~half the time:
- LOST (removed signal): django-14017 [4.2,0.1,4.2,4.3,0.1]->[0,0,0.1,0.1,0] (3 flips wiped);
  django-12774 [2.1,1.8,2.3,-3.2,1.9]->[-3.2,-3.2,-3.2,-3.2,2.2] (passes->4 breaks);
  django-15037, django-13820, django-15375, django-12050 (stable pass -> a break).
- GAINED (removed noise): django-13810 (fixed 2/3 breaks), django-11740 (->king-stable),
  django-11149 & django-13121 (fail-fail -> flips).
Harm(15) slightly > help(14) => net -0.05. Collapse can't tell noise from needed content.

## UNIFIED THEORY (two facts -> the answer)
1. m20b-v2 matched king's cache/weighted profile but scored 0.24 lower => cache & weighted-ratio
   are NEAR-WORTHLESS as direct objectives (corr(cache,score)~0.01). Score = pass/break.
   *Ratio-bonus chasing is FALSIFIED, not just argued.*
2. King sends 132k fresh input vs m12 429k at ~equal TOTAL tokens (999k vs 994k) => king is NOT
   compressing more; it KEEPS the same content but stably CACHED (0.37x weighted) and never re-drops.
=> The ONLY lever that scores is KEEPING the content the agent needs (no breaks); cache-stability
   is what makes "keep more content" AFFORDABLE (cached = 0.37x weighted, so savings ratio stays up).
m12 drops aggressively BECAUSE its churn means kept content isn't cached (full weighted cost). If kept
content were frozen+cached, m12 could keep more -> fix breaks -> without tanking the ratio.
m20b-v2 confirmed the mechanism: freeze->cache up (83%), but it froze a STUBBED/lossy version->lost
content->broke. Therefore: FREEZE WITHOUT DROPPING = keep m12 content + cache it = king's recipe.

## DESIGN this points to (NOT compress-more, NOT chase-cache, NOT remove-redundancy -- all falsified)
**Freeze-on-emit with m12's FULL content retention:** compress each turn's content ONCE as it ages
out, freeze those exact bytes, never re-compress earlier turns; KEEP the rich content m12 selects
(the harvest that wins Hard + Medium-flips). Do NOT stub superseded views (that craters Hard, per
m20b-v2). Expected: cache->~85% with ZERO content loss -> fresh-input/weighted drop (ratio safe) +
eliminating re-drop removes the churn behind m12's 17 breaks, without losing Hard/Medium-flip edge.

## Falsified directions (do not revisit)
- ratio-bonus via redundancy removal (m20b-v2): net-negative, craters Hard.
- aggressive/blind collapse or stubbing superseded views: removes needed content -> breaks.
- optimizing cache% or weighted-ratio as ends in themselves: ~0 score correlation.
