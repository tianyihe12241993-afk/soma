# Codex pre-upload audit — `upload_miner_skel_recoff_v1.py` (recency-off / fresh-input compression)

_2026-07-08. Independent read-only Codex audit (gate #1). Scratchpad task b5h8kugb4. Candidate = skeleton_v2
(previously Codex-GO) with the ONE change `_RECENCY = False` (compress the fresh/final message too — the
weight-1.0 input). Rationale: reports/comp110_local_eval_findings.md + state/CURRENT.md (fresh-input reframe)._

## Verdict: **GO-WITH-CHANGES**  → change applied (see bottom) → upload-ready (USER-run).

## Mandate results
1. **Compliance — PASS.** Emits ONLY `[[CMP]] source line N [[/CMP]]` and `[[CMP]] source line N ~ source line M Omitted [[/CMP]]` (skel_recoff_v1.py:90). No marker-injected text, no steering, no task/category/benchmark awareness, no network/LLM/subprocess, stdlib only (os/re/typing). Kept lines are whole-original byte-verbatim (splitlines(keepends=True); out.append(raw[i]) at :109/:149).
2. **Diff integrity — PASS.** Only code change vs skeleton_v2 is `_RECENCY` env-default-on → forced `False` (+2 comments) at :62. Pre-final messages byte-identical to skeleton_v2; only the final message changes from verbatim to the same skeleton form it would have as an interior message.
3. **Break-safety — CONCERN / change requested.** With recency off, the FRESH tool result the agent is about to act on is compressed. Under `target` (budget 550) a synthetic 33k read → ~760 chars. The source-line marker makes omitted spans locatable but does NOT preserve the code needed to patch and cannot instruct a re-read → can plausibly cause wrong patches or extra read loops. The 3/3 local recoff patches completed but do NOT prove correctness (no local grading). ⇒ `target=550` too aggressive on the freshest read under a "prove safe" gate.
4. **Cache-safety — PASS.** Recency-off makes compression a pure, position-independent function of each message's own content → emitted prefix byte-stable across turns; removes the old final-verbatim→compressed transition. (Confirms the fresh-insight cache-stability claim.)
5. **Robustness — PASS.** Deterministic; input not mutated; malformed/None/list-content shapes don't crash; top-level exception → original messages; non-list input → [].

## Codex recommendation
"Do not upload this exact `target` default first. Change the code default to a gentler recency-off profile,
at least `safe` (budget 900), OR create a first-test variant with a larger fresh-result budget. Recency-off
is directionally justified for weighted input savings, but `target=550` is too aggressive for the freshest
read under a prove-safe pre-upload gate."

## CHANGE APPLIED (Claude, per Codex GO-WITH-CHANGES — the "larger fresh-result budget" option)
Added a **`gentle`** profile `(min_compress 2000, head 30, tail 15, budget 4000)` and set it as the code
DEFAULT (env does not reach the container, so the default is what runs). Effect: reads <2000 chars pass
through untouched; big reads kept to ~4–5k chars of signal (verified: 12.5k→5.2k, 59% cut, **41% preserved**
vs target's ~4%) → correctness-first for the first platform test while still cutting the fresh input
meaningfully. Re-verified: compliance GATE+FILE PASS, deterministic, budget-capped, cache-stable.

## Status
Codex compliance/cache/robustness = PASS; the single requested change (gentler fresh-read budget) is applied
and was pre-endorsed by Codex. **Upload-ready for a USER-run first platform test on a SPARE hotkey.** This is
a platform-TRUTH test: local cannot measure the weighted savings (step variance) or correctness (no local
grading) — only the platform (fixed baseline, 15 runs, real grading) can. Read at `status=scored`.
