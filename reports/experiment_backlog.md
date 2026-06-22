# Experiment backlog

Candidates are based on **m7/v11.1** (NOT flip-routing). Each is one manifest in
`experiments/manifests/`. Run with `make experiments` (or
`python scripts/run_experiment_matrix.py --manifest <m> [--results <file>]`),
then `make summarize`.

## Decision gate (applied per candidate vs m7)
A candidate is **REJECTED** if any of:
- Broken baselines increase materially vs m7 (`broke_baseline` ↑).
- Medium score drops vs m7 (needs task→category map to evaluate).
- Avg compression does not improve meaningfully (`< +0.30×` vs m7).

A candidate is **PREFERRED** if it:
- Improves shared-pass compression **without** adding negative-score tasks.
- Holds or improves pass-rate.

**Hard rescue** (Hard-category gains) is considered **only** if it does not damage
Medium or shared-pass tasks.

## Backlog (priority order)
| # | id | base | status | blocked on |
|---|----|------|--------|-----------|
| 1 | **H1M_m7_deeper_safe_v1** | m7 | **offline-validated** (deep +13.7% ratio, 0 regress, safety ok) | platform eval for pass/neg-run |
| 2 | H3_fragile_task_guard | m7 | folded into H1M (guard @3 hits) — verify on eval | platform eval |
| 3 | H2_medium_specialist | m7 | covered by H1M Medium-first; task→category map imported | platform eval |
| 4 | H4_output_weight_ready | m7 | measurement-readiness | input/cached/output token split (MISSING) |

H1M detail: experiments/reports/H1M_m7_deeper_safe_v1.md. Profiles light/medium/deep (env H1M_PROFILE);
deep best offline. Real pass/neg-run: run h1m@deep through the SOMA eval on the Medium-first H1 targets,
dump per-task results, then `run_experiment_matrix.py --results <file>`.

## Live status
<!--STATUS-->
# Experiment summary
_computed 2026-06-21T16:01:09Z — 1 run(s)_

| run | exp | cand status | base ratio | cand ratio | base broke | cand broke | gate |
|-----|-----|-------------|-----------|-----------|-----------|-----------|------|
| 2026-06-21_160109_H1_m7_deeper_safe_compression | H1_m7_deeper_safe_compression | needs_data | 3.003× | —× | 0 | — | BASELINE ONLY — no candidate yet |
<!--/STATUS-->
