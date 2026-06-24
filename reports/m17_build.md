# m17 build — content-selective harvest (2026-06-24)

_Built per user direction ("Build m17, content-selectivity"). m17 = m12 with ONE change. NOT submitted; m12
stays LIVE. Reference/candidate until the same-window A/B gate passes._

## What m17 is (single variable vs m12)
File: `miner/cot_compression/upload_miner_m17.py` (sha `8ed24474`). Base: m12 = `upload_miner_m7_compliant.py`.
The ONLY behavioral change: in `compress_structurally` (the HARVEST path), each over-budget tool result's
intra-result reduction was **blind head/tail `truncate_message`**; it is now **extractive selection then a hard
head/tail cap** (`_select_then_cap`):
- `extractive_message(budget, active=frozenset())` — pins error / failing-test / diff / file-path / code-signature
  lines and fills the rest by TF-IDF (the SAME engine the rich path `compress_gently` already uses).
- then `truncate_message(head, tail)` at the SAME byte cap m12 used — guarantees the compression ratio.
Assistant truncation, routing, dedup, drops, escalation, markers, loop guard = byte-for-byte m12.

## Why this is the right lever (from the analysis)
- m12's RICH path already uses extractive (content-selectivity is the literature's idea, already implemented).
  The HARVEST was the one compressor still cutting blind — it protected error-bearing results at WHOLE-result
  granularity but lost clues buried in the MIDDLE of a result. m17 closes exactly that gap.
- Cache-stable: `active=frozenset()` → selection is a pure function of message text (no sliding-window
  dependence) → old prefix stays byte-stable turn-over-turn → avoids the EXP-1b cache-invalidation cost.
- Ratio-safe by construction: the final `truncate_message` enforces the same per-result byte cap as m12, so
  compression ratio ≤ m12 in every case (extraction only changes WHICH bytes survive within the budget).

## Validation (offline, before any paid eval)
- **Compiles** (ast.parse OK). **Diff vs m12** = only the docstring + 4 harvest sites + the `_select_then_cap`
  helper. Nothing else.
- **Compliance scanner PASS** (`scripts/check_prompt_compliance.py`) — identical to m12 (only allowed CMP/BLOCK
  markers + allowed loop-reason strings; no LLM call, no task-id, no steering).
- **Unit test** (`/tmp/test_m17_unit.py`) on a bulky result with load-bearing lines buried in the MIDDLE:
  | buried clue | m12 | m17 |
  |---|---|---|
  | code signature | LOST | **KEPT** |
  | failing-test (`FAILED ... AssertionError`) | LOST | **KEPT** |
  | diff hunk (`diff --git`) | LOST | **KEPT** |
  Ratio: m17 3937 vs m12 3928 tokens = **+0.2%** (ratio-neutral). HYPOTHESIS VALIDATED at unit level.
- **Bug caught + fixed by the test:** first design (extractive only, no cap) inflated tokens **5×** on
  single-line/few-line blobs (JSON/minified/long unbroken logs) that line-granularity extraction can't shrink.
  The `_select_then_cap` (extractive THEN truncate) fixes it: line-structured results shrink under the cap (cap
  is a no-op, clues kept); single-line blobs fall through to m12's exact truncate (ratio identical).

## Open item for the gate (why the A/B needs care)
m17 differs from m12 ONLY on harvest-path tasks (smaller/pass-likely). Large/deep/error-heavy tasks route to
RICH, where m17 is byte-identical to m12. **We cannot pre-classify comp-108 tasks by harvest-vs-rich** (E/M/H is
a platform-relative rank not reproducible locally; `config/task_categories.csv` covers a different task set, not
comp-108). So the A/B must either (a) run a harvest-weighted mix (Pass-labelled tasks lean harvest) and observe
where m12/m17 diverge, or (b) first do a FREE local replay of m17-vs-m12 compression on the existing EXP-1b
trajectories to identify which tasks are harvest-path, then scope the paid A/B to those.

## Gate (ship criteria — unchanged bar)
Same-window comp-108 A/B (m12 vs m17), RUNS=5, MAXJOBS=8. Ship to a fresh hotkey (same OpenRouter key, m12 left
LIVE) ONLY if: **fewer breaks** AND **M/H not regressed** (byte-identical on rich-path tasks by construction; must
not regress on harvest tasks) AND **net-positive after the weighted-savings gate**. Else HOLD m12.

## Driver
Wired as profile `m17` in `run_batch_eval_parallel.sh`. Run:
`MAXJOBS=8 RUNS=5 PROFILES="m12 m17" TASKS="..." bash experiments/candidates/H1M_m7_deeper_safe_v1/run_batch_eval_parallel.sh`
