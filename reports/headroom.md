# m7 — safe compression headroom
_from data/latest/miner_detail.json; proven-achievable upper bound (leader passed at the higher ratio)._

**33 SAFE tasks with headroom.** Est. total per-task score gain **+11.24** → avg over 45 tasks **+0.250** (rough lift 1.279 → ~1.53 if fully captured).

## SAFE — passes baseline AND compressed; a leader proved a higher ratio still passes
| task | our ratio | proven ratio | by | ×more | ~score gain | cur score |
|------|-----------|--------------|----|-------|-------------|-----------|
| django__django-14752 | 2.47× | 11.37× | 5DhHqmB1 | 4.61× | +0.764 | 2.014 |
| sympy__sympy-16766 | 1.53× | 5.79× | 5FbqgypX | 3.77× | +0.664 | 0.812 |
| django__django-13363 | 3.83× | 11.07× | 5DhHqmB1 | 2.89× | +0.530 | 2.861 |
| django__django-15499 | 1.26× | 3.47× | 5EkiFXSR | 2.75× | +0.506 | 0.237 |
| django__django-13417 | 2.13× | 5.77× | 5E7hCCzj | 2.71× | +0.498 | 1.953 |
| django__django-11133 | 2.84× | 7.32× | 5FbqgypX | 2.57× | +0.473 | 0.366 |
| django__django-14580 | 4.69× | 11.77× | 5DhHqmB1 | 2.51× | +0.460 | 1.665 |
| django__django-10880 | 2.50× | 6.17× | 5EkiFXSR | 2.47× | +0.452 | 1.421 |
| django__django-14855 | 3.44× | 8.45× | 5EkiFXSR | 2.46× | +0.449 | 2.213 |
| django__django-11119 | 2.68× | 6.55× | 5DhHqmB1 | 2.44× | +0.446 | 1.485 |
| django__django-10914 | 2.81× | 6.79× | 5EkiFXSR | 2.41× | +0.440 | 1.509 |
| django__django-16255 | 2.24× | 5.20× | 5DhHqmB1 | 2.32× | +0.421 | 1.369 |
| django__django-12419 | 4.88× | 11.12× | 5EkiFXSR | 2.28× | +0.412 | 2.960 |
| sympy__sympy-24539 | 2.50× | 5.44× | 5EkiFXSR | 2.17× | +0.388 | 1.478 |
| django__django-13741 | 2.23× | 4.51× | 5E7hCCzj | 2.03× | +0.353 | 1.366 |
| sympy__sympy-17655 | 3.62× | 7.17× | 5FbqgypX | 1.98× | +0.342 | 1.629 |
| django__django-11603 | 2.65× | 5.10× | 5FbqgypX | 1.93× | +0.328 | 2.054 |
| django__django-11239 | 1.72× | 3.17× | 5E7hCCzj | 1.84× | +0.306 | 0.532 |
| sympy__sympy-15809 | 1.85× | 3.23× | 5FbqgypX | 1.75× | +0.280 | -0.767 |
| django__django-14915 | 5.72× | 9.96× | 5DhHqmB1 | 1.74× | +0.277 | 1.780 |
| django__django-14089 | 2.28× | 3.89× | 5DhHqmB1 | 1.71× | +0.267 | 1.387 |
| sympy__sympy-16450 | 2.82× | 4.79× | 5FbqgypX | 1.70× | +0.265 | 1.968 |
| sympy__sympy-15017 | 2.29× | 3.82× | 5EkiFXSR | 1.67× | +0.257 | 1.426 |
| django__django-11951 | 3.78× | 6.25× | 5E7hCCzj | 1.65× | +0.252 | 1.668 |
| sympy__sympy-21847 | 2.07× | 3.40× | 5EkiFXSR | 1.64× | +0.249 | 1.354 |
| sympy__sympy-19954 | 7.32× | 11.45× | 5FbqgypX | 1.56× | +0.223 | 2.011 |
| django__django-15569 | 5.77× | 8.56× | 5EkiFXSR | 1.48× | +0.197 | 1.769 |
| django__django-15315 | 6.08× | 9.00× | 5FbqgypX | 1.48× | +0.196 | 1.872 |
| django__django-15851 | 2.33× | 3.42× | 5EkiFXSR | 1.47× | +0.192 | 1.425 |
| django__django-13933 | 3.40× | 4.49× | 5E7hCCzj | 1.32× | +0.139 | 1.590 |
| django__django-16100 | 2.08× | 2.69× | 5EkiFXSR | 1.30× | +0.130 | 2.376 |
| sympy__sympy-23534 | 2.50× | 2.98× | 5FbqgypX | 1.19× | +0.088 | 0.343 |
| django__django-14493 | 1.88× | 1.88× | 5DhHqmB1 | 1.00× | +0.001 | 0.621 |

## RECOVERED — we fixed a failing baseline (✗→✓); push cautiously (may lose the recovery)
| task | our ratio | proven ratio | by | ~score gain |
|------|-----------|--------------|----|-------------|
| django__django-11299 | 0.74× | 4.64× | 5E7hCCzj | +0.920 |
| django__django-12308 | 3.33× | 8.24× | 5EkiFXSR | +0.454 |
| sympy__sympy-22714 | 2.38× | 5.37× | 5EkiFXSR | +0.406 |
| sympy__sympy-15875 | 2.48× | 3.33× | 5EkiFXSR | +0.147 |

## No headroom — already ≥ leaders' proven ratio; don't compress more (1)
- django__django-14539 — 2.89× (best leader 2.60×)
