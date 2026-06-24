# m18 build + validation report — size-gated adaptive-light (2026-06-24)

GATED EXPERIMENT. NOT submitted. m12 stays LIVE/unchanged. Paid A/B awaits explicit approval.

## 1. Source + sha
- File: `miner/cot_compression/upload_miner_m18.py`
- sha256: `0c69ba9a5d94d04ff6bd2340bdcb970859be4e36`
- Base: m12 = `upload_miner_m7_compliant.py` (sha 93d8d05f).

## 2. Diff summary vs m12 (purely additive — 1476 → 1656 lines)
ONLY removal from m12 = the docstring title line. Everything else is ADDED:
- **Docstring** explaining the single-variable change.
- **4 constants** (`ULTRALIGHT_MAX_MSGS=40`, `ULTRALIGHT_MAX_TOKENS=60_000`, `ULTRALIGHT_MAX_CUM=250_000`, `ULTRALIGHT_RESULT_CAP=40_000`) — the A/B-tunable gate knobs.
- **`compress_ultralight()`** — new function: compress_gently's EXACT dedup machinery + blind generous cap on huge results, NO extractive selection/reordering.
- **Gate** in `handle_assemble`: one `if` block that downgrades `harvest`→`ultralight` for clearly small/shallow contexts (conservative; any uncertainty → m12 harvest; monotonic passthrough→ultralight→harvest→rich).
- **Branch** in `handle_assemble`: one `elif mode == "ultralight"` (mirrors the rich branch's orphan-guard + empty-fallback + loop-guard exactly).
No existing m12 function was modified. `compress_gently` / `compress_structurally` (rich + harvest = the Hard moat) are byte-for-byte m12.

## 3. Compliance
`scripts/check_prompt_compliance.py` → **PASS** ("only allowed CMP/BLOCK markers + allowed loop-reason strings"). No LLM/API call, no task-id/benchmark/category logic (gates on raw structural size only), no behavior steering, no private markers, no STOP-NOW language.

## 4. Unit / offline-smoke results (`/tmp/test_m18_unit.py`) — ALL PASS
- **small/shallow context** (≈29 msgs, >3k tok): m12 mode=`harvest`, **m18 mode=`ultralight`** ✓ (gate fires correctly)
- **large/deep context** (121 msgs): m12=`rich`, **m18 output BYTE-IDENTICAL to m12** (5046 == 5046 tok) ✓ (Hard moat protected)
- **no inflation**: ultralight 3862→2107 tok (dedup savings; out ≤ raw) ✓ — savings-gate has headroom
- **dedup works**: 7 `[[BLOCK N]]` back-references emitted in ultralight ✓
- **markers compliant**: only CMP/BLOCK in output ✓

## 5. Is large-context output byte-identical to m12?
**YES for DEEP contexts** (proven: identical output + identical estimatedTokens). **Important nuance:** a hard task's *shallow EARLY turns* (small context, depth<40) DO get ultralight before the task deepens; once it escalates (depth/tokens/cum cross thresholds) it sticks to m12's rich/harvest. So m18 is byte-identical to m12 on the DEEP portion, but lighter on a hard task's early-small phase (then m12-identical). Whether that transient early-lightness perturbs hard outcomes is exactly what the **large/hard controls** in the A/B test.

## 6. Proposed A/B (DO NOT RUN until approved)
⚠️ **MAXJOBS override:** the spec says MAXJOBS=8, but today's incident proved that's unsafe on this Mac — MAXJOBS=8 CPU-stalls (load 15) and **MAXJOBS=4 OOM-crashed Docker**. Only **MAXJOBS=3** is proven safe (EXP-1b 4h/54-of-54). Using 3.

- Profiles: `m12 m18` · RUNS=5 · MAXJOBS=3 · same OpenRouter key/account/window.
- **Small/easy targets (signal):** django-14122, sympy-15349, django-11740, django-13810, django-12039, django-12050
- **Large/hard controls (no-regression, m12-strong + large baseline):** sympy-18698 (3.6M,+1.31), sympy-24661 (2.5M,+2.54), django-13158 (1.9M,+2.50), django-14017 (1.85M,+2.56)
- 10 tasks × 2 profiles × 5 runs = **100 solves ≈ 8–10h at MAXJOBS=3.** (Trim option: drop to 3 controls / RUNS=4 if too long.)

Command:
```
MAXJOBS=3 RUNS=5 STAGGER=10 PROFILES="m12 m18" \
TASKS="django__django-14122:Pass sympy__sympy-15349:Pass django__django-11740:Pass django__django-13810:Pass django__django-12039:Pass django__django-12050:Pass sympy__sympy-18698:Flip sympy__sympy-24661:Pass django__django-13158:Pass django__django-14017:Flip" \
bash experiments/candidates/H1M_m7_deeper_safe_v1/run_batch_eval_parallel.sh > /tmp/soma_m18ab.log 2>&1
```

## 7. Metrics + accept/reject (per spec)
- PRIMARY: pass-pass break count, # −4 runs, resolved/5 per task (on the small targets).
- SECONDARY: mean total tokens, calls/steps, cache-hit, weighted-savings-gate safety, ratio, large/hard regression.
- ACCEPT (promising): small-target break count clearly lower than m12 AND no large/hard regression AND tokens don't explode AND cache not materially worse AND savings gate safe AND estimated score delta positive.
- REJECT: breaks equal/worse, OR any large/hard regression, OR tokens/calls rise materially, OR cache drops, OR m17-style wander, OR improvement is noise-level.

## 8. Recommendation
**RUN the A/B** (after approval). m18 passed every offline gate, is purely additive over m12, protects the Hard moat by construction (deep = byte-identical), and is the only lever with real evidence behind it (the king's real Easy/Medium data). Watch per-task `mode` in the logs — if ultralight never fires on the small targets, the thresholds are too conservative; raise `ULTRALIGHT_MAX_MSGS/TOKENS` and re-run (cheap to retune). Hold m12 LIVE throughout; nothing submitted regardless of outcome.
