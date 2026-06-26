# m12 run-variance — per-run analysis (2026-06-24) — OVERTURNS "root=sampling"

**Source:** dashboard miner-detail now embeds `sweRunsByTaskId` — per RUN (5/task): `platform_score`,
`pass_with_compression`, token split (weighted/input/cached/output), `time_taken_seconds`, `agent_steps`.
Snapshots: `data/raw/platform_results/2026-06-24/{m12_5Dz7,king_5DFvym}_perrun.json`. 250 runs each.

## Score = mean of 5 run scores (confirmed)
django-11095: runs [−4.0, +1.4, +1.3, +1.2, +1.5] → mean 0.286 = platform_score. ✓
A single −4 run drags a ~1.36-tier task to 0.286.

## The variance tax
**25 of 50 m12 tasks are "split"** (some runs pass, some break). If every split task scored like its
PASSING runs, m12 mean rises **+0.90 (0.768 → ~1.67).** King is +0.0116 ahead → variance tax = 77× the gap.

## Head-to-head: m12 vs king break-stability (THE decisive comparison)
| | m12 | king |
|---|---|---|
| split tasks (runs disagree) | 27/50 | 21/50 |
| total −4 break RUNS (of 250) | **17** | **7** |

**8 tasks where m12 breaks MORE than king:**
| task | m12 runs | king runs |
|---|---|---|
| sympy-23262 | [−4,−4,+1,+2,−4] 3 brk | [+1,+1,+2,+1,+1] **0 brk** |
| django-13810 | [−4,−4,+1,−4,+1] 3 brk | [+1,+1,+1,+1,+1] **0 brk** |
| django-11740 | [+1,−4,+1,+1,−4] 2 brk | [+1,+1,+1,+1,+1] **0 brk** |
| sympy-15349 | [−4,+1,+1,+1,−4] 2 brk | [+1,−4,+1,+1,+1] 1 brk |
| sympy-11618 | [−4,+1,+1,+1,+1] 1 brk | all pass **0 brk** |
| django-12754 | [+1,+1,+1,−4,+1] 1 brk | all pass **0 brk** |
| django-11551 | [+1,−4,+1,+1,+2] 1 brk | all pass **0 brk** |
| django-11095 | [−4,+1,+1,+1,+2] 1 brk | all pass **0 brk** |
(king breaks more on only 3: django-14122, django-15103, sympy-24213.)

## Why this falsifies "root = sampling"
The platform runs the **SAME agent (qwen3-coder)** for every miner. The only per-task difference between
m12 and the king is the **compressed context** each feeds the agent. If the −4 breaks were intrinsic agent
sampling, the king would break on the same tasks. It does NOT (0/5 where m12 is 3/5). Therefore the breaks
are **m12's compression occasionally dropping content the agent needs to keep the baseline passing** — and
they are FIXABLE, because the king's compression demonstrably avoids them on the identical task.

The earlier "pass/fail runs look identical → must be sampling" read was made WITHOUT king per-run data
(unavailable until the dashboard exposed it). With the comparison, it's clear m12 is simply less break-stable.

## It's content-selection quality, not aggressiveness
- sympy-23262: king kept MORE (24% savings vs m12 47%) → stable.
- django-13810: king compressed MORE (33% vs 30%) → still stable.
Mixed direction ⇒ the win is keeping the RIGHT lines (errors/tests/diffs/the failing path), not a global
dial. This is precisely the m17 thesis (extractive selection in the harvest path), which never got a paid A/B.

## Headroom & direction
Matching king's break rate (17→7 break-runs ≈ recover 10 runs × ~5 pts / 250) ≈ **+0.20 mean → ~0.97, well
past #1.** NEW DIRECTION: break-stability via smarter content-selection on the break-prone tasks (NOT more
ratio, NOT global depth). Free secondary: pure never-inflate on the ~6 inflating passing tasks (see
king_vs_m12_pertask_diagnosis.md). The running RUNS=5 A/B includes django-13810 + sympy-23262 → it is the
first direct read on whether any compression change lowers their break rate. m12 stays LIVE until beaten scored.

## Caveats
- 5 runs/task is small n; the 17-vs-7 aggregate is robust but per-task (e.g. 3/5 vs 0/5) has wide CIs.
- Need to confirm the mechanism on ONE task: diff m12's break-run context vs pass-run context vs king's
  context on django-13810 to see exactly what content is dropped. (next investigation)

---

## GAP #2 (from token-split metrics): cache / weighted-token stability
"Weighted" = scored savings token count, with cached tokens at ~0.37× (verified:
weighted ≈ input + output + 0.37·cached). Cache rate therefore drives the savings score.

| | cache/total | weighted-ratio (base÷weighted) | weighted tok | steps | time(s) |
|---|---|---|---|---|---|
| m12 | 55% | 2.96× | 646k | 49.5 | 726 |
| king | 87% | 3.93× | 411k | 49.7 | 559 |

Same ~49 steps, near-equal TOTAL tokens (994k vs 944k), but king is 87% cache-hit vs m12 55%
→ king weighted tokens 36% lower → king's steady ratio-bonus + savings-multiplier edge on every
passing task (king 34.6% sv vs m12 27.2% on shared pass-pass). 23/50 m12 tasks run <65% cache;
some 0–6% (django-12050 m12 0%/3.12× vs king 86%/5.00×).

MECHANISM: m12 compression is drop-based + DYNAMIC — re-decides drops every turn → prompt prefix
changes each turn → provider prompt-cache MISSES → re-processed as fresh input. King is prefix-stable
(compress old turns once, freeze, append) → cache holds. This SAME re-compress-every-turn behavior
plausibly causes BOTH gap #1 (re-dropping removes later-needed content → breaks) AND gap #2 (cache
churn). A cache-stable append-only / freeze-on-emit compression attacks both. = the m19 thesis, which
we rejected as "churn inherent to drop-stripping" — but king's 87% PROVES cache-stability is achievable;
the lesson is m12's drop-based architecture can't do it, not that it's impossible. REVISIT m19 with a
freeze-on-emit design (NOT drop-based).

CAVEAT: per-task corr(cache%, score)≈0.01 — pass/break (±4–5) dwarfs the ratio bonus (±0.5). So
break-stability (gap #1) is the BIG lever (~+0.20 mean); cache/weighted (gap #2) is the steady edge
on PASSING tasks (our weak Easy lane), a meaningful slice of king's +4.62 pass-pass lead.

PROS confirmed: m12 break-runs avg 43.6 steps vs 50.1 pass-runs → breaks are PREMATURE-PATCH (agent
submits early & broken), not wander. m12 wins Hard/flips (7 vs 5) + stable where king breaks
(django-15037, sympy-16792, django-14122).
