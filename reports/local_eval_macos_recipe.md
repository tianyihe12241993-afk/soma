# Local copilot-stack eval on macOS — setup recipe + blockers (2026-07-07)

The comp-110 agent is the GitHub Copilot CLI in a Docker Compose stack (copilot + proxy +
compression sidecar). Its network-isolation layer assumes a **Linux host**; macOS Docker Desktop
runs containers in a LinuxKit VM but these setup commands run on the macOS host. Blockers hit while
running `benchmark-solve` for the LEAN v2 smoke, in order, with the fix for each:

## Blocker 1 — `FileNotFoundError: 'modprobe'` (host)
`copilot.py:_ensure_bridge_netfilter()` runs `modprobe br_netfilter` on the host to enable Docker
bridge iptables filtering. macOS has no `modprobe` → `subprocess.run` raises → `runtime-error`.
**Fix (non-invasive):** put a no-op `modprobe` on PATH. Then `_ensure_bridge_netfilter` runs it
(rc 0), finds `/proc/sys/net/bridge/bridge-nf-call-iptables` absent, warns "isolation not effective",
returns False → the iptables DROP rules are skipped entirely. Functional routing is unaffected.
```
mkdir -p ~/.soma-shimbin && printf '#!/bin/sh\nexit 0\n' > ~/.soma-shimbin/modprobe && chmod +x ~/.soma-shimbin/modprobe
export PATH="$HOME/.soma-shimbin:$PATH"
```

## Blocker 2 — compression is COUPLED to network isolation
Do NOT "fix" blocker 1 by setting `SOMA_COPILOT_NETWORK_ISOLATION=false`. The copilot CLI's LLM
endpoint (`COPILOT_PROVIDER_BASE_URL`) is pointed at the proxy sidecar ONLY inside the
`if network_isolation:` block (copilot.py ~1334). With isolation off, the CLI talks to OpenRouter
directly → **the compression sidecar is never in the path** → the miner never fires (verified: run 2
produced a trajectory but 0 compression calls). So isolation must be logically ON (hence the shim),
even though its hard iptables enforcement degrades to a no-op on macOS. For a local smoke that's
fine — the CLI still uses the proxy URL, so compression fires; the enforcement only prevents bypass.

## Blocker 3 — `docker compose` requires `copilot-cli-container/.env`
The compose file has `env_file: - .env`; the backend does NOT write it (expects a setup `cp`, like the
repo-root `.env`). Missing → `runtime-error: env file ... not found`. **USER ACTION** (Claude is barred
from creating env files by policy + the protect hook):
```
cp ~/joshua-work/SOMA-benchmark/src/soma_bench/benchmark/backends/copilot/copilot-cli-container/.env.example \
   ~/joshua-work/SOMA-benchmark/src/soma_bench/benchmark/backends/copilot/copilot-cli-container/.env
```
The example holds only COPILOT_PROVIDER_BASE_URL / COPILOT_MODEL / COPILOT_OFFLINE /
COPILOT_PROVIDER_API_KEY (no real secret — the backend injects live values via the passed env at
runtime). An empty file also satisfies compose; copying the example is the documented path.

## Full smoke command (once blocker 3's .env exists)
```
cd ~/joshua-work/SOMA-benchmark
export PATH="$HOME/.soma-shimbin:$PATH"
export OPENROUTER_API_KEY="<comp-110 key>"          # or source from soma/config/secrets.env
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export LLM_BASE_URL="https://openrouter.ai/api/v1"
uv run python -m soma_bench benchmark-solve \
  --agent-name copilot --benchmark SWE-bench/SWE-bench_Verified \
  --instance-id django__django-11099 --benchmark-type swebench_verified --execute \
  --model deepseek/deepseek-v4-pro \
  --copilot-compression-script-path ~/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py \
  --output-dir outputs/lean-v2-smoke
```
Then read: `outputs/lean-v2-smoke/output.jsonl` (status/patch), the copilot stdout for
`[compression-service][messages.in/out]` firing markers + `metadata.token_usage` (run-level ratio).
For the 3-profile A/B, `SOMA_LEAN_PROFILE` must reach the SIDECAR container (host env won't
propagate) — pass it through the compose env for the compression service (follow-up: confirm the
flag/compose path; default=target works with no propagation).

## Residual risk
Even with blockers 1–3 cleared, more macOS-vs-Linux assumptions may surface deeper in the copilot
container / SWE sandbox. If so, the comp-108 conclusion applies: the authoritative eval runs on a
real-Linux Docker host (cloud/VM). The miner's FIRING is already proven independently via the direct
sidecar E2E (mounting upload_miner_lean_v1.py into soma-copilot-compression-service:latest and
POSTing /transform) — see experiments/candidates/LEAN_comp110_v1/BUILD_REPORT.md. What the full
agent-loop smoke adds is the run-level token ratio + does-it-still-solve, which remain PENDING.
