# CURRENT — live status (2026-07-07) — READ FIRST after compaction

## ★★★ 2026-07-07 — comp-110 (CoT-Compression-5) intel + payout CONFIRMED + scraper FIXED. ⚠️ The new comp's platform id is **110**, not 109.
**Sources: Discord (raw: `data/raw/discord_notes/2026-07-06_comp109_round5_announcement.md`), upstream DendriteHQ/SOMA@main (fetched as `upstream` remote), live dashboard RSC flight.**
- **✅ comp-108 payout CONFIRMED by owner oli (Discord ~2:25 PM):** `5DAbJik` (cap32+pin) → **0.5714** + `5F9ZRe` (np3) → **0.0952** = **66.7% of the pool, exactly as projected.** oli: "winners - please make sure your hotkey is registered." DQ reason (Matt): hidden injection about not writing tests + word-replacement string modification.
- **comp-110 = CoT-Compression-5** (dashboard flight: `competition_id: 110`, type **"compression"** not "swe", state `upload`). Uploads 06 Jul 14:30 → **13 Jul 14:30 UTC**, eval → 20 Jul. 4 subs in queue as of 03:40Z 07 Jul. Fresh board.
- **⚠️ REGIME CHANGES (Discord announcement — bigger than assumed):** new agent as base, **new model = DeepSeek V4 Pro via the DeepSeek provider on OpenRouter**, new scoring, **NEW TASK TYPE: code search** (swe-explorer: locate the correct file + lines). **E/M/H layers REPLACED by per-task-type layers** (3 types × 50 tasks × 5 runs = 750 runs). Tasks may be **HIDDEN** this round (anti-overfit; from SWE-bench verified). Baseline costs to be shared ~07 Jul.
- **⚠️ MANDATORY miner setup (USER action before upload):** OpenRouter Settings → Privacy → enable BOTH Data Collection options; Settings → Guardrails → Workspace → enable the DeepSeek provider. Without this the gateway's DeepSeek routing won't work for our runs.
- **NEW SCORING DECODED from upstream code (`mcp_platform/app/api/routes/scoring.py`, commit 4f04bb2):** explore-task score = `gate × tau` where gate = smoothstep of quality margin (quality = hit_file_rate − noise_file_rate vs baseline; margin ≤ −0.20 → floor **−2**) and **tau = clamp(2·log2(baseline_weighted/miner_weighted), ±2)**. ⇒ **PASSTHROUGH SCORES 0 ON EXPLORE TASKS** (no savings → tau=0): compression is REQUIRED to score on the new layer — the comp-108 "sit at the compliant frontier with near-passthrough" play does NOT transfer to the explore layer. Miner explore total = avg per-task blended toward −2 by total savings (smoothstep saturating at ±20%). swebench flip is +2 (was +4); weighted tokens (1.0 input / ⅓ cached / 3.0 output) now in docs/miner/scoring.md. Incentive layers are now built from **arbitrary category lists** (`build_incentive_layers`) = the task-type layers.
- **✅ Gate #1 (rules) PASSED:** live `miner/README_prompting.md` (upstream@main) is UNCHANGED for round 5 (oli: no issue/PR before uploads → frozen; one late PR pending owner review ~07 Jul). Champion file `miner/cot_compression/upload_miner_uphard_salience.py` sha256 **695b4fe4… EXACT match**, parses, and every emitted string ⊆ the allowed set (§5.1/§5.2).
- **✅ Scraper FIXED (was broken on the rebuilt JS dashboard):** `collect_dashboard.py` now parses the RSC flight (`sweMiners` for swe comps / `miners` for compression comps + `competitions` metadata), supports `--comp NNN` archives, legacy fallback kept. Verified live: comp-110 = 4 in-queue; `--comp 108` archive = 324 miners / 204 scored / 36 failed-review, top scored = 5DAbJik 0.7228 ✅. `config/dashboard.yaml` → competition_id 110.
- **⚠️ MISSING TOOLS on this machine/branch:** `scripts/check_readme_current.py`, `scripts/vet_draw.py`, `scripts/watch_comp_status.py` are referenced throughout state/ but were never committed to ops-snapshot (they lived untracked on the comp-108 machine). Rebuild before relying on them.
- **STRATEGIC READ (not yet decided):** cap32+pin (695b4fe4) is compliance-proven but its tuning (16k/28k/32k caps, salience pin) was optimized for the OLD agent/model/tasks; the explore layer changes the game (savings×quality, passthrough=0). Defense likely = re-submit the proven base early + build an explore-aware candidate behind the standing gates. USER decides uploads.

## 🏆🏆 2026-07-06 — WON comp-108 (CoT-Compression-4). cap32+pin = CHAMPION. Confirmed on the platform (browse, archive `?comp=108`).
**comp-108 ENDED. Our `cap32+pin` (5DAbJik) = platform-labeled "Highest score in this competition" / dashboard "Top score 0.723" = the WINNER (Overall crown).**
- Final board (via /browse, dashboard archive): **cap32+pin Overall 0.723 (E1.044/H0.281/M0.862), status=scored, ⭐ top score.** ALL 23 miners with a higher raw Overall = **failed review** (every beyond-ceiling cheater DQ'd: 5CaFqLa 1.443, 5CcZeD 0.977, 5FWZGczz 0.888, 5EeUAVZ 0.852, 5GpLcd 0.825, 5Fjms 0.758, 5DZLFZj 0.728, +others). 204 scored / 36 failed-review / 83 not-qualified.
- **Our reward elements (computed from the final scored rows):** **Overall (57.1%) = cap32+pin (CROWN)** + **Pair(M,H) (9.5%) = np3 0.599** ⇒ **~66.6% of the pool.** Specialist corners went to clean rivals: Single-M + Pair(E,M) → 5DMC61SU (M0.954), Single-E → 5D22vwFM/5GvYDY7h (E~1.15), Single-H + Pair(E,H) → 5F4g41c5 (H0.718). (Overall crown is platform-CONFIRMED; element split is my calc from the board — scraper can't parse the new JS page.)
- **THE STRATEGY WORKED:** build a fully-compliant miner (cap32+pin, verified 3× vs README + the explicit rules), hold the floor, let review enforcement clear the cheaters. cap32+pin sat at the compliant frontier (~0.73) the whole time; everyone above it was beyond-ceiling and got DQ'd. Compliance rigor = the win.
- **NEXT: comp-109 (CoT-Compression-5) is now LIVE** — uploads 06 Jul 14:30 → **13 Jul 14:30 UTC**, eval → 20 Jul. Fresh board (0 subs). Prize pool ~41,328 dTAO. If we defend the title, cap32+pin (695b4fe4) is the proven compliant base to re-submit. ⚠️ TOOLING: the dashboard changed (JS-loaded, archive via `?comp=108` URL param) → `collect_dashboard.py`/`collect_runs.py` need updating for the new page before they'll scrape comp-109.
- **WALLET OPS in progress (user-run):** unstake-all + transfer — commands in `reports/wallet_ops.md`. `btcli stake remove --wallet-name tony-miner --all-hotkeys --unstake-all --safe --tolerance 0.05 --partial` then `btcli wallet transfer --wallet-name tony-miner --dest <SS58> --amount <TAO>`. tony-miner coldkey has NO seed backup (recover_seed.py / swap-coldkey Plan B).


_Mode: comp 108 (CoT-Compression-4, SN114). ⚠️ SCORING REGIME CHANGED 2026-06-26 — see top section. Dual-agent
(Claude+Codex) protocol OPERATIONAL (see CLAUDE.md). Files = source of truth. Read this + NEXT_ACTIONS + DISCOVERIES (top) before acting._

## ★★★ 2026-07-03 ~19:50Z — ⚠️⚠️ CORRECTION: cap32+pin SCORED **STRONG** (I'd misread it at `evaluating`). New-king DQ now worth **81%**, not 23.8%.
**READ-FIRST — supersedes the 18:00Z "cap32+pin FAILED" claim below (that was the 5DAh trap: I read E1.015/M0.585/H0.116 while it was `eval=evaluating`; final scored numbers are much better).**
- **cap32+pin (5DAbJik) FINAL scored: total 0.7228, E1.044 / M0.862 / H0.281.** vet_draw = **CLEAN** (cache 90.9%, break 11.2%, 0 timeouts) → trustworthy, not a confounded draw. **It BEATS np2 (0.684) AND np3 (0.682) on total** — our best miner. The combined-Overall thesis WORKED (contra my earlier "refuted"): the pin held Medium (0.862 ≈ np2 0.849, slightly better) AND fuller-keep lifted Hard (0.281 > np2 0.173). **Overall-element (mean) = 0.729.**
- **THE STAKES ARE NOW HUGE.** AS-IS (new king 5GpLcd 0.831 stands): **0%** (king sweeps). But **IF the new king is DQ'd → OUR SHARE = 81.0%**: cap32+pin takes **Overall (57.1%) + Pair(E,M) 0.953 (9.5%) + Single-M 0.862 (4.8%)**, np3 keeps **Pair(M,H) (9.5%)**. cap32+pin's 0.729 Overall-element beats the next-eligible 5DCnA57 (0.703). ⇒ the new-king compliance review is now worth **81% to us**, not 23.8%.
- **PROTECT cap32+pin (5DAbJik)** — it's now the Overall-crown asset; do NOT disturb/re-eval it (0.729 is a clean but single draw; re-eval could redraw lower). Same for np2/np3.
- **All 3 pinned shots now SCORED: cap32+pin 0.729 (E1.044/M0.862/H0.281) is our BEST.** np3+pin (5E4Y4jz) = 0.639 (E0.769/M0.798/H0.350 — got np3-like Hard 0.35 but Easy cratered 0.769); np2+pin (5FLUziw) = 0.521 (E0.766/M0.642/H0.155). The np3+pin/np2+pin Easy-craters (~0.77 vs np2's 1.05) look like BAD DRAWS (the pin doesn't touch passthrough Easy) — vet_draw them if it matters, but both are BELOW cap32+pin so they don't change our element position (cap32+pin leads Overall/Pair(E,M)/Single-M; np3 leads Pair(M,H)).
- **COMPLIANT FRONTIER ≈ 0.76 Overall** (best-combinable per-category: E~1.05/M~0.86/H~0.37 → mean 0.76). cap32+pin (0.729) is AT it; our whole build history never crossed it. The E↔H tradeoff (compress-hard-for-savings vs keep-context-for-flips) is the frontier — you get high (E,M) OR high H, not all three. The cheaters (0.83–0.99) sit ABOVE this frontier = the quantitative definition of beyond-ceiling. So cap32+pin had ~zero compliant headroom left; and the cheater scores are not compliantly reachable (the combination breaks the tradeoff; individual numbers are formula-legal but the simultaneity isn't).
- **New king suspicion unchanged:** its signature (2.70x/79% cache) does NOT match the DQ'd `#source line N` pattern (1.33x/93.6%) → weaker "matches banned pattern" case; can't verify from outside. But given 81% rides on it, an honest review-request to the SOMA team is well worth it.

## ★★★ 2026-07-03 ~18:00Z — [CORRECTED by 19:50Z above — cap32+pin did NOT fail; I misread it at `evaluating`] NEW KING 5GpLcd 0.825 → our share 0% AGAIN. Compliance suspicion this time is WEAKER (signature differs).
**READ-FIRST.** New scored miner **`5GpLcdxSNZgDg…` = 0.825 (E1.115/M0.943/H0.434)** takes Overall+Pair(E,M)+Pair(E,H)+Pair(M,H)+Single-M = **OUR SHARE 0%** (same crater as the DQ'd 5EeUAVZ). **IF it's DQ'd → back to 23.8%** (np2 Pair(E,M)+Single-M, np3 Pair(M,H)); floor is on separate live hotkeys, untouched.
- **USER suspects an unapproved prompt edit (like the 2 prior DQ'd kings). HONEST ASSESSMENT: the signature does NOT match the `#source line N` pattern.** New king = **2.70x compression / 79.1% cache / 38% flip / 10% break**. The DQ'd 5EeUAVZ = **1.33x / 93.6% cache / 40% flip / 2% break** (light-passthrough + annotation). The new king is the OPPOSITE — a HARD compressor with LOWER cache. So it's either (a) a genuinely strong compressor, or (b) a DIFFERENT edit — **can't tell from outside (source_code_available=False; no access to its emitted output/markers)**. Its across-the-board strength (high E AND M AND H at once, esp. 38% flips at 2.70x) is notable/worth a review request, but the "matches the banned pattern" evidence is WEAK this time. Only the SOMA team (code access) can rule. PLAY: flag for review honestly (request, not accusation), HOLD, track for DQ (watcher repointed to 5GpLcd).
- ~~cap32+pin SCORED = FAILED (M0.585/H0.116)~~ **WRONG — those were `evaluating` (partial) numbers. See 19:50Z correction above: cap32+pin scored 0.7228 (E1.044/M0.862/H0.281), CLEAN, beats np2/np3, Overall-element 0.729 → the combined-Overall thesis WORKED. This "FAILED" bullet is retained only as the record of my 5DAh-trap error (read at `evaluating`, not `scored`).**

## ★★★ 2026-07-01 ~21:15Z — FRESH-EYES REVIEW of the submission (Fable 5 pass): shots well-aimed + verified, BUT ⚠️ Single-M margin = **0.0015** and 118 miners still in queue.
**Re-verified everything load-bearing with fresh board data (snap 2026-07-01/210625, 324 miners / 125 eligible):**
- ✅ **Floor intact 23.8%** (np2 Pair(E,M) 0.951 + Single-M 0.849; np3 Pair(M,H) 0.599) — BUT margins now: **Single-M +0.0015** over 5GgqHgSd's M=0.848 (RAZOR-THIN ⚠️), Pair(M,H) +0.044, Pair(E,M) +0.058. **118 in queue** → the floor is EXPOSED to every new scoring, esp. Single-M. ⇒ **np2+pin is now also a DEFENSIVE asset:** if the pin adds even +0.002 M it re-secures Single-M on a 2nd hotkey.
- ✅ **The 3 shots are well-aimed at a SMALL gap:** Overall leader 5DCnA57 0.703; **np2 is ALREADY #2 at 0.691, np3 #3 at 0.685** — a +0.012 mean lift takes the 57% crown. Shots still `in queue`.
- ✅ **Fresh verification passed:** (1) **base-file identity PROVEN** — on-disk np2.py sha256 a64231c9 == registry live-np2sub, np3.py 420de1cc == live-np3sub ⇒ np2_pin/np3_pin truly = LIVE base + only-the-pin; (2) **compliance scanner PASS on all 3**; (3) Codex GO ×2 audits; (4) watcher live + tracking.
- ❌ **CORRECTED MY OWN 06-30 ERROR:** the "documented shas are STALE" claim was **hash-algo confusion** — 695b4fe4/b60c7d68 are **sha256** and were always correct (I'd compared SHA-1/git-hash). Files never drifted. Registry/state fixed; final-set sha256s recorded (salience 695b4fe4 / np3_pin 489f4e3c / np2_pin 54443001).
- ⚠️ **Honest residual risks (unchanged, restated):** (a) cap32+pin keeps up to 2× np2 on 26.7–53k **Medium** reads — nocap's "more bulk→mis-navigate" break mechanism is BOUNDED but not eliminated by the pin → its M could land < 0.849; (b) the pin's **solve-level benefit is UNPROVEN** — the only "salience edges np2" evidence was local eval (later proven to never exercise compression); valid support = the offline function test only (keeps 30/30 imports); the pin changes KEPT-LINE COMPOSITION, which can cut either way; (c) pin over-matches prose lines starting with `raise`/`@` (composition-only, minor).
- 📌 **HYGIENE:** the 3 uploaded files are UNTRACKED in git → not byte-recoverable if edited in place (the uphard lesson). RECOMMEND: commit them (user-approved).

## ★★★ 2026-06-30 ~18:25Z — ✅ DQ LANDED: both kings FAILED-REVIEW → 23.8% is REAL (not projected). 3 final shots UPLOADED + queued + watcher-tracked.
**READ-FIRST.** Platform APPLIED the DQ: **5EeUAVZ AND 5DZLFZj both now `review=failed review`** on the board (watcher caught the `scored→failed review` transition at 12:08Z → `state/comp_watch.md`). `make reward` (snap 182510, failed-review excluded) CONFIRMS **OUR SHARE = 23.8% REAL**: np2 (5CPbtf) wins **Pair(E,M) 0.951 + Single-M 0.849** (14.3%); np3 (5F9ZRe) wins **Pair(M,H) 0.599** (9.5%). Field: 5DCnA57 Overall 57.1%, 5GgVXz 14.3%, 5EKyJnby 4.8%.
- **3 FINAL SHOTS UPLOADED (USER) — all `in queue`, watcher now tracking for scored-transition:** cap32+pin `5DAbJikTa2…` (uphardsaliencesub) · np3+pin `5E4Y4jzYKY…` (np3pinsub) · np2+pin `5FLUziw5Cp…` (np2pinsub). All Codex-GO, on OWN hotkeys → CANNOT hurt the 23.8% floor. **READ ONLY at scored:** `vet_draw.py --hotkey HK` → E/M/H vs np2/np3 + **Overall vs 0.703** (5DCnA57). Watcher (`com.soma.compwatch`, 30 min) writes `state/comp_watch.md` + macOS notify when any hits scored OR fails review.
- **DEFEND:** do NOT disturb np2/np3/m26 — the 23.8% rests on them. The 3 queued shots can only ADD (best = cap32+pin if its Hard lands ~0.37 → Overall ~0.74-0.76 > 0.703). Honest EV: each needs an unproven pin-lift; 23.8% is the secured floor.

## ★★★ 2026-06-30 ~18:00Z — CLAUDE+CODEX RECONCILED on the final 3 shots: cap64/nocap CAN'T win Overall; cap32+pin is the only viable probe; defending 23.8% is high-EV.
**READ-FIRST for the upload decision.** Codex strategic red-team (agent afbedc22) + Claude AGREE (high confidence — independently, from the platform JSON):
- **cap64+pin and nocap+pin are FUTILE for Overall.** Best-case math (even if the import-pin FULLY fixes Medium to np2's 0.849): nocap+pin = mean(E0.984, M0.849, **H0.032**) = **0.622 < 0.703 target.** Because **H is cratered and the pin fixes Medium (breaks) NOT Hard (flips)** — no source mechanism by which pinning imports raises baseline-FAIL flip rate; nocap even flipped FEWER than np2 (4 vs 5). **cap64 ≈ nocap** (diverges only on results >107k chars) → same fate, low-information duplicate.
- **cap32+pin = the ONE defensible Overall probe.** 32k keeps big Hard results in np3's H-peak zone (np3@28k→H0.369); IF its H lands ~0.37 AND the pin holds M, best-case mean(≈1.0, ≈0.85, ≈0.37) ≈ **0.74–0.76 > 0.703.** UNPROVEN (no cap32+pin platform data; cap32 is proportional vs np3 flat → H could land below 0.37). Realistic ~0.70–0.74, straddles the target.
- **H-peak CONFIRMED:** 16k→0.173, 28k→**0.369** (peak), uncapped→0.032 (crater). Looser-than-~28-32k craters the Hard we need. (Caveat both noted: np2/np3 flat vs nocap proportional = imperfect comparison, but cap64/nocap are still looser than the peak.)
- **HONEST EV (Codex, MEDIUM conf; Claude concurs):** even the grounded alternatives (np2+pin on 0.691, np3+pin on 0.685) need a **+0.018 lift with no proven mechanism** → **defending the 23.8% floor is the higher-EV call.** Our compliant H ceiling is ~np3's 0.369 (king's H0.535 was the unapproved annotation; 5GgVXz's 0.676 is unreplicable).
- **RECONCILED RECOMMENDATION:** Shot1 = UPLOAD **cap32+pin** (only viable probe, can't hurt floor). Shots2-3 = SKIP cap64/nocap (Overall-futile); swap to **np3+pin** (proven H0.369 + pin lifts weak E/M) + **np2+pin** (proven 0.691 + pin) IF chasing Overall, ELSE **defend 23.8%**. Compliance of all 3 planned files: CONFIRMED mechanically clean. **USER DECIDES** (the floor is safe either way).
- **→ RESOLVED 2026-06-30 ~18:15Z: USER chose Option A (3 grounded shots). FINAL SET BUILT + ALL CODEX-GO, LOCKED, upload-ready:** Shot1 **cap32+pin** (`upload_miner_uphard_salience.py`, git 57e325c7, Codex-GO 1st audit) · Shot2 **np3+pin** (`upload_miner_np3_pin.py`, 5ecc8e9e = live np3 flat-28k + the EXACT salience pin) · Shot3 **np2+pin** (`upload_miner_np2_pin.py`, 24352456 = live np2 flat-16k + the pin). Codex audit (agent acff00df, verdict pulled from rollout): **np2_pin=GO, np3_pin=GO, 0 blocking** — diff-vs-base = ONLY the pin; `_STRUCT_PATTERN` byte-identical (SHA-256 e925483d) across all 3; COMPLIANCE/CACHE/BOUND/INTERACTION all PASS (caps unchanged 16k/28k, idempotent early-return intact, pin independent of cap math). Registered np3pinsub/np2pinsub; cap64+pin & nocap+pin DEPRECATED-for-Overall. **NEXT: USER assigns 1 clean DeepInfra+Venice hotkey per shot → give them to me → run check_readme_current.py → upload → vet_draw.py + E/M/H + Overall vs 0.703 at scored.** Honest EV unchanged: all need an unproven pin-lift; 23.8% floor is the EV-floor and is untouched.

## ★★★ 2026-06-30 ~11:55Z — ✅ OWNER RULE: BOTH KINGS (5EeUAVZ + 5DZLFZj) FAIL REVIEW → we PROJECT to **23.8%**. nocap FAILED (predicted). Prompt list FROZEN.
**READ-FIRST — best-case branch landed.** Owner oli|SOMA (Discord ~11:5xZ): *"the current TOP TWO submissions use a prompt that was not approved… cannot pass the review process."* = BOTH `5EeUAVZ` (0.852) AND old king `5DZLFZj` (0.728) DQ'd (both used `#source line N`). NEW RULE: the approved prompt-string list is **FROZEN once a comp starts** — no new prompts/mods accepted mid-comp.
- **PROJECTED standing once the DQ is applied (category-mean proxy, both excluded): OUR SHARE = 23.8%** (was 0% under the king; was 14.3% pre-king). np2 RECLAIMS **Pair(E,M) 0.951 + Single(M) 0.849** (=14.3%); np3 keeps **Pair(M,H) 0.599** (=9.5%). Others: Overall(57%)→5DCnA57 0.703, Pair(E,H)+Single(H)→5GgVXz, Single(E)→5EKyJnby 1.079. ⚠️ **NOT YET APPLIED** — both kings still show `review=scored` on the board; the 23.8% materializes when the platform marks them failed-review. The watcher now tracks BOTH for that transition.
- **nocap (`5FXAR4pqoo…`) = 0.416 = CONFIRMED FAILURE = the predicted uncapped-tail crater.** E0.984 (good, light-keep preserves Easy) but **M0.266 CRATERED via 17% breaks** (django-12039 −2.389, django-12774 −2.204, sympy-23262 −1.906). Fuller-keep INCREASED breaks (17% vs np2 ~10%) → refutes "keep more → fewer breaks" on the real arbiter. **DISCARD** (separate hotkey, untouched). Validates the ranking **salience/cap32 > nocap**; cap32's 32k cap would have avoided the crater.
- **FROZEN-PROMPT RULE kills the mid-comp marker branches:** `#source line N` will NOT be approved this comp; Karim's omit-marker won't land this comp → `uphard_omitcount` stays DORMANT (dead for THIS comp); the line-number-annotation candidate idea = DEAD for this comp. `check_readme_current`'s new-marker watch = moot this comp (still useful for the NEXT comp). Proposed future flow: PR → team thread → README update (pre-comp only).
- **PLAY: HOLD + DEFEND.** Don't disturb np2/np3/m26 — the projected 23.8% rests entirely on them. Watch for the DQ to land, then `make reward` to confirm. Local-eval-can't-test-compression (09:55Z) still stands → no more local compressor A/Bs.

## ★★★ 2026-06-30 ~09:55Z — ⚠️ LOCAL EVAL DOES NOT EXERCISE OUR COMPRESSION → all local compressor A/Bs this session are NOISE. PLATFORM-ONLY.
**READ-FIRST for anyone tempted to trust a local A/B.** The missed-flip A/B (`bvtw2f6jp`, 35/36 completed) returned flip rates np2 50% / cap32 33% / salience 45% — **but these are NOISE, the A/B is INVALID.** Proof: across ALL 36 solves (3 tasks × 3 profiles × 4 runs), **ZERO `[[CMP]]` markers reach the LLM trajectory** (our compressors ALWAYS emit `[[CMP]]` when they compress); the three profiles produce near-identical trajectories (within ~2–11%); a 67k-char `read` toolResult (well over the 16k floor) is reduced to ≤15k **without our markers** → the local OpenClaw harness does its OWN context truncation, PRE-EMPTING our compressor. (The "348 [[CMP]]" earlier = the marker string in 36 copies of `baked_base_miner.py` source, not output.)
- **IMPLICATION: local eval can't compare compressors** (the agent truncates context before our cap_tool_result sees a >16k single result). EVERY local compressor A/B this session — missed-flip, "worst-common salience edges np2", the cap32/nocap flip reads — is UNRELIABLE for the same reason. This EXPLAINS local's chronic unreliability. **The PLATFORM is the ONLY valid arbiter for np2 vs np3 vs nocap vs cap32 vs salience — full stop.**
- **So: we genuinely CANNOT rank nocap/cap32/salience locally.** nocap is ON the platform now → that's the only real test. cap32/salience are NOT uploaded → unknown until platform-tested. Don't spend more on local compressor A/Bs.
- (Local eval still validly tests: does a solve run e2e / crash / time out — i.e., pipeline health. It does NOT test compression behavior.)

## ★★★ 2026-06-30 ~08:35Z — KING 5EeUAVZ UNDER COMPLIANCE REVIEW (unapproved `#source line N`) → likely DQ → floor likely RESTORED. **HOLD.**
**READ-FIRST — reframes the "0% / king dominant" 08:05Z section below.** Discord, owner **Matt|SOMA ~04:15Z**: the king `5EeUAVZ` (Thomas_Colden's) **used `#source line N`** — a prompt edit discussed on-channel but **NOT approved**. Verbatim: *"not approved yet… not strictly following rules… upload+scoring got done before any approval… applies only to current 1st place miner… team still discussing what to do."* Owners also said it *"doesn't look like exploit by design"* (so not malicious, but rule-breaking).
- **IMPLICATION: the king's 0.852 / 90.5% may be INVALIDATED.** If `5EeUAVZ` is failed-review/DQ'd → excluded from rewards → **np2 reclaims Single-M + np3 reclaims Pair(M,H) → floor back to 14.3%** (np2/np3 still scored+LIVE, so reclaim is automatic — nothing to rebuild).
- **ITS EDGE WAS LIKELY THE ANNOTATION, NOT "lighter compression."** `#source line N` = informative line-number provenance on each kept chunk → agent edits the right lines (fewer breaks) + sees structure (more flips). Explains 40% vs 30% flips at IDENTICAL savings/cache (08:05Z). **WE CANNOT COPY IT** (unapproved). ⇒ do NOT panic-rebuild to chase the king's recipe.
- **DO: HOLD.** Don't disturb np2/np3/m26 — protecting them now doubles as auto-reclaim if the king is DQ'd. Wait for the owner ruling. `uphard_salience`/cap32 (compliant structure-pinning, NO new markers) stays the valid lever regardless.
- **IF king is ALLOWED + `#source line N` later approved for all** → NEW compliant lever → add line-number annotation to our compressor (new candidate). `scripts/check_readme_current.py` will catch the marker landing.
- **COMPLIANCE MAP (this Discord, 2026-06-29→30):** `#source line N` NOT approved (king used it, under review). Karim's `[[CMP]] {n} chars omitted [[/CMP]]` / `{n} more chars truncated` = PENDING ("looks okay at first glance", not approved → our dormant `omitcount` stays dormant). Loop prompts beyond the 2 existing reasons = REJECTED (Hiccup's "Do not repeat/submit" = directive, denied). ALL prompt content must live in prompt.md or fail review. Principle owners stated: **INFORMATIVE-only** (state facts), never **DIRECTIVE** (tell the agent what to do).

## ★★★ 2026-06-30 ~08:05Z — ⚠️ NEW KING 5EeUAVZ CRATERED OUR FLOOR 14.3% → **0%** [see 08:35Z above: king under compliance review, may be DQ'd]. (full: `reports/new_king_5EeUAVZ_analysis.md`)
**READ-FIRST — this SUPERSEDES "Floor UNCHANGED 14.3%" below.** A new scored miner **`5EeUAVZDbk2j…` = 0.852** (E1.076/M0.959/H0.535) appeared and **wins 5 of 7 elements = 90.5% of pool**: Overall + Pair(E,M) + Pair(E,H) + **Pair(M,H) (took np3's)** + **Single-M (took np2's)**. Single-E → 5EKyJnby 1.225 (*evaluating*), Single-H → 5GgVXz 0.676. **OUR SHARE = 0%** (np2/np3 still score 0.684/0.682 LIVE — we lost the winner-take-all elements, not points). Old king 5DZLFZj 0.728 also dethroned.
- **MECHANISM (per-run, 5/task): the king is "np2 but LIGHTER + CLEANER", not a new trick.** Savings IDENTICAL (King +1.234 vs np2 +1.258 mean Trim(ln) on pass-pass), cache IDENTICAL (~93.6%). The edge = it keeps MORE context (**1.33x vs np2's 1.49x**) → **breaks fewer RUNS (9.0% vs np2 12.4%) AND flips more RUNS (40% vs 30%)**. Task-level binary "5 flips/16" hid this — the difference is how many of the 5 runs/task land.
- **WHERE THE GAP IS (actionable): flip edge = sympy Hard** (king 5/5 vs np2 **1/5 on sympy-18698**; +2 on 23824/20801; also 19346/14976) = np2 OVER-compresses, king keeps fuller → flips. **break edge = django baseline-pass** (king 0 vs np2 **4 break-runs on django-12039**; +sympy-23262, django-13158/11740). 
- **VALIDATES OUR DIRECTION + the running A/B.** The king is empirical proof that **fuller-keep (cap32/nocap) + import-salience → fewer breaks + more flips** is the winning recipe (savings are dead weight in the weighted regime). Our **missed-flip A/B (`bvtw2f6jp`, RUNNING)** tests exactly the king's 3 biggest flip wins (sympy-18698/14976/23824) — does cap32/salience push np2 1/5 → toward king's 5/5? **Realistic reclaim = Single-M** (need M>0.959 = match king's ~9% break rate; gap +0.11, hard but a favorable draw of a king-recipe miner could edge it). The king's 0.852 also has run-variance (partly a favorable draw); board is active.

## ★★★ 2026-06-30 ~07:30Z — gap DECOMPOSED (breaks + missed-flips); SALIENCE candidate built; missed-flip A/B DIED (disk full) → REBUILT (see 08:05Z above for new-king context).
**READ-FIRST. Floor UNCHANGED at 14.3% (m12 0.130 · np2 0.684 WINS Single-M · np3 0.682 WINS Pair(M,H) · m26 0.610; king 5DZLFZj 0.728 = 71.4%; 5GgVXz Hard-zone 14.3%). This session: turned the "algo exhausted / just redraw" verdict (below, SUPERSEDED) into a real root-cause + a candidate (`uphard_salience`).**

- **WHERE OUR 0.044 GAP TO THE KING ACTUALLY IS (comprehensive per-run decomposition, `reports/reanalysis_2026-06-29.md`):** ~**60% BREAKS** (baseline-pass→fail, −4) + ~**40% MISSED HARD FLIPS** (baseline-fail the king solves & we don't). It's NOT just −4 breaks and NOT just sympy: django breaks 10% / sympy 13% (broad). Quality/savings ≈ 0 (we match the king per-token). So the king beats us on **fewer breaks AND more flips, across both families** — no single lever closes it.
- **TWO LEVERS map to the two loss types:** (1) **breaks** ← `salience` (pin imports/structure the extractive was dropping); (2) **missed flips** ← `cap32`/fuller-keep (np2 OVER-COMPRESSES huge Hard contexts, e.g. sympy-18698 3.27x→flips 1/5 vs king 2.55x→3/5; keep them fuller → flip). **`uphard_salience` = cap32 + salience = both levers in one.** django breaks look like inherent variance (no clean fix).
- **ROOT CAUSE (verified) of the break half:** base `_line_is_pinned` pins def/class/errors/tests/diffs/paths but DROPS imports/decorators/raise/except (low token-richness). On code reads that loses the file's API → wrong edit → break. Real 32k sympy read: np2 dropped 19/30 imports. **`salience` (`_STRUCT_PATTERN`) pins them → keeps 30/30 at ~identical compression.**
- **CANDIDATE FILES (all forks of np2; m12/np2/np3/m26 stay LIVE; uploads USER-run):**
  - `upload_miner_uphard_salience.py` (**sha256 695b4fe4** = the documented sha, CORRECT; git-hash 57e325c7, SHA-1 efd7b923 — same bytes. ⚠️ CORRECTION 2026-07-01: the 06-30 "STALE sha" note was WRONG — hash-algo confusion, the file never drifted) — **THE candidate.** cap32 + import-pinning. Codex GO-WITH-CHANGES (raise\b applied). VERIFIED: diff vs cap32 = ONLY the `_STRUCT_PATTERN` import-pin (clean superset); parses. Targets BOTH breaks + flips.
  - `upload_miner_uphard_cap32.py` (git-hash **a2a42bf7**; shasum 04cc727d; was documented b60c7d68 = STALE) — combined-Overall (np2 E+M + np3 Hard); ≈ np2 except keeps >53k results fuller (NP_MAX_KEEP 32k = np3's proven zone; floor 16k, frac 0.60 — VERIFIED 2026-06-30). Codex GO.
  - `upload_miner_uphard_nocap.py` (fb577c10) — = the version USER uploaded earlier (huge results uncapped, np5-crater risk). Logic-recon of live 96052567.
  - `upload_miner_uphard_omitcount.py` (9a02818f) — DORMANT (gated; Karim's "{n} chars omitted" marker pending README; OMIT_COUNT_ENABLED=False ⇒ == cap32).
- **A/B RESULTS (local eval; the PLATFORM is the only real arbiter — local crashes 50% of tasks):** salience EDGES np2 on import-heavy sympy *breaks* (worst-common: sympy 6/9 vs np2 5/11) — directional, N small. **`uphard_salience` is the best candidate** but unproven on-platform. ⚠️ **the SAFE/no-regression check is IMPOSSIBLE locally** (those tasks runtime-error).
- **MISSED-FLIP A/B (`bnfpmk15g`, run 072014) = DEAD, 0/36 usable.** Not 50%-crash — **100%**: host disk hit **99.4% full (2.8 GB free)**, Docker's containerd content store threw **I/O errors**, couldn't pull the sympy sandbox images → every solve `runtime-error`. Zero signal. Hog = `Docker.raw` **218 GB allocated** (old swebench images); `docker prune` can't fix (daemon errors on its own store). ⇒ first failed UNANSWERABLE. **RESOLVED 2026-06-30 ~07:35Z: USER chose fix-Docker-and-retry. Docker RESET (quit → deleted `Docker.raw` → restart) reclaimed 218 GB (disk 98%→46%, 227 GB free); fresh daemon v29.2.1, store clean, no more I/O errors.** Verified nothing irreplaceable lost (gateway image `alpine/openclaw:2026.5.27` pullable; sympy sandboxes auto-pull; host repos survive). **A/B RE-RUNNING — DOCKER FIX CONFIRMED, now blocked on KEY.** Smoke test (`bksmm33iz`, np2/sympy-18698) ran the pipeline END-TO-END: image pulled, gateway up, agent loop ran to the first model call — Docker is fully healthy. BUT it died `runtime-error: HTTP 401 "User not found"` = the **984d OpenRouter key is DEAD/revoked** (definitive auth rejection, not rate-limit/credit). The full 36-solve run would all 401 the same. **BLOCKED: need a fresh valid OpenRouter key** (proper location = `config/secrets.env`, git-ignored; the hook blocks me from writing it → USER adds it). Once keyed, launch the full A/B.
- **BEST-OF-N DOWNGRADED (was "the play"):** np2d1 (0.49) + np3-redraw 5DSci2Z (0.464) = TWO clean redraws both ~0.46–0.49 ⇒ **0.684 is np2's FAVORABLE draw, not a floor** (typical clean draw ~0.55). Redraws are a tail lottery (~15%/draw beats king). ⇒ **DON'T disturb the live winners** (a platform re-eval could redraw them ~0.49 → lose Single-M/Pair(M,H)). Protecting the floor > chasing.
- **TOOLS built this session:** `scripts/vet_draw.py` (account-clean check: cache≥88%/break≤13%/<4 timeouts; CLEAN vs BAD-DRAW vs BAD-ACCOUNT) · `scripts/check_readme_current.py` (standing pre-upload compliance gate; re-fetches live README) · `scripts/collect_runs.py` FIXED (per-run via inline sweRunsByTaskId). Run BOTH gates before any hotkey.
- **COMPLIANCE (verified vs LIVE README 2026-06-29):** allowed = `[[CMP]]`/`[[/CMP]]`/`[[BLOCK X]]` + 2 loop reasons only. NO loop-prevention prompt allowed (Discord: steering REJECTED; Hiccup's strict version pending — NOT in README). All our miners + salience PASS. Karim's omitted-count marker tentatively-favored but NOT yet landed.
- **SECURITY:** OpenRouter key 984d (`sk-or-…984d`) pasted in chat (used for local eval, env-only, not persisted) → ROTATE when done.
- _The 2026-06-29 ~05:10Z + ~06:30Z sections below are SUPERSEDED: "algo exhausted / best-of-N is the play" → corrected to "gap = breaks + missed-flips; salience/cap32 are real partial levers; best-of-N is a tail lottery; platform is the arbiter."_

## ★★★ 2026-06-29 ~05:10Z — CURRENT: ALGO SPACE EXHAUSTED → the ONLY play is VARIANCE BEST-OF-N. 14.3% floor held.
**READ-FIRST. Verdict this session: there is NO algorithmic miner that beats the king or wins a new element — proven 5 builds + raw-metric dive + 3 Codex passes. The active play is now clean np2/np3 redraws (the king is one noisy draw). m12/np2/np3/m26 LIVE on DeepInfra+Venice. Plan = `reports/variance_draw_plan.md`.**

### ⟳ 2026-06-29 ~06:30Z UPDATE — fresh per-task re-analysis + USER decisions (aggressive draws + build Hard specialist)
- **RE-ANALYSIS (Codex-verified, `reports/reanalysis_2026-06-29.md`):** the king is np2's **TWIN** (np2 compresses marginally BETTER per-token; cache 93.9 vs 93.8%); the 0.044 gap is **66% same-outcome RUN-VARIANCE**, not breaks/savings → king is a beatable lucky draw (confidence UP for best-of-N). Hard-discriminator is provably absent (all token features overlap). Easy-lift refuted (np2 already ≥ king on Easy savings).
- **USER chose: AGGRESSIVE draws (4-5+ accounts) + BUILD the Hard specialist now.** Allocation (in the plan): ~3× np2 (Pair(E,M)) + 1× np3 (Overall/defense) + 1× **uphard** (Hard zone), EACH on its own DeepInfra+Venice account.
- **CORRECTED HARD MECHANISM (big finding):** Hard flips need CONTEXT → aggressive compression HURTS Hard (proven: np2@16k H0.173 < np3@28k H0.369). 5GgVXz wins Hard (0.676) by keeping BIG results FULLER (~1.68x) while compressing small/mid. A flat cap can't; a **PROPORTIONAL** cap can.
- **BUILT: `upload_miner_uphard.py` (sha 950a054d) — Codex-cleared GO.** np2 fork: `cap = max(8000, 0.60·len)` → uniform ~1.66x (keep 60% of each result; <8k passthrough → Easy preserved; 87k→52k vs np2's 16k = 36k MORE flip-context). Cache-stable/idempotent/bounded/compliant verified. Codex caught + I fixed: (1) the backwards 4k-flat version (over-compresses → kills flips), (2) guard-ordering. **READY for USER upload on a spare hotkey** (registry: uphardsub, hotkey TBD). Read at scored: Easy≥0.85 → Pair(E,H) (E+H)/2 vs 0.760 + Single-H vs 0.676. FALLBACK if Hard<0.369: draw np3 as the Hard vehicle.
- _Note: "algo exhausted" still holds for Overall/Pair(E,M) (use draws); uphard is a fresh PROPORTIONAL attempt at the Hard zone only — the one corner not previously tried cache-stably._

- **ALGO TRULY EXHAUSTED (last stones turned this session):**
  - **strelief SCORED 0.509 = CLEAN FAIL** (`5DLMDwMm`, sha c70bd40a). Relieving failure-output context → the model WANDERS (7 breaks), did NOT flip Hard. The Hard-flip-via-relief idea is DEAD; 5GgVXz's H0.676 needs its unreplicable task selection, not a relief heuristic.
  - **ehspec = Codex NO-GO** (sha 44caadda, inverted size-tier 6k-small/28k-big). Premise was TASK-level size medians; Codex caught per-**RESULT** Easy/Hard sizes OVERLAP (14–58k) → a 16k size boundary CANNOT separate categories. Not built.
  - **ASSISTANT-CONTENT band (44% of tokens) = STRUCTURALLY BLOCKED.** Assistant msgs are tiny (median 325c, p90 1526c) → a cache-stable per-message cap fires 0–2% = NO-OP; 95% carry tool-call JSON → line-extractive CORRUPTS the action → break; the 44% is only large CROSS-message aggregate → capturing it needs recency/summarization = CACHE-BUST (np4 prefix 16%). No viable cache-stable build. This EXPLAINS why np2 only caps big tool-results (np2 design CONFIRMED correct).
  - **WEIGHTED-TOKEN METRIC DIVE: we are already token-OPTIMAL.** np2 cache 93–94% == king, output ~1% == king, savings term matched. The king's 0.044 Overall edge is NOT a savings or routing advantage we can engineer — only the luck of the draw.
    - **⟳ 2026-06-29 RE-DERIVATION (Codex-verified, `reports/reanalysis_2026-06-29.md`) — CORRECTS the mechanism:** the gap is NOT "the BASE/breaks term" as first written. Per-task decomposition: **66% of the gap is on SAME-outcome tasks** (both pass-pass, king scores higher run-to-run), only 34% from break/flip diffs. And **np2 compresses slightly MORE efficiently** (weighted ratio king/np2 = 1.036). ⇒ king ≈ np2 **TWIN**; the gap is **RUN-VARIANCE**. This RAISES confidence: the king's 0.728 is a beatable lucky draw, not a better algorithm.
    - **Two fresh creative levers tested + CLOSED:** (1) Hard-specialist via failure-signal — **no discriminator exists** (every token feature overlaps Hard-vs-E/M, |d|≤0.81, 28% misclass floor; ehspec NO-GO generalized). (2) Easy-lift via tighter cap — **refuted** (np2 Easy savings 0.556 ≥ king 0.552; one Easy break = 10× the gap). Don't build either.
- **⇒ THE ONLY PLAY = VARIANCE BEST-OF-N + DEFENSE** (`reports/variance_draw_plan.md`): **PRIMARY = Pair(E,M)** (king 0.968 vs our np2 0.951 = gap only **0.017**, the most-winnable element → reclaim → back to **23.8%**). **LOTTERY = Overall** (gap 0.044, ~24.6%/clean draw). Draws: **4× np2** (sha a64231c9, shots Pair(E,M)+Overall) + **1× np3** (sha 420de1cc, shots Overall, insures Pair(M,H)), **EACH on its OWN isolated DeepInfra+Venice account** (never 2 draws/a live re-eval on one account → that contention is what poisoned m33).
- **IN FLIGHT: np2d1** (`5FPPav7s…`, np2 redraw) — evaluating **0.608** (recovered from a 0.347 screener low; only 1 break = **django-11551**). **django-11551 = np2's high-variance Achilles SCREENER task** — the lottery turns on it: this draw rolled it badly (likely a Pair(E,M) miss), so re-draw for a clean roll. Read at scored: Easy≥0.85 binding → E+M>0.968 / total>0.728.
- **BASE-CHOICE SETTLED (user asked "base on np3 / new base?"):** NO. Data refutes "np2 worse" — np2 (16k) 24 clean/6 shaky/4 break ≈ np3 (28k) 20 clean/11 shaky/3 break (np2 has MORE clean). **np2 = Pair(E,M) offense** (its Easy 1.052 is the REQUIRED asset; np3's Easy 0.859 CANNOT win Pair(E,M)). **np3 = Pair(M,H) defense** (H0.369). New base = algo exhausted. Keep np2 for the Pair(E,M) draws.
- **ROUTING (the floor's life-support, refined):** allow ONLY **DeepInfra + Venice** (price-sort → DeepInfra primary ~90% cache, Venice 89%-off fallback); **BLOCK** Google/Novita/Alibaba (0% cache → tank savings) + **AtlasCloud** (breaks) + **WandB** (useless cache). NEVER the DeepInfra-only pin (no fallback → truncation craters, killed m33/np2c/np_prop). Every LIVE miner stays on this.
- **DEFEND:** np2/np3/m26 LIVE on DeepInfra+Venice. Watch the THIN **Single-M** (np2 0.849, only +0.017 over the king) — first thing we'd lose if a rival's Medium creeps.
- _Prior 2026-06-28 ~23:00Z section (the routing-fix headline) below remains valid; this section supersedes its STRATEGY with the exhausted-algo verdict + the concrete draw plan._

## ★★★ 2026-06-28 ~23:00Z — CURRENT: 14.3% floor (lost Pair(E,M) to new king); the ROUTING FIX is the headline.
**READ-FIRST. Portfolio DROPPED 23.8% → 14.3%. New king 5DZLFZj 0.728 took Overall+Pair(E,M)+Single-E. The session's biggest finding: the recent craters were the DeepInfra-ONLY-pin (no fallback) TRUNCATING solves — FIX = allow DeepInfra+Venice only. m12 LIVE.**
- **PORTFOLIO = 14.3%:** np2 (5CPbtf, 0.684, E1.052/M0.849/H0.173) **WINS Single-M (4.8%)** · np3 (5F9ZRe, 0.682, H0.369) **WINS Pair(M,H) (9.5%)**. Both SAFE from the king (king M0.832<np2 0.849; king H0.272 too low for Pair(M,H)). m12 (5Dz7) 0.130 LIVE. m26 (5Ekcy) 0.610 (E1.066).
- **NEW KING 5DZLFZj 0.728** (E1.105/M0.832/H0.272) = Overall(57%)+Pair(E,M)(9.5%)+Single-E(4.8%) = **71.4%**. We LOST Pair(E,M) (np2 0.951 → king 0.968). RIVALS: 5GgVXz (H0.676)=Pair(E,H)+Single-H=14.3% (the Hard-flip 19% zone); 5DCnA57 old#1 0.697; 5Ggq 0.673.
- **⚠️ ROUTING ROOT-CAUSE + FIX (biggest finding):** a **DeepInfra-ONLY pin = NO FALLBACK** → under heavy eval load DeepInfra saturates → solves TRUNCATE → −4 breaks. Cratered m33 (scored 0.216, BYTE-IDENTICAL np2), np2c, likely np_prop (0.487) — NOT credits ($102 funded) / provider (DeepInfra confirmed) / algo. **FIX (PROVEN): allow ONLY DeepInfra+Venice** (both cache-effective: DeepInfra primary ~90% hit, Venice 89%-off fallback); **BLOCK no-cache Novita/Google/Alibaba (0% cache → tank savings) + AtlasCloud.** Proof: m33's 41 post-fix full-token tasks scored ≈ np2 (1.04× tokens); its 9 pin-truncated tasks (−1.41, 5 breaks) poisoned the total. **KEEP every live miner on DeepInfra+Venice** — a re-eval under the pin craters the floor.
- **CATEGORY MAP CRACKED (validated):** Hard = the **16 baseline-FAIL tasks** (model fails uncompressed) → won by **FLIPPING** (+2), CAN'T break. Easy/Medium = the 34 baseline-PASS (Easy=small, Medium=big). Our −4 breaks are on baseline-PASS Easy/Medium, NOT Hard.
- **STRATEGY (Codex-reconciled):** (1) kings' OVERALL edge over np2 (0.044) is WITHIN VARIANCE (Z~0.66 SE) → **BEST-OF-N clean np2/np3 draws** (~24.6%/draw, 3→>50% vs 0.728) on the FIXED routing, **EACH ON ITS OWN ACCOUNT** (concurrent draws on one account starve each other). (2) **Hard-FLIP = a REAL above-noise lever** (5GgVXz H0.676 ~3 SE) → the 19% uncontested (Pair(E,H)+Single-H) → strelief / 5GgVXz-style aggressive. (3) DEFEND the floor.
- **IN FLIGHT:** **strelief** (5DLMDwMm, sha c70bd40a, IN QUEUE) = np2 16k + np3 28k relief on failure-output results; RE-AIMED as a **Hard-flip helper**; FIRST clean test on the fixed routing (Easy≥0.85 = all-clear, then read Hard).
- **DEAD/skip:** m33 (0.216 pin-poisoned, DISCARD), np_prop (0.487), np2c/np2b/np5; nptok (sha ba18fbd0, token-cap = wrong direction, NOT uploaded); hardspec (sha e31cf08a, ≈m26, SKIP per Codex).
- _Prior 05:10Z section (23.8% era) below is now SUPERSEDED._

## ★★★ 2026-06-28 05:10Z — CURRENT: 23.8% locked; np2c (Overall lottery) + np_prop (king-method Hard challenger) in flight.
**READ-FIRST. 23.8% (np2 Pair(E,M)+Single-M + np3 Pair(M,H)) is SECURE + correctly-routed. m12 LIVE. Two challengers in flight + two pending levers.**
- **OUR MINERS:** m12 (5Dz7) 0.130 LIVE/untouched · m26/np1 (5Ekcy, cap6k) #5 0.610 **E1.066 (0.001 from Single-E!)** · np2 (5CPbtf, cap16k) #2 **0.684 = Pair(E,M)+Single-M = 14.3%** · np3 (5F9ZRe, cap28k) #3 **0.682 = Pair(M,H) = 9.5%**.
- **DEAD experiments:** np2b (5DG31B) **0.129 = PROVIDER CRATER** (e2c/AtlasCloud acct, NOT the algo — per-task proved np2≈np2 on identical-treatment tasks). np5 (5CZxaU) **0.25 = the 48k NEAR-PASSTHROUGH CLIFF** (keeping big results raw → wander; CONFIRMS near-passthrough craters for us → cap settled at 16k). np_prop-as-pure-proportional rejected by Codex (would fragment the 10-29k band np2 passes → regress).
- **IN FLIGHT:**
  - **np2c (5GCWMTZk)** = byte-identical np2 (sha a64231c9) on the 47b STABLE key = **VARIANCE LOTTERY #2 for OVERALL (57%)**. Uploaded, screening. READ AT scored + **verify Easy~1.05 (binding) FIRST**. If the draw tops #1's 0.697 → win Overall.
  - **np_prop (sha 05bca9f2, NOT yet uploaded; Codex pre-upload GO)** = the **HYBRID = THE KING'S METHOD** (§24/§26): np2 EXACT for results ≤32k (E/M byte-identical → 14.3% protected) + a **2× ceiling on >32k** (64k→32k=50% vs np2's 16k/4× = never over-compress) → fixes the over-compression breaks → targets **Hard**. ADDITIVE Hard/Overall-challenger. USER uploads on the 47b key. Read at scored: Easy~1.05 (binding) + **Hard vs np2's 0.173** + BREAK count vs np3 (Codex watch: breaks climb → tune ceiling toward 28k).
- **KEY FINDINGS this session:**
  - **PROVIDER LEVER (huge, §17):** np2b crater = AtlasCloud **0% cache**. We're ALREADY optimal (DeepInfra ~90% cache, np2 measured 94%). BUT the account uses **BALANCED routing → routes to Venice (67% cache) sometimes** = a HIDDEN variance source. DEFENSIVE: pin DeepInfra (ignore AtlasCloud/Alibaba/Novita/W&B; Venice fallback). Provider quality ~equal across providers → it's defensive, not a path past #1.
  - **CAP fully mapped + SETTLED at 16k:** 6k 0.610 / **16k 0.684 (peak)** / 28k 0.682 / 48k 0.25 (cliff). Local sweep §23: 14k & 20k each took a failure, 16k clean 8/8.
  - **THE KING'S METHOD (§24):** uniform-light/proportional (per-task ratio median 1.24×/max 2.02×/std 0.36, NEVER over-compresses) vs our bimodal absolute cap (std 0.61; 9 tasks >2× up to 4× = our over-compression breaks). → np_prop hybrid replicates it surgically.
  - **COMPRESSION-ALGO space mapped:** cap (16k settled), coherent-extractive (≈np2 §21), dedup (cache-bust §16), reasoning (uncapturable §17), lossless (0.5% §19), near-passthrough (craters §22). The **PROPORTIONAL ceiling (np_prop)** is the one LIVE mechanism left.
- **PENDING LEVERS:** (1) **np_prop upload** (Hard via the king's never-over-compress). (2) **SINGLE-E tighter-cap specialist** (~4-5k → push Easy past #1's 1.067; tighter→higher Easy: m26 6k 1.066 > np2 16k 1.052; near-free, +4.8%→28.6%; additive). (3) **Pin DeepInfra routing** (defensive consistency).
- **RIVALS:** #1 5DCnA57 0.697 (Overall+Single-E=61.9%); 5GgVXzUB (Pair(E,H)+Single-H=14.3%); 5Ggq #2 0.673. Full chain: reports/cache_stable_design.md §15–§26.

## 🚨★★★ 2026-06-27 12:55Z — PROVIDER ROUTING IS A ~0.55 LEVER (the biggest found). m14 confound CONFIRMED REAL.
**np2b (5DG31B) SCORED: total 0.129 (E0.565/M−0.400/H0.249) — BYTE-IDENTICAL np2 code (sha a64231c9) but on a DIFFERENT
OpenRouter account with AtlasCloud NOT blocked. vs np2 (5CPbtf, original account, good routing) = 0.684 (E1.052/M0.849/H0.173).
SAME CODE → DELTA −0.555.** Only the account+provider differ. This DEFINITIVELY confirms the m14 confound was REAL (not a false
analysis): the OpenRouter PROVIDER that serves qwen3-coder swings the score by ~0.55 — far bigger than ANY compression lever we
found (those moved 0.01–0.05).
- **FINGERPRINT = model QUALITY (quantization), not context-capping:** Medium CRATERED (−0.400 vs +0.849, Δ−1.249) + Easy fell
  (0.565 vs 1.052) but Hard ~flat/up (0.249 vs 0.173). A context-cap would crater HARD (big contexts); instead the damage hits the
  tasks np2 normally PASSES (Medium) → a WEAKER/more-quantized model on AtlasCloud fails them → breaks. So: AtlasCloud serves a
  lower-quality qwen3-coder; the GOOD account blocks it and routes to a better endpoint.
- **CONSEQUENCES:** (1) np2b is a DEAD lottery ticket (confounded crater, wins nothing — confirms my warning). (2) The same-account/
  same-provider discipline (the m14 rule) is VALIDATED — future tickets stay on the good-provider account. (3) Our 23.8% (np2/np3/m26
  on the original account) is correctly-routed + SAFE. (4) ★ **THE BREAKOUT:** provider routing is a huge, untouched, NON-compression
  lever. HYPOTHESIS to test: the np2(0.684)→#1(0.697) Overall gap of 0.013 could be PROVIDER quality, not compression — if #1 routes
  to a marginally better qwen3-coder endpoint. If so, beating #1 = matching/beating its provider routing (block weak providers, force
  the best/least-quantized/full-context qwen3-coder), NOT a better compressor. TEST PLAN: upload np2 on a fresh hotkey with EXPLICITLY
  optimized routing (block AtlasCloud+weak; force best) → does it beat 0.684→0.697? Test on a SEPARATE hotkey first (never re-route the
  live 23.8% earners blind — np2b shows a bad provider craters). NEXT: enumerate qwen3-coder providers on OpenRouter (quant/context/
  speed) + check what the np2 account currently uses.

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
