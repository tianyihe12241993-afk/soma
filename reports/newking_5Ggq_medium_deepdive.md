# New king 5Ggq — why its Medium is so high (2026-06-24)

5Ggq (0.957, new king) Medium = **1.281** vs m12 0.953. Deep-dive on the derived Medium set
(category map solved from 10 miners' per-task scores → config/comp108_category_map_derived.json;
APPROXIMATE — leaderboard E/M/H doesn't reconcile to a plain mean for all miners, but 5Ggq's own
fit is tight: M 1.281→1.260). 19 Medium tasks, 5Ggq vs m12 per-run mechanics.

## Medium: 5Ggq +1.260 vs m12 +0.812 (gap +0.448/task) — it's STABILITY, not capability
| mechanic (Medium subset) | 5Ggq | m12 |
|---|---|---|
| break-runs (−4) | **1** | **12** |
| flips (+4) | 2 | **4** |
| cache | 86% | 54% |
| weighted-ratio | 3.56× | 2.77× |

**m12 is MORE capable on Medium** (flips 4 vs 2; wins the flip tasks outright) but loses the
category to 12 break-runs + cache churn.

### Where 5Ggq wins (all breaks / cache-churn):
django-13810 +3.12 (m12 3brk→0), sympy-23262 +2.13 (3→1), sympy-15349 +2.09 (2→0),
django-15161 +1.71 (m12 14% cache/0.7× ratio → 5Ggq 89%/1.4×), django-11095 +1.10,
sympy-11618 +1.08, django-13033 +0.90, django-11551 +0.74.

### Where m12 wins (our harvest is stronger — FLIPS):
sympy-23824 m12 +3.01 flip (king +1.29), django-14017 m12 +2.56 flip (king +0.88),
django-13343 m12 +1.82 (king +0.88).

## STRATEGIC TAKEAWAY: Medium is m12's MOST winnable category
If m12's 12 Medium break-runs became passes (≈ +5 each over ~95 Medium runs ≈ +0.63/task),
m12 Medium → ~1.44, ABOVE 5Ggq's 1.26 — the raw flip power is already there. Contrast Easy
(m12 0.412 = genuine decisiveness/capability gap, dead lever). Medium = where break-stability +
cache-stability fixes convert DIRECTLY into beating the king. The same two gaps (break-stability,
cache) — and Medium is where the payoff is largest because we already out-flip the king there.

CAVEAT: category map is derived/approximate; a few task assignments may be wrong, but the mechanic
(m12 12 breaks vs 5Ggq 1 on Medium; m12 out-flips) is robust to small misassignment.
