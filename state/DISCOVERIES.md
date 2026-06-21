# DISCOVERIES (durable findings)

- **Incentive is layer-based (7 elements), not top-3.** Overall(E,M,H)=w1, pairs=1/6 each, singles=1/12 each.
  Winner of each = highest avg on that subset; failed-review excluded. Up to ~7 distinct miners can earn.
- **Flip-routing leaks Medium on the platform.** v15 (m7 + persistent-failure→rich) scored Medium **1.183**
  vs m7's 1.421 — the trigger pulls iterating medium tasks off the harvest bonus. Local validation under-detected
  this (only 2 medium instances). Implies m9/m10/m11 (more aggressive routing) likely also lose Medium.
- **Easy is ~1.13-bounded for us** across gentle/aggressive/adaptive compression. The king's Easy (1.347) and
  2nd's (1.433) come from agent *decisiveness* (fewer steps), not compression — unreachable via our lever.
- **King's Hard (1.751) = flip conversion @ comp_ratio ~0.85 + decisiveness.** We convert flips ~41% @ 0.52.
- **Gold-patch proxy under-counts** (equiv fixes: 11099 `\A..\Z`, 16429 `d.tzinfo if is_aware`, 14539 entity-loop).
  Real pass/fail needs SOMA_SWEREBENCH_EVAL (infeasible locally on arm64). Always manual-check gold=False.
- **Early-cutoff noise:** intermittent (~10–30% in bad windows) provider/agent variance — model emits a no-tool-call
  turn → session ends with empty/partial patch. NOT our code (same miner clean in one batch, cut in another).
- **Local e2e test-env is partly broken** (can't install some deps / run tests) → verification-wander inflates
  step counts vs the platform. Use the gold-PATCH metric + comp_ratio, not run-status, locally.
- **Dashboard:** thesoma.ai/dashboard embeds the leaderboard as JSON; per-miner: /dashboard/miner/107/<hotkey>.
  Display column order is total/Easy/Hard/Medium; JSON keys are {Easy,Medium,Hard}.
