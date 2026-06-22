# Gap analysis — our 5 submissions vs the leaders
_computed 2026-06-21 from data/latest/miner_detail.json (per-task scrape). 45 scored tasks each (5 screeners excluded)._

## Our submissions (registry mapping — note your v18/v22 labels are swapped vs config/miners.yaml)
| hotkey (8) | registry | total | avg ratio | broke baseline | recovered | neg-score tasks | barely-compressed (<2×) |
|---|---|---|---|---|---|---|---|
| 5GsHHNme | m7 / v11.1 | **1.279** | 2.99× | 1 | 5 | 3 | 8 |
| 5EF8nHth | m8 / v15 | 1.159 | 2.84× | 0 | 2 | 2 | 10 |
| 5CFqU2Ss | m9 / v22 *(you said v18)* | 0.937 | 2.64× | 3 | 2 | 9 | 14 |
| 5GL4Kxda | m10 / v18 *(you said v22)* | 0.916 | 2.66× | 2 | 1 | 8 | 15 |
| 5F26J6aG | m11 / v24 | 1.038 | 2.70× | 1 | 3 | 7 | 12 |

## Category scores (ours vs element leaders)
| | Easy | Medium | Hard |
|---|---|---|---|
| **m7 (best)** | 1.127 | **1.421** | 1.281 |
| m8 | 1.057 | 1.183 | 1.230 |
| m11 | 0.943 | 1.030 | 1.135 |
| m9 | 1.165 | 0.931 | 0.728 |
| m10 | 1.029 | 1.073 | 0.653 |
| 5EkiFXSR (overall) | 1.171 | 1.480 | 1.712 |
| 5FbqgypX (medium) | 1.192 | **1.620** | 1.421 |
| 5DhHqmB1 (hard) | 1.347 | 1.127 | **1.751** |

## THE main gap — under-compression (highest leverage)
On the **36 tasks both m7 and the overall leader pass**, score ≈ `1 + 0.5·ln(ratio)` holds:
- leader: **4.89×** → avg score **1.716**
- m7:    **3.03×** → avg score **1.559**

The ~0.16/task gap on shared passes is **entirely the token-bonus from deeper compression** — not the agent solving more. m7 is leaving compression on the table: 8 tasks under 2× and most others at 2–3×. Matching ~5× on the safe tasks would lift m7's per-task ~1.56 → ~1.72, pushing its total from 1.279 toward ~1.43 (would contend for Medium and overall).

Why m7 is here: `TARGET_TOKENS = 8_000` ("8k harvest"). Leaders target lower. m7 only breaks 1/45 baselines — it is *very* safe, i.e. it has headroom to compress harder before risking passes.

## Second gap — a few catastrophic single tasks (Hard)
Tasks where 5EkiFXSR scores big and m7 doesn't:
- `django__django-14999`: leader **4.008** vs m7 1.096 (m7 fails this baseline ✗→✗)
- `django__django-11555`: leader 1.520 vs m7 0.448
- `sympy__sympy-17139`:   leader 0.893 vs m7 **−0.246** (m7 BROKE a passing baseline ✓→✗)

These 3 explain much of the Hard gap (m7 1.281 vs king 1.751). The Easy gap is smaller; Medium (1.421 vs 1.620) is our closest reward.

## m9 / m10 / m11 (the flip-routing bets) — strictly worse than m7
Flip-routing did NOT improve compression ratio (still 2.6–2.7×) and made things worse: m9/m10 broke 2–3 baselines and produced 8–9 negative-score tasks each. Confirms the standing decision: abandon flip variants; m7 is floor and ceiling.

## Recommendation (analysis only — miner edits happen outside this repo)
1. **Compress harder on the safe tasks.** Lower m7's target toward ~5–6k on tasks it already passes with margin; the per-task token bonus is the dominant, formula-confirmed lever. Validate that passes hold (local validation under-detects breaks — see RISKS).
2. **Triage the 3 Hard losers** (14999, 11555, 17139) — esp. sympy-17139 where compression broke a passing baseline.
3. **Stop iterating on flip-routing** — the detail confirms it adds broken baselines + negative tasks without ratio gains.
