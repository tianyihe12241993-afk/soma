# CURRENT — detailed status & MacBook handoff (2026-06-22)

_**Mode: POST-COMPETITION RESEARCH** for competition 107 (CoT-Compression, SN114). Completed; we do
NOT submit. Goal: design the strongest next-round miner, evidence-backed, files = source of truth._

## ⏭ CONTINUE ON THE MACBOOK (this Windows/WSL2 box cannot run the real eval)
The only thing left is the **real SWE-bench eval of the H1M candidate**, and it must run on a
**real-Linux Docker host**. macOS Docker Desktop = a real Linux VM (LinuxKit), which works (your past
laptop). WSL2 does NOT (see "Blocker resolution" below).

On the MacBook:
```bash
git clone https://github.com/tianyihe12241993-afk/soma.git && cd soma
export OPENROUTER_API_KEY=sk-or-...            # your key; do NOT commit; ROTATE the one pasted in chat
bash experiments/candidates/H1M_m7_deeper_safe_v1/run_real_eval.sh        # 2-task smoke, ~$ small
# then gate the result:
python3 experiments/candidates/H1M_m7_deeper_safe_v1/h1m_run.py \
  --results experiments/runs/<stamp>_H1M_smoke_real_eval/h1m_smoke_gate.csv
```
STOP after the smoke; confirm before the full Medium-first set. On the FIRST successful solve, check the
token-with/without field names in `output.jsonl` `metadata` (the gate-CSV converter flags them) — that's
the one thing I couldn't finalize (every run here died pre-success due to the WSL2 bug).

## The thesis (proven from per-task data — do not relitigate)
The gap to top miners is **compression DEPTH, not solving/consistency**. On 36 shared-pass tasks: mean
score gap +0.157/task, ratio-model explains +0.231 (residual −0.074). m7 ~3.0× vs leaders ~4.9×.
Flakiness is a near-universal floor (m7 15.3% neg-runs ≈ top-4 14%), NOT our gap. Flip-routing was
net-negative and is permanently dropped. Next direction = **m7-style architecture + deeper pass-safe
compression, Medium-first.**

## H1M_m7_deeper_safe_v1 — candidate status
- **Built** (`experiments/candidates/H1M_m7_deeper_safe_v1/h1m_miner.py`): m7/v11.1 derivative; a PROFILE
  layer deepens ONLY the harvest path (lower TARGET 8k→{7k,6k,5.2k} + tighter caps); RICH path + all
  protections + coach UNCHANGED; fragile guard (ERROR_GUARD_MIN_HITS 4→3) routes still-failing tasks to m7.
  Profiles via env H1M_PROFILE = light|medium|deep; =m7 reproduces baseline exactly. NO routing/flip.
- **Offline-validated** (h1m_eval.py): h1m@deep **+13.7%** compression on 6/6 harvest cases, 0 regressions,
  all protected content kept, no broken pairing, guard fires correctly. A/B (h1m@m7≡m7) holds.
- **Decision gate IMPLEMENTED + PROVEN** (h1m_run.py --results): fixtures PASS→ACCEPT, FAIL→REJECT (rejects
  on safety even when compression improved). Ready to ingest real eval output.
- **Real-task projection** (experiments/runs/2026-06-22_005707_H1M_eval/): REAL m7 Medium-first baseline
  7/7 pass, 0% neg-run, 0 broke, 3.02×, Medium est score 1.690; projected h1m@deep ~3.43×, h1m@medium ~3.34×.
- **Verdict: ADVANCE (candidate-only).** Do NOT promote over m7 until the Mac eval gives real pass-rate /
  neg-run / Medium score. Reports: experiments/reports/H1M_m7_deeper_safe_v1.md.

## Blocker resolution (why the eval must move to the Mac)
The real eval (`soma_bench` + OpenClaw + Docker-in-Docker) fails under WSL2 with
`rm '.openclaw/sandbox-skills/skills': Device or resource busy`. CONFIRMED it's **WSL2, not Docker
Desktop**: reproduces on Docker Desktop AND native docker.io 29.1.3, on openclaw 2026.6.9 + 2026.6.8-beta.2,
root + non-root — only common factor is the WSL2 kernel's mount semantics under DinD. macOS = real Linux VM
→ works. The whole stack + every config fix is captured in the turnkey `run_real_eval.sh`. Full writeup:
reports/H1M_real_eval.md; machine: data/latest/h1m_real_eval_smoke.json.

## Where everything lives
- Candidate + eval: `experiments/candidates/H1M_m7_deeper_safe_v1/` (h1m_miner.py, h1m_eval.py,
  h1m_run.py [gate], run_real_eval.sh [Mac driver], fixtures/).
- Manifests: `experiments/manifests/` (H1–H4 + H1M_real_eval_medium_first.yaml).
- Reports: `reports/` (postmortem, top_miner_comparison, per_category_gap, compression_depth_risk,
  m7_gap_analysis, h1_safe_compression_targets, next_round_strategy, experiment_backlog, label_mapping_audit,
  run_variance) + `experiments/reports/H1M_*.md`.
- Data: `data/raw/` (immutable scrapes + extension-sb114 per-run evidence), `data/processed/` (per-task +
  per-run jsonl), `data/latest/` (json + csv).
- Ops scripts: `scripts/` (collectors, import/normalize, compare, gaps, per_category_gap,
  compression_depth_risk, rank_headroom, run/summarize experiments, checkpoint, setup_wsl_env.sh).
- Config: `config/miners.yaml` (audited m7=v11.1…m11=v24; m9=v22/m10=v18 RESOLVED), top_miners.yaml,
  experiments.yaml, task_categories.csv (E/M/H), secrets.env.example. **secrets.env is git-ignored.**

## Hard rules (still in force)
Do not submit. Do not modify m7 or live miner code. Don't revive flip-routing. Files = source of truth,
not chat. Never commit secrets. Separate observed-platform / local-replay / manual-interpretation.

## Reminders
- **ROTATE** the OpenRouter key and the WSL sudo password (both were pasted in chat).
- To restore this Windows box's Docker: `sudo apt remove docker.io` + re-enable Docker Desktop WSL
  integration (or just keep native docker.io — harmless).
- On the Mac, run `make`/scripts via the repo; the eval is self-contained in run_real_eval.sh.
