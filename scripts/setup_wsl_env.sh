#!/usr/bin/env bash
# Set up the SOMA "miner dev + ops" environment in WSL/Ubuntu. Idempotent.
#
#   wsl -d Ubuntu-22.04 bash /mnt/e/soma/scripts/setup_wsl_env.sh
#
# Layout: venv on the Linux filesystem (fast IO) at ~/.venvs/soma; the repo stays
# in place at /mnt/e/soma. No sudo required (python3 -m venv bundles pip).
#
# Installs (pinned to the repo's known-good set so the scalecodec/cyscale
# namespace clash never happens — async-substrate-interface 1.5.15 uses
# scalecodec, not cyscale):
#   bittensor + btcli, wallet/substrate stack, tiktoken, PyYAML, pytest,
#   httpx + python-dotenv (for the upload script), requests.
#
# NOT installed here (do these yourself when you need to UPLOAD a miner):
#   - soma_shared  : pip install "git+https://github.com/DendriteHQ/SOMA-shared.git@main"
#                    (private DendriteHQ repo; may need a GitHub token)
#   - a Bittensor wallet registered on netuid 114 (btcli wallet ...)
set -u
VENV="$HOME/.venvs/soma"
PIP="$VENV/bin/pip"
PY="$VENV/bin/python"

[ -d "$VENV" ] || python3 -m venv "$VENV"
"$PIP" install --upgrade pip setuptools wheel >/dev/null

echo "installing miner-dev + ops stack into $VENV ..."
"$PIP" install \
  bittensor==9.0.0 bittensor-cli==9.13.1 \
  async-substrate-interface==1.5.15 bittensor-wallet==4.0.1 scalecodec==1.2.11 \
  httpx==0.28.1 python-dotenv==1.2.1 tiktoken==0.12.0 PyYAML==6.0.3 \
  pytest==9.0.2 pytest-asyncio==1.3.0 requests==2.32.5

# safety net: if a resolver picked cyscale and broke the scalecodec namespace,
# repair it (no-op when bittensor already imports cleanly).
if ! "$PY" -c "import bittensor" >/dev/null 2>&1; then
  echo "repairing scalecodec namespace (cyscale clash) ..."
  "$PIP" uninstall -y cyscale scalecodec >/dev/null 2>&1
  "$PIP" install --force-reinstall --no-deps --no-cache-dir scalecodec==1.2.11 >/dev/null
fi

echo "===== verification ====="
"$PY" - <<'PYEOF'
import importlib
for m in ("bittensor","bittensor_wallet","scalecodec","tiktoken","yaml","httpx","dotenv","requests","pytest"):
    try:
        mod=importlib.import_module(m); print(f"  {m:16}", getattr(mod,"__version__","ok"))
    except Exception as e:
        print(f"  {m:16} FAIL: {e}")
PYEOF
echo -n "  btcli            "; "$VENV/bin/btcli" --version 2>&1 | head -1
"$PY" -c "import soma_shared" 2>/dev/null && echo "  soma_shared      ok" \
  || echo "  soma_shared      not installed (upload-only; see header)"
echo
echo "Activate with:  source ~/.venvs/soma/bin/activate"
echo "Then in /mnt/e/soma:  make collect / make reward / make detail / pytest"
