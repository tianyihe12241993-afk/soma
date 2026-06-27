# CURRENT — live status (2026-06-26 ~10:50 UTC) — READ FIRST after compaction

_Mode: comp 108 (CoT-Compression-4, SN114). ⚠️ SCORING REGIME CHANGED 2026-06-26 — see top section. Dual-agent
(Claude+Codex) protocol OPERATIONAL (see CLAUDE.md). Files = source of truth. Read this + NEXT_ACTIONS + DISCOVERIES (top) before acting._

## ★★★ 2026-06-27 09:20Z — CORRECTED PICTURE + NEW PLAN (attack OVERALL 57% + Single-E). PORTFOLIO = 23.8%.
**Re-verified ALL scores 4 ways (leaderboard == detail `category_scores` == per-task `platform_score`; 2 snapshots; current 09:20Z; penalties ~0 on ours).**
- **LABELING FIX:** `5DCnA57` = the **#1 NEAR-PASSTHROUGH (0.697)**, NOT "the king" (I'd conflated them). Repo's "king" = `5Ggq` (#2, 0.673,
  E0.924/M0.848/H0.261). 5DCnA57 wins the **Overall element (weight 1.0 = 57% of pool) + Single-E** → 61.9%.
- **OUR 3 LIVE MINERS** (all USER-confirmed ours 2026-06-27): **np1/m26** (`5Ekcy`, cap 6k) #5 **0.610** E1.066/M0.620/H0.170 ·
  **np2** (`5CPbtf`, cap 16k) #2 **0.684** E1.052/M0.849/H0.173 · **np3** (`5F9ZRe`, cap 28k) #3 **0.682** E0.859/M0.828/H0.369.
  m12 (`5Dz7`) 0.130 LIVE/untouched.
- **WE WIN: Pair(E,M) 0.951 + Single-M 0.849 (np2) + Pair(M,H) 0.599 (np3) = 23.8%.** m26 wins nothing yet, but **E1.066 = 0.001 from Single-E**.
- **RIVALS:** `5GgVXzUB` (E0.845/M0.252/**H0.676**, LEGIT review=scored) wins Pair(E,H) 0.760 + Single-H 0.676 = 14.3%. 5DCnA57 = 61.9%.
- **NEW PLAN (USER 2026-06-27) — attack BOTH:** **(1) Single-E** (+4.8% → 28.6%, NEAR-FREE: push m26's 1.066 past 5DCnA57's 1.067) and
  **(2) the OVERALL element** (57%; beat 5DCnA57's 0.703). Overall math: our Medium (0.849 ≫ 5DCnA57's 0.719) means we need only
  **(E+H)/2 > 0.630** (np2 0.613 / np3 0.614 — short ~0.03). The blocker: Overall needs ONE miner **HIGH-E-AND-H**; the flat per-message cap
  is **ZERO-SUM E↔H** (np1 6k / np2 16k / np3 28k = the three points — can't get both) → Overall needs a **NEW mechanism, not a flat-cap tweak**
  (better-extractive np4 = NO-GO: Hard-block critical content SPREAD 22–63k, np2 already keeps it; a "balanced middle cap" wins NO element).
- **IN PROGRESS:** deep-dive **#1 5DCnA57 vs our 3** on **cache% / weighted-vs-raw tokens / input·cached·output split / per-task** — to find HOW
  5DCnA57 keeps Hard content without the Easy-wander our cap suffers (the Overall edge). Report → `reports/cache_stable_design.md §15`.
- Cap lever EXHAUSTED at 23.8% (own both E↔H corners). m12 + np1 + np2 + np3 all LIVE; uploads USER-run; read only at status=scored.

## 🚨🚨 SCORING REGIME CHANGE (2026-06-26, commit b79fcaee, LIVE) — WEIGHTED TOKENS. m12 CRATERED 0.768→0.130, LOST EVERYTHING.
**SOMA merged weighted-token scoring (announced by Matt). Verified from the commit (mcp_platform/.../scoring.py + docs/miner/scoring.md):**
- **weighted_tokens = 1.0·input + (1/3)·cached_input + 3.0·output.** Ratio term AND the total savings-multiplier now use WEIGHTED tokens.
- **FLIP base 4.0→2.0** (λ=0.5 unchanged). **BREAK −4.0 UNCHANGED.** pass-pass +1, fail-fail 0 unchanged. So break:flip asymmetry 4:4 → **4:2** (avoiding a break now worth 2× landing a flip → consistency matters even MORE).
- **FULL RE-SCORE of the board (snap 104640):** king 0.957→**0.673** (#1, H0.727→0.261); oldking 0.780→0.556; 5DtEz 0.714→0.383;
  5GBPFA 0.797→0.373; **m12 5Dz7 0.768→0.130 (E0.412→0.364, M0.953→−0.442, H0.919→0.067).** Everyone fell; **m12 fell HARDEST → we now win NOTHING (lost Single-Hard + the 4.76%).**
- ★ **VERIFIED MECHANISM = CACHE, not output** (output ~1% of tokens for all = red herring). Cached fraction: m12 **56%** / 5DtEz 60% vs king **85%** / oldking 88%.
  m12's blind-truncate HARVEST rewrites the context every turn → BUSTS the prompt cache → its tokens land in the 1× input bucket not the ⅓ cached bucket → weighted_with stays high → ratio bonus collapses (Medium went NEGATIVE). The king keeps a STABLE prefix (85% cached) → low weighted tokens → bonus survives. **m12 was built for raw-token scoring where cache was irrelevant; that regime just ended.**
- ★★ **THE "CACHE LEVER" WE DECLARED DEAD IS NOW THE DOMINANT LEVER.** (Old CORRECTED-SCIENCE #3 "caching does not affect score / cache lever DEAD" is REVERSED.) Our shelved **AOW-lite/AOW-bet freeze prototypes (cache-stable compression) are now the RIGHT direction.** New optimal compressor = STABLE-PREFIX / append-only / minimal per-turn churn (maximize cached%) + avoid breaks (now 2× flips). Output reduction is minor.
- ★ **LOCAL EVAL CONFIRMS MECHANISM + FIX (m25 calibration, 36 solves, 0 fail).** Local captures `cache_read_tokens` + the assemble MODE per run. By MODE: m12's **`pruned`/harvest-drop → ~0% cache** (django-13810: weighted/raw=**1.03** — compression is COUNTERPRODUCTIVE under weighted tokens); m12's **`gentle`/rich → 80-90% cache** (weighted/raw ≈0.45, like the king). ⇒ the cache-bust is SPECIFICALLY the **harvest DROP/PRUNE (rewrites the prefix → invalidates prompt cache)**; rich/gentle (never-drops, stable prefix) is ALREADY cache-good. **FIX = prefix-stable / no-prune / append-only (rich-everywhere or AOW-freeze).** m25 does NOT fix it (68% cache, also perturbs harvest). **We can now measure cache% per candidate LOCALLY** (token_usage.total: input/output/cache_read + mode) — the eval infra is validated for the cache regime. TENSION to solve: huge contexts still need size reduction WITHOUT rewriting the cached prefix (e.g. truncate only newest / append compact summary, never rewrite old turns).
- **OBSOLETE (all raw-token-era, do NOT act on):** CORRECTED-SCIENCE #1-5 (esp. "game is PASS/BREAK not compression" — compression-CACHE now matters a lot), the whole-architecture frontier numbers, the two-singles / Single-E / m26 Easy-specialist plan, m25/m27 verdicts, the "defend Hard 0.919" strategy. ALL category means/standings below are raw-token-era unless marked NEW. Re-derive under weighted tokens.
- **STILL VALID but now SECONDARY:** the category-MAP recovery (E/M/H assignment is task-intrinsic, formula-independent). DEPRIORITIZED because the NEW strategy (cache-stability) is category-AGNOSTIC — cache behavior tracks compression MODE/context-SIZE, not E/M/H. Trace STOPPED (5GhUtKrYP finished; map effort was also disrupted: caught it at task 8 not 0, AND the regime change mid-trace shifted means globally → corrupted attribution → only 14/45 mapped, unreliable). To get a CLEAN map later: catch a fresh miner from task~0 evaluating ENTIRELY under the new formula. The live-trace method + dual-agent protocol remain valid. NOTE: 5GhUtKrYP finished at total −0.92 (E−1.32/M−0.19/H−1.31) = another cache-buster scoring NEGATIVE → confirms cache-busting compression is catastrophic under weighted tokens.
- ★ **OPPORTUNITY:** field reshuffled, everyone dropped, king only 0.673 (lots of headroom), m12 mis-built for the new regime. A purpose-built **cache-stable compressor** could leap. We have a head start (AOW prototypes + this verified mechanism). m12 stays LIVE/untouched (now low-scoring but not harmful); building a cache-optimized candidate on a separate hotkey is the obvious next move — USER decision, via dual-agent protocol.
- ★ **OUR BEST SUBMISSION under weighted tokens = m25 (5GpB36) total 0.449, #9 of 54 legit** (E0.917 #6 / M0.289 #18 / H0.169 #12) — wins NOTHING but our strongest; the ordering INVERTED (m12 old-best now near our bottom 0.130; lighter m25/m22 rose). Our re-scored set: m25 0.449 > m22 0.429 > m21 0.362 > m13 0.338 > m14 0.176 > m12 0.130 > m15 −4.0(broken) ; m17 not-qualified.
- ★★ **FIELD ARCHETYPE FLIPPED: 5DCnA57 (NEAR-PASSTHROUGH) is now #1 (0.697)**, king #2 (0.673). The light/near-passthrough compressor we dismissed as under-compression-penalty-capped under RAW tokens now WINS — minimal context rewrite → maximal cache + minimal agent disruption (consistency), accepting ~0 compression bonus. **⇒ the winning design may be NEAR-PASSTHROUGH (compress as little as possible, only when the window forces it, keep prefix maximally stable) — even simpler than aow_bet's freeze. Lean LIGHT + cache-stable.** Hard is low for everyone now (field max 0.342); field top total 0.697 (was 0.957) = depressed + beatable.
- ★ **aow_bet cache-stable candidate = NO-GO as-is (Claude+Codex, 2026-06-26; reports/cache_stable_design.md §8).** Freeze MECHANISM validated deterministically (scripts/prefix_stability.py: aow_bet 99.9% prefix-stable in harvest vs m12 70%/min5.8%; window-bound PASS max 46k tok; compliance PASS; no corrupted output). BUT Codex caught the blocker I missed: **save_state persists the LARGER frozen output (line 503, NOT decoupled) → resolve_stateful_messages rebuilds `working` from it → on harvest→rich escalation, rich sees aow_bet's larger trajectory, NOT m12's → aow_bet ≠ m12 in rich → the PROVEN m21/m22/m25 Hard-crater mechanism** (m21 keep-more cratered Hard 0.461). My "strictly ≥ m12" was FALSE. Reconciled: compliance/corruption were Codex over-flags (holding raw bytes is compliant; fallbacks are m12-equivalent), but the state-coupling Hard risk is real → NO-GO stands. Built scripts/prefix_stability.py + window_bound_check.py + analyze_cache.py (reusable). NEXT BUILD = **near-passthrough** (path B: cache-stable across ALL modes, no harvest/rich state-coupling; the 5DCnA57 #1 archetype). Decoupling aow_bet (path A) fights the freeze (state-output mismatch → re-seed → cache lost; m25's tension). m12 LIVE/untouched; no hotkey spent.
- ★ **np1 NEAR-PASSTHROUGH candidate BUILT + offline-validated (2026-06-26, upload_miner_np1.py; reports/cache_stable_design.md §10).**
  STATELESS idempotent per-message cap (extractive-cap each tool result >6000 chars w/ active=frozenset; passthrough everything
  else incl already-[[CMP]]/<=cap). NO mode-split, NO save_state, NO resolve_stateful_messages → the aow_bet/m21/m22 state-coupling
  Hard-crater CANNOT occur (one mode). VALIDATED: prefix-stability **100%/min99.8%** (m12 70%/min5.8%; aow_bet 99.9%), 0 orphans/80
  turns, IDEMPOTENT (np1 on own output = byte-identical), passthrough when small (changed=False native), output ≤ native always
  (can't overflow worse than baseline), compliant (allowed markers only, no LLM/task-ID). Reuses all m12 compliant primitives; m12
  git-clean/untouched. OPEN (platform-only): pass-rate (does 6k cap break agent? light+extractive→low risk), savings-floor vs
  under-compression penalty (~0.70 cap like 5DCnA57; either way ≫ our m25 0.449). NP_RESULT_CAP=6000 = light first cut; tune down if it eats the savings penalty.
  **CODEX PRE-UPLOAD AUDIT DONE (agent a551465a; reports/cache_stable_design.md §11): 1 hard blocker (no-inflation: 6001-char
  result inflated to 6018 via the [[CMP]] wrapper when extractive couldn't shrink it) FOUND → FIXED (emit wrapped only if
  len<orig, else passthrough) → RE-VALIDATED (6001→6001, all outputs ≤ input, idempotent, 100% prefix-stable, 0 orphans).
  Compliance/idempotence/window all CONFIRM; corruption=accepted WARN (string-only on compressed results, m12-equivalent);
  strategy=platform-only WARN (pass-rate + savings-floor unquantifiable offline). np1 is OFFLINE-CLEAR. **UPLOADED 2026-06-26 ~16:0x as label m26, hotkey 5EkcybHjWyP3Pi26Hr2FYsCNyVKHEDEyDC9abaJoheQDBgFP (USER-confirmed; in config/miners.yaml m26sub).** **SCORED #3 of 59: total 0.610 (E1.066 / M0.620 / H0.170)** — from m12's cratered 0.130 to #3. Cache-stable thesis VALIDATED.
- GAP analysis (reports/cache_stable_design.md §12; dissect_top_miners.py): m26 cache 93% (BEST, > #1's 91%), ratio 1.64×, mean 0.575,
  7 neg. vs #1 5DCnA57 (91%, 1.18×, 0.664, 6 neg), king (85%, 1.64×, 0.605, 9 neg). Easy 1.066 ≈ #1, BEATS king. Gap = MEDIUM+HARD,
  NOT Easy → and it's **BREAKS from OVER-COMPRESSION**: m26's 2 worst losses are tasks 315 (BREAK @2.43×) + 297 (BREAK @2.86×), its
  2 HARDEST-compressed tasks; #1 (light 1.18×) didn't break them. Net gap to #1 = −3.99/45, those 2 breaks = −4.33 → fix → PASS #1.
- ★ **NEXT SHOT np2 = upload_miner_np2.py BUILT** (np1 + NP_RESULT_CAP 6000→16000 = LIGHTER → keep big results fuller → fewer
  breaks; targets ~1.3×, toward #1's 1.18×, above 5HdTr7's 1.07× inflate-trap). Offline-validated (cache-stable 99.9%/idempotent/
  ≤native/compliant — mechanism identical to np1). Cap is the platform-calibration knob. NEXT: Codex pre-upload audit → USER uploads →
  platform calibrates. **UPDATE: Codex audit DONE (SAFE, only the cap changed; lighter = empirical calibration bet). Ratio pre-check
  (scripts/ratio_compare.py): np2 = CLEAN near-passthrough — cap 16k passes results ≤16k (ratio 1.0×, NO inflation, guard holds),
  compresses only >16k; KEEPS the break-task results (315/297 ~16-18k) ~full → should FIX m26's 2 over-compression breaks; BUT
  near-passthrough on typical tasks → forgoes savings (under-compression-penalty risk, platform-only). KEY: flat-cap is BINARY (cant
  hit 5DCnA57's uniform-light 1.18× — that needs cache-stable LOSSLESS DEDUP = the real np3 lever).** UPLOADED as np2 (5CPbtf3sUKrpGikpCuDVvMrpTe4VpPWMXNX5sFeTXHDSY7QS, np2sub).
  **★★★ np2 SCORED #2 of 64: total 0.684 (E1.052/M0.849/H0.173) — and WINS Pair(E,M) 0.951 + Single-M 0.849 = 14.3% OF THE POOL.**
  From m12 cratered/0% → np2 14.3% (Pair(E,M)+Single-M). Thesis CONFIRMED: lighter cap → Medium 0.620→0.849 (+0.229, recovered the
  over-compression breaks), Easy held (~tied #1), NO under-compression penalty (total rose). Share: 5DCnA57 71.4% / np2 14.3% / king 9.5% / 5DtEz 4.8%.
  np2 is now OUR LIVE BEST (m26/np1 → #4 0.610). np2 dissect: cache 93%, ratio 1.49×, 11 neg (more wander/inflation than m26 + the
  VERY biggest Hard tasks 315@2.57×/296@3.27× still over-compressed). **GAP to grow = HARD** (np2 H0.173 caps Overall 57% gap-0.019,
  Pair(E,H), Pair(M,H)); + near-free Single-E (np2 1.052 vs 5DCnA57 1.067, −0.015, may flip on re-draw). DEFEND 14.3% (keep np2 live;
  watch for higher-E+M rival).
- ★ **np3 BUILT + Codex-GO, READY TO UPLOAD (upload_miner_np3.py, sha 420de1cc; reports/cache_stable_design.md §14).** DIAGNOSIS
  (repetition analysis of 6 comp-108 trajs): np2's Hard breaks are NOT from repeats (exact-dup ~10%, DEDUP WEAK) but from big
  UNIQUE blocks (24k-64k; 4/6 tasks >16k) that np2's 16k cap shreds → Hard breaks. FIX = keep big blocks fuller. np3 = np2 +
  NP_RESULT_CAP 16k→28k (keeps 24k blocks FULL, 56-64k to 28k). Codex audit GO (agent aabdb48e): integrity CONFIRM (only the cap;
  rewriter-bug-free; Codex re-ran harnesses: 99.8% prefix-stable, 0 orphans, idempotent, ≤native), invariants CONFIRM, strategy
  CONFIRM-the-bet-with-real-risk. **ADDITIVE BET — np2 stays LIVE holding 14.3%; np3 can only gain Overall (57%), never lose income.**
  RISKS (platform-only): more near-passthrough → wander could drop E/M; some Hard may be agent-side (lighter won't help); if a big
  block is mostly PINNED error/traceback lines the cap won't engage → np3==np2 → Hard flat + E/M wander for nothing. CONTINGENCIES:
  E/M erodes → tune cap to 24k; Hard flat → agent-side → np4 = better extractive on the 56-64k blocks. USER uploads to a SEPARATE
  hotkey (same OpenRouter acct), read at status=scored. m12 (5Dz7) LIVE/untouched; np2 (5CPbtf) LIVE = our 14.3%.**
- CAVEAT: re-scoring may still be settling across all 104 miners; the RELATIVE picture (cache-stable on top, m12 near bottom) is STRUCTURAL and locked regardless of exact final numbers. Need fresh data with BASELINE split tokens (detail page now exposes them) to recompute exact new scores.

## ★★ BOARD CHANGE 2026-06-26 ~08:34 (snap 083352, 103 miners) — SINGLE-E BAR JUMPED to 1.197; our Single-E play likely DEAD [RAW-TOKEN ERA — see regime change above; now OBSOLETE]

## ★★ BOARD CHANGE 2026-06-26 ~08:34 (snap 083352, 103 miners) — SINGLE-E BAR JUMPED to 1.197; our Single-E play likely DEAD
- **5GBPFAAeKQ (NEW) SCORED clean Easy specialist: E1.197 / M0.604 / H0.612 / tot0.797** (mean checks: (1.197+.604+.612)/3=0.80 ✓, no
  hidden penalty). It is the m26 ARCHETYPE built BETTER than us — maxed Easy, cratered M/H to ~0.6. **Legit Single-E winner now = 1.197**
  (the 1.259 above it is the failed-review cheater 5CaFqLaP). Our best Easy ever = m25 0.859 → now **+0.338 short** (was +0.064 vs old bar 0.923).
- **5H4JafmQpK (evaluating): E0.950 / M1.330 / H0.101** — a high-E+high-M miner; if it scores its Pair(E,M)≈1.14 > king 1.07 → may take Pair(E,M). WATCH.
- **IMPLICATION:** the Single-E lane is now contested by specialists we likely CANNOT out-build (m25 perturbation maxed at 0.859; 5GBPFA is 1.197
  by an unknown stronger Easy mechanism). The two-singles ~9.52% plan is in JEOPARDY — Single-E may now be as out-of-reach as Overall/Medium.
  Reachable set shrinks back toward HOLD Single-H (m12 0.919, still field-best Hard). m26 build does NOT clear the measurability gate (can't
  predict +0.34). DESIGN NOTE (for any Easy specialist): do NOT try to "keep Medium" on it — portfolio takes MAX per element so m12 holds our
  Medium(0.953)/Hard(0.919); keeping Medium on the Easy miner only steals its Easy budget. 5GBPFA proves Easy+Medium can't coexist (E1.197 but M0.604).

## ★★ WHOLE-ARCHITECTURE DEEP-DIVE done (2026-06-26, user reframe "leave m12") — ceiling UNCHANGED ~9.52%. (report: whole_architecture_deepdive.md; Claude+Codex reconciled)
User asked: stop anchoring on m12, is the architecture itself the ceiling? Re-derived from raw per-run JSON (matches board 3dp).
- **The reframe was RIGHT that we anchored wrong:** m12 is the HARD VERTEX (field-best H0.919); stop improving it, ADD specialists.
  Corrected the record: **flips are TIED** (m12 16 ≈ king 17, 6 shared tasks — NO m12 flip edge; the old "m12 out-flips king" was
  overgeneralized from dj-14017). Gap to king = 100% breaks, re-confirmed (m12 17 / king 6); breaks sit on HIGH-VARIANCE tasks
  (m12 already passes 7/10 break-tasks at 3-4/5) the king converts to 5/5, at NO consistent token strategy (ratio 0.45–1.72×).
- **The reframe did NOT unlock a new reliable element.** Pair(E,H) LOOKED reopened: 5DtEz proves E0.837+H0.813 coexist (pair
  0.825=9.5%), and the old m24 NO-GO used the WRONG constraint (it required preserving m12's H0.919; Pair(E,H) only needs the
  pair>0.825, works at H0.813). BUT both models ruled **Pair(E,H) as a deliberate TARGET = NO-GO:** 5DtEz is the SAME perturbation
  tradeoff as m25 (kills flips, makes new breaks) — its damage just landed on MEDIUM (M0.499) sparing Hard, while m25's landed on
  HARD (0.536). We CANNOT steer which category the damage hits (W-NS), CANNOT validate offline (no comp-108 E/M/H map exists for
  267-316), and our one real attempt (m25) put damage on HARD. "One observed outcome ≠ replicable mechanism" (Codex). It is m27 again.
- **Frontier claim CORRECTED (Codex refuted my overclaim):** NOT "nobody is good at all 3" — the king IS balanced (E0.858∧M1.281∧
  H0.727, all ≥0.7). The defensible statement: **no observed miner pairs king-level E/M with m12-level Hard (0.919);** pushing E/M
  to king-level forces H to ~0.727. For US it's moot (our Easy lever craters our Hard) → Overall unreachable FOR US, not provably
  for everyone. Bigger elements (Overall 57%, pairs) need the king's consistency mech (unreachable/banned) or category-steered damage.
- **NET: reachable ceiling unchanged = ~9.52%** (m12 Single-H + m26 Single-E; Pair(E,H) only a free lottery upside of the m26 build,
  never a target). The m26 Single-E decision below stands as the one open growth move. m12 LIVE/untouched throughout; nothing built.

## ★★ m25 SCORED + m27 NO-GO → the reachable growth = a SINGLE-E specialist (m26). DECISION PENDING.
**m25 (5GpB36, platform label "m23", upload_miner_m25.py) SCORED: E0.859 / M0.667 / H0.536 / tot0.684 — ZERO penalty (clean).**
- FAILED as an m12 replacement (Hard 0.536 << 0.919, gate failed). m12 stays LIVE.
- ★ **But Easy 0.412→0.859 (+0.447) = #2 in the FIELD** (behind only 5GCWaCnb 0.923, ABOVE the king 0.858). On the portfolio,
  **m25 is #2 on Single-E (+0.064 to win)** — the closest we've ever been to a 2nd reward element.
- **m25 MECHANISM (dual-agent verified):** the extractive (blind→signals) swap is a high-variance content PERTURBATION:
  Easy gain = ~86% pass-pass BOOST (perturbation, +6.09 of +7.05) + ~14% ratio + a little break-fix; it is STRICTLY anti-flip
  (gained 0 new flips, KILLED 3) and DESTABILIZES passing tasks (−10.6 over 18) → THAT is why M/H cratered (the "opposite result").
- **m27 (Easy+Hard DUAL-MODE specialist, Pair(E,H)) = NO-GO** (Claude + Codex, reports/m27_eh_specialist.md). The
  settled-vs-exploration router CANNOT separate where the perturbation helps from where it hurts — Codex measured: help-fires
  and hurt-fires have IDENTICAL per-turn signal distributions (depth/tokens/ratio/still_failing all overlap). Hard protection
  unachievable (router producing Easy = router perturbing Hard, shared fires; H stays ≈0.536). NO file built.
- ★ **REACHABLE PLAY (the path, NOT yet built — user decision): TWO SINGLES.** Pair(E,H) needs ONE balanced miner = impossible
  with this mechanism. Instead: m12 keeps Single-H, + an **EASY-ONLY specialist (m26)** that ABANDONS Hard entirely (no dual-mode,
  nothing to protect) and pushes Easy 0.859→>0.923 to win Single-E → m12+m26 = 2 elements → **4.76%→~9.52% (double).** ~+0.064 gap,
  field-demonstrated reachable (5GCWaCnb=0.923). HONEST risks: the +6.09 boost is perturbation (passthrough loses it → E may dip
  <0.84) + savings-gate on a passthrough-heavy specialist. So m26 design is non-trivial — would go through the dual-agent protocol
  (Claude design+offline-validate, Codex audit, separate hotkey) before any upload.
- CAVEAT: confirm m25's key was SAME OpenRouter acct as m12 (zero penalty + Easy 0.859 imply a good backend, so likely fine).
  Also flagged: a PROVIDER-ROUTING lever (block weak OpenRouter backends e.g. AtlasCloud) could lift CONSISTENCY (m14 proved
  backend swings score ~0.35); evidence-driven + keep redundancy; pays only on re-eval. NOT acted on.

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
