# INTERIOR-ULTRA v1 — upload-readiness report (m1 re-upload)

_2026-07-08. Candidate: `miner/cot_compression/upload_miner_interior_ultra_v1.py`, sha256 **630377f4…**
(frozen: experiments/candidates/INTERIOR_ULTRA_comp110_v1/frozen/interior_ultra_v1_GO_630377f4.py).
Upload is USER-run on hotkey m1 (oro-miner). Screener ≈ 10-min oracle._

## Design (m1 post-mortem applied)
skeleton_v2 base; **interior-only** compression at **ultra (300,1,1,250)** hardcoded (no env knob).
NEVER compressed: system/developer/user, assistant-with-tool_calls, the final message, and the
**newest contiguous tool-run anywhere in the list** (Codex-demanded guard — the fresh reads the agent
acts on are provably untouchable, incl. `[…, tool(fresh), assistant]` orderings and parallel tool calls).
Interior history → path/error/test/import/signature skeleton + exact approved `[[CMP]]` line-range markers.
Whole-line byte-verbatim keeps, true budget cap, net-reduction only, deterministic, position-independent
(cache-stable), fail-open, stdlib only, no pin/dedupe/state.

## Gates
- **Rules/compliance:** GATE=PASS + FILE=PASS (live README snapshot 2026-07-08).
- **Offline battery:** 24/24 PASS (system/user/tool_calls untouched; fresh-tail verbatim incl. parallel
  runs + Codex counter-example; determinism; no mutation; CRLF byte-verbatim; RANGE markers tile the
  original exactly; budget true-cap 241≤250; fail-open). One harness line "no disallowed marker text"
  is a KNOWN TEST BUG (regex missing re.M) — disproven by the corrected per-line check (0 violations).
- **Real-payload reduction:** **29.6%** over all 734 captured requests (recency-protected). Weighted
  model ≈ ×0.75 → ~22% predicted weighted savings — above the 20% gate with margin, platform decides.
- **Codex audit:** round 1 GO-WITH-CHANGES (fresh-tail ordering hole + env knob) → both fixes applied
  exactly as prescribed + counter-example test PASS → micro re-confirm launched (scratchpad
  codex_iu_confirm.txt; read before upload). Trail: scratchpad codex_iu_out.txt.

## Honest risks
- Interior-ultra (budget 250) drops most interior prose/code bodies; comp-108 evidence says interior
  compression is break-TOLERABLE (np2 ~89% pass), not break-free. Expected shape: some Easy sacrifice
  (the qualifier rides −0.56), Medium/Hard hold, savings ≥20%.
- Markers are message-local line numbers; no steering to re-read (compliant, but re-read is agent-initiative).

## Upload + oracle loop (USER)
```
~/.venvs/soma312/bin/python miner/upload_miner_with_openrouter_key.py \
  --platform_url https://platform.thesoma.ai --wallet_name oro-miner --hotkey_name m1 \
  --solution_file miner/cot_compression/upload_miner_interior_ultra_v1.py \
  --openrouter_api_key "$(sed -n 's/^OPENROUTER_KEY_COMP110=\"\(.*\)\"$/\1/p' config/secrets.env)"
```
Read at scored (~10 min): **solves but savings <20% → tighten** (budget 250→180) · **breaks (E/M ≤ −2) →
loosen** (→ deep 380) · **passes → freeze + prepare final**. Baseline for comparison: m1-v1 was
E −3.98 / M −3.10 / H +1.13, screener FAIL.
