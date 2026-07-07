# comp-110 (CoT-Compression-5) — MINER BRIEF + setup status (2026-07-07)

_Sources: Discord announcement (raw: `data/raw/discord_notes/2026-07-06_comp109_round5_announcement.md`),
upstream DendriteHQ/SOMA@main (merged locally), SOMA-benchmark@main (cloned to `~/joshua-work/SOMA-benchmark`,
pushed 2026-07-06 14:36Z = the comp-110 release), SOMA-shared (now PUBLIC), live dashboard flight._

## What comp-5 is (all confirmed from code, not just chat)
- **Timeline:** uploads 06 Jul 14:30 → **13 Jul 14:30 UTC**; eval 13→20 Jul. Platform `competition_id: 110`.
- **New agent:** the official **`@github/copilot` CLI** in a sandboxed Docker Compose stack
  (`copilot` + `proxy` sidecar + `compression-service` sidecar), offline-auth, pointed at the gateway.
  Replaces OpenClaw entirely (platform executor rewritten upstream: `sandbox_service/app/compact_bench_executor.py`).
- **New model:** `deepseek/deepseek-v4-pro`, **`GATEWAY_FORCE_PROVIDER=deepseek`** (from `.env.example` upstream).
  ⇒ the DeepSeek provider is forced on the miner's OpenRouter key → the OpenRouter account MUST have
  Data Collection ON (both) + DeepSeek provider enabled in Guardrails, or runs fail.
- **3 task types** (`_BENCHMARK_TYPES` in the orchestrator), 50 tasks × 5 runs each = 750 runs:
  1. `swebench_verified` — classic solve: problem statement → patch.
  2. `swe_explorer_explore` — **NEW**: agent explores the repo and reports the regions it read
     (written to `/workspace/explore-result.json`); NO patch. Quality = hit_file_rate − noise_file_rate.
  3. `swe_explorer_edit` — **NEW**: agent gets the ground-truth modified files as a hint → patch.
- **Scoring:** per-task-type layers replace E/M/H (same 7-element combinatorial structure, categories =
  task types). Weighted tokens carry over (1.0 input / ⅓ cached / 3.0 output). swebench flip = +2, break = −4.
  **Explore score = smoothstep(quality margin vs baseline; ≤−0.20 → floor −2) × clamp(2·log2(weighted savings), ±2).**
  ⇒ **passthrough scores ZERO on explore tasks** — you must compress to score there, but −0.20 quality
  margin nukes you to −2. Savings gated by preserved exploration quality.
- **Prompt rules:** README_prompting.md UNCHANGED and FROZEN for the round (gate PASS 2026-07-07).
- Tasks from SWE-bench Verified; owners may HIDE the exact task list this round (anti-overfit).

## ⚠️⚠️ THE INTERFACE BREAK (the headline finding)
**comp-108 miners are INCOMPATIBLE with comp-110 as-is.** The champion `upload_miner_uphard_salience.py`
(cap32+pin, sha256 695b4fe4) speaks the OLD OpenClaw protocol: a subprocess reading a trajectory JSON on
stdin (`python miner.py assemble`). The comp-110 stack replaced that with SOMA-benchmark's compression
service (`soma-copilot-compression-service:latest`), which **imports the miner as a Python module** and calls:

```python
compress_messages(messages: list, path: str, metadata: dict) -> list
```
(also accepted names: `compress_payload` / `process_request` / `transform_payload`)

- `messages` = the **OpenAI-style chat messages array of each outgoing LLM request** (the proxy intercepts
  every Copilot→LLM call and POSTs `/transform`). Return the compressed list → it replaces `payload["messages"]`.
- The module is loaded ONCE per run → **module-level state persists across requests** (block-reference /
  dedupe schemes remain possible).
- No `assemble`, no trajectory JSON, no `baseMiner` envelope, no stdout protocol.

**⇒ The title defense REQUIRES porting cap32+pin's logic to the new contract.** What carries over conceptually:
cap huge tool-result contents (~32k zone), pin imports/decorators/raise/except (`_STRUCT_PATTERN` regex is
reusable verbatim), `[[CMP]]`/`[[BLOCK X]]` markers (still the allowed set), loop-detection reasons,
byte-stable prefix for prompt caching (weighted tokens still favor cached ⅓). What must be re-engineered:
message-array traversal (tool results live in `role:"tool"` / assistant tool_call messages now), pairing
rules, and the explore-mode tradeoff (keep exploration quality while cutting tokens).
**Porting = new candidate file; per hard rules, build only on explicit instruction; upload = USER.**

## Local eval (this MacBook, Docker Desktop) — the new flow
```bash
cd ~/joshua-work/SOMA-benchmark
cp .env.example .env     # add OPENROUTER_API_KEY; LLM_MODEL=openrouter/deepseek/deepseek-v4-pro to mirror the comp
uv sync                  # one-time env resolve (USER runs — see checklist)
# smoke one instance with a miner mounted:
source .env && uv run python -m soma_bench benchmark-solve \
  --agent-name copilot --benchmark SWE-bench/SWE-bench_Verified \
  --instance-id <ID> --benchmark-type swebench_verified --execute \
  --copilot-compression-script-path /absolute/path/to/candidate.py \
  --output-dir outputs/smoke --swerebench-eval
# explore mode: --benchmark-type swe_explorer_explore (regions land in explore-result.json)
```
Comp-108 caveat still applies until re-proven: local eval was NOISY/unreliable for compressor A/Bs —
the platform is the arbiter. But the NEW stack logs `[compression-service][messages.in/out]` per request,
so at minimum we can now verify the miner actually FIRES locally (which comp-108's local eval could not).

## Setup status on this MacBook
| piece | status |
|---|---|
| SOMA-benchmark + SOMA-plugin clones | ✅ `~/joshua-work/{SOMA-benchmark,SOMA-plugin}` |
| venv `~/.venvs/soma` (bittensor 9.12.2, httpx, dotenv) | ✅ |
| soma_shared (upload signing; repo now PUBLIC) | ⏳ USER: `~/.venvs/soma/bin/pip install "git+https://github.com/DendriteHQ/SOMA-shared.git"` |
| uv | ✅ `/opt/homebrew/bin/uv` |
| soma-bench env (`uv sync`) | ⏳ USER runs (external-code execution) |
| Docker images (copilot-cli, compression-service) | 🔄 building in background |
| Docker daemon | ✅ 29.2.1 |
| upload runbook | `miner/upload_miner_with_openrouter_key.py` — needs venv + soma_shared + wallet + hotkey |
| ops tools (collector/gates/watcher) | ✅ all rebuilt + tested (see NEXT_ACTIONS ENV READY block) |

## Strategy skeleton (USER decides; Codex red-team pending)
1. **Port cap32+pin → `compress_messages`** (the only path to any submission at all). Keep it minimal &
   compliance-clean; verify with the local smoke (miner FIRES + run completes) + `check_readme_current.py --check-file`.
2. **Explore-layer variant:** the explore formula pays savings ONLY if quality holds — a conservative
   cap-only compressor (no aggressive trimming of file-path-bearing lines) is the safest first probe.
3. Screener = 5 tasks; don't burn the hotkey before both gates + Codex audit pass.
4. Baseline costs + task visibility land ~07 Jul — re-read before finalizing knobs.
