# DECISIONS (durable; don't relitigate)

- **m7 / v11.1 is our confirmed best (1.279) and the recipe to protect/replicate.** Everything built on top
  (v15→v18→v22→v24) added persistent-failure flip-routing that, on the platform, *leaked Medium* (v15 → 1.183).
- **Compression is at its ceiling.** Six levers tried (v14 richer, v17 harder, v19 loop-coach, v20 snapshot,
  v21 reasoning-trim, v23 gentler-harvest) — all no-gain or harmful. m7's 8k harvest is the sweet spot.
- **The king's edge (decisiveness + Easy 1.43) is not reachable via compression** — it's agent/model behavior.
  Easy ceiling for us is ~1.13 across gentle/aggressive/adaptive. Stop chasing Easy/overall #1.
- **Shipped v22→m9, v18→m10, v24→m11 (2026-06-17)** as flip "king-shots" on fresh hotkeys (m7 untouched/floor).
  Expectation revised DOWN after v15's platform result: likely ≤ m7 (Medium leak outweighs unmeasurable Hard gain).
- **v26 (depth-gated threshold) validated for a future cycle**, not shipped (m12 unregistered).
- **Reward model is layer-based (7 elements), not top-3.** Winning a single category (~4.8%) is the only realistic
  path for us; overall/pairs need broad strength we lack.
- **Ops/tracking lives here (SOMA-ops). Miner code is NOT edited or submitted from this repo.**
- **PIVOT (2026-06-21): post-competition RESEARCH mode.** Comp 107 completed; we do NOT submit.
  Goal = design the strongest next-round miner offline, evidence-backed. Next direction is fixed:
  **m7-style architecture + deeper PASS-SAFE compression**, NOT more routing. Flip-mode rescue /
  persistent-failure routing / release-flip-on-pass are **permanently dropped** (postmortem: net-negative —
  no pass gain, more broken baselines + negative tasks). Hypotheses H1–H4 in experiments/manifests/.
- **Label audit RESOLVED (2026-06-21):** m9=5CFqU2Ss=v22, m10=5GL4Kxda=v18 (registry, corroborated by 4
  git-tracked files; chat label rejected per "chat ≠ source of truth"). Scores are hotkey-anchored, so
  analysis is label-independent. Full evidence: reports/label_mapping_audit.md.
- **Dev/ops env runs in WSL Ubuntu-22.04** (scope: "miner dev + ops"). One-shot idempotent installer
  `scripts/setup_wsl_env.sh` → venv at `~/.venvs/soma` (Linux fs, fast IO); repo stays at `/mnt/e/soma`.
  Pinned to the repo's known-good set; pin `async-substrate-interface==1.5.15` to avoid the cyscale↔scalecodec
  namespace clash that breaks `import bittensor`. Full guide: `docs/wsl-env.md`. NOT installed (upload-only):
  `soma_shared` (private DendriteHQ repo — sandbox blocks external git installs, user runs it) + a netuid-114 wallet.
