# m16 step-test result — Easy is NOT reachable via our compression lever (2026-06-23)

_Controlled same-window paired A/B: m12 vs m16, 4 Easy-proxy comp-108 tasks (sympy-15349, django-12155,
sympy-13647, sympy-20590), RUNS=3 each (12 runs/profile), MAXJOBS=3, same OpenRouter key, interleaved →
controls for the temporal-provider variance that confounded m13/m14/m15. Run 2026-06-23_193955_H1M_pbatch.
(First attempt skipped m16 due to a missing driver profile — fixed, re-run.)_

## Result
| | resolved | mean agent_steps | broke | cache_hit | avg_total tok |
|---|---|---|---|---|---|
| m12 | 8/12 | **34.7** | 0 | 0.36 | 592k |
| m16 | 10/12 | **40.2** | 1 | 0.59 | 715k |
The rescue fired (12 rich_light + 12 raw_last_resort across m16 runs) — m16 genuinely differed from m12.

## Verdict: the hypothesis is DISPROVEN
1. **m16 took MORE agent_steps (40.2 vs 34.7), not fewer.** The king's Easy edge is FEWER steps (decisiveness);
   m16's cleaner compression does the OPPOSITE. We cannot replicate the king's Easy advantage via compression.
2. **The reliability bump is noise + costly:** resolved 10/12 vs 8/12 is within binomial noise at n=12, came
   WITH a new break (sympy-15349) and +23% total tokens (worse ratio). Not a clean win.
3. **m16's one consistent effect is cache-stability** (cache_hit 0.59 vs 0.36, lower uncached input) — but it
   raised total tokens and didn't cut steps, so its platform-score value is uncertain-to-negative.

## Conclusion (4 candidates, all falsified)
m13 (cap), m14/m15 (never-inflate), m16 (light-safe) — none cracks Easy. Consistent evidence: **Easy is bound
by AGENT DECISIVENESS (step count), which we cannot buy (behavior steering banned) and cannot induce via
compression.** m12's Easy ≈0.41 is near our compliant ceiling.

## Recommendation
- **No-submit m16** (no win, higher tokens, uncertain value). Kept as reference.
- **Stop chasing Easy via compression** — proven dead lever.
- **Keep m12 live (0.768, #2); defend/extend the M+H moat** (field #1: Medium 0.953, Hard 0.919).
- The king (0.780) beats m12 only on Easy decisiveness we can't match → m12 is near our practical ceiling for a
  compliant compression-only miner. Future value = hold M+H, watch rivals + the in-flux scoring layer
  (penalty-fix / scoring-formula / llm-semantic-scoring branches), re-pull the task set each new competition.
