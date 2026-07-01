# Why nocap failed (5FXAR4… = 0.416) — detailed analysis (2026-06-30 ~12:05Z)

**Snapshots:** detail `data/raw/dashboard/2026-06-30/115258_miner_detail.json` · per-run `…/platform_results/2026-06-30/120240_swe_runs.json` (nocap) + `080429_swe_runs.json` (np2).
**nocap = `max(16k, 0.60·len)` chars/result, NO upper cap.** Diverges from np2 (flat 16k) and cap32 (cap 32k) only on results > ~53k chars — i.e., the biggest tool contexts.

## Category scores: the crater is MEDIUM
| cat | nocap | np2 | Δ |
|---|---|---|---|
| Easy | 0.984 | 1.052 | −0.07 |
| **Medium** | **0.266** | **0.849** | **−0.58 ← the disaster** |
| Hard | 0.032 | 0.173 | −0.14 |
| **Total** | **0.416** | **0.684** | −0.27 |

nocap is worse than np2 in **all three** categories — the uncapped fuller-keep was a net negative everywhere — but Medium is the crater.

## Root cause: break rate jumped to 20% (np2 = 12.4%)
Per-RUN, on baseline-pass tasks (where −4 breaks live):
- **nocap: 29/145 break-runs = 20.0%**
- **np2:   18/145 break-runs = 12.4%**

That ~60% relative increase in breaks, concentrated on the big baseline-pass (= Medium) tasks, is what cratered M from 0.849 → 0.266.

## The breaks land on the biggest-context tasks, where nocap keeps the most
nocap broke 3 Medium tasks that np2 *passed* (`np2=pp → nocap=BREAK`), all large-context. Per-run pass rate + total context tokens kept/run:

| task | nocap pass | np2 pass | nocap kept/run | np2 kept/run | nocap vs np2 |
|---|---|---|---|---|---|
| sympy-23262 | **2/5** | 3/5 | 2.29M | 1.73M | **+32% kept, −1 pass** |
| django-12774 | **1/5** | 3/5 | 1.03M | 854k | **+21% kept, −2 pass** |
| django-11292 | **1/5** | 4/5 | 998k | 1.12M | −11% kept, −3 pass |

On 2 of the 3 (sympy-23262, django-12774), **nocap kept 21-32% more context and broke more runs** — direct support for "uncapped keep on big results hurts." The third (django-11292) kept *less* yet still broke more — so run-variance is also in play, not pure mechanism.

## Why does keeping MORE context cause MORE breaks?
The fuller-keep thesis ("more context → fewer breaks") is **refuted** on the real arbiter. Most plausible mechanisms, in order:
1. **More bulk = more to mis-navigate.** A bigger kept context gives the agent more surface to edit the wrong place → wrong patch → break.
2. **It's the BASE extractive (no import-pin).** nocap keeps *more low-value content* but can still drop the critical imports/structure (the verified break cause) — bulk without fixing the root cause. (This is exactly what `salience` targets.)
3. **Higher weighted tokens → lower savings.** nocap's mean weighted tokens ran +17-33% over np2 on the big tasks (874k vs 657k, etc.) → less savings bonus (minor, since savings ≈ 0.5pt).
4. **Run-variance** amplifies all of the above (django-11292).

## Conclusions
- **nocap is strictly worse than np2** — more breaks (Medium), fewer/cheaper flips (Hard), slightly lower Easy. The uncapped tail is a net negative. DISCARD.
- **The crater confirms the de-risking rationale for cap32** (cap the tail at 32k = np3's proven zone) and the **targeting rationale for salience** (pin imports/structure rather than just keeping more bulk).
- **Validated ranking: salience > cap32 > nocap** — but per the local-eval finding (CURRENT 09:55Z), only the *platform* can confirm cap32/salience actually beat np2. The prompt list is now frozen, so any such test must use the existing (compliant) markers — which cap32/salience do.
- Practical: with the prompt-freeze + both kings DQ'd, **we project 23.8% by holding np2/np3**. A cap32 spare-hotkey swing at Overall is the only forward option, and nocap's crater is a caution flag on that whole family.
