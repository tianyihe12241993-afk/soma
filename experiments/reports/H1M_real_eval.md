# H1M real SWE-bench eval — setup status (2026-06-22)

Goal: cost-controlled real eval of m7 vs h1m@medium vs h1m@deep on the Medium-first targets,
starting with a 2-task smoke.

## STATUS UPDATE (2026-06-22, after user started Docker + gave repo URLs)
**Stack SETUP COMPLETE and validated up to the execute boundary. Smoke NOT yet run — awaiting
confirmation before the first PAID `--execute` (cost control). No results invented.**
- ✅ Docker daemon up (v29.5.3); docker-desktop WSL integration active.
- ✅ Cloned public repos: `~/SOMA-benchmark`, `~/SOMA-plugin`.
- ✅ `uv` installed; `uv sync` built `soma-bench` in its own .venv (CPython 3.12); `benchmark-info` OK
  (backend=openclaw, workspace=docker).
- ✅ **OpenClaw is a Docker image** (`alpine/openclaw:latest`) — no host node/openclaw install needed.
- ✅ Instance-fetch deps installed (datasets, huggingface_hub, docker-py).
- ✅ SWE-rebench SWE-bench fork is **public** (needed for `--swerebench-eval` pass/fail).
- ✅ `~/SOMA-benchmark/.env` written (OPENROUTER_API_KEY from secrets.env — redacted/600/uncommitted;
  model `qwen/qwen3-coder` as a cheap default — CONFIRM).
- ⏭ Remaining before smoke: (a) clone+point the SWE-rebench harness for pass/fail; (b) run the PAID
  `--execute` smoke (2 tasks × 3 profiles). Both await user go + model confirmation.

_(superseded) earlier status: BLOCKED at the Docker gate — smoke NOT run, no real results produced._

## RESOLVED DIAGNOSIS (2026-06-22) — it's WSL2, not Docker Desktop. Run on real Linux/macOS.
Decisive tests: the `rm '.openclaw/sandbox-skills/skills': Device or resource busy` failure reproduces on
**Docker Desktop's WSL2 backend AND native `docker.io` 29.1.3 in WSL2**, on **two** OpenClaw images
(2026.6.9, 2026.6.8-beta.2), as **root and non-root** — identical every time, ~12s, ~$0. The only common
factor is **WSL2** (kernel `6.18.33.1-microsoft-standard-WSL2`): its mount-namespace/propagation under
Docker-in-Docker leaves OpenClaw's skills bind-mount un-removable. **The user's past working laptop was
macOS** — Docker Desktop on macOS runs a real Linux VM (LinuxKit) with normal mount semantics, which is why
it worked there. **Conclusion: no WSL fix; run the eval on a real-Linux Docker host (macOS Docker Desktop,
native Linux, a Linux VM, or a cloud Linux instance).**

**Turnkey deliverable:** `experiments/candidates/H1M_m7_deeper_safe_v1/run_real_eval.sh` — one command on a
non-WSL host. It clones SOMA-benchmark/SOMA-plugin/SWE-bench-fork, installs uv+soma-bench+harness+deps,
writes `.env` (key from `OPENROUTER_API_KEY` env or config/secrets.env — never committed), runs the 2-task
smoke for m7 / h1m@medium / h1m@deep with `--swerebench-eval`, and emits the gate CSV for `h1m_run.py --results`.
On the Mac: `git clone <this soma repo>` → `export OPENROUTER_API_KEY=…` → run the script.
(One field to verify on the FIRST successful run: the token-with/without keys in output.jsonl `metadata`,
used to compute compression ratio in the gate CSV — the converter flags them.)

## SMOKE ATTEMPT (2026-06-22) — stack fully built, blocked on an OpenClaw bug
Ran the real pipeline end-to-end for m7/django-10914. It now **builds + injects + launches** correctly,
but the OpenClaw agent dies in ~12s before any solve. **~No spend** (fails during workspace prep, pre-LLM).

**What works:** uv + soma-bench; SWE-rebench harness (swebench 4.0.3); plugin installed; Docker builds the
compression-service image (666MB) + pulls django SWE-bench image (3.94GB) + alpine/openclaw + dind; the
**m7 miner is injected** into the compression service in DinD (`service ready :8000`); model resolves to
`openrouter/qwen/qwen3-coder`. Fixes applied along the way: COMPACT_BENCH_COMPRESSION_SERVICE_CONTEXT,
removed broken docker `credsStore` (desktop.exe), COMPACT_BENCH_LLM_BASE_URL, plugin template, SOMA_OPENCLAW_USER=root.

**The blocker (upstream, not ours):** OpenClaw's nested sandbox seeds `.openclaw/sandbox-skills/skills`
as a **root-owned bind-mount** in the agent workspace, then its own prep step tries to `rm` it:
- as uid 1000 → `Permission denied`
- as root → `Device or resource busy` (can't rm an active mount)
Either way the agent exits 1 with an empty patch (`swerebench: skipped-empty-patch`). This is a defect in
`alpine/openclaw:latest`'s sandbox-skills handling under this Docker/WSL setup — **not an H1M issue and not a
config I can flip** (no skills-disable in the benchmark CLI; tried both users).

**Options:** (a) pin a known-good `alpine/openclaw` image tag via `SOMA_OPENCLAW_GATEWAY_IMAGE` (the `:latest`
default may have drifted); (b) an OpenClaw skills-disable flag if one exists; (c) raise with the SOMA/OpenClaw
maintainers (DendriteHQ) — it's their container. The `h1m_run.py --results` gate is ready+proven and will
turn real results into ACCEPT/REJECT the moment this upstream bug is cleared. Machine: data/latest/h1m_real_eval_smoke.json.

## Prerequisite probe (WSL Ubuntu-22.04)
| prereq | state |
|---|---|
| Docker CLI in WSL | ❌ missing (WSL integration off) |
| Docker daemon | ❌ not available (`docker-desktop` distro Stopped; Docker Desktop not running) |
| `soma_bench` (SOMA-benchmark) | ❌ not installed / repo not on disk |
| `openclaw` agent + SOMA-plugin scaffold | ❌ not present (README references `/path/to/...` placeholders) |
| `swebench` / `datasets` / `docker` (py) | ❌ not installed (PyPI-installable, but moot without the above) |
| disk free | ✅ 929 GB |
| OPENROUTER_API_KEY | ✅ in config/secrets.env (git-ignored; not printed) |

The real eval runs **outside** this ops repo: the OpenClaw agent solves a SWE-bench task inside a
per-instance Docker image (`ghcr.io/epoch-research/swe-bench.eval.x86_64.<instance>`), with the miner
injected as `<SOMA-plugin>/base_miner.py`, driven by `python -m soma_bench benchmark-solve`. None of that
tooling is present, and the daemon is down — so it cannot run here yet.

## What only YOU can unblock
1. **Start Docker Desktop** and enable **WSL integration for Ubuntu-22.04** (Settings → Resources → WSL).
2. **Provide the SOMA-benchmark + OpenClaw SOMA-plugin** (repo URL / access — not referenced by URL in
   this repo; likely the private DendriteHQ benchmark). Then in WSL: `cd <SOMA-benchmark> && ~/.venvs/soma/bin/pip install -e .`
   (Claude's sandbox blocks installing from external git, so this is a user step.)

## Prepared and ready (so it's one command once unblocked)
- `experiments/manifests/H1M_real_eval_medium_first.yaml` — profiles, smoke/medium-first/fragile instances,
  plugin path, command template, runs_per_task=2 (cost control).
- `experiments/candidates/H1M_m7_deeper_safe_v1/run_smoke_real_eval.sh` — guarded smoke driver: reads the
  key (never prints), aborts unless Docker + soma_bench present, runs the 2 smoke instances × 3 profiles,
  logs to `experiments/runs/<stamp>_H1M_smoke_real_eval/`. (UNTESTED here; the soma_bench-output→gate-CSV
  conversion is the one step to finalize against real output.)
- The **gate is already proven** (`h1m_run.py --results`, fixtures PASS→ACCEPT / FAIL→REJECT), so smoke
  results convert straight into an ACCEPT/REJECT.

## Exact smoke command (per profile × instance)
```
cp <profile base_miner> <SOMA-plugin>/base_miner.py
H1M_PROFILE=<medium|deep|''> OPENROUTER_API_KEY=$KEY \
python -m soma_bench benchmark-solve --agent-name openclaw \
  --benchmark SWE-bench/SWE-bench_Verified --instance-id django__django-10914 \
  --openclaw-plugin-path <SOMA-plugin> --execute
```

## Cost / time estimate (rough; dominated by model choice + runs_per_task)
- **Smoke** (2 tasks × 3 profiles × 2 runs = 12 runs): ~**$3–$18**, ~**1–3 h** incl. first-time image pulls (~5–12 GB for 2 instances).
- **Full Medium-first** (7 × 3 × 2 = 42 runs): ~**$10–$60**, ~**3–9 h**, ~15–40 GB image pulls (one-time).
- **+ fragile phase** (4 × 3 × 2 = 24 more runs): +~$6–$35, +~2–5 h.
- Levers: the OpenRouter model the agent uses (biggest factor), `runs_per_task` (2 here vs platform 5), and image-pull caching.

## Requested outputs (smoke)
1. Docker/eval stack setup: **did NOT succeed** — Docker down + tooling/repos absent.
2. Smoke command: above.
3. Cost/time: above.
4. Smoke result m7 vs h1m@medium vs h1m@deep: **NOT RUN (blocked).** Standing offline projection: m7
   Medium-first baseline 3.02× / 1.690; h1m@medium ~3.34×, h1m@deep ~3.43× (+13.7%). Real = PENDING.
5. Gate h1m@medium: **PENDING_EVAL** (offline gate PASS; needs real results).
6. Gate h1m@deep: **PENDING_EVAL** (offline gate PASS; needs real results).
7. Safe to proceed to full Medium-first? **NO** — cannot run even the smoke until Docker + SOMA-benchmark
   are set up. (And per instructions, full set runs only after smoke passes + explicit confirmation.)
