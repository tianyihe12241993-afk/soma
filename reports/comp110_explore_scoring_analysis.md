# comp-110 explore-layer scoring — code analysis + LEAN v4 proposal (2026-07-07)

_All from reading the actual code: `mcp_platform/app/api/routes/scoring.py` (compute_explore_task_score,
compute_explore_miner_total_score, compute_weighted_tokens), `frontend.py` (assembly ~540-985),
`services/swebench_orchestrator.py` (screener gate ~770-820), `core/config.py` (weights ~279-291),
`SOMA-benchmark/src/soma_bench/benchmark/solve.py` (explore setup + ground truth). The hit/noise
FORMULA itself is computed by the hidden validator scorer (not in-repo); its platform-side USE is confirmed._

## ⚠️ HEADLINE (changes the whole strategy): there is a HARD ≥10% weighted-savings SCREENER GATE
`swebench_orchestrator.py:799`: a miner qualifies only if `weighted_savings_ratio >=
SWEBENCH_SCREENING_MIN_WEIGHTED_TOKEN_SAVING_RATIO` (default **0.10**), computed as aggregate
`1 - miner_weighted_total/baseline_weighted_total` over the **swebench_verified screener tasks**
(after also passing ≥50% of them). **A near-passthrough miner FAILS screening and never enters
evaluation.** Our v3 (~1.2% savings) would be DISQUALIFIED. This is the OPPOSITE of comp-108, where
near-passthrough + compliance WON. **comp-110 forces real compression just to qualify.**

## Answers to the 8 questions

**1. How savings are measured.** Weighted tokens `= 1.0·input + (1/3)·cached_input + 3.0·output`
(config defaults, `compute_weighted_tokens`). Savings appear in THREE places:
- Screener gate: aggregate `s = 1 - miner_wt/baseline_wt` over swebench_verified screener tasks, must be ≥0.10.
- Per-task explore reward: `tau = clamp(2·log2(baseline_wt_avg / miner_wt_avg), -2, +2)`.
- Miner-total explore blend: `s_ratio = 1 - total_miner_wt/total_baseline_wt` over all explore tasks.

**2. Per-message / run / task / aggregate?** NOT per-message. Weighted tokens are computed **per RUN**,
**averaged per task** over repeats (`miner_weighted_tokens_avg`), used for per-task `tau`; and **summed
across tasks** (`explore_miner_weighted_total`) for the total blend. Quality likewise = per-task average
of (hit−noise) over repeats. Compression is applied per-message but SCORED as run→task-avg→cross-task-aggregate.

**3. Quality gate.** `gate = 3r² − 2r³` (smoothstep), `r = clamp((margin+δ)/(2δ), 0, 1)`, δ=0.20,
`margin = miner_quality − baseline_quality`, quality = avg(hit_file_rate − noise_file_rate). So:
margin ≥ +0.20 → gate=1 (keep all savings reward); margin = 0 → gate=0.5; margin ≤ −0.20 → floored.
Per-task score = `gate · tau`. Quality decides how much of the savings reward you KEEP.

**4. What causes the −2 floor.**
- Per-task: `margin <= -0.20` → immediate −2 (quality ≥0.20 worse than baseline), regardless of savings.
- Miner-total HARD floor: `margin_agg < 0 AND s_ratio < 0` (worse quality AND used more tokens) → −2.
- Miner-total SOFT drag: `total = m·p_avg + (1−m)·(−2)`, `m = smoothstep((s_ratio+0.20)/0.40)`. At 0%
  savings m=0.5 → `total = 0.5·p_avg − 1.0`. **Low savings drags the total toward −2 even with fine quality.**
  m=1 (no drag) only at s_ratio ≥ 0.20; m=0 (full floor) at s_ratio ≤ −0.20.

**5. hit-rate / noise-rate.** Computed by the hidden validator SWE-Explorer scorer against
`ground_truth.read_core_files` (the source+test files the reference solution read). Agent writes
`regions` [{path, line ranges}] to `/workspace/explore-result.json`; prompt tells it to find
N_source + N_test files. Platform stores {precision, recall, f1_score, hit_file_rate, noise_file_rate,
weighted_core_coverage} (`validator.py:_EXPLORER_METRIC_KEYS`). By definition/name: **hit_file_rate =
recall over core files** (found ÷ ground-truth-core); **noise_file_rate = false-positive rate**
(non-core reported ÷ reported); quality = hit − noise. It is **FILE-level** (line-level detail feeds
the separate weighted_core_coverage, which is NOT in the hit−noise quality used by the gate).

**6. Do source-line markers affect quality?** **Neutral-to-positive, and net-safe.** Quality depends
ONLY on the agent's final regions (which files it reports), not on marker text. Markers help
INDIRECTLY: keeping omissions locatable prevents compression from making the agent lose/mis-identify
files (which would drop hit / raise noise). They can't lift quality above baseline (the agent still
must identify files), but they stop aggressive compression from degrading it. Because hit/noise are
FILE-level, the block-relative line-number caveat mostly can't hurt hit−noise (it could only affect
line-level weighted_core_coverage). Smoke evidence: agent solved with 96 markers, no degradation.

**7. Target compression ratio.**
- `tau` maxes (+2) at **2× per-task weighted savings (50% reduction)**; beyond 2× no extra per-task reward.
- Total blend `m`=1 (no floor drag) at **≥20% aggregate weighted savings**.
- Screener needs **≥10% aggregate** just to qualify.
⇒ **Floor to survive = 10%. Target = ≥20% aggregate; up to ~2× on compressible tasks to max tau.**
Below 10% = disqualified; 10–20% = qualified but floor-dragged; ≥20% + quality-held = full reward.

**8. Is lowering the threshold to 2–3k worth the break risk?** **It is not optional — it is REQUIRED.**
v3 at ~1.2% fails the 10% screener → scores nothing. The copilot agent chunks reads small, so the
compressible mass lives in **2–10k messages**; a 10k threshold misses it. Dropping to ~2–3k is the
only way to reach ≥10–20% aggregate with this agent. Break risk is bounded by the existing safeguards
(quality floor keeps paths/errors/tests/signatures/imports; source-line markers keep omissions
locatable; recency guard; fail-open) AND the explore quality metric being FILE-level (robust to
dropping bulk lines if file identity + key regions survive). **Verdict: YES, mandatory; risk manageable
with v3's safeguards + markers. Must re-audit + re-smoke, and VALIDATE it actually clears 10% on a
screener-like swebench task (the uncompressible system prompt caps achievable savings — feasibility
is not guaranteed and must be measured).**

## ★ FEASIBILITY VERDICT (2026-07-07): lowering the threshold CANNOT clear the ≥10% screener. Do NOT build v4 on this lever.
Method (cheap + variance-free): captured the 29 REAL per-request `[messages.in]` payloads from a
keep-stack no-script solve of django-14017 (ground-truth traffic), then replayed them offline through
v3's compressor at thresholds 10k/5k/3k/2k/1k/500/200 × recency on/off, scoring weighted tokens
(input×1 + cached×⅓ + output×3; prefix-cache model). Model validated vs the live run: my captured
context = 0.47× the live input+cached weighted → real traffic carries ~2× uncompressible mass I can't
see (tool schemas/framing) → my savings numbers are an OPTIMISTIC UPPER BOUND (real ≈ ×0.47).

| threshold | OPTIMISTIC savings | dilution-adj (~×0.47) | sidecar in/out | markers | compliance |
|---|---|---|---|---|---|
| 10k (v3) | 0.0% | 0.0% | 1.00× | 0 | clean |
| 5k | 1.7% | ~0.8% | 1.02× | 144 | clean |
| 3k | 4.2% | ~2.0% | 1.06× | 292 | clean |
| 2k | 6.6% | ~3.1% | 1.09× | 138 | clean |
| 1k / 500 / 200 | **7.9% (saturates)** | **~3.7%** | 1.09× | — | clean |

**Compliance held at EVERY threshold: 0 bad markers, 0 system/user touched, 0 partial lines** (v3's
guarantees survive threshold changes). Recency on/off changed savings by <0.5pp (the final message
isn't the big content here).

**Why it's capped (the hard ceiling ~4–8%):**
1. **~2× uncompressible mass** (system prompt 23.5k resent every turn + tool schemas/framing) — identical
   in miner AND baseline, so it sits in both sides of `1−miner/baseline` and dilutes savings.
2. **Head+tail extraction floor:** v3 keeps 25 head + 15 tail lines + all signal lines. The copilot
   agent's tool results are SMALL (≤10.6k, mostly 2–8k = <40 lines) → head+tail already covers the whole
   message → they barely compress. Only the few 10k+ reads compress ~2×; the many small ones ~1×. Net
   in/out just 1.09× even compressing everything.
3. **Output (weight 3)** is the agent's generation — uncompressible by us.
⇒ Compressible content is ~22% of REAL weighted context, and the extraction floor lets us remove only a
fraction of it → **max ~4–8% weighted savings, vs the 10% gate.**

**The only way to reach 10% would be to drop head/tail and keep ~20% of each tool result (≈5×
compression)** — which would (a) strip the file content the agent needs → break swebench solves, and
(b) tank the explore hit−noise quality gate → −2 floor. I.e. the aggression required to pass the
SAVINGS gate fails the PASS and QUALITY gates. **The safe per-message compression lever is not a viable
path to qualify for comp-110 with the copilot agent.** ⇒ escalate: this needs a different lever or a
strategic rethink (see below), not a v4 threshold tweak.

## Proposed LEAN v4 (DESIGN ONLY — SHELVED by the feasibility verdict above; retained for reference)
Goal: clear the ≥10% screener, target ≥20% aggregate weighted savings, up to ~2×/task, without
degrading explore quality (hit−noise) or breaking swebench.
1. **Much lower budgets.** Compress tool + non-final-assistant content above ~2–3k (not 10k). Retune
   profiles around the screener gate: e.g. conservative(mid 4k), target(mid 2.5k), aggressive(mid 1.5k) —
   final numbers set by measuring aggregate savings on a screener-like task.
2. **Keep ALL v3 safety:** whole-line only, quality floor, source-line omission markers (now ESSENTIAL —
   they make aggressive omission locatable so hit−noise holds), fail-open, deterministic, cache-stable, no pin/dedupe.
3. **Reconsider recency (measure, don't assume).** v3 protects the final message — often the largest
   fresh tool read — which directly costs screener savings. With source-line markers making omissions
   safe, compressing the final message too may be necessary to clear 10%. A/B `SOMA_LEAN_RECENCY` for
   savings-vs-break on a real solve.
4. **Prioritize persistent content.** Cached tokens (weight 1/3) dominate the weighted total; compressing
   EARLY big reads pays on every later turn (they stay compressed in the re-sent, cached history). Ensure
   the compression is stable so the cached prefix stays cached (v3 already is).
5. **Compress assistant CoT too** (it's literally "CoT compression") — already allowed in v3; verify it
   engages at the lower threshold.
6. **Explicit feasibility gate BEFORE upload:** run a screener-like swebench_verified solve with v4,
   measure aggregate weighted savings vs a no-script baseline (multiple runs to beat variance), confirm
   ≥10% (ideally ≥20%). If the uncompressible system prompt caps us below 10%, compression alone can't
   qualify and we need a different lever (escalate to USER + team).
Verification bar (same as v3): rules gate, Codex GO, harness (incl. range accuracy + no-partial +
net-reduction + cache-stable), sidecar E2E, champion regression — PLUS the new feasibility gate (#6).
