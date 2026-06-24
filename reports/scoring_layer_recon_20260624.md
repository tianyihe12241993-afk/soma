# Upstream scoring-layer recon — does an incoming change favor our M+H profile? (2026-06-24)

User asked: dig into the in-flux scoring layer for a formula change that would favor m12 (M+H strong, Easy weak).
Source: DendriteHQ/SOMA (the platform repo, `mcp_platform/app/api/routes/scoring.py`), checked via `gh`.

## Answer: NO incoming change favors us. But the recon revealed the exact formula, which is decision-useful.

## What's ACTIVE (merged) vs DORMANT
- **MERGED TODAY 08:55 UTC — PR #157 `fix/scoring-penalty`** ("negative penalty value mismatch fix",
  `scoring.py` +31/−28). It is a **consistency fix**: `raw_total_score` for the penalty summary now uses the
  mean of ALL run scores (`_build_swe_raw_scores`) instead of the mean-of-category-means, so raw and
  penalty-applied totals reconcile. **NOT a category reweighting.** Does not favor M+H or Easy.
- Recent merged: a95a06c (frontend screener-flag fix), 9301a74 (task names in aggregate), 11f54f5 (configurable
  screener token weights), 100c884 (weighted-savings gate). All consistency/plumbing, no reweighting.
- **`validator/llm-semantic-scoring` is DORMANT** — last commit 2026-04-27 (2 months stale). This is the ONLY
  branch that could fundamentally change scoring (LLM judges semantic pass vs exact test-pass). It is NOT
  imminent. Other branches (`feat/vali-scoring-reliability` Apr, `weight-hot-fixes` Jun-09, `scoring-display-fix`)
  are validator weight/emission/display mechanics, not category scoring.
- Open PRs (#158 weighted-tokens-on-frontend, #154 copilot, #142 failed-review-handling) — none reweights scoring.

## THE FORMULA (now precise — confirmed from scoring.py)
Per-task raw score: break = −4, both-fail ≈ 0, pass-pass ≈ +1, flip ≈ +4; plus a ratio bonus
`0.5·clamp(ln(baseline_tok/compressed_tok), −2, +2)` per task.
**Global token-savings MULTIPLIER (the key mechanism):**
```
applied_score = -4.0 + (raw_score + 4.0) * multiplier
savings_ratio = 1 - compressed_tokens/baseline_tokens          # overall, across all tasks
multiplier = smoothstep(clamp((savings_ratio + 0.20)/0.40, 0, 1))   # = -2n³ + 3n²
```
- savings ≥ **+20%** → multiplier **1.0** → applied = raw (full score).
- savings = **0%** → multiplier **0.5** → applied = −4 + (raw+4)·0.5 (pulls every task halfway to the −4 floor).
- savings ≤ **−20%** (inflation) → multiplier **0** → applied = **−4 for EVERY task** (catastrophic).
- savings = +10% → mult ≈ 0.84.
The "penalty" field = raw − applied = the multiplier shortfall.

## Why this matters (it explains our results + confirms the failed experiments)
1. **m18/ultralight was doomed by the multiplier, independent of perturbation.** Near-passthrough produces
   <20% savings → multiplier <1 → every task pulled toward −4. So ultralight loses TWICE (perturbation + the
   multiplier crush). Light compression only works if it stays **≥20% savings (~1.25×+)** — the king/5DAh sit at
   **~29% (1.41×)**, NOT near-passthrough. m18 dropped below the threshold on small tasks → mis-designed.
2. **m12 is optimally + ROBUSTLY positioned:** 43% savings (1.75×) → full multiplier **with margin**; all three
   categories positive (0.41/0.95/0.92) → ~zero penalty exposure; strong per-task ratio bonus. If the platform
   ever RAISES the 20% savings gate, m12's 43% margin absorbs it; the king (29%) has less headroom.
3. **The high-Easy rivals carry exposure m12 doesn't:** 5DAh's −3.6 Hard means many tasks at the −4 floor; any
   penalty/consistency tightening (the active work) hurts collapse-miners, not our clean all-positive profile.

## Verdict
No merged or imminent scoring change favors (or threatens) our M+H profile — the active work is penalty
CONSISTENCY, and the one game-changer (llm-semantic-scoring) is dormant. The formula CONFIRMS: (a) m12 is
well-optimized and penalty/gate-robust; (b) every "go lighter" lever we killed was correctly killed (the
multiplier punishes <20% savings hard); (c) the rivals' high Easy comes with category-collapse risk m12 avoids.
**HOLD m12.** Monitor: leaderboard each cycle (ignore `evaluating` scores) + whether `llm-semantic-scoring`
revives — that dormant branch is the only thing that could materially change the game.
