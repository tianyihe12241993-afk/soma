# Re-analysis from fresh raw data — 2026-06-29 (post-compaction)

**Trigger:** user asked to reanalyze all results + find creative solutions. Re-derived from the
fresh per-task platform dump `data/raw/dashboard/2026-06-29/044246_miner_detail.json` (king + np2 +
5GgVXz, 50 tasks each, full token splits + outcomes). Codex independently re-derived all 4 claims
(read-only). This CORRECTS the prior verdict's reasoning and CLOSES two creative levers.

## What the fresh data says (all Codex-verified)

### 1. The king is np2's TWIN; the 0.044 gap is RUN-VARIANCE, not a compression advantage. ✅
- Aggregate: king cache 93.8% vs np2 93.9%; mean baseline-pass compression 1.53x vs 1.52x;
  weighted-token ratio king/np2 = **1.036** → **np2 actually compresses slightly MORE efficiently** and
  still trails. So the gap is NOT savings/strategy.
- Gap decomposition (summed per-task king−np2 = 2.187): **66% (1.443) is on SAME-outcome tasks**
  (mostly both-pass-pass where the king just scores higher run-to-run), only 34% (0.744) from
  break/flip differences. Example: task 297 sympy-23262 — both "pass" but np2 −0.63 vs king +1.12
  (np2 had run-level breaks inside its 5-run average).
- **CORRECTION to prior verdict:** CLAUDE.md said "the king's gap is the BASE/outcomes term = breaks/flips,
  NOT savings." WRONG. It's 2/3 same-outcome run-variance between two near-identical compressors.
  **This is GOOD NEWS: the king's 0.728 is a lucky draw, mathematically beatable by best-of-N.**

### 2. Hard-specialist lever (the 14.3% Hard zone) is STRUCTURALLY DEAD for a compliant miner. ✅
- 5GgVXz (H0.676, wins Pair(E,H)+Single-H) flips only **6/16** Hard tasks vs np2's **5/16** — nearly the
  same COUNT. Its Hard edge = it compresses Hard **1.68x vs np2 1.53x** → more *runs* flip per task. It
  applies that aggression UNIFORMLY (E/M 1.77x, 5 breaks) → craters Medium to 0.252. Net total 0.586 < np2 0.684.
- So "compress harder → flip Hard" is directionally REAL (this is the inverse of the failed strelief,
  which kept MORE on failure-output). BUT to win the Hard zone without cratering E/M you need to compress
  Hard tasks harder than E/M tasks → you need a **Hard-vs-E/M discriminator**.
- **No such discriminator exists.** Tested every token feature (baseline tokens, output, input, output/total,
  output/input, compressed total): ALL have overlapping Hard-vs-E/M ranges, |Cohen's d| ≤ 0.81. Best
  threshold = 28% misclassification (Codex confirmed). This extends the ehspec NO-GO from "size" to ALL features.
- Failure-content as a per-message signal? Likely overlaps too (the agent hits test failures during
  iteration on E/M tasks it eventually solves, not just on Hard) + cache-stability risk if the cap depends
  on accumulated conversation state. Unvalidated and doubly risky.
- **Verdict:** Hard zone is only reachable by a SEPARATE uniform-aggressive sacrificial miner (own hotkey)
  that must beat 5GgVXz's Pair(E,H) 0.760 / H 0.676 — marginal, and a net-negative total. Low EV.

### 3. Easy-lift via tighter cap — REFUTED as a clean lever. ✅ (Codex attacked hardest)
- Hypothesis was: np2's 16k cap passes small Easy tasks through → low savings → E1.052 < king 1.105; a
  tighter cap lifts Easy. **But the savings proxy on pass-pass Easy is np2 0.556 ≥ king 0.552** — np2 is
  already AT/ABOVE the king on Easy savings. The king's small Easy lead is run-variance, not savings we can engineer.
- Asymmetry: one new Easy BREAK ≈ −0.29 to the Easy category mean = ~10× the 0.053 gap. Tighter cap is a
  bad bet (tiny upside, large break downside).

### 4. E/M category boundary is fuzzy + UNNEEDED. ✅
- "Hard = baseline-fail, exact" (CLAUDE.md) is overstated: published Hard vs baseline-fail mean — king Δ0.008,
  np2 **Δ0.053**, 5GgVXz Δ0.034. Three on-disk category maps disagree (FIT vs eval-trace vs baseline-fail).
- **Doesn't matter:** the platform publishes each miner's Easy/Medium/Hard means in `category_scores`. We read
  element wins directly at scored. The map only mattered for building a category-targeted compressor — which #2 killed.

## Net: the play is unchanged but now confirmed + sharpened
The compression algorithm is genuinely exhausted (we already match/beat the king per-token; no Hard
discriminator; Easy gap isn't savings). **Best-of-N variance draws remain EV-max** — and the twin/variance
finding RAISES confidence (the king is a beatable draw, not a better algorithm). Codex's independent pick: (a) pure best-of-N np2 redraws for Pair(E,M).

**Sharpened recommendation:**
- The real scaling knob = **number of simultaneous live clean draws** (winner-take-all → our score on each
  element = MAX over our live hotkeys). Each funded DeepInfra+Venice account = one more lottery ticket on
  Pair(E,M) (gap 0.017) + Overall (gap 0.044). Run as many np2 draws as accounts allow; keep np3 for Pair(M,H)/Overall.
- Read each draw at scored from published `category_scores`: Easy≥0.85 binding (else starved/discard) → E+M>0.968 (reclaim Pair(E,M) → 23.8%) / total>0.728 (Overall).
- DON'T build more compressors (5 builds + this dive + Codex = exhausted). DON'T chase Easy-lift or a Hard specialist as primary.
- Secondary, optional, can't-hurt-floor: a uniform-aggressive Hard-zone draw on a spare hotkey ONLY if accounts are spare — must beat 5GgVXz Pair(E,H) 0.760; low EV.
