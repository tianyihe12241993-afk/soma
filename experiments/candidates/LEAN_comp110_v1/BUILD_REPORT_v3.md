# LEAN v3 — comp-110 candidate build report (2026-07-07)

**Status: BUILT + CODEX GO (gate #1, after 1 NO-GO round). All 10 required verification gates PASS.
NOT uploaded, NOT committed (standing rule). Smoke BLOCKED only on the user `.env` step.**
Files: `miner/cot_compression/upload_miner_lean_v3.py` (sha256 `c8f540b2…`), frozen at
`experiments/candidates/LEAN_comp110_v1/frozen/lean_v3_GO_c8f540b2.py`.

## What v3 is (delta from the Codex-GO v2)
LEAN v2's compliance skeleton, but elisions now emit LOCATABLE source-line omission markers instead
of dropping middle lines silently:
- single dropped line → `[[CMP]] source line N [[/CMP]]`
- dropped span N..M → `[[CMP]] source line N ~ source line M Omitted [[/CMP]]`
Kept lines stay verbatim (not wrapped). This is the comp-108 king's now-LEGAL Hard edge (README §1
merged 2026-07-07: "include a source line reference … so omitted lines remain locatable").

## Codex gate #1 trail
- **Round 1 → NO-GO** (`reports/codex_lean_v3_audit_round1.md`): 1 BLOCKING (checked-in
  `miner/README_prompting.md` was stale — pre-PR-merge — so the authoritative file didn't sanction
  the templates, even though the live fetch did) + 2 CONCERN (pin knob still present; block-relative
  coordinate system). Source-line accuracy + cache-stability PASS.
- **Fixes:** synced `miner/README_prompting.md` from upstream/main (now lists all 15 markers);
  removed the `SOMA_LEAN_PIN` knob entirely ("no pin" absolute); documented the block-relative
  coordinate convention (can't qualify the marker without breaking exact-template compliance).
- **Round 2 → GO** (`reports/codex_lean_v3_reaudit_GO.md`): all resolved; no regressions; ranges
  accurate; interior cache-stable; fail-open. Caveat: don't smoke with `SOMA_LEAN_RECENCY=0` if
  final-answer protection is required (first smoke uses default recency ON → fine).

## Verification matrix (all 10 required gates)
1. Rules gate PASS ✅ (against live fetch AND the synced checked-in file) — gate enhanced to validate
   the source-line templates (folds `source line <int>` → template; negative control FAILs correctly).
2. Codex audit GO ✅ (round 2).
3. Harness PASS ✅ — `test_lean_v3.py`, all 3 profiles + pin-removed assertion.
4. Real sidecar E2E loads ✅ — mounted in `soma-copilot-compression-service:latest`, 9.9–10.6×,
   markers all exact-template.
5. Protected lines survive ✅ — tracebacks/FAILED tests/imports kept.
6. Omitted source-line ranges accurate ✅ — full reconstruction (kept lines + ranges rebuild the
   original exactly), verified locally AND through the real sidecar; 1-based inclusive confirmed by Codex.
7. No partial-line output ✅ — whole original lines only.
8. No net-increase marker wrapping ✅ — `len(rendered) < len(text)` guard.
9. Interior messages byte-stable as history grows ✅ — only the final message is position-dependent.
10. Champion regression PASS ✅ — v2 (frozen) + cap32+pin champion still gate-PASS.

## Known tradeoffs (documented, to validate in the smoke)
- **Coordinate system:** "source line N" is 1-based within the content BLOCK, not the file's absolute
  line number (the template is fixed and can't be qualified). Whole-file-from-line-1 reads: equal;
  partial/numbered output: diverges. **#1 thing to watch in the smoke** — does the agent navigate/edit
  correctly with block-relative markers?
- **Budgets are targets, not hard caps** (marker overhead not pre-counted); net-reduction is the guarantee.
- **Recency guard on by default;** v3's locatable omissions may allow reducing/disabling it (lower break
  risk + better cache) — a `SOMA_LEAN_RECENCY` A/B, DEFERRED until after the first smoke is reviewed.

## First smoke result (2026-07-07, django__django-11099, v3 target, isolation on + modprobe shim)
Run: `outputs/lean-v3-smoke/`. **status=completed, no error; agent produced a 40-line patch
(has_changes=True).** Metadata confirms the miner was in-path: `compression_enabled=True`,
`network_isolation=True`, `compression_script_path=…upload_miner_lean_v3.py`,
image `soma-copilot-compression-service:latest`. token_usage: input 21,571 / output 4,372 /
cache_read 329,856 / cache_creation 0 (heavy provider caching — consistent with a cache-stable
prefix, not proof). Largest copilot-trajectory row ~26k chars (i.e. content DID exceed the 10k
target budget, so v3 had something to compress).
**ESTABLISHED:** v3 runs end-to-end in the real copilot loop and the agent still SOLVES with it
in-path (no break). **NOT ESTABLISHED from artifacts:** (a) the sidecar `[compression-service]
[messages.in/out]` firing markers — `sidecar_log_paths=None`, proxy/compression containers torn
down post-run; (b) the run-level token RATIO — needs a no-script baseline on the same instance;
(c) whether block-relative source-line markers reached + were navigated by the model (trajectory
shows copilot's PRE-compression view; compressed LLM inputs live only in the torn-down sidecar).
Firing itself is independently PROVEN by the direct sidecar E2E (this file, above).
**To close the gaps (one controlled re-run, USER-approved):** re-run with `SOMA_COPILOT_KEEP_STACK=true`,
then `docker logs` the compression container for the firing markers + the actual compressed inputs
(confirms markers + lets us eyeball block-relative behavior); AND a no-script control on the same
instance for the token baseline → the compression ratio.

## Next (gated on USER)
1. USER: `cp copilot-cli-container/.env.example → .env` (recipe: reports/local_eval_macos_recipe.md).
2. Claude runs the first smoke on **v3 target profile** (recency default ON), `modprobe` shim + isolation ON.
   Read: firing via `[compression-service][messages.in/out]`, run-level token ratio vs a no-script control,
   patch/solve status, and (critically) whether block-relative markers let the agent edit correctly.
3. NO profile A/B until the user reviews the first smoke result.
