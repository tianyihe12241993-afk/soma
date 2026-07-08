# comp-110 LOCAL EVAL — first real end-to-end results (2026-07-07)

_Working UNDER the current scoring formula (user directive: don't wait for the in-flux change; make the
candidate as good as possible now + pass all testings). Candidate = `upload_miner_skeleton_v2.py`
(sha 429d1b26), profile `target`. Model deepseek/deepseek-v4-pro via OpenRouter, copilot stack, macOS._

> ## ⚠️ CORRECTION (2026-07-07, later) — the "CANNOT clear 20%" verdict below is WRONG.
> The comp-110 dashboard has a **qualifier** (`5DtYjEJbjzi6…`, 1 of 46) that cleared the screener with
> **19.8% aggregate RAW-token savings** (detail scrape 225745), passing correctness, output low/stable.
> My verdict was based on two method errors: (1) I measured WEIGHTED savings vs a fresh **paired** baseline
> (2–4× step variance) — the platform uses a **FIXED seeded baseline** aggregated over 15 runs, so my flail
> outlier (66 steps) dragged raw-11% down to weighted-3.5% in a way the platform method would not; (2) the
> metric comparable to the dashboard is RAW, where we sit at **11.0%** vs the qualifier's **19.8%**.
> **Corrected verdict: 20% IS achievable; our candidate is behind on compression aggressiveness (~half),
> not blocked by a wall.** Path = compress ~2× harder (deep+) while keeping trajectories short/stable/correct
> (the qualifier keeps output ~6.4k/run vs our 12k). Everything below is retained as the raw record + the
> (still-valid) findings that the pipeline works, the miner fires, and step-variance is huge. See state/CURRENT.md
> LATEST-2 + DISCOVERIES for the corrected read.

## What was proven for the FIRST time (pipeline validation)
- The comp-110 copilot stack runs end-to-end locally: solve `completed`, real patch produced, and the
  miner **FIRES** (`compress_messages` called once per outgoing request — 36 calls on django-14017).
  All prior sessions were blocked on `.env`; this is the first confirmed firing + full solve.
- Offline gates all PASS (harness ×3 profiles: 26 checks each; rules/compliance gate GATE+FILE).
- Solve rate: **miner 100% / baseline 100%** produced patches (6 runs each; correctness NOT graded — see limits).

## The measured screener number (the load-bearing result)
Metric = the screener's own: `1 − Σ miner_weighted / Σ baseline_weighted`, weighted = 1·input + (1/10)·cached + 3·output.
Design: 2 confirmed-resolvable instances × 3 runs each, miner+baseline interleaved (n=6 pairs).

| instance | run | miner_wt | base_wt | m_steps | b_steps | savings |
|---|---|---|---|---|---|---|
| django-14017 | 1 | 276,343 | 112,314 | **66** | 27 | −146.0% |
| django-11099 | 1 | 51,216 | 42,294 | 18 | 14 | −21.1% |
| django-14017 | 2 | 104,934 | 248,939 | 16 | **55** | +57.8% |
| django-11099 | 2 | 30,190 | 55,463 | 11 | 19 | +45.6% |
| django-14017 | 3 | 110,877 | 139,269 | 31 | 33 | +20.4% |
| django-11099 | 3 | 53,480 | 51,602 | 18 | 18 | −3.6% |

- **AGGREGATE WEIGHTED SAVINGS = 3.5%** (ratio-of-sums). **Gate = 20%. Miss by a wide margin.**
- Per-run savings: mean −7.8%, median +8.4%, range **−146% … +58%**.
- **miner steps mean 26.7 vs baseline 27.7** — statistically indistinguishable. Compression does NOT
  systematically reduce agent turns.

## Mechanism (why 3.5%, and why it's robust)
1. **Byte compression is real but capped ~13–20%.** Sidecar out/in char ratio = 0.867 (13.3%) on the
   django-14017 miner run; the cleanest equal-steps pair (run3: 31 vs 33 steps) shows **+20.4%** — that
   isolates the byte + fixed-trajectory effect. Consistent with the offline re-derivation ceiling (~11–13%
   real; comp110_scoring_rederivation.md §4-5).
2. **`agent_steps` variance dominates everything.** The SAME miner on django-14017 took **66, 16, 31**
   steps across three runs; the baseline took **27, 55, 33**. cache_read grows ~with (steps × per-turn
   context), so one flail (run1 miner 66 steps → cache 1.72M → weighted 276k) contributes a huge term that
   no byte-compression offsets. Which side flails is ~random.
3. **The trajectory/output lever (the ONLY math path to 20%, re-derivation §5-6) is NOISE, not a reliable
   positive.** Compression neither reliably reduces nor increases steps (26.7≈27.7). So aggregate savings
   sits between ~0% and the ~13–20% byte-floor, never reliably ≥20%.

## VERDICT (Claude; pending Codex gate #2 re-derive + gate #3 red-team)
**Under the current formula, this compliant pure-`compress_messages` context compressor CANNOT clear the
20% weighted-savings screener gate.** Measured 3.5%; best-case byte ceiling ~13–20% (equal-steps) is at/below
the gate and is swamped by step variance. This empirically CONFIRMS the offline re-derivation's high-confidence
conclusion. Profile tuning (safe/deep) cannot move a 3.5% result past 20% — it only trades a few points of
byte-savings against flail risk, both under the ceiling.

## Honest limits of this measurement
- **Correctness (the ≥50% pass gate) is NOT graded locally.** `patch_evaluation` = 0 tests run (no per-repo
  SWE-bench eval images; `--swerebench-eval` would build them — slow/x86). Local measures savings +
  patch-production + steps (a flail proxy), not resolved-correctness. Platform grades correctness.
- **Paired vs fixed baseline:** I ran a fresh paired baseline each time; the platform may use a FIXED
  canonical baseline cost per task ("baseline costs to be shared"). Either way miner_mean ≈ baseline_mean
  (14017: 164k vs 167k; 11099: 45k vs 50k) ⇒ the ~3.5% conclusion is robust to that choice.
- n=6 pairs, 2 django instances. More instances/runs would tighten the CI but not change the sign (the
  effect is < the noise). The platform (5 runs × 3 tasks) is the only true arbiter.

## Options for the USER (uploads are USER-run regardless)
- **A. HOLD + keep polished (Claude lean).** The candidate is a compliant, cache-safe, non-breaking,
  correctly-firing compressor — as good as pure compression gets. The 20% gate is unreachable by
  compression on this agent/model; a non-qualifying upload gets no evaluation (wastes a hotkey). The team
  said the formula is CHANGING to reward input-reduction better → re-measure with retune_harness/local_eval
  the hour it lands (watcher armed).
- **B. Tune aggressiveness + re-measure (low EV).** Test `safe`/`deep` profiles (safe may flail less → higher
  aggregate; deep more byte-savings, more flail risk). ~1 more 12-solve batch (~1h, credits). Expected still <20%.
- **C. Investigate a step-reducing design (R&D).** A compressor that reliably cuts agent turns is the only
  path to 20%; unproven and speculative. Our skeleton already tries clarity (paths/signal/markers) and it
  didn't systematically help.
- **D. Confirm the platform baseline definition + any real "20% achiever" mechanism** before further invest.
