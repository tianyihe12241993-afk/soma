# H3_cache_stable_depth_v1 — cache-stable HARVEST (RESEARCH; DO NOT SUBMIT)

Offline research candidate. Derivative of `H1M_m7_deeper_safe_v1`. **Not submitted.**

## The problem this fixes

A compression miner runs inside the coding agent (OpenClaw + qwen3-coder). Every agent
step it returns a compressed message list fed back to the model. Reward per passed task is
roughly `1 + 0.5*ln(tokens_baseline / tokens_compressed)`; a compression-induced FAIL is
worth about **−4**. The provider **caches the prompt PREFIX** (we see large `cache_read`
counts), so **any byte change to an early message invalidates the cache from that point on
→ it costs MORE tokens, not fewer.**

H1M's HARVEST path realized only **~+8%** compression in a real eval because it:

- **rebuilds a digest and re-truncates the whole history every turn**, and
- **injects a growing digest into the FIRST user message** (`inject_digest`).

Both mutate the cached prefix **every turn → cache miss every turn**, eating the savings.

## What changed vs H1M@deep

Only the **HARVEST** path is re-architected to be **cache-stable**. The **PASSTHROUGH**
path and the **RICH** path (`compress_gently`) are kept **intact**, and every protection
is preserved (load-bearing content, `ERROR_MARKERS`, active paths, recent-intact tail,
orphan/pairing guard, fragile-guard routing to rich).

New harvest path = `compress_cache_stable` (replaces `compress_structurally`):

| Aspect | H1M@deep HARVEST | H3 HARVEST (cache-stable) |
|---|---|---|
| First user message | digest INJECTED + GROWN every turn | **BYTE-IDENTICAL, frozen** (no digest) |
| Old-message compression | function of **global state + position** (re-truncated every turn) | **pure function of the message's OWN content** |
| Tool results | oldest **dropped** (digest left behind) | **masked in place** (body→marker), never dropped |
| Repeated file reads | re-truncated | **superseded earlier views elided** to a 1-line ref; latest kept |
| Dropping | routine (digest replaces) | **last resort**, only past a hard cap |
| Prefix across turns | mutates → cache miss every turn | **byte-stable** → cache hit (only the boundary msg + tail change) |

Core invariant: an old message is compressed as a **pure function of its own content**
plus append-monotonic, position-independent trajectory facts (the set of later-read paths,
the global sticky keep-list). As the trajectory grows by appending, an already-old message
masks to the **same bytes every turn**, so the cached prefix only changes at the **one**
message that just crossed the recent-tail boundary.

### Masking (the −4 defense)
A stale tool-result body is replaced by `mask_tool_body(...)`, a deterministic
content-derived marker that **preserves**: the command echo, exit/status, failing-test
names, assertion lines, the traceback tail, file paths, and line numbers (extracted via the
reused `ERROR_MARKERS` / `TEST_LINE_PATTERN` / `PATH_PATTERN` / `is_error_bearing` helpers,
plus `[old output elided: N lines]`). The message and its `toolCallId` are kept, so
tool_call ↔ tool_result pairing is never broken.

### Superseded file-view elision
If the same path is read/shown again later, earlier full views collapse to
`[old file view elided: path=..., N lines, superseded by later read]`; the LATEST view stays
high-fidelity. (Superseded status flips at most once, when the later read appears — the one
acceptable boundary change.)

### Sticky keep-list
Load-bearing items (active file paths, failing-test names, assertion lines, traceback tails,
current patch/diff) are always preserved regardless of profile depth.

### Fragile-guard hardening (general signals only — NO task-id logic)
H1M rejected a fragile task (django-14493) on a new broken baseline the baseline kept. H3
makes borderline transcripts fall back to the RICH (m7-like) path **earlier** via
`fragile_transcript(...)`, which adds to H1M's recent-error count:
- **error density** in a wider recent window (`ERROR_DENSITY_WINDOW`),
- **oscillating failures** — the SAME failing test/assertion recurring across rounds
  (`oscillating_failures`), and
- **large + still-failing** transcripts (deep and still error-bearing at the tail).

Verified: on a borderline oscillating-failure transcript (same failing test recurring, only
2 errors in the recent-4 window) H1M@deep **stays in harvest** while H3 **routes to rich**.

### New metadata (offline inspection, in `baseMiner`)
`prefixHashBefore`, `prefixHashAfter`, `stablePrefixBytes`, `pruneEvents`,
`maskedToolResults`, `elidedFileViews` — added alongside all existing fields.

## Profiles (env `H3_PROFILE`, default `cache_safe`)

Control how aggressively masked bodies / elided views are truncated (deeper = shorter kept
head/tail). Kept-bytes are **monotonic: ultra ⊆ king ⊆ safe**. Read from `os.environ` at
import (the real driver bakes the value into the file).

| field | `cache_safe` | `cache_king` | `cache_ultra` |
|---|---|---|---|
| `MASK_HEAD` (stale body head bytes) | 520 | 360 | 240 |
| `MASK_TAIL` (stale body tail bytes) | 220 | 150 | 100 |
| `PROTECTED_MASK_HEAD` (load-bearing body head) | 1400 | 900 | 600 |
| `PROTECTED_MASK_TAIL` (load-bearing body tail) | 1200 | 800 | 520 |
| `STALE_CAP` | 9000 | 6500 | 4500 |
| `ASSIST_HEAD` / `ASSIST_TAIL` | 700 / 220 | 520 / 170 | 360 / 120 |
| `ERROR_GUARD_MIN_HITS` (lower = bail to rich earlier) | 3 | 2 | 2 |

- `cache_safe` ≈ h1m@deep depth, but cache-stable.
- `cache_king` ≈ king-like deeper truncation, still cache-stable + protections intact.
- `cache_ultra` = over-push to locate the break boundary; **not a real candidate**.

Global harvest knobs: `HARD_CAP_TOKENS=60_000` (prune only past this), `MASK_BODY_MAX=1_400`
(smaller bodies left intact), `SUPERSEDED_VIEW_MIN_CHARS=400`.

## Offline test results

Run: `python3 h3_eval.py` (stdlib only; no network/Docker). Latest run: **10/10 PASS**.

```
1.  profile bake + depth monotonic            PASS  tokens safe=10479 king=9555 ultra=8877
2.  tool pairing integrity (all trajs)        PASS  ok all trajectories/profiles
3.  first user msg byte-identical             PASS  byte_identical=True no_injected_digest=True
4.  failing-test/assert/traceback survive     PASS  failing_test/assertion/traceback all kept
5.  superseded views elided, latest kept      PASS  elided_ref=True latest_kept=True elided=9
6.  tool bodies masked in place               PASS  ids_kept=True masked=14 prune=0 marker=True
7.  patch/diff preserved                      PASS  patch_hunk=True
8.  PREFIX STABILITY (headline)               PASS  byte-stable prefix across 4 turns; b=[30,32,34,36]
9.  prune events minimized                    PASS  small_prune=0 forced_prune>0 pairing_ok=True
10. compression monotonic w/ depth            PASS  tokens safe=12552 king=11052 ultra=9947
```

Cross-turn evidence (the headline): across 4 successive append turns the H3 compressed
output's frozen head + already-compressed old region stay **byte-identical**; only the
boundary message + recent tail change. End-to-end through the subprocess + state path, turn
2 masked only **1** message (the one that crossed the tail) vs turn 1's 14 — the cache win.
For contrast, H1M's `compress_structurally` mutates the first user message **every** turn.

## Risks / assumptions

- **Offline-only**: real platform pass/fail and the −4 rate are `PENDING_EVAL` (need the
  SOMA SWE-bench harness: Docker + agent + OpenRouter). Structural safety here is a strong
  pass-safety proxy, not a guarantee.
- **Prefix-cache model**: assumes the provider caches a contiguous prefix and that
  byte-identical leading messages produce a cache hit. Matches the observed `cache_read`
  behavior but is not independently confirmed here.
- **Superseded-view heuristic** keys on the tool-call path arg / first body path; an
  unusual tool that re-reads a path without a recognizable path arg would simply not be
  elided (safe failure — it gets masked instead).
- **`cache_ultra` is a probe**, not a shipping profile.
- No task-id logic anywhere; all routing/depth decisions are general transcript signals.

## Files
- `h3_miner.py` — the miner. `run_event` / `cli_main` / plugin entry contract identical to
  H1M, so the driver can run it as `base_miner.py`.
- `h3_eval.py` — the offline harness (stdlib only).
- `README.md` — this file.
