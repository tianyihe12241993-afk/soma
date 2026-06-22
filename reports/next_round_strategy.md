# Next-round strategy (evidence-based)

## CANDIDATE 1 BUILT & OFFLINE-VALIDATED — H1M_m7_deeper_safe_v1 (2026-06-21)
First real next-round candidate is implemented (`experiments/candidates/H1M_m7_deeper_safe_v1/`)
and evaluated offline (`experiments/reports/H1M_m7_deeper_safe_v1.md`, `data/latest/h1m_candidate_results.json`).
A profile layer deepens ONLY the m7 harvest path; rich path / protections / coach untouched; fragile
guard fires one error-hit sooner. **Offline result (ratio + structural safety, real): h1m@deep = +13.7%
deeper compression on 6/6 clean harvest cases, 0 regressions, all protected content kept, no broken
tool-pairing; the fragile guard correctly routes error-dense transcripts to rich.** A/B sanity passes
(h1m@m7 ≡ m7). **PENDING_EVAL:** real pass-rate / neg-run / Medium score need the SOMA SWE-bench env.
**Verdict: advance h1m@deep (medium as fallback) to the platform eval on the Medium-first H1 targets;
do NOT promote to base until eval confirms Medium pass-rate/neg-run hold.** Next experiment below.

**Real-task experiment run (2026-06-22): `experiments/runs/2026-06-22_005707_H1M_eval/`.** REAL m7
Medium-first baseline = 7/7 pass, 0% neg-run, 0 broke, 3.02× avg, Medium est score 1.690. Projected
h1m@deep ~3.43× (+13.7%, +0.064/task), h1m@medium ~3.34×. Offline gate PASS; candidate real
pass/neg-run/broke = PENDING_EVAL. The ONLY remaining step before a base decision: run h1m@deep on the
SOMA SWE-bench eval → `h1m_run.py --results <file>` (applies the full gate).

## DECISION (per-category gap + compression-depth risk, 2026-06-21)
**Deeper compression is pass-safe — prioritize H1.** On shared-pass tasks the correlation
between compression ratio and negative-run rate is ≈0 / slightly **negative** in every
category (overall −0.09; Easy −0.22, Medium −0.03, Hard −0.12) — deeper compressors are
NOT flakier. **27/36 (75%)** shared-pass tasks have a leader passing CLEANLY (≤1 neg run)
at ≥4.5×, so leader-level depth is demonstrably achievable. → **Run H1_m7_deeper_safe_compression
first**, ordering the 19 "safe" targets in `reports/h1_safe_compression_targets.md`.

- **Order H1 Medium-first (this absorbs H2).** Medium is m7's strongest, most pass-stable
  category (neg-run 4.4% vs leaders 10.1%; m7 beats the top-4 *average* by +0.17) yet still
  sits at only 2.84× with large proven headroom and is our closest reward element (m7 1.421 vs
  Medium-leader 1.620). 8 of the top-12 safe targets are Medium → H1's safe set IS the H2 play.
  Keep **H2_medium_specialist** as the formal second track if a Medium-only build is wanted.
- **Risk is concentrated in ~4 tasks → guard, don't avoid depth (H3).** Only fragile tasks
  (sympy-17139 [m7], + sympy-16766 / django-11239 / django-14493 [m9/m10/m11 only]) and a few
  deep-and-unstable cases need task-signature fallback. Everything else is safe to push.
- **2 catastrophic Hard gaps are SOLVING gaps, not compression** (django-14999: m7 1.10 vs
  4.01 at ~equal ratio; sympy-22714) — do NOT chase these with compression; out of H1 scope.
- **Keep rejecting flip-routing.** The only *extra* fragile tasks were broken by m9/m10/m11.

Recommended first experiment: **H1, Medium-first**, using the "safe" targets list, with the
H3 fragile guard on the ~4 known signatures. See reports/per_category_gap.md +
compression_depth_risk.md + h1_safe_compression_targets.md.


> **The next direction is NOT "more routing." It is "m7-style architecture with
> deeper pass-safe compression, backed by per-task evidence."**

## What the data says (competition 107, completed)
1. **Top miners beat m7 on compression RATIO, not solving.** All scored miners share
   the same 34 baseline passes. On the 36 tasks m7 and the overall leader both pass,
   score ≈ `1 + 0.5·ln(ratio)` holds; the leader runs ~4.9× vs m7 ~3.0× → the gap is
   almost entirely the token bonus. (reports/top_miner_comparison.md, m7_gap_analysis.md)
2. **m7 under-compresses almost everywhere.** Proven-safe headroom on ~33/45 tasks
   (a top miner passed the same task at a higher ratio); only ~1 task is at the ceiling.
3. **Flip-routing was a net negative.** m8/m9/m10/m11 did not raise pass count; they
   raised broken-baseline and negative-score counts. (reports/postmortem.md)
4. **m7 is very safe** (breaks ~1/45 baselines) → room to push compression deeper
   before risking passes.
5. **Per-run consistency is a noise floor, NOT our gap** (full per-run sweep, 5000 runs).
   m7 has ~15.3% of runs scoring negative; the top miners are the same (13.6–14.4%). So
   flakiness is paid by everyone — fixing it helps all miners equally and is not where m7
   loses. (m9/m10 at ~22% negative-runs are the exception — extra breakage from flip-routing,
   part of why those variants cratered.) See reports/run_variance.md, data/processed/run_scores.jsonl.

## The plan (in priority order)
- **H1 — deeper pass-safe compression (PRIMARY).** Lower m7's target/caps on tasks it
  already passes with margin (start with the <2× barely-compressed set). Goal ~4.5–5×.
  Gate: ratio ↑ ≥ +0.30× with **zero** new broken baselines / negative tasks.
- **H3 — fragile-task guard (PAIR WITH H1).** Conservative near-pass-through fallback
  on fragile signatures (e.g. sympy-17139) so deeper compression elsewhere can't
  re-break them. Gate: broke_baseline ↓, ratio elsewhere preserved.
- **H2 — Medium specialist.** Medium is our closest reward (1.421 vs 1.620). Push
  Medium-task ratio pass-safely. **Blocked** until the task→category map is imported.
- **H4 — output-weight readiness.** Track input/cached/output tokens separately so we
  optimize *weighted* cost if the formula changes. Measurement-readiness now.

## Permanently dropped (do not revisit as defaults)
- Flip-mode rescue, persistent-failure→rich routing, release-flip-on-pass.
- Chasing Easy/overall #1 via compression (Easy ~1.13-bounded for us; king's edge is
  agent decisiveness, not our lever).

## Guardrails
- Keep any prompt/coach content within **public allowed-prompt rules** (loop-detection +
  forced-stop only). No workflow steering.
- Treat local replay as noisy: separate **observed platform**, **local replay**, and
  **manual interpretation** in all records.
- Validate every deeper-compression push against the pass flags before trusting a ratio gain.

## Missing data that would sharpen this
- **task→category map** (Easy/Medium/Hard per task) → unblocks H2 + Medium/Hard
  attribution. Template: data/raw/platform_results/TASK_CATEGORIES_TEMPLATE.csv.
- **token-type split** (input/cached/output) → unblocks H4 weighted-cost optimization.
- **platform upload receipts** (hotkey+version+timestamp) → closes the label audit to 100%.
