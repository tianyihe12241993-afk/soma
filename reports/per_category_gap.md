# Per-category gap — m7 vs top-4 leaders (t1, t2, t3, t4)
_computed 2026-06-21T22:19:54Z from processed data. Negative run = run_score < 0._

| metric | Easy | Medium | Hard |
|---|---|---|---|
| m7 avg score | 0.621 | 1.500 | 1.760 |
| leader avg score | 1.032 | 1.329 | 2.118 |
| **score gap** | 0.411 | -0.171 | 0.358 |
| m7 avg ratio | 2.62× | 2.84× | 3.53× |
| leader avg ratio | 3.96× | 4.04× | 5.40× |
| m7 neg-run rate | 26.2% | 4.4% | 21.7% |
| leader neg-run rate | 20.5% | 10.1% | 14.5% |
| m7 broke-baseline | 0 | 0 | 1 |
| leader broke (t1-4 sum) | 0 | 4 | 0 |
| shared-pass tasks | 9 | 17 | 10 |
| shared-pass mean gap | 0.380 | 0.016 | 0.197 |
| …ratio-explained | 0.217 | 0.214 | 0.271 |
| …residual | 0.163 | -0.198 | -0.074 |

## Top 10 Medium — under-compressed but pass-stable
| task | m7× | proven× | by | head | m7 score | ~gain |
|---|---|---|---|---|---|---|
| django__django-15851 | 2.33 | 8.06 | t10 | 3.47× | 1.425 | +0.622 |
| django__django-11119 | 2.68 | 8.81 | t5 | 3.28× | 1.485 | +0.594 |
| sympy__sympy-24539 | 2.50 | 6.91 | t7 | 2.76× | 1.478 | +0.508 |
| django__django-13417 | 2.13 | 5.77 | t2 | 2.71× | 1.953 | +0.498 |
| django__django-14580 | 4.69 | 11.77 | t4 | 2.51× | 1.665 | +0.460 |
| django__django-14855 | 3.44 | 8.45 | t1 | 2.46× | 2.213 | +0.449 |
| django__django-10914 | 2.81 | 6.79 | t1 | 2.41× | 1.509 | +0.440 |
| django__django-11603 | 2.65 | 6.31 | t10 | 2.38× | 2.054 | +0.434 |
| sympy__sympy-21847 | 2.07 | 4.30 | t10 | 2.08× | 1.354 | +0.366 |
| sympy__sympy-15017 | 2.29 | 4.68 | t7 | 2.05× | 1.426 | +0.358 |

## Top 10 Hard — under-compressed but pass-stable
| task | m7× | proven× | by | head | m7 score | ~gain |
|---|---|---|---|---|---|---|
| django__django-14752 | 2.47 | 12.02 | t10 | 4.87× | 2.014 | +0.792 |
| django__django-13363 | 3.83 | 12.14 | t10 | 3.17× | 2.861 | +0.576 |
| django__django-10880 | 2.50 | 6.17 | t1 | 2.47× | 1.421 | +0.452 |
| django__django-12419 | 4.88 | 11.12 | t1 | 2.28× | 2.960 | +0.412 |
| django__django-15315 | 6.08 | 10.44 | t7 | 1.72× | 1.872 | +0.270 |
| django__django-15569 | 5.77 | 9.29 | t10 | 1.61× | 1.769 | +0.238 |

## Top fragile tasks (m7/variants broke a passing baseline)
| task | cat | broke_by | m7_broke | severity |
|---|---|---|---|---|
| sympy__sympy-17139 | Hard | m7 | yes | -0.25 |
| sympy__sympy-16766 | Easy | m10,m9 |  | -3.19 |
| django__django-11239 | Easy | m10,m11,m9 |  | -1.50 |
| django__django-14493 | Medium | m9 |  | -0.41 |

## Top catastrophic Hard-gap tasks (leader − m7)
| task | m7 score | leader score | gap | m7× | leader× |
|---|---|---|---|---|---|
| django__django-14999 | 1.096 | 4.008 | +2.912 | 2.46 | 2.68 |
| sympy__sympy-22714 | 1.320 | 3.602 | +2.282 | 2.38 | 5.37 |
| sympy__sympy-19954 | 2.011 | 3.161 | +1.150 | 7.32 | 10.16 |
| sympy__sympy-17139 | -0.246 | 0.893 | +1.139 | 3.87 | 5.93 |
| django__django-11299 | 2.385 | 3.101 | +0.716 | 0.74 | 4.37 |
| django__django-13363 | 2.861 | 3.112 | +0.251 | 3.83 | 7.17 |
| django__django-12419 | 2.960 | 3.191 | +0.231 | 4.88 | 11.12 |
| django__django-15930 | 0.757 | 0.907 | +0.150 | 0.96 | 0.90 |
| django__django-14752 | 2.014 | 2.150 | +0.136 | 2.47 | 3.38 |
| django__django-15315 | 1.872 | 1.659 | -0.214 | 6.08 | 1.41 |
