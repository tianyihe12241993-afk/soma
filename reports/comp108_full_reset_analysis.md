# Comp-108 Full-Reset Strategic Analysis

**Author:** Chief strategist (full-reset analysis)
**Date:** 2026-06-25
**Authoritative snapshot:** `data/raw/dashboard/2026-06-25/192615_leaderboard.json` (87 miners, 40 scored / 41 eligible under the script filter)
**Per-run truth:** `data/raw/platform_results/{2026-06-24,2026-06-25}/*_perrun.json` (8 miners with per-run detail)
**Reward math:** `scripts/compute_reward_elements.py` logic (reproduced in `/tmp/q3_reward.py`)
**All numbers below were independently re-computed this session from the real files; reproduction commands and verification notes are in the appendix. Numbers I could not verify are explicitly flagged.**

---

## BLUNT VERDICT

**Active dethroning of comp-108 is unrealistic — there is no compliant, testable single-miner lever that clears any reward-element threshold, and I am recommending we STOP active comp-108 miner work and shift to next-round preparation.** We currently own exactly one of seven reward elements — Single-Hard (m12 H = 0.9193, +0.107 cushion) = 4.76% of the pool — and every active path to more requires either raising Medium or Hard above m12 (no lever we have ever scored does this: all 7 of our experimental hotkeys drop both M and H) or raising Easy past 0.9226 without cratering Hard (mutually exclusive in our entire envelope, root-caused by E/M/H being non-separable by any compression-time signal). The only legitimate upside is **passive**: hold m12 frozen to defend Single-H, and let king's volatile Hard re-evaluate downward into a free Pair(M,H) capture — a competitor-drift bet we do not control, requiring no build. **No build is justified; there is no concrete, non-rehashed, compliant path with a pre-build validation gate that clears a threshold, because the score-deciding variable (fresh-sample pass/break/flip) is unobservable offline and swamps any single-lever effect.** One live competitive risk to surface: a failed-review miner (5CaFqLaPBYTQ, H 3.15) sits off-board today; if its status ever flips to scored it instantly sweeps every element including our Single-H — our 4.76% is safe only while that miner stays disqualified.

---

## 1. CATEGORY-DIFFERENCE ANALYSIS (E / M / H) — with distributions

**Question:** Is there ANY observable signal *at compression time* that separates Easy / Medium / Hard? **Computed answer: not for the boundaries that matter.** The non-separability finding holds under fresh distributions, with one red-team refinement applied below.

Computed over the **15 named comp-108 m12 trajectories** (6 Easy / 3 Medium / 6 Hard; 61 run-deduped trajectories, longest session per task/run) + the **per-run platform JSONs** (all 50 comp-108 tasks).

### 1A. Trajectory-signal distributions (per-run-deduped; min / median / max)

These are the native, compression-time observables. Every signal heavily overlaps across the three categories.

| Signal | Easy (n=24) | Medium (n=13) | Hard (n=24) | Separates? |
|---|---|---|---|---|
| **peak token (final native)** | 10.7K / **35.2K** / 61.0K | 17.8K / **47.9K** / 68.1K | 24.7K / **48.7K** / 95.6K | partial (overlap: Easy max 61K > Hard min 25K) |
| **depth (msg count)** | 32 / **132** / 178 | 62 / **106** / 224 | 60 / **113** / 196 | **no** (medians within 26 msgs; full overlap) |
| **# tool calls** | 15 / **65** / 88 | 30 / **52** / 111 | 29 / **56** / 97 | **no** |
| **# error results** | 2 / **7** / 16 | 5 / **7** / 13 | 1 / **5** / 17 | **no** (Hard has the *fewest*) |
| **error-result freq** | 0.03 / **0.17** / 0.29 | 0.06 / **0.12** / 0.23 | 0.01 / **0.08** / 0.31 | **no / inverted** (Easy most error-dense) |
| **# test-run calls** | 2 / **16** / 34 | 4 / **16** / 61 | 4 / **15** / 28 | **no** (medians identical) |
| **# diff/patch lines** | 0 / **4** / 14 | 0 / **8** / 88 | 0 / **6** / 19 | **no** |
| **max repeated tool-call** | 1 / **1** / 2 | 1 / **1** / 1 | 1 / **1** / 1 | **no loops in any category** |
| **has_traceback** | 100% | 100% | 96% | **no** (universal) |

**Key inversions that kill intuitive "harder = messier" signals:** error frequency is *highest* for Easy (median 0.17) and *lowest* for Hard (0.08); test-run counts have identical medians (~15–16); loops are absent everywhere (max repeated tool-call = 1). Depth is flat: Easy median 132 ≥ Hard median 113.

### 1B. Separability tests (computed)

**Pairwise AUC** = P(a random Hard value > a random Easy value); 0.50 = no separation:

| Signal | E-v-M | E-v-H | M-v-H |
|---|---|---|---|
| peak token | 0.689 | **0.762** | 0.580 |
| depth | 0.452 | 0.451 | 0.495 |
| err_freq | 0.446 | 0.332 | 0.340 |
| test_runs | 0.559 | 0.456 | 0.397 |

**Best single-threshold 3-class accuracy** (majority baseline = 0.393): peak_tok **0.607**; everything else 0.49–0.56 (noise). Only token size beats chance, and only marginally.

### 1C. RED-TEAM REFINEMENT — "non-separable" is true specifically for Medium and specifically for compression-time signals (not a universal "nothing works")

A multivariate test (GNB + kNN, leave-one-out at the task level, n=15) was run beyond the original single-threshold analysis. Findings that **refine** (not refute) the headline:

1. A **combination** of the two router-visible signals (running context peak + depth) reaches **0.733 LOO accuracy (11/15)** vs 0.400 majority — a genuine multivariate lift over the single-signal 0.607.
2. But 0.733 is the **same ceiling** the original analysis already disclosed (degenerate `Medium | Easy | Hard` split); the combination reaches it more cleanly, it does not exceed it.
3. The lift comes **entirely from the Easy-vs-Hard token axis** (running_peak task-level AUC(H>E) = **1.000**, perfect) — which is exactly what m12's existing `PASS_THROUGH_TOKENS` / `LARGE_THRESHOLD_TOKENS` knobs already key on.
4. The boundaries that matter for any *new* lever are still noise: **Easy-vs-Medium running-peak task-level AUC = 0.500 (chance)**; Medium task running-peaks `[7.5K, 9.5K, 20.9K]` are smeared across the entire Easy+Hard range — **Medium is not isolable.** Every Medium task is misclassified by the best combo.
5. The one non-token signal that looks discriminating (err_results, GNB E-v-M 0.889) uses **whole-trajectory cumulative error count — hindsight the router never has** (m12 only sees `recent_errors` in a window of 4). Combining many signals **hurts** (all-8 GNB/kNN collapse to 0.400 = majority).
6. **Fragility:** flipping one known low-confidence label (django-12050 Hard→Medium) drops the 3-class combo from 0.733 to 0.333; n_Medium=3 makes any Medium-involving accuracy statistically meaningless. Treat the task-level 3-class number as **directional only**; the run-level and AUC results are the robust ones.

**Accurate claim:** (a) the Easy-vs-Hard axis IS separable by token size (one m12 already exploits); (b) the two boundaries needed for any "leave-Easy-native" or "isolate-Medium" lever are NOT separable; (c) the few signals that look discriminating are hindsight the compressor cannot see at decision time. **Active category-routing levers remain dead, and any category-aware logic would also be a compliance violation.**

### 1D. Platform-side composition (per-run JSONs; reproduced exactly this session)

| Miner | Category | pass-pass | BREAK | FLIP | fail-fail | mean score |
|---|---|---|---|---|---|---|
| **m12** | Easy | 49% | 12% | 3% | 35% | **+0.462** |
| **m12** | Medium | 67% | 15% | 14% | 4% | +0.898 |
| **m12** | Hard | 50% | 10% | 15% | 25% | +0.857 |
| newking 5Ggq | Medium | 76% | 6% | 12% | 6% | **+1.23** |

**Easy is m12's weakest category (+0.462)** — driven by a 35% fail-fail rate (baseline-unsolvable items binned Easy) plus a 12% BREAK rate, not by compression being "too hard." The BREAK rate is **not** higher for Hard (10%) than Easy (12%) or Medium (15%) — there is no category where harder compression is systematically more dangerous in a per-call-routable way. The category that pays — Medium — is where newking dominates (+1.23, only 6% BREAK), and it does so by **reliability**, not by compressing harder.

---

## 2. PLATFORM-EMULATION GAP ANALYSIS

**Bottom line:** the local harness is a faithful emulator of the **mechanical, deterministic** half of the platform and is **structurally blind** to the half that decides scores (fresh-model pass/break/flip).

### 2A. What local replay CAPTURES faithfully (deterministic — verified)
The replay imports m12's actual module and re-executes its exact math. `replay()` is a pure function (3 identical re-runs, 48 rounds). It faithfully reproduces:
- **Routing-mode transitions** passthrough→harvest→rich, including stickiness and all four escalation triggers (depth≥90, observed≥120k, cumulative≥600k, still_failing).
- **Connector-rewrite feed-forward + save_state escalation** (`assistCap/trunc2/tailCap` advance exactly as live); compressed output forwarded as next turn's prefix.
- **Per-turn compression delta vs native:** harvest median token removal **79.8%** (3,295 turns), rich **86.1%** (187 turns); passthrough ~8% is an accounting artifact (router returns `changed=False`).
- **Aggregate raw-token savings / qualification-gate risk:** m12 sits at **37.9% savings** (50.2M with / 80.9M without, task-level sums) — far above the ~10% screener gate that DQ'd m17. Large headroom for a deeper-passthrough candidate.
- **Hard-routing-invariance as a candidate gate:** the m24 sweep mechanically finds the first `PASS_THROUGH_TOKENS` that changes any Hard-task turn's mode (first Hard divergence at 4000, driven by django-14122).

### 2B. What local replay CANNOT predict (the walls)
- **MODEL SAMPLING VARIANCE (the dominant uncertainty).** Each recorded trajectory is ONE frozen sample; the replay can re-run the compressor but can never ask a *fresh* model "given this compressed context, do you still solve it?" **50% of m12's tasks (25/50) have runs that DISAGREE on pass/fail across the SAME miner's 5 platform attempts** (Easy 7/13, Medium 9/17, Hard 9/20), with an **average per-task score spread of 2.67 points** and within-task token CV of **34.8%**. Any local emulator over fixed trajectories sees none of this.
- **Pass/break/flip OUTCOME preservation.** Local replay measures *what* m12 removed (the break-RISK surface), not *whether* removal changes the verdict — the outcome is a fresh-model draw.
- **Per-run score reconstruction.** Score `= base + 0.5·clamp(ln(WO/W), ±2)` is structurally confirmed, but the platform stores only **task-level** without-compression tokens, not per-run WO; reconstruction lands within 0.6 on only 34/50 runs.
- **Screener/qualification gating** beyond the aggregate savings number, and the **E/M/H category map** (APPROXIMATE), are platform-side.

### 2C. Honest verdict for build-gating
Local emulation can prove a candidate is **mechanically safe** (no Hard reroute, savings ≥10%, compression behaves) and can **rank break-RISK**, but it **cannot demonstrate a score gain**, because the score-deciding variable (fresh-sample pass/break/flip) is unobservable offline and swamps any single-lever effect with a 50%-of-tasks pass-disagreement and a 2.67-pt spread. **A candidate whose projected delta is below the ~2.67-pt variance floor is not locally distinguishable from m12. No build should be proposed on a projected score lift alone — only on mechanical-safety + risk-reduction that survives the variance envelope.**

---

## 3. TOP-10 MINER COMPARISON TABLE

Ranked by Overall, snapshot `2026-06-25/192615`. Per-run columns only where a per-run JSON exists. "Wins" = reward element won.

| # | hotkey | name | Total | E | M | H | aggRatio* | sav%* | all5/50 | breaks/250 | meanRun | Wins (reward) |
|---|--------|------|-------|---|---|---|-----------|-------|---------|------------|---------|---------------|
| 1 | 5GgqHgSdxgAL | king (newking) | **0.957** | 0.858 | **1.281** | 0.727 | 1.61 | 37.8 | **24** | **6** | 0.957 | **Overall, (E,M), (M,H), Single-M = 80.95%** |
| 2 | 5H6919WaPmWc | — | 0.787 | 0.782 | 0.846 | 0.732 | — | — | no per-run | — | — | none |
| 3 | 5DFvymSeEwuG | old-king | 0.781 | 0.812 | 0.934 | 0.596 | 1.71 | 41.6 | 22 | 7 | 0.780 | none |
| 4 | 5Dz7JaCBw6t9 | **m12 (OURS, live)** | 0.769 | 0.412 | 0.953 | **0.919** | 1.61 | 37.9 | 18 | 17 | 0.768 | **Single-H = 4.76%** |
| 5 | 5DxrcCtcvrFa | — | 0.761 | 0.748 | 0.766 | 0.748 | — | — | no per-run | — | — | none |
| 6 | 5GCWaCnbJkwJ | — | 0.760 | **0.923** | 0.701 | 0.665 | — | — | no per-run | — | — | **Single-E = 4.76%** |
| 7 | 5DADzDbZb3y6 | m20b-v2 (ours-exp) | 0.715 | 0.172 | 0.650 | 0.808 | 1.52 | 34.3 | 17 | 10 | 0.715 | none |
| 8 | 5DtEz84j53Pf | 5DtEz | 0.714 | 0.837 | 0.499 | 0.813 | 1.79 | 44.3 | 21 | 13 | 0.714 | **(E,H) = 9.52%** |
| 9 | 5HjRhPLmdRYR | — | 0.689 | 0.684 | 0.671 | 0.713 | — | — | no per-run | — | — | none |
| 10 | 5GYxeJjdvfat | — | 0.661 | 0.117 | 0.661 | 0.569 | — | — | no per-run | — | — | none |

`*aggRatio/sav%` computed on **weighted/display** `tokens_with_compression` vs `tokens_without_compression` (the conservative, internally-consistent definition). **See appendix caveat: the very-high aggRatios attributed to m21 (7.93x) and 5CwZBKyL (15.76x) in prior Q4 notes do NOT reproduce from any single token-field in these files — I compute 1.59x and 3.39x on the weighted definition; the qualitative ordering (most-aggressive compressor → lowest total) holds on every definition, but the exact magnitudes are unverifiable and should not be cited as fact.**

**Pool is fully allocated:** king 80.95% + 5DtEz 9.52% + 5GCWaCnb 4.76% + m12 4.76% = 100%. All 4 element winners are inside the top-10; there is **no element-winning specialist outside the top-10.** Five top-10 miners (#2, #5, #6, #9, #10) have **no per-run JSON** — including the Single-E winner 5GCWaCnb, whose mechanism (ratio? flips? consistency?) is unknown.

### Patterns inferred (computed, not "copy them")

1. **Winners are BALANCED, won by CONSISTENCY not ratio.** King wins ~81% of the pool with the flattest leader profile (E 0.86 / M 1.28 / H 0.73) and the separating metric: **24/50 all-5-pass (highest), 6/250 break-runs (lowest)**. Its aggRatio (1.61) is **identical to m12's (1.61)** — king does not out-compress us; it wins by not breaking.
2. **More compression is net-NEGATIVE past the saturated savings gate.** The most aggressive compressors post the lowest totals (5CwZBKyL most-aggressive → total 0.530; m21 → 0.597) while the ~1.5–1.8x cluster scores 0.71–0.96. The savings multiplier is saturated at 1.0 for everyone here, so extra savings buys nothing and harder compression costs passes. This disproves "compress harder" (confirms dead-ends m17/m18/m20b/m21/m24).
3. **m12 differentiates on flips, not pass-pass.** m12 has the strongest flip profile of the leaders but the most break-runs (17/250) and weakest pass-pass — flips (base +4) are how it wins Single-H. 5DtEz wins (E,H) purely by being above-average on E and H while sacrificing Medium — it beats m12's pair only because **m12's Easy (0.412) is its single broken category.**
4. **Specialists win zero elements (existence proofs).** 5DAh2r (H -3.600, total 0.051) and 5FUTAP (H -3.873, total -0.657) clearly route to break Hard to protect E/M — both are #2 on a single element but win nothing because the sacrificed category sinks every pair/overall. Easy-sacrificers (5EgyJKN E -0.108, 5E1xf E -0.130) also win nothing. **Conditional on the current eligibility set, specialization only wins if the sacrificed category doesn't drag the kept ones below the incumbent — and on comp-108 the categories are non-separable, so a single miner cannot reliably "drop Easy to lift Hard."** This is inductive evidence for non-separability, not a proof no specialist could ever win.

---

## 4. REWARD-ELEMENT TARGETING TABLE

Eligible set = **41 under the script filter** (`compute_reward_elements.py`: not-failed-review AND all 3 categories numeric) — this admits m22 (status `evaluating`, E0.712/M0.742/H0.564) on top of the 40 `scored`. **Recomputed under both n=40 and n=41: all 7 winners and cushions are byte-identical** (m22 wins nothing), so the count discrepancy is immaterial. Pool = 1.75 (Overall 1.0 = 57.1%; three pairs 1/6 ea = 9.52%; three singles 1/12 ea = 4.76%). Pair/single values shown as **category averages** (the form the script ranks on).

**m12 frozen scores (byte-identical across all 23 snapshots 06-24 → 06-25):** E **0.4117**, M **0.9534**, H **0.9193**; leaderboard `total` field **0.7685**; mean(E,M,H) = **0.7615** (the quantity used for the Overall element).

| Element | Weight (% pool) | Current owner | Winning avg | m12 on subset | m12 rank | Gap to win | Verdict |
|---|---|---|---|---|---|---|---|
| **Overall (E,M,H)** | 1.000 (**57.1%**) | king `5Ggq` | 0.9553 | 0.7615 | #5 | **+0.1938** | **UNREALISTIC** |
| **Pair (E,M)** | 0.1667 (9.5%) | king `5Ggq` | 1.0693 | 0.6826 | #8 | **+0.3867** | **UNREALISTIC** |
| **Pair (E,H)** | 0.1667 (9.5%) | `5DtEz` | 0.8248 | 0.6655 | #8 | **+0.1593** | **UNREALISTIC** (needs E≥0.73 AND H≥0.92 together) |
| **Pair (M,H)** | 0.1667 (9.5%) | king `5Ggq` | 1.0041 | **0.9363 (#2)** | #2 | **+0.0678** | **UNREALISTIC active / PASSIVE-only** |
| **Single (E)** | 0.0833 (4.8%) | `5GCWaCnb` | 0.9226 | 0.4117 | #16 | **+0.5109** | **UNREALISTIC** |
| **Single (M)** | 0.0833 (4.8%) | king `5Ggq` | 1.2810 | 0.9534 | #4 | **+0.3276** | **UNREALISTIC** |
| **Single (H)** | 0.0833 (4.8%) | **m12 (OURS)** | 0.9193 | **0.9193 (#1)** | #1 | **−0.1065 cushion** (vs 5DtEz 0.8128) | **PASSIVE-HOLD (own it now)** |

**Current share = 0.0833 / 1.75 = 4.76%** (Single-H only).

**Why every active gap is UNREALISTIC — our proven scoring envelope.** The relevant question is not "what gap exists" but "can any hotkey we can build reach the threshold." Our **7 scored/evaluating experimental hotkeys** define the envelope (all vs m12, recomputed this session):

| Lever (hotkey) | ΔEasy | ΔMedium | ΔHard |
|---|---|---|---|
| m21 keep-more (`5ENt`) | +0.152 | −0.188 | −0.459 |
| m22 extractive (`5Cff`) | +0.300 | −0.211 | −0.355 |
| m20b-v2 (`5DADz`) | −0.239 | −0.303 | −0.111 |
| 5CwZBKyL (`5CwZ`) | +0.344 | −0.349 | −0.676 |
| 5EX5r3 | −0.024 | −0.068 | −0.443 |
| 5CApy5s | +0.150 | −0.236 | −0.486 |
| 5DRi5y | +0.008 | −0.393 | −0.696 |

- **No lever we have ever scored raises Medium OR Hard above m12** — all 7 hotkeys post ΔM<0 AND ΔH<0. m12 sits at our ceiling for both (M 0.953, H 0.919). This kills Pair(M,H), Single-M, Pair(E,H), and Overall as *active* targets.
- **Easy is liftable but only by cratering Hard.** Best Easy ever = **0.755** (5CwZBKyL), still **0.17 short** of the Single-E threshold (0.9226), and it dropped Hard to **0.243**. Pair(E,H) needs E≥0.73 AND H≥0.92 simultaneously (sum ≥ 1.6496); our envelope max joint E+H is m12's 1.331 — the two are mutually exclusive because Easy-lifting transits the harvest path that holds Hard.
- **Root cause (re-confirmed §1):** E/M/H non-separable by any per-call signal, so a single miner cannot push one category without spending another.

**Specialist vs balanced:** weights favor Overall (57%) > pair (9.5%) > single (4.76%) *if reachable*, but reachability is ~0 for all active targets. The portfolio rule (multi-hotkey, MAX per element, free try) does not rescue any specialist — it only lets us lose for free. **A 2-category specialist does NOT beat a balanced miner here, and neither beats simply holding Single-H.**

---

## 5. FINAL RANKED PLAN

### Passive-capture breakeven math (recomputed, with red-team correction applied)

- **Pair(M,H) capture — the only passively reachable element.** m12 is the clean #2 (avg 0.9363; #3 non-king is 5EFLSBvXcp at 0.7982). Naive breakeven holding king-M fixed at 1.281 is "king H < 0.5917." **RED-TEAM CORRECTION: king's E/M/H co-move under re-eval — this is the substantive fix.** In the only snapshot where king H fell below 0.5917 (2026-06-24 21:03, H=0.4333), king M was simultaneously **0.8383, not 1.281**, giving a king (M,H) pair avg of **0.6358**. The correct, draw-robust trigger is **king's (M,H) pair average < m12's 0.9363**, not H-alone-with-M-pinned. Under the pair condition the bet is still real and m12 auto-inherits; king's pair *has* dropped below 0.9363 once (0.6358) in the comp-108 window. **It is a free option on a whole-king-redraw with unknown (likely small) exercise probability — board frozen 16 snapshots, so the hazard is unquantifiable; do NOT assign it the 1-in-21 historical dip frequency (that dip was the single unstable initial draw, survivorship-style).**
- **Overall capture — KILL, and the kill is STRONGER than stated.** Even on a deep king-Hard collapse (H < 0.146), **m12 does NOT inherit Overall — m12 is only #5 (0.7615), behind 5H6919 (0.7867) and 5DFvym (0.7807).** Overall is unreachable even on king collapse.

### Ranked plan

1. **BEST DEFENSIVE MOVE — Passive Single-H defense (PURSUE, dominant strategy).** Leave m12 untouched and frozen. 4.76% locked, +0.107 cushion; m12 H pinned at 0.9193 across all 23 snapshots, never re-evaluated. Nearest threat 5DtEz 0.8128 would need +13% on Hard while m12 stays frozen. Cost: nothing. **Caveat to monitor: the off-board failed-review miner 5CaFqLaPBYTQ (H 3.15) would dethrone Single-H instantly if its status flips to scored.**
2. **BEST OFFENSIVE / HIGHEST-EV MOVE — Passive Pair(M,H) capture (PURSUE).** Hold m12 frozen; if king's (M,H) pair average re-evaluates below 0.9363, m12 auto-captures +9.52% (→ 14.3% total) with no build and no m12 risk. A competitor-drift bet we do not control. **This is the only positive-EV upside available, and it is passive.** Required validation: keep collecting snapshots; monitor king's (M,H) pair and the 5CaFqLaPBYTQ status.
3. **WHETHER TO SPEND ANOTHER HOTKEY — No.** Every active single-miner and specialist target (Overall, all three pairs, Single-E, Single-M) is KILLED: each requires raising M or H above m12 (no lever does, across all 7 hotkeys) or raising Easy past 0.9226 without cratering Hard (impossible in our envelope). An insurance twin is also KILLED — zero observed base rate for a downward m12 re-eval (never re-evaluated in 23 snapshots), and a twin would face the same sampling variance it is meant to insure against. A fresh hotkey only lets us lose for free.
4. **WHETHER TO STOP ACTIVE COMP-108 WORK — Yes, STOP and prepare for the next round.** Active dethroning is unrealistic; the board is frozen; we hold the only positive-EV position we can hold. The one legitimate forward lever (CONDITIONAL, not a build authorization) is **next-round global compression depth/safety tuning to improve the high-value Medium bucket without raising BREAK** (newking wins Medium at +1.23 with 6% break vs m12's 15% break) — **NOT category routing.** Pre-build validation gate (all four required before any build, and never on projected lift alone): (1) **zero Hard-task routing divergence** vs m12 in the corrected main-agent-session emulator; (2) aggregate raw savings **≥10%** qualification gate; (3) per-turn compression-diff **reduces break-RISK on Medium specifically**; (4) projected delta judged against the **2.67-pt variance floor**. Build only into a live next round, never speculatively against the frozen comp-108 board.

---

## APPENDIX — Reproduction & verification notes

- Ownership/cushions: `/tmp/q3_reward.py` over the snapshot `miners` list; reproduced exactly (king Overall 0.9553 / (E,M) 1.0693 / (M,H) 1.0041 / Single-M 1.2810; 5DtEz (E,H) 0.8248; 5GCWaCnb Single-E 0.9226; m12 Single-H 0.9193, +0.1065 over 5DtEz 0.8128; m12 (M,H) pair avg 0.9363 = #2).
- m12 H = 0.9193 and total = 0.7685 verified byte-identical across all 23 m12 snapshots; mean(E,M,H) = 0.7615.
- King Hard distinct trace: 0.7346 → 0.4333 → 0.8332 → 0.9814 → 0.7272 (frozen), dipping below 0.5917 exactly once (0.4333), at which draw king M = 0.8383.
- Per-run metrics (king aggRatio 1.61 = m12 1.61; king 24 all5 / 6 breaks; m12 18 all5 / 17 breaks): computed over the 8 per-run JSONs.
- Per-category composition (m12 Easy +0.462 / Medium +0.898 / Hard +0.857) reproduced from `m12_5Dz7_perrun.json` + `comp108_category_map_derived.json` (break = score ≤ −3.5 proxy).
- Lever envelope (all 7 ΔM<0 AND ΔH<0): computed directly from the leaderboard.

**LOAD-BEARING NUMBERS THE MAIN SESSION SHOULD INDEPENDENTLY DOUBLE-CHECK:**
1. **aggRatio for m21 and 5CwZBKyL.** Prior Q4 cited 7.93x and 15.76x; I cannot reproduce these from any single token field — I get 1.59x and 3.39x on weighted `tokens_with_compression`. The "compress-harder is net-negative" *ordering* holds on every definition, but the exact ratio magnitudes are UNVERIFIED. Do not cite the high numbers as fact.
2. **Baseline `tokens_without_compression` is NOT uniform across per-run files** (king/m12 ≈ 80.9M; m21/5CwZBKyL ≈ 404.6M for the same 50 tasks). This means savings% / ratio comparisons across miners may not be apples-to-apples; verify the baseline-token semantics before trusting cross-miner savings%.
3. **Category map is APPROXIMATE** (`comp108_category_map_derived.json`, platform does not expose E/M/H; RMSE ~0.069/cell, ~12 swing tasks). All per-category composition and the n=15 task-level 3-class accuracy (0.733) are directional; element ownership uses the authoritative leaderboard E/M/H and does NOT depend on the derived map.
4. **`config/comp108_tasks.txt` baseline-label parse** returned only one label this session (the per-run JSONs carry `pass_without_compression` directly, so BREAK/FLIP classification did not rely on it) — verify the file format if you intend to use it as the baseline source.
5. **5CaFqLaPBYTQ (failed review, H 3.151, total 2.023)** — confirm its review_status on the next snapshot; a flip to `scored` overturns all ownership including our Single-H.
6. **The 2.67-pt within-task score spread and 50%-pass-disagreement (25/50)** are from prior Q2 computation over `m12_5Dz7_perrun.json`; re-run if used to gate a build decision.
