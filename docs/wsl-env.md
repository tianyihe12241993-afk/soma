# WSL/Ubuntu environment (miner dev + ops)

The working environment for this repo lives in **WSL Ubuntu-22.04**. Set up with:

```bash
wsl -d Ubuntu-22.04 bash /mnt/e/soma/scripts/setup_wsl_env.sh
```

This is idempotent — re-run it any time to repair/refresh.

## Layout
- **venv:** `~/.venvs/soma` (on the Linux filesystem, for fast IO)
- **repo:** stays in place at `/mnt/e/soma` (the Windows `E:\soma`)
- **no sudo needed:** `python3 -m venv` bundles pip; `gcc`/`make`/`git` already present.

## Daily use
```bash
source ~/.venvs/soma/bin/activate
cd /mnt/e/soma
make collect      # immutable raw leaderboard snapshot
make reward       # normalize + compute the 7 reward elements
make detail       # per-task scores for our miners + element leaders
make detail ARGS="--all"          # all scored miners
make detail ARGS="--hotkey 5Gs..." # specific miner(s)
make status       # latest pointer + projection + last checkpoint
make checkpoint NOTE="what changed"
pytest miner/cot_compression/test_improved_miner.py   # miner unit test
```

## Installed (pinned to the repo's known-good set)
bittensor 9.0.0 + btcli 9.13.1, bittensor-wallet 4.0.1, async-substrate-interface
1.5.15, scalecodec 1.2.11, tiktoken 0.12.0, PyYAML 6.0.3, httpx 0.28.1,
python-dotenv 1.2.1, pytest 9.0.2 / pytest-asyncio 1.3.0, requests 2.32.5.

> **Substrate note:** we pin `async-substrate-interface==1.5.15` (uses `scalecodec`,
> not `cyscale`). If you let pip pull a newer one it installs `cyscale`, which
> clobbers the `scalecodec` namespace and breaks `import bittensor`. The setup
> script has a safety-net repair for this.

## NOT installed here — needed only to UPLOAD a miner
1. **`soma_shared`** (the upload scripts import it). Private DendriteHQ repo:
   ```bash
   pip install "git+https://github.com/DendriteHQ/SOMA-shared.git@main"
   ```
   May need a GitHub token / repo access. (Claude's sandbox blocks installing from
   external git repos, so run this yourself.)
2. **A Bittensor wallet** registered on netuid 114 (`btcli wallet ...`). The Linux
   home currently has only an unrelated `sn3miner` wallet; `btcli wallet list` will
   error on it until you add/repair your competition wallet. btcli itself works.

## Full subnet stack (validator / platform / local SWE-bench eval)
Not installed (scope was "miner dev + ops"). For that, install `requirements.txt`
in full and enable the Docker daemon (Docker Desktop → Settings → Resources → WSL
integration → enable Ubuntu-22.04).
