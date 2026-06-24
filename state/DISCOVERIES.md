# DISCOVERIES (durable findings)

- **★★ COMPREHENSIVE 50×5 ANALYSIS (2026-06-24): m12 is STATISTICALLY AT PARITY with the #1 king; the 0.012 gap is
  window/sampling NOISE, not a fixable deficit.** Across all 50 tasks × 5 runs, top-3 compared: (1) total fail-rate
  EQUAL — m12 81/225, king 82, 5DtEz 84, similar premature/mid/wander mixes. (2) baseline-PASS exposure IDENTICAL
  (m12 29/45 = king 29/45). (3) m12's −4 break gap (16 vs king 6) is allocation, not skill — and on the 6 tasks
  m12 breaks but king passes, **the king compresses HEAVIER on 4/6** (definitively kills "lighten to fix breaks").
  (4) break overlap 30% asymmetric but same compression/steps/exposure → cross-window sampling luck. Combined with
  the 2-task trajectory forensics (solver-stochastic premature/wander WITH context present), the verdict is final:
  **NO compression lever captures the −4 gap (depth/m17/m18/lighten ALL refuted) because the gap isn't
  compression-driven — it's the qwen3-coder agent's run/window stochasticity.** We are effectively TIED with the
  king, separated by noise; a calmer re-eval window could flip m12 to #1 with ZERO code change (and the king's #1
  is partly luck). HOLD m12 — it's at the field ceiling on every controllable factor. Reports:
  comprehensive_runvariance_50x5.md + m12_pass_fail_forensics.md.

- **★★ ROOT CAUSE of m12 run-variance = SOLVER STOCHASTICITY, not compression (2026-06-24 trajectory forensics).**
  Same-window pass-vs-fail trajectory comparison (m17 A/B run 060037, local toolMetas) on the two broken pass-pass
  tasks with local pairs: **django-13810 FAIL = premature patch** (edits at step 2 after 1 read, 24 tools) vs PASS
  (inspects to step 5 + fetches canonical source, 36 tools); **django-12039 FAIL = WANDER** (56-58 tools, ~960-986k
  tokens, 9 reads in first 10 steps) vs PASS (38-43 tools, 539-646k). **OPPOSITE archetypes** (G/J vs K), and in
  BOTH the fail run had adequate-or-MORE context (12039 fails read MORE) — so NO missing-context (archetypes A-E
  absent). The divergence is the agent's ACTION SAMPLING at the first decision point, which compression doesn't
  control. → run-variance is irreducible qwen3-coder stochasticity; a compliant compressor CANNOT fix it (can't
  steer, can't add attempts, context isn't the bottleneck). This CLOSES THE LOOP on every failed lever (depth/m17/
  m18/5DtEz-relocation all targeted compression while the cause is the solver) and explains the king's 6-vs-16
  break edge as window/sampling luck, not a preservation rule. Forensic report: reports/m12_pass_fail_forensics.md.
  CANNOT analyze king/5DtEz trajectories (no local runs; platform scrape = summary only). VERDICT: reject any
  compression-preservation miner change; HOLD m12; the 17-broken-task headroom is real but NOT ours to capture.

- **★ 5DtEz84j (E+H, M-low) ANALYSIS: run-variance is RELOCATED not removed; the king's edge is SAME-RATIO
  RELIABILITY; portfolio is the only structurally-new lever (2026-06-24, analysis-only).** Fresh per-run scrapes,
  all scored. Key numbers (45 tasks×5): **−4-runs: king 6, m12 16, 5DtEz 11 — at the SAME ~1.75-1.84× ratio + same
  ~50 steps.** So the king (0.780, the only profile beating m12) wins by BREAKING LESS at equal compression, NOT
  by lightness/depth. 5DtEz (1.84× ratio, MORE than m12) gets Easy by being reliable on the tasks m12 breaks
  (django-11740/14122: m12 2×−4, 5DtEz 0×−4) but BREAKS a different set (django-13033 4×−4 where m12 gets 4/5) →
  Medium 0.50. So changing the scheme RELOCATES breaks across categories, net 5DtEz total 0.714 < m12 0.768.
  CONCLUSIONS: (1) Easy IS reachable (5DtEz proves) but NOT via lightness (it compresses more) and copying its
  tradeoff is net-WORSE for us (M0.95 worth more than the Easy gained). (2) m19 persistent-small NOT justified —
  5DtEz isn't doing it, and break-relocation predicts net ≈/< m12. (3) The winning lever (king) = same-ratio
  fewer-breaks = what m17 tried + failed; may be agent/window noise (unfixable by us). (4) **PORTFOLIO** (keep m12
  as M/H specialist + a 2nd-hotkey E-specialist for Easy/(E,H) elements) sidesteps the single-miner bind and the
  element math supports it (~14%→~25%+ share) — BUT blocked: we can't yet BUILD a working Easy specialist (5
  attempts failed; rivals' schemes opaque). DATA CAUTION: 5DAh per-run scrape is STALE/inconsistent with its
  scored leaderboard (scrape 0.878/8.6%-savings can't yield leaderboard H=−3.6/total 0.051) — trust leaderboard
  category truth, not its per-run rows. Full: reports/5DtEz84j_tradeoff_analysis.md. HOLD m12; portfolio = research track.

- **★ SCORING FORMULA (precise, from DendriteHQ/SOMA scoring.py, 2026-06-24) + recon: NO incoming change favors
  us.** Per-task raw: break −4 / both-fail ≈0 / pass-pass ≈+1 / flip ≈+4, plus ratio bonus 0.5·clamp(ln(ratio),
  −2,+2). **GLOBAL SAVINGS MULTIPLIER (key):** `applied = −4 + (raw+4)·mult`, mult = smoothstep on
  savings_ratio=(1−compressed/baseline): **mult=1 at ≥20% savings, 0.5 at 0%, 0 at ≤−20% inflation (→ every task
  floored to −4).** Implications: (1) near-passthrough/ultralight (<20% savings) is CRUSHED by the multiplier —
  m18 was doomed by this independent of perturbation; light only works if ≥20% savings (~1.25×+; king/5DAh sit at
  ~29%/1.41×, NOT passthrough). (2) **m12 (43% savings, all categories positive) is multiplier/penalty/gate-ROBUST
  with margin**; high-Easy rivals carry collapse exposure (5DAh −3.6 Hard = many −4 floors). RECON of in-flux
  layer: PR #157 `fix/scoring-penalty` MERGED today 08:55 = penalty CONSISTENCY fix (raw_total = mean-of-runs not
  mean-of-category-means), NOT a reweighting. The one game-changer branch `validator/llm-semantic-scoring` is
  DORMANT (last commit 2026-04-27). No merged/imminent change favors M+H or Easy. HOLD m12; watch only if
  llm-semantic-scoring revives. Full: reports/scoring_layer_recon_20260624.md.

- **★★ m18 (size-gated adaptive-light) REJECTED — the Easy↔Hard tension is STRUCTURAL (2026-06-24).** Stage-1 live
  gate (m12 vs m18, 5 tasks ×3, same window): m18 went ultralight on the shallow EARLY turns of the HARD controls
  (indistinguishable from easy turns) and **broke them** — django-13158 m12 3/3 → m18 0/3 (m18 took HALF the
  steps, agent off-track); sympy-18698 1/3→0/3. The thesis (recover easy-breaks) was UNTESTABLE: m12 broke none
  of the 3 small targets locally this window (run-variance is window-dependent — django-14122 breaks on platform,
  ran 3/3 locally) → nothing to recover, m18 just cost +21–77% tokens on clean tasks. **Fundamental flaw (kills
  the whole size-gated approach, not just thresholds):** a hard task starts shallow, so adaptive-light perturbs
  its early trajectory before it can be recognized as hard; easy vs early-hard are not separable by any legal
  structural signal. So you must pick ONE: light (easy wins, hard dies — the king) OR aggressive (hard wins, easy
  breaks — m12). **A single compliant miner cannot win both Easy AND Hard.** m12 chose Hard+Medium (the bigger
  moat) = defensible local optimum. FOUR levers now dead, same failure (agent destabilizes under perturbation):
  depth (EXP-1b), content-selection (m17), uniform-light (king collapse), adaptive-light (m18). Easy is NOT
  reachable without sacrificing the Hard moat. HOLD m12. Real remaining lever = upstream scoring layer (not us).
  Report: reports/m18_stage1_verdict.md. (Note: miner runtime mode isn't persisted to disk — infer from token/
  step deltas; grepping solve dirs for mode words is contaminated by the baked source file.)

- **★★ 5DAh2rUM "NEW KING" COLLAPSED 0.887→0.051 ON FINALIZATION (2026-06-24) — the reliability thesis below was
  built on a mirage.** It showed 0.887 #1 while EVALUATING (Easy/Medium only); when Hard finished it scored
  **H=−3.600** (its LIGHT 1.41× compression broke nearly every Hard run) → total 0.051. LESSONS: (1) NEVER trust
  an evaluating score (discipline vindicated). (2) m12's aggressive harvest → **Hard 0.919 is a massive durable
  moat** — the only light competitor imploded on Hard (−3.6). (3) **"go lighter for reliability" is DANGEROUS,
  not promising** — SHELVE the reliability/lightness A/B (light king died on Hard; EXP-1b lighter broke more;
  both point the same way now). m12's own run-variance (breaking 2-3 of 5 on some tasks) is REAL but looks
  irreducible/agent-noise + going lighter to fix it risks the Hard moat → HOLD m12. We are #2 (0.768), 0.012 from
  the (old) king 0.780, who beats us ONLY on Easy (agent-bound). The reliability analysis below is RETAINED for
  history but its action (lighten m12) is REJECTED.
- **[SUPERSEDED by the collapse above] NEW KING 5DAh2rUM (0.887, EVALUATING) WINS VIA RUN-RELIABILITY, NOT COMPRESSION (2026-06-24).** Same-window
  scrape of king vs m12 on the 50 comp-108 tasks: the king compresses LIGHTER (avg 1.41× vs our 1.75×, 12/45
  tasks inflate <1×), passes FEWER (32 vs 33), flips FEWER (6 vs 7) — yet scores higher (0.887 vs 0.768). Why:
  leaderboard total ≈ mean(E,M,H); m12 is bimodal (M0.953/H0.919 elite, **E0.412 cratered**), king balanced
  (0.85/0.98/0.78). The Easy gap is the whole delta — and m12's low Easy is **RUN-VARIANCE breaking pass-pass
  tasks**, NOT decisiveness: per-run detail shows m12 breaking 2–3 of its 5 runs (each −4) on tasks where the
  king passes 5/5 (e.g. django-14122 m12 [+1.18,−4,+0.79,+0.96,−4] vs king all-pass). So: **the lever is
  RELIABILITY (run-to-run consistency), not ratio/depth/Easy-decisiveness.** REVISES the "Easy is dead/agent-
  bound" story — m12 is breaking easy tasks under its own aggressive compression. CONFOUND: cross-window (king
  evaluating NOW vs m12 scored earlier) → partly provider-window luck; BUT m12's within-task within-window
  variance (3 pass + 2 break on the same task same window) proves it's at least partly intrinsic to m12's
  compression. UNRESOLVED vs EXP-1b (same-window, 6 Medium/Hard tasks) which found lighter broke MORE → the
  depth↔reliability relation is task-dependent; needs a SAME-window m12-vs-reliability-variant A/B on a BROAD
  (easy-inclusive) set, RUNS=5, scored on per-run break-rate. Full: reports/new_king_5DAh2rUM_analysis.md.
  ⚠️ King is EVALUATING — re-scrape when `scored`; number may shift. m12 Hard moat (0.919 vs 0.776) intact.

- **★ DEPTH IS DEAD (EXP-1b SETTLES IT, 2026-06-24) — same-window A/B, m12 8k vs deeper 4k vs lighter 16k, 54/54.**
  Breaks rise MONOTONICALLY away from m12 (broke baseline on: m12=1 task, deeper=2, lighter=3) → m12 is the
  reliability optimum. Deeper uses MORE total tokens in every category (agent wanders more steps → the per-message
  ratio gain is erased at task level) AND has the LOWEST cache-hit (0.80–0.84) + most uncached input. Lighter
  ADDS breaks → m12 is NOT over-compressing. Flip (sympy-24066) = 0/3 at all depths → capability-bound. Net:
  changing TARGET_TOKENS either way is neutral-to-negative. **Run-variance is AGENT/PROVIDER noise, not our
  compression depth** (lighter didn't cut it; it added breaks) → the comp108_headroom "17.6 pts" was an upper
  bound, mostly irreducible. CLOSES the depth-frontier line. HOLD m12. Report: reports/exp1b_depth_frontier_verdict.md.
- **★ NEW: aggressive re-compression BREAKS PROMPT CACHING (EXP-1b, 2026-06-24).** Deeper (4k) had the lowest
  cache-hit + highest billed (uncached) input — rewriting context harder each turn changes the cached prefix →
  cache misses. The weighted-savings gate counts input×1 / cached×⅓ / output×3, so cache-loss DIRECTLY worsens
  the gate, on top of the agent-wander token blow-up. Implication: any future compression change must be
  CACHE-STABLE (append-mostly), not heavy turn-over-turn rewrite, or it loses on the gate even if the ratio looks good.
- **★ CoT-COMPRESSION LITERATURE SCAN (2026-06-24, user-prompted) — no famous method is plug-in usable.**
  LLMLingua/LLMLingua-2/Selective Context need an LM scorer = banned (LLM call in miner). TokenSkip/LightThinker/
  C3oT need FINE-TUNING the solver = inapplicable (we don't own qwen3-coder). ACON (closest paper, long-horizon
  agent context compression) uses a compressor LLM (banned) BUT its findings transfer: moderate compression beats
  aggressive (= our EXP-1b), and it lists what to PRESERVE (action→outcome pairs, error/state). Lost-in-the-Middle
  + DocString-compression give deterministic principles (keep head+tail+code, trim prose). Only compliant new
  idea: deterministic CONTENT-SELECTIVITY (protect error/test/diff/state, compress prose, cache-stable) — targets
  breaks w/o depth. Hypothesis only. Full: reports/cot_compression_literature.md.
- **★ EVAL SPEED — SAFE CONCURRENCY ON THIS MAC IS MAXJOBS=3 (settled 2026-06-24 after 3 data points).** The
  binding limit is **patch-eval RAM spikes**, NOT steady-state RAM, NOT CPU, NOT OpenRouter. Each solve's
  patch-eval phase builds a SWE-bench eval image + runs the full test suite = transient multi-GB. Evidence:
  **MAXJOBS=8** → load 15 on 10 cores, CPU-starved, stalled (38min/0-done); **MAXJOBS=4** → Docker Desktop OOM-
  CRASHED ~10min in (daemon socket gone, MemTotal=0; solves then completed in 1 SEC each = bogus instant-fails;
  had to force-kill + relaunch Docker Desktop). **MAXJOBS=3** → ran EXP-1b 4h, 54/54, clean (PROVEN). So:
  steady-state ~0.8GB/solve is misleading — the patch-eval spike is what OOMs. **Use MAXJOBS=3 here** (~6h for 60
  solves). My earlier "MAXJOBS=8 free 2×" was WRONG twice over (CPU AND RAM). RunPod with more cores+RAM would
  genuinely help now; OpenRouter per-account rate is the ceiling beyond that. Rule: don't exceed MAXJOBS=3 on a
  16GB/12GB-Docker Mac; watch for `docker info`→MemTotal=0 (= OOM crash) and 1-sec "ok" solves (= bogus).

- **★ BIG UNEXPLORED ALGORITHMIC HEADROOM on comp-108 — m12 is UNDER-compressing AND breaking (2026-06-23, user-prompted).**
  ⚠️ SUPERSEDED 2026-06-24 by EXP-1b: the "ratio headroom" was illusory (depth → agent wander) and the
  "run-variance headroom" was mostly agent noise (lighter added breaks). Kept for history; HOLD m12 is the conclusion.
  Why 108 scores are all <1 (vs 107 all >1): decomposition of m12's 108 tasks shows points left on the table:
  (1) **Run-variance on pass-pass = ~17.6 pts** (29 pass-pass tasks score mean 0.633 vs clean-baseline
  1.24; 17/29 break on >=1 of 5 runs). BIGGEST prize. (2) **Low compression ratio = ~+0.27/task x ~38 tasks**
  (m12 avg 1.75x vs m7@107 2.99x; 31/45 under 2.0x, 19/45 under 1.5x) — cross-category bonus via 0.5*ln(ratio).
  (3) **Weak flips: 7 won / 2 partial / 7 fail-fail** (fail-fails have LOWER ratio 1.38x = not over-compressed
  = likely capability-bound; the 2 partials are convertible). Recovering pass-pass baseline + ratio -> mean
  ~0.74 toward ~1.0+ -> beats king, lifts M/H/E (cross-category, NOT the agent-bound Easy trap). CAVEATS:
  some run-variance is agent/provider noise (17.6 is upper bound); deeper compression may CAUSE breaks
  (depth-vs-breaks FRONTIER). NEVER TESTED ON 108 (prior work was Easy-narrow + on the WRONG 107 task list +
  provider-confounded). RESEARCH (same-window A/B on 108, the only trustworthy eval): (A) is pass-pass
  run-variance our-compression-fixable? (B) push ratio 1.75->~2.5x SAFELY (frontier); (C) convert the 2
  partial flips. CORRECTS earlier "m12 is at our ceiling" defeatism. Plan: reports/comp108_headroom.md.

- **★ PLATFORM SCORES ARE TEMPORALLY NOISY (OpenRouter provider window) — cross-window A/B is UNRELIABLE (2026-06-23).**
  m15 (never-inflate, SAME 1e8a key as m12) scored 0.587 (E0.388/M0.886/H0.476) — H/M "collapse" vs m12 0.768.
  But the DIAGNOSTIC proves it's the PROVIDER WINDOW, not the code: on flip-candidate (Hard) tasks m15
  compresses IDENTICALLY to m12 (mean ratio 1.54x vs 1.48x; per-task near-identical) at the SAME step count
  (49.1 vs 50.5), yet the agent BREAKS MORE (django-13925 3/5->0/5, sympy-18698 3/5->0/4). Identical compression
  + identical steps + worse pass = weaker MODEL OUTPUT, i.e. m15 ran in a worse qwen3-coder window than
  m12-days-ago. ⇒ (a) never-inflate is CONFIRMED byte-identical on H/M (not harmful via code); m14/m15 low
  scores were the provider window, never a clean never-inflate verdict. (b) Provider variance swings Hard by
  ±0.3+, DWARFING code effects — so NO cross-window platform A/B is trustworthy; ONLY same-window controlled
  evals (the step-test) are. (c) Single platform scores (ours/rivals'/m12's 0.768) are partly luck-of-window.
  Implication: stop trying to read code changes off single platform submissions; rely on same-window local A/B
  on the re-pointed comp-108 tasks. m12 stays LIVE/BEST. Full: reports/m16_steptest_result.md.

- **★ EASY IS UNREACHABLE via our compliant compression lever — 4 candidates falsified it (2026-06-23).**
  Controlled same-window A/B m12 vs m16 (4 Easy-proxy comp-108 tasks, RUNS=3): m16's rescue FIRED, but m16 took
  MORE agent_steps (40.2 vs 34.7), NOT fewer — directly DISPROVING the "cleaner compression -> fewer steps ->
  better Easy" hypothesis. The king's Easy edge is agent DECISIVENESS (fewer steps), which we cannot buy
  (behavior steering BANNED) and cannot induce via compression. m16's only consistent effect was cache-stability
  (cache_hit 0.59 vs 0.36) but at +23% total tokens (worse ratio) and a new break; resolved 10/12 vs 8/12 is
  noise at n=12. Tested + failed: m13 (cap), m14/m15 (never-inflate), m16 (light-safe). CONCLUSION: stop chasing
  Easy via compression; m12 Easy ~0.41 is near our compliant ceiling. DEFEND the M+H moat (field #1: M 0.953,
  H 0.919). The king (0.780) beats m12 (0.768) ONLY on Easy decisiveness we can't match. Report:
  reports/m16_steptest_result.md.

- **★ The Easy gap is AGENT DECISIVENESS (step count), NOT compression — re-confirmed on comp-108 (2026-06-23).**
  King vs m12 on the 15 Easy-proxy tasks: tokens/step IDENTICAL (m12 17,222 vs king 17,457) → NOT cache;
  agent_steps m12 44.2 vs king 38.9 → m12's agent WANDERS more. All 6 m12-inflated Easy tasks = m12 takes more
  STEPS at similar tok/step (not cache-bust, not compression depth). So m12's Easy "inflation" (ratio<1) is the
  agent accumulating more tokens by taking more steps than the no-compression baseline. The king wins Easy by
  being more DECISIVE (fewer steps), exactly as found in comp-107 ("Easy unreachable via our compression
  lever"). CONSTRAINTS: we CANNOT add a decisiveness nudge (behavior steering BANNED); compression ratio/cache
  is NOT the lever. ONLY possible indirect lever: IF m12's erratic small-context compression CONFUSES the agent
  into wandering, a cleaner context (m16 rich) might cut steps — UNPROVEN, measurable only via agent_steps on
  the real comp-108 eval. ⇒ Stop chasing Easy via compression mechanics (m13/m14/m15/m16 token-levers all miss);
  defend the M+H compression+flip moat (where our lever actually works); test the step-count hypothesis cheaply
  before any more Easy work. Full: reports/king_vs_m12_easy.md.

- **★ COMP-108 TASKS ARE 100% DIFFERENT FROM COMP-107 — and our LOCAL EVAL was on the WRONG tasks (2026-06-23).**
  0/45 instance overlap (107=config/task_categories.csv; 108=un-masked scrape). So ALL 107 task-specific
  knowledge is MOOT for 108 (fragile tasks sympy-17139/django-11239/etc., break/flip lists, fragile guards —
  none are in 108). CRITICAL: run_batch_eval's TASKS list = 107 instances → local eval has NEVER tested on the
  108 platform tasks → THE root cause of every local-vs-platform divergence (not just "local is noisy"). FIX:
  re-point local eval at the 50 comp-108 instances (now un-masked via upstream 9301a74) before trusting any
  local result. Tasks rotate every competition — re-pull the set each round. Full reset:
  `reports/comp108_research_reset.md`. Real 108 race (scored only): king 5DFvymSeEw 0.780 (E0.812/M0.934/H0.596)
  vs m12 0.768 (E0.412/M0.953/H0.919) — we're #2, DOMINANT M+H, weak Easy; the Easy-only 1.0+ miners are "not
  qualified" (failed the ≥10% weighted-savings gate). Path to #1 = lift Easy WITHOUT tripping the savings gate
  (so never-inflate/pass-through is the wrong Easy lever — it risks "not qualified", which is where m15 sits).

- **Upstream (DendriteHQ/SOMA origin/main) competition-mechanics updates (checked 2026-06-23).**
  (1) **`100c884` WEIGHTED token-savings screener GATE is real + on main:** screening requires ≥10% WEIGHTED
  savings (`SWEBENCH_SCREENING_MIN_WEIGHTED_TOKEN_SAVING_RATIO=0.1`; weights input×1, cached×⅓, output×3) ON TOP
  OF the pass-ratio gate (0.5). ⇒ NEVER-INFLATE RISK: reverting marginal tasks to passthrough (ratio 1.0 = 0
  savings) can drop weighted savings below 10% and FAIL screening — so m15's screener_passed=False may be a
  GENUINE savings-gate fail, NOT (only) the frontend flag bug. Test: does m15 proceed to full 50 (passed) or
  stay task_count=5 (failed). (2) **`8c6f43b` full-task eligibility:** a miner is EXCLUDED from a category
  layer's pool unless eligible across that category's full task set — tightens the 7-element incentive. (3)
  **`9301a74` task names now shown in aggregate** (masking relaxed) → may unblock task_id→instance mapping.
  (4) `11f54f5`/`b430e3c` screener weights configurable + split token usage (input/cached/output) persisted.
  (5) `a95a06c` frontend screener-flag fix + validator weight-split normalize. UNMERGED branches in flight
  (scoring in flux — WATCH): penalty-fix, scoring-formula, validator/llm-semantic-scoring, weight-hot-fixes.

- **m14 confound cause is RE-OPENED — it is NOT the AtlasCloud block (2026-06-23, corrected by user).**
  AtlasCloud has been blocked since ~m2/m3 and the provider config is CONSTANT across ALL versions (m12, m13,
  m14, m15) — so the block does NOT differentiate m14 from the others and can't explain m14's collapse. (True:
  no provider config in SOMA code → routing is OpenRouter-account-level; that stands.) CORRECTION of an earlier
  overclaim: m15's 84% pass is on the 5 SCREENER tasks ONLY — NOT comparable to m14's 51% on the full 50, so
  "m15 recovered" is NOT established. OPEN: why did m14 (sha 141f7352, key ...aa828) score 0.423 while m12/m13
  (...1e8a) scored 0.768/0.571? Remaining variable = the ...aa828 KEY — is it a DIFFERENT OpenRouter account
  (diff routing/credits despite the block), or is m14's collapse real? UNRESOLVED. The m15 FULL 50-task eval
  (...1e8a key, same code) is the actual test: if H/M hold ≈ m12 → m14 was key/account; if H/M collapse too →
  reopen never-inflate. Do NOT conclude until m15's full score is in.
- **`screener_passed` was a FRONTEND DISPLAY BUG — fixed upstream a95a06c (2026-06-23).** The real screening
  gate is PASS-RATIO `SWEBENCH_SCREENING_PASS_RATIO=0.5` + `SWEBENCH_SCREENING_MIN_PASSED_TASKS` (config.py),
  NOT only token-savings. Commit a95a06c "Fix frontend screener flag and normalize validator weight split"
  replaces raw `screener_passed` with `_screener_passed_from_status(fallback=...)`. So a scraped
  `screener_passed=False` while pass-ratio ≫0.5 is STALE/buggy — trust the pass ratio. Also new upstream:
  e717e1f negative-penalty fix, 11f54f5 screener token weights configurable, 9301a74 task names in aggregate,
  validator weight-split normalization (affects emissions, not our score).

- **The OpenRouter KEY is a CONFOUND for cross-submission A/B — HOLD IT CONSTANT (2026-06-23, m14).** m14 =
  m12 + never-inflate ONLY (byte-identical to m12 on Hard/Medium, offline-proven) but scored **0.423**
  (E0.399/M0.537/H0.341) — WORSE than m12 (0.768) AND m13 (0.571). Cause is NOT the code: it used a DIFFERENT
  OpenRouter key (...aa828) than m12/m13 (...1e8a). Evidence it's the key/provider, not never-inflate:
  (1) byte-identical to m12 on H/M yet H/M collapsed; (2) Easy DROPPED 0.412→0.399 when never-inflate should
  RAISE it — m13 (same guard, OLD key) got Easy 0.561; (3) run signature = uniform pass-rate 64%→51% with runs
  COMPLETING normally (47 vs 51 steps, 686 vs 715s, only 2 early-fails each — NOT credit/rate-limit failures)
  = weaker model OUTPUT; (4) category pattern Hard≫Medium≫Easy hurt = classic weaker-backend (hard tasks are
  most model-sensitive). OpenRouter load-balances qwen3-coder across providers (diff quant/hardware); a new
  key can land on a worse backend. ⇒ **m14 is INCONCLUSIVE for never-inflate** (never cleanly tested). LESSON:
  reuse the SAME key across A/B submissions. To get a clean never-inflate read: re-submit m14's code to a
  fresh hotkey with the ...1e8a key. m12 stays LIVE/BEST (0.768), untouched. Full: reports/m13_platform_result.md.

- **PLATFORM FALSIFIED the run-variance/over-compression thesis (2026-06-23, m13=m12.1b scored 0.571 vs m12
  0.768).** m12's AGGRESSIVE HARVEST is net-POSITIVE on Hard+Medium even with per-run variance; m12.1b's
  aggressiveness-cap (>8x harvest→rich) + gentler routing made **Hard COLLAPSE 0.919→0.434 and Medium drop
  0.953→0.718**, lifting only Easy (0.412→0.561). Per-task: it redistributed toward the mean — stabilized weak
  tasks UP (t270 2/5→4/5) but BROKE strong ones DOWN (t315 3/5→0/5, t290 flip 3/5→0/5). The per-run 10-20x
  "outliers" were a SYMPTOM of already-failing short runs, not the cause (the confound was right) — capping
  them didn't recover failures, it degraded working runs. **LESSONS: (1) don't soften the H+M harvest — it's
  our edge; (2) gentleness only pays on EASY (never-inflate lifted Easy +0.149 — the one extractable win);
  (3) LOCAL EVAL IS UNRELIABLE for H+M** (it showed fragile +3; full Hard collapsed) — validate H+M candidates
  on the PLATFORM (fresh hotkey), not local. Full: `reports/m13_platform_result.md`. m12 stays LIVE/BEST.

- **RUN-VARIANCE is m12's dominant lever — the "7 flips" are mostly PARTIAL (2026-06-23).** Per-run scrape
  (250 rows = 50 tasks×5 runs, comp 108) proves it: displayed per-task score = MEAN of 5 runs; a flipping run
  scores ≥3.0 (formula floor) yet 6 of our 7 "flips" score <3.0 → each has failing runs (e.g. +1.31 = only
  ~1-2 of 5 flip). Only 2 flips are clean 5/5 (302,303). PLUS 17 pass-pass tasks BREAK on 2-3 of 5 runs (−4
  each) — invisible in the "−9.0" because many stay net-positive (t267 should be +1.4, scored +0.29). Upside:
  flip-reliability ~+7 realistic, pass-pass break-elimination up to ~+30 (upper bound) — both dwarf the
  never-inflate play. Attribution: break runs are over-compressed (14/17 lower tokens; extreme 10-20× ratios
  on t268/269/307/315) BUT also shorter (40.7 vs 54.2 steps, ~10% lower per-step retention) → the 10-20×
  outliers are ours; the bulk is mixed with provider noise → MUST measure on the Mac eval (RUNS=5, break-rate).
  Full analysis + the m12.1b reshape: `reports/m12_run_variance_analysis.md`. This is WHY the parallel eval
  matters: measuring/attacking run-variance needs many runs/task, infeasible serially.

- **Eval is LLM-latency-bound, not CPU-bound → parallelize, don't buy cores (2026-06-23).** Last batch = 32
  solves / 222 min serial = ~6.9 min/solve; each solve is an OpenClaw agent loop of up to 60 OpenRouter
  round-trips (`SOMA_BENCHMARK_MAX_ITERATIONS=60`), CPU near-idle waiting on the network. So 32 CPUs wouldn't
  speed a single solve; only concurrency cuts wall-clock. The serial driver ran 1 solve at a time → built
  `run_batch_eval_parallel.sh` (MAXJOBS). Renting a RunPod GPU box is the wrong product (we infer via
  OpenRouter, 0 local GPU) and nested privileged Docker there risks the same WSL2 mount trap; a plain CPU
  Linux VM is the right fallback, but OpenRouter throughput caps concurrency regardless.
- **The harness is parallel-safe on one Docker daemon — names are SHA(output_dir) (2026-06-23).** In
  `SOMA-benchmark/.../backends/openclaw.py`: gateway name (`:693-701`), private+control network (`:743`),
  problems/workspace dir (`:222-224`) are all `sha256(output_dir)[:12]`; the gateway port (8000) is NOT
  host-published (reached via container DNS on each run's OWN private network); the stale-resource sweeper
  SKIPS running gateways (`:1128`) and is age-gated (`:1132`). So distinct `--output-dir` ⇒ fully isolated
  solves. TWO hazards the serial driver had that break under concurrency (fixed in the parallel driver):
  (1) the plugin venv `.soma-openclaw-venv` builds INSIDE plugin_path with reinstall-on-run-start (`:451,461`)
  → solves sharing one plugin dir RACE on the venv ⇒ give each solve its own plugin copy; (2) the serial
  driver's global `docker ps|grep openclaw|rm -f` after each solve would KILL in-flight siblings ⇒ drop it,
  one safe sweep only after all jobs finish (harness cleans its own per-run gateway/workspace).

- **Incentive is layer-based (7 elements), not top-3.** Overall(E,M,H)=w1, pairs=1/6 each, singles=1/12 each.
  Winner of each = highest avg on that subset; failed-review excluded. Up to ~7 distinct miners can earn.
- **Flip-routing leaks Medium on the platform.** v15 (m7 + persistent-failure→rich) scored Medium **1.183**
  vs m7's 1.421 — the trigger pulls iterating medium tasks off the harvest bonus. Local validation under-detected
  this (only 2 medium instances). Implies m9/m10/m11 (more aggressive routing) likely also lose Medium.
- **Easy is ~1.13-bounded for us** across gentle/aggressive/adaptive compression. The king's Easy (1.347) and
  2nd's (1.433) come from agent *decisiveness* (fewer steps), not compression — unreachable via our lever.
- **King's Hard (1.751) = flip conversion @ comp_ratio ~0.85 + decisiveness.** We convert flips ~41% @ 0.52.
- **Gold-patch proxy under-counts** (equiv fixes: 11099 `\A..\Z`, 16429 `d.tzinfo if is_aware`, 14539 entity-loop).
  Real pass/fail needs SOMA_SWEREBENCH_EVAL (infeasible locally on arm64). Always manual-check gold=False.
- **Early-cutoff noise:** intermittent (~10–30% in bad windows) provider/agent variance — model emits a no-tool-call
  turn → session ends with empty/partial patch. NOT our code (same miner clean in one batch, cut in another).
- **Local e2e test-env is partly broken** (can't install some deps / run tests) → verification-wander inflates
  step counts vs the platform. Use the gold-PATCH metric + comp_ratio, not run-status, locally.
- **Dashboard:** thesoma.ai/dashboard embeds the leaderboard as JSON; per-miner: /dashboard/miner/107/<hotkey>.
  Display column order is total/Easy/Hard/Medium; JSON keys are {Easy,Medium,Hard}.
- **Per-task detail is scrapable** (collect_miner_detail.py): each miner page exposes 50 tasks with
  pass_with/without_compression, tokens_with/without, platform_score, run_count + sweSummary + swePenalties.
  Machine: data/latest/miner_detail.json + task_scores.csv; report: reports/task_detail.md.
- **The CORRECT detailed source is the platform JSON API, not the RSC scrape** (verified from
  mcp_platform/app/api/routes/frontend.py + live probe 2026-06-21). Endpoints under
  `…/api/public/frontend-key/swe/miners/{comp}[/{hotkey}[/tasks[/{task}/runs]]]`:
  leaderboard → summary → per-task → **per-RUN**. The per-run layer (`SweMinerTaskRunItem`:
  run_id, attempt_no, pass_with_compression, tokens_with_compression, platform_score,
  **time_taken_seconds, agent_steps**) is the granularity the RSC page NEVER embeds — it explains why
  pass/pass tasks can score low (some of the 5 attempts fail / cost more). DB tables: swe_bench_runs,
  swe_bench_run_validations.
- **API access (live probe):** `platform.thesoma.ai/api/public/frontend-key/...` = 401 (needs key);
  `/api/private/frontend/...` = 403 (private net); `thesoma.ai/api/...` = 404.
- **CORRECTION — per-run is KEYLESS via the dashboard's own Next.js server action.** No API key needed.
  The dashboard renders per-run rows by POSTing the server action `getSweTaskRunsAction` to
  `/dashboard/miner/{comp}/{hk}` with header `Next-Action: <hash>` and body `[comp, hk, task_id]`;
  the Flight `1:` line returns `runs[]`. The action-id hash is auto-discovered from the page JS bundle
  (survives redeploys). Tool: **`scripts/collect_runs.py` (make runs)** — vendored from
  E:/extension-sb114/soma_scraper.py (proven). The key-based fetch_platform_api.py was removed as redundant.
- **task→category map RESOLVED** (was the big missing piece). E:/extension-sb114/out/task_categories.json
  gave the 45-task E/M/H split (18 Medium, 14 Hard, 13 Easy) → config/task_categories.csv. Medium/Hard
  task-level attribution + H2 are now UNBLOCKED.
- **Per-run variance is real but is a NEAR-UNIVERSAL NOISE FLOOR, not m7's competitive gap** (full per-run
  sweep, 20 miners × 50 × 5 = 5000 runs, 2026-06-21). A 'pass/pass' task can score low because 1-of-5 runs
  breaks (−4): m7 has 19 flaky tasks / 15.3% of runs negative. BUT the top miners are the SAME: t1–t4 run
  13.6–14.4% negative, others 15.6–17.5% — m7 (15.3%) ≈ the leaders. So consistency is NOT where m7 loses.
  (m9/m10 at 22% ARE worse — part of why the flip variants cratered.) The idealized "fix all flaky runs"
  upper bound (~+0.68/45 for m7) helps everyone equally; it is not a differentiator. **Primary competitive
  lever stays COMPRESSION DEPTH** (m7 ~3.0× vs leaders ~4.9× on shared passes). Per-run data:
  data/processed/run_scores.jsonl; reports/run_variance.md. (Corrects an earlier over-claim that consistency
  was a co-equal lever.)
- **Per-task score is NOT pass + token-ratio alone.** Several pass/pass tasks score negative for m7
  (e.g. sympy-15809 ✓→✓ score −0.767, django-15499 ✓→✓ 0.237). run_count=5 → score averages 5 runs;
  some runs fail/cut off even when the task is marked "pass_with_compression". Variance is real per-task.
- **ROOT CAUSE of the real-eval block = WSL2, not Docker Desktop (CONFIRMED 2026-06-22).** The OpenClaw `rm .openclaw/sandbox-skills/skills: Device or resource busy` reproduces on BOTH Docker Desktop's WSL2 backend AND native docker.io 29.1.3 installed in WSL, on openclaw 2026.6.9 + 2026.6.8-beta.2, root + non-root — identical. Sole common factor: WSL2 kernel 6.18.33.1-microsoft-standard-WSL2 (mount-namespace/propagation under Docker-in-Docker leaves the skills bind-mount un-removable). User's past WORKING laptop was macOS (Docker Desktop = LinuxKit Linux VM, normal mounts). FIX: run the eval on a real-Linux Docker host (macOS/native Linux/VM/cloud), NOT WSL2. Turnkey: experiments/candidates/H1M_m7_deeper_safe_v1/run_real_eval.sh. ~$0 spent (agent dies ~12s pre-LLM every attempt).
- **Real eval stack BUILT but blocked by an upstream OpenClaw bug (2026-06-22).** Full stack works: uv+soma-bench, SWE-rebench harness (swebench 4.0.3), plugin, Docker builds compression-service(666MB)+django SWE-bench image(3.94GB)+alpine/openclaw+dind, m7 miner injected into the compression service (ready :8000), model openrouter/qwen/qwen3-coder. BUT the OpenClaw agent dies ~12s in workspace prep: `rm .openclaw/sandbox-skills/skills` fails — Permission denied (uid1000) / Device-or-resource-busy (root, it's a bind-mount). alpine/openclaw:latest seeds a root-owned skills bind-mount then rm's it. NOT an H1M/config issue; ~no spend. Config fixes found along the way: COMPACT_BENCH_COMPRESSION_SERVICE_CONTEXT=/mnt/e/soma/sandbox_service/compression_service, remove docker credsStore(desktop.exe), COMPACT_BENCH_LLM_BASE_URL, COMPACT_BENCH_PLUGIN_TEMPLATE_PATH, SOMA_OPENCLAW_USER=root. Unblock: pin a known-good openclaw image tag / skills-disable / raise with DendriteHQ. reports/H1M_real_eval.md, data/latest/h1m_real_eval_smoke.json.
- **Real SWE-bench eval is BLOCKED on infra not present here (2026-06-22).** Probe: Docker daemon NOT
  available (docker-desktop WSL distro Stopped; Docker Desktop not running), and soma_bench / openclaw /
  SOMA-benchmark / SOMA-plugin are absent (external; referenced only as /path/to/... in the miner README;
  no URL in this repo — likely private DendriteHQ). The eval runs OUTSIDE this ops repo: openclaw solves a
  SWE-bench task inside per-instance Docker images (ghcr.io/epoch-research/swe-bench.eval.x86_64.<inst>) with
  the miner injected as <SOMA-plugin>/base_miner.py via `python -m soma_bench benchmark-solve`. UNBLOCK needs
  (user): start Docker Desktop + WSL integration; provide+`pip install -e` SOMA-benchmark + the SOMA-plugin.
  Prepared & ready: experiments/manifests/H1M_real_eval_medium_first.yaml, candidate run_smoke_real_eval.sh
  (guarded; key read from secrets.env, never printed), and the proven --results gate. Smoke NOT run; no
  results invented. Cost est: smoke ~$3-18/1-3h; full Medium-first ~$10-60/3-9h (model + runs_per_task driven).
- **H1M real-task experiment run (2026-06-22): experiments/runs/2026-06-22_005707_H1M_eval/.** REAL m7
  baseline on the 7 Medium-first targets = 7/7 pass, 0% neg-run, 0 broke, avg 3.02×, Medium est score 1.690;
  fragile group (sympy-17139/-16766/django-11239/-14493) m7 baseline = pass 0.75, neg-run 40%, broke 1 (only
  sympy-17139 — the rest are flip-only breaks, m7 clean). Candidate projection (offline proxy × m7): h1m@deep
  ~3.43× (+13.7%, est +0.064/task), h1m@medium ~3.34× (+10.8%). Offline gate PASS (ratio≥8%, guard fires,
  protections intact); real pass-rate/neg-run/broke = PENDING_EVAL (SOMA SWE-bench; per-call contexts not
  available offline). Verdict: ADVANCE candidate-only; do NOT promote to base until the eval confirms.
- **Candidate H1M_m7_deeper_safe_v1 built + offline-validated (2026-06-21).** m7 derivative; a profile layer
  deepens ONLY the harvest path (lower TARGET 8k→{7k,6k,5.2k} + tighter MID/MID2/ASSIST/TAIL caps); rich path,
  all protections (load-bearing, ERROR_MARKERS, active paths, recent-intact, digest), and coach are UNCHANGED;
  fragile guard fires one error-hit sooner (ERROR_GUARD_MIN_HITS 4→3). Offline (ratio+structural-safety on
  sample+synthetic transcripts via the compression-service protocol): **h1m@deep = +13.7% deeper on 6/6 clean
  harvest cases, 0 regressions, 100% protected content kept, 0 broken tool-pairing**; fragile guard correctly
  sends error-dense transcripts to rich. A/B sanity: H1M_PROFILE=m7 ≡ m7 exactly. ~est per-call score lift
  (1+0.5ln model) +0.06 (deep). **PENDING_EVAL:** real platform pass-rate/neg-run/Medium need the SOMA SWE-bench
  env — NOT measurable offline, not invented. Files: experiments/candidates/H1M_m7_deeper_safe_v1/ (h1m_miner.py,
  h1m_eval.py), experiments/reports/H1M_m7_deeper_safe_v1.md, data/latest/h1m_candidate_results.json.
- **Deeper compression is NOT riskier (2026-06-21 risk analysis).** On shared-pass tasks, corr(ratio,
  neg-run-rate) ≈0 / slightly negative every category (overall −0.09; Easy −0.22, Med −0.03, Hard −0.12).
  27/36 shared-pass tasks have a leader passing CLEANLY (≤1 neg) at ≥4.5× → leader-level depth is
  demonstrably pass-safe. ⇒ H1 (deeper pass-safe compression) is the right call. reports/compression_depth_risk.md.
- **Per-category gap (m7 vs top-4):** Easy gap +0.41 & m7 is FLAKIEST here (26% neg-runs vs 20%) — m7's worst
  category. Medium gap −0.17 (m7 BEATS the top-4 average) & m7 is most STABLE (4.4% vs 10.1%) at only 2.84×
  → Medium = m7's strength + safest place to push depth + closest reward (1.421 vs 1.620). Hard gap +0.36;
  leaders compress DEEPER (5.40×) AND are LESS flaky (14.5%) than m7 (3.53×, 21.7%) → Hard flakiness is not
  caused by depth. reports/per_category_gap.md, data/latest/per_category_gap.json.
- **2 catastrophic Hard gaps are SOLVING gaps, not compression:** django-14999 (m7 1.10 vs leader 4.01 at
  ~equal ratio 2.46 vs 2.68) and sympy-22714 — m7 fails/flaky where the leader solves. Compression won't fix these.
- **Only ~4 fragile tasks total:** m7 breaks just sympy-17139; sympy-16766/django-11239/django-14493 were broken
  ONLY by flip variants (m9/m10/m11) → another nail in flip-routing. H1 targets: 19 safe / 12 moderate / 5 fragile.
- **NOTE token-type split still MISSING** (one compressed-token count per run; no input/cached/output) → H4
  weighted-cost + "compression vs output-token" remain blocked.
- **FIRST REAL SWE-bench eval RAN — on the Mac (2026-06-22). H1M smoke complete + VALID.** The WSL2 block is
  gone on macOS Docker Desktop. `run_real_eval.sh` had 4 latent bugs (it had never completed a solve anywhere):
  (1) Bash-4 assoc arrays → macOS ships Bash 3.2 (rewrote as `case`); (2) missing `--openclaw-current-user`
  (mandatory on macOS); (3) missing the macOS gateway env (`SOMA_HOST_DOCKER_BINARY`=arm64 static CLI +
  `SOMA_OPENCLAW_GATEWAY_IMAGE`=2026.5.27 pin + settle) — all baked into the .env it writes; (4) **`H1M_PROFILE`
  is NOT referenced in soma_bench → the host env var never reaches the compression container, so the miner
  (read at import) defaulted to "medium" and `h1m@deep` silently ran as medium.** FIX: bake the profile INTO
  `base_miner.py` (the file IS what's copied to `/app/miner/base_miner.py` in the container), via sed on copy.
  All 4 fixed; spend ~$0.15 total (failures were all pre-LLM).
- **H1M smoke RESULT (corrected run 2026-06-22_044503, profiles genuinely distinct): deeper compression is
  PASS-SAFE.** m7 / h1m@medium / h1m@deep each **resolved 2/2** (django-10914, django-15851), F2P + P2P 100%,
  0 new broken baselines, 0 integrity errors. **Gate: h1m@deep = ACCEPT** (all 5 checks, ratio +13.9%);
  h1m@medium = REJECT on ratio (−35.5%) — **BUT that ratio check is single-run NOISE** (agent path varied
  16–37 calls/run, which dominates token totals). The RELIABLE depth measure stays OFFLINE (deep +13.7%,
  medium +10.8%, 0 regressions, protections intact). So both profiles are pass-safe on the 2 tested tasks;
  deep compresses deepest with the same safety. Real neg-run / pass-rate at scale = still need the full
  Medium-first set (7 tasks, multiple runs). Tools: `analyze_smoke.py`; gate CSVs rebuilt from
  evaluation-summary.json (NOT output.jsonl `resolved`, which is always None — verdict lives in
  `evaluation-summary.json.patch_evaluation`).
- **The top miners beat m7 on COMPRESSION RATIO, not pass-rate (2026-06-21 top-10 detail).** All scored
  miners share the same 34 baseline passes. Leaders 5EkiFXSR/5FbqgypX/5E7hCCzj/5ERdwbn5 run **~4.7–5.0×**
  mean compression while still passing 37–39/45; m7 runs only **~3.0×** (passes 38). On the 45 scored tasks
  5EkiFXSR beats m7 on 34/45, 5FbqgypX on 31/45 — almost entirely via deeper compression (bigger 0.5·ln(ratio)
  token bonus), not extra passes. Exception: Hard-king 5DhHqmB1 wins via pass-rate (40 passes) at only 3.06×.
  ⚠️ This refines the prior "compression at its ceiling / 8k harvest is the sweet spot" decision — leaders get
  ~5× without losing the pass, so there may be ratio headroom above m7's ~3×. (Strategy call left to user.)
- **Compression-techniques survey (web, 2026-06-22; reports/compression_techniques_research.md).** The
  leaders' 4.8–5× pass-safe is NOT a smarter model — it's disciplined EXTRACTIVE masking. Three findings
  change our approach: (1) **CACHE-STABILITY is likely the leaders' real edge** — a prefix-mutating
  compressor cache-thrashes (cache_read invalidated → MORE tokens, not fewer); Manus reports cached input
  10× cheaper. So compression must be APPEND-ONLY / stable-prefix (keep system+task+recent-tail byte-
  identical, elide only the MIDDLE). This may explain our noisy/high real-eval token totals (we may be
  cache-thrashing). (2) **Context Rot (Chroma) tested the Qwen3 family** — our model degrades as input
  grows even under the window cap, so DEEPER compression can IMPROVE pass-rate (removing stale rot), not
  just save tokens — reconciles the old "aggression→wander" (crude load-bearing loss hurts; rot removal
  helps). (3) **Mask tool-result BODIES, never drop the message** (keep msg+tool_call_id) — structurally
  prevents the −4 orphan-pair fail AND tool outputs are the bulk of the ratio. TRAPS for us: compress-to-
  embeddings (AutoCompressor/ICAE/xRAG — impossible over a text API) and abstractive LLM summary at the head
  (cache-busting + hallucination). Closest real-world patterns: SWE-agent LastNObservations + keep_output,
  OpenHands ObservationMaskingCondenser, Manus append-only+file-offload. Lost-in-the-Middle (2307.03172)
  backs eliding the middle. ⇒ for the king-depth sweep, watch CACHE behavior, not just total tokens.
- **H1M FOUNDATION BATCH (real eval, 2026-06-22; 15 tasks × m7 + h1m@deep × 2 runs; run 2026-06-22_052602).**
  Per-category (resolved / neg-runs / broke): **Medium deep 14/14, 0 neg, 0 broke (BEAT m7's 13/14 — deep
  resolved sympy-24539 where m7 flaked); Hard-bonus deep 4/4, 0 broke; Easy deep 4/4, 0 broke.** → deep is
  PASS-SAFE + shippable-class on the non-fragile categories. **FRAGILE: deep 4/8 vs m7 5/8; deep broke a P2P
  baseline on django-14493 that m7 kept (1 NEW break) + went 0/2 on django-11239 (m7 1/2).** **GATE = REJECT,
  solely on `no_new_broken_baseline_vs_m7` (django-14493)**; ALL other checks PASS — compression **+8.2% real**
  (cleared +8%), Medium neg-run 0% (=m7), Medium score no-drop, 0 integrity errors. → the fragile guard
  (ERROR_GUARD_MIN_HITS=3) does NOT fully protect under deep compression; harden/exclude fragile before
  shipping deep. **Token totals NOISY at n=2 + show likely CACHE-THRASH:** deep used MORE tokens than m7 on
  some tasks (10914 40.5 calls/657k vs 29.5/443k; 13363) and far LESS on others (15851 18c/182k vs 31c/360k;
  14752; sympy-17139) — path variance + prefix-mutation eating depth gains, exactly the cache-stability
  concern. ⇒ king plan: depth-push on Medium/Hard-bonus/Easy is safe; fragile needs guard work; realizing the
  king's 5× needs CACHE-STABLE (append-only) deepening, not just lower targets.
- **🔴 TOP OF COMP 107 FAILED REVIEW (2026-06-22, dashboard re-check — a NEW competition cycle has opened; the
  default /dashboard now shows it).** Per-miner comp-107 pages (`/dashboard/miner/107/<hk>`, status in escaped
  Flight JSON `\"status\":\"failed review\"`) confirm: **FAILED = t1 5EkiFXSR (1.460, overall king), t2
  5E7hCCzj (1.436), t3 5FbqgypX (1.415, MEDIUM king), t4 5DhHqmB1 (1.410, HARD king), t5 5GEUZcud (1.355),
  t7 5ERdwbn5 (1.263).** STILL SCORED = t6 5G6J5dA1 (1.335), t8 5EPkREJ9 (1.256), t9 5CJs9EmL (1.222),
  t10 5GgUhFiG (1.158) + all our miners. **Ratio is NOT the discriminator** (t10 survived at 5.24×; t5 failed
  at 2.40×; t4 failed at 3.06×) → it's a per-miner manual/compliance review, cause UNKNOWN from the data —
  MUST investigate (Discord/review notes) before doubling down on aggressive compression (DQ risk for our
  H1M/H3 deep candidates is unquantified). **RECOMPUTED reward elements among VALID miners (tracked set only —
  untracked ranks 11+ may shift it): Overall t6 1.334 / m7(us) #2 1.276; Medium t9 1.423 / m7(us) 1.421
  (≈TIE, +0.003 wins it); (M,H) t6 1.361 / m7(us) #2 1.351; Hard t6 1.525; Easy t10 1.373; (E,M) t9 1.321.**
  → m7 is suddenly top-tier (review-PASSING): #2 overall + a hair from the Medium element + #2 (M,H). The
  king target drops from t1 (1.460, 4.83× deep) to **t6 (1.335, 2.88× — NOT a deep compressor; wins via Hard
  1.525 + balance)** → extreme-depth chase is no longer required to be king-competitive.
- **H4_compliant_cache_stable BUILT + offline-green (2026-06-22) — the next-round legal candidate.** Copied
  H3's compression engine, stripped ALL prompt-side steering: removed the coach (append_coach/build_coach_text/
  governor), force-stop ("STOP NOW"/"do not explore"/"if tests pass stop"), behavior-steering, and ALL private
  markers ([SOMA COMPRESSED HISTORY], [SOMA CONTEXT NOTE], [old output elided…]) + dead digest helpers. Now uses
  ONLY allowed markers (`[[CMP]]`/`[[/CMP]]` for masked/truncated regions; `[[BLOCK N]]` + `Same response as in
  [[BLOCK N]].` for dedup/superseded views) and loop-detection emits ONLY `loop_detected: repeated assistant
  response` / `loop_detected: repeated tool call signature`. Kept the full engine (cache-stable harvest, frozen
  head, masking, superseded-view elision, sticky keep-list, fragile guard, rich, load-bearing allowlist,
  pairing). **New scanner `scripts/check_prompt_compliance.py`: PASS on H4, FAIL on H3 + m7 (coach detected).**
  Offline: 12/12 tests PASS; **H4 compresses +5.69% vs H3** (compact markers replace verbose private ones; +15–18%
  on harvest synthetics); **prefix-stability identical to H3 (no regression)**; 0 protection regressions. Files:
  experiments/candidates/H4_compliant_cache_stable/{h4_miner.py,h4_eval.py}, scripts/check_prompt_compliance.py,
  data/latest/h4_compliance_results.json, experiments/reports/H4_compliant_cache_stable.md. NOT real-eval'd yet.
- **🔬 H3 CACHE-STABLE EVAL FALSIFIED THE CACHE THESIS — h1m_deep WINS (2026-06-22, run 2026-06-22_122215;
  m7 / h1m@deep / h3@cache_safe / h3@cache_king × 4 fragile + 4 Medium × 2 runs).** GATES: **h1m@deep =
  ACCEPT** (+28.1% real compression, 0 new breaks, Medium 8/8 vs m7 6/8); **h3_cache_safe = REJECT** (1 new
  break + compression **−12.8%**, WORSE than m7); **h3_cache_king = REJECT** (1 new break, +18.7%). Per-category
  cache_hit: fragile m7 0.84 / h1m 0.81 / **h3_safe 0.73 / h3_king 0.67**; Medium m7 0.63 / h1m 0.68 /
  h3_safe 0.70 / **h3_king 0.58** — **H3 cache_hit is LOWER than h1m, the OPPOSITE of its design goal** (one
  h3_king/sympy-24539 run had 0 cache_read), and H3 fresh-input + tokens are HIGHER. **The cache-stability
  re-architecture did NOT pay off in the live eval** — the digest-in-msg1 (h1m) cached BETTER than H3's "fix";
  per-message `[[CMP]]` masking makes MORE fresh-input bytes than bulk truncation, and the offline prefix-
  stability proof didn't translate to live cache gains. ROBUST across the noise: **Medium is pass-safe +
  more-reliable than m7 for ALL compressors (8/8 vs m7 6/8); fragile breaks MORE under any deep compression**
  (h3 2–3 new breaks vs h1m/m7 1; guard still imperfect). ⇒ **DROP the cache-stable H3/H4 engine; h1m@deep is
  the better base.** The next-round COMPLIANT candidate should apply the H4 coach-strip + `[[CMP]]` markers to
  **h1m@deep's engine, not H3's.** (n=2/task caveat, but gate + cache + break signals all agree.)
- **m12 (m7-compliant) FIRST NEW-ROUND SCORE — CoT-Compression-4/comp108 (2026-06-22): SCORED, PASSED REVIEW,
  total 0.768 = currently #1 among SCORED miners.** Cats Easy 0.412 / Medium 0.953 / Hard 0.919. → our
  compliant (coach-free, [[CMP]]) approach is review-clean + competitive. Per-task (45 non-screener): miner-pass
  33 vs baseline-pass 29 (**+4 flips**), mean ratio **1.75×**, mean score 0.738, **11 NEGATIVE-score tasks**.
  **DRAG DIAGNOSIS (gap analysis):** (1) **Easy 0.412 is the weak category** (vs M/H ~0.93) — same structural
  Easy weakness as old m7. (2) **7 baseline-PASS tasks scored NEGATIVE** (we broke / over-compressed): tasks
  270 (−1.98, failed a base-pass), 297 (−1.83, failed), 313 (−1.03, ratio 0.66× = we INFLATED tokens!), 292/295/
  307 (passed but run-variance negatives). These −1 to −2 hits are the main score drag. (3) flips modest (+4)
  and partly EATEN by the 7 broken baselines. Head-to-head vs #2 5GYxeJjd (0.661): m12 wins 24 / loses 21
  (CLOSE) — we win via more compression (1.75× vs their 1.34×) where we don't break, but LOSE the tasks we
  broke (rival is GENTLER → keeps those passes; e.g. task 295 m12 −1.02 vs rival +1.09). **LEVER = RELIABILITY,
  not more depth: cut the over-compression breaks (esp. Easy + the 7 base-pass negatives) by routing break-prone
  tasks gentler/pass-through — deeper (H4b) would break MORE, the wrong direction for this round.** Threat:
  5CwZBKyL in-queue 1.062 but only 5 screener tasks done (provisional, not a full eval yet).
- **NEW-ROUND SCORING + QUALIFICATION GATE decoded from DendriteHQ/SOMA source (2026-06-22; no new commits
  since the policy — origin/main 82dfc28, README_prompting unchanged → our compliance still holds).** Two
  mechanics, both new for comp 108:
  **(A) Per-run SCORE (mcp_platform/app/api/routes/scoring.py):** `score = base + λ·clamp(ln(ratio), −2, +2)`
  where ratio = tokens_without/tokens_with, and base/λ by pass-outcome: **pass→pass = +1.0 (λ0.5); break
  (base-pass→compressed-FAIL) = −4.0 (λ0, flat); FLIP (base-fail→compressed-pass) = +4.0 (λ0.5); both-fail =
  0 (λ0.1).** Displayed per-task score = mean of the 5 runs (so a "passing" task with some broken runs averages
  negative — explains m12's −1 to −2 "pass" tasks = run-variance breaks). There is ALSO an aggregate savings
  MULTIPLIER (`adjust_miner_score_with_token_savings`: −4+(raw+4)·smoothstep) that crushes scores toward −4 as
  savings→≤−20%. **Dominant terms: breaks −4 (flat) and flips +4 dwarf the compression term (±λ·ln ≈ ±0.3 at
  our 1.75×).** → **Avoiding a −4 break is worth ~3 clean pass-pass tasks; flips (+4) are gold.** Confirms
  reliability-first (m12.1's 1b break-cut is the top lever); compression ratio is a secondary per-task bonus.
  **(B) Screener QUALIFICATION GATE:** must achieve **≥10% WEIGHTED token savings** to qualify, weights
  **input×1.0 + cached_input×(1/3) + output×3.0** (configurable). The comp-108 "not qualified" miners failed
  this; m12 cleared it. **Output weighted 3× → reducing agent OUTPUT/steps (less wander via cleaner context)
  is the high-value gate lever; cached-input savings (our bulk) count only 1/3.** ⇒ strategy: (1) never break
  (−4), (2) win/keep flips (+4), (3) keep ≥10–20% real savings + reduce wander/output (gate + multiplier),
  (4) Easy is structurally low partly because short tasks lack compressible content to clear the savings floor.
- **NEW KING in comp 108 = 5DFvymSeEw (0.7801), barely above m12 (0.7685, +0.012) — and it's a MIRROR IMAGE
  of us (2026-06-23).** Category gap (king − m12): **Easy +0.401 (king 0.812 vs m12 0.412), Medium −0.019
  (m12 0.953), Hard −0.323 (m12 0.919 vs king 0.596).** We WIN Hard + Medium decisively and LOSE only Easy —
  but the Easy gap (+0.40) just outweighs our Hard lead (+0.32). KEY: the king does NOT beat us on the hard
  stuff — m12 passes MORE (33 vs 30), more FLIPS (7 vs 5), far better Hard; the king simply has FEWER NEGATIVES
  (7 vs m12's 11) at the SAME compression (~1.77× vs 1.75×), and those extra m12 negatives concentrate in EASY.
  ⇒ **The entire deficit to #1 is EASY RELIABILITY (cut our Easy breaks/run-variance/inflation negatives).
  That is EXACTLY what m12.1 targets** (never-inflate + shallow_small→passthrough + fewer breaks) — and it does
  NOT touch our Hard 0.92 moat (king is only 0.60 there). If m12.1 lifts Easy from 0.41 toward ~0.7+ while
  holding Hard, total → ~0.88+ >> king 0.78. CAVEAT: the m12-vs-m12.1 regression set is fragile+Medium (no
  Easy instances — comp-108 task names masked), so m12.1's Easy lift is a platform bet; ADD known-Easy
  SWE-bench instances (from config/task_categories.csv) to a follow-up eval to validate the Easy gain directly.
- **m12.1 REGRESSION EVAL VERDICT (2026-06-23, run 2026-06-22_235242, m12 vs m12.1, 8 tasks×2): DO NOT SHIP —
  m12.1 OVER-ROUTED Medium.** Breaks: m12.1 fragile=2 vs m12=3 (1 fewer — marginal reliability win); Medium
  breaks 0 for both. BUT tokens-PER-CALL (robust to call-count noise) shows **m12.1 uses +28% more tokens/call
  on Medium** (m12 17162 → m12.1 22009; consistent +25/+33/+4/+43% across all 4 Medium tasks) = ~28% LESS
  compression on Medium → lower ratio → lower Medium score. The 1b gentle routing (shallow_small→passthrough +
  earlier error-guard 24/6/3) is too aggressive — it catches compressible MEDIUM tasks and routes them to
  rich/passthrough, surrendering our Medium strength for a 1-break gain. BAD trade vs the strategy (grow/keep
  H+M). **FIX → m12.1b: keep 1a never-inflate (pure win, no downside); DROP/narrow the shallow_small→passthrough
  route + revert the over-sensitive error-guard so it fires ONLY on persistent/genuinely-break-prone signals,
  NOT shallow-Medium.** m12 stays live; do not replace with m12.1.
