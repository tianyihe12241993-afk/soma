# Top-miner comparison
_computed 2026-06-21T16:30:50Z — recomputed from data/processed/task_matrix.jsonl_

On the **36 tasks m7 and the top miner both pass**, the mean score gap is **+0.157/task**. The compression-ratio model (0.5·ln(ref/m7)) explains **+0.231/task**, leaving a residual of **-0.074/task** (solving/variance). → the gap is **compression depth, not solving ability**.

| miner | ours | total | E | M | H | mean ratio | median | pass | broke | neg |
|-------|------|-------|---|---|---|-----------|--------|------|-------|-----|
| t1 |  | 1.460 | 1.171 | 1.480 | 1.712 | 4.83× | 4.08× | 39 | 1 | 5 |
| t2 |  | 1.436 | 1.255 | 1.437 | 1.606 | 4.93× | 4.64× | 37 | 2 | 4 |
| t3 |  | 1.415 | 1.192 | 1.620 | 1.421 | 4.95× | 4.51× | 38 | 1 | 6 |
| t4 |  | 1.410 | 1.347 | 1.127 | 1.751 | 3.06× | 1.88× | 40 | 0 | 3 |
| t5 |  | 1.355 | 1.126 | 1.279 | 1.646 | 2.40× | 1.64× | 39 | 2 | 5 |
| t6 |  | 1.335 | 1.281 | 1.197 | 1.525 | 2.88× | 1.80× | 39 | 1 | 4 |
| **m7** | ✓ | 1.279 | 1.127 | 1.421 | 1.281 | 2.99× | 2.50× | 38 | 1 | 3 |
| t7 |  | 1.263 | 1.156 | 1.312 | 1.316 | 4.74× | 4.68× | 37 | 1 | 4 |
| t8 |  | 1.256 | 1.252 | 1.059 | 1.455 | 2.86× | 2.72× | 38 | 2 | 4 |
| t9 |  | 1.222 | 1.220 | 1.423 | 1.024 | 2.81× | 2.34× | 36 | 1 | 3 |
| **m8** | ✓ | 1.159 | 1.057 | 1.183 | 1.230 | 2.84× | 2.69× | 36 | 0 | 2 |
| t10 |  | 1.158 | 1.373 | 1.191 | 0.924 | 5.24× | 4.06× | 33 | 2 | 8 |
| **m11** | ✓ | 1.038 | 0.943 | 1.030 | 1.135 | 2.70× | 2.48× | 36 | 1 | 7 |
| **m9** | ✓ | 0.937 | 1.165 | 0.931 | 0.728 | 2.64× | 2.39× | 33 | 3 | 9 |
| **m10** | ✓ | 0.916 | 1.029 | 1.073 | 0.653 | 2.66× | 2.44× | 33 | 2 | 8 |

_Category scores (total/E/M/H) are scraped platform aggregates; ratio/pass/broke/neg are recomputed per-task. Top miners win on RATIO at equal pass-rate (see postmortem)._
