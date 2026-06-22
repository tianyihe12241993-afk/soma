# NEXT_ACTIONS (handoff to the next session)

_Mode: post-competition research. Files are the source of truth. Env: WSL `source ~/.venvs/soma/bin/activate`._

## H1M real-task experiment — DONE offline (2026-06-22): experiments/runs/2026-06-22_005707_H1M_eval/
- m7 Medium-first baseline (REAL): 7/7 pass, 0% neg-run, 0 broke, avg 3.02×, Medium est score 1.690.
- h1m@deep projected ~3.43× (+13.7%), h1m@medium ~3.34× (+10.8%); offline gate PASS (ratio≥8%, guard works,
  protections intact). Verdict: **ADVANCE candidate-only**. Real pass/neg-run/broke = **PENDING_EVAL**.
- [x] ~~Implement + prove the full ingestion gate~~ — DONE (2026-06-22): `h1m_run.py --results <file>` now
      parses real per-task results, computes candidate pass/neg-run/broke/ratio/Medium-score, diffs vs m7,
      and emits ACCEPT/REJECT. Proven end-to-end with fixtures/h1m_deep_results_{PASS,FAIL}.csv
      (PASS→ACCEPT; FAIL→REJECT on 4 safety checks while compression still +15% — rejects on safety, not ratio).
- [x] ~~Build the real SWE-bench eval stack~~ — DONE (2026-06-22): Docker up; SOMA-benchmark + SOMA-plugin
      (public) cloned; uv + soma-bench; SWE-rebench harness (swebench 4.0.3); compression-service image built;
      m7 miner injected + compression service live; model openrouter/qwen/qwen3-coder. Driver:
      experiments/candidates/H1M_m7_deeper_safe_v1/run_one_solve.sh. .env at ~/SOMA-benchmark (key redacted/600).
- [x] ~~Real eval blocked~~ — DIAGNOSED 2026-06-22: it's **WSL2**, not Docker Desktop. The OpenClaw sandbox-skills `rm` (Device-or-resource-busy) reproduces on Docker Desktop + native docker.io, 2 openclaw images, root+non-root — only common factor is the WSL2 kernel's mount semantics under DinD. Past working laptop was **macOS (LinuxKit VM)** -> real-Linux mounts work.
- [ ] **Run the eval on a real-Linux Docker host (your Mac / Linux VM / cloud).** One command: clone this soma repo there, `export OPENROUTER_API_KEY=...`, then `bash experiments/candidates/H1M_m7_deeper_safe_v1/run_real_eval.sh` -> smoke (m7/h1m@medium/h1m@deep on 2 tasks) -> gate CSV -> `h1m_run.py --results`. STOP after smoke; confirm before full Medium-first. NOT possible under WSL2.

## Highest leverage — CANDIDATE 1 BUILT; needs platform eval next
- [x] ~~Build the H1 candidate, Medium-first~~ — DONE: H1M_m7_deeper_safe_v1 (experiments/candidates/).
      Offline-validated: h1m@deep +13.7% deeper, 0 regress, protections+pairing intact, fragile guard works,
      A/B(h1m@m7≡m7) ok. Report: experiments/reports/H1M_m7_deeper_safe_v1.md.
- [ ] **RUN H1M on the SOMA SWE-bench eval** (the ONE thing offline can't do): get real pass-rate / neg-run /
      Medium score for h1m@deep (+ medium fallback) on the Medium-first H1 targets. Needs the eval env
      (Docker+agent+OpenRouter). Then dump per-task results → `python scripts/run_experiment_matrix.py
      --manifest experiments/manifests/H1_*.yaml --results <file>` → `make summarize` → apply the gate.
- [ ] Only AFTER the eval confirms Medium pass-rate/neg-run hold: decide whether H1M_deep replaces m7 as base.
- [ ] **Add the H3 fragile guard for ~4 signatures only:** sympy-17139 (m7), + sympy-16766 / django-11239 /
      django-14493 (flip-only). Conservative near-pass-through fallback; do NOT touch the safe targets.
- [ ] **Do NOT chase the 2 solving-gap Hard tasks with compression** (django-14999, sympy-22714) — m7 fails
      where the leader solves; that's agent behavior, not our compression lever.
- [ ] **Run it through the gate:** local replay → dump per-task results → `python scripts/run_experiment_matrix.py
      --manifest experiments/manifests/H1_*.yaml --results <file>` → `make summarize`. Gate in experiment_backlog.md.

## Detailed data — SOLVED (keyless)
- [x] ~~Get ALL detailed data incl per-run~~ — DONE. `make runs` (scripts/collect_runs.py) scrapes per-run
      keyless via the dashboard server action; `scripts/normalize_run_scores.py` → data/processed/run_scores.jsonl
      + reports/run_variance.md. No API key needed (earlier conclusion corrected).
- [x] ~~task→category map~~ — DONE (config/task_categories.csv from extension-sb114). Medium/Hard unblocked.
- [ ] Optional: `make runs ARGS="--all"` for a full-field per-run sweep of ALL ~228 miners (~20 min, polite throttle).

## Remaining missing data (marked, not invented)
- [ ] **task→category map** (E/M/H per of the 50 tasks). Fill `config/task_categories.csv`
      (template: `data/raw/platform_results/TASK_CATEGORIES_TEMPLATE.csv`), then `make research`.
      Unblocks: Medium/Hard task-level attribution, H2_medium_specialist, the Medium gate.
- [ ] **token-type split** (input / cached-input / output per task) for H4 weighted-cost readiness.
      Add columns to the import schema when available.
- [ ] (Optional) **platform upload receipts** (hotkey+version+timestamp) → close the label audit to 100%.

## Hygiene
- [ ] Re-run `make detail` periodically only if you want fresher rival scrapes (comp is over; board is static).
- [x] ~~WSL env + soma_shared~~ — DONE (env ready; soma_shared 0.1.0 in venv). Upload path needs only a wallet,
      but we are NOT submitting, so wallet is not required for research.

## First three experiments to run (priority)
1. **H1_m7_deeper_safe_compression** — primary lever (ratio ↑ without breaking passes).
2. **H3_fragile_task_guard** — protect the broke-baseline cases so H1 can push safely.
3. **H2_medium_specialist** — our closest reward element; BLOCKED until task→category map imported.
