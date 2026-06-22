# m7 gap analysis — safe compression headroom
_computed 2026-06-21T16:30:50Z from data/processed/shared_pass_tasks.jsonl. Model: score ~ 1 + 0.5·ln(ratio) (manual interpretation). Proven upper bound._

**34 SAFE headroom tasks** (m7 passes, a top miner proved a higher ratio, not fragile). Est. total per-task gain **+15.38** → avg over 45 tasks **+0.342** (rough lift 1.279 → ~1.62 if fully captured).

## Ranked safe headroom (push these first)
| task | m7 ratio | proven | by | ×more | ~gain | m7 score | actual gap | ratio-expl |
|------|----------|--------|----|-------|-------|----------|-----------|-----------|
| django__django-16255 | 2.24× | 16.98× | t6 | 7.58× | +1.013 | 1.369 | +0.301 | +0.299 |
| django__django-11299 | 0.74× | 4.64× | t2 | 6.29× | +0.919 | 2.385 | +0.717 | +0.890 |
| django__django-13741 | 2.23× | 12.39× | t10 | 5.57× | +0.858 | 1.366 | +0.190 | +0.209 |
| django__django-14752 | 2.47× | 12.02× | t10 | 4.87× | +0.792 | 2.014 | +0.136 | +0.157 |
| sympy__sympy-15809 | 1.85× | 7.89× | t10 | 4.27× | +0.726 | -0.767 | +1.102 | +0.051 |
| django__django-15851 | 2.33× | 8.06× | t10 | 3.47× | +0.622 | 1.425 | +0.218 | +0.192 |
| django__django-11119 | 2.68× | 8.81× | t5 | 3.28× | +0.594 | 1.485 | +0.220 | +0.205 |
| django__django-13363 | 3.83× | 12.14× | t10 | 3.17× | +0.576 | 2.861 | +0.251 | +0.313 |
| django__django-15499 | 1.26× | 3.82× | t10 | 3.03× | +0.554 | 0.237 | +1.376 | +0.506 |
| sympy__sympy-24539 | 2.50× | 6.91× | t7 | 2.76× | +0.507 | 1.478 | +0.348 | +0.388 |
| django__django-13417 | 2.13× | 5.77× | t2 | 2.71× | +0.498 | 1.953 | +0.345 | +0.314 |
| sympy__sympy-22714 | 2.38× | 6.44× | t7 | 2.70× | +0.497 | 1.320 | +2.282 | +0.406 |
| django__django-11133 | 2.84× | 7.32× | t3 | 2.57× | +0.473 | 0.366 | +1.441 | +0.409 |
| django__django-14580 | 4.69× | 11.77× | t4 | 2.51× | +0.460 | 1.665 | +0.117 | +0.176 |
| django__django-12308 | 3.33× | 8.24× | t1 | 2.48× | +0.454 | 2.933 | -0.754 | +0.454 |
| django__django-10880 | 2.50× | 6.17× | t1 | 2.47× | +0.452 | 1.421 | -0.773 | +0.452 |
| django__django-14855 | 3.44× | 8.45× | t1 | 2.46× | +0.449 | 2.213 | +0.340 | +0.449 |
| django__django-10914 | 2.81× | 6.79× | t1 | 2.41× | +0.440 | 1.509 | +0.400 | +0.440 |
| django__django-11603 | 2.65× | 6.31× | t10 | 2.38× | +0.434 | 2.054 | +0.298 | +0.319 |
| django__django-12419 | 4.88× | 11.12× | t1 | 2.28× | +0.412 | 2.960 | +0.231 | +0.412 |
| sympy__sympy-21847 | 2.07× | 4.30× | t10 | 2.08× | +0.366 | 1.354 | +0.264 | +0.249 |
| sympy__sympy-15017 | 2.29× | 4.68× | t7 | 2.05× | +0.358 | 1.426 | -2.002 | +0.257 |
| sympy__sympy-17655 | 3.62× | 7.17× | t3 | 1.98× | +0.342 | 1.629 | -2.114 | +0.190 |
| sympy__sympy-16450 | 2.82× | 5.26× | t7 | 1.86× | +0.311 | 1.968 | +0.173 | +0.176 |
| django__django-14915 | 5.72× | 9.96× | t4 | 1.74× | +0.277 | 1.780 | +0.006 | +0.002 |
| django__django-15315 | 6.08× | 10.44× | t7 | 1.72× | +0.270 | 1.872 | -0.214 | -0.732 |
| django__django-14089 | 2.28× | 3.89× | t4 | 1.71× | +0.267 | 1.387 | +0.050 | +0.035 |
| django__django-13933 | 3.40× | 5.77× | t10 | 1.70× | +0.264 | 1.590 | -1.021 | +0.129 |
| django__django-11951 | 3.78× | 6.25× | t2 | 1.66× | +0.252 | 1.668 | -0.981 | +0.184 |
| django__django-15569 | 5.77× | 9.29× | t10 | 1.61× | +0.238 | 1.769 | -1.057 | +0.197 |
| sympy__sympy-19954 | 7.32× | 11.45× | t3 | 1.56× | +0.223 | 2.011 | +1.150 | +0.164 |
| django__django-16100 | 2.08× | 3.16× | t10 | 1.52× | +0.210 | 2.376 | +0.085 | +0.130 |
| sympy__sympy-15875 | 2.48× | 3.33× | t1 | 1.34× | +0.147 | 1.349 | +0.999 | +0.147 |
| sympy__sympy-23534 | 2.50× | 3.21× | t8 | 1.28× | +0.125 | 0.343 | -1.008 | -0.230 |

## Barely-compressed (m7 ratio < 2×) — 6 tasks, biggest raw headroom
| task | m7 ratio | m7 score |
|------|----------|----------|
| django__django-11299 | 0.74× | 2.385 |
| django__django-15499 | 1.26× | 0.237 |
| sympy__sympy-16766 | 1.53× | 0.812 |
| django__django-11239 | 1.72× | 0.532 |
| sympy__sympy-15809 | 1.85× | -0.767 |
| django__django-14493 | 1.88× | 0.621 |

## Fragile tasks EXCLUDED from the push list (4)
- django__django-11239, django__django-14493, sympy__sympy-16766, sympy__sympy-17139

## Caveats
- Upper bound: assumes m7 can match the proven ratio **without losing the pass**. Validate each push locally; a broken pass costs ~−4 (catastrophic).
- Score model is manual interpretation; observed `actual_score_gap` is carried for truth.
- Medium/Hard attribution needs the task→category map (currently missing).
