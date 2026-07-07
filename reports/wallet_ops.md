# Wallet ops runbook (btcli 9.23.1) — unstake + transfer

_USER runs these (they move real funds + need the coldkey password; the agent never runs them).
Wallet = `tony-miner` (coldkey `5FX5SGtt…`, NO seed backup — see recover_seed.py / DISCOVERIES for the
recovery + swap-coldkey Plan B). Substitute placeholders. Clear shell history after (`history -d`)._

## 1. Check free (unstaked) balance first
```bash
btcli wallet balance --wallet-name tony-miner
```

## 2. Unstake from ALL hotkeys (frees alpha stake back to TAO in the coldkey)
```bash
btcli stake remove --wallet-name tony-miner --all-hotkeys --unstake-all --safe --tolerance 0.05 --partial
```
- `--all-hotkeys` = every hotkey under the coldkey; `--unstake-all` = all stake; add `--all-netuids` if it doesn't cover every subnet.
- **Dynamic-TAO slippage:** unstaking converts alpha→TAO at the market rate; large unstakes move the price. `--safe --tolerance 0.05` caps the rate change at 5% and `--partial` completes a partial fill rather than executing a bad one. Raise/lower tolerance to taste.
- Prompts for the coldkey PASSWORD and shows the full unstake plan BEFORE executing — read it, then confirm.
- Alternatives: `--all-alpha` / `--unstake-all-alpha` (alpha only), `--include-hotkeys hk1,hk2` / `--exclude-hotkeys …` (subset), `--netuid N` (one subnet), `--amount X` (partial).

## 3. Transfer TAO to another wallet (AFTER unstaking settles)
```bash
btcli wallet transfer --wallet-name tony-miner --dest <RECIPIENT_SS58> --amount <TAO>
```
- `--dest`/`-d` = recipient ss58 (PASTE it, verify char-by-char — transfers are IRREVERSIBLE).
- `--amount`/`-a` = TAO (float). Leave a little for the fee; avoid `--all`/`--allow-death` unless emptying+reaping the account.
- Shows balance → prompts for the coldkey PASSWORD → confirmation → submits.

## Notes
- Order matters: unstake FIRST (frees TAO), let it settle, THEN transfer the free balance.
- Chain spec 423/424 (2026-07): "locked alpha transfers in coldkey swaps" now allowed — if instead of unstake+transfer you want to migrate to a NEW backed-up coldkey, `btcli wallet swap-coldkey announce/execute` carries staked positions (2-step, ~5-day delay). See DISCOVERIES 2026-07-02.
