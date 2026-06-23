# H4_compliant_cache_stable — next-round RULE-COMPLIANT compression miner

**Status:** offline-green. Ready to queue for real eval **after** the live H3 eval finishes.
**Base:** copied from `H3_cache_stable_depth_v1/h3_miner.py` (compression engine kept intact);
all prompt-side steering removed for next-round compliance with `miner/README_prompting.md`.
**Stdlib only.** `run_event` / `cli_main` / plugin entry contract identical to H3/H1M.

Files (all written this session; **H3 miner, the eval scripts, base_miner.py, docker were NOT touched**):
- `experiments/candidates/H4_compliant_cache_stable/h4_miner.py` — the miner
- `experiments/candidates/H4_compliant_cache_stable/h4_eval.py` — offline harness + H3-vs-H4 comparison
- `scripts/check_prompt_compliance.py` — static policy scanner
- `data/latest/h4_compliance_results.json` — machine results

---

## 1. What was removed from H3 (all prompt-side, now illegal)

- **The entire coach** — `append_coach`, `build_coach_text`, `strip_coach`, `is_coach_message`,
  and their calls in `handle_assemble`. This injected a `[SOMA CONTEXT NOTE]` user message that
  told the agent to conclude / change approach.
- **The force-stop governor** — `GOVERNOR_TOKENS` / `GOVERNOR_TARGET_TOKENS` and the
  "stop and return…", "STOP NOW", "do not explore further" governor text.
- **All behavior-steering text** — "change your approach", "solution is complete", "if the tests
  pass, stop and return…", etc.
- **All custom/private markers** — `[SOMA COMPRESSED HISTORY]` (the injected first-message digest),
  `[SOMA CONTEXT NOTE]`, and the prose markers `[old output elided: N lines]`,
  `[soma key lines: …]`, `[soma: identical/near-identical …]`, `[old file view elided: …]`,
  `[soma: trimmed N chars]`.
- **Dead helpers + constants** removed with them: `compress_structurally` (H3's drop-with-digest
  path, never routed in H3 either), `inject_digest`, `extract_existing_digest`, `_split_digest`,
  `extract_issue_text`, `extract_test_status`, `describe_tool_call`, and all `DIGEST_*` /
  `COACH_*` / `GOVERNOR_*` / `TEST_STATUS_*` / `ISSUE_REINJECT_CLIP` constants.

**Kept intact (the compression engine):** cache-stable harvest (frozen head / stable prefix),
tool-result body masking, superseded file-view elision, sticky keep-list, fragile guard, rich
fallback (`compress_gently`), load-bearing allowlist, active-file preservation,
failing-test/assertion/traceback-tail preservation, tool-call/tool-result pairing integrity,
passthrough mode, orphan guard. Masking still **preserves** all load-bearing content; the allowed
markers merely wrap it.

---

## 2. What markers remain (the exact allowed strings + where)

Only the strings in `README_prompting.md §5.1/§5.2` are emitted:

| Allowed string | Where used in H4 |
|---|---|
| `[[CMP]]` / `[[/CMP]]` (aliased once to `Compressed text starts here` / `Compressed text ends here`) | `mask_tool_body()` wraps the elided middle of a stale tool-result body; `truncate_text()` wraps a truncated assistant/tool region. Kept head/tail sit **outside** the markers; load-bearing pinned lines (failing tests, assertions, traceback frames, file:line, diff) are surfaced **inside** them. Empty/fully-elided → `[[CMP]][[/CMP]]`. |
| `[[BLOCK N]]` / `[[/BLOCK N]]` (N = integer) | Labels the **surviving (latest)** copy of a deduped/superseded view, in `compress_gently()` (exact + near duplicates) and `compress_cache_stable()` (superseded file views). The body between the markers is byte-identical to the original. |
| `Same response as in [[BLOCK N]].` | Replaces the **earlier** identical/superseded copy (built by `same_response_ref()`); message envelope + `tool_call_id` are always kept — only the body text changes. |
| `loop_detected: repeated assistant response` / `loop_detected: repeated tool call signature` | The **only** text the loop guard ever emits (`detect_loop_reason()` / `append_loop_guard()`). |

No other bracketed `[[…]]` markers, no invented hints, no task-ID logic, no SWE-specific steering.

---

## 3. Force-stop / behavior-steering text remaining: **NONE** (scanner-proven)

`scripts/check_prompt_compliance.py` statically scans the source for `STOP NOW`, `stop and return`,
`do not explore`, `change your approach`, `solution is complete`, `tests pass, stop`, `[SOMA`,
`CONTEXT NOTE`, `COMPRESSED HISTORY`, any bracketed `[[…]]` marker outside the allowed set, and any
`loop_detected:` reason outside the allowed set. **H4 passes (exit 0).** The eval harness also scans
every fixture's *output* for the same forbidden strings (test 11) — all clean.

---

## 4. Scanner result (sanity-checked against H3 and m7)

| Target | Verdict | Exit |
|---|---|---|
| `h4_miner.py` | **PASS** — compliant | 0 |
| `h3_miner.py` | **FAIL** — coach/governor + `[SOMA…` markers present | 1 |
| `h1m_miner.py` (m7) | **FAIL** — coach/governor + `[SOMA…` markers present | 1 |

The scanner accepts `[[BLOCK X]]` with a numeric/placeholder slot; the private-marker checks are
case-sensitive (the real H3/m7 markers are exact-cased) so ordinary prose never false-positives.

---

## 5. Offline test table (h4_eval.py — all PASS, exit 0)

```
1  task instruction preserved byte-identical          PASS
2  failing-test names preserved                       PASS
3  assertion lines preserved                          PASS
4  traceback tail preserved                           PASS
5  file paths preserved                               PASS
6  active patch/diff preserved                        PASS
7  tool-call/tool-result pairing integrity            PASS
8  tool-result bodies masked in place                 PASS
9  ONLY allowed markers in output                     PASS
10 ONLY allowed loop-reason strings in output         PASS
11 NO force-stop/steering (output + source scan)      PASS
12 prefix/cache-stability >= H3                        PASS
   sanity: scanner FAILS on H3 (coach present)        PASS
   all fixtures ran ok                                PASS
   loop guard fired on synth-loop w/ allowed reason   PASS
```

Fixtures: the 5 real sample transcripts + 4 synthetics (clean-harvest x2, error-dense→rich, no-progress loop).
Each fixture runs on a **clean session** (unique sessionId) so the sticky passthrough→harvest→rich
mode ratchet never leaks between fixtures.

---

## 6. H3-vs-H4 compression (same fixtures; ratio = tokens_in / tokens_out, higher = more compression)

| case | H4 mode | ratio H3 | ratio H4 | Δ% | protection regression |
|---|---|---|---|---|---|
| sample-1 | harvest | 1.146 | 1.159 | +1.1% | 0 |
| sample-2 | harvest | 1.213 | 1.249 | +2.9% | 0 |
| sample-3 | harvest | 1.595 | 1.632 | +2.3% | 0 |
| sample-4 | rich | 1.000 | 1.003 | +0.3% | 0 |
| sample-5 | harvest | 1.634 | 1.763 | +7.9% | 0 |
| synth-harvest-clean | harvest | 6.191 | 7.121 | +15.0% | 0 |
| synth-harvest-big | harvest | 7.369 | 8.704 | +18.1% | 0 |
| synth-errdense-rich | rich | 0.996 | 0.999 | +0.3% | 0 |
| synth-loop | harvest | 1.504 | 1.552 | +3.2% | 0 |

**Mean Δ = +5.69%** (H4 compresses *slightly more* than H3) and **zero protection regression** on
every fixture. Reason: H4 removed the appended coach/governor message and replaced H3's verbose
private markers (`[old output elided: N lines]`, `[old file view elided: path=…, superseded…]`,
`[soma: identical to a later tool result …]`) with the compact allowed markers
(`[[CMP]][[/CMP]]`, `Same response as in [[BLOCK N]].`) — fewer bytes for the same structure.

---

## 7. Prefix / cache-stability (across appended turns, on the same growing trajectory)

| | stable transitions | total | stable ratio | mean boundary |
|---|---|---|---|---|
| H3 | 4 | 51 | 0.0784 | 22.69 |
| H4 | 4 | 51 | 0.0784 | 22.69 |

**H4 ≥ H3 (identical).** Both share the same `prefix_boundary` / `RICH_INTACT_MSGS`, and H4's
masking is — like H3's — a **pure function of each message's own content**. A targeted check
confirms an already-old message masks to **byte-identical** output across two appended turns, and
the prior turn's prefix region is a byte-prefix of the next turn's output — the core cache
invariant is preserved. (The low absolute stable-ratio is an artifact of a single steadily-growing
synthetic path where every turn shifts the tail boundary; it is identical for both miners, so there
is no regression.)

---

## Readiness

- `python -c "import ast; ast.parse(...)"` on `h4_miner.py`: **OK**. `py_compile` on all three
  deliverables: **OK**.
- `h4_eval.py`: **exit 0** (all tests pass). `check_prompt_compliance.py` on H4: **exit 0**.
- Compliance: only the allowed markers + allowed loop-reason strings are emitted; no force-stop /
  behavior-steering text anywhere (scanner-proven, source + output).
- Compression and cache-stability are **≥ H3** with **no protection regression**.

**H4 is ready to queue for a real SWE-bench eval after the live H3 run finishes.** It must not be
swapped into `base_miner.py` while the H3 eval is in flight. Offline tests are a structural / safety
proxy; the real platform pass/fail, negative-run rate and broke-baseline remain **PENDING_EVAL**.
