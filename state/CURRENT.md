# CURRENT — live status (2026-06-25 ~23:00 UTC) — READ FIRST after compaction

_Mode: comp 108 (CoT-Compression-4, SN114) — ACTIVE MINER WORK STOPPED per the full-reset verdict; posture = MONITOR
+ NEXT-ROUND PREP. Files = source of truth. Read this + NEXT_ACTIONS + DISCOVERIES (top entries) before acting._

## ⏳ IN FLIGHT (2026-06-26) — m25 BUILT + Phase-A VERIFIED; awaiting USER hotkey upload (the M,H coin-flip)
User reopened the M,H thesis (per-task decomposition showed m22 is a REDISTRIBUTION: break-fix gains +4.958 Medium are
REAL, net-negative is entangled collateral) and authorized a build. **m25 = upload_miner_m25.py (sha 52fe47f9), SEPARATE
hotkey, m12 LIVE untouched.** = m12 + (1) GENTLE break-fix (extractive at truncation sites ONLY, NO drop-spans), (2)
RESOLVED-GATE (fire only on settled turns), (3) DECOUPLED STATE (emit break-fix, save m12-exact -> rich/Hard reads clean).
- Phase-A PASS: 54 fns byte-identical to m12; rich+passthrough+gate-off byte-identical; gate-on <=m12 tok+chars + decoupled
  clean state; deterministic; compliant; m12 git-clean. Real-traj: ACTIVE (ships 545x), targets Easy/Medium (32/43 content-
  changes), Hard protected (6 changes/2315). RESIDUAL FLIP-LEAK: 201 ships on flips (decouple protects DEEP flips, not shallow).
- HONEST: coin-flip ~15-25%. Strictly safer than m22 (gate skips active-failing; deep flips protected) but NOT flip-clean;
  shallow-flip + non-gateable pass-task new-breaks remain. Local CANNOT predict break outcomes -> platform is the test.
- **NEXT: USER registers a new hotkey + uploads (cmd in reports/m25_build.md / platform_commands.md, SAME OpenRouter acct).
  ACCEPT GATE (>=3 scrapes): Medium UP AND Hard>=0.919 AND flips>=m12; else reject. m12 LIVE regardless.** Report: reports/m25_build.md.

## ★★ FULL-RESET VERDICT (2026-06-25, workflow wohsbvkmr, 10 agents; report reports/comp108_full_reset_analysis.md). ALL load-bearing numbers independently re-verified by main session.
**BLUNT: active dethroning of comp-108 is UNREALISTIC. STOP active miner work; prepare for the next round.** We own
exactly ONE of 7 reward elements — Single-H (m12 H=0.9193, +0.107 cushion) = 4.76%. PROVEN why no active lever works:
- **Lever envelope (the killer evidence):** ALL 7 of our scored experimental hotkeys post ΔMedium<0 AND ΔHard<0 vs m12
  (m21/m22/m20bv2/5CwZ/5EX5r3/5CApy5s/5DRi5y). m12 is our M+H CEILING. Best Easy ever = 0.755 (5CwZ) but it cratered
  Hard to 0.243. Pair(E,H) needs E>=0.73 AND H>=0.92 together; mutually exclusive (Easy-lift transits the Hard-holding
  harvest path). Root cause: E/M/H NON-SEPARABLE by any per-call signal (re-confirmed §1: Easy-vs-Hard IS token-separable
  — m12 already exploits it — but Easy-vs-Medium and Medium-isolation are noise; discriminating signals are hindsight
  the router can't see). m12 Easy is only 0.412 = 35% fail-fail (unsolvable tasks) + 12% breaks, NOT a compression-fix gap.
- **5DCnA57Dve8W rival = NOT a threat once penalties count (CORRECTED 2026-06-26 via per-task detail).** Its leaderboard
  0.957/H0.787 is PRE-penalty/in-eval raw; its scored DETAIL page shows penalties Easy −0.435 + Hard −0.581 → EFFECTIVE
  E0.528/M1.120/H0.168, total **0.701 (BELOW m12 0.768).** Pattern = near-passthrough LIGHT compressor (1.25× vs 1.61×;
  INFLATES tokens on 11/45 tasks; ~0 breaks → high RAW pass-rate) that EATS the savings/under-compression penalty. So:
  effective Hard 0.168 ≪ our 0.919 (Single-H SAFE); effective (M,H)=0.644 < m12 0.936 (m12 still clean #2 → passive
  Pair(M,H) INTACT). It is the LIVE PROOF the "go light / near-passthrough / never-break" lever is penalty-capped (~0.701,
  below m12) — validates our rejection of EH-passthrough. CAVEAT: still evaluating; WATCH leaderboard converge to the
  penalized ~0.701 (expected) vs the raw 0.957 (then re-assess). source hidden. (detail saved /tmp/5DCnA57_comp108_detail.json)
- **ONLY positive-EV upside = PASSIVE Pair(M,H) capture (INTACT — 5DCnA57's penalty keeps m12 #2):** m12 is clean #2 (pair avg 0.9363 vs king 1.0041). If king's
  (M,H) PAIR AVG re-draws < 0.9363, m12 auto-inherits +9.52% -> ~14.3%. Free option, NO build, NO m12 risk. RED-TEAM
  CORRECTION: trigger is king (M,H)-pair<0.9363 NOT "king H<0.5917 with M pinned" (king E/M/H CO-MOVE under re-eval; at
  its H=0.433 dip M was 0.838 -> pair 0.636). Probability UNQUANTIFIABLE (board frozen 16 snaps; that dip was 1 unstable
  initial draw — do NOT assign 1-in-21). Overall capture KILLED even on king collapse (m12 only #5, behind 5H6919/5DFvym).
- **INSURANCE TWIN = KILLED (corrects my earlier 2x recommendation).** It defends the WRONG threat: a twin is also ~0.919
  so it CANNOT beat a competitor who exceeds 0.919; m12 has zero observed downward re-eval variance (pinned 0.9193 across
  23 snaps, never re-evaluated); a twin's fresh eval faces the same sampling variance it is meant to insure. Don't spend it.
- **★ NEW LIVE RISK:** failed-review miner **5CaFqLaPBYTQ (E1.26/M1.61/H3.15/total2.02)** sits OFF-BOARD. If its status
  flips to `scored`, it SWEEPS ALL 7 elements incl our Single-H. Our 4.76% is safe ONLY while platform review keeps it off
  (H=3.15 is the prompt-cheat signature that failed review). MONITOR review_status every snapshot.
- **Don't spend another hotkey.** Every active single-miner/specialist target (Overall/all 3 pairs/Single-E/Single-M) KILLED.
  The ONE conditional FORWARD lever is NEXT-ROUND global Medium safety-tuning (lower BREAK toward newking's 6% vs m12 15%;
  NOT category routing), gated by: zero Hard-route divergence + savings>=10% + per-turn Medium break-RISK down + delta vs
  the 2.67pt variance floor. NOT authorized now; next-round research only.
- Flagged UNVERIFIED (immaterial to verdict): aggRatio magnitudes for m21/5CwZ (compress-harder ordering holds regardless);
  cross-miner baseline-token non-uniformity; category map APPROXIMATE (ownership uses authoritative leaderboard E/M/H).

## ⏭ STANDINGS — we hold ONLY Single-Hard (4.8%); king dominates
| miner | total | E | M | H | status | share |
|---|---|---|---|---|---|---|
| **king `5Ggq…`** | **0.957** | 0.858 | 1.281 | 0.727 | scored | **85.7%** (Overall+E,M+M,H+E+M) |
| 5DtEz `5DtEz…` | 0.714 | 0.837 | 0.499 | 0.813 | scored | 9.5% (Pair E,H) |
| **m12 `5Dz7…` (OURS, LIVE)** | **0.768** | 0.412 | 0.953 | **0.919** | scored | **4.8% (Single-H ONLY)** |
| old king `5DFvym…` | 0.780 | 0.812 | 0.596 | 0.934 | scored | 0% (dethroned) |

- **m12 = LIVE/BEST.** solution `upload_miner_m7_compliant.py` (sha 3c4e3086), key …1e8a lineage in config/secrets.env.
  **Our entire 4.8% rests on Hard 0.919 being FIELD-BEST (next 5DtEz 0.813). If anyone beats 0.919 Hard → 0%. PROTECT HARD.**
  Never replace until something BEATS it scored.

## ★ INVESTIGATION wzm1fb1sn VERDICT IN (2026-06-25) — king's edge = CONSISTENCY (replicable), NOT content quality
**Decisive verdict landed (full: state/DECISIONS.md top + workflow wzm1fb1sn output). Three corrections + a decision:**
- **King Medium 1.281 = LEADERBOARD DRIFT, not per-run reproducible.** Real per-run = **0.909**. Target the mechanism
  (consistency), NOT the number. (Supersedes the "Medium 1.281" figure in the standings table below — keep table for
  the board snapshot but know 1.281 is aggregation drift.)
- **King does NOT preserve flips** — it's WORSE than m12 on flips (Medium flip contrib +0.188 vs m12 +0.503; django-14017
  king 0/5 vs m12 3/5). Its ENTIRE Medium edge is baseline-PASS consistency (+0.721 vs +0.333), bought by killing −4
  break-runs. all-5-consistent-pass: m12 14 / king 18 / m22 17 (king = consistency champ). This is the GOOD news: the
  king's edge is **variance reduction (determinism)** — a compliant MECHANICAL lever — NOT unreachable content-quality.
- **"Generic break-fix selector + Hard-safe" = PROVEN MUTUALLY EXCLUSIVE (m18/m21/m22, 3 proofs).** Break-fix wants the
  destination (error/diff/sig), flip wants the path (exploration) — zero-sum in one budget. save_state feeds compressed
  output back into rich → ANY harvest content change craters Hard (m22 left rich byte-identical, Hard still cratered).
  → **smarter-selector direction PERMANENTLY DROPPED.**
- **DECISION (RESOLVED 2026-06-25): option (b) m23 = NO-GO after the mandatory pre-build gate audit → HOLD m12.**
  Full: reports/m23_gate_audit.md + DECISIONS.md top. The RESOLVED gate CANNOT causally separate settled-Easy from
  flip turns (early flip-exploration is signal-identical: no errors yet, recent clean, shallow). Faithful offline
  replay of the platform loop over real comp-108 m12 trajectories: flip task sympy-24066 leaks 217/104/70 fires
  (lenient/strict/resolution-signature); the only zero-leak gate (G4) is threshold-OVERFIT to 3 flips AND misses
  django-14122 (a real Easy target). Zero-sum under the ≤m12 ceiling + save_state propagation = one misclassified
  early turn craters Hard, un-undoably. The "determinism pass" half = NO-OP (m12 already deterministic; variance is
  agent-side). m23 NOT built, upload_miner_m23.py NOT created, m12 LIVE untouched. 4th content-change blocked
  (m18/m21/m22 + this). Smarter-selector AND RESOLVED-gated break-fix both now closed.

## ★ BEAT-THE-KING RE-ANALYSIS DONE (2026-06-25, workflow wiz2yq9to, 25 agents) — PORTFOLIO is the path; new Hard-RISK found
**Verified element ownership (live snap data/raw/dashboard/2026-06-25/192615_leaderboard.json, 40 eligible):**
Overall+Pair(E,M)+Pair(M,H)+Single(M) = king 5Ggq; Pair(E,H) = 5DtEz; Single(E) = 5GCWaCnb (NEW rival); **Single(H) = m12
(OURS, 0.9193, +0.107 cushion).** Our share = **4.76%**. (old-king eligibility resolved: m12 DOES hold Single-Hard.)
- ★★ **NEW RISK — our income is more exposed than thought.** King's Hard is VOLATILE under re-eval: drew
  0.433→0.833→**0.981**→0.727 across the 06-24 window while m12's stayed pinned 0.919. **At 0.981 the king takes
  Single-Hard from us.** Board frozen since 06-24 22:19 but comp not over; next re-eval = coin-flip on our 4.76%.
- **13 of 16 new ideas KILLED, 0 PURSUE, 3 MAYBE.** Every single-miner CONTENT lever stays dead. The ONLY
  structurally-new surface = **PORTFOLIO (multi-hotkey specialists)** — and existence proofs are LIVE in the pool
  (5DAh2r E0.853/M0.976/H=−3.6 and 5FUTAP M1.062/H=−3.87 win elements by ABANDONING Hard → platform rewards extreme specialists).
- **RANKED PLAN (all on SEPARATE hotkeys; m12 LIVE untouched; zero m12 downside):**
  1. ~~EH-passthrough specialist~~ **VALIDATED NO-GO 2026-06-25** (reports/m24_ehpass_verdict.md). Offline sweep of
     PASS_THROUGH_TOKENS over real comp-108 m12 trajectories: NO threshold gives Hard-routing==m12 AND savings≥10% AND
     material Easy lift. Raises >3500 re-route Hard (≥20k → 6 Hard tasks); deep break-prone Easy tasks (django-12039 92%
     still-harvest @10k) need ≥20k = Hard crater, while the safe window only rescues SMALL already-passing Easy tasks.
     Easy lift << the +0.32 needed for Pair(E,H). Same Easy↔Hard size-overlap wall that put m12 on depth-routing.
  2. **Hard-variance INSURANCE twin (DEFENSE, wins no new element):** register ONE more BYTE-IDENTICAL m12 hotkey.
     Element score = max across our hotkeys → best-of-2 on Hard cuts P(lose Single-Hard in a bad re-eval) from ~12-17%
     to ~1-3%. DUAL-PURPOSE: also passively captures Pair(M,H) if the king re-draws low Hard. Maximal reliability.
  3. **Pair(M,H) (cheapest gap +0.068):** m12 already eligible #2 (0.9363 vs king 1.0041); active lift BLOCKED by the
     wall (Medium break-fix kills flips); PASSIVE capture if king Hard re-draws <~0.855 (free if we hold the #2 twin).
- **SINGLE BEST NEXT MOVE:** build the OFFLINE VALIDATOR for #1 (replay 20 Hard+11 Easy comp-108 streams through a
  widened-passthrough clone; ASSERT per-Hard-task routing == m12 AND weighted-savings ≥10%; report Easy passthrough rate).
  Costs zero hotkey. If both gates pass → ship #1; else fall back to #2. **WON'T PROMISE: dethroning the king on Overall**
  (its edge = Easy/Medium baseline-pass CONSISTENCY = agent-side, banned to steer).
- NOTE/correction: the board scores Single-M off king Medium **1.281** (authoritative). An earlier per-run reconstruction
  got 0.909 (workflow wzm1fb1sn) but that may be OLD-KING 5DFvym's Medium misattributed — UNRESOLVED, immaterial (Medium
  is not a lever for us). Full synthesis: workflow wiz2yq9to output.

## ⏭ (resolved) m22 SCORED 0.672, REJECTED; EASY provably fixable but break-fix family CLOSED (m23 NO-GO above)
**m22 (`5Cffmt…`, sha aeccd26e, upload_miner_m22.py) SCORED 0.672 (E0.712/M0.742/H0.564)** [label still "evaluating"
but all 250 runs in = final]. REJECTED vs m12 0.768. = m12 + extractive-not-blind harvest at constant token budget.
- ✅ **EASY +0.300 (0.412->0.712) — the lever WORKS for breaks.** m22 turned break-prone tasks into ALL-5-CONSISTENT-
  pass: django-14122/11740/11095/12754/13033/11551 (each 1-2 breaks -> 0), django-13810 (3->1). FIRST time we moved Easy.
- ❌ **Medium -0.211, Hard -0.355.** TWO failure modes: (a) KILLED FLIPS — django-13925 (3 flips->0), django-14017
  (3->0), sympy-18698 (3->1): the extractive selector dropped the EXPLORATION content the agent uses to SOLVE baseline-
  fail tasks; (b) NEW breaks on passing tasks (django-12774 pass->4brk, django-15375). 
- ★ **3rd HARD CRATER (m18/m21/m22): the tokens<=m12 invariant HELD but Hard still cratered -> Hard failure is
  CONTENT-driven, NOT token-driven.** Changing WHICH spans harvest keeps (even at <= tokens) feeds rich/Hard a different
  trajectory -> disrupts the agent. "Hard-safe by token-budget" is FALSIFIED.
- ★ **CORE TENSION:** break-fix selection (keep error/diff span) KILLS flips (drops exploration the agent needs to
  solve) — break-fix and flip-enable want DIFFERENT content. Generic extractive helped Easy, killed Medium/Hard. Net -0.096.
- ★ **RELIABILITY (user's insight):** all-5-consistent-pass tasks: m12 21 / m22 23 / KING 27 (king=consistency champ).
  m22 SHUFFLED reliability (fixed some, broke others), didn't net-improve. The king's edge = CONSISTENCY.
- **INVESTIGATION RUNNING (wzm1fb1sn):** why king Medium=1.281 (does it fix breaks AND keep flips AND stay consistent?);
  m22 flip-kill mechanism; is "break-fix WITHOUT flip-kill, Hard-safe" THREADABLE or FUNDAMENTAL? -> decides m23-or-ceiling.
- RESOLVED/REJECTED chain: m22 0.672 / m21 (5ENtg) 0.597 (keep-more neutralized+Hard crater) / m17 (5FqAHka1) NOT
  QUALIFIED (django-11551 screener) / m20b-v2 (5DADz) 0.715. m22 key = ...c7e299 (same acct as m12, no confound).
  Platform command runbook: reports/platform_commands.md.

## ★ CORRECTED SCIENCE (this session — supersedes earlier cache/freeze/multiplier theories; do NOT relitigate)
1. **SCORE ≈ mean of per-run BASE OUTCOMES + a small ln ratio term. Verified + reconciled** (raw mean of 250 runs
   0.7685 = leaderboard 0.768 to 4 dp; king 0.9572=0.957). Per RUN: score = base + 0.5·clamp(ln(baseline_without /
   RAW tokens_with), −2,+2), base = {pass-pass +1, flip +4, break −4, fail-fail 0}, λ={0.5,0.5,0,0.1}. Task = mean
   of 5 runs.
2. **The global savings multiplier is applied ONCE over AGGREGATE tokens, NOT per-run/per-task — and it is SATURATED
   at 1.0 for all top miners** (m12 global savings 38.55%, +18.5pp margin over the 20% floor; king 41.6%; all =1.0).
   ⇒ the "27% of runs below the 20% floor" cost m12 EXACTLY 0.000. The savings-multiplier-floor lever is a NO-OP.
   (My earlier per-run-multiplier framing was a MECHANISM ERROR — corrected.)
3. **SCORE USES RAW TOKENS, not cache-weighted** (dashboard "weighted"=input+output+0.37·cached is display only).
   ⇒ **CACHING DOES NOT AFFECT SCORE. Cache lever DEAD.**
4. **The ln ratio term is MINOR** (±0.5·ln, m12≈king on raw savings: 26.7% vs 29.0% on shared pass-pass). The score
   is DOMINATED by the base outcomes (±1/±4/0). ⇒ **the game is PASS/BREAK (content-selection + agent behavior),
   NOT token compression.** Token-savings levers (harder/lighter/cache/floor) are all minor-to-zero.
5. **King's edge = pass-reliability + content-SELECTION quality on Easy+Medium** (more passes/flips, its breaks are
   NOT lopsidedly hard-compressed: 10 lower/9 higher tokens vs m12's 22/9 — its savings come from BETTER SELECTION,
   not blind trimming). NOT cache, NOT a savings-floor, NOT harder global compression. We likely cannot replicate it
   without the BANNED LLM/task/category logic.
6. **MEASURABILITY GATE (standing rule, adopt for ALL future candidates):** predicted category-mean delta must exceed
   ~0.25 (one 95% CI half-width; single-read category-mean SE≈0.12, within-task RAW-token swing median 2.4×) BEFORE
   spending a hotkey; acceptance requires a multi-read mean (≥3 scrapes) with ZERO Hard regression across all reads.

## ✅ LEVERS TESTED & REJECTED (well-evidenced — do NOT rebuild these)
- **m20b-v2 (superseded-view collapse): SCORED 0.715, REJECTED.** Worse than m12 on all 3, dented Hard 0.919→0.808.
  +10.64 on the 10 "fixable" tasks but −13.31 off-target → NET −2.67. PROVES "improve the 10 tasks" is NON-PREDICTIVE
  of the board (it green-lit a loser). reports/m20bv2_verdict_and_unified_theory.md.
- **AOW-lite / AOW-bet (freeze-on-emit, both built+verified): STRUCTURAL WALL.** To be byte-stable they either ==
  m12 (watchdog reverts every drop-turn) or keep the FULL trajectory at 0% savings → worse RAW-token ratio. The
  cache they buy is worthless (see #1). Files retained as reference; do NOT ship. reports/plan_beat_the_king.md.
- **Savings-multiplier-floor relief (workflow wgkcj0en4): NO-GO** — the multiplier is global+SATURATED (=1.0) so
  lifting below-floor runs = +0.000; the only real bit (ln term on passing below-floor runs) = feasible +0.016
  (~+0.004 after stripping 2 variance tasks), ~12× short of the +0.189 king gap, AND it's a wander/break trap (71%
  of m12 breaks used FEWER tokens than passing runs → compress-harder DRIVES breaks; 2 Hard tasks transit harvest),
  AND unvalidatable (4× below noise). Dead on mechanism + magnitude + safety + validatability.
- Earlier round: m13 (cap/gentling collapsed M/H), m14 (key confound), m15/m16/m18/m19-ref, depth EXP-1b — all
  rejected (see DISCOVERIES + miners.yaml).

## ★ BREAKS LEVER — REAL but DOWNGRADED (the current best hope, eyes open)
m12 has 17 break-runs (10 tasks). They ARE compression-content-driven (same agent for all miners; survivors pass).
BUT rigorously: (a) "17/17 fixable, 0 intrinsic" was SELECTION BIAS — pooled the 3 survivors break 20/150=13.3% on
those tasks; "≥1 survivor clean" ≈ expected max over 3×5-run lotteries (P~0.42). (b) 3/17 are premature collapses
(≤15 steps, agent quits before compression bites) → UNFIXABLE by retention. (c) king wins on savings not breaks
(misattribution). (d) the "fix the 10" success criterion green-lit m20b-v2 (a loser). VALIDATION is the real blocker:
the effect (+0.06–0.11) is < single-read noise (Overall sd~0.098; 17/250 breaks ±3.1% → re-read = 9–24 breaks) →
needs paired A/B candidate+fresh-m12 same-window, per-task diffs, **N≥15 reads/task**, gating on NET 50-task mean
(NOT the subset) + Hard≥0.919 on a powered sample. m17 is the cheap zero-downside first probe of this lever.

## STRATEGY (UPDATED 2026-06-25, workflow wie3sqfl0 — full: reports/m12_cons_and_strategy.md)
- **Greatest ABSOLUTE strategy = Easy-high triple-threat (wins Overall 57%)** — hinges on Easy (77% of our gap);
  INFEASIBLE for us (need Easy 0.412→~0.994) + DQ-prone. REJECT chasing Overall.
- **BEST FOR US = Pair(E,H) = 14.29% (3×).** Raise Easy 0.412→≥0.731 holding Hard≥0.919, via NOT-BREAKING baseline-
  passing tasks (SAFE uncapped lever; no flips; doesn't touch Hard; Easy feeds Overall too). m21 IS this.
- **Pair(M,H) REJECTED** (corrects earlier read): needs Medium→1.089 but pass-pass caps at ~1.0 → needs net-new
  FLIPS (risky lever), knife-edge, moat-correlated downside.
- **Two-track:** DEFEND Single-Hard (hold m12 LIVE, 4.76% near-zero-variance, any candidate must clear Hard≥0.919)
  + PURSUE Pair(E,H) via m21 (board-gated).
- ★ CAVEAT: "Easy=breaks" is UNVERIFIED (no comp-108 category map: CSV=217-266, scored=267-316, zero overlap; breaks
  may be TASK-INTRINSIC — m12 & king break the same tasks). TODO: build the comp-108 category map before trusting
  Easy-targeted numbers. m12 cons: CON1 upside-down routing (root), CON4 over-prune, CON2/3 error-guard/ratchet,
  CON5 live-tail truncation, CON7 blind-truncate-in-harvest (m21 fixes CON1/4/6/7).

## (prior) STRATEGY (current, honest)
- **DEFEND Hard 0.919** — our only income; nothing ships that risks it (m20b-v2's 0.808 is the cautionary event).
- **Medium is the most winnable category** — m12 OUT-FLIPS the king there (4 vs 2; wins sympy-23824/django-14017),
  loses it only to break-runs. Fixing Medium breaks (without losing flips/Hard) is the path to taking elements.
- **Easy = DEAD lever** (agent decisiveness, behavior-steering BANNED; m13/14/15/16 failed).
- **HONEST CEILING:** m12 is near its safe/validatable ceiling. The king's lead is a reproducible compression-savings
  advantage we can't match without trading into breaks/Hard, and the breaks lever is small + hard to validate.
  Remaining real gains require a compression REWRITE, validated platform-only. Next: a fresh deep-dive (user-driven)
  to find a king-beating approach we haven't tried. Evidence base: reports/{plan_beat_the_king, king_vs_m12_pertask_
  diagnosis, m12_runvariance_perrun, newking_5Ggq_medium_deepdive, m20bv2_verdict_and_unified_theory}.md +
  data/raw/platform_results/2026-06-24/*_perrun.json (m12,5Ggq,5DFvym,5DtEz,m20bv2).

## EVAL PIPELINE + DISCIPLINE
- Driver `experiments/candidates/H1M_m7_deeper_safe_v1/run_batch_eval_parallel.sh` (reads config/comp108_tasks.txt,
  50 real comp-108 instances). Analyzer `analyze_batch.py [rundir]`. **MAXJOBS=3 ONLY on this Mac** (4=OOM, 8=CPU-stall).
- **LOCAL ≠ PLATFORM (critical):** local replay does NOT reproduce platform breaks (django-13810 local m12 4/5 pass,
  platform 3/5 break) — the m13/m20b-v2 trap. Platform is also temporally noisy (Hard ±0.3). ⇒ decide ONLY on
  platform-SCORED results (never `evaluating`, never local-only); one variable; 2nd hotkey; m12 stays LIVE.

## Candidate files (miner/cot_compression/)
upload_miner_m7_compliant.py (=m12 LIVE, never touch) · upload_miner_m17.py (sha ac9519f0, UPLOADED→5FqAH, screening) ·
upload_miner_aow_lite.py / upload_miner_aow_bet.py (freeze experiments, REJECTED reference) · upload_miner_m20b_v2.py
(REJECTED) · _m12_1b/_m14/_m16/_m12_deeper/_m12_lighter (reference) · upload_miner_v11_m7.py (orig m7, NON-compliant).
