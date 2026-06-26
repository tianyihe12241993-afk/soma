# King vs m12 — per-task diagnosis (2026-06-24)

**NEW DATA SOURCE:** the dashboard miner-detail page (`/dashboard/miner/108/<hotkey>`) now
embeds full per-task JSON: `pass_without_compression`, `pass_with_compression`,
`tokens_without/with_compression`, `input/cached/output_tokens_with_compression`,
`platform_score`, `run_count` (5). This CLOSES the "token-type split" gap noted in CLAUDE.md.
Immutable snapshots: `data/raw/platform_results/2026-06-24/{m12_5Dz7,king_5DFvym}_pertask.json`.

## Outcome mix (50 tasks, platform-aggregated over 5 runs)
| | pass-pass | FLIP | BREAK | fail-fail | mean |
|---|---|---|---|---|---|
| m12 (5Dz7) | 31 | 7 | 3 | 9 | 0.7685 (#2) |
| king (5DFvym) | 30 | 5 | 4 | 11 | 0.7801 (#1) |

**Counterintuitive:** the king has MORE breaks (4) and FEWER flips (5) than m12, yet outscores us.
Its edge is NOT outcome mix — it's the savings-multiplier + run-stability on shared pass-pass tasks.

## Where the king actually beats us (king_score − m12_score, top)
| Δ | task | m12 | king | why |
|---|---|---|---|---|
| +3.13 | django-13810 | −1.98 BRK | +1.16 PP | m12 BREAKS, king passes |
| +3.10 | sympy-23262 | −1.83 BRK | +1.27 PP | m12 BREAKS, king passes |
| +2.20 | django-11740 | −0.93 PP | +1.27 PP | m12 passing-but-NEGATIVE (run variance) |
| +2.09 | sympy-14531 | −0.16 PP | +1.92 PP | m12 unstable on a passing task |
| +1.89 | django-11149 | −0.80 FF | +1.09 FF | m12 INFLATES (−3% sv) vs king +53% sv |
| +1.11 | sympy-15349 | −1.03 PP | +0.08 PP | m12 INFLATES (−51% sv) → multiplier floors it |

**Shared pass-pass tasks (28): king is +4.62 ahead; m12 avg savings 27.2% vs king 34.6%.**
m12 wins it most of that back on Hard/flip tasks king can't do (sympy-23824, django-14017,
django-13158, django-15037-king-breaks), netting the near-tie. So: **king wins the pass-pass /
high-savings / stable lane (= Easy); m12 wins the hard / flip lane.** Confirms the standing read.

## Recoverable headroom (need only +0.58 pts / +0.0116 mean to pass king)
1. **3 BREAK tasks = −4.23** (django-12039, django-13810, sympy-23262). Fixing just the 2 worst
   (django-13810, sympy-23262) to pass-pass = **+5.8 pts = +0.116 mean → well past king.**
   - BOTH are in the running local A/B → we'll get direct evidence whether the break is
     COMPRESSION (m12 drops needed content → agent fails; fixable) or SAMPLING (qwen3-coder
     variance; not fixable). This is the key question.
2. **Inflation drag (10 tasks with savings<0):** sympy-15349 (−51% sv, PP, −1.03), sympy-14976
   (−52%, FF, −0.76), django-13315 (−51%, FF), django-15161 (−43%, PP), django-12155 (−95%!, PP),
   sympy-13647/20590/22456 (PP, mild). A PURE never-inflate guard (emit original when
   compressed>original) recovers the passing ones with ZERO risk to the harvest. This is the
   m14/m15 thesis — now with receipts. CAVEAT: m13 collapsed M/H because it bundled never-inflate
   WITH aggressiveness-cap+gentling; a pure never-inflate must NOT touch harvest aggressiveness.
   Check m15's scored result (it isolated pure never-inflate) before rebuilding.
3. **Pass-pass but negative (4): run-variance** — django-14122 (−1.02), django-11740 (−0.93),
   sympy-14531 (−0.16), sympy-15349 (−1.03/also inflation). These = qwen3-coder sampling (broke in
   some of 5 runs). NOT compression-fixable per established root-cause. Don't chase these.

## NET takeaway
The path to #1 is NOT more/less compression globally — it's **(a) stop INFLATING on the ~6 passing
tasks where compressed>original (pure never-inflate, harvest untouched), and (b) determine if the 2
big BREAK tasks are compression or sampling (A/B answers this).** If even one break is a true
compression break we can fix it without touching the winning harvest, we pass the king.
m12 stays LIVE until something beats it scored.
