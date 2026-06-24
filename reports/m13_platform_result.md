# m13 (= m12.1b_run_stability) PLATFORM result — the design is FALSIFIED

_Scored 2026-06-23 on comp 108. Hotkey 5CApy5s5 (fresh; m12 untouched). Solution = upload_miner_m12_1b.py
(sha 90460bb9). Scrape: data/raw/platform_results/2026-06-23/125419_swe_runs.json (50 tasks × 5 runs)._

## Headline: m12.1b is WORSE on the platform, and inverts the local read
| | total | Easy | Medium | Hard |
|---|---|---|---|---|
| **m12 (live)** | **0.768** | 0.412 | 0.953 | 0.919 |
| **m13 (m12.1b)** | **0.571** | **0.561** ↑ | **0.718** ↓ | **0.434** ↓↓ |
| Δ | **−0.197** | **+0.149** | **−0.236** | **−0.486** |

**Hard COLLAPSED (0.919→0.434) and Medium dropped (0.953→0.718); only Easy improved.** Net −0.197.

## Mechanism (per-task head-to-head, 45 common tasks)
- baseline-PASS tasks (n=29): m12 +18.4 → m13 **+13.6 (−4.8)** — m13 BREAKS more pass-pass tasks.
- baseline-fail/flip tasks (n=16): m12 +14.9 → m13 **+9.7 (−5.1)** — m13 FLIPS less / loses flip consistency.
- It's a **redistribution toward the mean**: m13 stabilized some low/break-prone tasks UP (t270 2/5→4/5 +2.17,
  t307 3/5→5/5 +1.93, t267/269/295/298/313 up) but **broke working high-value tasks DOWN** — t315 **3/5→0/5
  (−3.13)**, t290 flip **3/5→0/5 (−2.49)**, t279 5/5→3/5 (−1.94), t303 flip 5/5→3/5, t293 4/5→2/5. The breaks
  outweigh the fixes.
- Avg compression barely moved (m12 1.75x → m13 1.66x; BOTH 0 tasks >8x at task level), so this is NOT "m13
  compressed far less." The cap/never-inflate/routing changes **altered the context** in ways that helped the
  already-weak tasks and hurt the strong ones — net-negative where m12 was winning (H+M).

## What this falsifies / proves
1. **The run-variance-from-over-compression thesis is FALSIFIED.** m12's aggressive harvest is **net-POSITIVE
   on Hard/Medium even with per-run variance**; capping/gentling it (the "cure") was worse than the disease.
   The per-run 10-20x "outliers" were largely a SYMPTOM of already-failing short runs (the confound flagged in
   m12_run_variance_analysis.md §D), not the cause — so capping them didn't recover the failures, it just
   degraded the runs that were working.
2. **Local eval MISLED us** — it showed HardFragile 6→9 (+3) on 4 cherry tasks, but the FULL Hard category
   collapsed on the platform. 5-runs × 10-tasks local cannot represent 50-task platform scoring. Submitting to
   a fresh hotkey was the right call (the user's instinct); local would never have caught this.
3. **The ONE real win: never-inflate / gentleness lifts EASY (+0.149).** Easy 0.412→0.561 is the extractable
   signal — short Easy tasks benefit from passthrough-instead-of-tiny-inflated-harvest + gentler handling.
4. **No harm done:** m13 is a separate hotkey at 0.571; **m12 stays live at 0.768, #2, review-PASS.**

## Decision + next
- **REJECT m12.1b's cap + gentler-routing design.** Do NOT pursue the aggressiveness cap / harvest→rich
  fallback — the platform says it trades away the H+M harvest that is our edge.
- **m12 remains BEST and LIVE.** Keep it.
- **Extract only the Easy win:** next candidate = **m12 + never-inflate ONLY** (no cap, no routing changes,
  no determinism rewrite) — isolate whether never-inflate alone lifts Easy (~0.41→~0.56) WITHOUT touching the
  H+M harvest. Change ONE thing. **Validate on the PLATFORM (fresh hotkey), not just local** — local is now
  proven unreliable for H+M. (Even "byte-identical-on-Medium-locally" diverged on the platform.)
- Open question for that test: is the Easy lift from never-inflate specifically, or from the routing/cap
  side-effects? m12+never-inflate-only isolates it.
- Reframe the strategy: our edge IS the aggressive harvest on H+M (don't soften it). Easy is the only place
  gentleness pays. So grow H+M by KEEPING m12's harvest and finding H/M-specific gains (not global gentling).
