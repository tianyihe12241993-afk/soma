# EXP-1b depth-frontier verdict — HOLD m12, depth is not a lever (2026-06-24)

_Same-window local A/B on the real comp-108 tasks (the only trustworthy eval). Run dir
`experiments/runs/2026-06-23_222022_H1M_pbatch`. 54/54 solves, 0 FAILED, 0 OpenRouter 429s. Profiles differ ONLY
in TARGET_TOKENS: m12=8k (LIVE), m12_deeper=4k, m12_lighter=16k — identical code otherwise._

## The data (6 tasks × 3 profiles × RUNS=3)

### Task-level breaks (baseline passes but we fail = the −4/−5 swing — the dominant scoring factor)
| profile | tasks that broke baseline | count |
|---|---|---|
| **m12** | sympy-24066 | **1** |
| m12_deeper | sympy-24066, sympy-23262 | 2 |
| m12_lighter | sympy-24066, django-12039, django-13810 | 3 |
**Breaks rise monotonically as you move away from m12 (deeper +1, lighter +2). m12 has the FEWEST breaks.**

### Resolved (per-category, runs)
| category | m12 | m12_deeper | m12_lighter |
|---|---|---|---|
| clean (2 tasks, 6 runs) | 3/6 | 5/6 | 5/6 |
| ppBreak (3 tasks, 9 runs) | **5/9** | 5/9 (+1 break) | 3/9 (+2 breaks) |
| flipPartial (sympy-24066, 3 runs) | 0/3 | 0/3 | 0/3 |
- The clean "win" for deeper/lighter is NOISE: m12 scored only 1/3 and 2/3 on tasks it normally passes →
  run-variance this window was large. With n=3 the deeper 5/6 vs m12 3/6 is within that noise.
- On the SELECTED hard tasks (ppBreak + flip — the reason for the experiment) deeper is NOT better (same 5/9,
  +1 break) and lighter is clearly worse (3/9, +2 breaks).

### Tokens / cache (the compression-ratio + savings-gate dimension) — deeper is WORSE everywhere
| category | metric | m12 | m12_deeper | m12_lighter |
|---|---|---|---|---|
| clean | avg_total tokens | 367k | 460k | 598k |
| ppBreak | avg_total tokens | 874k | **1067k** | 824k |
| flip | avg_total tokens | 699k | 866k | 772k |
| ppBreak | avg uncached input | 166k | **215k** | 120k |
| (all) | cache-hit rate | 0.82–0.86 | **0.80–0.84** | 0.86–0.91 |
**Deeper uses MORE total tokens AND more uncached input AND has the LOWEST cache-hit in every category.**

## The 7 questions, answered
1. **Does deeper lift compression-ratio without breaks?** NO. Deeper raises TOTAL tokens (agent wanders more
   steps) → the per-message ratio gain is erased at the task level, and it adds a break. The ratio bonus premise
   fails in practice.
2. **Does deeper break pass-pass tasks?** YES, mildly — +1 baseline-break vs m12's fewest. Wrong direction.
3. **Does lighter cut breaks?** NO — lighter ADDED breaks (3 tasks vs m12's 1). So **m12 is NOT over-compressing**;
   easing off makes things worse.
4. **Is run-variance compression-caused or agent-noise?** AGENT/PROVIDER NOISE. Lighter (less compression)
   increased breaks; m12 got 1/3 then 2/3 on "clean" tasks. Depth doesn't control it → it's irreducible via our
   lever. (Confirms the comp108_headroom caveat: the 17.6-pt "run-variance headroom" was an upper bound, mostly
   agent noise.)
5. **Does the flip convert at any depth?** NO — sympy-24066 = 0/3 and broke at all three depths → capability/
   agent-bound, not compression-bound.
6. **Safe direction (deeper/lighter)?** NEITHER. Deeper costs tokens+cache+a break; lighter costs resolves+breaks.
7. **Recommendation?** **HOLD m12.** It is the best of the three on the factors that actually score (fewest
   breaks, best tokens/cache), and the only signal favoring deeper (one extra majority-pass) is the noisiest.

## NEW mechanism finding (worth recording) — aggressive re-compression breaks prompt caching
Deeper (TARGET_TOKENS 4k) had the LOWEST cache-hit (0.80–0.84) and the HIGHEST uncached input. Rewriting the
context more aggressively each turn changes the cached prefix → cache misses → more BILLED input. The
weighted-token-savings gate counts input×1, cached×⅓, output×3, so cache-invalidation **directly worsens the
gate** on top of the agent-wander token blow-up. So deeper is doubly self-defeating: lower ratio (wander) AND
worse gate (cache loss). Any future change that heavily rewrites context turn-over-turn inherits this cost —
prefer append-mostly / cache-stable edits.

## Estimated platform-score delta
- **deeper:** ≈ neutral-to-NEGATIVE. No reliable resolve gain on hard tasks, +1 break, lower ratio bonus (more
  total tokens), worse savings gate (cache loss). Not worth the M/H moat risk.
- **lighter:** NEGATIVE. Fewer resolves on hard tasks, most breaks.
- **m12:** best of the three. No change.

## Decision
**HOLD m12 (LIVE, 0.768, #2). Do not change TARGET_TOKENS in either direction.** This closes the depth-frontier
research line. Confirms comp108_headroom's "depth is illusory" hypothesis with same-window evidence, and matches
the external ACON finding (aggressive compression degrades long-horizon agents; moderate is best —
reports/cot_compression_literature.md). m12's ~1.75× is the equilibrium, not under-compression.

## What's left (if we pursue anything — low expected value)
- NOT depth, NOT Easy. The only literature-backed compliant idea is **content-selectivity** (protect
  error/test/diff/state, compress prose; cache-STABLE) — see reports/cot_compression_literature.md. Targets breaks
  without raising aggressiveness. Hypothesis only; same same-window bar; protect-list first (low risk).
- Otherwise: monitor (king 0.780 the only miner ahead; we own M+H), watch the in-flux upstream scoring layer.
