#!/usr/bin/env bash
# H1M FULL batch eval on a real-Linux Docker host (macOS Docker Desktop). Bash 3.2 compatible.
# Runs PROFILES x TASKS x RUNS through soma_bench + SWE-rebench. The H1M profile is BAKED into
# base_miner.py (the env var does NOT reach the compression container — see DISCOVERIES).
# Per-(profile,task,run) output: experiments/runs/<stamp>_H1M_batch/<profsan>__<inst>__r<run>/.
# Analyze with analyze_batch.py.  Usage:
#   export OPENROUTER_API_KEY=sk-or-...           # or config/secrets.env
#   [PROFILES="m7 h1m@deep"] [RUNS=2] [TASKS="inst:Cat ..."] bash run_batch_eval.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
WORK="${WORK:-$HOME}"
MODEL="${OPENROUTER_MODEL:-qwen/qwen3-coder}"
PROFILES="${PROFILES:-m7 h1m@deep}"
RUNS="${RUNS:-2}"
B="$WORK/SOMA-benchmark"; PLUGIN="$WORK/SOMA-plugin"; FORK="$WORK/SWE-bench-fork"
STAMP="$(date -u +%Y-%m-%d_%H%M%S)"
RD="$REPO/experiments/runs/${STAMP}_H1M_batch"

# task:category — Medium-first(7) + Hard fragile-guard(4) + Hard bonus(2) + Easy(2)
TASKS="${TASKS:-\
django__django-15851:Medium django__django-11119:Medium sympy__sympy-24539:Medium \
django__django-14580:Medium django__django-14855:Medium django__django-10914:Medium \
django__django-11603:Medium \
sympy__sympy-17139:HardFragile sympy__sympy-16766:HardFragile django__django-11239:HardFragile \
django__django-14493:HardFragile \
django__django-14752:Hard django__django-13363:Hard \
django__django-16255:Easy django__django-13741:Easy}"

KEY="${OPENROUTER_API_KEY:-}"
[ -z "$KEY" ] && KEY="$(grep -E '^OPENROUTER_API_KEY=' "$REPO/config/secrets.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"')" || true
[ -n "$KEY" ] || { echo "ABORT: set OPENROUTER_API_KEY (env or $REPO/config/secrets.env)"; exit 2; }
docker info >/dev/null 2>&1 || { echo "ABORT: docker not running"; exit 3; }

echo "== ensure repos =="
[ -d "$B/.git" ]      || git clone --depth 1 https://github.com/DendriteHQ/SOMA-benchmark.git "$B"
[ -d "$PLUGIN/.git" ] || git clone --depth 1 https://github.com/DendriteHQ/SOMA-plugin.git "$PLUGIN"
[ -d "$FORK/.git" ]   || git clone --depth 1 https://github.com/SWE-rebench/SWE-bench-fork.git "$FORK"

echo "== toolchain =="
command -v uv >/dev/null 2>&1 || python3 -m pip install -q uv
( cd "$B" && uv sync >/dev/null && uv pip install -q datasets huggingface_hub docker >/dev/null )
[ -d "$WORK/.venv-swerebench" ] || uv venv "$WORK/.venv-swerebench" >/dev/null
uv pip install -q --python "$WORK/.venv-swerebench/bin/python" -e "$FORK" >/dev/null

echo "== .env (macOS gateway fixes baked) =="
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
mkdir -p "$RD"
: > "$RD/tasks.tsv"
for tok in $TASKS; do printf '%s\t%s\n' "${tok%:*}" "${tok#*:}" >> "$RD/tasks.tsv"; done

M7_MINER="$REPO/miner/cot_compression/upload_miner_v11_m7.py"
H1M_MINER="$REPO/experiments/candidates/H1M_m7_deeper_safe_v1/h1m_miner.py"
H3_MINER="$REPO/experiments/candidates/H3_cache_stable_depth_v1/h3_miner.py"
M12_MINER="$REPO/miner/cot_compression/upload_miner_m7_compliant.py"
M121_MINER="$REPO/miner/cot_compression/upload_miner_m12_1.py"
ntasks=$(echo $TASKS | wc -w | tr -d ' '); total=0
echo "== BATCH: profiles=[$PROFILES] x ${ntasks} tasks x RUNS=$RUNS (PAID from here) $(date -u +%H:%M:%S) =="
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
      *) echo "  skip unknown profile $prof"; continue ;;
    esac
    if [ -n "$profvar" ]; then
      sed "s|^${profvar} = _os\.environ.*|${profvar} = \"$profval\"  # baked by run_batch_eval.sh|" "$src" > "$PLUGIN/base_miner.py"
    else
      cp "$src" "$PLUGIN/base_miner.py"
    fi
    run=1
    while [ "$run" -le "$RUNS" ]; do
      out="$RD/${prof//[@\/]/_}__${inst}__r${run}"; mkdir -p "$out"
      echo "  [$(date -u +%H:%M:%S)] $inst / $prof / r$run"
      ( cd "$B" && set -a && . ./.env && set +a && \
        uv run python -m soma_bench benchmark-solve --agent-name openclaw \
          --benchmark SWE-bench/SWE-bench_Verified --instance-id "$inst" --execute --openclaw-current-user \
          --openclaw-plugin-path "$PLUGIN" --openclaw-plugin-reinstall-on-run-start \
          --openclaw-command "--timeout 1800" --swerebench-eval --output-dir "$out" ) \
        > "$out/solve.log" 2>&1 && echo "    ok" || echo "    FAILED (see $out/solve.log)"
      docker ps -a --format '{{.Names}}' 2>/dev/null | grep -iE 'soma-openclaw|openclaw-gateway' | xargs -I{} docker rm -f {} 2>/dev/null || true
      total=$((total + 1)); run=$((run + 1))
    done
  done
done
echo "== DONE: $total solves @ $(date -u +%H:%M:%S). run dir: $RD =="
