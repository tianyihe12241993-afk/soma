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

## Reward model (summary; full math in scripts/compute_reward_elements.py)
Incentive is split across **7 elements** (not top-3): Overall(E,M,H) weight 1; pairs (E,M),(E,H),(M,H)
weight 1/6 each; singles (E),(M),(H) weight 1/12 each. Each element's winner = highest average score
on that category subset. **Failed-review miners are excluded.** A miner earns the summed weight of the
elements it wins. Winning only a single category (e.g. Medium) still earns ~4.8% of the pool.
