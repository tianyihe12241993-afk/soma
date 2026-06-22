# H1M_eval run — 2026-06-22_005707_H1M_eval
_2026-06-22T00:57:07Z_

REAL m7 baseline (platform scrape) + OFFLINE candidate proxy/projection. Candidate real pass/neg-run/broke = PENDING_EVAL (needs SOMA SWE-bench env; raw per-call task contexts unavailable offline). No scores invented.

## m7 baseline on Medium-first targets (REAL, platform scrape)
- tasks: 7 | pass_rate 1.0 | neg-run rate 0.0 | broke 0 | neg-score 0
- avg ratio 3.016× | median 2.684× | Medium ratio 3.016× | Medium est score 1.69

## Candidate (offline proxy + projection; real pass/neg-run PENDING_EVAL)
| profile | offline ratio Δ | proj avg ratio | proj Medium ratio | est score Δ/task | protected | guard | real pass/neg |
|---|---|---|---|---|---|---|---|
| h1m@medium | +10.8% | 3.342× | 3.342× | +0.051 | True | fires (offline) | PENDING_EVAL |
| h1m@deep | +13.7% | 3.429× | 3.429× | +0.064 | True | fires (offline) | PENDING_EVAL |

## Fragile guard group (m7 baseline; candidate expected to fall back to m7)
- tasks: ['sympy__sympy-17139', 'sympy__sympy-16766', 'django__django-11239', 'django__django-14493']
- m7 broke-baseline here: 1 | m7 neg-run rate 0.4
- candidate: guard (ERROR_GUARD_MIN_HITS=3) routes still-failing/error-dense to m7 rich path → no deeper compression; offline harness confirmed the guard fires. Verify on eval.

## Decision gate
### h1m@medium
- compression_improvement>=8%: **PASS** — offline +10.8%
- fragile_guard_works: **PASS** — guard fired on 1 case(s), protected=True
- medium_est_score_no_drop: **PASS (projected)** — projected +0.051/task on Medium (deeper ratio)
- new_broken_baseline_vs_m7: **PENDING_EVAL** — offline harness: 0 broken; real needs SOMA eval
- medium_neg_run_increase: **PENDING_EVAL** — m7 Medium-first targets are pass-stable (neg_run_rate=0.0); real needs eval
- → ADVANCE (candidate-only): offline gate PASS; real-task gate PENDING_EVAL
### h1m@deep
- compression_improvement>=8%: **PASS** — offline +13.7%
- fragile_guard_works: **PASS** — guard fired on 1 case(s), protected=True
- medium_est_score_no_drop: **PASS (projected)** — projected +0.064/task on Medium (deeper ratio)
- new_broken_baseline_vs_m7: **PENDING_EVAL** — offline harness: 0 broken; real needs SOMA eval
- medium_neg_run_increase: **PENDING_EVAL** — m7 Medium-first targets are pass-stable (neg_run_rate=0.0); real needs eval
- → ADVANCE (candidate-only): offline gate PASS; real-task gate PENDING_EVAL

## What is needed to finish the gate (the one thing offline can't do)
Run h1m@deep (and h1m@medium) through the SOMA SWE-bench eval on the Medium-first targets, export per-task results (task_id, pass, neg_runs, ratio, score), then `python h1m_run.py --results <file>`. Only that yields real pass-rate / neg-run / broke-baseline; until then candidate stays CANDIDATE-ONLY.
