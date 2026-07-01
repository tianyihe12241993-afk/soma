# SCOREBOARD — comp 108 (CoT-Compression-4)

## ★★★ 2026-06-30 ~11:55 — ✅ BOTH KINGS DQ'd (owner rule) → PROJECT 23.8% (snap 115258; both still show scored, DQ pending)
Owner oli|SOMA: top-2 (5EeUAVZ 0.852 + 5DZLFZj 0.728) used unapproved `#source line N` → **cannot pass review**. Prompt list now FROZEN mid-comp.
Projection with both excluded (category-mean proxy):
| element | weight | winner | ours? |
|---|---|---|---|
| Overall | 1.0 | 5DCnA57 0.703 | — |
| **Pair(E,M)** | 1/6 | **np2 0.951** | ✅ RECLAIMED (old king had it) |
| Pair(E,H) | 1/6 | 5GgVXz 0.760 | — |
| **Pair(M,H)** | 1/6 | **np3 0.599** | ✅ |
| Single(E) | 1/12 | 5EKyJnby 1.079 | — |
| **Single(M)** | 1/12 | **np2 0.849** | ✅ |
| Single(H) | 1/12 | 5GgVXz 0.676 | — |
**SHARE: 5DCnA57 57.1% · np2 14.3% (Pair(E,M)+Single-M) · 5GgVXz 14.3% · np3 9.5% (Pair(M,H)). OURS = 23.8%** (pending the platform applying the DQ).
- nocap (5FXAR4) 0.416 = FAILED (E0.984/M0.266/H0.032; 17% breaks, uncapped-tail crater — predicted). DISCARD. m12 0.130, m26 0.610 LIVE.

## ★★★ 2026-06-30 ~08:05 — ⚠️ NEW KING 5EeUAVZ → OUR SHARE 0% [SUPERSEDED by 11:55 — kings DQ'd] (snap 075706; `reports/new_king_5EeUAVZ_analysis.md`)
**New scored miner `5EeUAVZDbk2j…` = 0.852 (E1.076/M0.959/H0.535) wins 5 of 7 elements = 90.5%.** Took Pair(M,H) from np3 AND Single-M from np2.
| element | weight | winner | ours? |
|---|---|---|---|
| Overall | 1.0 | **5EeUAVZ 0.856** | — (was old king 0.728) |
| Pair(E,M) | 1/6 | **5EeUAVZ 1.017** | — (lost) |
| Pair(E,H) | 1/6 | **5EeUAVZ 0.805** | — |
| Pair(M,H) | 1/6 | **5EeUAVZ 0.747** | ❌ LOST (np3 had it) |
| Single(E) | 1/12 | 5EKyJnby 1.225 *(evaluating)* | — |
| Single(M) | 1/12 | **5EeUAVZ 0.959** | ❌ LOST (np2 0.849 had it) |
| Single(H) | 1/12 | 5GgVXzUB 0.676 | — |
**SHARE: 5EeUAVZ 90.5% · 5EKyJnby 4.8% · 5GgVXz 4.8%. OURS = 0%** (was 14.3%). np2 0.684 / np3 0.682 still LIVE+scored (unchanged) — lost the elements, not points.
- **King = "np2 but LIGHTER (1.33x vs 1.49x) + CLEANER": breaks 9.0% RUNS (np2 12.4%), flips 40% RUNS (np2 30%); savings+cache IDENTICAL.** Validates fuller-keep (cap32/nocap) + salience. Reclaim target = Single-M (need M>0.959). Detail + task-level flip/break diffs: `reports/new_king_5EeUAVZ_analysis.md`.

## ★★★ 2026-06-27 ~08:57 — np3 SCORED; PORTFOLIO (np2+np3) = 23.8% (snap 085653, 70 legit; make reward) [SUPERSEDED by 06-30 above]
np3 (5F9ZRe, cap 28k) total 0.682, E0.859/M0.828/**H0.369** (field-HIGHEST Hard). vs np2: H **+0.196**, E **−0.193**, M −0.021, total −0.002.
The cap is a ~ZERO-SUM **E↔H lever** (low cap=high E/low H = np2; high cap=high H/low E = np3). But on SEPARATE hotkeys it's
ADDITIVE — np3 won the M+H corner np2 couldn't.
| element | weight | winner | ours? |
|---|---|---|---|
| Overall | 1.0 | 5DCnA57 0.703 | — |
| **Pair(E,M)** | 1/6 | **np2 0.951** | ✅ |
| Pair(E,H) | 1/6 | 5GgVXzUB 0.760 | — (NEW rival, E~0.844/H0.676 = balanced-high) |
| **Pair(M,H)** | 1/6 | **np3 0.599** | ✅ NEW |
| Single(E) | 1/12 | 5DCnA57 1.067 | — (np2 1.052, −0.015, near-free) |
| **Single(M)** | 1/12 | **np2 0.849** | ✅ |
| Single(H) | 1/12 | 5GgVXzUB 0.676 | — (np3 0.369 far) |
**SHARE: 5DCnA57 61.9% · np2 14.3% · 5GgVXzUB 14.3% (NEW) · np3 9.5%. OURS = np2 14.3% + np3 9.5% = 23.8%** (from 14.3%).
- KEY STRATEGY: the reward model rewards SPECIALISTS (corners), not balance. np2=E+M corner, np3=M+H corner. A "balanced-cap" np4
  (middle) would win NO corner → adds nothing. The CAP lever is now EXHAUSTED (we own both its endpoints' corners).
- TO GROW past 23.8%: the remaining high-value elements (Overall 57%, Pair(E,H), Single-H) need a miner HIGH on E AND H at once
  (5DCnA57/5GgVXzUB have it). Our cap lever gives E OR H (zero-sum) → can't. Needs a NEW mechanism (better extractive: keep big-block
  critical content WITHOUT the E-wander) — np4 candidate for OVERALL, but UNCERTAIN (np3 showed Hard needed the EXTRA content, not
  just better-selected 16k). Near-free: Single-E (−0.015, may flip on re-draw → 28.6%). DEFEND 23.8% (np2+np3 live; watch 5GgVXzUB).
- m12 (5Dz7) 0.130 LIVE/untouched. np2 (5CPbtf) + np3 (5F9ZRe) LIVE = 23.8%. Detail: reports/cache_stable_design.md §15.

## ★★★ 2026-06-27 ~01:30 — np2 SCORED #2; WINS Pair(E,M)+Single-M = 14.3% OF THE POOL (snap 012850, 64 legit; make reward)
From m12 cratered (0% post-regime) → np2 **14.3%**. np2 (5CPbtf, upload_miner_np2.py) total 0.684 (E1.052/M0.849/H0.173), #2 Overall.
| element | weight | winner | our miner? |
|---|---|---|---|
| Overall (E,M,H) | 1.0 | 5DCnA57 0.703 | — (np2 #2, 0.684, gap on Hard) |
| **Pair (E,M)** | 1/6 | **np2sub (OURS) 0.951** | ✅ |
| Pair (E,H) | 1/6 | 5DCnA57 0.695 | — |
| Pair (M,H) | 1/6 | king 5Ggq 0.555 | — (np2 H drags it) |
| Single (E) | 1/12 | 5DCnA57 1.067 | — (np2 #2, 1.052, −0.015 = contested/noise) |
| **Single (M)** | 1/12 | **np2sub (OURS) 0.849** | ✅ |
| Single (H) | 1/12 | 5DtEz 0.342 | — (np2 0.173 mid) |
**Incentive share: 5DCnA57 71.4% · np2 (OURS) 14.3% · king 9.5% · 5DtEz 4.8%.**
- WIN: np2 owns the E+M corner (top-tier Easy 1.052 + Medium 0.849). m26/np1 #4 (0.610), m25 0.449, m12 0.130 (LIVE).
- GROW levers (all gated on HARD — np2 H=0.173 is the cap): Overall (57%, gap 0.019 on Hard), Pair(E,H)/Pair(M,H) (Hard), and the
  near-free Single-E (np2 1.052 vs 5DCnA57 1.067, −0.015 → may flip on a re-draw). Lifting Hard (keep the biggest-task results fuller
  without losing E+M) is the path to Overall. DEFEND 14.3%: keep np2 live (our income now); watch for a higher-E+M rival.
- np2 = our LIVE BEST now. Full: reports/cache_stable_design.md §12-13. Detail: dissect np2 — cache 93%, ratio 1.49×, 11 neg (Hard over-compress on 315@2.57×/296@3.27× + wander).

## 🚨 2026-06-26 ~16:25 — SCORING REGIME CHANGED → WEIGHTED TOKENS (commit b79fcaee). FULL RE-SCORE. (snap 162500, 115 miners)
`weighted = 1·input + (1/3)·cached + 3·output`; FLIP 4→2; BREAK −4. **Cache-stability now dominates.** ALL boards below are RAW-TOKEN-ERA (superseded).
| miner | total | E | M | H | status | note |
|---|---|---|---|---|---|---|
| **5DCnA57 (NEAR-PASSTHROUGH)** | **0.697** | 1.067 | 0.719 | 0.324 | scored | **FIELD #1** — light/cache-stable wins now |
| king 5Ggq | 0.673 | 0.924 | 0.848 | 0.261 | scored | #2 (was 0.957) |
| 5DFvym (old king) | 0.556 | 0.901 | 0.593 | 0.196 | scored | |
| **m25 (OURS, 5GpB36)** | **0.449** | 0.917 | 0.289 | 0.169 | scored | **our BEST now (#9 of 54)** |
| 5DtEz | 0.383 | 0.796 | 0.001 | 0.342 | scored | Medium collapsed |
| 5GBPFA (Easy spec) | 0.373 | 0.940 | 0.121 | 0.091 | scored | |
| **m12 (OURS, 5Dz7) LIVE** | **0.130** | 0.364 | −0.442 | 0.067 | scored | **CRATERED (was 0.768)** — cache-busting harvest |
| **m26 (OURS, 5Ekcy) np1** | _pending_ | — | — | — | **SCREENING** | NEW cache-stable near-passthrough candidate (the recovery bet) |
- **We win NOTHING now** (m12 lost Single-H; under weighted tokens Hard is LOW for ALL, field max 0.342). Our best = m25 0.449 (#9 of 54).
- **WHY m12 cratered:** 56% cache vs king's 85% — its harvest rewrites the prefix → cache busts → weighted ratio collapses → Medium went negative.
- **m26 (np1) is the recovery bet** (expected band 0.130 < m26 ≤ ~0.697). Full mechanism: state/CURRENT.md (top) + reports/cache_stable_design.md.

## ★ 2026-06-24 ~22:20 — [RAW-TOKEN ERA, SUPERSEDED] NEW KING 5GgqHgSdxgAL = 0.957 (did NOT collapse). OUR SHARE → 4.8%.
| miner | total | E | M | H | status | incentive share |
|-------|-------|---|---|---|--------|-----------------|
| **5Ggq (NEW KING)** | **0.957** | 0.858 | **1.281** | 0.727 | scored/qual | **85.7%** |
| 5DtEz84j | 0.714 | 0.837 | 0.499 | 0.813 | scored | 9.5% (wins Pair E,H) |
| **m12 (OURS, 5Dz7)** | 0.768 | 0.412 | 0.953 | **0.919** | scored/LIVE | **4.8% (wins Single-H ONLY)** |
| old king 5DFvym | 0.781 | 0.812 | 0.596 | 0.934 | scored | 0% (dethroned) |

**7-element winners now:** 5Ggq takes Overall + Pair(E,M) + Pair(M,H) + Single(E) + Single(M);
5DtEz takes Pair(E,H); **m12 keeps ONLY Single(H)** because Hard 0.919 is field-best (next 5DtEz 0.813).
⚠️ Our ENTIRE 4.8% rests on Hard 0.919 being field-best — if anyone beats it, we go to 0%.
5Ggq profile: 6/250 breaks, 85% cache, 4.03x weighted-ratio, 56 steps. Its +0.189 over m12 = our two known
gaps (break/run-variance + inflation), same as old-king diagnosis but bigger. Snapshots + analysis:
data/raw/platform_results/2026-06-24/newking_5Ggq_perrun.json, reports/m12_runvariance_perrun.md.

---

# SCOREBOARD

## ★ COMP 108 (CoT-Compression-4) — current standings (2026-06-24, scrape 070944 — all SCORED)
_Caveat: platform temporally noisy; an EVALUATING score is NOT final — see the 5DAh2rUM collapse below._
| # | miner | total | Easy | Medium | Hard | status / note |
|---|-------|-------|------|--------|------|------|
| 1 | 5DFvymSeEw (king) | 0.780 | 0.812 | 0.934 | 0.596 | scored. beats us ONLY on Easy |
| 2 | **m12 (us)** | **0.768** | 0.412 | **0.953** | **0.919** | scored. 0.012 from #1; field-best M AND H; LIVE |
| 3 | 5DtEz84j | 0.714 | 0.837 | 0.499 | 0.813 | scored |
| 4 | 5GYxeJjd | 0.661 | 0.117 | 0.661 | 0.569 | scored |
| ✗ | 5DAh2rUM (failed king) | **0.051** | 0.853 | 0.976 | **−3.600** | scored. WAS 0.887 evaluating → Hard COLLAPSED |
**5DAh2rUM COLLAPSE (the big lesson):** showed 0.887 #1 while EVALUATING (E/M only), then Hard finished → **H=−3.600**
(its LIGHT compression, 1.41×, broke nearly every Hard run) → total crashed to 0.051. VALIDATES: (1) never trust
evaluating scores; (2) m12's aggressive harvest → **Hard 0.919 is a massive durable moat** (field-best by a mile;
the light competitor got −3.6); (3) "go lighter for reliability" is DANGEROUS, not promising — the reliability A/B
is shelved (the one light miner imploded on Hard; + EXP-1b lighter broke more). 7-element: king wins Overall+E+
(E,M)+(E,H); m12 wins M+H+(M,H) ≈19%. (E,H) is close — m12 needs Easy≥0.49 to take it (we lose by 0.038). HOLD m12.

---
_Below: comp-107 (COMPLETED, different task set — historical). Hand-maintained; `make reward` writes the live
machine version. Columns: total / Easy / Medium / Hard._

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

## ⚠️ UPDATE 2026-06-22 — TOP MINERS FAILED REVIEW → standings reshuffled
Dashboard re-check (per-miner comp-107 pages; a new competition cycle has opened so default /dashboard moved):
**FAILED REVIEW (excluded from reward): t1 5EkiFXSR (1.460), t2 5E7hCCzj (1.436), t3 5FbqgypX (1.415=Medium
king), t4 5DhHqmB1 (1.410=Hard king), t5 5GEUZcud (1.355), t7 5ERdwbn5 (1.263).** Survivors: t6 5G6J5dA1
(1.335), t8 5EPkREJ9 (1.256), t9 5CJs9EmL (1.222), t10 5GgUhFiG (1.158) + our miners.

**Recomputed element leaders among VALID miners (tracked set; ranks 11+ untracked → confirm vs full board):**
| element | leader | score | m7 (us) |
|---|---|---|---|
| Overall (E,M,H) | t6 | 1.334 | **#2, 1.276** |
| Medium | t9 | 1.423 | **1.421 (≈TIE — +0.003 wins)** |
| (M,H) pair | t6 | 1.361 | **#2, 1.351** |
| Hard | t6 | 1.525 | #3, 1.281 |
| Easy | t10 | 1.373 | 1.127 |
| (E,M) pair | t9 | 1.321 | #3, 1.274 |
| (E,H) pair | t6 | 1.403 | 1.204 |

**m7 is now top-tier and review-PASSING.** New effective king = **t6 (1.335, ratio only 2.88× — NOT a deep
compressor; wins via Hard 1.525 + balance)**. ⚠️ WHY the top failed = unknown (NOT ratio-driven: t10 survived
at 5.24×, t5 failed at 2.40×) → investigate before aggressive-compression bets.
