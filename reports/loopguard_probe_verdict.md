# Loop-detection threshold sweep — OFFLINE PROBE VERDICT

_Date: 2026-06-25. Offline, read-only. The last compliant NON-content lever (the loop guard appends only an
allowed reason-string; it never changes compression, so Hard 0.919 is byte-identical regardless)._

## VERDICT: **NO-GO (no-op).** The loop guard is already saturated on the addressable population, not under-tuned.

## Probe (128 real comp-108 m12 runs; `/tmp/loopguard_probe.py`)
Parameterized per-turn `detect_loop_reason` sweep over (LOOP_THRESHOLD, LOOP_WINDOW).

**Firing rate (% of runs the guard fires ≥once):**
```
  3/12 (m12 current): 67.2% tool-call   0.0% assistant
  2/12:               90.6%             0.0%
  2/8:                90.6%             0.0%
  4/12:               43.8%             0.0%
```
**Wander proxy (12 longest runs = most break/wander-prone):** ALL 12 already fire at the current 3/12 (tool-call
recurrence 4–12, well past 3). 2/12 catches the same set — no new coverage on the wander population.

**Addressable population (max tool-call recurrence, window 12):** recur 1 = 9%, recur 2 = 23%, recur 3+ = 67%.
- Current 3/12 already catches 67%. A 2/12 would NEWLY catch only the 23% that recur exactly twice.

## Why tuning can't help (mechanism)
1. **Not under-firing.** The guard already fires on 67% of runs and on EVERY long/wander run. The wander-type
   breaks are already receiving the compliant reason-string — and they still break on the platform. Catching the
   loop is a NECESSARY-not-sufficient condition; here it's already met and the break happens anyway, so emitting it
   more/earlier addresses nothing. (The "does the reason-string change behavior" part is platform-only, but the
   inference is strong: the guard is present on the breaking runs and they break.)
2. **Loops are NORMAL behavior, not a break signature.** Repeated tool-call signatures (re-reading files, re-running
   tests) are pervasive across ALL categories — including our strong Medium (sympy-23262 recurs 12×). So firing more
   (2/12 → 90%) is mostly FALSE POSITIVES: nagging the agent when it is working fine. Compliant, but counter-productive.
3. **Tuning up loses coverage** (4/12 → 43.8%) with no upside. The assistant-loop branch never fires (0%) in comp-108.
4. **Part of the break population has no loop to catch** (~9% of runs have max-recurrence 1 — premature single-decision
   patches, per the earlier forensics: django-13810 fail = premature-patch step2). No loop guard can reach those.

## Conclusion
The loop guard sits at/near its useful setting. There is no threshold that adds USEFUL coverage: down = false-positive
nagging on normal re-reads, up = less coverage, and the breaking wander runs are already caught. This confirms the
prior forensics (breaks = solver stochasticity, not a loop-coverage gap) on the comp-108 data. **The last compliant
active lever is closed.**

## Net (this session)
Active single-miner space now EXHAUSTIVELY swept and closed: content levers on BOTH separability axes (token size m24,
depth depth-gate) + the gated break-fix (m22/m23) + the non-content loop guard (this). Root cause: comp-108 E/M/H are
non-separable by any per-call signal (DISCOVERIES top). The only remaining position-improving move is the PORTFOLIO/TIMING
play: the byte-identical insurance twin (defend Single-Hard vs the king's volatile Hard; hold passive position for
Pair(M,H) → ~14.3%). Artifact: `/tmp/loopguard_probe.py`; m12 LIVE untouched.
