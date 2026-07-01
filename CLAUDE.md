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

**DIRECTION (do not relitigate; current 2026-06-28 ~23:00Z):** Portfolio DROPPED 23.8% → **14.3%** — new king
**5DZLFZj (0.728, E1.105/M0.832/H0.272)** took Overall + Pair(E,M) + Single-E (= 71.4% of pool). We hold only
**np2 Single-M (4.8%) + np3 Pair(M,H) (9.5%) = 14.3%** (both SAFE from the king: its M0.832<np2's 0.849, its H0.272 too low for Pair(M,H)).

⚠️ **#1 OPERATIONAL LESSON — ROUTING (recent craters were INFRASTRUCTURE, not algo/variance):** a **DeepInfra-ONLY pin
= NO FALLBACK** → under heavy eval load DeepInfra saturates → solves TRUNCATE → −4 breaks. This (NOT credits/provider/algo)
cratered m33 (scored 0.216, byte-identical np2), np2c, and likely np_prop (0.487). **FIX (PROVEN): allow ONLY DeepInfra +
Venice** (both cache-effective: DeepInfra primary ~90% hit, Venice fallback 89%-off) and **BLOCK the no-cache providers
(Novita/Google/Alibaba = 0% cache → tank weighted-savings) + AtlasCloud.** Proof: m33's 41 post-fix full-token tasks scored
≈ np2 (1.04× tokens), the 9 pin-truncated tasks (−1.41, 5 breaks) poisoned its total. **KEEP every live miner on DeepInfra+Venice**
— a re-eval under the pin would crater the 14.3% floor. (Provider cache map verified: see reports / 2026-06-28 checkpoints.)

**CATEGORY MAP CRACKED (validated across all miners):** Hard = the **16 baseline-FAIL tasks** (model fails them UNCOMPRESSED)
→ won by **FLIPPING** (+2), they CANNOT break. Easy/Medium = the 34 baseline-PASS tasks (Easy=small, Medium=big). Our −4
breaks are on baseline-PASS Easy/Medium tasks, **NOT Hard**.

**STRATEGY (UPDATED 2026-06-30 — gap DECOMPOSED into breaks + missed-flips; salience/cap32 are real partial levers; full status: `state/CURRENT.md` TOP + `reports/reanalysis_2026-06-29.md`):** The earlier "ALGO SPACE EXHAUSTED → just redraw" verdict was INCOMPLETE. Real per-run decomposition: our 0.044 gap to the king = ~**60% BREAKS** (baseline-pass→fail, −4; django 10% / sympy 13% — BROAD, not sympy-only) + ~**40% MISSED HARD FLIPS** (baseline-fail the king flips & we don't, mostly sympy where np2 OVER-compresses, e.g. sympy-18698 3.27x→1/5). Quality/savings ≈ 0 (we match the king per-token). **TWO LEVERS:** (1) **breaks ← `salience`** — root cause VERIFIED: the extractive pins def/class/errors/tests/diffs/paths but DROPS imports/decorators/raise/except → loses the file API → wrong edit → break; `_STRUCT_PATTERN` pins them (real 32k sympy read: keeps 30/30 imports vs np2's 11/30 at ~same compression). (2) **missed-flips ← `cap32`/fuller-keep** — np2 over-compresses huge Hard contexts; keep them fuller (cap32: ≤53k=np2, >53k cap 32k=np3's proven zone) → flip. **`uphard_salience` (sha 695b4fe4, Codex-GO) = cap32 + salience = BOTH levers**, the lead candidate. Local A/B: salience directionally edges np2 on import-heavy sympy breaks; **a missed-flip A/B (np2 vs cap32 vs salience on sympy-18698) is running** to test the flip lever. ⚠️ **LOCAL EVAL IS AN UNRELIABLE PROXY** (crashes ~50% of tasks, can't run the safe-set) → the **PLATFORM is the only arbiter**; next step = platform-test `uphard_salience` on a spare clean hotkey (read break rate vs np2's 10.6% + Hard flips). **BEST-OF-N is a TAIL LOTTERY, not the play** (DOWNGRADED): np2d1 0.49 + np3-redraw 0.464 = two clean redraws both ~0.46–0.49 ⇒ **0.684 is np2's FAVORABLE draw, not a floor** (~15%/draw beats king) ⇒ **DON'T disturb the live winners** (a re-eval likely redraws them ~0.49 → lose Single-M/Pair(M,H)); protecting the 14.3% floor > chasing. DEFEND: live miners on DeepInfra+Venice (block Google/Novita/Alibaba/AtlasCloud/WandB). New tools: `scripts/vet_draw.py` (account-clean check) + `scripts/check_readme_current.py` (compliance gate) — run BOTH before any hotkey.

**CURRENT SOLUTIONS** (hotkey→label in `config/miners.yaml`; m12 LIVE; ALL uploads USER-run; read ONLY at scored + verify Easy~1.05 binding first; **keep all on DeepInfra+Venice routing**):
- **m12** (`5Dz7…`) — LIVE 0.130. **UNTOUCHED.**
- **np2** (`5CPbtf…`, cap 16k) — LIVE **0.684** (E1.052/M0.849/H0.173). **WINS Single-M (4.8%).** Income.
- **np3** (`5F9ZRe…`, cap 28k) — LIVE **0.682** (E0.859/M0.828/H0.369). **WINS Pair(M,H) (9.5%).** Income.
- **PORTFOLIO = 14.3%** (np2 Single-M + np3 Pair(M,H)). **LOST Pair(E,M)** to the new king.
- **m26 / np1** (`5Ekcy…`, cap 6k) — 0.610 (E1.066).
- **m33** (`5CM1JK…`, = np2 byte-identical redraw) — SCORED **0.216 POISONED** by the DeepInfra-only-pin truncation (9 pin-tasks −1.41/5 breaks). **DISCARD** (not variance — its 41 post-fix full-token tasks scored ≈ np2 = the routing fix PROVEN).
- **VARIANCE DRAWS = THE ACTIVE PLAY** (`reports/variance_draw_plan.md`): **np2d1** (`5FPPav7s…`, np2 redraw, sha a64231c9) — evaluating **0.608** (1 break = django-11551 → likely a Pair(E,M) miss, recovering on total; re-draw for a clean django roll). Run more np2 draws (target Pair(E,M)) + np3 draws (target Overall), EACH on its OWN isolated DeepInfra+Venice account; read at scored (Easy≥0.85 binding → E+M>0.968 / total>0.728).
- **DEAD:** **strelief** (`5DLMDwMm`, sha c70bd40a) SCORED **0.509** = clean fail (relief→WANDER, 7 breaks, no Hard flip); **ehspec** (sha 44caadda) Codex **NO-GO** (per-result Easy/Hard sizes overlap → size-tier can't separate); np_prop (`5FNrjmdT`) 0.487; np2c (`5GCWMTZk`) crater; np2b/np5; nptok (ba18fbd0, token-cap = wrong direction); hardspec (e31cf08a, ≈m26, SKIP); m13/m14/m21/m22/m25/m17 raw-era.
- **NEW KING 5DZLFZj** 0.728 (E1.105/M0.832/H0.272) = Overall+Pair(E,M)+Single-E = **71.4%**. RIVALS: **5GgVXz** (H0.676) = Pair(E,H)+Single-H = 14.3% (the Hard-flip **19% zone**); **5DCnA57** old #1 0.697; **5Ggq** 0.673.

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
  `collect_runs.py` **FIXED 2026-06-29** — gives REAL per-RUN data (run_id/attempt_no/pass/tokens/score/steps, 5/task). The dashboard
  stopped serving the `getSweTaskRunsAction` server action and now EMBEDS per-run rows inline in the page RSC under `sweRunsByTaskId`
  (keyed by task_id); the script parses that directly (no action replay). `--hotkey HK [..]`; writes `*_swe_runs.json` (import-compatible).
- **`scripts/vet_draw.py` (NEW 2026-06-29) — VET a draw's account before trusting its score.** `--hotkey HK` (scrapes per-run) or
  `--from-file *_swe_runs.json`. Computes cache% / timeouts / break% and classifies: CLEAN (cache≥88% & break≤13% → trust) /
  BAD DRAW (break>13%, cache OK → discard score, account fine to redraw) / BAD ACCOUNT (low cache → fix routing). Reference = np2-ORIG
  (5CPbtf: cache 93.9%, break 10.6%, the 0.684 good-account draw). Use on EVERY redraw — the resubmit craters (m33 0.22 / np2b 0.13 / np2d1 0.49)
  were caught by this signature. ⚠️ Calibrated for np2-CLASS light compressors; a Hard specialist (uphard/5GgVXz) breaks more BY DESIGN — judge those on Hard, not break%.
- Category map (E/M/H per task) **CRACKED 2026-06-28** (validated across all miners): **Hard = the 16 baseline-FAIL
  tasks** (per-miner mean over baseline-fail == published Hard, exact). Easy/Medium = baseline-PASS (Easy=small,
  Medium=big baseline-tokens; approximate). Won't drive the miner (task-awareness banned) — it's a DIAGNOSTIC: Hard is
  won by FLIPPING (can't break); our −4 breaks are on baseline-PASS Easy/Medium. Score-inference fails (compressed
  scores cluster near pass-pass); use the baseline-fail signal. Live-trace (`trace_eval_categories.py`) = the other path.

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
