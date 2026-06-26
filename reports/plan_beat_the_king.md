# PLAN: Beat the king (comp-108) — grounded + adversarially verified (2026-06-24)

_Produced by a 14-agent workflow (4 ground -> 3 design -> judge -> 5 red-team -> synth). Two red-team attacks LANDED (Hard-regression, cannot-validate) and amended the plan. HONEST HEADLINE: caching/stability ALONE does NOT beat the king (breaks are content-driven, H1; even the king breaks 6-7/250 at 88% cache). AOW-lite is a Hard-SAFE first step that ~3x our share (4.8%->~14%) via the cache mechanism; reaching #1 needs the separate content-RETENTION work._

# FINAL PLAN: BEAT THE KING (comp-108, SN114 CoT-Compression)

## THESIS

The king (0.957) and m12 (0.768) ship **the same ~999k total content per run** — our capability is already there. The gap is **structural, not qualitative**: the king converts ~85% of its context to a byte-stable *cached* prefix (132k fresh input), while m12 re-derives its entire compressed history every turn (429k fresh input), churning the prefix so the provider can't cache it. We close the gap by making m12 emit **byte-identical frozen bytes for already-compressed turns** instead of recomputing them — copying the king's *mechanism* without touching m12's *content* (the Hard moat). This does not make us #1 on its own (the 76% Overall cliff needs ≤6 breaks, and stability delivers only ~4-5 break-fixes), but it triples-to-quadruples our incentive share to ~14-19% on the highest-confidence lever we have (cache), and lays the only safe foundation for the content-retention work that reaches #1.

---

## THE CONCRETE BUILD — "AOW-lite" (Append-Only-Window, harvest-only)

**File:** `/Users/user/SOMA/miner/cot_compression/upload_miner_m7_compliant.py`. m12 stays LIVE and untouched; the candidate is a **separate copy** uploaded under a **second hotkey**. Uploads/pushes are done by the USER.

### What changes (additive, ~40-70 lines, no edit to either compression body)

1. **State (additive, `save_state` 347-378 / `load_state` 335-344):** add `"frozenPrefix": list` (already-compressed, frozen harvest-output messages) and `"frozenSourceCount": int` (raw high-water mark consumed into the prefix). Missing/malformed → `[]`/`0` (old m12 state simply starts fresh-freezing this run). Surface both in `resolve_stateful_messages` `extras` (386-391).

2. **Boundary (new, ONLY in the harvest branch 1366-1393):**
   ```
   total = len(raw_messages)
   verbatim_start = max(frozenSourceCount, total - WINDOW_MSGS)
   verbatim_start = snap_back_to_call_boundary(verbatim_start)   # reuse find_call_index (1071-1080)
   newly_evicted = raw_messages[frozenSourceCount : verbatim_start]
   verbatim_tail   = raw_messages[verbatim_start:]
   ```
   `verbatim_start` is monotonic non-decreasing → the frozen region only grows, append-only **by construction** (cleaner than lazy per-message freeze).

3. **Compress-once-on-eviction:** run the **unmodified** `compress_structurally` on the closed historical region, take the suffix for `newly_evicted`, splice onto `frozenPrefix`. Selection logic byte-for-byte unchanged.

4. **Emit:** `result_messages = [*frozenPrefix, *verbatim_tail]`, then the existing orphan-guard (1378-1383), empty-guard, loop-guard (1390-1392), and **never-inflate guard run AFTER reassembly**.

5. **Ratio watchdog (RED-TEAM #2 FIX):** because the frozen prefix is never re-pruned, on very long harvest tasks `[*frozenPrefix, *verbatim_tail]` could exceed what m12's whole-set re-prune would ship — a *token/ratio regression* (it shows MORE correct content, never wrong content). Guard: if the reassembled size exceeds m12's would-be harvest budget by > a set margin, re-run `compress_structurally` on the whole working set for that turn (accept a one-turn cache bust). Self-healing, bounded; enforced by the existing REJECT-on-ratio gate.

### What stays UNTOUCHED — the Hard moat
- `compress_gently` (RICH) is **byte-for-byte m12**. Passthrough is unchanged. Dedup, loop guard, markers, escalation — unchanged.
- We do **NOT** add any superseded-view / blind-truncation lever (the m20b-v2 trap that dented Hard).
- **Phase 2 (rich-path freeze with stable `[[BLOCK N]]`) is NOT in scope until Phase 1 proves cache-lift + Hard-hold on platform.**

### RED-TEAM #4 AMENDMENT — Hard is NOT automatically safe; gate freeze hard
The "rich is byte-identical → Hard is bit-identical" claim is **FALSE** and I confirmed it: (a) **98/248 runs run at <45 agent-steps → execute entirely in harvest** (the path AOW-lite rewrites), and Hard pass-runs live there; (b) mode is sticky `passthrough→harvest→rich` (line 1345), so **every Hard run passes through harvest first**, and `working = [*state["messages"], *new]` (419) feeds the AOW-frozen prefix INTO `compress_gently` — so even rich-routed Hard runs get a non-native input. Therefore:
- **Persist an `everTouchedRich` flag.** Apply freeze **only** when `mode=="harvest"` AND the session has **never** escalated to rich. Once rich fires, hard-disable freeze for that session forever (revert to live-m12 behavior). This removes the state-contamination channel into `compress_gently`.
- This still leaves direct exposure on pure-harvest Hard tasks — which is exactly why the validation gate (below) **REJECTS on a single new Hard break**, not on an aggregate H drop.

### Compliance
Runs `scripts/check_prompt_compliance.py` before upload — clean by construction (no new markers, no new strings, no task/category branching, mode keys only on transcript shape, determinism: content-only freeze, no `randomUUID`/timestamp wrapper bytes). Both m12 and the candidate currently PASS.

---

## EXPECTED OUTCOME (anchored to official m12 E0.412 / M0.953 / H0.919, total 0.768, share 4.8% = Single-Hard only)

**RED-TEAM #1 RE-ANCHOR:** the value thesis is the **cache lever**, NOT break-fix. Break-reduction is treated as **unmodeled upside**, not a load-bearing assumption. (m20b-v2 proved the cache mechanism is not strictly upside-only — it ADDED +4 breaks via content-stub; AOW-lite has no stub, but "provably zero new breaks" is unproven, so we do not claim it.)

| Metric | m12 baseline | AOW-lite most-likely | Source |
|---|---|---|---|
| Cache fraction (harvest tasks) | ~55% | ~70-80% | feasibility verdict (k≈0.37 cached weight, empirical) |
| Weighted ratio | 2.96× | ~3.4-3.8× | headroom (b) rows |
| Break-runs | 17 | ~12-14 (LOW conf, upside) | break verdict (freeze touches ~4-5) |
| **Hard** | **0.919** | **0.919 flat** (floor held) | rich untouched + everTouchedRich gate |
| **Medium** | **0.953** | **~1.05-1.13** | headroom: 17→14 breaks → M≈1.13 |
| **Easy** | **0.412** | **~0.41** (dead lever) | only 2 of 17 breaks; king E0.858 unreachable |

**Elements we take from the king:**
- **Pair-MH (king 1.004): the cheapest, most-likely win** — needs only 17→14 breaks (MH 1.022) OR the cache bump alone (headroom row (b) cache→3.61× → H0.983, M1.029 → MH≈1.006). **Most-likely landing: Pair-MH + held Single-Hard ≈ 14.3% of pool — a ~3× share increase.**
- **Upside (optimistic, 17→~10 breaks): Single-Medium (king 1.281, needs M>1.281) + Pair-MH + Single-Hard ≈ 19.1%.**

**Honest confidence:** Cache lift — **HIGH** (king/newking already prove it on identical content; 157/234 local runs show nonzero cacheRead; mechanism verified). Break-fix to king level — **does NOT happen** (need ≤6, stability gives ~12-13). **Beating the king outright (Overall, 76% cliff) — NO, not with this change alone.** This is the correct, Hard-safe foundation that captures the king's mechanism and triples our share; reaching #1 requires the separate content-RETENTION work to kill the residual ~8-11 H1 Medium breaks.

---

## VALIDATION PLAN — and addressing "can we even validate?" head-on (RED-TEAM #5)

Red-team #5 is **correct and decisive**: a 3-5 break-fix (+0.06 to +0.11 Overall) is **smaller than single-read noise** (Overall sd≈0.098; break count 17/250 = 6.8% ±3.1% → a re-read of the *identical* miner yields 9-24 breaks). **A single 250-run absolute comparison cannot tell success from noise, and the "any Hard-break ⇒ REJECT" gate would false-reject a genuinely-safe miner.** Therefore we **do NOT gate on score-lift.** We restructure validation around two things noise cannot hide:

1. **PRIMARY GATE = the cache mechanism, observed in ONE read (near-deterministic, high-confidence).** The load-bearing lever is cache, and it is directly visible per-run: `cached_input_tokens_with_compression` and `input_tokens_with_compression` (fresh). **Success = on harvest-routed tasks, fresh-input drops toward the king's profile (m12 429k → target <250k aggregate) and cache fraction rises toward ~80%.** This is mechanism verification, not score resolution — it does NOT need 10 reads. If cache rises and content is byte-frozen, the weighted-token win is a near-arithmetic certainty (the score delta is just hidden by the local harness's un-discounted `total_tokens` — the known m13/m20b-v2 trap, which is exactly why we validate **on-platform only, never local-only**).

2. **PAIRED A/B for the score/break check (cancels the dominant provider-window noise).** Score the candidate **and a fresh m12 re-read in the SAME provider window**, compare **per-task differences** (paired bootstrap), restricted to the **harvest-routed Medium subset** where the lever acts (denser signal). This cancels the ±0.3 Hard / ±0.18 Medium window swing that the absolute comparison cannot. Pre-commit to **N≥3 paired reads** to clear ~1 sd (~150 agent-hrs floor — accepted).

**Validation rules (non-negotiable):**
- **Second hotkey, same OpenRouter account. m12 LIVE/untouched throughout.**
- **ONE variable only** (AOW-lite vs m12; nothing else changes).
- **Platform-SCORED only** — never `evaluating`, never local-only.
- **Per-task break check (RED-TEAM #1):** explicitly confirm AOW-lite's harvest splice did NOT add break-runs on the 12 Medium / 3 Hard break-prone tasks before any Phase-2 consideration.

---

## RISK & KILL CRITERIA (protecting Hard 0.919 above all)

| Risk | Guard / Kill criterion |
|---|---|
| **Hard regression (existential — Single-Hard is our only guaranteed 4.8%)** | `everTouchedRich` gate (no freeze once rich fires) + rich path byte-identical. **KILL: any single NEW Hard break** on the per-task paired check (not an aggregate H drop — losing Single-Hard at 2 breaks is net-negative regardless of Medium gains). |
| **Splice adds a Medium break** (AOW changes which bytes are sent first) | Orphan-guard (1378-1383) + call-boundary snap (worst case = no-op revert to m12). **KILL: net break-run increase** on the harvest Medium subset (paired). |
| **Ratio/token regression** (frozen prefix never re-pruned) | Ratio watchdog (re-prune on margin breach) + never-inflate guard after reassembly. **KILL: avg ratio does not improve / regresses** (experiment_backlog gate). |
| **Cache lift fails to materialize** | PRIMARY gate is the cache observation itself. **KILL: fresh-input / cache fraction does not move toward king profile** on harvest tasks in the first read → the thesis is falsified, abort. |
| **Validation can't resolve signal** | Addressed by mechanism-gate + paired A/B. **If even the cache mechanism is ambiguous after 1 read, do NOT promote.** |

**Hard protection summary:** rich is byte-identical; `everTouchedRich` blocks state-contamination into rich; freeze acts only in pure-harvest; and the kill criterion is a single Hard break, not an aggregate. We never trade a Hard pass for a Medium gain.

---

## SEQUENCED STEPS (each independently checkpointed)

1. **[AGENT]** Copy m12 → new candidate file `upload_miner_aow_lite.py`. Implement AOW-lite: state fields, boundary, compress-once-on-eviction splice, `everTouchedRich` gate, ratio watchdog. No edit to `compress_gently`/passthrough. `make checkpoint NOTE="aow-lite implemented"`.
2. **[AGENT]** Run `scripts/check_prompt_compliance.py` on the candidate → must PASS. Diff against m12 to prove `compress_gently`/passthrough are byte-identical. Checkpoint.
3. **[AGENT]** Local sanity-only (NOT a gate): confirm it runs, produces valid output, prefix is byte-stable turn-to-turn on a replay trace (the one thing local CAN show). Explicitly note local does NOT reproduce the platform score (m13 trap). Checkpoint.
4. **[USER]** Upload candidate under the **second hotkey** (same OpenRouter account). m12 untouched. Confirm hotkey↔version in `config/miners.yaml` + `reports/label_mapping_audit.md`.
5. **[AGENT]** After scored (never `evaluating`): scrape per-run, **PRIMARY GATE** — verify cache fraction ↑ / fresh-input ↓ toward king profile on harvest tasks. If no movement → KILL (thesis falsified). Checkpoint + record in `state/DISCOVERIES.md`.
6. **[USER + AGENT]** Trigger a **paired m12 re-read in the same window**; **[AGENT]** run paired-bootstrap on the harvest Medium subset + per-task Hard break check. Repeat for **N≥3 paired windows**. Checkpoint each.
7. **[AGENT]** Decision gate: PROMOTE only if (cache lift confirmed) AND (no new Hard break) AND (no net Medium break increase) AND (ratio improved). Record verdict in `reports/` + `state/DECISIONS.md` + `state/SCOREBOARD.md`.
8. **[USER]** If promoted and we want it live, swap the candidate to the primary hotkey (or keep dual). Only on explicit instruction.
9. **[AGENT, conditional]** If Phase 1 lands (cache up, Hard held), scope **Phase 2**: rich-path freeze-on-emit with stable `[[BLOCK N]]` (persisted content-hash→N map + monotonic counter; assert every back-ref resolves else keep full). Separate candidate, same validation gauntlet. This is the path toward the residual Medium break-retention work needed for #1.

---

## FALLBACK (if freeze-on-emit's break benefit proves weak — the expected case per the break verdict)

The plan **already assumes** break-fix is weak; the cache win (Pair-MH ≈ 14% share) stands on its own and is the success criterion. If breaks do not drop at all:
- **AOW-lite still wins Pair-MH purely on cache** (headroom row (b): cache→3.61× → H0.983/M1.029 → MH≈1.006 > king 1.004) with Hard held — **promote it; banking the 3× share increase.**
- **Then pivot to the real #1 lever: content RETENTION, not derivation-freezing.** The residual ~8-11 H1 Medium breaks need the king's actual edge — keeping MORE/BETTER content as a stable cached history (not re-dropping it), so the agent stops losing the code it patches against. This is the Phase-2+ research direction (m7-style deeper PASS-SAFE retention backed by per-task evidence), validated identically on the second hotkey. The 76% Overall cliff (≤6 breaks) is reachable only through that retention work, never through caching alone.

**Decision: execute AOW-lite now.** It is the highest-confidence, lowest-risk, Hard-safe step that captures the king's mechanism, and the only one of the candidate designs that guarantees the 0.919 floor by not touching the bytes that produce it.

Key files: candidate target `/Users/user/SOMA/miner/cot_compression/upload_miner_m7_compliant.py` (`compress_structurally` 1083-1290, `compress_gently` 955-1060 [UNTOUCHED], `resolve_stateful_messages` 381-431, `save_state`/`load_state` 335-378, mode gate 1337-1348, `find_call_index` 1071-1080); scoring `/Users/user/SOMA/mcp_platform/app/api/routes/scoring.py`; compliance gate `/Users/user/SOMA/scripts/check_prompt_compliance.py`; per-run data `/Users/user/SOMA/data/raw/platform_results/2026-06-24/{m12_5Dz7,newking_5Ggq}_perrun.json`; m20b-v2 contrast `/Users/user/SOMA/miner/cot_compression/upload_miner_m20b_v2.py`; category map (approximate) `/Users/user/SOMA/config/comp108_category_map_derived.json`.
---

## UPDATE 2026-06-24 (~23:55) — AOW-lite BUILT + verified; result FALSIFIES the freeze thesis (key learning)
File: miner/cot_compression/upload_miner_aow_lite.py (m12 UNTOUCHED; compliance PASS; rich/passthrough/
compress_structurally/compress_gently + 46 helpers byte-IDENTICAL; only harvest+state+2 new fns differ).
Verification (6-agent workflow wy0z7htd0): runs ✓, everTouchedRich gate ✓ (Hard protected, byte-exact m12 once
rich), determinism ✓, fallbacks ✓ — but **prefix_stable = FAIL: AOW-lite delivers ZERO cache advantage; its
output is byte-identical to m12 across all 40 tested harvest turns.**

ROOT CAUSE (architectural, verified): m12's "prefix churn" is NOT wasteful re-derivation — it is m12 legitimately
DROPPING the oldest interactions to hit its 8k target. A frozen prefix that outlives an m12 drop is necessarily
LARGER (nominal) than m12's re-pruned output. So freeze and the "never ship worse ratio than m12" watchdog are
MUTUALLY EXCLUSIVE in steady-state harvest: the watchdog fires on every drop-turn and reverts to m12. (A latent
no-op bug — freezing past the first user message made compress_structurally no-op the live region, +11% tokens —
was also found and fixed; doesn't change the conclusion.)

THE DEEPER INSIGHT (this is the real lever): the watchdog compares NOMINAL tokens, but SCORING uses WEIGHTED
tokens (cached @ ~0.37x). The KING wins cache by shipping a STABLE prefix that is nominally LARGER but ~85% CACHED
→ lower WEIGHTED. Our "never nominally worse than m12" safety rail STRUCTURALLY FORBIDS the winning move. m20b-v2
already proved freezing DOES cache (83%) — it only lost because it STUBBED content (broke tasks). AOW-lite keeps
m12's content (no stub), so loosening the watchdog would get m20b-v2's cache WITHOUT m20b-v2's break-loss.

=> AOW-lite-as-built (safe watchdog) = provably == m12 = pointless to ship. The WIN requires a real BET: ship the
stable frozen prefix, ACCEPT higher nominal tokens, bet the cache discount (king 85%, m20bv2 83% — materialization
confident) makes WEIGHTED lower. Hard stays protected by everTouchedRich (unchanged). Risk = harvest-task RATIO
only (Easy/Medium savings component), validated ONLY on-platform (cache invisible locally), m12 = safe fallback.
DECISION PENDING (user): make the cache BET (loosen watchdog on the built file → 2nd hotkey) vs hold.

---

## UPDATE 2026-06-25 (~01:40) — CACHE BET hits a STRUCTURAL WALL (decisive; stop bolt-on freezing)
AOW-bet fix (rebaseline savings to cumulative-original) was VERIFIED under the realistic REWRITE connector model:
- prefix_stable = PASS — aow 0.927 stable-frac vs m12 0.658, strictly more stable, freeze accumulates, aow != m12.
  THE CACHE PROPERTY IS NOW ACHIEVED. Hard-safe ✓, deterministic ✓, compliant ✓, engine byte-identical ✓, m12 untouched ✓.
- positive_savings_vs_original = FAIL (DISQUALIFYING). To be byte-stable, AOW holds the prefix at FULL FIDELITY and
  only compresses the last 8 msgs; that tail is < TARGET_TOKENS so compress_structurally no-ops -> AOW emits the
  ENTIRE uncompressed native trajectory: 0% nominal savings on every harvest turn (held grows to 42k+ tok by turn 22),
  vs m12's 15-84%.

WHY THE BET FAILS EVEN WITH CACHE (the math): at turn 22 AOW weighted ≈ 6k fresh + 0.37×42k cached ≈ 22k; m12 weighted
≈ 7k (dropped to target). Keeping the full growing trajectory costs ~2-3× MORE weighted tokens than m12's bounded
drop, EVEN at the 0.37× cache discount. The cache discount cannot offset a 6× larger retained content.

THE KING'S ACTUAL PROFILE (now fully understood): king TOTAL tokens ≈ m12 (999k vs 994k) — it does NOT keep an
unbounded full-fidelity trajectory. It compresses to a BOUNDED size like m12 BUT keeps that compressed content
BYTE-STABLE across turns (85% cached). So the king does BOTH: bounded compression AND stability. m12 has
bounded-but-CHURNING (re-decides drops globally each turn, escalation tightens -> prefix shifts -> 55% cache).
AOW-bet has stable-but-UNBOUNDED (0% savings). You cannot bolt stability onto m12's GLOBAL/context-dependent
compression — the compressed bytes for turn K change as the trajectory grows.

REQUIREMENT TO MATCH THE KING (the only path, and it is a RE-ARCHITECTURE, not a bolt-on): per-turn DETERMINISTIC
compression — compress each historical turn to a FIXED budget using ONLY that turn's content (context-independent),
so the compressed bytes for turn K are IDENTICAL every turn -> the prefix is BOUNDED (each turn capped) AND STABLE
(byte-identical) -> cached. This is "Design 3 / deterministic-prefix" from the original panel. It rewrites
compress_structurally's global drop/escalation logic into per-turn budgeting (loses cross-turn dedup + global
optimization — a real risk), and is still platform-validation-only for the cache benefit.

VERDICT: freeze-on-emit / AOW is DEAD (two builds, both proven == m12 or 0%-savings). The cache lever is REAL and
its best case is still only ~14% share (Pair-MH), NOT #1. Capturing it requires the deterministic-prefix
re-architecture (multi-day, platform-validated bet). Candidates upload_miner_aow_lite.py / upload_miner_aow_bet.py
retained as reference (both safe, both no-gain). m12 (5Dz7) LIVE/untouched at 4.8%.
