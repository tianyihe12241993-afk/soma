# Cache-stable compressor — design + validation (2026-06-26, post weighted-token regime change)

_Goal: a compressor that wins under the NEW weighted-token scoring (1.0·input + (1/3)·cached + 3.0·output).
m12 stays LIVE/untouched; this is a SEPARATE candidate, designed + offline-validated here, Codex-audited before any
upload, USER-run. Direction set by the verified regime-change mechanism (state/CURRENT.md top)._

## 1. The objective (what the new formula rewards)
Verified from commit b79fcaee + local eval: under weighted tokens the dominant lever is **CACHE-STABILITY**. A
byte-stable emitted PREFIX keeps the provider prompt-cache warm → those tokens land in the ⅓ cached bucket instead of
the 1× input bucket → weighted tokens drop ~2× → the ratio bonus survives. Confirmed by mode:
- m12 **`pruned`/harvest-drop → ~0% cache**, weighted/raw ≈ **1.03** (compression is COUNTERPRODUCTIVE — worse than none).
- m12 **`gentle`/rich → 80-90% cache**, weighted/raw ≈ **0.45** (already king-level).
- King aggregate **85% cache**; m12 aggregate **56%**; 5GhUtKrYP (cache-buster) scored **−0.92 total** (negative).
Secondary: avoid breaks (now 2× a flip; flip 4→2, break −4). Output is ~1% of tokens = negligible.

## 2. Root cause (precise)
m12's HARVEST path **drops oldest interactions + blind head/tail truncates** → it REWRITES the emitted prefix every
turn → the provider cache invalidates from the first changed byte → ~0% cache. m12's RICH path never-drops + keeps
last-10 byte-intact + dedup-via-[[BLOCK]] → near-stable prefix → 85% cache. **The cache-bust is localized to the
harvest drop/prune; rich is already correct.** So the fix is targeted, not a rewrite.

## 3. Leading candidate: aow_bet (ALREADY BUILT — purpose-built for this regime)
`miner/cot_compression/upload_miner_aow_bet.py` (2001 lines, STATE_VERSION=7, parses clean). It is m12's compression
ENGINE + a freeze-on-emit wrapper, applied ONLY in harvest mode, ONLY before the session has shown rich depth
(`everTouchedRich` gate), ONLY when the previous output is a byte-identical prefix of the working set:
- **Freeze-on-emit:** once interactions age out of the recent verbatim window, compress them ONCE, FREEZE those exact
  output bytes (`frozenPrefix`/`frozenCount` in state), and REUSE them verbatim next turn → emitted prefix is
  byte-IDENTICAL turn-to-turn → provider caches it (the king's 85% profile).
- **SAVINGS_CEIL = 1.02** (inflation multiplier ≥1.0): the bet is that shipping a prefix NOMINALLY LARGER than m12's
  ~8k aggressive prune but byte-STABLE wins, because cached tokens are ⅓-weight. Reverts to m12 only on pathological
  inflation past native×1.02. (Under RAW scoring this larger output was the reason aow_bet was SHELVED — "cache is
  worthless." Under WEIGHTED scoring that reverses: the cache is worth ~2×.)
- Compliance preserved: allowed markers only ([[CMP]]/[[BLOCK N]]/"Same response as in [[BLOCK N]]."/loop reasons);
  never drops in harvest (truncate-only); no LLM calls; no task/category awareness. (Full pre-upload audit = Codex gate.)
- Siblings: `upload_miner_aow_lite.py` (earlier, capped freeze boundary → often no-op'd) and
  `upload_miner_m19_cache_stable.py` (freeze truncation depth). aow_bet supersedes aow_lite (the prepend-head +
  remove-boundary-cap fixes). All three now wired into the eval driver as profiles aow_bet/aow_lite/m19cs.

## 4. Validation plan (offline-first; the new formula is cache → we can measure it locally)
The local eval captures `token_usage.total` (input/cache_read/output) + assemble mode per run → `scripts/analyze_cache.py`
reports cache% + weighted/raw per (miner,task,mode) — the offline proxy for the new score.
- **STEP 1 (running, bg b0311jfml):** m12 vs aow_bet on the two tasks where m12 busts cache (django-13810 @0%,
  sympy-20590 @~10%), 2 runs each. GATE: does aow_bet flip the harvest-mode cache% from ~0% toward ~80% (king-level)
  AND keep weighted/raw < 1.0? If yes → mechanism validated under the new regime.
- STEP 2 (if STEP 1 passes): broader run (more harvest tasks + a few rich/deep tasks to confirm no regression),
  ≥3 runs, measure cache% + PASS-RATE (aow_bet must not break the agent — freeze must not corrupt the context).
- STEP 3: tune SAVINGS_CEIL upward if the data shows bigger stable prefixes pay (cache is cheap now), and compare
  aow_bet vs aow_lite vs m19cs.
- STEP 4: Codex pre-upload audit (diff-vs-m12: compliance, freeze correctness, no context corruption) → USER uploads
  to a SEPARATE hotkey, same OpenRouter account. m12 stays LIVE.

## 5. Open questions / risks
- **Local cache ≠ platform cache?** Provider caching (TTL, settings) may differ; the RELATIVE m12-vs-aow_bet cache
  delta on the same task should still be valid. Platform-scored result is the only arbiter.
- **Does freeze corrupt the agent's context?** Freezing an early compressed view and never updating it could starve
  the agent of later-relevant detail → breaks. STEP 2 pass-rate gate checks this. (m12 rich already never-drops, so
  the risk is in the freeze boundary, not the content.)
- **SAVINGS_CEIL too tight?** 1.02 was tuned for the raw-era "minimal inflation" intent; the weighted era may favor a
  larger stable prefix. Tune empirically in STEP 3.
- **Huge contexts:** if the frozen prefix + live tail exceeds the window, aow_bet must still reduce — verify it does so
  without rewriting the frozen prefix (truncate newest only). Check in STEP 2 on the biggest tasks.

## 6. Results

### STEP 1a — local OpenRouter cache% = UNRELIABLE (abandoned as a metric)
The 8-solve m12-vs-aow_bet run (django-13810, sympy-20590) showed `cache_read` is NOISE: the SAME mode on the
SAME task swung 0%↔85% across runs (gentle was 85% in the calibration run, 0-1.5% here; nothing_to_remove 0/17/44%).
It reflects OpenRouter's cross-run cache TTL/warmth, NOT the miner's intrinsic prefix-stability. ⇒ cannot validate
cache-stability via local cache_read. (Also the 2 test tasks didn't reliably trigger the prune path.)

### STEP 1b — DETERMINISTIC prefix-stability = aow_bet VALIDATED ✓ (scripts/prefix_stability.py)
Replayed m12 vs aow_bet on a synthetic GROWING conversation (state threaded by sessionId), measuring the byte
common-prefix of each turn's compressed output vs the previous turn — exactly what the provider prompt-cache rewards,
with ZERO OpenRouter dependence (fully reproducible). Result, in HARVEST mode (where m12 busts cache):
| miner | avg output-prefix stability | min |
|---|---|---|
| m12 | **69.6%** | **5.8%** (turn 20 re-prune rewrote ~94% of the prefix) |
| **aow_bet** | **99.9%** | **99.6%** |
m12 rewrites its prefix every harvest turn (catastrophically on re-prune → 5.8%); **aow_bet's freeze holds it
byte-identical at 99.9%.** aow_bet's output is LARGER (49k vs 30k chars at turn 25 — the SAVINGS_CEIL bet) but
byte-STABLE → cheap under weighted tokens (cached at ⅓). Mechanism PROVEN. NOTE: aow_bet kept ~94% of native here
(barely compressing = near-passthrough-like, consistent with 5DCnA57 #1) → window-overflow risk on HUGE tasks must
be checked (does the ceiling force reduction without busting the frozen prefix?).

## 7. Remaining risks (prefix-stability is necessary, not sufficient)
- **Pass-rate:** does the larger frozen context keep the agent SOLVING (no breaks from stale/over-large context)?
  Local cache run: aow_bet resolved 3/4 vs m12 4/4 (tiny sample). Local pass-rate is noisy (local≠platform for
  outcomes) → the PLATFORM is the arbiter.
- **Window overflow** on huge tasks (aow_bet barely compresses) — verify the ceiling reduces without rewriting the
  frozen prefix.
- **Local cache ≠ platform cache** confirmed → only the platform-scored result settles the actual weighted-token gain.

## 8. Codex pre-upload audit + reconciliation (2026-06-26, agent a0c48473) — VERDICT: NO-GO as-is
Codex returned NO-GO. Reconciled item by item (Claude verified each against the code; some refuted, the bottom line stands):
- **Item 1 COMPLIANCE — Codex NO-GO; Claude RECONCILES to PASS.** Codex flagged "freeze emits non-m12 bytes" (holds
  `working[:hold_boundary]` raw, and `frozen_count==0` passes the prefix guard on the first harvest turn). True, but those
  are raw CONVERSATION bytes held verbatim (= passthrough of the front) — COMPLIANT (no markers/steering/LLM/task-ID;
  Codex itself confirmed markers constrained + no network). "Not byte-identical to m12" ≠ non-compliant. NOT a compliance violation.
- **Item 2 FREEZE CORRECTNESS — Codex NO-GO; Claude RECONCILES to "no corrupted output shipped".** Codex: not every
  failure falls back to m12_native (post-freeze orphan guard → `sanitized`=working at 1886-1888; final invariant only
  clears state at 1907-1912). VERIFIED: the orphan-guard→`working` fallback is m12-EQUIVALENT (m12's own rich branch does
  the same, 1921-1924) and `working` is a VALID output; the final invariant only resets the freeze, result was already
  cache-property-asserted. No path ships a CORRUPTED/orphaned list. So "ships a bad output" is overstated — but Codex is
  right that "every failure → m12_native" was imprecise (some → `working`, which is m12-equivalent and valid).
- **Item 3 WINDOW-BOUND — Codex CONFIRM = Claude.** Bounded (max 46k tok), rich-gate + native×1.02 ceiling contain it. PASS.
- **Item 4 STATE CARRY-OVER → RICH DIVERGENCE — Codex RIGHT, Claude WAS WRONG. THE REAL BLOCKER.** save_state (line 503)
  persists `output_messages` = aow_bet's LARGER frozen output (NOT decoupled/m12-exact); resolve_stateful_messages (558-561)
  rebuilds `working` from it in BOTH feed modes. So on harvest→rich escalation, compress_gently runs on aow_bet's
  accumulated LARGER trajectory, not m12's pruned one → **aow_bet ≠ m12 in rich**. This is the PROVEN m21/m22/m25
  Hard-crater mechanism (harvest content change feeds rich via state; m21's keep-more harvest cratered Hard 0.919→0.461).
  My "strictly ≥ m12 by construction" claim is FALSE — aow_bet has real Hard/rich downside. (Local sample also had aow
  cache 4.6% < m12 7.2%, resolved 3/4 < 4/4 — noisy but not reassuring.)

**RECONCILED VERDICT: NO-GO on aow_bet as-is** (both models agree on the bottom line; the decisive reason is Item 4, the
state-coupling Hard-crater risk — NOT compliance, which is fine). Do not spend a hotkey on it as-is.

## 9. Forward (post-NO-GO)
Two paths; **near-passthrough preferred**:
- **(A) Decouple aow_bet's state** (save m12-exact to state so rich sees m12's trajectory). BUT this fights the freeze: the
  freeze needs the connector to feed back aow_bet's ACTUAL (larger) emitted output and match it via outputFingerprint;
  saving m12-exact → feedback mismatch → GUARD(a) fails → re-seed → freeze never accumulates → cache fix lost. Same tension
  m25 hit. Non-trivial; may be self-defeating.
- **(B) NEAR-PASSTHROUGH design (PREFERRED).** 5DCnA57 (near-passthrough) is the new field #1 (0.697). Compress minimally,
  only when the window forces it, keep the prefix maximally stable — NO harvest/rich split → NO state-coupling Hard risk →
  cache-stable across ALL modes (not harvest-only). Simpler, and it's the proven winning archetype. This is the next build.
m12 LIVE/untouched. No hotkey spent. Next: design + offline-validate a near-passthrough candidate (cache-stable everywhere,
no state-coupling), re-audit, then user uploads.

## 10. np1 — near-passthrough candidate BUILT + offline-validated (2026-06-26)
`miner/cot_compression/upload_miner_np1.py` (copy of m12 + surgical core swap; m12 untouched/git-clean). DESIGN: **stateless,
idempotent, per-message cap.** Drops m12's resolve_stateful_messages / save_state / mode-routing entirely (that state-coupling
sank aow_bet). handle_assemble applies ONE deterministic transform: `cap_tool_result` extractive-caps each tool result whose
text > NP_RESULT_CAP (6000 chars) using active=frozenset() (PURE fn of the message's own content), wraps it in [[CMP]];
everything else (system/user/assistant, already-[[CMP]], <=cap) passes through verbatim. Reuses ALL m12 compliant primitives
(sanitize, extractive_compress, markers, loop-guard). compress_structurally/compress_gently/save_state remain as unused dead code.
- WHY cache-stable: the transform depends ONLY on each message's own content (not global size/recency) and is IDEMPOTENT
  (already-[[CMP]]/<=cap → unchanged), so an already-emitted prefix is reproduced byte-identical next turn under EITHER feed
  mode → provider cache stays warm. No harvest/rich split + no carried state ⇒ the aow_bet/m21/m22 cross-mode Hard-crater
  mechanism CANNOT occur (np1 has one mode).
- VALIDATION (scripts/prefix_stability.py, window_bound_check.py, + functional probe): prefix-stability **100% (min 99.8%)** on
  the cap path (vs m12 70%/min 5.8%, aow_bet 99.9%); **0 orphans / 80 turns**; **idempotent** (np1 on its own output = byte-
  identical); **passthrough** when nothing exceeds cap (changed=False, native emitted = maximal cache); cap preserves signal
  (kept the AssertionError line, 24k→6k); **compliant** (only allowed markers, no LLM/task-ID/network).
- WINDOW-BOUND: np1 only CAPS (never inflates) ⇒ output ≤ native ALWAYS ⇒ cannot overflow worse than the no-plugin baseline
  (which runs on the platform). The probe's 153k-tok max at 80 synthetic rounds is just ≤ that round's native; real comp-108
  natives are bounded by what the agent runs.
- OPEN (platform-only): (a) PASS-RATE — does the 6k per-result cap break the agent? (light + extractive-pinned → low
  disruption expected, but local≠platform). (b) SAVINGS — does np1 clear the weighted savings floor or eat the
  under-compression penalty like 5DCnA57 (~0.70 cap)? Either way ≫ our current best m25 0.449. (c) the real score.
- NP_RESULT_CAP=6000 is a LIGHT first cut (consistency-first); tune down later if it eats the savings penalty. m12 LIVE/untouched.

## 11. Codex pre-upload audit of np1 + reconciliation (2026-06-26, agent a551465a) — 1 blocker FOUND + FIXED
Codex returned NO-GO with ONE hard blocker; all else CONFIRM/WARN. Reconciled:
- **1 COMPLIANCE: CONFIRM** — dead code (save_state/resolve_stateful_messages/compress_gently/compress_structurally) verified
  NEVER called from handle_assemble; only allowed markers; no LLM/network/task-ID/steering in the live path.
- **2 NO-CORRUPTION: WARN (accepted)** — cap_tool_result flattens list-block content to a [[CMP]] string (less shape-preserving
  than m12's block-preserving truncation) but Codex probed it accepted + toolCallId preserved + idempotent; only happens on
  genuinely-compressed results (now also only when it shrinks). m12 likewise strings compressed tool output. Non-blocking; noted.
- **3 IDEMPOTENCE: CONFIRM** — dead code not reached; CMP_START-skip idempotent (probe second_capped=0). Caveat: loop-guard
  strip/re-append churns the TAIL on loop turns — immaterial (tail is after the cached PREFIX).
- **4 NO-INFLATION: NO-GO → FIXED.** Codex probe: a 6001-char result exited at **6018** because extractive_compress returns text
  UNCHANGED when all lines are pinned/fit, and cap_tool_result wrapped it in [[CMP]] anyway (+17). FIX applied (Codex's own
  one-liner): emit the wrapped form ONLY if `len(wrapped) < len(text)`, else pass the message through unchanged. RE-VALIDATED:
  6001→6001 (passthrough, was 6018), 6500→6016, 10000→6016, 24000→6016 — **every output ≤ input → output ≤ native always**;
  idempotent PASS; window_bound 100% prefix-stable / min99.8% / 0 orphans / bounded. Blocker CLOSED.
- **5 STRATEGY: WARN (platform-only, inherent)** — (a) 6k cap may break agents on tasks needing full tool output (−4); (b) may eat
  the under-compression/savings-floor penalty (5DCnA57-class ~0.70 cap). Unquantifiable offline; band = m12 0.130 < np1 ≤ ~0.697.
  Either way ≫ our current best m25 0.449. The 6k cap is a reasonable first setting; tune vs the task distribution after the platform read.

NOTE: Codex's sandbox could not run prefix_stability.py/window_bound_check.py (temp-dir write blocked) — so those numbers are
Claude's writable-env runs; Codex audited by code-reading + manual single-call probes. The fix Codex prescribed was applied and
re-validated in the writable env.

**RECONCILED VERDICT: the one hard blocker (inflation) is FIXED + re-validated; compliance/idempotence/window all PASS; corruption
is an accepted WARN; strategy risk is platform-only and inherent. np1 is offline-CLEAR to upload to a SEPARATE hotkey.** The
platform-scored result settles pass-rate + savings (the two unquantifiable-offline risks). m12 LIVE/untouched; no hotkey spent yet.

## 12. np1 (m26) SCORED #3 (0.610) — gap analysis + np2 (2026-06-26)
**np1 uploaded as m26 (5Ekcy) SCORED #3 of 59: total 0.610, E1.066 / M0.620 / H0.170.** Validates the cache-stable thesis
(m12 0.130 → m26 0.610). Detail-page dissection (scripts/dissect_top_miners.py):
- **m26 cache% = 93% (BEST in field, > #1's 91%), ratio 1.64×, mean 0.575, 7 negatives.** vs #1 5DCnA57 (cache 91%, ratio
  **1.18×**, mean 0.664, 6 neg) and king (85%, 1.64×, 0.605, 9 neg). m26's Easy 1.066 ≈ #1 (1.067) and BEATS king (0.924).
- **The gap is MEDIUM+HARD, NOT Easy — and it's BREAKS from OVER-COMPRESSION.** m26's 2 biggest losses vs #1: task 315
  (BREAK, compressed **2.43×**) −2.39, task 297 (BREAK, **2.86×**) −1.94 — its two HARDEST-compressed tasks. #1 (light, 1.18×)
  didn't break them. Plus task 302 INFLATED (0.84× = agent wandered under compression). Net gap to #1 = −3.99/45, and **those 2
  breaks alone = −4.33** → fix them and m26 PASSES #1. (m26 already has better cache + tied Easy; it just over-compresses a
  handful of big-result tasks into breaks.)
- **DIAGNOSIS: m26 is too aggressive (1.64×); #1 wins by being LIGHTER (1.18×) → fewer breaks/wander.** Fix = "go lighter."

**np2 = upload_miner_np2.py** (copy of np1, ONE change): **NP_RESULT_CAP 6000 → 16000** (lighter flat cap → keeps big critical
results fuller → fewer breaks/wander; targets ~1.3×, between m26's 1.64× and #1's 1.18×, safely above 5HdTr7's 1.07× inflate-trap).
Flat (not fractional/recency) to preserve idempotency → cache-stability. OFFLINE-VALIDATED: AST OK; 12k results now passthrough
(lighter than np1); 40k→20k cap keeps the AssertionError + ≤ orig (no inflation); IDEMPOTENT; prefix-stability 99.9% / 0 orphans /
bounded ≤ native (mechanism identical to np1). OPEN: the cap is the platform-calibration knob (too light → inflate-trap; too heavy
→ breaks); 16k = reasoned first cut. NEXT: Codex pre-upload audit → USER uploads → platform calibrates. np3 edge (if np2 lands near
but not above #1): cache-stable deterministic LOSSLESS dedup ([[BLOCK N]] back-ref) for ratio bonus without breaks. m12 LIVE; m26 stays live as current best.

## 13. np2 SCORED #2, WINS Pair(E,M)+Single-M = 14.3% — BEAT-THE-KING plan (target HARD → Overall 57%) (2026-06-27)
np2 (5CPbtf) SCORED **#2 of 64, total 0.684 (E1.052/M0.849/H0.173)**; WINS **Pair(E,M) 0.951 + Single-M 0.849 = 14.3% of the pool**
(from m12's 0% post-regime). Lighter cap 6k→16k recovered Medium 0.620→0.849 (+0.229), Easy held (~tied #1), NO under-compression
penalty. np2 = OUR LIVE BEST (m26/np1 #4 0.610, m25 0.449, m12 0.130 LIVE).
**BEAT-THE-KING MATH (king = 5DCnA57, Overall #1, 0.703, 71.4%):** np2−king = E −0.015 / **M +0.130** / H −0.151 / Overall −0.019.
np2 ALREADY beats the king on Medium and ~ties Easy; the ONLY gap is Hard. With the Medium cushion, np2 needs Hard only
**0.173 → ~0.21-0.23 (+0.035 to +0.057)** to take Overall — NOT the king's 0.324; target ~0.22 is well below the field Hard ceiling
(~0.342). **⇒ ~1-2 Hard break-fixes from taking Overall (57% of the pool).**
**WHY np2 Hard is low (dissect):** the VERY biggest/deepest tasks (315 @2.57×, 296 @3.27×) STILL over-compress — their tool results
are >>16k so even the lighter cap shreds them → Hard breaks/fail-fail; + more wander (11 neg) from near-passthrough. The 6k→16k step
fixed MEDIUM-sized over-compression but NOT the >16k Hard results.
**np3 LEVERS (lift Hard ~+0.05 WITHOUT losing the E+M that wins 14.3%):**
- (1) **Higher cap on the biggest results** (24-32k) → keep >16k Hard results fuller → fewer Hard breaks. COST: more wander on typical
  (cushioned by +0.130 Medium lead + (2)).
- (2) **Cache-stable LOSSLESS DEDUP** ([[BLOCK N]] back-ref exact repeats; deep tasks repeat most across turns) → reduces total context
  → less cap pressure + less wander + claws back savings so the higher cap doesn't under-compress. Must be DETERMINISTIC/idempotent
  (else busts cache). Lossless → preserves E+M.
- (3) **Better extractive on the biggest results** (pin full traceback/relevant code, not just error/sig) → keep what the agent needs
  WITHIN the cap → fewer Hard breaks, NO wander tradeoff. Targeted but content-speculative.
- BEST first shot: (1)+(2) combined — higher cap keeps Hard-big fuller; dedup offsets the wander/savings, threading the flat-cap binary.
**CONTINUOUS PLAN (100h):** np3 (Hard→Overall) → offline-validate (cache-stable, lossless, preserves E+M, ratio) → Codex audit →
upload (separate hotkey; np2 LIVE) → read scored → tune. DEFEND 14.3% (np2 live; watch higher-E+M rival). Near-free Single-E
(np2 1.052 vs king 1.067, −0.015 → may flip on re-draw = +4.8%). HONESTY: Hard is partly agent-side (deep fail-fails) + ceiling ~0.34,
the cap-raise has a wander tradeoff — but the target is only +0.05 (1-2 break-fixes), cushioned by Medium.

## 14. Hard-break DIAGNOSIS + np3 BUILT (2026-06-27)
DIAGNOSIS (repetition analysis of 6 captured comp-108 trajectories): np2's Hard breaks are NOT from repeated content
(exact-dup big-block content only ~0-18%, avg ~10% -> DEDUP IS WEAK, not the lever). They are from big UNIQUE tool-result
blocks (24k-64k; 4 of 6 tasks have a unique block >16k) that np2's 16k cap SHREDS to 24-67% -> the agent loses critical
info -> Hard breaks/fail-fails. => the lever is KEEP THE BIG UNIQUE BLOCKS FULLER (a higher cap), NOT dedup.
np3 = upload_miner_np3.py (copy of np2, ONE change: NP_RESULT_CAP 16000 -> 28000). Keeps 24k blocks FULL, 56-64k to 28k (vs
16k). OFFLINE-VALIDATED: AST OK (TARGET_TOKENS/TIGHT_TOKENS intact after a rewriter bug was caught+fixed); 24k block 64%->100%,
56k 27%->48%, 64k 24%->42%; idempotent; output<=native (no inflation); 100% prefix-stable; 0 orphans. sha 74... (see registry).
TRADEOFF (platform-only): lighter -> more near-passthrough on typical -> more wander/inflation (np2 already had 11) AND
under-compression risk; the Hard gain (keep big blocks -> fewer Hard over-compression breaks) must outweigh. ADDITIVE BET:
np2 stays LIVE holding our 14.3% (Pair(E,M)+Single-M), so np3 can only gain (try for Overall 57%), never lose our income.
NEXT: Codex pre-upload audit (diff = only the cap; cache-stable/idempotence/no-inflation inherited; the wander/under-compression
risk is the real question) -> USER uploads to a separate hotkey -> platform settles Hard-gain vs wander-cost. If 28k over-shoots
(E/M drop from wander), tune down (24k); if Hard insufficient, the 56-64k blocks need better extractive (np4). m12 LIVE/untouched.

---

## §15 — Deep-dive: #1 5DCnA vs our portfolio (2026-06-27, detail snap 092038) — OVERALL gap is VARIANCE, not mechanism

**Setup:** detail page carries per-task token splits (input/cached/output `_with_compression` + `tokens_without_compression`)
+ `platform_score` (mean of `run_count`=5 runs) + pass flags. Computed over the 45 real (non-screener) tasks.

### A. Aggregate token economics + base-reward events
| miner | cache% | wtd/raw | wtd/base | out/task | pp | flip | break | ff | mean |
|---|---|---|---|---|---|---|---|---|---|
| #1 5DCnA | 91.9 | 0.410 | 0.346 | 60360 | 28 | 5 | 1 | 11 | 0.664 |
| np2 | 94.0 | 0.399 | 0.267 | 55261 | 27 | 5 | 2 | 11 | 0.612 |
| np3 | 93.9 | 0.398 | 0.287 | 56343 | 29 | 5 | 0 | 11 | 0.635 |
| np1/m26 | 94.0 | 0.401 | 0.245 | 54260 | 26 | 5 | 3 | 11 | 0.575 |

(wtd = 1·input + ⅓·cached + 3·output; base = tokens_without_compression. flip=fail→pass +2, break=pass→fail −4.)
**OUR cache% (94%) BEATS #1 (91.9%); our compression (wtd/base) is BETTER; np3 has the MOST pass-pass (29) and ZERO task-level
breaks vs #1's 1. On fundamentals np3 ≥ #1 — we are NOT mechanically behind.**

### B. Per-task #1-vs-np3: the edge is tiny and is RATIO+CONSISTENCY, not pass-rate
- #1 beats np3 by **+1.30 total across 45 tasks (+0.029/task)** — np3 WINS −9.10 worth, #1 wins +10.40, net +1.30.
- **0 of #1's edges are pass-rate** (they pass the SAME tasks); **all 11 are shared-pass score gaps** (same pass, #1 scores higher).
- np3-vs-np2 per-task is a WASH (median Δ −0.032); the Easy-category gap (np3 0.859 vs np2 1.052) is NOT a uniform cap effect.

### C. Smoking gun = RUN VARIANCE
`sympy-15349`: #1 +1.02, np3 **−1.09**, BOTH pass (T/T). A pass-pass mean of −1.09 ⇒ ~2/5 of np3's runs BROKE. But the block is 17k
(< np3's 28k cap) → **np3 didn't compress it differently than #1** → same input, np3 drew unlucky runs. Several other #1 edges
(django-12754, sympy-14531, django-13033) are the same: np3 passes but with variable/break-y runs dragging the 5-run mean.

### D. VERDICT — Overall is ~parity, lost to variance; REOPENS the attack (overturns §14's "need a new mechanism")
1. The gap to #1 (#1 0.697 vs np2 0.684 / np3 0.682) is WITHIN the run-variance we measured → a re-eval could flip Overall to us.
2. The lever is **CONSISTENCY** (kill np3's worst-run breaks on ~8 shared-pass tasks → recover the Easy the breaks drag down → win Overall),
   NOT a new high-E-AND-H compressor. #1 wins by being steady, not by passing more.
3. **Single-E** (m26 1.066 vs #1 1.067) = same story: at the frontier, coin-flip on re-eval; agent-variance-bound, marginal build headroom.
NEXT: characterize np3's variable-run tasks (which compress-engaged tasks break some runs) → is the break from over-compression (cap fix)
or agent-side (a re-eval/parallel-hotkey play)? That decides whether the Overall lever is a cap tweak or a consistency/resubmit strategy.

### E. PER-RUN STABILITY (the real lever) — task-level "0 breaks" hides run-level -4s
Detail page gives only the 5-run MEAN. Scoring math lets us infer breaks rigorously: break=-4 (λ=0), lowest non-break run = ff -0.2
⇒ any task mean < -0.2 REQUIRES break-runs; `min_breaks = ceil(-5·mean/4)` is a hard lower bound (no calibration).

| miner | rigorous min -4 break-runs (45 tasks) | tasks mean<0 | clean-run mean (PS≥0.5) |
|---|---|---|---|
| #1 5DCnA | **9** | 6 | 1.157 |
| np2 | 14 | 11 | 1.170 |
| np3 | 11 | 9 | **1.206** |
| np1/m26 | 11 | 7 | 1.108 |

**KEY: #1 wins Overall PURELY by breaking less (9 vs np3's 11). On clean runs np3 scores HIGHER (1.206 > 1.157) — we out-compress
#1; we just break more.** Stability is the whole game. Trend: HEAVIER compression → MORE breaks (np2 16k=14 > np3 28k=11 > #1 lightest=9).
np3's break-y baseline-pass tasks split: OVER-COMPRESSION (sympy-16792, django-13033/12050/14122 at ~0.4× base — np3 broke, #1 kept
light & passed 1.16-1.36 → CAP-FIXABLE) vs AGENT-VARIANCE (sympy-15349 at 1.04× — np3 didn't compress yet broke 2/5 → irreducible luck).

**PLAY for Overall = SIZE-TIERED np4:** keep compressing MID results (our clean-run bonus edge, 1.206) but PASS HUGE results through
(kill the over-compression breaks #1 avoids on those exact tasks). Target np3 breaks 11→~7 (< #1's 9) at our higher clean-mean → win
Overall. Accept the ~2 agent-variance breaks (re-eval floor). This is the mechanistic basis for size-tiering (vs the earlier block-size hypothesis).
NOTE: tension — compress more = higher bonus but more breaks; #1 picks low-break/low-bonus, np3 picks high-bonus/more-breaks (≈tied Overall).
Size-tier aims to get BOTH (bonus on mid, stability on huge). Validate offline (prefix-stable/idempotent/≤native) + Codex pre-upload audit before any hotkey.

---

## §16 — np4 = np2 + cache-stable lossless DEDUP: BUILT, validated, NO-GO (cache bust). 2026-06-27
GOAL: #1 beats us on Overall by run-stability not compression (§15-E: our clean-mean 1.206 > #1 1.157). #1 is near-pure-
passthrough → leaves duplicate-content savings on the table. Lossless dedup (replace a byte-identical repeated tool result
with the allowed `Same response as in [[BLOCK N]].` back-ref) should lift our clean-run ratio above #1 WITHOUT adding
breaks (lossless ⇒ no agent divergence) → flip Overall.
BUILD (upload_miner_np4.py): np2's 16k cap + `dedup_exact_results()` — EARLIEST occurrence = survivor (kept verbatim),
later exact (collapsed-ws) copies → back-ref; survivor labelled [[BLOCK i]] where i = its MESSAGE INDEX (stable as turns
append → no renumber, unlike the m12 rich dedup). Functional tests PASS: dedup correct, idempotent, ≤native, compliant
(only [[CMP]]/[[BLOCK N]]), back-refs resolve, 47% saved on a dup-heavy case.
**CACHE GATE FAILED (the decider).** prefix_stability turn-by-turn vs np2 (no-dedup baseline):
np2 ~99.6–99.8% every turn; np4 MATCHES np2 EXCEPT the dup-introduction turn where it **CRATERS to 16.2%** — labelling the
EARLY survivor changes the prefix from its index forward ⇒ **84% of the cached context invalidated that turn**, re-charged at
1× not ⅓×. One-time bust (~+33k weighted tok) > dedup savings (~13k) ⇒ **NET NEGATIVE under weighted tokens** = the regime's
"cache-busting compression scores negative" failure mode. ROOT CAUSE: a compliant back-ref REQUIRES a [[BLOCK N]] target, so
the survivor MUST be labelled; the survivor is EARLY (its content first appeared early) ⇒ labelling it busts the early/cached
prefix. No cache-safe lossless dedup exists (referencing without labelling is non-compliant; compressing the later copy is
lossy = just "compress more" = the break-risk we're avoiding). **VERDICT: NO-GO. Not uploaded. upload_miner_np4.py kept as a documented dead-end.**
IMPLICATION: with cap (zero-sum E↔H, §14), better-extractive (NO-GO §14), and dedup (cache-bust, here) all dead-ended, **no
compression lever cleanly beats #1's near-pure-passthrough on Overall under the cache-dominant regime.** #1's shape is near-
optimal. Our 23.8% (E+M corner via np2, M+H corner via np3) is the compression-lever CEILING. Beating #1's Overall (57%) =
out-executing its near-passthrough (marginal) or a re-eval VARIANCE win (the gap is 0.015, within run-variance). Single-E (0.001) same.

---

## §17 — OpenRouter provider research for qwen/qwen3-coder (2026-06-27, via /browse) — we're ALREADY on the best provider
Triggered by np2b's −0.555 crater (AtlasCloud allowed). Pulled the provider table for `qwen/qwen3-coder` (Qwen3-Coder-480B-A35B, 1M ctx):
| provider | CACHE hit | latency | tput | uptime | GPQA/TAU bench | token share | in/out $/M |
|---|---|---|---|---|---|---|---|
| **DeepInfra (Turbo)** | **~90%** | 0.47–0.82s | 16–43 | 99.67% | 62.5/49.5 | 57–81% | 0.30/1.00 |
| AtlasCloud | **0.0%** | 1.70s | 42 | 100% | 63.0/47.0 | 6.9% | 0.78/3.80 |
| Venice | 66.9% | 0.85–1.09s | 14 | 93.65% | 63.0/45.8 | 2.3% | 0.35/1.50 |
| NovitaAI | 8.3% | 2.21s | 20 | 99.99% | – | 32.3% | 0.38/1.55 |
| Weights&Biases | 7.1% | 3.66s | 40 | 99.92% | 65.6/47.7 | 0.9% | 1.00/1.50 |
| Alibaba OSS | 0.0% | 1.08s | 44 | 99.91% | – | 0.1% | 0.975/4.875 |
| Google Vertex | – | 2.92s | 25 | 77.60% | – | – | 0.22/1.80 |

**Decisive finding: model QUALITY is ~equal across providers (GPQA ~62–66%, TAU ~46–50%, tool-call err all <0.7%). The one column that
differs by 10× is CACHE HIT RATE — DeepInfra ~90% vs AtlasCloud 0.0%.** Under the weighted-token regime (cached = 1/3×), cache hit
rate IS the score for a cache-stable miner. AtlasCloud's 0% cache (+ re-processing the full context every turn → slow → likely
timeouts on long Medium tasks) is what cratered np2b — NOT a dumber model.
**⇒ We are ALREADY on the right side of the lever.** np2's measured 94% cache matches DeepInfra (~90%), so the good account effectively
routes to DeepInfra (the default: cheapest, fastest, best cache, 57–81% token share). Our 23.8% reflects GOOD routing — we are NOT handicapped.
**So the provider lever is mostly DEFENSIVE, not a path past #1:**
- DEFEND: ensure ALL our accounts IGNORE AtlasCloud + the 0%-cache providers (Alibaba OSS) so we never accidentally crater like np2b.
- MARGINAL UPSIDE: if the good account uses Balanced routing, it may occasionally hit a non-DeepInfra (lower-cache) provider → a hidden
  source of break/variance. PINNING DeepInfra (OpenRouter "Exacto" / provider order=[DeepInfra]) removes that roulette → possibly a few
  fewer breaks. TEST on a FRESH hotkey (never re-route the live 23.8% blind). The gap to #1 is only 0.013, so even small consistency gains could matter.
- HONEST: quality is equal across good providers + we're already on the best one, so there is NO "smarter provider" to unlock. The 0.013
  gap to #1 is most likely genuine run-variance / #1's marginal edge, not a provider we're missing. Provider routing rules OUT "we're handicapped"; it is not a free 0.05.

---

## §18 — np5 = NEAR-PURE-PASSTHROUGH Overall-challenger (Bet 1). BUILT + offline-green 2026-06-27
Premise (§15-E + §16-17): #1 (0.697) beats us on Overall PURELY by run-stability (9 breaks vs our 11-14); quality/provider/compression
all ~equal; we've never fielded a near-pure-passthrough (np2/np3/m26 all extractive-CMP big results → byte-change → divergence → breaks).
np5 = np2 lineage, NP_RESULT_CAP 16k→**48k** = the untested near-passthrough cap region = #1's winning shape.
KEY DESIGN: Easy tasks have SMALL results (<16k) → np5 treats them BYTE-IDENTICALLY to np2 → inherits np2's HIGH Easy (~1.05), NOT
np3's anomalous 0.859 (that was Easy-draw VARIANCE — np2/np3 treat Easy tasks identically). np5 diverges from np2 ONLY on big
(Medium/Hard) results, keeping them fuller → fewer over-compression breaks (+Hard) at a slight Medium-ratio cost. NET BET: np2's Easy +
fewer breaks + higher Hard → Overall toward/past #1's 0.697. ADDITIVE (wins no corner → can't cannibalize np2/np3's 23.8%).
OFFLINE VALIDATION (all PASS): compiles; only the cap constant changed (no dedup/passthrough extras); np5==np2 BYTE-IDENTICAL on
≤16k results (8k,16k) → Easy inherited; np5 keeps MORE on 24k/40k (24000/40011 vs np2's 16026) → the lighter-touch divergence;
≤native always; idempotent; compliant (only [[CMP]]/[[BLOCK N]]); **prefix-stability 99.9% = np2's (vs np4-dedup's 16% crater).**
48k = first cut, PLATFORM-calibrated (lighter 56-64k=fewer breaks/less ratio; heavier 40k=more ratio/more breaks). NEXT: Codex pre-upload audit → USER uploads fresh hotkey (good DeepInfra account).

---

## §19 — Lossless-redundancy measurement → the algorithmic search is EXHAUSTED (measured, not argued). 2026-06-27
Measured intra-message redundancy across 4049 distinct comp-108 tool results (9.2M chars): trailing-ws 0.0%, blank-run-excess
0.0%, consecutive-dup lines 0.4% → **LOSSLESS-SAFE TOTAL = 0.5%.** Aggressive/lossy (non-consecutive dup lines) = 6.7% more (7.1%
total) but lossy (changes structure → break risk). After λ=0.5 + cache dilution (1/3×), realized score gain from the lossless edge ≈ noise.
⇒ The lossless-compression lever (the one I argued was "non-break-trading") has NO FUEL on this task set — tool results are already clean.

**CONCLUSION — every algorithmic lever is now MEASURED and empty/dead:**
| lever | verdict | evidence |
|---|---|---|
| flat cap (param) | zero-sum E↔H, exhausted | §14, cap curve 6k/16k/28k peaks ~16k |
| better extractive | NO-GO (Hard content spread 22-63k) | §14 |
| cross-message dedup | cache-bust (84% prefix invalidated) | §16 |
| reasoning (CoT) compression | uncapturable (15k micro-msgs, mean 736c) | §17-pre |
| lossless redundancy removal | 0.5% fuel = noise | §19 (here) |
| provider routing | we're already optimal (DeepInfra ~90% cache) | §17 |
| breaks | variance-dominated, not code-controllable | §15-E |
**⇒ The 0.68-0.70 Overall ceiling is STRUCTURAL: #1's near-passthrough is near-optimal AND the data leaves no free algorithmic lever.**
Beating #1's Overall is NOT algorithmic. Remaining real paths: (1) np5 near-passthrough shape test (PENDING — the one live shot; could
edge #1 via fewer breaks or underperform); (2) VARIANCE harvesting (run the best shape on multiple GOOD-account hotkeys → Overall
element goes to the best draw); (3) DEFEND 23.8% (strong, 2nd on board) + NEXT-ROUND (propose a NEW allowed mechanism publicly to expand
the toolkit — the only way to unlock genuinely new algorithm space). STOP hunting compression algorithms — the well is measured-dry.

---

## §20 — Extractive SELECTION fragments badly → coherent/structure-aware selection (np6 proposal). 2026-06-27
User pushed back on "the well is dry": the cap is one knob, but the extractive SELECTION (what/how to keep within the cap) is a
SEPARATE, never-changed knob. CONFIRMED empirically. extractive_compress (upload_miner_np2.py:751) is LINE-BASED: pins
error/test/diff/sig lines + top TF-IDF lines, emits them in order with "…" at every gap. Applied to real break-task blocks (target 16k):
| break task | input | "…" gaps | avg contiguous run |
|---|---|---|---|
| django-14122 | 64k/1397 lines | 166 | 3.4 lines |
| django-12050 | 64k/1426 lines | 191 | 3.3 lines |
| sympy-20590  | 64k/1969 lines | 221 | 3.3 lines |
Output sample (django-12050): `def get_field_names_from_opts(opts): … def get_children_from_q(q): … class RawQuery: … def chain(self, using): …`
= it keeps function SIGNATURES and DROPS the BODIES → a table-of-contents skeleton, not usable code. For a coding agent fixing a bug,
this is near-useless → a PLAUSIBLE source of our compression-induced breaks (§15-E split: some breaks agent-variance e.g. sympy-15349,
some compression-induced e.g. the 0.4x tasks #1 passed). §14's "keeps 8/8 critical LINES" was MISLEADING — keeps the lines, shreds the CONTEXT.
PROPOSAL np6 = COHERENT / STRUCTURE-AWARE extractive: keep WHOLE load-bearing units (the function being touched, full traceback, full
failing-test body, full diff hunk) intact + drop whole boilerplate units — quality over quantity. A coherent 16k beats a fragmented 16k
skeleton for the agent. EXCITING COMBO: coherent + TIGHT cap (16k) = hard compression (ratio edge over #1) WITH usable context (fewer
breaks) → targets BOTH gaps (breaks + balance). Compliant (structure heuristics, no task-awareness/LLM), cache-stable (per-message
deterministic/idempotent), bounded (≤cap). CAVEATS: offline can't prove solve-rate/break reduction (platform-only); truly-spread Hard
(§14, content 22-63k) still can't fit any 16k coherent-or-not. GATE: Codex design review (this build-fork) BEFORE building.

---

## §21 — np6 hybrid coherent-extractive: BUILT (Codex GO-WITH-CHANGES), validated, NO-GO (≈np2). 2026-06-27
Built the Codex-approved hybrid (keep highest-confidence load-bearing UNIT coherent + np2 line-breadth + np2 fallback;
upload_miner_np6.py, np2's 16k cap). Compiles, cap=16k, fallback works (no-anchor → exact np2). BUT VALIDATION = ≈np2:
- 50% of >16k blocks have NO error/traceback/diff anchor → np2 fallback (no change).
- On the 50% anchored blocks, gaps barely drop: np2 ~162 → np6 ~158-159; and at anchor budget 0.4/0.7/0.9 → 158/158/157 (flat).
- Overall: mean "…" gaps np2 139 → np6 137; 75/127 blocks byte-identical to np2.
WHY ≈np2 (two structural reasons): (1) the coherent window expands only to blank-line boundaries → structurally SMALL (one
block), so a bigger budget fraction doesn't grow it; the breadth still scatters the rest. (2) DEEP WALL: the anchor is the
ERROR/traceback, NOT the code the agent must FIX — and we can't identify the right code unit without TASK-AWARENESS (banned).
So coherent selection can't target the needed content. VERDICT: NO-GO — np6 ≈ np2 offline → uploading reproduces np2's 0.684,
a wasted hotkey. Matches Codex's predicted disappointment ("reduces visible fragmentation but moves Overall by noise") + the
§15-E irreducible-variance floor. The fragmentation DIAGNOSIS was right + valuable; the FIX can't land within the no-task-awareness rule.

## ⇒ COMPRESSION-ALGORITHM SPACE EXHAUSTIVELY VALIDATED DEAD
cap (zero-sum §14) · better/coherent extractive (≈np2 §21, can't ID right content w/o task-awareness) · dedup (cache-bust §16) ·
reasoning (uncapturable §17) · lossless redundancy (0.5% §19) · provider (already-optimal §17). #1's near-passthrough is near-optimal;
the break-gap is irreducible variance + the task-awareness wall. REMAINING (non-algorithmic): np5 near-passthrough (PENDING, the
one live shot) · variance-harvest Overall (best shape × N good-account hotkeys) · DEFEND 23.8% · NEXT-ROUND (propose a new allowed
mechanism — the only way to unlock real new algorithm space, e.g. a compliant relevance signal that doesn't require task IDs).

---

## §22 — np5 (cap 48k near-passthrough) SCORED 0.25 = CRATER. USER RIGHT (cap, not provider). Bet 1 DEAD. 2026-06-27
np5 (5CZxaU, cap 48k, GOOD DeepInfra account confirmed by user) scored total ~0.25 (E0.420/M0.247/H0.124) vs np2 0.684.
I HYPOTHESIZED a provider crater (E should be ~1.05 if good provider). REFUTED by per-task detail: on IDENTICAL-TREATMENT tasks
(np5 output byte-identical to np2 — small results), np5 ≈ np2: django-13820 1.46≈1.47, django-12155 1.39=1.39, django-12143
1.16≈1.20, django-11333 -0.01≈-0.02 (+ high per-task variance: sympy-23824 np5 1.77 vs np2 0.43, sympy-14531 np5 -0.51 vs np2 1.32).
np5≈np2 wherever output is identical ⇒ SAME good provider (user was right). The crater comes ENTIRELY from the BIG-result tasks
where np5 diverges (keeps 16-48k results RAW vs np2 capping to 16k) → catastrophic agent WANDER → break.
**KEY: 48k is a CLIFF, not a gentle slope.** np3 (28k) = 0.682; np5 (48k) = 0.25. Keeping the 16-48k results raw makes the agent
wander/break catastrophically. NEAR-PASSTHROUGH IS CATASTROPHIC FOR US, not just suboptimal.
⇒ **Bet 1 (near-pure-passthrough Overall challenger) is DEAD, decisively.** When WE go lighter than np2, we don't approach #1's
0.697 — we fall off a cliff. #1's near-passthrough edge is NOT replicable via our cap. np2's 16k is the CONFIRMED cap sweet spot
(6k m26=0.610 / 16k np2=0.684 / 28k np3=0.682 / 48k np5=0.25). The cap's lighter side is a cliff.
CORRECTION: my "Easy<1.05 ⇒ provider crater" heuristic was WRONG for np5 — np5 DOES diverge from np2 on Easy tasks that have
16-48k results (Codex's "easy peaks 6-58k" 3c point), so its Easy can crater from the CAP, not the provider. The decisive test is
per-task on IDENTICAL-TREATMENT (byte-identical-output) tasks, NOT the Easy aggregate. m12/np2/np3 live = 23.8% untouched; np5 dead hotkey.

---

## §23 — Local cap-sweep around 16k (user request): 16k CONFIRMED sweet spot; small changes bad-to-neutral. 2026-06-28
Ran np14/np16/np20 × 4 big-result Pass tasks (django-12050, django-13033, django-14122, sympy-20590) × RUNS=2 (24 solves, e2c key,
run 2026-06-28_002514_H1M_pbatch). Per-category (Pass, 8 solves/cap):
| cap | resolved | broke | neg | note |
|---|---|---|---|---|
| np16 16k | 8/8 | 0 | 0 | ONLY clean cap |
| np14 14k | 7/8 | 1 | 1 | over-compression break (django-14122) |
| np20 20k | 7/8 | 0 | 1 | wander non-resolve (django-13033) |
⇒ 16k is the local sweet spot; a small change EITHER way (tighter 14k or looser 20k) each introduced one failure. No small tweak beats
16k. CONFIRMS the platform verdict (6k 0.610 / 16k 0.684 peak / 28k 0.682 / 48k 0.25 cliff). CAVEAT: 8 solves/cap (RUNS=2) — the single
failures are SUGGESTIVE not definitive (could be partial run-variance); token totals are confounded by trajectory length (broken/non-
resolved runs end early → fewer tokens, so np14/np20's lower avg_total is NOT a cleaner-compression signal). NET: the cap lever is
SETTLED at 16k (np2); small tweaks don't help. Local variant files upload_miner_np_14000.py / _20000.py are TEST-ONLY (not candidates).
NOTE: sweep ran on a user-pasted OpenRouter key (now exposed in chat) — user to ROTATE it.

---

## §25 — np_prop = PROPORTIONAL/ratio cap (the king's method). BUILT + offline-clean. 2026-06-28
The king's distinguishing pattern (§24) = uniform-light, never over-compress (ratio median 1.24x/max 2.02x/std 0.36) vs np2's
bimodal absolute cap (std 0.61, 9 tasks >2x up to 4x = our over-compression breaks). np_prop replicates it: instead of an ABSOLUTE
16k cap, keep NP_KEEP_FRAC (0.55) of EACH result floored at NP_FLOOR (10k) => uniform ~1.8x ceiling. upload_miner_np_prop.py
(cap_tool_result rewritten: target = max(NP_FLOOR, len*NP_KEEP_FRAC)).
OFFLINE VALIDATION (all PASS): compiles; proportional ratio confirmed (8k pass / 12k 1.27x / 20-64k UNIFORM 1.82x, never over-
compresses); IDEMPOTENT (the [[CMP]] guard prevents re-compression -> resolves the original author's "fractional cap churns the
prefix" concern); PREFIX-STABILITY 99.9% (cache-safe); compliant (allowed markers only); <=native.
HONEST RISK (the catch): np_prop COMPRESSES the small/mid results (10-16k) that np2 PASSES THROUGH -> via the SAME fragmenting
extractive (§20, signatures-without-bodies) -> could HURT Easy/Medium (np2's strength + our 14.3% income), where the king
presumably compresses COHERENTLY. So np_prop trades: FEWER big-result over-compression breaks (good for Hard) for MORE small/mid
fragmentation risk (risk for Easy/Medium). NET is platform-only. ADDITIVE Overall-challenger (np2/np3 hold the corners regardless).
NEXT: Codex design review (new MECHANISM, like np6) to red-team the fragmentation-on-small risk + whether proportional beats np2/the
king -> then local-test or upload. NOT a constant change — first genuinely new compression MECHANISM with a real basis.

---

## §26 — np_prop REVISED to the HYBRID (Codex GO-WITH-CHANGES). Built + validated. 2026-06-28
Codex design review of np_prop-as-proportional: GO-WITH-CHANGES — compress-everything would RELOCATE breaks (fragment the 10-29k
band np2 passes -> likely regress below np2, the np5/np6 dynamic). Endorsed the HYBRID: keep np2's EXACT behaviour for <=2*NP_CAP,
apply a 2x ceiling only ABOVE it. IMPLEMENTED (upload_miner_np_prop.py): cap_tool_result target = max(NP_CAP=16k, native*0.5).
VALIDATION (all PASS): BYTE-IDENTICAL to np2 for native <=32k (8k/16k/24k/32k: diff=0 -> Easy/Medium CANNOT regress, our 14.3%
protected); >32k kept at 50% (48k->24k=2x, 64k->32k=2x) vs np2's 16k (3-4x over-compression); IDEMPOTENT; PREFIX-STABILITY 99.9%;
compliant; <=native. So the hybrid is a SURGICAL fix: same E/M as np2 + huge Hard blocks kept at 50% (the king's never-over-compress
principle) -> targets the over-compression breaks WITHOUT the np_prop/np5/np6 risks. Wander risk LOW: 64k->32k keep is between np3's
safe 28k (scored 0.682, no crater) and np5's 48k (cratered 0.25), nearer np3. ADDITIVE Hard/Overall-challenger (np2/np3 hold corners).
NOTE on local-eval (Codex rec): the local cap-sweep (§23) showed np16 was 8/8 CLEAN on the big tasks -> local does NOT reproduce the
platform over-compression breaks -> a local test of the hybrid is likely INCONCLUSIVE (~np2 locally). The PLATFORM is the real test.
NEXT: quick Codex pre-upload confirm of the built code -> USER uploads on the good (47b/DeepInfra) key as an additive challenger; read Hard vs np2 + Easy~1.05 binding at scored.
