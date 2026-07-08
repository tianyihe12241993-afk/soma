# comp-110 LOCAL TESTING ARCHITECTURE — right-sized, tiered (2026-07-08)

_The platform runs 3 benchmark types × 50 hidden tasks × 5 runs (750 runs/miner) in EVALUATION, and
5 known django tasks × 3 attempts (swebench_verified only) in SCREENING. **We do NOT replicate that
locally** — we right-size each tier to the DECISION it must support. comp-108's core lesson stands:
local exists to kill bad candidates cheaply and pick the one worth a hotkey; the platform is the arbiter._

## The 4 tiers (cost ↑, frequency ↓)

### Tier 0 — OFFLINE (free, seconds, run on EVERY edit)
- Rules/compliance gate: `scripts/check_readme_current.py --check-file <miner>`.
- Invariant battery (scratchpad gates): fresh-tail guard, system/user untouched, whole-line/byte-verbatim,
  marker range-tiling, budget cap, determinism, cache-stability, fail-open.
- **Byte-reduction replay** on the 734 captured real requests → predicted weighted ≈ byte-cut × 0.75.
- DECISION: kill designs that can't reach the gate or violate invariants. (Proof of value: floors
  2k/4k/8k were eliminated here for zero solves — saved ~30 solves.)

### Tier 1 — SCREENER EMULATOR (the money tier; ~10–15 solves ≈ 1h per candidate)
- **swebench_verified ONLY, the 5 REAL screener tasks** (django-15103/13964/11551/15375/13516).
- **2–3 runs/task** (platform screening itself uses ~3 attempts; majority-per-task is the gate — 2 runs
  detect gross breaks, 3 settle majorities). NOT 5: variance sits mostly at the task level; the 5th run
  buys almost no decision value at +67% cost.
- Candidate runs scored vs the **FIXED seeded baseline** (3 graded no-compression runs/task, built once —
  15 solves, DONE, 15/15 RESOLVED) with the platform's exact math: Gate A majority-resolved ≥50% of tasks;
  Gate B weighted ratio-of-sums ≥20% (1·input + 0.1·cached + 3·output).
- **Every patch GRADED** (`scripts/grade_patch_local.py` — real swebench harness; the copilot backend
  never grades on its own, it only captures). "Patch produced" ≠ correct (m1's 6/6-patches → −4 lesson).
- Report: `scripts/emulator_report.py` (gates + token splits + steps + output/step + sidecar ratio +
  marker scan + per-task detail).
- DECISION: which candidate gets the ONE upload.

### Tier 2 — CROWN VALIDATION (finalists only; ~4–6 solves)
- The uploaded miner IS the eval miner (one upload/hotkey) → finalists must also not crater the other
  two types. NOT 50×5 — just a smoke per type:
  - `swe_explorer_explore` ×1–2: compression FIRES + savings>0 (tau; passthrough scores 0) + quality
    hit−noise ≥ baseline (`scripts/score_explore_local.py`, public SWE-Explore-Bench ground truth).
  - `swe_explorer_edit` ×1–2: still resolves with ground-truth hints.
- DECISION: veto a screener-winner that would bomb the eval layers.

### Tier 3 — GENERALIZATION (optional, pre-eval-window)
- 3–5 diverse non-django public tasks × 1 run: catch django-overfit before the hidden set punishes it.
- DECISION: tune-down aggression if breaks appear off-django.

## Why NOT full replication (3 × 50 × 5)
- The 50 eval tasks are HIDDEN — unreplicable by definition; the screener tasks + a diverse sample are
  the only legitimate proxies.
- 5 runs/task locally ≈ +67% cost for negligible extra signal at our n (majority-of-3 == platform screening).
- The explore/edit layers matter only if we QUALIFY — validating them deeply before having a
  screener-passing candidate is inverted priority.

## comp-108 lessons embedded in this design
1. "Local eval never exercised compression" → we PROVE firing per run (sidecar messages in/out captures).
2. "Paired baselines are noise" (2–4× step variance) → FIXED seeded baseline, ratio-of-sums.
3. "Patch produced ≠ correct" → every run graded by the real harness.
4. "Platform is the only arbiter" → the emulator picks the candidate; the platform's screener verdict
   remains the truth; we spend ONE hotkey on the emulator's winner, not on guesses.

## Standing assets
seeds: `SOMA-benchmark/outputs/baseline_seed_<task>_r{1..3}` (graded) · runners: scratchpad
`seed_baseline.sh` / `phase2_candidates.sh` · scoring: `scripts/emulator_report.py` · grading:
`scripts/grade_patch_local.py` · explore: `scripts/score_explore_local.py` · offline: byte-sweep +
gate battery (scratchpad) · macOS: modprobe shim + DOCKER_DEFAULT_PLATFORM=linux/amd64 for grading.
