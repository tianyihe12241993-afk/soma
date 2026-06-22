# Compression-depth risk
_computed 2026-06-21T22:21:36Z on shared-pass tasks. neg run = run_score<0._

## Correlation: compression ratio vs risk (per miner-task, miner passes)
| scope | n | r(ratio,neg-rate) | r(ratio,broke) | r(ratio,score) | mean ratio | mean neg-rate |
|---|---|---|---|---|---|---|
| overall | 379 | -0.087 | — | 0.279 | 3.93× | 7.6% |
| Easy | 90 | -0.217 | — | 0.272 | 3.56× | 10.0% |
| Medium | 185 | -0.027 | — | 0.256 | 3.55× | 5.4% |
| Hard | 104 | -0.116 | — | 0.116 | 4.93× | 9.6% |

_r≈0 → deeper compression does NOT track higher flakiness; r>0.3 → it does._

## compression vs output-token increase
- **MISSING DATA** — the dashboard exposes one compressed-token count per run; there is no input/cached/output split, so weighted/output-token analysis is not possible yet.

## Feasibility of leader-level depth (≥4.5× with ≤1 neg) for m7-style
- 27 / 36 shared-pass tasks have a leader passing CLEANLY at ≥4.5× (75%). → deep compression is demonstrably pass-safe on these.

## Tasks where a leader compresses much deeper than m7 with NO extra negative runs (proven-safe-deep)
| task | cat | m7× (neg) | leader× (neg) | by |
|---|---|---|---|---|
| django__django-16255 | Easy | 2.24 (0) | 16.98 (0) | t6 |
| django__django-11299 | Hard | 0.74 (1) | 4.64 (0) | t2 |
| django__django-13741 | Easy | 2.23 (0) | 12.39 (0) | t10 |
| django__django-14752 | Hard | 2.47 (0) | 12.02 (0) | t10 |
| sympy__sympy-16766 | Easy | 1.53 (1) | 5.79 (0) | t3 |
| django__django-15851 | Medium | 2.33 (0) | 8.06 (0) | t10 |
| django__django-11119 | Medium | 2.68 (0) | 8.81 (0) | t5 |
| django__django-13363 | Hard | 3.83 (0) | 12.14 (1) | t10 |
| django__django-15499 | Easy | 1.26 (1) | 3.82 (0) | t10 |
| sympy__sympy-24539 | Medium | 2.50 (0) | 6.91 (0) | t7 |
| django__django-13417 | Medium | 2.13 (0) | 5.77 (1) | t2 |
| django__django-11133 | Medium | 2.84 (1) | 7.32 (0) | t3 |
| django__django-14580 | Medium | 4.69 (0) | 11.77 (0) | t4 |
| django__django-10880 | Hard | 2.50 (0) | 6.17 (1) | t1 |
| django__django-14855 | Medium | 3.44 (0) | 8.45 (0) | t1 |

## Tasks where deep compression clearly causes instability (≥4.5×, ≥3/5 neg)
| task | cat | miner | ratio | neg | score |
|---|---|---|---|---|---|
| sympy__sympy-19954 | Hard | t9 | 6.06 | 4 | -1.27 |
| sympy__sympy-22714 | Hard | t2 | 7.08 | 3 | 0.596 |
| django__django-12308 | Hard | t2 | 9.38 | 3 | 1.237 |
| django__django-12308 | Hard | t10 | 4.83 | 3 | 1.2 |
| sympy__sympy-23534 | Medium | t2 | 7.49 | 3 | -1.634 |
