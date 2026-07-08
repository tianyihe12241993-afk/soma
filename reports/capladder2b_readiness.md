# CAPLADDER-v2b — UPLOAD-READINESS REPORT (comp-110)
_2026-07-08. First candidate to clear BOTH screener gates in the local emulator._

## Candidate
- **File:** `miner/cot_compression/upload_miner_capladder2b_v1.py`
- **sha256 (16):** `8cc04b837b9a2e20`  (frozen: experiments/candidates/CAPLADDER2_comp110/frozen/capladder2b_GO_8cc04b837b9a2e20.py)
- **Design:** interior-only structure-preserving compression. Fresh observation group (final msg + newest contiguous tool-run) + system/developer/user + all assistant messages verbatim. Interior tool reads: verbatim below FLOOR 1200; above it keep a 1200-char verbatim head + all top-level structure/imports/decorators/signatures/tracebacks/errors/failing-tests/paths/line-refs + tail, drop only CONTIGUOUS non-salient runs ≥5 lines → one approved marker each. Grep/search outputs self-salient → preserved. Deterministic, position-independent (cache-stable), fail-open, stdlib only.

## Codex verdict: **GO** (CONFIRMED-GO on re-audit)
- Round 1 NO-GO: single issue — non-list input returned `[]` (payload-erasing, not fail-open). FIXED → returns the original object untouched. Round 2 diff-audit: CONFIRMED-GO, only the fail-open line changed. Trail: scratchpad/codex_cl2b_audit.txt.
- Codex found NO violations in: marker templates, role protection, fresh-tail guard, CRLF-preserving whole-line keeps, net-reduction guard, min-run marker tiling, tool-structure integrity, stdlib/no-network/no-state.

## Gates run
- Rules/README compliance: GATE=PASS + FILE=PASS (live snapshot 2026-07-08).
- Tier-0 battery: PASS (fail-open None/str/int → unchanged; system/user/assistant untouched; fresh-tail incl. [tool,tool,assistant]; deterministic; whole-line + markers tile original exactly; net non-increase; CRLF byte-verbatim; floor passthrough).
- **Screener emulator (baseline set: PINNED `dpkbase_` DeepSeek seeds, n=2/task, 5 real screener tasks, 2 runs each, graded):**
  - **Gate A: PASS — 10/10 runs resolved, 5/5 tasks.**
  - **Gate B: PASS — weighted +47.0% / raw +56.4%** (gate 20%). est. platform score 1.438.
  - Per-task weighted sav: 13964 +83/+74 · 15375 +82/+81 · 15103 +41/−10 · 11551 −42/+35 · 13516 +37/−38 (two negative draws absorbed — qualifier-like).
  - The R2-fix does not affect these (real inputs are always lists; the changed branch never fires live).

## Remaining risks (honest)
1. **n=2 baselines are noisy** — 13964's pinned baseline drew heavy runs, flattering the aggregate. TRUE weighted mean is likely below 47%, but the emulator margin is 2.3× the gate → qualification verdict is robust to large shrinkage. Real screener uses ~3 attempts × its own fixed baseline.
2. **Per-run variance** — individual runs still swing (−42% to +83%); the screener's ratio-of-sums over 15 runs smooths this, as it did for the 5 real qualifiers.
3. **Correctness at scale** — local Gate A is 10/10 but on 5 tasks × 2 runs; the platform grades ≥50%-pass over its own screener set. Our architecture is Gate-A-perfect across ~130 runs, 10 architectures — lowest-risk dimension.
4. Hidden EVAL tasks (13→20 Jul) are unseen; screener qualification ≠ eval performance.

## Purpose of upload
Platform-truth screener test: does v2b's emulator qualification hold on the real screener (fixed baseline, ~3 attempts, real grading)? It is the first candidate whose local numbers justify spending a hotkey. It resembles the strong qualifier profile (5EPDbSXL: aggressive raw cut, non-breaking, cache-stable).

## Upload command (USER-run; spare hotkey; window closes 13 Jul 14:30 UTC)
```
cd /Users/eric.xiao/joshua-work/soma
~/.venvs/soma312/bin/python miner/upload_miner_with_openrouter_key.py \
  --platform_url https://platform.thesoma.ai --wallet_name oro-miner --hotkey_name <SPARE_HOTKEY> \
  --solution_file miner/cot_compression/upload_miner_capladder2b_v1.py \
  --openrouter_api_key "$(sed -n 's/^OPENROUTER_KEY_COMP110=\"\(.*\)\"$/\1/p' config/secrets.env)"
```
Prereqs: hotkey registered on netuid 114; OpenRouter key's account = **DeepSeek provider only** (verified pinned) + Data Collection ON. Read at `status=scored`: `screener_passed` + E/M/H.
