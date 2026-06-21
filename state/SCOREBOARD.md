# SCOREBOARD

_Hand-maintained snapshot; `make reward` writes the live machine version to data/latest/ + reports/.
Columns: total / Easy / Medium / Hard. As of ~2026-06-21 (mid-eval, provisional)._

## Our miners
| slot | ver | total | Easy | Medium | Hard | status |
|------|-----|-------|------|--------|------|--------|
| m7 | v11.1 | **1.279** | 1.127 | 1.421 | 1.281 | scored — BEST |
| m8 | v15 | 1.159 | 1.057 | 1.183 | 1.230 | scored (Medium leaked) |
| m3 | v6 | 1.080 | 0.979 | 1.368 | 0.887 | scored |
| m6 | v8 | 1.034 | 0.791 | 1.241 | 1.057 | scored |
| m2 | v4 | 1.003 | 0.832 | 1.132 | 0.841 | scored |
| m1 | v2 | 0.884 | 1.047 | 0.376 | 1.239 | scored |
| m11 | v24 | 1.038 | 0.943 | 1.030 | 1.135 | scored — below m7 |
| m9 | v22 | 0.937 | 1.165 | 0.931 | 0.728 | scored — Medium crushed |
| m10 | v18 | 0.916 | 1.029 | 1.073 | 0.653 | scored — below m7 |
| m5 | v7 | -2.507 | -2.83 | -3.30 | -1.41 | broken/negative |

> **m9/m10/m11 (flip bets) finished eval 2026-06-21 — all below m7.** Medium leaked to 0.93–1.07
> (vs m7 1.421), Hard didn't compensate. Confirms: flip-routing was a net downgrade; m7 is the floor+ceiling.

## Reward element leaders (rivals; failed-review excluded) — refreshed 2026-06-21
| element | winner | score |
|---------|--------|-------|
| Overall (E,M,H) | 5EkiFXSR | 1.454 |
| (M,H) pair | 5EkiFXSR | 1.596 |
| (E,H) pair / Hard | 5DhHqmB1 (king) | 1.549 / 1.751 |
| (E,M) pair / Medium | 5FbqgypX | 1.406 / 1.620 |
| Easy | 5GgUhFiG | 1.373 |

Incentive split: 5EkiFXSR ~66.7%, 5FbqgypX ~14.3%, 5DhHqmB1 ~14.3%, 5GgUhFiG ~4.8%.
**Us:** win nothing. Closest = Medium (m7 1.421) — now 3rd+ behind 1.620 and others.
_(machine-truth: data/latest/category_winners.json — regenerate with `make reward`.)_
