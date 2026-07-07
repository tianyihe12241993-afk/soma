# LEAN v2 — comp-110 candidate build report (2026-07-07)

**Status: BUILT + LOCALLY VERIFIED + CODEX GO (after 2 NO-GO rounds). NOT uploaded, NOT committed
(per instruction). USER decides next.** Current sha256 `163be033888029714de86d8f…`.

## Codex pre-upload audit trail (gate #1, dual-agent protocol)
- **Round 1 → NO-GO** (`reports/codex_lean_v1_audit.md`): 5 blocking — compressing user messages
  (compliance), partial-line output, net-increase block-wrapping, no recency protection, pin surface.
  I also found a latent tiered-budget dead-zone. All 6 fixed (dedupe cut; whole-line-only; user/system/
  developer never touched; final-message recency; clean budget model).
- **Round 2 → NO-GO** (`reports/codex_lean_v1_reaudit_round2_GO.md` has round-2 body too / round1 file):
  4/5 confirmed; new objection = recency protection is position-dependent (cache). Reconciled: it's a
  fundamental break-safety-vs-cache tradeoff (Codex's own fix #4), not a defect. Tightened to
  FINAL-MESSAGE-ONLY + toggle (`SOMA_LEAN_RECENCY=0`) + honest docstring.
- **Round 3 → GO** (`reports/codex_lean_v1_reaudit_round2_GO.md`): all fixes hold; every non-final
  message confirmed position-independent (tight cache invariant); residual transition agreed
  fundamental; compliant / deterministic / fail-open. Verdict GO.

## Files created/changed (all uncommitted)
| file | what |
|---|---|
| `miner/cot_compression/upload_miner_lean_v1.py` | the candidate (LEAN v2) — sha256 `163be033888029714de86d8f…` |
| `experiments/candidates/LEAN_comp110_v1/test_lean_miner.py` | standalone stdlib test harness (30 checks) |
| `experiments/candidates/LEAN_comp110_v1/BUILD_REPORT.md` | this report |
| `scripts/check_readme_current.py` | gate fix: fold f-string `[[BLOCK …]]` placeholders (lazy match to first `]]`) |
| `data/raw/readme_prompting/2026-07-07_0529*.md` | gate-run README snapshots (raw, immutable) |

## Contract (verified from code, not assumed)
`compress_messages(messages, path=None, metadata=None) -> list`, imported as a module by the
compression sidecar (`SOMA-benchmark/src/compression_service/app/main.py`), called on EVERY
outgoing LLM request; returned list replaces `payload["messages"]` (proxy.py `_transform_payload_
via_compression_service`). **Discrepancy vs the build prompt, reported as required:** `metadata`
is only `{"path": path}` — NO task/mode information exists in the contract. Mode-adaptive behavior
would have to be inferred from message content; NOT implemented (compliance question outstanding).
A second intentional deviation: "preserve recent turns more than older" is implemented as
SIZE-tiering, not turn-recency — recency-dependent rules would re-compress messages differently as
they age, breaking the byte-stable prefix that the ⅓-weighted cache pays for (comp-108-proven).
The suffix is still naturally fuller: the newest turns are small until their tool results arrive.

## Design implemented (per postmortem conclusions)
- **Tiered cap** (ported): ≤min passthrough / mid → line-extraction to budget / >53k (proven
  boundary) → head+signal+tail to larger budget. Profiles via `SOMA_LEAN_PROFILE`:
  conservative (9k/16k/30k) · **target (6k/10k/18k, default)** · aggressive (4k/6k/10k) [chars].
- **Quality floor**: traceback frames, error/exception/FAILED/assert, test names, diff markers,
  def/class signatures, imports, file paths, `line N` refs ALWAYS survive (explore hit-rate +
  swebench edit-location safety).
- **Endurance/leanness**: deep per-step budgets (M-winner zone), aiming at more surviving agent steps.
- **Break-aversion**: fail-open (any exception → original messages returned); system/developer,
  tool_calls, non-text parts, None content, order/count/roles never touched; input never mutated.
- **Determinism + cache stability**: pure function of (content, profile); growing-history prefix
  re-compresses byte-identically (tested); dedupe numbering stable by first-occurrence order.
- **Dedupe**: identical ≥2k blocks → first occurrence `[[BLOCK n]]…[[/BLOCK n]]`, repeats →
  `Same response as in [[BLOCK n]].` (all README §5.1 allowed strings; markers wrap ORIGINAL
  extracted lines only — no counts/descriptions, the 5Fjms DQ lesson).
- **Pin NOT ported** (Codex-verified net-negative). Isolated experiment flag `SOMA_LEAN_PIN=1`
  (adds @decorator/raise/except to keep-patterns) — OFF by default, local A/B only.

## Test results
`python3 experiments/candidates/LEAN_comp110_v1/test_lean_miner.py` — **ALL PASS × 4 configs**
(conservative / target / aggressive / target+pin-flag). Coverage: contract; structure preservation
(roles/order/count, system & tool_calls & parts & None untouched, no input mutation, JSON-safe);
quality floor (traceback/FAILED/import/path lines survive); marker compliance (exact allowed strings
only, no "omitted/truncated/elided" descriptions); tier budgets honored (huge→≤1.2×budget);
determinism (byte-identical); dedupe; growing-history prefix stability; hostile shapes fail-open.

Observed ratios (chars, synthetic):
| profile | bulk-heavy overall | huge block | realistic mix |
|---|---|---|---|
| conservative | 3.89× | 5.24× | 3.14× |
| **target** | 6.34× | 8.73× | **4.29×** |
| aggressive | 10.85× | 15.65× | 5.66× |

⚠️ Calibration note: the ~2.5× goal is a RUN-LEVEL platform TOKEN ratio (M-winner's
tokens_without/tokens_with); synthetic char ratios are only a proxy (real runs add system prompts,
assistant turns, many small requests). Run-level depth must be calibrated in real eval — if target
proves too deep, conservative is one env var away.

## Real-stack E2E (the actual comp-110 sidecar image)
Mounted into `soma-copilot-compression-service:latest`, POSTed `/transform`:
`compressor_loaded: true` · 195,391 → 17,997 chars (10.9×, exactly at budget) · traceback frame
survives · `[[CMP]]` markers present · byte-identical across repeat calls · system/user untouched.

## Compliance
`check_readme_current.py --check-file upload_miner_lean_v1.py` → **GATE=PASS + FILE=PASS**
(after fixing a gate false-positive on f-string placeholders; champion file re-checked, still PASS).
Emitted strings ⊆ README §5.1: `[[CMP]]` `[[/CMP]]` `[[BLOCK X]]` `[[/BLOCK X]]`
`Same response as in [[BLOCK X]].` No loop injection (endurance evidence says never kill runs).

## Uncertainties (honest)
1. **Real message shape unobserved** — no fixtures exist; parts-list/tool_calls handling is
   defensive but unexercised against real copilot CLI traffic. First real run should check the
   `[compression-service][messages.in/out]` logs.
2. **Run-level depth uncalibrated** (see above); DeepSeek V4 Pro's sensitivity to extraction unknown.
3. **Copilot CLI may resend histories with its own structure** (e.g. re-chunked reads) — dedupe
   hit-rate unknown until observed.
4. **Explore-mode adaptivity** not implemented (no mode signal in contract; content-inference is a
   compliance question to settle on-channel before any such variant).

## Design changes from the audit (what the shipped v2 actually does)
- Compresses ONLY `tool` outputs + non-final `assistant` reasoning (the CoT). NEVER system/developer/user.
- Whole-original-lines extraction only; giant single-line content (minified JSON) left verbatim.
- Tiered char budgets per profile (conservative/target/aggressive); `[[CMP]]` emitted only on net reduction.
- Quality floor kept (paths/errors/tests/diffs/imports/signatures/line-nums always survive).
- Final message left verbatim (recency/break-safety); toggle `SOMA_LEAN_RECENCY=0`.
- Dedupe/`[[BLOCK]]` REMOVED (was cache-unstable + net-increase). Pin OFF (`SOMA_LEAN_PIN=1` = local A/B only).

## Recommended next A/B runs (before ANY hotkey)
1. **Keyless**: none left — sidecar E2E done (interior cache-stability + all break scenarios verified).
2. **One real smoke solve** (needs OPENROUTER key; USER runs):
   `cd ~/joshua-work/SOMA-benchmark && source .env && uv run python -m soma_bench benchmark-solve \
     --agent-name copilot --benchmark SWE-bench/SWE-bench_Verified --instance-id <easy-id> \
     --benchmark-type swebench_verified --execute --swerebench-eval \
     --copilot-compression-script-path /Users/eric.xiao/joshua-work/soma/miner/cot_compression/upload_miner_lean_v1.py \
     --output-dir outputs/lean-v1-smoke`
   Read: run completes e2e · messages.in/out logs show firing · token totals vs a no-script control run.
3. **Depth A/B** (same instance × {conservative, target, aggressive} via `SOMA_LEAN_PROFILE`):
   compare steps-survived, tokens/step, pass — pick the profile nearest 2.5× run tokens without breaks.
4. **Explore-mode smoke**: `--benchmark-type swe_explorer_explore` — verify `explore-result.json`
   regions still hit the right files under compression.
5. **Pin A/B** (optional): `SOMA_LEAN_PIN=1` vs off on the same instance — the isolation test the
   pin never had.
6. Then: Codex pre-upload audit (gate #1 of the dual-agent protocol) on final bytes → USER upload decision.
