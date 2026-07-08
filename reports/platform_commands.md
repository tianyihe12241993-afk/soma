# Platform commands — runbook (SN114 comp-108/110)

> **⚠️ comp-110 UPLOAD ENV (2026-07-08, this MacBook):** the upload script imports `soma_shared.contracts.miner.v1.messages`,
> which uses `str | None` syntax → **requires Python 3.10+**. The old `~/.venvs/soma` is Python **3.9** → upload fails at
> import (`TypeError: unsupported operand type(s) for |`). FIX (built): **`~/.venvs/soma312`** (Python 3.12) with
> `uv venv --python 3.12 ~/.venvs/soma312 && uv pip install --python ~/.venvs/soma312/bin/python bittensor httpx python-dotenv git+https://github.com/DendriteHQ/SOMA-shared.git`
> (installed bittensor **10.5.0** — if wallet-load/signing errors, pin `bittensor==9.12.2`). comp-110 uploads = command #2
> (`upload_miner_with_openrouter_key.py`, OpenRouter key mandatory for DeepSeek routing). First comp-110 test: candidate
> `miner/cot_compression/upload_miner_skel_recoff_v1.py`, wallet `oro-miner`, hotkey `m1`.


_Operational commands for uploading miners + managing the OpenRouter key on the platform.
**SECURITY: the OpenRouter key is a SECRET — never commit it. It lives only in `config/secrets.env`
(git-ignored). The `<OPENROUTER_KEY>` below is a PLACEHOLDER; substitute your real key at run time.**
USER runs these externally (platform ops + raw secret are not done by the agent). Run from repo root with the venv:
`.venv/bin/python ...` (the venv has `soma_shared`/bittensor)._

## Standing values
- `--platform_url https://platform.thesoma.ai`
- `--wallet_name tony-miner`
- `--hotkey_name` = the LOCAL bittensor hotkey LABEL (e.g. `m22`), not the ss58. The script derives the ss58.
- **Key discipline:** always use the SAME OpenRouter ACCOUNT as m12 (the `…1e8a` lineage). A different ACCOUNT
  = weaker/different backend = CONFOUNDED score (the m14 lesson: false 0.423). Same account, fresh key = fine.

## Hotkey registry (label → ss58 → what)
- `m22` → `5CffmtHw6Ug2voLWV6KXeJJzCkEPzDDvkCgtjffrFd9AJiG7` → m22 candidate (key `…c7e299`, same acct as m12)
- m12 (LIVE) → `5Dz7JaCBw6t9ktdRVaLYi3ntEzvCDfb5XmTHyzPdDyT6KS9j` (key `…1e8a`)
- (full registry + status in `config/miners.yaml`)

## 1. Upload a miner solution (no key change)
```bash
.venv/bin/python miner/upload_miner.py \
  --platform_url https://platform.thesoma.ai \
  --wallet_name tony-miner \
  --hotkey_name <HOTKEY_LABEL> \
  --solution_file miner/cot_compression/<SOLUTION>.py
```

## 2. Upload a miner solution AND set its OpenRouter key (one shot)
```bash
.venv/bin/python miner/upload_miner_with_openrouter_key.py \
  --platform_url https://platform.thesoma.ai \
  --wallet_name tony-miner \
  --hotkey_name <HOTKEY_LABEL> \
  --solution_file miner/cot_compression/<SOLUTION>.py \
  --openrouter_api_key <OPENROUTER_KEY>
```
Use for a NEW miner, or to FORCE a key onto an already-queued miner if the platform bound the key at submission
(re-uploads → restarts the pipeline: in queue → screening → evaluating → scored).

## 3. Update ONLY the OpenRouter key (no re-upload — keeps queue position)  ← used for m22 on 2026-06-25
```bash
.venv/bin/python miner/update_openrouter_api_key.py \
  --platform_url https://platform.thesoma.ai \
  --wallet_name tony-miner \
  --hotkey_name <HOTKEY_LABEL> \
  --openrouter_api_key <OPENROUTER_KEY>
```
POSTs a wallet-signed request to `…/miner/openrouter-key/update`. Swaps the key server-side for that hotkey,
leaving the queued/scored submission in place. After running, `make collect` and confirm the miner is NOT
stalled on `no api key`/quota (the tell that the update didn't bind → fall back to command #2).

## 4. Delete the OpenRouter key for a hotkey
```bash
.venv/bin/python miner/delete_openrouter_api_key.py \
  --platform_url https://platform.thesoma.ai \
  --wallet_name tony-miner \
  --hotkey_name <HOTKEY_LABEL>
```

## After any of these
- `make collect` → check the dashboard status (read scores ONLY when `scored`, never `evaluating` — the 5DAh trap).
- Hygiene: the key lands in shell history when passed as `--openrouter_api_key` — clear it (`history -d <line>`) if needed.
- m12 (`5Dz7…`) stays LIVE/untouched unless explicitly promoting a beaten-it-scored candidate.
