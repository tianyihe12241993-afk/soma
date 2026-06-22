# Research summary
_computed 2026-06-21T16:30:50Z_

- Miners compared: 5 ours + 10 top.
- Per-task rows: 1000 across 50 tasks.
- On the **36 tasks m7 and the top miner both pass**, the mean score gap is **+0.157/task**. The compression-ratio model (0.5·ln(ref/m7)) explains **+0.231/task**, leaving a residual of **-0.074/task** (solving/variance). → the gap is **compression depth, not solving ability**.
- **Missing data:** per-task category on 5/50 tasks (only 45 have E/M/H) → Medium/Hard task-level attribution BLOCKED. Import config/task_categories.csv (see data/raw/platform_results/TASK_CATEGORIES_TEMPLATE.csv).
- Reports: reports/top_miner_comparison.md, reports/postmortem.md, reports/m7_gap_analysis.md.
- Next: reports/next_round_strategy.md + experiments/manifests/ (H1–H4).
