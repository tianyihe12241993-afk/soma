# NEXT_ACTIONS (handoff to the next session)

_Mode: ACTIVE comp 108 (CoT-Compression-4). Files are the source of truth. Full live status: state/CURRENT.md.
Eval runs on the Mac (Docker Desktop), NOT WSL2._

## TOP OF QUEUE (2026-06-25 ~20:55) — ★ RE-ANALYSIS DONE: PORTFOLIO path + new Hard-variance RISK. Plan below.
**Full: state/CURRENT.md top (workflow wiz2yq9to, 25 agents). Verified ownership: m12 holds Single-H (0.919, +0.107); share 4.76%.**
- [ ] ★ **NEW RISK: defend Single-Hard.** King's Hard is volatile under re-eval (drew up to 0.981 > our 0.919). Register
      ONE more BYTE-IDENTICAL m12 hotkey (insurance twin) → best-of-2 max cuts P(lose our 4.76%) from ~12-17% to ~1-3%,
      AND passively captures Pair(M,H) if king re-draws low Hard. USER action (upload, separate hotkey, same acct). Reliable, zero downside.
- [x] ~~GROWTH: EH-passthrough specialist (raise PASS_THROUGH_TOKENS)~~ — **VALIDATED NO-GO** (reports/m24_ehpass_verdict.md,
      validator /tmp/m24_ehpass_validator.py). Sweep over real comp-108 m12 trajectories: NO threshold satisfies Hard-routing==m12
      AND savings≥10% AND material Easy lift. Any raise >3500 re-routes Hard (≥20k → 6 Hard tasks, 449 diffs); the deep break-prone
      Easy tasks (django-12039 92% still harvest @10k) need ≥20k which craters Hard, while the safe window only rescues small
      already-passing Easy tasks. Easy lift far short of Pair(E,H) (need E>0.731) / Single-E (>0.923). Same Easy↔Hard size-overlap
      wall that put m12 on depth-routing. (Untested variant: DEPTH-gated passthrough — same Hard-early-route risk, platform-only outcome.)
- [ ] ★ **NOW THE TOP RELIABLE MOVE: register the byte-identical INSURANCE TWIN** (defense + passive Pair(M,H)). USER action.
      I'll give the exact upload command (reports/platform_commands.md cmd #1, new hotkey, same OpenRouter acct). Protects 4.76%
      (king Hard volatile, drew 0.981>0.919) AND holds passive position for Pair(M,H) → ~14.3% if king re-draws Hard <0.592.
- [x] ~~Probe depth-gated passthrough~~ — **NO-GO** (reports/depth_gated_passthrough_verdict.md). Per-category depths
      FULLY OVERLAP in comp-108 (Easy 12-89 med56 / Med 20-112 med49 / Hard 10-98 med53; Easy median DEEPER than Hard).
      No depth gate separates Easy from M/H; any D_pt lifting Easy_PT floods Med_PT(+1518 route chg)/Hard_PT(+2313) and
      halves savings. ROOT CAUSE proven on BOTH axes: comp-108 E/M/H are NON-SEPARABLE by any per-call signal -> active
      single-miner growth space CLOSED (see DISCOVERIES top).
## TOP OF QUEUE (2026-06-26) — ★ m25 BUILT + VERIFIED; USER to upload (the M,H coin-flip). Then gate on scored.
**Full: reports/m25_build.md + state/CURRENT.md top. m25 = upload_miner_m25.py sha 52fe47f9. m12 LIVE untouched/git-clean.**
- [ ] **USER: register a NEW hotkey + upload m25** (SAME OpenRouter acct as m12, …1e8a lineage). Cmd:
      `.venv/bin/python miner/upload_miner_with_openrouter_key.py --platform_url https://platform.thesoma.ai
      --wallet_name tony-miner --hotkey_name <NEW_M25_LABEL> --solution_file miner/cot_compression/upload_miner_m25.py
      --openrouter_api_key <OPENROUTER_KEY>`  then `make collect` (read score ONLY when status=scored).
- [ ] **ACCEPT GATE (>=3 scrapes):** Medium UP AND Hard>=0.919 AND flip-count >= m12. Else REJECT (m25 = rejected reference;
      m12 stays LIVE). Same gate that correctly killed m22.
- [ ] **What m25 is:** m12 + gated gentle break-fix (extractive truncation-sites only, NO drop-spans) + RESOLVED-gate +
      DECOUPLED state (emit break-fix, save m12-exact -> rich/Hard reads clean). Targets the real +4.958 Medium break-fix
      gains while hedging the m22 craters (deep-Hard via decouple, active-flip turns via gate). HONEST: coin-flip ~15-25%;
      residual shallow-flip leak (201 ships) + non-gateable pass-task new-breaks remain. Update miners.yaml m25sub hotkey post-upload.
- [ ] If m25 REJECTED: the active space is then fully exhausted (every combination tried) -> revert to MONITOR + next-round prep.

## (superseded by m25 build) TOP OF QUEUE (2026-06-25 ~23:00) — FULL-RESET: STOP active comp-108 work; MONITOR + NEXT-ROUND PREP.
**Full: reports/comp108_full_reset_analysis.md + state/CURRENT.md top (workflow wohsbvkmr; all numbers main-session-verified).**
- [ ] **POSTURE = HOLD m12 frozen + MONITOR. Do NOT build, do NOT spend a hotkey.** Active dethroning proven unrealistic
      (all 7 experimental hotkeys drop M AND H; E/M/H non-separable). We own only Single-H (4.76%, +0.107 cushion).
- [ ] **MONITOR each window via `make collect`:** (a) **5CaFqLaPBYTQ review_status** — if it flips scored→ it sweeps ALL
      7 elements incl our Single-H (existential; H=3.15 cheat-signature, currently failed review); (b) **king's (M,H) pair
      avg** — if it re-draws <0.9363, m12 auto-captures Pair(M,H) → ~14.3% (free, passive, the only positive-EV upside);
      (c) any new high-Hard rival that could take Single-H.
- [ ] **INSURANCE TWIN = KILLED** (do not register). Defends wrong threat (twin also ~0.919, can't beat a rival >0.919;
      m12 no observed downward variance). Supersedes the earlier twin recommendation.
- [ ] **NEXT-ROUND PREP (the one forward lever, CONDITIONAL, not authorized now):** global Medium safety-tuning to cut
      BREAK rate (m12 15% → toward newking 6%) WITHOUT category routing. Pre-build gate (all 4): zero Hard-route divergence
      vs m12 + savings≥10% + per-turn Medium break-RISK reduction + projected delta > 2.67pt variance floor. Build only
      into a LIVE next round, never against the frozen comp-108 board, never on projected lift alone.
- [ ] m12 (5Dz7) LIVE/untouched. All active single-miner levers exhausted+closed this session (see DISCOVERIES top).

### Validated DEAD/closed levers (do NOT rebuild)
- [x] ~~loop-detection-threshold sweep~~ — **NO-GO/no-op** (reports/loopguard_probe_verdict.md). The guard ALREADY
      fires on 67% of runs + ALL wander-prone runs (recur 4-12 >> 3); those break on-platform anyway. Loops = NORMAL
      behavior (re-reads/re-runs) across all categories incl. Medium → tuning down (2/12→90%) = false-positive nagging,
      up = less coverage. ~9% of breaks have no loop (premature patch). Guard is SATURATED, not under-tuned. Last
      compliant active lever CLOSED.
- [ ] ★ **ONLY position-improving move left = register the INSURANCE TWIN** (byte-identical m12, 2nd hotkey, same acct).
      Defends Single-Hard vs king's volatile Hard (drew 0.981>0.919) AND holds passive position for Pair(M,H) → ~14.3%
      if king re-draws Hard <0.592. USER action; cmd = reports/platform_commands.md #1 with a NEW hotkey label. Zero downside.
- [ ] (Monitor) fresh `make collect` each window to confirm standings + whether king Hard re-drew (opens Pair(M,H)).
- [ ] **Do NOT relitigate:** all single-miner CONTENT levers dead (13 falsified); break-fix family closed (m22/m23);
      beating the king on Overall is not reachable (agent-side consistency, banned to steer). Portfolio is the only new surface.
- [ ] Eval: MAXJOBS=3 on this Mac. Driver run_batch_eval_parallel.sh (50 comp-108 tasks; subset to 11 Easy+20 Hard for #1).

## (superseded) TOP OF QUEUE (2026-06-25 ~20:30) — m23 RESOLVED-gate audit = NO-GO. HOLD m12. Both break-fix paths now closed.
**Full: reports/m23_gate_audit.md + state/DECISIONS.md top + state/CURRENT.md top.**
- [ ] **m23 (RESOLVED-only break-fix + determinism pass) = NO-GO** after the mandatory pre-build gate audit. The gate
      CANNOT causally separate settled-Easy from flip turns (early flip-exploration is signal-identical). Real flip
      task sympy-24066 leaks 217/104/70 fires (lenient/strict/resolution-sig); only an overfit gate (G4) hit 0 and it
      misses a real Easy target. Determinism half = no-op (m12 already deterministic). m23 NOT built. Do NOT relitigate
      without NEW evidence (e.g., a gate that provably zero-fires on ≥the 3 flips AND django-13925/14017 trajectories).
- [ ] **HOLD m12 (5Dz7) LIVE** — 0.768 / Hard 0.919 field-best / 4.8% Single-Hard. It beats every candidate built
      (m17/m18/m20b-v2/m21/m22 + m23-blocked) and is our compliant ceiling. Decide ONLY on scored.
- [ ] **CLOSED levers (do NOT propose):** (a) smarter flip-preserving selector (<15%, zero-sum, lost 3×);
      (b) RESOLVED-gated break-fix (gate leaks, this audit); cache/freeze (RAW-token score); savings-floor (saturated);
      compress-harder (wander); keep-more (m21); m20b superseded-collapse. King's edge = consistency = agent-side, not
      our compliant lever.
- [ ] **Only structurally-new growth lever left:** favorable platform re-eval window OR a 2nd-hotkey portfolio
      specialist — both still blocked on the same agent-stochasticity wall (research track, not ready). m12 LIVE meanwhile.
- [ ] (Optional, NOT recommended) targeted local eval to capture django-13925/14017/sympy-16792/django-15037 m12
      trajectories — would harden the NO-GO; the causal leak already makes the call clear. MAXJOBS=3 on this Mac.

### Validated DEAD-ENDS (do NOT rebuild): cache/freeze lever (score uses RAW tokens — AOW-lite/AOW-bet structural
wall); m20b-v2 superseded-collapse (net −2.67, dented Hard 0.808); "improve the 10 break tasks" as a success
criterion (it green-lit m20b-v2, a loser → gate on NET 50-task mean); compress-harder-via-blind-drop (wander).
See state/DECISIONS.md + DISCOVERIES.md (top entries).

## (superseded) TOP OF QUEUE — ★ m20-BLIND A/B REJECTED (ratio backfired -> wander). Compress-harder family CLOSED.
Gated A/B (m12 vs m20-blind, 6 large/deep tasks x3): ratio went DOWN not up - m20b +21..74% tokens + more steps
(dropping superseded-view middles = needed content -> agent WANDERS to recover). Resolved nominally 11 vs 9 but
n=3 noise on capability-bound flips, swamped by token blow-up. Fails accept gate (ratio-up=NO). The A/B was the
oracle offline lacked: even the NARROWEST compress-harder cut fails the same wander way. ENTIRE compress-harder
family now closed (depth/m17/m18/m20-extractive/m20-blind). Ratio-bonus headroom real in formula but NOT
capturable - m12 keeps exactly what the agent needs. m20_blind sha 328fdcfa reference-only. Report:
m20_blind_ab_verdict.md. HOLD m12. Growth = portfolio specialist (2nd hotkey) or favorable re-eval window.

## (superseded) m20 (ratio-bonus / superseded-view) REJECTED offline. HOLD m12.
Ratio-bonus headroom is REAL (score=base+0.5*ln(ratio); m12 at +0.28 of max +1.0) BUT not safely capturable:
m20's safe collapse (extractive) PINS code signatures -> ZERO shrink on real code reads; truly-redundant re-reads
already caught by m12 near-dup; actual gain needs BLIND-dropping needed code = proven wander/break family. m12
already keeps exactly the safe content (signatures+error/test/diff+latest view). m20 sha 0be44494, reference-only.
Report: m20_superseded_verdict.md. Optional last-resort: m20-BLIND variant gated on same-window A/B (oracle we
lack offline); expectation modest-to-negative. HOLD m12.

## (superseded) m19 cache-stable REJECTED on offline validation. HOLD m12.
m19 (surgical cache-stable: froze truncation depth + drops-to-target) built + validated OFFLINE → REJECT (no paid
eval needed). FAILED: (1) churn NOT reduced (288=288 re-morph) — dominant churn is ASSISTANT TOOL-CALL STRIPPING
inherent to m12's drop-based harvest, not truncation depth; (2) medium ratio +31% lighter = M/H regression (m13
risk). FUNDAMENTAL TENSION confirmed: cache-stability vs m12's drop-based M/H aggressiveness conflict — the only
churn-free path is H3 mask-in-place (lighter + non-compliant markers = changes M/H). NO compliant M/H-preserving
cache-stable rewrite exists. Combined w/ forensics (breaks=first-decision solver stochasticity pre-churn): the
16-vs-6 -4 gap to king = window/sampling variance, NOT a fixable m12 stability defect. m19=reference-only, sha
dc4e5189. Report: m19_cache_stable_verdict.md. **HOLD m12 — at compliant ceiling on every measured axis.**

## (superseded) Stability lever found: SURGICAL cache-stable m19 (H3 port REJECTED)
m12 stability audit: deterministic (good) but ~3 msgs/turn prefix-churn (re-truncation under trunc2 escalation).
H3's cache-stable design is sound BUT not portable: NON-COMPLIANT markers (scanner FAIL: [SOMA/CONTEXT NOTE/
COMPRESSED HISTORY + "[old output elided]" etc) AND mask-vs-drop = lighter = M/H moat risk (m13-style). VIABLE
path = SURGICAL m19: freeze each old harvested msg to a FIXED content-only truncation depth (no re-deepening),
keep m12's drops + [[CMP]]/[[BLOCK]] markers + aggressiveness -> kills churn, preserves M/H, compliant by
construction. Lowest-risk lever yet (reduces perturbation, ratio-preserving). Expected -4-break impact MODEST
(forensics: breaks are first-decision stochastic, pre-churn) but firmer cache-hit/savings gain + matters on the
0.012 margin to #1. NOT built yet - awaiting go. Reports: h3_cache_stable_assessment.md + m12_stability_audit (/tmp).

## (superseded) TOP OF QUEUE (2026-06-24 FINAL) — ★ HOLD m12. Run-variance = SOLVER stochasticity (forensics), not fixable by us.
**Pass/fail trajectory forensics (reports/m12_pass_fail_forensics.md):** m12's −4 run-variance is the qwen3-coder
agent sampling worse trajectories (django-13810 fail=premature-patch step2; django-12039 fail=wander 58 tools/986k
tok) — OPPOSITE archetypes, fail runs had adequate/MORE context (NO missing-context). Compression is NOT the cause
→ no compression-preservation rule can fix it (m19/invariant-rule REJECTED). Closes the loop: depth/m17/m18/5DtEz
all failed because they targeted compression while the cause is the solver. **m12 is at our true ceiling.**
- [ ] **HOLD m12 (LIVE, #2, 0.768).** No more compression experiments — root cause is solver-stochastic, outside
      our compliant reach (can't steer agent / add attempts / context isn't the bottleneck).
- [ ] **Monitor only:** board each cycle (ignore evaluating scores); the dormant `validator/llm-semantic-scoring`
      branch (only thing that could change the run-scoring dynamic); comp task-set rotation.
- [ ] **PORTFOLIO** (2nd-hotkey specialist) remains the only structurally-new growth lever, but blocked: building
      a working specialist needs solving the same agent-stochasticity wall. Research track, not ready.

## (superseded) — HOLD m12. 5DtEz analyzed → m19 NOT justified; PORTFOLIO = research track.
**5DtEz84j deep-analysis (reports/5DtEz84j_tradeoff_analysis.md):** the king's edge = SAME-RATIO reliability
(6 −4-runs vs m12's 16 at equal ~1.75× compression). 5DtEz gets Easy by RELOCATING breaks (easy↓/medium↑), net
0.714 < m12 0.768. So: (a) **do NOT build m19** persistent-small — 5DtEz isn't doing lightness (it compresses
MORE), break-relocation predicts net ≈/< m12; (b) copying any rival tradeoff is net-worse; (c) the only
structurally-new lever is **PORTFOLIO** — keep m12 as M/H specialist + a SEPARATE 2nd-hotkey E-specialist to grab
Easy/(E,H) elements (~14%→~25%+ share), sidestepping the single-miner bind. BLOCKED on the open problem: we can't
yet build a working Easy specialist (5 attempts failed; rivals' schemes opaque). Treat portfolio as RESEARCH, not
a ready move. m19 spec exists in the report but is NOT approved/justified. m12 stays LIVE.

## (superseded) — HOLD m12. m18 REJECTED. 4 levers dead. Easy↔Hard is structural.
**m18 (size-gated adaptive-light) REJECTED** at Stage-1 gate: ultralight fired on the shallow early turns of HARD
controls and BROKE them (django-13158 3/3→0/3). Fundamental flaw — easy vs early-hard are indistinguishable, so a
single compliant miner CANNOT win both Easy and Hard; m12's Hard+Medium choice is a defensible local optimum.
Report: reports/m18_stage1_verdict.md. m18 = reference-only; m12 stays LIVE.

## (superseded) earlier top-of-queue — HOLD m12. 3 levers dead (depth, content-selection, lightness). No build.
**State:** m12 #2 (0.768), 0.012 behind king 5DFvymSeEw 0.780 (beats us ONLY on Easy). The "new king" 5DAh2rUM
**COLLAPSED 0.887→0.051** (Hard −3.6 on finalization — its light 1.41× compression broke Hard). m12 Hard 0.919 =
field-best by a mile = our durable moat.
- [x] EXP-1b → HOLD (depth dead). m17 (content-selective harvest) → REJECTED (A/B partial: +32% tokens, +breaks,
      fewer resolved = agent-wander, same as depth). reliability/lightness A/B → SHELVED (light king died on Hard).
- [ ] **NO ACTIVE BUILD. HOLD m12.** Three compliant levers now tested & dead: depth (EXP-1b), content-selection
      (m17), lightness (king's collapse + EXP-1b). All fail the same way: perturbing m12's output → agent wander →
      more run-to-run breaks. m12 is at our compliant ceiling. DEFEND M+H (esp. the Hard moat).
- [ ] **Recurring monitor (low effort):** re-scrape board (`make collect`) for new/finalized rivals — DON'T act on
      `evaluating` scores (5DAh2rUM proved why). Watch the in-flux upstream scoring layer (penalty/formula/llm-
      semantic branches) — that could shift incentives more than any miner tweak. (E,H) is close: m12 needs Easy
      ≥0.49 to take it from the king — but Easy is agent-bound + lightness (the obvious Easy lever) is now proven
      dangerous on Hard. Not a mandate.
- [ ] **EVAL: MAXJOBS=3 ONLY on this Mac** (MAXJOBS=4 OOM-crashed Docker; 8 CPU-stalled). Watch docker MemTotal=0
      (OOM) + 1-sec "ok" (bogus). A higher-RAM/more-core RunPod box WOULD help now (CPU+patch-eval-RAM are limits).
- [ ] Ongoing: watch rivals (only king 0.780 ahead; #3-4 ≤0.66), in-flux upstream scoring layer
      (penalty-fix/scoring-formula/llm-semantic-scoring branches), comp-108 task-set rotation. m15 full eval
      (read only when status=scored + non-null runs). reports: comp108_strategy_plan.md, comp108_headroom.md,
      king_vs_m12_easy.md, m16_steptest_result.md.
- [ ] DISCIPLINE: same-window local A/B only (platform temporally noisy); hold key/window constant; never
      decide off a single platform score; harvest stays byte-identical (M+H moat).

## (earlier note) ★ EASY IS A DEAD LEVER; DEFEND M+H — superseded by the plan above (Easy is a low-confidence
## NUDGE at zero risk, not fully dead; the +0.06 target is small enough to attempt safely)
Step-test verdict (reports/m16_steptest_result.md): m16 took MORE agent_steps (40.2 vs 34.7), DISPROVING the
"cleaner compression → fewer steps → better Easy" hypothesis. With m13/m14/m15/m16 all falsified, **Easy is
agent-decisiveness-bound and UNREACHABLE via our compliant compression lever.** m12 Easy ~0.41 ≈ our ceiling.
- [ ] **DO NOT submit m16** (no win, +23% tokens, uncertain value). Reference only. Stop Easy-via-compression.
- [ ] **Strategy = HOLD/EXTEND the M+H moat.** m12 is field #1 (Medium 0.953, Hard 0.919); king (0.780) beats
      m12 (0.768) only on Easy we can't match. m12 is near our practical ceiling for a compliant
      compression-only miner. Keep m12 LIVE.
- [ ] **WATCH (low-effort): m15's full eval** (still queued; read only when runs are non-null); rivals each
      cycle; the in-flux upstream scoring layer (penalty-fix / scoring-formula / validator/llm-semantic-scoring
      branches — re-check before drawing conclusions); re-pull the comp-108 task set if it rotates.
- [ ] If pursuing more: the only real lever left is M/H-SPECIFIC compression gains (more flips without leaking
      Medium — TIGHT, eval-gated on the REAL comp-108 tasks), NOT Easy. High bar; low expected headroom.

## (SUPERSEDED) earlier RESEARCH RESET: reports/comp108_research_reset.md
**Comp-108 tasks are 100% different from comp-107 (0 overlap) → ALL 107 task-knowledge is moot, AND local eval
has been on the WRONG (107) tasks the whole time** — the root cause of every local-vs-platform divergence.
RESET STEPS:
1. **RE-POINT local eval at the 50 comp-108 instances** (un-masked; from the m12 scrape task_names) — #1 fix;
   update run_batch_eval TASKS. Without it, local eval is worthless for 108.
2. Re-characterize on 108: which break under harvest, which are flip-candidates, which fail-fail.
3. Get per-task E/M/H for the 50 (SWE-bench difficulty data; platform doesn't expose it).
4. Design the Easy lever that STILL clears the **≥10% weighted-savings gate** (never full-passthrough —
   never-inflate alone likely fails it; m15 is the live test). HOLD M+H (don't soften the harvest; m13 proved
   softening collapses H+M).
5. Trust only PLATFORM scores (same account/window) for verdicts; watch temporal provider variance.
- [ ] **WATCH m15:** proceeds to full 50-eval (passed both screening gates) OR stuck task_count=5 / "not
      qualified" (failed the ≥10% weighted-savings gate → decisive verdict against never-inflate).

## (SUPERSEDED by the reset above) prior comp-108 plan — reports/improvement_roadmap_comp108.md
Real 108 race (scored only): king 5DFvymSeEw 0.780 (E0.812/M0.934/H0.596) vs m12 0.768 (E0.412/M0.953/H0.919),
we're #2, dominant M+H, weak Easy. (Earlier "Easy floor ~0.49" still directionally right, but the ≥10%
weighted-savings gate + 108-task-specific work now gate it.) m12 analysis: reports/m12_comp108_analysis.md.
- [x] ~~PHASE 1 build m12.1~~ — built + eval'd → **REJECTED (do not ship): over-routed Medium (+20% tok/call,
      ~20% LESS Medium compression) for only 1 fewer fragile break.** m12 stays live. (file exists:
      upload_miner_m12_1.py — kept as reference, NOT to submit.)
- [x] ~~BUILD + EVAL m12.1b~~ — DONE (2026-06-23). Built `upload_miner_m12_1b.py` (never-inflate + cap +
      deterministic + tightened routing), 15/15 offline checks PASS, compliance PASS. Full RUNS=5 regression
      (100/100 ok): **NO-SUBMIT — TIE with m12 (34 vs 33/50)**, HardFragile +3 (incl django-14493 1/5→5/5),
      Medium preserved (+1.0% tok/call), but **Easy regressed 10→7** (reject trigger; likely agent noise as
      m12_1b is mechanism-inert on Easy, but n=10 unproven) + 2 fragile −1. Keep m12 live. Full:
      `reports/m121b_eval_results.md`; decision in DECISIONS.md.
- [x] ~~submit m12_1b + check platform~~ — DONE (2026-06-23): uploaded to fresh hotkey **m13**, scored
      **0.571 vs m12 0.768 → REJECTED.** Hard COLLAPSED 0.919→0.434, Medium 0.953→0.718; only Easy rose
      0.412→0.561. The aggressiveness-cap/gentler-routing design is FALSIFIED (m12's harvest is net-positive on
      H+M; softening it lost our edge). LOCAL EVAL MISLED (showed fragile +3). m12 stays LIVE/BEST. Full:
      `reports/m13_platform_result.md`; DECISIONS + DISCOVERIES updated. (The RUNS=10 local re-eval is now MOOT
      — platform gave the decisive answer.)
- [x] ~~BUILD m14_never_inflate_only~~ — DONE (2026-06-23): `upload_miner_m14.py` = m12 + never-inflate guard
      ONLY (sha cf… ; diff = guard block + 3 metadata fields + return; ALL m13 constructs absent: no
      MAX_COMPRESSION_RATIO/cap/repeated_failure/shallow/error-guard). Offline 8/8 PASS (verify_m14.py):
      Medium + Hard/deep BYTE-IDENTICAL to m12, never-inflate fires only on inflation (m12 0.997x→m14 1.000x),
      m14==m12 exactly where m12 didn't inflate, protection preserved, compliance PASS. Smoke 6/6 ok (m12 vs
      m14, Med/Hard/Easy, RUNS=1): m14 bakes + runs e2e, analyzer reads, 0 429s/collisions. READY to submit.
- [ ] **SUBMIT m14 to a FRESH hotkey** (NOT m12's, NOT m13's). Register a new hotkey, then upload
      `upload_miner_m14.py` with the same key (user runs — classifier-blocked for me). m12 stays LIVE; m13
      stays rejected/reference. Accept m14 over m12 only if: Easy ↑ or competitive, Medium ≈ m12, Hard ≈ m12,
      review-PASS, no new break pattern. (Expectation: H+M ≈ m12 since m14 is byte-identical there; Easy may
      lift like m13's +0.149 since never-inflate is the isolated cause.)
- [ ] **Reframe strategy:** our edge IS the aggressive harvest on H+M — do NOT globally soften it. Grow H+M via
      H/M-SPECIFIC gains (not gentling); use gentleness ONLY where it pays (Easy). Drop the cap/rich-fallback.
- [ ] ~~BUILD m12.1b (old spec)~~ — superseded; RESHAPED 2026-06-23 by the per-run finding
      (`reports/m12_run_variance_analysis.md`): RUN-VARIANCE is the dominant lever, not inflation. m12's "7
      flips" are mostly partial (only 2 of 7 are 5/5) and 17 pass-pass tasks break on 2-3 of 5 runs. So
      m12.1b's PRIMARY goal = run-determinism + bounded aggressiveness:
        1. **never-inflate** (keep — fixes <1× inflated breaks like t313/t281; pure win)
        2. **CAP per-call aggressiveness** (NEW, key): never let one compression call hit a destructive ratio
           (the 10-20× break runs on t268/269/307/315); always retain a load-bearing floor.
        3. **deterministic compression** (NEW): same input → same output, so a passable task lands 5/5 instead
           of gambling per run.
        4. tighten 1b gentle-routing on genuinely break-prone signals only (NOT shallow-Medium — m12.1's bug).
      Offline + `scripts/check_prompt_compliance.py` PASS, then real-eval vs m12 on the Mac.
      **Re-eval bar (UPDATED): run at RUNS=5 and measure BREAK-RATE + 5/5 consistency (not just aggregate
      pass) — fewer break runs than m12, Medium tok/call ≈ m12, never-inflate verified.** (Parallel driver
      makes RUNS=5 affordable; MAXJOBS=3 cleared by the smoke.)
- [x] ~~SPEED UP the eval~~ — DONE (2026-06-23): eval is LLM-latency-bound (CPU near-idle), so built
      `run_batch_eval_parallel.sh` (MAXJOBS concurrent solves; default 3 for 12GB Docker). bash-3.2 slot gate
      dry-tested (peak=MAXJOBS); analyzer takes an explicit RUN_DIR + matches `*_H1M_*batch`. Use this for the
      m12.1b eval. (RunPod GPU = wrong product; details in DISCOVERIES + CURRENT eval section.)
      **REAL-SOLVE smoke PASSED (2026-06-23, run 2026-06-23_041345_H1M_pbatch):** MAXJOBS=2, m12, 2 Medium
      tasks. Both solves ran CONCURRENTLY (2 gateways coexisted cleanly, 0 collisions) and both RESOLVED 2/2,
      0 breaks; wall-clock ~5.5 min vs ~11 serial (~2x). Peak Docker mem 3486MiB / 11947MiB (incl ~680MiB
      LibreChat stack) → two solves added only ~2.8GB; peak single openclaw container 710MiB. No 429s/timeouts.
      Per-solve plugin copies isolated + auto-cleaned. analyze_batch.py read the `_pbatch` output unchanged
      (explicit arg + auto-discovery). **CLEARED: full regressions can run at MAXJOBS=3 (huge RAM headroom).**
      ⚠ Full m12-vs-m12.1b regression is BLOCKED on building m12.1b first (it does not exist yet).
- [ ] **CONFIRM upload cadence:** one upload per window per hotkey (107 rule) OR can we re-upload an improved
      solution to m12's hotkey mid-round? Sets how fast we iterate (re-upload vs fresh-hotkey burn vs wait).
- [ ] Phase 2 smart adaptive depth (m12.2, deeper only where proven-safe); Phase 3 run-variance robustness;
      Phase 4 Easy floor; Phase 5 ongoing dashboard-driven iteration + staged pipeline. (roadmap doc)
- [ ] WATCH m12 + rivals each cycle (esp. 5CwZBKyL in-queue 1.062, only 5 screeners done). H4b/H3 = reference
      only (deeper breaks more — wrong direction this round). Do NOT replace m12 until m12.1 beats it on eval.
- [x] ~~build `h1m@deep-compliant`~~ — DONE: **H4b_compliant_h1m_deep** at
      `miner/cot_compression/upload_miner_h4b_compliant.py` (h1m@deep engine, TARGET 5200 baked; coach/force-stop/
      digest-injection removed; only `[[CMP]]`/`[[BLOCK N]]`/loop_detected markers). Scanner PASS, 0 banned
      strings, offline 15/15, **compresses +8.35% MORE than m7-compliant**, 0 protection regressions. STAGED,
      NOT submitted.
- [ ] **DECISION: submit H4b only AFTER m12's review/score signal** (recommended) — m12 tests whether our
      compliant approach passes review on the new round + how m7-class scores; H4b's deeper profile carries more
      fragile-break risk, so don't spend a 2nd registration burn until m12 de-risks it. To parallel-submit
      sooner, register a 2nd hotkey and I'll upload H4b to it (same flow as m12). Do NOT replace m12.
- [ ] **REDIRECT: build the next-round compliant candidate on h1m@deep's engine, NOT H3.** The H3 eval
      (run 2026-06-22_122215) FALSIFIED the cache-stable bet: **h1m@deep gate-ACCEPTed (+28.1%, 0 new breaks,
      Medium 8/8); both H3 profiles REJECTed** (new fragile breaks + worse/negative cache & compression). So
      apply the proven H4 compliance treatment (strip coach/force-stop, switch to `[[CMP]]`/`[[BLOCK N]]`/
      `Same response as in [[BLOCK N]].` markers, loop-detection → 2 allowed reason strings) to **h1m_miner.py
      @deep**, NOT h3_miner.py. Then real-eval that coach-free h1m@deep-compliant vs m7 (Medium-sanity +
      fragile, 2 runs) to confirm pass-safety holds with the coach gone. (H4_compliant_cache_stable stays as a
      reference but is built on the losing engine.)
- [ ] **Fragile breaks are the open problem for ANY deep compression** (h3 2–3, h1m/m7 1 new break). Either
      harden the guard further or exclude the ~4 fragile signatures from deepening before shipping.
- [ ] **Investigate WHY t1–t5/t7 failed review** (SWE hints injection / non-compliant prompt mods, NOT ratio)
      to confirm our compression-only approach carries no residual DQ risk.
- [ ] Pull the FULL comp-107 board (beyond tracked top-10) to confirm real element winners among valid miners
      (tracked recompute: m7 #2 overall + Medium ≈tie with t9).
- [ ] If we need any marker beyond the published list, request it in the public channel FIRST.

## H1M real-task experiment — DONE offline (2026-06-22): experiments/runs/2026-06-22_005707_H1M_eval/
- m7 Medium-first baseline (REAL): 7/7 pass, 0% neg-run, 0 broke, avg 3.02×, Medium est score 1.690.
- h1m@deep projected ~3.43× (+13.7%), h1m@medium ~3.34× (+10.8%); offline gate PASS (ratio≥8%, guard works,
  protections intact). Verdict: **ADVANCE candidate-only**. Real pass/neg-run/broke = **PENDING_EVAL**.
- [x] ~~Implement + prove the full ingestion gate~~ — DONE (2026-06-22): `h1m_run.py --results <file>` now
      parses real per-task results, computes candidate pass/neg-run/broke/ratio/Medium-score, diffs vs m7,
      and emits ACCEPT/REJECT. Proven end-to-end with fixtures/h1m_deep_results_{PASS,FAIL}.csv
      (PASS→ACCEPT; FAIL→REJECT on 4 safety checks while compression still +15% — rejects on safety, not ratio).
- [x] ~~Build the real SWE-bench eval stack~~ — DONE (2026-06-22): Docker up; SOMA-benchmark + SOMA-plugin
      (public) cloned; uv + soma-bench; SWE-rebench harness (swebench 4.0.3); compression-service image built;
      m7 miner injected + compression service live; model openrouter/qwen/qwen3-coder. Driver:
      experiments/candidates/H1M_m7_deeper_safe_v1/run_one_solve.sh. .env at ~/SOMA-benchmark (key redacted/600).
- [x] ~~Real eval blocked~~ — DIAGNOSED 2026-06-22: it's **WSL2**, not Docker Desktop. The OpenClaw sandbox-skills `rm` (Device-or-resource-busy) reproduces on Docker Desktop + native docker.io, 2 openclaw images, root+non-root — only common factor is the WSL2 kernel's mount semantics under DinD. Past working laptop was **macOS (LinuxKit VM)** -> real-Linux mounts work.
- [ ] **Run the eval on a real-Linux Docker host (your Mac / Linux VM / cloud).** One command: clone this soma repo there, `export OPENROUTER_API_KEY=...`, then `bash experiments/candidates/H1M_m7_deeper_safe_v1/run_real_eval.sh` -> smoke (m7/h1m@medium/h1m@deep on 2 tasks) -> gate CSV -> `h1m_run.py --results`. STOP after smoke; confirm before full Medium-first. NOT possible under WSL2.

## Highest leverage — CANDIDATE 1 BUILT; needs platform eval next
- [x] ~~Build the H1 candidate, Medium-first~~ — DONE: H1M_m7_deeper_safe_v1 (experiments/candidates/).
      Offline-validated: h1m@deep +13.7% deeper, 0 regress, protections+pairing intact, fragile guard works,
      A/B(h1m@m7≡m7) ok. Report: experiments/reports/H1M_m7_deeper_safe_v1.md.
- [ ] **RUN H1M on the SOMA SWE-bench eval** (the ONE thing offline can't do): get real pass-rate / neg-run /
      Medium score for h1m@deep (+ medium fallback) on the Medium-first H1 targets. Needs the eval env
      (Docker+agent+OpenRouter). Then dump per-task results → `python scripts/run_experiment_matrix.py
      --manifest experiments/manifests/H1_*.yaml --results <file>` → `make summarize` → apply the gate.
- [ ] Only AFTER the eval confirms Medium pass-rate/neg-run hold: decide whether H1M_deep replaces m7 as base.
- [ ] **Add the H3 fragile guard for ~4 signatures only:** sympy-17139 (m7), + sympy-16766 / django-11239 /
      django-14493 (flip-only). Conservative near-pass-through fallback; do NOT touch the safe targets.
- [ ] **Do NOT chase the 2 solving-gap Hard tasks with compression** (django-14999, sympy-22714) — m7 fails
      where the leader solves; that's agent behavior, not our compression lever.
- [ ] **Run it through the gate:** local replay → dump per-task results → `python scripts/run_experiment_matrix.py
      --manifest experiments/manifests/H1_*.yaml --results <file>` → `make summarize`. Gate in experiment_backlog.md.

## Detailed data — SOLVED (keyless)
- [x] ~~Get ALL detailed data incl per-run~~ — DONE. `make runs` (scripts/collect_runs.py) scrapes per-run
      keyless via the dashboard server action; `scripts/normalize_run_scores.py` → data/processed/run_scores.jsonl
      + reports/run_variance.md. No API key needed (earlier conclusion corrected).
- [x] ~~task→category map~~ — DONE (config/task_categories.csv from extension-sb114). Medium/Hard unblocked.
- [ ] Optional: `make runs ARGS="--all"` for a full-field per-run sweep of ALL ~228 miners (~20 min, polite throttle).

## Remaining missing data (marked, not invented)
- [ ] **task→category map** (E/M/H per of the 50 tasks). Fill `config/task_categories.csv`
      (template: `data/raw/platform_results/TASK_CATEGORIES_TEMPLATE.csv`), then `make research`.
      Unblocks: Medium/Hard task-level attribution, H2_medium_specialist, the Medium gate.
- [ ] **token-type split** (input / cached-input / output per task) for H4 weighted-cost readiness.
      Add columns to the import schema when available.
- [ ] (Optional) **platform upload receipts** (hotkey+version+timestamp) → close the label audit to 100%.

## Hygiene
- [ ] Re-run `make detail` periodically only if you want fresher rival scrapes (comp is over; board is static).
- [x] ~~WSL env + soma_shared~~ — DONE (env ready; soma_shared 0.1.0 in venv). Upload path needs only a wallet,
      but we are NOT submitting, so wallet is not required for research.

## First three experiments to run (priority)
1. **H1_m7_deeper_safe_compression** — primary lever (ratio ↑ without breaking passes).
2. **H3_fragile_task_guard** — protect the broke-baseline cases so H1 can push safely.
3. **H2_medium_specialist** — our closest reward element; BLOCKED until task→category map imported.
