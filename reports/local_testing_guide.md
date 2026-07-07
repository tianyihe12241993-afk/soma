# comp-110 LOCAL TESTING — the complete env (2026-07-07)

WHY THIS EXISTS: during the upload window the eval tasks are HIDDEN (validators confirmed), so the ONLY
signal is local testing on PUBLIC instances. This is the authoritative local-testing setup for this repo —
the official guide (SOMA-benchmark/README.md + SOMA/docs/miner/miner-setup.md) plus the macOS fixes and the
measurement pieces the platform does NOT ship locally. Goal: on public instances, measure the SAME three
things the platform scores — solve, weighted-token savings, and explore quality — so we can rank candidates
before spending a hotkey.

## 0. What the platform scores (targets to reproduce locally) — see reports/comp110_scoring_rederivation.md
- 3 benchmark types = the reward categories: `swebench_verified`, `swe_explorer_explore`, `swe_explorer_edit`.
- Screener (upload gate): pass ≥50% of screener tasks AND ≥20% aggregate WEIGHTED savings on swebench_verified.
  weighted = 1·input + (1/10)·cached + 3·output  (⚠ cached/gate are IN FLUX — re-derive when the watcher fires).
- Explore layer: gate(quality margin, δ=0.20) × tau(2·log2(weighted savings)); quality = hit_file_rate − noise_file_rate (file-level).

## 1. Prerequisites (DONE on this MacBook)
- `~/joshua-work/SOMA-benchmark` + `~/joshua-work/SOMA-plugin` cloned (keep `git pull` current).
- venv `~/.venvs/soma` (bittensor + soma_shared) — for the UPLOAD path only, not local eval.
- `uv` present; `uv sync` done in SOMA-benchmark (the eval env).
- Docker images built: `local/copilot-cli:latest`, `soma-copilot-compression-service:latest`.
- copilot-cli-container/.env present (USER-created; non-secret template copy). OpenRouter key in config/secrets.env.

## 2. macOS FIXES (required — the copilot backend assumes a Linux host)
1. **`modprobe` shim** (host lacks it → network-isolation setup crashes). Recipe: reports/local_eval_macos_recipe.md.
   `mkdir -p ~/.soma-shimbin && printf '#!/bin/sh\nexit 0\n' > ~/.soma-shimbin/modprobe && chmod +x ~/.soma-shimbin/modprobe`
   then prepend `~/.soma-shimbin` to PATH.
2. **Keep network isolation ON** (default). Do NOT set SOMA_COPILOT_NETWORK_ISOLATION=false — that UNWIRES the
   compression sidecar (the miner never fires). The shim lets isolation "logically on" while its iptables
   enforcement degrades harmlessly on macOS.
3. **Model/provider:** `--model deepseek/deepseek-v4-pro`; OPENROUTER_API_KEY sourced from config/secrets.env;
   OpenRouter account must have DeepSeek provider + Data Collection enabled.

## 3. THREE things we measure locally (the platform doesn't ship these locally)
### (a) Does the miner FIRE + how much does it compress (per-request)
Run with `SOMA_COPILOT_KEEP_STACK=true`, then `docker logs <compression-service container>`:
count `[messages.in]`/`[messages.out]`; the miner fired iff transform calls > 0; in/out char ratio = the
direct, path-independent compression it applied. (This is how we proved LEAN/SKELETON fire.)
### (b) WEIGHTED-TOKEN SAVINGS (the screener + tau input)
Run the instance WITH the miner and WITHOUT (no `--copilot-compression-script-path` = no-op baseline). From
each run's `output.jsonl` metadata.token_usage: `weighted = 1·input + cached_weight·cached + 3·output`.
savings = 1 − miner_weighted/baseline_weighted. ⚠ n=1 is dominated by TRAJECTORY VARIANCE — run several
instances and aggregate; the fixed-trajectory replay (retune_harness.py on captured payloads) isolates the
context-savings component variance-free.
### (c) EXPLORE QUALITY (the explore gate) — LOCAL SCORER (new capability)
The SWE-Explore-Bench ground truth (`read_core_files`) IS resolvable locally. `scripts/score_explore_local.py`
computes hit_file_rate/noise_file_rate/quality from the agent's regions (explore-result) vs the ground truth,
and the explore gate·tau. Run it under the benchmark env:
  `cd ~/joshua-work/SOMA-benchmark && uv run python .../scripts/score_explore_local.py --instance-id ID --output-dir OUT [--baseline-quality Q --miner-weighted M --baseline-weighted B]`
VERIFIED against real ground truth (django-14017: 3/4 core hit → quality 0.50 → gate·tau computed). Faithful
reconstruction of the file-level metric names; the platform is the arbiter, but this ranks candidates locally.

## 4. Turnkey runner
`experiments/candidates/SKELETON_comp110_v1/local_eval.sh` — runs one instance across the 3 benchmark types,
miner (+ optional baseline), with all macOS fixes + keep-stack firing/token capture, then calls the explore
scorer. Params: `INSTANCE`, `MINER` (script path, default skeleton_v2), `TYPES`, `BASELINE=1`, `PROFILE`.
⚠ Each solve spends OpenRouter credits (~$ small) and takes minutes; running miner+baseline × 3 types ≈ 6 solves.

## 5. Recommended local-eval protocol (when the formula lands & we resume)
1. Pick 3–5 public instances with LARGE reads (django db/models, sympy core) so compression engages.
2. For each: baseline + miner on all 3 types (`BASELINE=1 TYPES="swebench_verified swe_explorer_explore swe_explorer_edit"`).
3. Aggregate: weighted savings per type (does swebench clear the current gate?), explore quality (hit−noise vs baseline → gate),
   solve/resolved (swebench_verified + edit), firing confirmation. Compare miner profiles (safe/target/deep) + vs no-op.
4. Beat variance: ≥3 instances; trust the AGGREGATE, not any single run. The platform (5×N runs) is the final arbiter.

## 6. Honest limits of local testing
- Public instances ≠ the hidden eval set (different tasks); local ranks DIRECTION + relative quality, not the exact score.
- Explore hit/noise is a reconstruction of the metric names (exact validator formula hidden).
- n=1 token totals are variance-dominated (real lever incl. trajectory/output length); aggregate + use the fixed-traj replay.
- The score formula is IN FLUX — re-derive constants (comp110_scoring_rederivation.md) + re-run retune_harness before trusting numbers.
