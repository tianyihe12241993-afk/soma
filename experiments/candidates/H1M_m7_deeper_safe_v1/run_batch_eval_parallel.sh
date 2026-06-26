#!/usr/bin/env bash
# H1M PARALLEL batch eval on a real-Linux Docker host (macOS Docker Desktop). Bash 3.2 compatible.
# Same matrix + output layout as run_batch_eval.sh (analyze_batch.py reads it unchanged), but runs
# up to MAXJOBS solves concurrently. Each solve is an OpenClaw agent loop that spends ~7 min mostly
# WAITING on OpenRouter (LLM latency), so wall-clock ≈ serial_time / MAXJOBS until OpenRouter or RAM
# becomes the ceiling. CPUs barely matter per-solve; concurrency is the lever.
#
# PARALLEL-SAFETY (verified in SOMA-benchmark/.../backends/openclaw.py):
#   - gateway/dind/network/workspace names are all SHA-of(output_dir) (openclaw.py:693,743,224) and
#     every solve has a unique --output-dir  -> no name collision.
#   - the gateway port (8000) is NOT host-published; it's reached via container DNS on each run's OWN
#     private network -> no host-port collision.
#   - the stale-resource sweeper SKIPS running gateways (openclaw.py:1128) -> siblings never reaped.
#   - THE TWO HAZARDS this driver fixes vs the serial one:
#       (1) the plugin venv (.soma-openclaw-venv) is built INSIDE plugin_path with reinstall-on-start
#           -> two solves sharing one plugin dir RACE on the venv. Fix: each solve gets its own plugin
#              copy (miner baked in), removed when the solve finishes.
#       (2) the serial driver's global `docker rm -f ...openclaw` would KILL in-flight siblings.
#           Fix: no per-solve global cleanup; the harness cleans its own per-run gateway/workspace,
#           and we do a single safe sweep only AFTER every job is done.
#
# Per-(profile,task,run) output: experiments/runs/<stamp>_H1M_pbatch/<profsan>__<inst>__r<run>/.
# Usage:
#   export OPENROUTER_API_KEY=sk-or-...                 # or config/secrets.env
#   [MAXJOBS=3] [STAGGER=8] [PROFILES="m7 m12"] [RUNS=2] [TASKS="inst:Cat ..."] bash run_batch_eval_parallel.sh
#   MAXJOBS=1 reproduces serial behavior (still with per-solve plugin isolation).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
WORK="${WORK:-$HOME}"
MODEL="${OPENROUTER_MODEL:-qwen/qwen3-coder}"
PROFILES="${PROFILES:-m7 h1m@deep}"
RUNS="${RUNS:-2}"
MAXJOBS="${MAXJOBS:-3}"          # concurrent solves. CEILING = CPU during test execution, NOT RAM/OpenRouter. MAXJOBS=8 oversubscribed 10 cores (load 15, run stalled); use ~4 here (load ~10). RAM fine (~0.8GB/solve).
STAGGER="${STAGGER:-8}"          # seconds between launches; smooths image/gateway-settle + OpenRouter bursts.
B="$WORK/SOMA-benchmark"; PLUGIN="$WORK/SOMA-plugin"; FORK="$WORK/SWE-bench-fork"
STAMP="$(date -u +%Y-%m-%d_%H%M%S)"
RD="$REPO/experiments/runs/${STAMP}_H1M_pbatch"

# task:category — COMP-108 task set (baseline-status labels Pass/Flip). The comp-107 set is GONE (0 overlap);
# E/M/H is a platform-relative difficulty RANK we cannot reproduce locally, so we group by baseline status and
# rely on PLATFORM category scores. Regenerate config/comp108_tasks.txt per competition from the dashboard scrape.
# Override with TASKS="inst:Lab ..." for a cheap subset.
TASKS="${TASKS:-$(cat "$REPO/config/comp108_tasks.txt" 2>/dev/null)}"

KEY="${OPENROUTER_API_KEY:-}"
[ -z "$KEY" ] && KEY="$(grep -E '^OPENROUTER_API_KEY=' "$REPO/config/secrets.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"')" || true
[ -n "$KEY" ] || { echo "ABORT: set OPENROUTER_API_KEY (env or $REPO/config/secrets.env)"; exit 2; }
docker info >/dev/null 2>&1 || { echo "ABORT: docker not running"; exit 3; }

# --- sanity: warn if MAXJOBS likely overcommits Docker RAM ---
# CORRECTED 2026-06-24: the binding ceiling is NOT RAM and NOT OpenRouter — it is CPU during test execution.
# SWE-bench agents run pytest repeatedly while solving, so each solve is CPU-heavy in bursts. MAXJOBS=8 on this
# 10-core Mac drove load to ~15 (8.8 cores pinned on dinds), starving every solve (38 min, 0/60 done) and risking
# timeout-induced false FAILs. RAM is a non-issue (~0.8GB/solve, measured; 11.67GB fits ~12-15) and 429s were 0,
# but useful concurrency for these test-heavy tasks is ~MAXJOBS=4 (load ~10) on 10 cores. Use 4 here; on a box
# with more cores, raise toward (cores/2) and watch `uptime` load + the end-of-run 429 note.
MEMBYTES="$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)"
MEMGB=$(( MEMBYTES / 1073741824 ))
NEEDMB=$(( MAXJOBS * 800 ))   # ~0.8GB/solve, measured
echo "== host: Docker has ${MEMGB}GB; MAXJOBS=$MAXJOBS x ~0.8GB ~= $(( NEEDMB / 1024 ))GB (real ceiling = OpenRouter 429s, not RAM) =="
if [ "$MEMGB" -gt 0 ] && [ "$NEEDMB" -gt "$(( MEMGB * 1024 ))" ]; then
  echo "   WARNING: MAXJOBS=$MAXJOBS (~$(( NEEDMB / 1024 ))GB) may overcommit ${MEMGB}GB Docker RAM. If solves OOM/stall, lower MAXJOBS."
fi

echo "== ensure repos =="
[ -d "$B/.git" ]      || git clone --depth 1 https://github.com/DendriteHQ/SOMA-benchmark.git "$B"
[ -d "$PLUGIN/.git" ] || git clone --depth 1 https://github.com/DendriteHQ/SOMA-plugin.git "$PLUGIN"
[ -d "$FORK/.git" ]   || git clone --depth 1 https://github.com/SWE-rebench/SWE-bench-fork.git "$FORK"

echo "== toolchain =="
command -v uv >/dev/null 2>&1 || python3 -m pip install -q uv
( cd "$B" && uv sync >/dev/null && uv pip install -q datasets huggingface_hub docker >/dev/null )
[ -d "$WORK/.venv-swerebench" ] || uv venv "$WORK/.venv-swerebench" >/dev/null
uv pip install -q --python "$WORK/.venv-swerebench/bin/python" -e "$FORK" >/dev/null

echo "== .env (macOS gateway fixes baked; plugin path is overridden PER-SOLVE) =="
cat > "$B/.env" <<EOF
OPENROUTER_API_KEY=$KEY
OPENROUTER_MODEL=$MODEL
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
COMPACT_BENCH_LLM_BASE_URL=https://openrouter.ai/api/v1
SOMA_BENCHMARK_WORKSPACE=docker
SOMA_BENCHMARK_MAX_ITERATIONS=60
COMPACT_BENCH_COMPRESSION_SERVICE_CONTEXT=$REPO/sandbox_service/compression_service
COMPACT_BENCH_PLUGIN_TEMPLATE_PATH=$PLUGIN
SOMA_OPENCLAW_PLUGIN_PATH=$PLUGIN
SOMA_OPENCLAW_PLUGIN_REINSTALL_ON_RUN_START=true
SOMA_HOST_DOCKER_BINARY=$B/.docker-cli/docker
SOMA_OPENCLAW_GATEWAY_IMAGE=alpine/openclaw:2026.5.27
SOMA_OPENCLAW_GATEWAY_SETTLE_SECONDS=20
SOMA_SWEREBENCH_EVAL=true
SOMA_SWEREBENCH_HARNESS_ROOT=$FORK
SOMA_SWEREBENCH_HARNESS_PYTHON=$WORK/.venv-swerebench/bin/python
EOF
chmod 600 "$B/.env"
mkdir -p "$RD" "$RD/_plugins"
: > "$RD/tasks.tsv"
for tok in $TASKS; do printf '%s\t%s\n' "${tok%:*}" "${tok#*:}" >> "$RD/tasks.tsv"; done

# pristine plugin snapshot (SOURCE ONLY — no venv/state/git); per-solve copies are made from this.
PRISTINE="$RD/_plugin_pristine"
rsync -a --delete \
  --exclude '.soma-openclaw-venv' --exclude 'openclaw-gateway-state' \
  --exclude 'logs' --exclude '.git' --exclude '__pycache__' --exclude 'openclaw-problems' \
  "$PLUGIN/" "$PRISTINE/"

M7_MINER="$REPO/miner/cot_compression/upload_miner_v11_m7.py"
H1M_MINER="$REPO/experiments/candidates/H1M_m7_deeper_safe_v1/h1m_miner.py"
H3_MINER="$REPO/experiments/candidates/H3_cache_stable_depth_v1/h3_miner.py"
M12_MINER="$REPO/miner/cot_compression/upload_miner_m7_compliant.py"
M121_MINER="$REPO/miner/cot_compression/upload_miner_m12_1.py"
M121B_MINER="$REPO/miner/cot_compression/upload_miner_m12_1b.py"
M14_MINER="$REPO/miner/cot_compression/upload_miner_m14.py"
M16_MINER="$REPO/miner/cot_compression/upload_miner_m16.py"
M12_DEEPER_MINER="$REPO/miner/cot_compression/upload_miner_m12_deeper.py"
M12_LIGHTER_MINER="$REPO/miner/cot_compression/upload_miner_m12_lighter.py"
M17_MINER="$REPO/miner/cot_compression/upload_miner_m17.py"
M18_MINER="$REPO/miner/cot_compression/upload_miner_m18.py"
M20B_MINER="$REPO/miner/cot_compression/upload_miner_m20_blind.py"
M20BV2_MINER="$REPO/miner/cot_compression/upload_miner_m20b_v2.py"

# run ONE solve in a fully isolated per-solve plugin dir (bg-safe; logs its own status).
run_one() {
  inst="$1"; prof="$2"; run="$3"; src="$4"; profvar="$5"; profval="$6"
  out="$RD/${prof//[@\/]/_}__${inst}__r${run}"; mkdir -p "$out"
  sp="$RD/_plugins/${prof//[@\/]/_}__${inst}__r${run}"
  rm -rf "$sp" 2>/dev/null || true
  cp -R "$PRISTINE" "$sp" || { echo "    [FAILED prep] $inst/$prof/r$run (cp plugin)"; return 0; }
  # bake the miner into THIS solve's plugin copy (sed for profile-var miners, cp otherwise)
  if [ -n "$profvar" ]; then
    sed "s|^${profvar} = _os\.environ.*|${profvar} = \"$profval\"  # baked by run_batch_eval_parallel.sh|" \
      "$src" > "$sp/base_miner.py" || { echo "    [FAILED prep] $inst/$prof/r$run (sed)"; rm -rf "$sp"; return 0; }
  else
    cp "$src" "$sp/base_miner.py" || { echo "    [FAILED prep] $inst/$prof/r$run (cp miner)"; rm -rf "$sp"; return 0; }
  fi
  cp "$sp/base_miner.py" "$out/baked_base_miner.py" 2>/dev/null || true   # provenance
  echo "  [$(date -u +%H:%M:%S)] START $inst / $prof / r$run"
  (
    cd "$B" && set -a && . ./.env && set +a
    export SOMA_OPENCLAW_PLUGIN_PATH="$sp"
    export COMPACT_BENCH_PLUGIN_TEMPLATE_PATH="$sp"
    uv run python -m soma_bench benchmark-solve --agent-name openclaw \
      --benchmark SWE-bench/SWE-bench_Verified --instance-id "$inst" --execute --openclaw-current-user \
      --openclaw-plugin-path "$sp" --openclaw-plugin-reinstall-on-run-start \
      --openclaw-command "--timeout 1800" --swerebench-eval --output-dir "$out"
  ) > "$out/solve.log" 2>&1 \
    && echo "  [$(date -u +%H:%M:%S)] ok     $inst / $prof / r$run" \
    || echo "  [$(date -u +%H:%M:%S)] FAILED $inst / $prof / r$run (see $out/solve.log)"
  rm -rf "$sp" 2>/dev/null || true   # free the per-solve plugin (+ its venv) when done
}

# bash 3.2-safe slot gate: block until fewer than MAXJOBS *running* bg jobs (jobs -rp auto-reaps Done).
wait_for_slot() {
  while [ "$(jobs -rp 2>/dev/null | wc -l | tr -d ' ')" -ge "$MAXJOBS" ]; do sleep 3; done
}

ntasks=$(echo $TASKS | wc -w | tr -d ' ')
echo "== PBATCH: profiles=[$PROFILES] x ${ntasks} tasks x RUNS=$RUNS, MAXJOBS=$MAXJOBS (PAID from here) $(date -u +%H:%M:%S) =="
launched=0
for tok in $TASKS; do
  inst="${tok%:*}"
  for prof in $PROFILES; do
    case "$prof" in
      m7)             src="$M7_MINER";  profvar=""; profval="" ;;
      h1m@medium)     src="$H1M_MINER"; profvar="H1M_PROFILE"; profval="medium" ;;
      h1m@deep)       src="$H1M_MINER"; profvar="H1M_PROFILE"; profval="deep" ;;
      h1m@king)       src="$H1M_MINER"; profvar="H1M_PROFILE"; profval="king" ;;
      h1m@ultra)      src="$H1M_MINER"; profvar="H1M_PROFILE"; profval="ultra" ;;
      h3@cache_safe)  src="$H3_MINER"; profvar="H3_PROFILE"; profval="cache_safe" ;;
      h3@cache_king)  src="$H3_MINER"; profvar="H3_PROFILE"; profval="cache_king" ;;
      h3@cache_ultra) src="$H3_MINER"; profvar="H3_PROFILE"; profval="cache_ultra" ;;
      m12)            src="$M12_MINER";  profvar=""; profval="" ;;
      m12_1)          src="$M121_MINER"; profvar=""; profval="" ;;
      m12_1b)         src="$M121B_MINER"; profvar=""; profval="" ;;
      m14)            src="$M14_MINER"; profvar=""; profval="" ;;
      m16)            src="$M16_MINER"; profvar=""; profval="" ;;
      m12_deeper)     src="$M12_DEEPER_MINER"; profvar=""; profval="" ;;
      m12_lighter)    src="$M12_LIGHTER_MINER"; profvar=""; profval="" ;;
      m17)            src="$M17_MINER"; profvar=""; profval="" ;;
      m18)            src="$M18_MINER"; profvar=""; profval="" ;;
      m20b)           src="$M20B_MINER"; profvar=""; profval="" ;;
      m20bv2)         src="$M20BV2_MINER"; profvar=""; profval="" ;;
      *) echo "  skip unknown profile $prof"; continue ;;
    esac
    run=1
    while [ "$run" -le "$RUNS" ]; do
      wait_for_slot
      run_one "$inst" "$prof" "$run" "$src" "$profvar" "$profval" &
      launched=$((launched + 1))
      [ "$STAGGER" -gt 0 ] && sleep "$STAGGER"
      run=$((run + 1))
    done
  done
done

echo "== launched $launched solves; waiting for the last in-flight ones $(date -u +%H:%M:%S) =="
wait || true

# single SAFE sweep (nothing is running now): drop any leftover openclaw containers + per-solve plugins.
docker ps -a --format '{{.Names}}' 2>/dev/null | grep -iE 'soma-openclaw|openclaw-gateway' | xargs -I{} docker rm -f {} 2>/dev/null || true
rm -rf "$RD/_plugins" "$PRISTINE" 2>/dev/null || true

# OpenRouter pressure check: if many solves hit 429/rate-limit, MAXJOBS is too high for the account.
RL=$(grep -rilE '429|rate.?limit|too many requests' "$RD"/*/solve.log 2>/dev/null | wc -l | tr -d ' ')
echo "== DONE: $launched solves @ $(date -u +%H:%M:%S). run dir: $RD =="
[ "$RL" -gt 0 ] && echo "   NOTE: $RL solve log(s) mention rate-limit/429 — consider lowering MAXJOBS." || true
echo "   analyze: python experiments/candidates/H1M_m7_deeper_safe_v1/analyze_batch.py $RD"
