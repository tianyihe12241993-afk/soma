# comp-110 scoring RE-DERIVATION from current upstream (2026-07-07, max-effort pass)

_Source of truth: a clean detached worktree of current upstream `main` = commit **9c1be25**
(DendriteHQ/SOMA, 2026-07-07 09:03Z), created at `../soma-upstream-check` (removed after this pass;
`git worktree add --detach <path> upstream/main` to recreate). SOMA-benchmark re-fetched to
`821bdb9` (2026-07-07 11:45Z). Every load-bearing claim cites `mcp_platform/...` file:line (same
content in the worktree). This SUPERSEDES the stale-code numbers in comp110_explore_scoring_analysis.md._

## 1. What changed upstream (vs the code my earlier analysis used)
Both in one commit today. `mcp_platform/app/core/config.py`:
- **`swebench_screening_min_weighted_token_saving_ratio`: 0.1 → `0.2`** (config.py:275-276). Screener savings gate = **20%**.
- **`swebench_screening_cached_input_tokens_weight`: 1/3 → `1.0/10.0`** (config.py:283-284).
Everything else in that block unchanged: input weight `1.0` (279-280), output weight `3.0` (287-288),
`swebench_screening_pass_ratio` `0.5` (271-272), `swebench_dynamic_screener_task_count` `3` (291-292),
`swebench_screening_min_passed_tasks` `0` (267-268).

## 2. Current scoring constants + formulas (re-derived, with citations)
**Weighted-token formula** (`scoring.py:compute_weighted_tokens` 38-64, weights via `_scoring_token_weights` 30-35):
`weighted = 1.0·input + (1/10)·cached_input + 3.0·output`.  ← cached now ×1/10.

**Screener qualification** (`swebench_orchestrator.py` ~742-799; helper `_weighted_tokens_for_screening`
845-865 uses the SAME weights; `_required_screening_weighted_token_saving_ratio` 816):
run on `swebench_verified` screener tasks (3 tasks, repeats each). Qualify iff **(a)** pass ≥50% of
screener tasks (majority-resolved per task; `_required_screening_task_passes` 802) **AND (b)**
aggregate `1 − miner_weighted_total/baseline_weighted_total ≥ 0.20`. Fail (b) ⇒ not qualified ⇒ no evaluation.

**swebench_verified per-run score** (`compute_swe_run_score` 218-234; `base_swe_score` 199-215):
base + λ·`trim_token_ratio` where trim = clamp(ln(baseline/miner), ±2). Base/λ: pass→pass **+1**/0.5,
pass→fail (BREAK) **−4**/0, fail→pass (FLIP) **+2**/0.5, fail→fail **0**/0.1. (Unchanged from comp-108.)
**Miner swebench-category score** (`build_swe_miner_scores`; `adjust_miner_score_with_token_savings`
182-196; `compute_miner_score_multiplier` 174-179): `-4 + (raw+4)·m(s)`, `m(s)= -2s³+3s²`,
`s = clamp((savings+0.2)/0.4, 0,1)`, savings = `1 − compressed/baseline`. ⚠️ **This category's savings
use RAW `tokens_used`, NOT weighted** (build_swe_miner_scores sums `baseline["tokens_used"]` /
`compressed_tokens`). So weighting (cached 1/10) hits the SCREENER + EXPLORE, not the swebench score itself.

**Explore layer** (`scoring.py` 67-138 — formulas UNCHANGED; only the weighted inputs changed):
- per-task: `compute_explore_task_score` = `gate·tau`; `margin = miner_quality − baseline_quality`,
  quality = avg(hit_file_rate − noise_file_rate) over repeats; `margin ≤ −0.20 ⇒ −2` (91);
  `gate = 3r²−2r³`, `r = clamp((margin+0.2)/0.4,0,1)` (101-102); `tau = clamp(2·log2(baseline_wt/miner_wt), ±2)` (103).
  **miner_wt/baseline_wt are the per-task AVG weighted tokens (cached 1/10)** (frontend.py 830/848-853/881).
- miner total: `compute_explore_miner_total_score` 107-138: `total = m·p_avg + (1−m)·(−2)`,
  `m = 3r²−2r³`, `r = clamp((s_ratio+0.2)/0.4,0,1)`, `s_ratio = 1 − Σminer_wt/Σbaseline_wt` (weighted).
  Hard −2 if `margin_agg<0 AND s_ratio<0` (133). ⇒ **tau saturates (±2) at 2× weighted savings; the total
  blend removes floor-drag only at ≥20% aggregate weighted savings; 0% savings ⇒ total = 0.5·p_avg − 1.0.**

**Incentive/reward layers** (`incentive_calculator.py` `build_incentive_layers` 73-85, weights 136-176):
categories = the task types. Same combinatorial 7-element system as comp-108 but over
{swebench_verified, swe_explorer_explore, swe_explorer_edit}: L0 = full triple (weight `1/2⁰=1.0`, uses
miner TOTAL score), L1 = 3 pairs (`1/2¹` split → 1/6 each), L2 = 3 singles (`1/2²` split → 1/12 each).
Element winner = max category-avg (ties split, isclose 172). Normalized × (1−burn).

## 3. Where compute_weighted_tokens is used (traced)
- Screener qualification gate — `swebench_orchestrator.py` (via `_weighted_tokens_for_screening`) — **WEIGHTED (cached 1/10)**.
- Explore tau + explore-total blend — `frontend.py:881,924,947` → `compute_explore_*` — **WEIGHTED (cached 1/10)**.
- Per-run/per-task weighted for display + explore — `scoring.py:297-343`, `frontend.py:620,695,830` — **WEIGHTED**.
- swebench_verified category savings multiplier + per-run trim — `build_swe_miner_scores` / `compute_swe_run_score` — **RAW tokens_used** (NOT weighted).
- swe_explorer_edit — resolved(pass/fail)-based (`beev.resolved`), analogous to swebench.

## 4. Corrected feasibility (captured real traffic; cached 1/10; gate 20%)
Fixed-trajectory offline replay of the 29 captured `messages.in` payloads (django-14017), weighted
with cached 1/10; model validated at 0.63× live context (so real ≈ ×0.63; still an OPTIMISTIC upper bound
because ~1.6× uncompressible mass — tool schemas/framing — is invisible to the replay).
| variant | opt savings | real~ (×0.63) | vs 20% |
|---|---|---|---|
| v3 (window 25/15, thresh 10k) | ~0% | ~0% | ✗ |
| SKELETON safe / target / deep | 12.4 / 14.7 / 16.2% | 7.8 / 9.3 / **10.2%** | ✗ |
| EXTREME (head/tail 0, budget ~120) | 18.1% | **~11.4%** | ✗ |
- **Path-independent CONTEXT savings ceiling ≈ 9–13% real** (extreme ~11%). Below 20% by a clear margin.
- **What a fixed-trajectory replay CAN measure:** how much a compressor shrinks the bytes of a GIVEN
  request stream → the context-savings component. **What it CANNOT measure:** how compression changes the
  agent's TRAJECTORY — number of turns, re-reads, and especially OUTPUT tokens (weight 3). Output is
  ~23% of the weighted total and is generated by the agent, not touched by us; only a live multi-run
  eval reveals whether skeletons make the agent solve in fewer turns (less output → big weighted win) or
  re-read more (more output → loss).

## 5. Can a pure `compress_messages` context compressor clear 20%? — NO (not on its own)
Weighted decomposition of a real no-compression run (cached 1/10): **input 19% · cached 58% · output 23%**.
- Directly reducible by a context compressor: only the COMPRESSIBLE slice of input+cached (tool results +
  old assistant text). NOT reducible: system prompt (instructions), tool schemas/framing, the fresh read
  the agent must act on, and **all output** (weight 3). Cached is 58% of weighted but sits at ×1/10, so
  halving the *compressible* cached raw yields only single-digit weighted savings.
- Empirically the compressible slice, compressed to the bone, gives ~11% real weighted savings. **A pure
  context compressor cannot reach the 20% screener gate on this agent.** State this plainly.
- The only ≥20% path visible in the math is **cutting OUTPUT** (×3): e.g. a ~50% shorter trajectory
  (fewer/tighter turns) removes ~11–12% of weighted on its own, which stacked on ~9–11% context savings
  crosses 20%. That is a TRAJECTORY/behavior effect, not byte compression.

## 6. Alternative compliant levers (ANALYSIS ONLY — not implemented)
- **Shorter trajectories / fewer turns** = the highest-leverage lever (output ×3). A compressor can only
  pursue this INDIRECTLY: give the agent exactly what it needs to act NOW so it doesn't loop/re-read.
- **Salience over volume:** make file/path/error/test/def signals maximally prominent + keep the FRESH
  actionable read intact, so the agent decides in one turn. This trades raw byte-savings for turn-savings —
  the opposite of aggressive skeletonizing, and possibly net-better under the ×3 output weight.
- **Source-line markers to reduce TURNS, not just bytes:** if a marker tells the agent precisely which
  lines were omitted, it can issue one targeted re-read instead of several exploratory ones — turning a
  potential output-inflator into an output-reducer. Unproven; needs a smoke.
- **Early persistent reads:** compressing the earliest big reads pays on every later (cached) turn — but at
  ×1/10 the payoff is small; not worth break risk alone.
- **The "20% achiever" claim ⇒ likely NOT pure context compression.** Most consistent with trajectory/output
  reduction, a materially different task mix, or exploiting a scoring detail. Confirm before investing.

## 7. Verdicts on prior conclusions
- **VOID:** "10% gate", "cached ×1/3", "lower-threshold v4 clears 10%", "skeleton target 11.1% real clears the gate."
- **STILL TRUE:** cap32/LEAN window keeps small chunked reads whole (≈0 savings); dedup is dead (no exact re-reads);
  markers are compliant + file-level explore quality is robust to dropping bulk if paths survive; cache-safety
  forces compress-once-at-insertion.
- **LEAN v3:** still useful ONLY as a compliant, non-breaking, cache-safe REFERENCE implementation + the
  verified primitives (markers, whole-line, fail-open, recency). It does NOT qualify for comp-110 (near-0 savings).
- **Lower-threshold v4:** dead as a *qualification* path — even the extreme ceiling (~11% real) misses 20%.
- **SKELETON v1:** Codex GO-WITH-CHANGES, but ~10% real ⇒ does NOT qualify alone. Its markers-for-re-read idea
  is the seed of the trajectory lever, but that must be validated live, not offline.

## 8. Most likely path to clear 20% + recommended next action
The 20% weighted gate + cached ×1/10 make OUTPUT (×3) the dominant lever. **Best hypothesis: a compressor
that minimizes agent TURNS/OUTPUT (decisive-context + precise re-read markers), not one that maximizes byte
compression.** But this is unmeasurable offline. **RECOMMENDED NEXT ACTION (no build):** (1) get the SOMA
team's answers (§ team questions) — especially whether qualification is intended via context compression or
trajectory reduction, and exactly what tokens the weighted formula counts; (2) confirm the "20% achiever"
mechanism; (3) only then decide whether to invest in a trajectory-oriented candidate or treat comp-110 as
not-winnable via a pure compressor. Do NOT build another byte-compressor variant expecting it to qualify.
