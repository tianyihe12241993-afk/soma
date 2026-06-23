#!/usr/bin/env bash
# Turnkey H1M real SWE-bench smoke on a REAL-LINUX Docker host (macOS Docker Desktop /
# native Linux). DO NOT run under WSL2 — its mount semantics break OpenClaw's sandbox-skills
# (rm '.openclaw/sandbox-skills/skills': Device or resource busy). Verified working env on
# this project: macOS Docker Desktop (LinuxKit VM). Idempotent; no spend until the solve loop.
#
# Prereqs on the host: git, python3, docker (running), an OpenRouter key.
# Usage:
#   export OPENROUTER_API_KEY=sk-or-...            # do NOT commit; rotate the one exposed in chat
#   bash experiments/candidates/H1M_m7_deeper_safe_v1/run_real_eval.sh
# Optional env: OPENROUTER_MODEL (default qwen/qwen3-coder), WORK (clone dir, default $HOME),
#   INSTANCES (space-separated; default the 2 smoke tasks).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"          # the soma repo root
WORK="${WORK:-$HOME}"
MODEL="${OPENROUTER_MODEL:-qwen/qwen3-coder}"
INSTANCES="${INSTANCES:-django__django-10914 django__django-15851}"
B="$WORK/SOMA-benchmark"; PLUGIN="$WORK/SOMA-plugin"; FORK="$WORK/SWE-bench-fork"
STAMP="$(date -u +%Y-%m-%d_%H%M%S)"
RD="$REPO/experiments/runs/${STAMP}_H1M_smoke_real_eval"

# ---- key ----
KEY="${OPENROUTER_API_KEY:-}"
[ -z "$KEY" ] && KEY="$(grep -E '^OPENROUTER_API_KEY=' "$REPO/config/secrets.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"')" || true
[ -n "$KEY" ] || { echo "ABORT: set OPENROUTER_API_KEY (env or $REPO/config/secrets.env)"; exit 2; }
docker info >/dev/null 2>&1 || { echo "ABORT: docker not running"; exit 3; }
case "$(uname -r)" in *microsoft*|*WSL2*) echo "WARNING: this looks like WSL2 — the skills-mount bug will recur. Use real Linux/macOS." ;; esac

echo "== clone repos (public) =="
[ -d "$B/.git" ]      || git clone --depth 1 https://github.com/DendriteHQ/SOMA-benchmark.git "$B"
[ -d "$PLUGIN/.git" ] || git clone --depth 1 https://github.com/DendriteHQ/SOMA-plugin.git "$PLUGIN"
[ -d "$FORK/.git" ]   || git clone --depth 1 https://github.com/SWE-rebench/SWE-bench-fork.git "$FORK"

echo "== toolchain (uv + soma-bench + harness) =="
command -v uv >/dev/null 2>&1 || python3 -m pip install -q uv
( cd "$B" && uv sync >/dev/null && uv pip install -q datasets huggingface_hub docker >/dev/null )
[ -d "$WORK/.venv-swerebench" ] || uv venv "$WORK/.venv-swerebench" >/dev/null
uv pip install -q --python "$WORK/.venv-swerebench/bin/python" -e "$FORK" >/dev/null

echo "== .env (key not echoed) =="
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
# macOS gateway fixes (Docker Desktop / LinuxKit) — see soma-bench-macos-setup memory + setup/EVAL_PIPELINE.md
SOMA_HOST_DOCKER_BINARY=$B/.docker-cli/docker
SOMA_OPENCLAW_GATEWAY_IMAGE=alpine/openclaw:2026.5.27
SOMA_OPENCLAW_GATEWAY_SETTLE_SECONDS=20
SOMA_SWEREBENCH_EVAL=true
SOMA_SWEREBENCH_HARNESS_ROOT=$FORK
SOMA_SWEREBENCH_HARNESS_PYTHON=$WORK/.venv-swerebench/bin/python
EOF
chmod 600 "$B/.env"
mkdir -p "$RD"

# Bash 3.2-compatible (macOS default ships 3.2) — no associative arrays.
M7_MINER="$REPO/miner/cot_compression/upload_miner_v11_m7.py"
H1M_MINER="$REPO/experiments/candidates/H1M_m7_deeper_safe_v1/h1m_miner.py"

echo "== SMOKE: 3 profiles x ${INSTANCES} (PAID from here) =="
for prof in m7 h1m@medium h1m@deep; do
  case "$prof" in
    m7)         src="$M7_MINER";  profenv="" ;;
    h1m@medium) src="$H1M_MINER"; profenv="medium" ;;
    h1m@deep)   src="$H1M_MINER"; profenv="deep" ;;
  esac
  # bake the profile INTO the miner file — H1M_PROFILE env does NOT reach the compression container
  if [ -n "$profenv" ]; then
    sed "s|^H1M_PROFILE = _os\.environ.*|H1M_PROFILE = \"$profenv\"  # baked by run_real_eval.sh|" "$src" > "$PLUGIN/base_miner.py"
  else
    cp "$src" "$PLUGIN/base_miner.py"
  fi
  for inst in $INSTANCES; do
    out="$RD/${prof//[@\/]/_}__${inst}"; mkdir -p "$out"
    echo "  [$(date -u +%H:%M:%S)] $prof / $inst"
    ( cd "$B" && set -a && . ./.env && set +a && H1M_PROFILE="$profenv" \
      uv run python -m soma_bench benchmark-solve --agent-name openclaw \
        --benchmark SWE-bench/SWE-bench_Verified --instance-id "$inst" --execute --openclaw-current-user \
        --openclaw-plugin-path "$PLUGIN" --openclaw-plugin-reinstall-on-run-start \
        --openclaw-command "--timeout 1800" --swerebench-eval --output-dir "$out" ) \
      > "$out/solve.log" 2>&1 && echo "    ok" || echo "    FAILED (see $out/solve.log)"
  done
done

echo "== convert output.jsonl -> gate CSV =="
python3 - "$RD" > "$RD/h1m_smoke_gate.csv" <<'PY'
import json,sys,glob,os,csv
rd=sys.argv[1]; w=csv.writer(sys.stdout)
w.writerow(["task","pass","neg_runs","n_runs","ratio","score","broke_baseline","pairing_error","missing_patch","category","profile"])
for oj in sorted(glob.glob(rd+"/*/output.jsonl")):
    prof=os.path.basename(os.path.dirname(oj)).split("__")[0]
    for line in open(oj):
        line=line.strip()
        if not line: continue
        d=json.loads(line); md=d.get("metadata",{}) or {}
        inst=d.get("instance_id"); resolved=md.get("resolved"); tu=md.get("token_usage") or {}
        # NOTE: field names verified against the WORKING (resolved) schema on first real success;
        # adjust here if soma-bench uses different keys for tokens-with/without.
        tin=md.get("baseline_tokens") or tu.get("prompt_tokens_without_compression")
        tout=md.get("miner_tokens") or tu.get("prompt_tokens")
        ratio=(tin/tout) if (tin and tout) else ""
        w.writerow([inst, str(bool(resolved)).lower(), 0, 1, ratio, md.get("score",""),
                    "false","false", str(d.get("status")!="resolved" and not resolved).lower(), "", prof])
PY
echo "  wrote $RD/h1m_smoke_gate.csv  (review token fields vs real schema, then:)"
echo "  python3 $REPO/experiments/candidates/H1M_m7_deeper_safe_v1/h1m_run.py --results $RD/h1m_smoke_gate.csv"
echo "DONE. run dir: $RD"
