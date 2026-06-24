# CURRENT — live status (2026-06-23, late) — READ FIRST after compaction

_Mode: ACTIVE comp 108 (CoT-Compression-4, SN114). Files = source of truth. Read this + NEXT_ACTIONS +
DISCOVERIES (top entries) + this session's reports before acting._

## ✅ DONE: EXP-1b verdict = HOLD m12, depth is NOT a lever (2026-06-24, full report: reports/exp1b_depth_frontier_verdict.md)
- **Run COMPLETE:** depth-frontier 3-way A/B — m12 (8k LIVE) vs m12_deeper (4k) vs m12_lighter (16k), 6 tasks ×
  RUNS=3 = **54/54 solves, 0 FAILED, 0 429s**. Run dir `experiments/runs/2026-06-23_222022_H1M_pbatch`.
- **VERDICT: HOLD m12. Do NOT change TARGET_TOKENS either way.** Robust signals all favor m12:
  - **Breaks (the −4 swing) rise monotonically away from m12:** m12=1 task < deeper=2 < lighter=3. m12 fewest.
  - **Deeper uses MORE tokens everywhere** (ppBreak 1067k vs 874k) + LOWEST cache-hit (0.80–0.84) + most uncached
    input → agent-wander erases the ratio bonus AND cache-loss worsens the savings gate. Doubly self-defeating.
  - **Lighter ADDED breaks (3 vs m12's 1)** → m12 is NOT over-compressing; run-variance is AGENT/PROVIDER noise,
    not our depth (irreducible via this lever).
  - **Flip sympy-24066 = 0/3 at all depths** → capability/agent-bound, not compression-bound.
  - The only signal favoring deeper (one extra majority-pass on a "clean" task) is the noisiest (m12 flubbed it
    1/3 this window = variance). External lit agrees: ACON finds aggressive compression degrades long-horizon
    agents (reports/cot_compression_literature.md).
- **NEW finding:** aggressive re-compression breaks prompt caching → more billed input → worse savings gate.
  Any future change should be cache-STABLE (append-mostly), not heavy turn-over-turn rewrite.

## What's LIVE / submitted (comp 108)
- **m12 = LIVE/BEST.** hotkey `5Dz7JaCBw6t9ktdRVaLYi3ntEzvCDfb5XmTHyzPdDyT6KS9j`, solution
  `miner/cot_compression/upload_miner_m7_compliant.py` (sha 3c4e3086). **SCORED 0.768 (E0.412/M0.953/H0.919),
  #2, review-PASS.** Key in `config/secrets.env` (the …6c77d/…1e8a lineage). Never replace until something
  BEATS it same-window.
- King `5DFvymSeEw` **0.780** (E0.812/M0.934/H0.596) — #1, beats us ONLY on Easy; we crush Hard (+0.32).
- m13 (5CApy5s5, m12.1b cap design) 0.571 REJECTED. m14 (5DRi5yU6) ~0.42 + m15 (5EX5r3UR) ~0.59: both =
  m14 code (never-inflate) — CONFOUNDED by provider window (not the code); never-inflate confirmed
  byte-identical on H/M. All reference-only. m16 (built, NOT submitted — Easy-narrow dead end).

## STRATEGY (the conclusions, well-evidenced)
- **To beat the king = win the Overall element (57%)** → need Overall-avg +0.058 (m12 0.7615 vs king 0.7807).
  We already win (M,H)+M+H (~19%); king wins Overall+Easy elements. We have field-best M+H; **Easy is the only
  blocker.**
- **Easy is UNREACHABLE via our compliant compression lever** (agent DECISIVENESS / step-count, not compression;
  behavior steering BANNED; 4 candidates m13/m14/m15/m16 failed). DEAD lever.
- **Compression-ratio "headroom" is ILLUSORY** (EXP-1): deeper compression → agent wanders more → tokens UP,
  ratio DOWN. m12's 1.75× is the equilibrium, not under-compression. m7's 2.99× on 107 was task-driven.
- **m12 is near our compliant ceiling.** The score is agent(qwen3-coder)-dominated; compression tweaks
  (depth/cap/never-inflate/light) don't move it. Plan: reports/comp108_strategy_plan.md + comp108_headroom.md.
- **NET: defend M+H (don't touch the harvest); Easy/depth are dead levers; m12 #2 is a strong, near-ceiling hold.**

## EVAL PIPELINE + SPEED (Mac, real SWE-bench, comp-108 tasks)
- Driver `experiments/candidates/H1M_m7_deeper_safe_v1/run_batch_eval_parallel.sh` reads `config/comp108_tasks.txt`
  (50 real comp-108 instances; 107 list retired — comp-108 tasks are 100% different from 107). Profiles wired:
  m12, m12_1b, m14, m16, m12_deeper, m12_lighter. Analyzer `analyze_batch.py [rundir]`.
- **SPEED — SAFE = MAXJOBS=3 ON THIS MAC (settled after 3 failures, 2026-06-24).** Binding limit = patch-eval
  RAM spikes (eval-image build + full test suite = transient multi-GB), NOT steady-state RAM/CPU/OpenRouter.
  MAXJOBS=8 → CPU-stalled (load 15); MAXJOBS=4 → Docker Desktop OOM-CRASHED ~10min in (had to force-kill+relaunch
  Docker); MAXJOBS=3 → PROVEN (EXP-1b 4h, 54/54). Use 3 (~6h/60 solves). Watch `docker info`→MemTotal=0 (OOM) and
  1-sec "ok" solves (bogus). RunPod (more cores+RAM) would genuinely help now. Detail: DISCOVERIES.
- **DISCIPLINE:** platform is TEMPORALLY NOISY (provider window swings Hard ±0.3) → only SAME-WINDOW local A/B
  on comp-108 tasks is trustworthy; never decide off a single platform score; hold key/window constant;
  compliant-only; never read a miner score until status=scored AND runs have non-null agent_steps.

## ⏭ m17 BUILT + offline-VALIDATED (2026-06-24) — paid A/B is the open step
- **m17** = `miner/cot_compression/upload_miner_m17.py` (sha `8ed24474`). ONE change vs m12: the HARVEST
  (`compress_structurally`) intra-result reduction was blind head/tail truncation → now **extractive selection
  THEN a hard head/tail cap** (`_select_then_cap`, active=frozenset() → cache-stable). Pins error/test/diff/path/
  sig lines buried in the MIDDLE of a result that blind truncation drops, at the SAME byte budget (ratio-safe).
  Rich path already had extractive; harvest was the one gap. Report: reports/m17_build.md.
- **Validated offline:** compiles; diff vs m12 = docstring + 4 harvest sites only; compliance scanner PASS; unit
  test (`/tmp/test_m17_unit.py`) = m17 KEEPS 3 buried clues m12 LOSES, +0.2% tokens (ratio-neutral). A 5×-inflation
  bug (extractive can't shrink single-line blobs) was caught by the test and fixed with the truncate cap.
- **OPEN (needs user go-ahead — paid, multi-hour):** same-window comp-108 A/B m12 vs m17, RUNS=5, MAXJOBS=8.
  CAVEAT: m17 ≡ m12 byte-identical on RICH-path (large) tasks; differs only on HARVEST-path (smaller/Pass-likely)
  tasks, and we CAN'T pre-classify which comp-108 tasks hit the harvest (E/M/H not reproducible locally). So the
  A/B must run a harvest-weighted (Pass-labelled) mix. SHIP only if fewer breaks + M/H not regressed + net-positive
  after the savings gate; else HOLD m12. Wired as profile `m17` in run_batch_eval_parallel.sh.

## Candidate files (miner/cot_compression/)
upload_miner_m7_compliant.py (=m12 LIVE) · upload_miner_v11_m7.py (orig m7, NON-compliant, never submit) ·
upload_miner_m17.py (BUILT, validated, A/B-pending) · upload_miner_m12_1.py / _m12_1b.py / _m14.py / _m16.py /
_m12_deeper.py / _m12_lighter.py (all reference).
