# DECISIONS (durable; don't relitigate)

## 2026-06-26 — ★★ WEIGHTED-TOKEN regime: DIRECTION = cache-stable / near-passthrough; raw-token plans SUPERSEDED
Scoring changed to weighted tokens (commit b79fcaee; weighted = 1·input + (1/3)·cached + 3·output; flip 4→2). This is an
EXTERNAL platform change, not a relitigation — it OVERTURNS the raw-token-era decisions below (they were correct then).
- **DIRECTION (do not relitigate): build CACHE-STABLE compressors; the winning shape is NEAR-PASSTHROUGH / stateless
  prefix-stable.** The dominant lever is cache-stability (stable emitted prefix → cached at 1/3). Aggressive harvest
  drop/prune is DEAD (busts cache → negative score; m12 cratered 0.768→0.130). Avoiding breaks ≫ flips now (4:2).
- **aow_bet (freeze-on-emit) = NO-GO** (Codex): its save_state carries the larger frozen output → rich sees a different
  trajectory than m12 = the proven m21/m22 Hard-crater. ⇒ cache-stable candidates MUST be STATELESS / single-mode.
- **np1 (m26, 5Ekcy) is the candidate** — stateless idempotent per-message cap, prefix-stability 100% offline, Codex-audited
  (inflation blocker fixed), UPLOADED + screening. Decision on next steps gated on its SCORED result.
- **SUPERSEDED (raw-token-era, do NOT pursue until re-derived under weighted tokens):** the E/M/H specialist game, the
  7-element ownership analysis, two-singles ~9.52%, m25 Easy-specialist / m27 Pair(E,H) / whole-architecture frontier,
  "defend Hard 0.919" (Hard is now low for everyone, field max 0.342). These remain in the record as raw-token-era history.

## 2026-06-26 — WHOLE-ARCHITECTURE deep-dive ("leave m12"): ceiling UNCHANGED; Pair(E,H) as a TARGET = NO-GO; two record corrections
User reframe: stop anchoring on m12, is the architecture itself the ceiling? Re-derived from raw per-run JSON (Claude+Codex, matches board 3dp; report whole_architecture_deepdive.md).
- **Reframe was RIGHT on framing, WRONG on the hope.** RIGHT: m12 = the HARD vertex (field-best); don't improve it, ADD
  specialists at other vertices (portfolio = MAX per element). WRONG: there is no from-scratch single miner that beats the king —
  every Easy-capable miner in the field pays elsewhere (king pays Hard 0.727; 5DtEz pays Medium 0.499; m25 pays Hard 0.536).
- **Pair(E,H) as a deliberate TARGET = NO-GO (both models).** 5DtEz proves E0.837+H0.813 coexist (pair 0.825), and the old m24
  EH-NO-GO used the wrong constraint (preserve m12 H0.919; Pair(E,H) only needs pair>0.825). BUT 5DtEz is the SAME perturbation
  tradeoff as m25 — kills flips, makes new breaks — its damage merely landed on MEDIUM not Hard. We can't steer which category
  the damage hits (W-NS), can't validate offline (NO comp-108 E/M/H map for 267-316), and m25 (our only real attempt) put damage
  on HARD. So: NEVER build a miner TARGETING Pair(E,H). It remains only an unbankable lottery upside of a Single-E (m26) build.
- **RECORD CORRECTIONS (re-derived ground truth, supersede prior chain):** (1) **Flips are TIED** — m12 16 ≈ king 17 flip-runs,
  6 shared tasks; m12 has NO flip edge (the "m12 out-flips king" claim was overgeneralized from dj-14017 alone). (2) **The
  "frontier" is NOT "nobody is good at all 3"** — the king IS balanced (E0.858∧M1.281∧H0.727, all ≥0.7); the true statement is
  "no observed miner pairs king-level E/M with m12-level Hard." Overall is unreachable FOR US (our Easy lever craters our Hard),
  not provably impossible for everyone. (3) m12 does NOT already own Pair(M,H) — king Medium really is ~1.281 (board total
  arithmetic confirms: mean(0.858,1.281,0.727)=0.955≈0.957; the per-run "0.909" reconstruction was wrong). Pair(M,H)=passive only.
- **NET ceiling unchanged = ~9.52%** (m12 Single-H + m26 Single-E). The deep-dive verified the ceiling adversarially instead of
  assuming it; it did not move it. m12 LIVE/untouched; nothing built.

## 2026-06-26 — m25 SCORED (Easy-specialist proof); m27 Easy+Hard dual-mode = NO-GO; growth path = TWO SINGLES, not Pair(E,H)
- **m25 (5GpB36) SCORED E0.859/M0.667/H0.536, zero penalty.** Failed as m12-replacement (Hard cratered) — m12 stays LIVE.
  But Easy +0.447 = #2 field → #2 on Single-E (+0.064 to win). MECHANISM (Claude+Codex): the blind→extractive swap is a
  high-variance content PERTURBATION; the Easy gain is ~86% pass-pass BOOST (perturbation), only ~14% ratio + a little
  break-fix; it is STRICTLY anti-flip (0 new flips, killed 3) and destabilizes passing tasks (−10.6/18) → that is why M/H
  cratered. This is the "opposite result" root cause.
- **m27 (Easy+Hard DUAL-MODE specialist, Pair(E,H)) = NO-GO** (Claude+Codex independent, reports/m27_eh_specialist.md). The
  settled-vs-exploration router CANNOT separate where the perturbation helps from where it hurts — the help-fires and
  hurt-fires have IDENTICAL per-turn signal distributions (depth/tokens/ratio/still_failing). Hard protection unachievable
  (the router producing Easy is the one perturbing Hard; H stays ≈0.536). The non-perturbing alternative (passthrough) loses
  the 86%-perturbation boost (E<0.84) + balloons tokens on harvest turns (savings-gate fail). m27 = m25's gate relabeled, not distinct.
- **DURABLE: Pair(E,H) needs ONE miner high on BOTH E and H — impossible with our mechanism** (Easy needs perturbing
  compression of settled turns; Hard needs un-perturbed full trajectory; same router can't do both). So do NOT pursue a
  Pair(E,H)/dual-mode miner. The reachable ~9.52% = TWO SINGLES: m12 (Single-H) + an EASY-ONLY specialist (m26, abandons
  Hard, target Single-E >0.923). m26 is a SEPARATE candidate (user decision pending); design via the dual-agent protocol.
- Dual-agent (Claude+Codex) protocol is now OPERATIONAL and codified in CLAUDE.md; used for the m25 pre-upload audit, the
  beat-the-king re-analysis, the methods/recombination review, the m25 mechanism, and this m27 NO-GO.

## 2026-06-25 — FULL-RESET VERDICT (workflow wohsbvkmr): STOP active comp-108 miner work; HOLD m12 + MONITOR + NEXT-ROUND PREP
Scientific reset (10 agents, real data, adversarially red-teamed; all load-bearing numbers independently re-verified by
main session). Report: reports/comp108_full_reset_analysis.md. DURABLE conclusions:
- **Active dethroning of comp-108 is UNREALISTIC.** We own exactly 1 of 7 elements: Single-H (m12 0.9193, +0.107 cushion)
  = 4.76%. PROOF: all 7 of our scored experimental hotkeys post ΔMedium<0 AND ΔHard<0 vs m12 → m12 is our M+H ceiling;
  best Easy ever (0.755) cratered Hard to 0.243; Pair(E,H) needs E≥0.73 AND H≥0.92 together (mutually exclusive). Root:
  E/M/H non-separable by any per-call signal. m12 Easy 0.412 = 35% fail-fail (unsolvable) + 12% breaks, not a fixable gap.
- **DECISION: STOP active miner work. HOLD m12 frozen. MONITOR + prepare next round. Spend NO hotkey.**
- **ONLY positive-EV upside = PASSIVE Pair(M,H):** m12 #2 (0.9363); if king's (M,H) PAIR avg re-draws <0.9363, m12 auto-
  inherits +9.52%→~14.3%. Free, no build, no risk; probability UNQUANTIFIABLE (don't assign the 1-in-21 dip — survivorship).
- **INSURANCE TWIN = KILLED** (corrects/retracts the earlier 2× recommendation): defends the wrong threat (a twin is also
  ~0.919, can't beat a rival exceeding 0.919; m12 shows no downward re-eval variance). Do not register it.
- **NEW LIVE RISK (monitor):** failed-review miner 5CaFqLaPBYTQ (E1.26/M1.61/H3.15/tot2.02) would sweep ALL 7 elements incl
  Single-H if reinstated. Our 4.76% safe only while platform review keeps it off (H=3.15 = prompt-cheat signature).
- **ONE forward lever (CONDITIONAL, NEXT ROUND only, not authorized now):** global Medium safety-tuning to cut BREAK rate
  (m12 15%→newking 6%) WITHOUT category routing; gate = zero Hard-route divergence + savings≥10% + Medium break-RISK down
  + delta>2.67pt variance floor; build only into a live next round, never on projected lift.
- All active single-miner levers now exhaustively closed (break-fix m22/m23, token+depth passthrough m24/depth, loopguard,
  content softening m13, compress-harder, keep-more, cache, savings-floor). The compliant active space is empty.

## 2026-06-25 — BEAT-THE-KING RE-ANALYSIS (workflow wiz2yq9to, 25 agents): PORTFOLIO is the only growth surface; defend Hard
After NO-GOing m23, the user rejected "hold m12" and demanded creative+reliable alternatives. A 4-phase fan-out
(ground→ideate 5 lenses→adversarial red-team→synthesize) verified live element ownership and produced 16 candidates:
**0 PURSUE, 3 MAYBE, 13 KILL.** Durable conclusions:
- **Verified ownership (live snap 2026-06-25/192615):** m12 HOLDS Single-Hard (0.9193, +0.107 cushion); share 4.76%.
  king 5Ggq wins Overall+(E,M)+(M,H)+Single-M; 5DtEz wins (E,H); 5GCWaCnb wins Single-E. (old-king eligibility resolved.)
- **All single-miner CONTENT levers remain dead.** The ONLY structurally-new surface is the PORTFOLIO (multi-hotkey
  specialists) — and the platform PROVABLY rewards extreme specialists (5DAh2r/5FUTAP win elements with Hard = −3.6/−3.87).
- **NEW RISK (durable):** the king's Hard is VOLATILE under re-eval (0.433→0.833→0.981→0.727 in one window) while m12's is
  pinned 0.919. At 0.981 the king takes Single-Hard. Our income is more exposed than prior notes implied → DEFEND it.
- **PLAN (separate hotkeys; m12 LIVE untouched; user does all uploads):** (1) GROWTH = EH-passthrough specialist (raise
  PASS_THROUGH_TOKENS so Easy passes through untouched; route Hard to unchanged rich; target Pair(E,H) +9.52%→~14.3%; ~20%
  end-to-end; OFFLINE-validate routing==m12 + savings≥10% BEFORE spend). (2) DEFENSE = byte-identical m12 insurance twin
  (best-of-2 max cuts P(lose Single-Hard) ~12-17%→~1-3%; also passively captures Pair(M,H) if king re-draws low Hard).
  (3) Pair(M,H) cheapest gap but active version blocked by the wall; passive only.
- **Single best next move = build the OFFLINE VALIDATOR for the EH-passthrough specialist** (zero hotkey cost; tests the
  exact two failure modes — Hard re-route (m13) + savings-gate DQ (m17)). PURSUE only if it clears both offline.
- **WON'T promise dethroning the king on Overall** — its edge is Easy/Medium baseline-pass consistency = agent-side, banned to steer.
- Correction logged: board scores Single-M off king Medium 1.281 (authoritative); the earlier per-run 0.909 (wzm1fb1sn) may
  be old-king's Medium misattributed — UNRESOLVED but immaterial (Medium isn't our lever).

## 2026-06-25 — m23 RESOLVED-gate PRE-BUILD AUDIT = NO-GO. Build not undertaken. HOLD m12.
Per the user's m23 spec (option b: RESOLVED-only break-fix + determinism pass) the mandatory pre-build
gate audit ran FIRST and returned **NO-GO** (decision rule: "if gate leakage is non-trivial, do not build").
Full report: reports/m23_gate_audit.md. Evidence (faithful offline replay of the platform connector-rewrite
loop using m12's ACTUAL code, over real comp-108 m12 trajectories; harnesses /tmp/m23_gate_replay.py +
/tmp/m23_gate_variants.py):
1. **The RESOLVED gate cannot causally separate settled-Easy from flip turns.** At an early harvest turn a
   flip task is SIGNAL-IDENTICAL to a settled Easy task (agent hasn't run the failing test yet → no errors,
   recent window clean, shallow, no escalation). The flip leak, fires-per-gate on sympy-24066 (a real Flip):
   lenient 217, strict-no-error 104, resolution-signature(had≥2 err then clean) **still 70**. Only an
   ultra-strict G4 (depth<45 ∧ ≥3 prior errors ∧ last-10-clean) hit 0 — but by OVERFITTING thresholds to 3
   available flips AND it then fires 0 on django-14122 (a real Easy break-fix target → loses the upside).
2. **Zero-sum under the mandated ≤m12 (chars AND tokens) ceiling:** any kept break-fix span must be funded by
   removing exploration content → the same break-fix-vs-flip antagonism that killed m22. And save_state +
   connector-feedback means a single misclassified early harvest turn on a to-become-rich task propagates into
   rich → Hard crater (un-undoable; "decouple state" option A is unavailable to us — output IS the next context).
3. **The "determinism pass" half is a confirmed NO-OP:** m12's compression path has no randomness/time
   dependence (only utc_now in save_state metadata, never the output) → m12 is already deterministic. The −4
   break-run variance is agent-side (qwen3-coder sampling), already ruled outside our compliant reach.
- **Audit gap (honest):** the named django-13925/14017 (Medium-flip craters) + sympy-16792/django-15037
  (Hard-crater Pass) have NO local trajectories; verdict rests on 3 flips (sympy-14976/18698/24066), but
  sympy-24066 leaks decisively under every non-overfit gate and the leak is CAUSAL → more data ~certainly
  confirms. A targeted eval to capture them is possible but not recommended (spends eval to harden a clear call).
- **DECISION: HOLD m12** (investigation fallback (c)). m23 NOT built; upload_miner_m23.py NOT created; m12 LIVE
  file untouched/git-clean. This is the 4th content-change attempt blocked (m18/m21/m22 craters + this audit) —
  m12 (0.738 overall, Hard 0.919 field-best, 4.8% Single-Hard) is our compliant ceiling. Smarter-selector +
  RESOLVED-gated break-fix BOTH now closed. Growth, if any, = favorable re-eval window or a portfolio specialist
  (still blocked on the same agent-stochasticity wall).

## 2026-06-25 — INVESTIGATION wzm1fb1sn VERDICT: king's edge = CONSISTENCY (replicable), NOT content quality; smarter-selector PERMANENTLY DROPPED
Workflow wzm1fb1sn (4 agents, independent per-run re-derivation) reconciled every load-bearing number. Three durable flags:
1. **King Medium 1.281 = LEADERBOARD AGGREGATION DRIFT, NOT per-run reproducible.** Real per-run value = **0.909**.
   DO NOT target 1.281 as a number — target the *mechanism* (consistency), not the figure.
2. **The king does NOT preserve flips.** It is WORSE than m12 on flips (Medium flip contrib +0.188 vs m12 +0.503;
   on django-14017, the one true Medium flip, king scores 0/5 vs m12 3/5). Its ENTIRE Medium edge is on baseline-PASS
   tasks (+0.721 vs m12 +0.333, 2.2×), bought purely by **eliminating −4 break-runs → run-to-run consistency**
   (all-5-consistent-pass: m12 14, king 18, m22 17 — king = consistency champ). ~60% of its Medium-over-m12 gain is
   just 2 tasks (django-13810, sympy-23262) converted from −4-bleeders to all-5-clean.
3. **"Generic break-fix selector + Hard-safe" is PROVEN MUTUALLY EXCLUSIVE (m18/m21/m22 = 3 independent proofs).**
   Break-fix needs the *destination* (error/traceback/test/diff/sig/path); flip-enable needs the *path* (file-body
   reads, reasoning chain, exploration breadth) — antagonistic content classes in one zero-sum budget. Token-invariant
   clincher: m22 lost flips at tokens ≤ m12 (django-13925 same tokens 3→0; sympy-18698 fewer tokens, still lost). And
   Hard-crater is unavoidable for ANY harvest content change: save_state persists the COMPRESSED output → re-fed as
   rich's input next turn → m22 left rich byte-identical yet Hard still cratered. **PERMANENTLY DROP the
   "smarter flip-preserving selector" direction (<15% odds; fighting a zero-sum fight lost 3×).**

**DECISION (ranked, awaiting user greenlight before any build):**
- **PRIMARY = option (b): RESOLVED-only break-fix, consistency-gated.** Apply m22's extractive break-fix selection
  ONLY to tasks the router classifies as settled/resolved (`recent_errors==0`), leaving still-failing/exploring tasks
  on the BYTE-IDENTICAL m12 trajectory — so the flip/Hard exploration path is structurally never touched. Plus a
  determinism pass on the harvest path to kill −4 break-runs on baseline-PASS tasks (the king's actual lever).
  Odds ~45–55% of a SMALL net-positive. RISK = gate leakage (if "resolved" misclassifies a flip task → re-crater Hard).
- **REJECTED = option (a) "smarter flip-preserving selector"** (<15%; zero-sum, lost 3×; promises engineering we can't do).
- **FALLBACK = option (c) accept the m12 ceiling.** m12 (0.738 overall) trails the king (0.755) ONLY on consistency,
  not capability — a respectable safe position. If the RESOLVED-only gate can't be built cleanly under compliance,
  STOP — a 4th Hard-cratering content change would be malpractice.
**GATE before ANY submit (same gate that correctly killed m22):** Easy↑ AND Medium flat-or-up AND Hard flat-or-up
AND flip-count ≥ m12's 29; else reject. m12 stays LIVE/untouched; any candidate → 2nd hotkey, same OpenRouter acct.
Full synthesis: workflow wzm1fb1sn output (verification script /tmp/strat_analysis.py, read-only).

## 2026-06-25 — m17 PASSED Phase-A safety check -> CLEARED to upload as zero-downside probe (2nd hotkey)
m17 = miner/cot_compression/upload_miner_m17.py (sha ac9519f0). Phase-A (local, adversarial) ALL PASS:
compliance PASS; AST 57/58 functions BYTE-IDENTICAL to m12, only compress_structurally differs + new helper
_select_then_cap; compress_gently/extractive_compress/handle_assemble/state fns byte-identical; RICH-path output
BYTE-IDENTICAL to m12 on a deep trajectory (Hard 0.919 provably safe); deterministic; harvest bytes <= m12 (+0.6%
worst, under +1%); DEMONSTRATED m17 keeps a buried FAILED/AssertionError line m12's blind truncation DROPS. m12 live
file git-clean/untouched. CONCLUSION: m17 is zero-downside (cannot dent Hard or worsen ratio by construction) and
addresses ~1-2 of the 10 break tasks (truncation cases; NOT the whole-drop cases). Cleared to upload to a 2nd hotkey
(same OpenRouter account as m12). HONEST: it will NOT beat the king; it is a probe to see if the retention lever moves
the BOARD. Confirming any real break-fix still requires a paired A/B N>=15/task on NET 50-task mean (effect < single-
read noise). Upload cmd: python3 miner/upload_miner.py --platform_url <url> --wallet_name <w> --hotkey_name <NEW2nd>
--solution_file miner/cot_compression/upload_miner_m17.py  (USER runs; m12 stays LIVE).


## 2026-06-24 — PLAN to beat the king (reports/plan_beat_the_king.md, 14-agent verified)
KEY CONCLUSION (honest): caching/stability ALONE does NOT beat the king. The break-mechanism crux is
RESOLVED = H1/CONTENT-dominant, NOT H2/churn: the king runs 86-88% cache (max-stable prefix) and STILL
breaks 6-7/250, ALL at high cache -> a stable prefix does not eliminate breaks. Freeze-on-emit fixes churn
only, worth ~4-5 break-fixes (17->~12-14), NOT the +0.20 once hoped. Reaching #1 (win Overall 57%, needs
<=6 breaks) requires CONTENT-RETENTION (keep more/better of the code the agent patches against) = Phase 2,
the real lever. PLAN = two phases:
- PHASE 1 (do now): AOW-lite = freeze-on-emit, HARVEST-ONLY, append-only window; keep m12 content byte-for-byte
  (compress_gently/passthrough UNTOUCHED); everTouchedRich gate (no freeze once rich fires) + ratio watchdog.
  Hard-SAFE by construction. Value = CACHE lever (high confidence): cache 55->~75%, weighted-ratio 2.96->~3.5
  -> takes Pair-MH from king -> share 4.8%->~14% (3x), upside ~19%. Does NOT make us #1.
- PHASE 2 (after Phase 1 proves cache-lift+Hard-hold): content-RETENTION research (m7-style deeper PASS-SAFE
  retention) to kill the residual ~8-11 H1 Medium breaks. This is the only path to #1.
RED-TEAM amendments (2 landed): (#4 Hard) "rich is byte-identical->Hard safe" is FALSE (Hard runs pass through
harvest first; frozen prefix feeds INTO rich) -> everTouchedRich gate + KILL on any SINGLE new Hard break.
(#5 validate) effect (+0.06-0.11) < single-read noise (Overall sd 0.098) -> do NOT gate on score; PRIMARY GATE =
the directly-observable CACHE mechanism (fresh-input 429k->target<250k, cache->~80%) visible in ONE read; use
PAIRED A/B (candidate + fresh m12 same window, per-task diffs) for break/score, N>=3. Platform-scored only,
2nd hotkey, m12 LIVE.


- **m12.1b (=m13) SUBMITTED + REJECTED by the platform (2026-06-23): 0.571 vs m12 0.768.** Submitted to a
  fresh hotkey (m12 untouched). Hard COLLAPSED 0.919→0.434, Medium 0.953→0.718; only Easy rose 0.412→0.561.
  The aggressiveness-cap + gentler-routing design is FALSIFIED — m12's aggressive harvest is net-positive on
  H+M; softening it traded away our edge. KEEP m12 LIVE/BEST. **Run-variance-from-over-compression thesis is
  dead** (the 10-20x "outliers" were a symptom of failing short runs, not the cause). **Local eval is
  unreliable for H+M** (showed fragile +3; Hard actually collapsed) → validate H+M candidates ON THE PLATFORM.
  ONE extractable win: never-inflate/gentleness lifts EASY. NEXT: m12 + never-inflate ONLY (isolate the Easy
  lift, don't touch the H+M harvest), platform-validate. Full: `reports/m13_platform_result.md`. Below entry
  (the local NO-SUBMIT call) was overturned by the platform — submitting was the right move.
- **m12.1b_run_stability — local eval said NO-SUBMIT (2026-06-23), platform OVERTURNED it (see above).**
  (`reports/m121b_eval_results.md`, run 2026-06-23_050906_H1M_pbatch, 100/100 ok): m12_1b 34/50 vs m12 33/50
  = a TIE, composition shifting Hard↑ Easy↓. WINS: HardFragile 6→9 (+3, incl django-14493 **1/5→5/5** — the
  textbook partial-flip→clean-flip the candidate targeted); Medium preserved (17→18, tok/call +1.0%,
  (in+out)/call −18%); never-inflate + cap structurally hold (offline-proven). BUT does NOT clear the gate:
  **Easy regressed 10/10→7/10** (the spec's explicit reject trigger) and 2 fragile tasks slipped −1 each.
  The Easy drop is most likely AGENT NOISE (m12_1b is mechanism-inert on small Easy contexts; compression
  matched m12 within 3%) but n=10 can't prove it. Verdict: don't replace the live #2 on an ambiguous wash.
  m12_1b is KEPT as the lead candidate; the never-inflate + aggressiveness-cap + determinism design is sound.
  NEXT: targeted RUNS=10 re-eval (2 Easy + 4 fragile only) to separate signal from noise before any submit.
  The build/verify/eval pipeline (parallel driver + verify_m121b.py + analyze_runvariance.py) is validated.

- **m7 / v11.1 is our confirmed best (1.279) and the recipe to protect/replicate.** Everything built on top
  (v15→v18→v22→v24) added persistent-failure flip-routing that, on the platform, *leaked Medium* (v15 → 1.183).
- **Compression is at its ceiling.** Six levers tried (v14 richer, v17 harder, v19 loop-coach, v20 snapshot,
  v21 reasoning-trim, v23 gentler-harvest) — all no-gain or harmful. m7's 8k harvest is the sweet spot.
- **The king's edge (decisiveness + Easy 1.43) is not reachable via compression** — it's agent/model behavior.
  Easy ceiling for us is ~1.13 across gentle/aggressive/adaptive. Stop chasing Easy/overall #1.
- **Shipped v22→m9, v18→m10, v24→m11 (2026-06-17)** as flip "king-shots" on fresh hotkeys (m7 untouched/floor).
  Expectation revised DOWN after v15's platform result: likely ≤ m7 (Medium leak outweighs unmeasurable Hard gain).
- **v26 (depth-gated threshold) validated for a future cycle**, not shipped (m12 unregistered).
- **Reward model is layer-based (7 elements), not top-3.** Winning a single category (~4.8%) is the only realistic
  path for us; overall/pairs need broad strength we lack.
- **Ops/tracking lives here (SOMA-ops). Miner code is NOT edited or submitted from this repo.**
- **PIVOT (2026-06-21): post-competition RESEARCH mode.** Comp 107 completed; we do NOT submit.
  Goal = design the strongest next-round miner offline, evidence-backed. Next direction is fixed:
  **m7-style architecture + deeper PASS-SAFE compression**, NOT more routing. Flip-mode rescue /
  persistent-failure routing / release-flip-on-pass are **permanently dropped** (postmortem: net-negative —
  no pass gain, more broken baselines + negative tasks). Hypotheses H1–H4 in experiments/manifests/.
- **Label audit RESOLVED (2026-06-21):** m9=5CFqU2Ss=v22, m10=5GL4Kxda=v18 (registry, corroborated by 4
  git-tracked files; chat label rejected per "chat ≠ source of truth"). Scores are hotkey-anchored, so
  analysis is label-independent. Full evidence: reports/label_mapping_audit.md.
- **Dev/ops env runs in WSL Ubuntu-22.04** (scope: "miner dev + ops"). One-shot idempotent installer
  `scripts/setup_wsl_env.sh` → venv at `~/.venvs/soma` (Linux fs, fast IO); repo stays at `/mnt/e/soma`.
  Pinned to the repo's known-good set; pin `async-substrate-interface==1.5.15` to avoid the cyscale↔scalecodec
  namespace clash that breaks `import bittensor`. Full guide: `docs/wsl-env.md`. NOT installed (upload-only):
  `soma_shared` (private DendriteHQ repo — sandbox blocks external git installs, user runs it) + a netuid-114 wallet.
- **TARGET = the OVERALL king t1 (5EkiFXSR, 1.460), via PASS-SAFE COMPRESSION DEPTH (2026-06-22).** The
  board has 7 reward elements; the winning recipe that fits us is the DEPTH strategy (t1/t2/t3 run mean
  ratio ~4.8–5.0× at pass 37–39). **We already match the king on the hard parts** — pass 38 (vs t1's 39),
  broke 1 (=), neg 3 (better) — and lose almost purely on ratio (2.99× vs 4.83×). The ratio model explains
  +0.231/task of the +0.157/task gap (residual −0.074), so **matching the king's depth ≈ closes the whole gap.**
  → Next-round plan: push m7's harvest from ~3× toward ~4.8–5× while HOLDING passes + protections. Per
  category: Medium ~5× (safest + closest element), Hard pass/pass ~5× (flips→rich, fragile guard), Easy ~4×
  (flakiest — t10 proves crude over-push crashes pass-rate: 5.24× but only 33 passes). t4's Hard 1.751 comes
  from pass-rate/decisiveness (agent behavior, only 3.06×) — not our reachable lever; depth is.
- **King-depth SWEEP is the next experiment (chosen by user 2026-06-22), AFTER the foundation batch.** Added
  `king` (TARGET 3600) + `ultra` (2400) profiles to h1m_miner.py (protections untouched; only stale-content
  truncation tightens). Sweep m7 → deep → king → ultra via run_batch_eval.sh (`PROFILES=...`) on a focused set
  to find the **pass-safe depth ceiling** per category = the next-comp baseline. Foundation batch (m7 vs
  h1m@deep, 15 tasks) runs first to validate eval-at-scale + the m7 baseline + the fragile guard.
- **STRATEGY UPDATE (2026-06-22): the top of comp 107 FAILED REVIEW — target + thesis shift.** t1–t5 + t7
  (incl the overall, Medium, AND Hard kings) are all "failed review" (excluded from reward); only t6/t8/t9/t10
  + our miners survive. Consequences: (1) **m7 is now review-PASSING top-tier** — #2 overall, Medium ≈TIE
  with t9 (1.421 vs 1.423), #2 (M,H). (2) **The king target drops from t1 (1.460, 4.83× deep) to t6 (1.335,
  2.88× — NOT a deep compressor; wins via Hard 1.525 + balance).** So **chasing extreme 4.8× depth is no
  longer required** to be king-competitive — de-prioritize the king/ultra depth chase; favor m7-class +
  modest-safe-depth + Hard. (3) **OPEN RISK — why did they fail review? Ratio is NOT the cause** (t10 survived
  at 5.24×, t5 failed at 2.40×) → per-miner manual/compliance review, cause unknown. **INVESTIGATE the review
  criteria (Discord / platform notes) BEFORE shipping aggressive-compression candidates** — H1M/H3 deep could
  carry an unquantified DQ risk. The H3 cache-stable work stays valuable (review-safe, modest depth, Medium
  edge), but reframed: beat t6's 1.335 + win Medium, not catch a (now-DQ'd) 4.8× king. Confirm element leaders
  vs the FULL comp-107 board (tracked recompute excludes untracked ranks 11+).
- **PROMPTING POLICY locked for next comp (2026-06-22, official `miner/README_prompting.md` + Discord).** The
  top failed review for **SWE hints injection (t1,t2,t3,t7)** + **non-compliant prompt modifications /
  behavior-steering (t4,t5)** — PROMPT-SIDE CHEATING + problem-targeting force-stops, **NOT compression depth.**
  Our compression is the intended focus; m7 passed = legitimate. **Next round ONLY two prompt edits allowed:**
  (1) compression markers (metadata only, exact published strings, preserve meaning/order/policy/output),
  (2) loop-detection guards (objective loops only, exact reason strings, no behavior change, no token-shortcut
  forcing). **Force-stop is BANNED.** Allowed strings: markers `[[CMP]]` `[[/CMP]]` `Compressed text
  starts/ends here` `[[BLOCK X]]` `[[/BLOCK X]]` `Same response as in [[BLOCK X]].`; loop reasons
  `loop_detected: repeated assistant response` / `loop_detected: repeated tool call signature`. New strings →
  discuss publicly first. **OUR m7/H1M/H3 are NON-COMPLIANT on the prompt side** (coach = force-stop "STOP NOW"
  + loop nudge "change your approach" + custom `[SOMA …]` markers). **Next-round baseline = m7 compression,
  COACH-FREE / force-stop-free, published `[[CMP]]` markers, loop-detection reduced to the 2 allowed reason
  strings; keep harvest/rich/H3 cache-stable compression.** Stripping the coach likely costs little (v12's
  forced-stop already FAILED to help). Full gap analysis: reports/prompting_policy_and_compliance.md.

## 2026-07-08 — comp-110 DOCTRINE pinned (do not relitigate; full text = CURRENT.md 📌 PINNED block)
Screener = Gate A (≥50% tasks majority-RESOLVED) × Gate B (≥20% weighted savings vs FIXED baseline, cached×0.1, output×3), one upload per hotkey. Crown = comp-108 playbook: (1) qualify, (2) survive review/compliance, (3) never break (−4), (4) score all 3 task types (explore passthrough=0), (5) generalize to hidden tasks, (6) trajectory efficiency. Retired approaches (platform-refuted, do NOT revisit): fresh-read compression (E−3.98), tiny-budget interior skeletons ≤250 (M−4.00), system-prompt trimming (non-compliant), CoT-only compression (0.9% of stream), floors ≥2k (<5% savings).
