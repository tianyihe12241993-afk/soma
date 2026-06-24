# Comp-108 strategy & plan (2026-06-23) — defend M+H, nudge Easy

## Where we stand (scored, 19 miners)
- #1 king 5DFvymSeEw 0.780 (E0.812/M0.934/H0.596) · #2 m12 0.768 (E0.412/M0.953/**H0.919**). #3–4 ≤0.66.
- 7-element: **m12 wins (M,H)+M+H ≈ 19%**; king wins Overall(57%)+(E,M)+(E,H)+E. King's ONLY edge is Easy;
  we crush Hard (+0.32) and edge Medium.

## The target (precise, modest)
- Overall avg: m12 0.7615 vs king 0.7807. **Easy +0.058 (0.412→0.47) TIES Overall; ~0.50 FLIPS Overall(57%)
  +(E,H) → ~85% of the pool.** A SLIGHT lift — NOT the king's 0.81. Chasing Easy past ~0.50 is wasted
  (E-single/(E,M) need ~0.8 = agent-decisiveness we can't buy).

## Hard constraints (learned the hard way this round)
- **Easy is agent-DECISIVENESS-bound** (king wins via fewer agent steps, not compression). 4 candidates
  (m13 cap, m14/m15 never-inflate, m16 light-safe) failed to move it via compression; behavior steering is
  BANNED. So a big Easy lift is NOT available — only a marginal, uncertain one.
- **Platform scores are TEMPORALLY NOISY** (OpenRouter provider window swings Hard ±0.3). Cross-window /
  single-submission A/B is UNRELIABLE. Only SAME-WINDOW local A/B on the real comp-108 tasks is trustworthy.
- **Softening the harvest collapses H+M** (m13). The harvest is the moat — keep it byte-identical.

## Strategy
1. **PRIMARY — DEFEND M+H (locked).** Never touch the harvest/flip handling. m12's M0.953/H0.919 secures
   (M,H)+M+H (~19%) outright and is robust (we dominate Hard). This is non-negotiable; m12 stays LIVE.
2. **LEVERAGE — slight Easy lift (+0.06–0.09), ZERO H/M risk.** Only small-context-SCOPED changes that are
   byte-identical on M/H and can't trip the ≥10% savings gate. Candidate = m16 (rich on erratic/inflated small
   contexts; byte-identical on M/H by construction). Expectation: LOW confidence (Easy is agent-bound), so this
   is an upside bet, not a must.
3. **DISCIPLINE.** Same-window local A/B (m12 vs candidate) on comp-108 Easy tasks; hold the OpenRouter
   key/window constant; compliant-only; never decide off a single platform score.

## Plan (concrete, bounded)
- **Step 1 — confirm the Easy bet (cheap, controlled).** Larger same-window m12-vs-m16 eval: ~10 Easy-proxy
  comp-108 tasks, RUNS=5, MAXJOBS=3 (~100 solves). Measure: resolved, breaks, AND an Easy-score proxy that
  accounts for m16's higher token use (m16's reliability bump must NET positive after its worse ratio). The
  step-test n=12 hinted +2 resolved but more tokens/steps — this settles whether it's a real, net-positive
  Easy gain at zero H/M risk.
- **Step 2a — if m16 nets a real +Easy (≥+0.04, M/H byte-identical):** ship m16 to a FRESH hotkey, same key,
  m12 left LIVE. Read the platform result with the temporal-noise caveat (compare windows where possible).
- **Step 2b — if m16 ≈ m12 or net-negative:** HOLD m12. Easy is confirmed at our ceiling; #2 at 0.768 is a
  strong position. Stop Easy work; shift to monitoring + any M/H-specific opportunity.
- **Ongoing (low-effort):** watch the leaderboard/rivals each cycle (only the king is ahead; #3–4 far back);
  track the in-flux upstream scoring layer (penalty-fix / scoring-formula / llm-semantic-scoring — could change
  the incentive math); re-pull the comp-108 task set if the competition rotates.

## Realistic expectation
The Easy lift is the highest-leverage move BUT low-confidence (agent-bound). The honest base case: **m12 (#2,
0.768) is near our compliant ceiling, and holding it is a good outcome.** We pursue the slight Easy lift only
because the target is small (+0.06) and the candidate (m16) is zero-H/M-risk — pure upside if it lands, no
downside to m12 if it doesn't.
