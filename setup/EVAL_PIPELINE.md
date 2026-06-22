# SOMA evaluation pipeline — how it's set up + how to re-create on a new machine

Local e2e evaluation = run a candidate compression miner against SWE-bench tasks through the
real OpenClaw agent, exactly like the SOMA platform does, and read back gold-patch / token results.
This is what `soma-bench benchmark-solve --agent-name openclaw` does.

## The pieces (3 separate repos + Docker)

| Dir | Origin | Role | In the backup repo? |
|-----|--------|------|---------------------|
| `/Users/user/SOMA` | DendriteHQ/SOMA (→ private `tianyihe12241993-afk/soma`) | miner solutions (`miner/cot_compression/upload_miner_*.py`), compression-service Dockerfile (`sandbox_service/compression_service`), ops workspace | **YES** (this repo) |
| `/Users/user/SOMA-benchmark` | DendriteHQ/SOMA-benchmark | the `soma_bench` harness (uv project, py3.11+) | NO — clone fresh + apply patch |
| `/Users/user/SOMA-plugin` | DendriteHQ/SOMA-plugin | OpenClaw plugin; `base_miner.py` IS the active miner the harness installs into the gateway | NO — clone fresh + apply patch |

**Critical:** the harness only works because of LOCAL, UNCOMMITTED patches in `SOMA-benchmark`
and `SOMA-plugin`. A fresh `git clone` does NOT have them. They are captured here:
- `setup/patches/soma-benchmark-openclaw.patch`  → `src/soma_bench/benchmark/backends/openclaw.py`
- `setup/patches/soma-plugin-index-and-reqs.patch` → `index.js` + `requirements.txt`
(`base_miner.py` is NOT in the plugin patch on purpose — it's just a copy of whichever
`upload_miner_*.py` you're testing; pick one from `SOMA/miner/cot_compression/`.)

## Prerequisites
- **Docker Desktop** (Apple Silicon / arm64), running.
- **uv** (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- Python 3.11+ (uv will fetch it).
- An OpenRouter API key with credit (use a fresh altascloud-blocked key, same as for uploads).

## Re-setup steps (new laptop)

```bash
# 1. Clone all three repos (adjust the home path if not /Users/user)
git clone https://github.com/tianyihe12241993-afk/soma.git   /Users/user/SOMA          # your private backup
git clone https://github.com/DendriteHQ/SOMA-benchmark.git    /Users/user/SOMA-benchmark
git clone https://github.com/DendriteHQ/SOMA-plugin.git       /Users/user/SOMA-plugin

# 2. Apply the local patches (the part that's nowhere else in git)
git -C /Users/user/SOMA-benchmark apply /Users/user/SOMA/setup/patches/soma-benchmark-openclaw.patch
git -C /Users/user/SOMA-plugin    apply /Users/user/SOMA/setup/patches/soma-plugin-index-and-reqs.patch

# 3. Re-create the linux/arm64 static docker CLI the harness bind-mounts into the gateway
#    (Mach-O host docker won't run inside the linux gateway container)
mkdir -p /Users/user/SOMA-benchmark/.docker-cli
cid=$(docker create docker:dind)
docker cp "$cid:/usr/local/bin/docker" /Users/user/SOMA-benchmark/.docker-cli/docker
docker rm "$cid"
chmod +x /Users/user/SOMA-benchmark/.docker-cli/docker
file /Users/user/SOMA-benchmark/.docker-cli/docker   # expect: ELF ... ARM aarch64 ... statically linked

# 4. Config: copy the env template and fill in your key
cp /Users/user/SOMA/setup/soma-benchmark.env.example /Users/user/SOMA-benchmark/.env
#   then edit /Users/user/SOMA-benchmark/.env -> set LLM_API_KEY=sk-or-v1-...

# 5. Install the harness deps
cd /Users/user/SOMA-benchmark && uv sync

# 6. Pre-pull the pinned gateway image (latest is broken — see fixes #5)
docker pull alpine/openclaw:2026.5.27
#   soma-compression-service:latest is auto-built by the harness from
#   COMPACT_BENCH_COMPRESSION_SERVICE_CONTEXT on first run.

# 7. Pick the miner to test and install it as the plugin's base_miner.py
cp /Users/user/SOMA/miner/cot_compression/upload_miner_v11_m7.py /Users/user/SOMA-plugin/base_miner.py
python3 -c "import ast; ast.parse(open('/Users/user/SOMA-plugin/base_miner.py').read()); print('syntax OK')"
```

## Running an evaluation

The required env exports + CLI flags (mirror `SOMA-benchmark/outputs/e2e/run_*.sh`):

```bash
cd /Users/user/SOMA-benchmark
export LLM_API_KEY=sk-or-v1-...                                    # or rely on .env
export SOMA_HOST_DOCKER_BINARY=/Users/user/SOMA-benchmark/.docker-cli/docker   # fix #3
export SOMA_OPENCLAW_GATEWAY_IMAGE=alpine/openclaw:2026.5.27       # fix #5
export SOMA_OPENCLAW_GATEWAY_SETTLE_SECONDS=20                     # fix #7 (5–20 ok)

uv run python -m soma_bench benchmark-solve --agent-name openclaw \
  --benchmark SWE-bench/SWE-bench_Verified --instance-id django__django-11099 \
  --output-dir outputs/e2e/test-run --execute --openclaw-current-user \
  --openclaw-command "--timeout 1800"
```

`--openclaw-current-user` (fix #2) is mandatory for production parity. Use `--timeout 1800`
for hard/flip tasks (the 600s default cuts off king-style flips). Results land in
`<output-dir>/output.jsonl` (`status`, `metadata.token_usage.model_calls_count`, cumulative tokens).
A canonical multi-instance loop is `outputs/e2e/run_v26_validation.sh` — copy it as a template.

### Cleanup between runs (fix #8 — stale mounts cause "device or resource busy")
```bash
docker ps -a --format '{{.Names}}' | grep -E 'soma-openclaw' | xargs -I{} docker rm -f {} 2>/dev/null
rm -rf /private/var/folders/*/T/soma-openclaw-problems/run-*    # stale workspace mounts
rm -rf /Users/user/SOMA-plugin/logs                            # stale plugin logs
# and remove the run's own output dir before re-running the same instance
```

## What the macOS patches actually do (why a clone alone fails)

`soma-benchmark-openclaw.patch` (4 fixes, ~38 lines):
1. **`_host_docker_binary()` honors `SOMA_HOST_DOCKER_BINARY`** — the harness bind-mounts the host
   docker binary into the gateway; the Mach-O host binary can't run in linux → point it at the
   extracted arm64 static CLI (step 3).
2. **`_sqlite_state_tmpfs_args()`** — WAL-mode SQLite in the gateway state dir breaks over virtiofs
   ("no such table: acp_sessions"). Mounts the state dir as tmpfs on gateway + CLI containers.
   Opt out with `SOMA_OPENCLAW_STATE_TMPFS=0`.
3. **`SOMA_OPENCLAW_GATEWAY_SETTLE_SECONDS`** post-health settle in `_wait_for_gateway_ready`.
4. **gateway image pin** support (`SOMA_OPENCLAW_GATEWAY_IMAGE`) — `latest` (rebuilt 2026-06-11)
   fails workspace setup with `rm sandbox-skills/skills: Device or resource busy`.

`soma-plugin-index-and-reqs.patch`:
- **`index.js`: `disableSessionRewrite = true`** (~line 781) — session-JSONL rewrite mid-run trips
  `EmbeddedAttemptSessionTakeoverError` at cleanup in openclaw 2026.5.27. Compression still applies
  (local-benchmark-only divergence from production).
- **`requirements.txt` slimmed to comments** — heavy deps (scipy/sklearn/nltk) hit a `chown` race on
  virtiofs during plugin venv install; the improved miner is stdlib-only and the compression-service
  image carries its own deps.

## Reference
- Full discovery log: memory `soma-bench-macos-setup` (13 debug attempts, 2026-06-11).
- Miner design + scores: memory `soma-miner-improved`; ops state in `state/`.
- Confirmed-best miner to install for a baseline run: `upload_miner_v11_m7.py` (m7, 1.279).
