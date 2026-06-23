# Prompting policy (next competition) + our compliance gap
_Source: DendriteHQ/SOMA `miner/README_prompting.md` (origin/main 82dfc28) + Discord moderation thread, 2026-06-22._

## Why the top of comp 107 failed review (official, from SOMA mods)
| hotkey | rival | reason |
|---|---|---|
| 5EkiFXSR | t1 (1.460) | **SWE hints injection** |
| 5E7hCCzj | t2 (1.436) | **SWE hints injection** |
| 5FbqgypX | t3 (1.415) | **SWE hints injection** |
| 5ERdwbn5 | t7 (1.263) | **SWE hints injection** |
| 5DhHqmB1 | t4 (1.410) | **Prompt modifications that did not fit competition rules** |
| 5GEUZcud | t5 (1.355) | **Prompt modifications that did not fit competition rules** |

"These changes introduced behavior-steering prompt content outside the allowed scope." Community read
(danylo, credible): the winners used **force-stop to problem-target** — agents finishing in 3–4 steps by
detecting when the first patch matched the ground-truth patch (only possible by gaming the known PSET).
Mods' ruling: **force-stop WAS allowed in the just-finished round (so those scores stand), but is BANNED
next round; step-counting is buggy (0-step/300k-token runs exist).** → They failed for PROMPT-SIDE CHEATING
(hints injection, behavior-steering, problem-targeting), **NOT compression depth.** Our compression strategy
is the intended focus and is vindicated; m7 passed review = legitimate.

## The new rules (next competition) — ONLY two categories allowed
1. **Compression markers** — metadata wrappers only. MUST preserve instruction meaning, order, all
   requirements, tool/safety/role policy, and output contract. No rewriting/adding/removing/reordering.
2. **Loop-detection guards** — trigger only on objective repeated/no-progress; fail fast with a clear loop
   reason; MUST NOT change strategy/reasoning/tool policy, scoring, or non-loop successful behavior, and MUST
   NOT "force shortcuts to reduce token usage."

Everything else is disallowed. New strings must be discussed publicly first.

### Allowed EXACT strings (the whole list)
Markers: `Compressed text starts here` · `Compressed text ends here` · `[[CMP]]` · `[[/CMP]]` ·
`[[BLOCK X]]` · `[[/BLOCK X]]` · `Same response as in [[BLOCK X]].`
Loop reasons: `loop_detected: repeated assistant response` · `loop_detected: repeated tool call signature`

## Our compliance gap (m7 / H1M / H3 ALL currently NON-COMPLIANT on the prompt side)
The COMPRESSION ALGORITHM (harvest/rich/H3 cache-stable masking + dedup + drop/truncate) is **compliant and
is exactly the intended focus.** What must change for the next round:
1. **Remove the coach entirely** (`append_coach`/`build_coach_text`, appended every harvest+rich round). It
   contains **force-stop** ("If the tests pass, stop and return your final answer"; governor "STOP NOW … do
   not explore further") and a **behavior-steering loop nudge** ("…change your approach"). Both are banned:
   force-stop is out, and loop guards may not change strategy. → DELETE.
2. **Switch markers** from `[SOMA COMPRESSED HISTORY]` / `[/SOMA COMPRESSED HISTORY]` / `[SOMA CONTEXT NOTE]`
   (not on the allowed list) → `[[CMP]]` / `[[/CMP]]` (or `Compressed text starts/ends here`). Use
   `[[BLOCK X]]` + `Same response as in [[BLOCK X]].` for the near-duplicate / superseded-view dedup.
3. **Loop detection (if kept):** emit ONLY the two allowed reason strings as a fail-fast loop reason — no
   "change your approach", no steering, no task restatement.
4. Keep harvest/rich/cache-stable compression unchanged (markers aside). It's the legitimate lever.

## Action: next-round baseline = m7 compression, COACH-FREE, published markers
- m7 is now top-tier and review-PASSING (#2 overall, Medium ≈tie) — the right base.
- Stripping the coach/force-stop likely costs little (v12's forced-stop FAILED to improve Easy; the score is
  driven by compression, not the coach).
- Build a compliant variant (no coach, `[[CMP]]` markers, allowed loop reasons only), re-validate on the eval,
  and compare to m7. For ANY new marker/string we want, post in the public channel first.
- The H3 cache-stable masking maps cleanly onto `[[CMP]]`/`Same response as in [[BLOCK X]]` — it's the
  compliant, intended-focus direction. Just drop its inherited coach.

## DONE — H4_compliant_cache_stable built + offline-green (2026-06-22)
The compliant candidate now exists: `experiments/candidates/H4_compliant_cache_stable/h4_miner.py` (copy of
H3 with the entire coach/force-stop/steering removed; markers switched to `[[CMP]]`/`[[/CMP]]` + `[[BLOCK N]]`
+ `Same response as in [[BLOCK N]].`; loop-detection emits only the 2 allowed reason strings). Engine kept
intact (cache-stable harvest, frozen head, masking, superseded-view elision, sticky keep-list, fragile guard,
rich, load-bearing allowlist, pairing). New scanner **`scripts/check_prompt_compliance.py`** (fails on the
banned strings + non-allowed markers/loop-reasons): **PASS on H4, FAIL on H3 + m7**. Offline 12/12 PASS;
**+5.69% compression vs H3**, **prefix-stability identical** (no regression), 0 protection regressions.
Real-eval is queued for AFTER the running H3 eval (see NEXT_ACTIONS). Report:
`experiments/reports/H4_compliant_cache_stable.md`; machine: `data/latest/h4_compliance_results.json`.
