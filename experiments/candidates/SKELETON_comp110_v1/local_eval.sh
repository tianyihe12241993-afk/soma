#!/usr/bin/env bash
# Turnkey LOCAL eval for a comp-110 candidate on a PUBLIC instance (upload-window tasks are hidden).
# Measures the 3 platform-scored things: solve, weighted-token savings, explore quality — with all macOS
# fixes. Full guide: reports/local_testing_guide.md.  ⚠ Spends OpenRouter credits (~minutes/solve).
#
# Usage:  INSTANCE=django__django-14017 PROFILE=target BASELINE=1 \
#         TYPES="swebench_verified swe_explorer_explore swe_explorer_edit" \
#         bash experiments/candidates/SKELETON_comp110_v1/local_eval.sh
set -uo pipefail

INSTANCE="${INSTANCE:-django__django-14017}"
MINER="${MINER:-/Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_skeleton_v2.py}"
TYPES="${TYPES:-swebench_verified swe_explorer_explore swe_explorer_edit}"
BASELINE="${BASELINE:-1}"                 # also run the no-op baseline (needed for savings + explore gate)
PROFILE="${PROFILE:-target}"
CACHED_W="${CACHED_W:-0.1}"               # current weighted-token cached weight; UPDATE when the formula lands
SOMA=/Users/eric.xiao/joshua-work/soma
BENCH="$HOME/joshua-work/SOMA-benchmark"
SHIM="$HOME/.soma-shimbin"

mkdir -p "$SHIM"; printf '#!/bin/sh\nexit 0\n' > "$SHIM/modprobe"; chmod +x "$SHIM/modprobe"
export PATH="$SHIM:$PATH"
export OPENROUTER_API_KEY="$(sed -n 's/^OPENROUTER_KEY_COMP110="\(.*\)"$/\1/p' "$SOMA/config/secrets.env")"
[ -n "${OPENROUTER_API_KEY:-}" ] || { echo "FATAL: no OPENROUTER_KEY_COMP110 in config/secrets.env"; exit 1; }
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1" LLM_BASE_URL="https://openrouter.ai/api/v1"
export SOMA_SKEL_PROFILE="$PROFILE" SOMA_COPILOT_KEEP_STACK=true
cd "$BENCH" || exit 1

wtok() { # $1=output dir -> weighted tokens (1*input + CACHED_W*cache_read + 3*output)
  python3 -c "import json;d=json.load(open('$1/output.jsonl'));t=d['metadata'].get('token_usage',{});
print(1.0*t.get('input_tokens',0)+$CACHED_W*t.get('cache_read_tokens',0)+3.0*t.get('output_tokens',0))" 2>/dev/null || echo 0
}
status() { python3 -c "import json;d=json.load(open('$1/output.jsonl'));m=d['metadata'];pc=m.get('patch_capture') or {};print(d['status'],'patch='+str(pc.get('has_changes')))" 2>/dev/null || echo "n/a"; }

solve() { # $1=type $2=label $3=script-flag
  local out="outputs/lev_${INSTANCE}_$2_$1"
  echo ">>> solve: type=$1 label=$2  ($out)"
  uv run python -m soma_bench benchmark-solve --agent-name copilot \
    --benchmark SWE-bench/SWE-bench_Verified --instance-id "$INSTANCE" \
    --benchmark-type "$1" --execute --model deepseek/deepseek-v4-pro \
    $3 --output-dir "$out" >/dev/null 2>&1
  echo "$out"
}

echo "=== LOCAL EVAL  instance=$INSTANCE profile=$PROFILE miner=$(basename "$MINER") cached_w=$CACHED_W ==="
for T in $TYPES; do
  echo "----- benchmark type: $T -----"
  MOUT=$(solve "$T" miner "--copilot-compression-script-path $MINER")
  echo "  miner: $(status "$MOUT")  weighted=$(wtok "$MOUT")"
  if [ "$BASELINE" = "1" ]; then
    BOUT=$(solve "$T" baseline "")
    echo "  baseline: $(status "$BOUT")  weighted=$(wtok "$BOUT")"
    python3 -c "mv=$(wtok "$MOUT"); bw=$(wtok "$BOUT"); print('  weighted savings = %.1f%%'%((1-mv/bw)*100) if bw>0 else '  savings n/a')"
  fi
  if [ "$T" = "swe_explorer_explore" ]; then
    Q=""; [ "$BASELINE" = "1" ] && Q="--baseline-quality $(uv run python "$SOMA/scripts/score_explore_local.py" --instance-id "$INSTANCE" --output-dir "$BOUT" 2>/dev/null | sed -n 's/.*QUALITY (hit-noise) = //p') --miner-weighted $(wtok "$MOUT") --baseline-weighted $(wtok "$BOUT")"
    echo "  --- explore quality (miner) ---"
    uv run python "$SOMA/scripts/score_explore_local.py" --instance-id "$INSTANCE" --output-dir "$MOUT" $Q 2>&1 | sed 's/^/  /'
  fi
done

# firing evidence from the (kept) compression container, then tear down
CC=$(docker ps --format '{{.Names}}' | grep -E "compression-service" | head -1 || true)
if [ -n "$CC" ]; then
  echo "=== compression firing: $(docker logs "$CC" 2>&1 | grep -c '\[messages.in\]') transform calls ==="
fi
docker ps -aq --filter "name=soma-copilot" | xargs -r docker rm -f >/dev/null 2>&1
echo "=== done. outputs under $BENCH/outputs/lev_${INSTANCE}_* ==="
