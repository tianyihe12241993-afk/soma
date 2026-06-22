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

## Data flow
`make collect` → immutable raw snapshot in `data/raw/dashboard/DATE/TIME_leaderboard.json`
→ `make reward` (normalizes + computes the 7 reward elements) → `data/latest/category_winners.json`
+ `reports/reward_projection.md`. `make status` shows where we stand; `make checkpoint` saves state.

## Post-competition RESEARCH mode (current)
Competition 107 is **completed — we do NOT submit**. The goal is offline research to design the
strongest next-round miner. **Direction (do not relitigate): m7-style architecture with deeper
PASS-SAFE compression, backed by per-task evidence — NOT more routing.** Flip-mode rescue /
persistent-failure routing / release-flip-on-pass are **permanently dropped** (postmortem proved
net-negative).

Research data flow:
`make runs` (KEYLESS per-run scrape via the dashboard server action — the correct detailed source;
`make detail` is the per-task-only RSC fallback) → `make import` (→ `miner_task_scores.jsonl` +
`run_scores.jsonl`) → `make gaps` (shared_pass / compression_gap / fragile + `m7_gap_analysis.md`)
→ `make compare` (`top_miner_comparison.md`, `postmortem.md`, `scoreboard.json`)
→ `make experiments` (scaffold vs m7 baseline) → `make summarize`. `make research` runs the chain.
Per-task CATEGORY (E/M/H) comes from `config/task_categories.csv`. Detail tools are KEYLESS (no API key).

Research rules (in addition to the hard rules above):
- **Separate three truth-levels** in every record: *observed platform result* (`source:platform`),
  *local replay result* (`source:local`, treat as NOISY), *manual interpretation* (e.g. the
  `score≈1+0.5·ln(ratio)` model — label it, never store it as observed).
- **Never invent scores.** If data is missing, write an IMPORT_TEMPLATE and mark it missing
  (current gaps: per-task category map; token-type split).
- **Hotkey→version comes from `config/miners.yaml`** (audited in `reports/label_mapping_audit.md`).
  On any label mismatch, STOP and update the audit before analyzing. Scores are hotkey-anchored.
- **Candidates are based on m7.** A candidate is REJECTED if broken baselines rise, Medium drops,
  or avg ratio doesn't improve meaningfully (gate in `reports/experiment_backlog.md`).
- Keep all future prompt/coach content within **public allowed-prompt rules** (loop-detection +
  forced-stop only; no workflow steering).

## Reward model (summary; full math in scripts/compute_reward_elements.py)
Incentive is split across **7 elements** (not top-3): Overall(E,M,H) weight 1; pairs (E,M),(E,H),(M,H)
weight 1/6 each; singles (E),(M),(H) weight 1/12 each. Each element's winner = highest average score
on that category subset. **Failed-review miners are excluded.** A miner earns the summed weight of the
elements it wins. Winning only a single category (e.g. Medium) still earns ~4.8% of the pool.
