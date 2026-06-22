# H1 safe-compression targets
_computed 2026-06-21T22:21:36Z — 36 tasks (safe/moderate/fragile). est lift = 0.5·ln(leader/m7)._

| task | cat | risk | m7× | leader× (by) | head | m7 score | ~lift | m7 neg | leader neg | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| django__django-16255 | Easy | safe | 2.24 | 16.98 (t6) | 7.58× | 1.369 | +1.013 | 0/5 | 0/5 | m7 clean (0 neg); t6 proves 17.0x with 0 neg on this task |
| django__django-13741 | Easy | safe | 2.23 | 12.39 (t10) | 5.57× | 1.366 | +0.858 | 0/5 | 0/5 | m7 clean (0 neg); t10 proves 12.4x with 0 neg on this task |
| django__django-14752 | Hard | safe | 2.47 | 12.02 (t10) | 4.87× | 2.014 | +0.792 | 0/5 | 0/5 | m7 clean (0 neg); t10 proves 12.0x with 0 neg on this task |
| django__django-15851 | Medium | safe | 2.33 | 8.06 (t10) | 3.47× | 1.425 | +0.622 | 0/5 | 0/5 | m7 clean (0 neg); t10 proves 8.1x with 0 neg on this task |
| django__django-11119 | Medium | safe | 2.68 | 8.81 (t5) | 3.28× | 1.485 | +0.594 | 0/5 | 0/5 | m7 clean (0 neg); t5 proves 8.8x with 0 neg on this task |
| sympy__sympy-24539 | Medium | safe | 2.50 | 6.91 (t7) | 2.76× | 1.478 | +0.508 | 0/5 | 0/5 | m7 clean (0 neg); t7 proves 6.9x with 0 neg on this task |
| django__django-14580 | Medium | safe | 4.69 | 11.77 (t4) | 2.51× | 1.665 | +0.460 | 0/5 | 0/5 | m7 clean (0 neg); t4 proves 11.8x with 0 neg on this task |
| django__django-14855 | Medium | safe | 3.44 | 8.45 (t1) | 2.46× | 2.213 | +0.449 | 0/5 | 0/5 | m7 clean (0 neg); t1 proves 8.5x with 0 neg on this task |
| django__django-10914 | Medium | safe | 2.81 | 6.79 (t1) | 2.41× | 1.509 | +0.440 | 0/5 | 0/5 | m7 clean (0 neg); t1 proves 6.8x with 0 neg on this task |
| django__django-11603 | Medium | safe | 2.65 | 6.31 (t10) | 2.38× | 2.054 | +0.434 | 0/5 | 0/5 | m7 clean (0 neg); t10 proves 6.3x with 0 neg on this task |
| django__django-12419 | Hard | safe | 4.88 | 11.12 (t1) | 2.28× | 2.960 | +0.412 | 0/5 | 0/5 | m7 clean (0 neg); t1 proves 11.1x with 0 neg on this task |
| sympy__sympy-17655 | Easy | safe | 3.62 | 7.17 (t3) | 1.98× | 1.629 | +0.342 | 0/5 | 0/5 | m7 clean (0 neg); t3 proves 7.2x with 0 neg on this task |
| django__django-14915 | Medium | safe | 5.72 | 9.96 (t4) | 1.74× | 1.780 | +0.277 | 0/5 | 0/5 | m7 clean (0 neg); t4 proves 10.0x with 0 neg on this task |
| django__django-15315 | Hard | safe | 6.08 | 10.44 (t7) | 1.72× | 1.872 | +0.270 | 0/5 | 0/5 | m7 clean (0 neg); t7 proves 10.4x with 0 neg on this task |
| django__django-14089 | Medium | safe | 2.28 | 3.89 (t4) | 1.71× | 1.387 | +0.267 | 0/5 | 0/5 | m7 clean (0 neg); t4 proves 3.9x with 0 neg on this task |
| sympy__sympy-21847 | Medium | safe | 2.07 | 3.40 (t1) | 1.64× | 1.354 | +0.249 | 0/5 | 0/5 | m7 clean (0 neg); t1 proves 3.4x with 0 neg on this task |
| django__django-15569 | Hard | safe | 5.77 | 9.29 (t10) | 1.61× | 1.769 | +0.238 | 0/5 | 0/5 | m7 clean (0 neg); t10 proves 9.3x with 0 neg on this task |
| sympy__sympy-15017 | Medium | safe | 2.29 | 3.22 (t10) | 1.41× | 1.426 | +0.171 | 0/5 | 0/5 | m7 clean (0 neg); t10 proves 3.2x with 0 neg on this task |
| django__django-13933 | Medium | safe | 3.40 | 4.49 (t2) | 1.32× | 1.590 | +0.139 | 0/5 | 0/5 | m7 clean (0 neg); t2 proves 4.5x with 0 neg on this task |
| django__django-11299 | Hard | moderate | 0.74 | 4.64 (t2) | 6.29× | 2.385 | +0.920 | 1/5 | 0/5 | m7 neg=1; best higher-ratio proof t2 4.6x neg=0 (clean) |
| django__django-13363 | Hard | moderate | 3.83 | 12.14 (t10) | 3.17× | 2.861 | +0.576 | 0/5 | 1/5 | m7 neg=0; best higher-ratio proof t10 12.1x neg=1 (clean) |
| django__django-15499 | Easy | moderate | 1.26 | 3.82 (t10) | 3.03× | 0.237 | +0.554 | 1/5 | 0/5 | m7 neg=1; best higher-ratio proof t10 3.8x neg=0 (clean) |
| django__django-13417 | Medium | moderate | 2.13 | 5.77 (t2) | 2.71× | 1.953 | +0.498 | 0/5 | 1/5 | m7 neg=0; best higher-ratio proof t2 5.8x neg=1 (clean) |
| django__django-11133 | Medium | moderate | 2.84 | 7.32 (t3) | 2.57× | 0.366 | +0.473 | 1/5 | 0/5 | m7 neg=1; best higher-ratio proof t3 7.3x neg=0 (clean) |
| django__django-10880 | Hard | moderate | 2.50 | 6.17 (t1) | 2.47× | 1.421 | +0.452 | 0/5 | 1/5 | m7 neg=0; best higher-ratio proof t1 6.2x neg=1 (clean) |
| django__django-12308 | Hard | moderate | 3.33 | 7.23 (t3) | 2.17× | 2.933 | +0.388 | 1/5 | 1/5 | m7 neg=1; best higher-ratio proof t3 7.2x neg=1 (clean) |
| sympy__sympy-16450 | Medium | moderate | 2.82 | 4.79 (t3) | 1.70× | 1.968 | +0.265 | 0/5 | 1/5 | m7 neg=0; best higher-ratio proof t3 4.8x neg=1 (clean) |
| django__django-11951 | Easy | moderate | 3.78 | 6.25 (t2) | 1.65× | 1.668 | +0.252 | 0/5 | 1/5 | m7 neg=0; best higher-ratio proof t2 6.2x neg=1 (clean) |
| sympy__sympy-19954 | Hard | moderate | 7.32 | 11.45 (t3) | 1.56× | 2.011 | +0.223 | 1/5 | 0/5 | m7 neg=1; best higher-ratio proof t3 11.5x neg=0 (clean) |
| django__django-16100 | Medium | moderate | 2.08 | 3.16 (t10) | 1.52× | 2.376 | +0.210 | 0/5 | 1/5 | m7 neg=0; best higher-ratio proof t10 3.2x neg=1 (clean) |
| sympy__sympy-23534 | Medium | moderate | 2.50 | 3.21 (t8) | 1.28× | 0.343 | +0.125 | 1/5 | 1/5 | m7 neg=1; best higher-ratio proof t8 3.2x neg=1 (clean) |
| sympy__sympy-15809 | Easy | fragile | 1.85 | 7.89 (t10) | 4.27× | -0.767 | +0.726 | 2/5 | 0/5 | m7/variant broke baseline or m7 has >=2 negative runs here — guard, do not push |
| sympy__sympy-16766 | Easy | fragile | 1.53 | 5.79 (t3) | 3.77× | 0.812 | +0.664 | 1/5 | 0/5 | m7/variant broke baseline or m7 has >=2 negative runs here — guard, do not push |
| sympy__sympy-22714 | Hard | fragile | 2.38 | 5.37 (t1) | 2.25× | 1.320 | +0.406 | 2/5 | 0/5 | m7/variant broke baseline or m7 has >=2 negative runs here — guard, do not push |
| django__django-11239 | Easy | fragile | 1.72 | 3.17 (t2) | 1.84× | 0.532 | +0.306 | 2/5 | 0/5 | m7/variant broke baseline or m7 has >=2 negative runs here — guard, do not push |
| sympy__sympy-15875 | Easy | fragile | 2.48 | 3.33 (t1) | 1.34× | 1.349 | +0.147 | 2/5 | 1/5 | m7/variant broke baseline or m7 has >=2 negative runs here — guard, do not push |
