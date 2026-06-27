# SOMA-ops — operating rules (read before doing anything)

This workspace exists because **Claude Code sessions are disposable and compaction
loses chat detail.** The **source of truth is the files in this repo, not chat history.**

## Start-of-work protocol (every session, especially after compaction/resume)
1. Read, in this order:
   - `state/CURRENT.md` — what's going on right now
   - `state/NEXT_ACTIONS.md` — what to do next
   - `state/DECISIONS.md` — decisions already made (don't relitigate)
   - `state/SCOREBOARD.md` — miner scores / standings
   - the latest entry in `sessions/` (newest `*.md`) and `state/latest.md`
2. Or just run `make context` (prints the compact block; the SessionStart hook does this automatically).
3. **Never rely on chat history as the source of truth.** If it's not in a file, it didn't happen.

## During work
- After every important result, **update `state/latest.md`** (the checkpoint does this) and
  append a checkpoint: `make checkpoint NOTE="what changed"`.
- Record durable decisions in `state/DECISIONS.md`, findings in `state/DISCOVERIES.md`,
  risks in `state/RISKS.md`, and the live board in `state/SCOREBOARD.md`.
- Keep `state/NEXT_ACTIONS.md` current — it's the handoff to the next session.

## Hard rules (enforced by hooks where possible)
- **Never write secrets into git-tracked files.** Secrets live only in `config/secrets.env` (git-ignored).
- **Never submit or modify miner code unless explicitly instructed.** This repo is for *ops/tracking*,
  not for editing or uploading miners. Miner solution files live elsewhere (`/Users/user/SOMA/miner/...`).
- **Dashboard raw snapshots are immutable** — never overwrite or edit anything under `data/raw/`.
  Collect new snapshots; normalize/derive everything else.
- Don't let hooks make strategy decisions or auto-submit anything. Hooks only checkpoint, reload
  context, guard protected files, and audit.

## Dual-agent review protocol (Claude Code + Codex)
Use the two models **adversarially, not redundantly** — one generates, the other tries to refute.
**Disagreement is the signal** (it points at the wrong assumption); when they agree, that is higher
confidence, **not proof**. The **platform-`scored` result is the only real arbiter**, and the **USER decides**
(cross-model agreement is a recommendation). The repo (`state/` + `reports/`) is the **shared handoff** —
point Codex at it instead of re-explaining.
- **Roles.** *Claude Code* = driver / orchestrator / `state/` owner: long-context research, Workflow
  fan-out, building candidates, maintaining `state/`+`reports/`. *Codex* = **independent verifier / red-teamer**
  at decision gates — give it the artifact + the claim + a mandate to break it.
- **Three mandatory gates — Codex reviews INDEPENDENTLY before the action:**
  1. **Pre-upload miner audit** (the most expensive mistake = a broken / confounded / non-compliant upload).
     Before any hotkey is spent, Codex audits the candidate **diff-vs-m12**: compliance (allowed markers only,
     no steering, no task/category awareness, no LLM calls), Hard-safety, and the gate/decouple logic. A Codex
     NO-GO blocks the upload until reconciled.
  2. **Load-bearing-number re-derivation.** Any decision-driving number (element ownership, compression ratios,
     the scoring formula, penalty math) — Codex recomputes it from the raw JSON independently. Match → trust;
     mismatch → STOP and dig before acting. (This session shipped several numbers I flagged "couldn't verify".)
  3. **Strategy red-team at NO-GO / build forks.** Before "build X" or "this lever is dead", Codex attacks the
     verdict and tries to find the path that was missed.
- **Mechanics.** Sequence, don't collide: **Claude writes → Codex reviews READ-ONLY → reconcile → user decides.**
  Parallel build experiments go in a separate git worktree/branch. Use gstack `/review` (Claude self-pass) then
  `/codex` (independent OpenAI pass); reconcile disagreements, never just pick the answer you like.
- **Discipline.** Insert Codex at these gates, **not every edit** (cost only pays if it raises catch-rate).
  Two models can share a blind spot → agreement ≠ truth; the scored platform result settles it. m12 stays LIVE
  and miner uploads stay USER-run regardless of either model's confidence.

## Data flow
`make collect` → immutable raw snapshot in `data/raw/dashboard/DATE/TIME_leaderboard.json`
→ `make reward` (normalizes + computes the 7 reward elements) → `data/latest/category_winners.json`
+ `reports/reward_projection.md`. `make status` shows where we stand; `make checkpoint` saves state.

## ACTIVE comp-108 mode (CoT-Compression-4) — WEIGHTED-TOKEN regime (current)
We are in an **ACTIVE** competition and **DO submit** (separate hotkeys; **m12 stays LIVE**). The
"post-comp-107 research / deeper-compression" framing is OBSOLETE.

⚠️ **SCORING REGIME CHANGED 2026-06-26** (DendriteHQ/SOMA commit `b79fcaee`, LIVE; verified from
`mcp_platform/.../scoring.py`). The old raw-token "compress hard for the ratio bonus" era is DEAD:
- per-run = `base + λ·Trim(ln(weighted_baseline / weighted_miner), −2, +2)`, where
  **`weighted_tokens = 1.0·input + (1/3)·cached + 3.0·output`**.
- base: pass-pass **+1**, FLIP **+2** (was +4), BREAK **−4**, fail-fail **0**; λ = {0.5, 0.5, 0, 0.1}.
  The total savings multiplier also uses weighted tokens.
- ⇒ **DOMINANT LEVER = CACHE-STABILITY.** A byte-stable emitted PREFIX is cached at 1/3 weight;
  cache-busting compression (rewriting the prefix each turn) now scores NEGATIVE. Avoiding a break is
  worth 2× landing a flip. Output is ~1% of tokens (the 3× weight is a near-red-herring in aggregate).
- The re-score flipped the field: **m12 (our old #1, aggressive harvest) cratered 0.768→0.130**;
  **near-passthrough 5DCnA57 is now #1 (0.697, wins the Overall element = 57% of pool)**. We REBUILT
  cache-stable (np1/np2/np3) → from m12's 0% to **23.8% of the pool** (see below).
  Mechanism + numbers: `state/CURRENT.md` (top) + `reports/cache_stable_design.md`.

**DIRECTION (do not relitigate; current 2026-06-27):** the cache-stable **near-passthrough** lineage is
BUILT and WORKING (m12 0% → 23.8%). The flat per-message cap is a ~ZERO-SUM **E↔H lever** (np1 6k = max-Easy/
low-M&H; np2 16k = max-Medium; np3 28k = max-Hard/lower-Easy) and we now own **BOTH its corners**:
Pair(E,M)+Single-M (np2) and Pair(M,H) (np3). **NEXT TARGETS (USER-set 2026-06-27): (1) Single-E (+4.8%,
NEAR-FREE — m26 E1.066 vs 5DCnA57 1.067, only −0.001) and (2) the OVERALL element (57%, 5DCnA57 0.703).**
Overall needs ONE miner HIGH on E AND H at once — the flat cap CANNOT give that (zero-sum); it needs a NEW
mechanism, **NOT a better flat cap** (better-extractive np4 was NO-GO: Hard-block critical content is SPREAD
22–63k and np2 already keeps it; a "balanced middle cap" wins NO element — the reward pays SPECIALISTS/corners,
not balance). DEAD: aggressive harvest drop/prune (busts cache); aow_bet state-carryover (m21/m22 Hard-crater).

**CURRENT SOLUTIONS** (hotkey→label in `config/miners.yaml`; m12 stays LIVE regardless; ALL uploads USER-run):
- **m12** (`5Dz7…`, `upload_miner_m7_compliant.py`) — LIVE, 0.130 (cache-busting harvest). **UNTOUCHED.**
- **m26 / np1** (`5Ekcy…`, `upload_miner_np1.py`) — cache-stable near-passthrough, cap 6k. **#5, 0.610**
  (E1.066/M0.620/H0.170). Our **Easy weapon** — E1.066 is 0.001 from Single-E. Wins no element yet.
- **np2** (`5CPbtf…`, `upload_miner_np2.py`) — cap 16k. **#2, 0.684** (E1.052/M0.849/H0.173). **WINS
  Pair(E,M) 0.951 + Single-M 0.849 = 14.3%.** Our income.
- **np3** (`5F9ZRe…`, `upload_miner_np3.py`) — cap 28k. **#3, 0.682** (E0.859/M0.828/H0.369). **WINS Pair(M,H) 0.599 = 9.5%.**
- **PORTFOLIO = 23.8%** (np2 14.3% + np3 9.5%). RIVALS: **5DCnA57** #1 0.697 (wins Overall + Single-E = 61.9%);
  **5GgVXzUB** (E0.845/M0.252/**H0.676**, legit-scored) wins Pair(E,H) + Single-H = 14.3%; **5Ggq** "old king" #2 0.673.
- Raw-token-era & DEAD: m13/m14/m21/m22 rejected, m17 not-qualified, m25 (0.449) obsolete.

**EVAL PIPELINE** (runs on this Mac, Docker Desktop — NOT WSL):
- e2e local solve: `experiments/candidates/H1M_m7_deeper_safe_v1/run_batch_eval_parallel.sh`
  (`PROFILES="m12 m26 …" RUNS=n TASKS="inst:Cat …" MAXJOBS=3`; qwen3-coder via OpenRouter; analyzer
  `analyze_batch.py`). Each solve's `output.jsonl` has `token_usage` (input/cache_read/output) + assemble mode.
- **Cache-stability validation (deterministic, no-network):** `scripts/prefix_stability.py` (byte common-prefix
  of consecutive outputs = what the provider cache rewards — the REAL test), `scripts/window_bound_check.py`
  (output ≤ native + 0 orphans), `scripts/analyze_cache.py` (cache% + weighted/raw). **Local OpenRouter
  `cache_read` is NOISE** (TTL-dependent) — judge cache-stability by `prefix_stability`, the actual score by the PLATFORM.
- **Keyless dashboard scrape:** `make collect` (leaderboard, works). `collect_miner_detail.py` = per-miner
  detail page (category means + per-task scores + token splits; comp_id FIXED 107→108 in `config/dashboard.yaml`).
  `collect_runs.py` action-id auto-discovery is BROKEN (not needed — the detail page carries everything).
- Category map (E/M/H per task) is task-intrinsic but NOT in the data; recover via live-trace
  (`scripts/trace_eval_categories.py` + `solve_eval_categories.py`) — **SECONDARY** (cache strategy is category-agnostic).

**Discipline (in addition to the Hard rules):**
- Separate truth-levels: observed PLATFORM (`source:platform`, the only arbiter) vs LOCAL replay (NOISY,
  esp. `cache_read`) vs manual interpretation (label it, never store as observed). Never invent scores.
- **READ scores ONLY at `status=scored`** (never `evaluating`/`screening`). Hotkey→version from `config/miners.yaml`
  (on a label mismatch STOP and fix the registry first).
- A candidate must be **CACHE-STABLE** (`prefix_stability` ≥ ~99%), **bounded** (≤ native), **compliant**
  (allowed markers only), and pass the **Codex pre-upload audit** before a hotkey is spent. m12 stays LIVE; uploads USER-run.
- Compliant only: loop-detection + allowed markers (`[[CMP]]`/`[[BLOCK N]]`/`Same response as in [[BLOCK N]].`);
  NO steering, NO LLM/API calls in the compressor, NO task/category/benchmark-ID awareness.

## Reward model (summary; full math in scripts/compute_reward_elements.py + reports/cache_stable_design.md)
Incentive splits across **7 elements** (unchanged): Overall(E,M,H) weight 1; pairs (E,M),(E,H),(M,H) 1/6
each; singles (E),(M),(H) 1/12 each. Element winner = highest average on that category subset (failed-review
excluded). Winning one single ≈ 4.8% of the pool. **PER-RUN SCORE (CHANGED 2026-06-26 — weighted tokens):**
`base + λ·Trim(ln(weighted_baseline/weighted_miner),−2,+2)`; `weighted = 1·input + (1/3)·cached + 3·output`;
base {pp +1, FLIP +2, BREAK −4, ff 0}, λ {0.5,0.5,0,0.1}; savings multiplier also weighted ⇒ **cache-stability
dominates** (see ACTIVE comp-108 mode above).
