# Improved CoT-compression miner

`improved_miner.py` is a drop-in replacement for the SOMA-plugin `base_miner.py`
(the file the platform injects your upload as). Same protocol as the reference:
`python improved_miner.py assemble`, connector payload on stdin, one JSON object
on stdout. Stdlib only; uses tiktoken for the reported token estimate when
available (it is, in the compression-service image).

## Why it should beat the reference baseline

The reference keeps only the first user message + the last 4 tool results and
deletes everything else — all assistant reasoning, all earlier discoveries, and
any later user messages. Under the scoring formula, breaking a passing baseline
run costs −4 while extra token savings earn at most +1, so destroying context
is the expensive failure mode, not under-compressing (as long as total savings
stay ≥ 20%, where the savings multiplier saturates).

This miner instead:

- keeps every user/system message and all assistant text (plan + findings)
- keeps the newest tool interactions intact (newest 2 byte-exact)
- head+tail-truncates older tool results instead of deleting them
- fully drops only the oldest interactions under a token budget
- leaves a one-line digest per dropped interaction (tool, args, result snippet,
  discovered file paths) in a sentinel block inside the first user message —
  carried forward and regenerated each round, never nested
- drops exact-duplicate tool results first (repeated file reads/greps)
- preserves toolCall/toolResult pairing by construction, with an orphan-check
  fallback to sanitize-only output as a last-resort safety valve

### v2: prompt-cache preservation

The first e2e run showed v1 *losing* tokens on short tasks because it mutated
the trajectory every call, invalidating the provider's prompt cache (uncached
input is re-billed on every LLM call). v2 makes compression cost cache misses
only when it actually changes history:

- **Pass-through below the budget** (`ACTIVATION_TOKENS = 10k`): returns
  `changed=False` so OpenClaw sends its native, cache-warm context untouched —
  identical to a no-plugin run. No compression tax on short tasks.
- **Activation hysteresis**: once a session crosses the budget it stays managed,
  so each later round extends the previous compressed output rather than
  flipping between compressed and raw shapes.
- **Absolute target + pressure relief**: compress to `TARGET_TOKENS = 10k`, and
  when over it prune to 75% of target. The headroom makes following rounds pure
  appends (byte-stable prefix → cache hits) until the budget is hit again,
  instead of re-pruning every call.
- **Sticky truncation escalation** persisted in state so depth never flaps.

`run_cache_stability` asserts this: under simulated gradual growth, every
non-pruning round keeps a byte-identical compressed prefix.

Measured on the SOMA sample trajectories (chars/4 estimate, vs reference):

| case | input | improved | reference |
|---|---|---|---|
| sample-4 (13.8k tok) | 64 msgs | 71% savings, 51% of file paths kept, 100% assistant text | 92% savings, 16% paths, 0% assistant text |
| synthetic-long (198k tok) | 735 msgs | 93% savings, 653 ms | 99% savings |

## Test locally

```bash
python3 miner/cot_compression/test_improved_miner.py
```

Full end-to-end (real agent run, needs Docker + an OpenRouter key):

```bash
cp miner/cot_compression/improved_miner.py /path/to/SOMA-plugin/base_miner.py
cd /path/to/SOMA-benchmark && pip install -e .
python -m soma_bench benchmark-solve --agent-name openclaw \
  --benchmark SWE-bench/SWE-bench_Verified --instance-id <id> \
  --openclaw-plugin-path /path/to/SOMA-plugin --execute
```

## Upload

```bash
python3 miner/upload_miner_with_openrouter_key.py \
  --platform_url https://platform.thesoma.ai \
  --wallet_name <wallet> --hotkey_name <hotkey> \
  --solution_file miner/cot_compression/improved_miner.py \
  --openrouter_api_key <key>
```

Remember: one upload per competition window — run the local harness and at
least one end-to-end benchmark task before submitting.

## Tuning knobs (top of `improved_miner.py`)

- `ACTIVATION_TOKENS` / `TARGET_FRACTION` / `MIN_TARGET_TOKENS` — how early and
  how hard to compress (raise `TARGET_FRACTION` for safety, lower it for savings)
- `KEEP_RECENT_FULL` / `UNTOUCHABLE_RECENT` — size of the protected tail
- `MID_*` / `ASSIST_*` / `*_CAP` — truncation budgets per tier
