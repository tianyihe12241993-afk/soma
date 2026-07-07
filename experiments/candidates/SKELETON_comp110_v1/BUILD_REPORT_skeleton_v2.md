# SKELETON v2 — consolidated comp-110 candidate (2026-07-07)

**Status: BUILT + CODEX GO (gate #1, after 1 NO-GO round). Frozen. NOT uploaded, NOT committed
(awaiting user approval). Held pending the in-flux score-formula change.**
File: `miner/cot_compression/upload_miner_skeleton_v2.py` sha256 `429d1b26…`; frozen at
`experiments/candidates/SKELETON_comp110_v1/frozen/skeleton_v2_GO_429d1b26.py`.

## What it is
The consolidated candidate the user asked for: SKELETON design (budgeted structural skeleton,
file-PATH priority within a hard budget) + LEAN v3 safety primitives + Codex fixes + PR#176-proofing +
all formula-dependent numbers exposed as knobs. Direction = team-confirmed stable intent: reduce
input/context tokens while preserving quality (explore hit-rate). See reports/comp110_scoring_rederivation.md.

## Verified (all gates except the deferred live smoke)
- **Rules gate:** GATE=PASS + FILE=PASS (emits only current-live §5.1 `[[CMP]] source line …` templates).
- **Harness** (`test_skeleton_v2.py`): ALL PASS ×3 profiles — contract, role safety, range accuracy,
  CRLF/lone-CR/terminal-newline byte-verbatim, budget-true-cap (oversized-head regression), cache-safety,
  determinism, net-reduction, quality-signal (paths), hostile shapes, no-`[[Omitted]]`-in-source.
- **Sidecar E2E** (real `soma-copilot-compression-service` image): loads, compresses, markers exact,
  CRLF preserved, path signal preserved, system untouched.
- **Regressions:** LEAN v3 / SKELETON v1 / cap32+pin champion still gate-PASS.
- **Codex gate #1:** round1 NO-GO (budget not a true cap; `[[Omitted]]` in comments) → both fixed →
  **round2 GO** (all items PASS). Trail: reports/codex_skeleton_v2_audit_round1.md + reports/codex_skeleton_v2_reaudit_GO.md.

## Knobs (formula-dependent — do NOT hard-tune to today's numbers)
`SOMA_SKEL_PROFILE` = safe/target/deep → (min_compress, head, tail, budget). `SOMA_SKEL_RECENCY` (final-msg
guard). Module globals MIN_COMPRESS/HEAD_LINES/TAIL_LINES/BUDGET are what the re-tune harness sweeps.

## Re-tune harness (`retune_harness.py`) — tune-and-ship in minutes
Parameterized on (input/cached/output weight, gate). At CURRENT constants (cached 1/10, gate 20%):
safe→deep→ceiling = 7.8→11.4% real, 100% .py paths kept, NONE clear 20% (confirms context-compression
can't qualify under the current formula). Demo at hypothetical (cached 1/3, gate 10%): target 15.7% /
deep 17.2% CLEAR. So when the watcher flags the formula change: run this with the new constants → read
the tuning → set the profile → smoke → decide. NOTE: measures the CONTEXT-savings component only
(fixed trajectory); output/turn effects need a live multi-run eval.

## Known / deferred
- **Does NOT clear the current 20% gate** — by design we hold (formula in flux). This is strategy, not a code defect (Codex agreed).
- **Live smoke deferred** until the formula lands + we re-tune (spends credits; tuning isn't final).
- **PR #176** (omission-tag syntax) unmerged → one-line switch documented in `_omission_marker` if it lands.

## Next (gated on formula change / user)
1. Watcher flags a scoring-formula change → re-derive constants (reports/comp110_scoring_rederivation.md method).
2. `retune_harness.py --input-weight … --cached-weight … --output-weight … --gate …` → pick the profile that clears with margin + best quality.
3. Local smoke (copilot stack) at that profile → confirm agent solves + explore hit-rate holds + real weighted savings.
4. Codex re-audit on final bytes → USER upload decision.
