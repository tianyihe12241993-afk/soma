# Comp-108 RESEARCH RESET — we were running the 107 playbook on a different game

_2026-06-23. Triggered by the user: "this is a new competition, we didn't analyze what's different from the
previous one where m7 was best... re-research from scratch." Foundational findings below. This SUPERSEDES the
107-derived assumptions in prior reports for anything task-specific._

## THE foundational finding: comp-108 tasks are 100% different from comp-107
- comp-107 task set (config/task_categories.csv): 45 instances. comp-108 task set (un-masked scrape
  2026-06-23): 50 instances (45 scored + 5 screener). **OVERLAP = 0.** Not one shared instance.
- ⇒ **Every 107 task-specific fact is MOOT for 108:** the "fragile" tasks (sympy-17139, sympy-16766,
  django-11239, django-14493), the break list, the flip targets, the fragile-guard signatures — none of those
  instances are in 108. The H3/H4/m12.1/m12.1b fragile-task tuning was all 107-specific.
- ⇒ **Our LOCAL EVAL has been running on the 107 tasks the whole time** (run_batch_eval TASKS = 107 instances).
  So local eval ≠ platform BY CONSTRUCTION — we were validating candidates on the wrong task set. THIS is the
  root cause of every local-vs-platform divergence (m13, m14), not just "local is noisy."

## What un-masked now (upstream 9301a74): we can finally do real task-level work
Task names are now visible in the aggregate. comp-108 = django×24 + sympy×21 (45 scored). Baseline structure
(from m12's runs): **29 baseline-PASS** (pass-pass candidates) + **16 baseline-FAIL** (flip candidates).
Per-category E/M/H split = TODO (platform doesn't expose per-task category; derive from SWE-bench difficulty).

## The REAL comp-108 race (status=scored only; the Easy-only 1.0+ miners are "not qualified")
| miner | total | Easy | Medium | Hard | note |
|-------|-------|------|--------|------|------|
| 5DFvymSeEw (king) | 0.780 | 0.812 | 0.934 | 0.596 | balanced; strong E+M, weak Hard |
| **m12 (us)** | **0.768** | **0.412** | **0.953** | **0.919** | #2; DOMINANT M+H, weak Easy |
| 5GYxeJjd | 0.661 | 0.117 | 0.661 | 0.569 | |
| 5FqfEPFi | 0.636 | 0.457 | 0.570 | 0.580 | |
| m13 (us) | 0.571 | 0.561 | 0.718 | 0.434 | cap design — rejected |
| 5CwZBKyL | 0.530 | 0.755 | 0.604 | 0.243 | |
| m14 (us) | ~0.40 | ~0.41 | ~0.55 | ~0.23 | KEY-confound / unexplained |
- The top-4 "Easy 1.0+" entries are **`not qualified`** (3) or `evaluating` (1) — they pass Easy but FAIL the
  screening **weighted-savings gate** (don't compress enough) → earn nothing. Easy-only is NOT a winning play.
- **m12 is the field's #1 on BOTH Medium (0.953) and Hard (0.919)** — nobody else is close on Hard. Our moat is
  real. The king beats us purely on **Easy (0.812 vs 0.412)**.

## The HARD CONSTRAINT we'd missed: the ≥10% weighted-savings screener gate (upstream 100c884)
Screening now requires **≥10% WEIGHTED token savings** (input×1, cached×⅓, output×3) ON TOP of pass-ratio 0.5.
⇒ You cannot win Easy by NOT compressing — that gets you "not qualified" (the top-4). **This is the trap
never-inflate / Easy-pass-through walks into.** m15 (never-inflate) is currently `screening / screener_passed
=False` — possibly heading for "not qualified" because never-inflate cut its savings below 10%.

## Open / unresolved
- **m14 confound STILL unexplained** (user confirms same OpenRouter account → not the key, not AtlasCloud which
  is constant). Candidates: temporal provider variance (OpenRouter routes qwen3-coder across backends over
  TIME even on one account) OR real. m15 full-eval = one more sample (itself possibly noisy).
- **Per-task E/M/H category** for the 50 108-tasks (need SWE-bench Verified difficulty data).

## CHARACTERIZATION of comp-108 (2026-06-23) — eval RE-POINTED
- **Eval re-pointed:** `config/comp108_tasks.txt` (50 instances, baseline Pass/Flip labels); both drivers now
  read it (`run_batch_eval[_parallel].sh`). The 107 task list is gone.
- **E/M/H is a platform-RELATIVE rank we CANNOT reproduce locally.** Formula
  (`swe_difficulty_calculator.py`): `difficulty = 0.75·(1−baseline_pass_rate) + 0.25·(baseline_tokens/max)`,
  ranked, split into equal thirds (Hard=top, Easy=bottom). We only have the baseline pass BOOL (not the rate)
  + baseline tokens, so our reproduction MIS-VALIDATES (Easy mean 0.725 vs platform 0.412). ⇒ group locally by
  baseline status; trust PLATFORM for true E/M/H. Meaning: **Hard = baseline-fails-most + biggest context;
  Easy = baseline-passes + smallest context.**
- **m12 gap structure on the REAL 108 tasks:** 16 flip-candidates → 7 flips won (≥3/5), 2 partial, **7
  FAIL-FAIL (0/5 = capability gap, compression can't fix)**. 29 pass-pass → 12 clean 5/5, **17 break on some
  runs** (run-variance). So our losable points = run-variance on pass-pass + the 7 unwinnable fail-fails.
- **★ THE EASY MECHANISM (smallest-context pass-pass tasks):** m12 mean ~0.72 on the Easy-proxy, dragged below
  a clean +1.0 by TWO things — (a) **run-breaks** on small tasks (django-13810 2/5→−1.98, django-12039
  2/5→−0.42 — the BIGGER killer), and (b) **inflation** (6/15 at ratio<1; sympy-15349 0.66×→−1.03). So Easy is
  low from RELIABILITY (breaks on small contexts) + an inflation tax. **Implications for the Easy lever:**
  never-inflate fixes only (b) and risks the ≥10% savings gate; the bigger win is (a) NOT BREAKING small
  contexts. And on Easy you still must compress enough to clear the savings gate → want LIGHT-but-real
  compression on small contexts (ratio slightly >1), never inflation, never full-passthrough.

## RESET STRATEGY (evidence-based for 108)
1. **RE-POINT local eval at the 50 comp-108 instances** (now un-masked) — #1 fix; without it local is worthless.
   Re-characterize on 108: which tasks break under harvest, which are flip-candidates, which are fail-fail.
2. **Hold the moat (M+H).** m12's harvest dominates Medium+Hard — do NOT soften it (m13 proved softening
   collapses H+M). Our #2 is built on M+H.
3. **Lift Easy WITHOUT tripping the savings gate.** The Easy gap (0.412 vs king 0.812) is the path to #1, but
   the candidate must keep ≥10% weighted savings (never full-passthrough). never-inflate alone likely violates
   this → wrong lever. Need an Easy lever that still compresses (e.g. Easy-appropriate compression, not
   pass-through).
4. **Trust ONLY platform scores** (same account/window) for verdicts; local (once re-pointed at 108) is a
   directional pre-filter, not ground truth — and watch for temporal provider variance across submissions.
5. **Re-check upstream each round** — scoring/validator layer is in active flux (penalty-fix, scoring-formula,
   llm-semantic-scoring branches) + tasks rotate every competition.
