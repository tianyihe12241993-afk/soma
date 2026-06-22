# H1M_m7_deeper_safe_v1 — candidate evaluation
_computed 2026-06-22T00:25:31Z. DERIVATIVE of m7/v11.1; research only, NOT submitted._

## What changed vs m7 (exact)
A single **profile layer** (`experiments/candidates/H1M_m7_deeper_safe_v1/h1m_miner.py`) overrides ONLY the HARVEST-path knobs; the RICH path, all protections (load-bearing results, ERROR_MARKERS, active paths, recent-intact window, digest path-preservation) and the coach are untouched. Compression is deepened purely algorithmically — no routing, no flip, no rich-rescue, no task-ID logic.

| knob | m7 | light | medium | deep |
|---|---|---|---|---|
| TARGET_TOKENS | 8000 | 7000 | 6000 | 5200 |
| MID_HEAD/TAIL | 1000/400 | 850/350 | 650/280 | 520/220 |
| MID2_HEAD/TAIL | 500/200 | 450/180 | 380/160 | 320/140 |
| ASSIST_HEAD/TAIL | 1200/300 | 1000/280 | 850/250 | 700/220 |
| TAIL_RESULT_CAP | 16000 | 13000 | 11000 | 9000 |
| ERROR_GUARD_MIN_HITS (fragile guard) | 4 | 3 | 3 | 3 |

Fragile guard: a still-failing / error-dense recent window routes to the m7 RICH path one hit sooner than m7 — borderline fragile tasks fall back to m7 behaviour automatically.

## Offline result (compression ratio + structural safety; harvest-vs-harvest)
| variant | mean Δratio vs m7 | ~est score lift | improved | regressed | protected kept | pairing ok | guard fired |
|---|---|---|---|---|---|---|---|
| m7/v11.1 | +0.0% | 0.0 | 0/7 | 0 | True | True | 0 |
| h1m@m7 | +0.0% | 0.0 | 0/7 | 0 | True | True | 0 |
| h1m@light | +2.6% | 0.013 | 6/6 | 0 | True | True | 1 |
| h1m@medium | +10.8% | 0.051 | 6/6 | 0 | True | True | 1 |
| h1m@deep | +13.7% | 0.063 | 6/6 | 0 | True | True | 1 |

**A/B sanity:** `h1m@m7` reproduces m7 exactly (+0.0%, 0 changed) → the profile system is a clean no-op at baseline.

## Per-case ratio (m7 vs h1m@deep)
| case | m7 ratio/mode | h1m@deep ratio/mode | note |
|---|---|---|---|
| sample-1 | 1.033/harvest | 1.033/harvest | passthrough (too small) |
| sample-2 | 1.127/harvest | 1.354/harvest |  |
| sample-3 | 1.324/harvest | 1.498/harvest |  |
| sample-4 | 2.913/harvest | 3.005/harvest |  |
| sample-5 | 1.138/harvest | 1.261/harvest |  |
| synth-clean-large | 6.694/harvest | 7.889/harvest |  |
| synth-clean-big | 7.887/harvest | 9.219/harvest |  |
| synth-errdense-fragile | 6.69/harvest | 1.522/rich | fragile guard → rich (conservative) |

## What is measured vs PENDING
- **Measured offline (real):** compression ratio, protected-content preservation, toolCall/toolResult pairing, fragile-guard behaviour. h1m@deep deepens compression on 6/6 clean harvest cases (+13.7% mean) with **zero** regressions, **all** protected markers retained, **no** broken pairing.
- **PENDING_EVAL (cannot do offline):** real platform pass-rate, negative-run rate, broke-baseline, Medium category score. These need the SOMA SWE-bench eval (Docker+agent+OpenRouter). Not invented.
- **PENDING:** ratio on the actual H1 target SWE-bench tasks (django-15851 etc.) — needs their real trajectories (only available in the eval env). Targets remain the evaluation PRIORITY.

## Decision
- **Best profile: h1m@deep** (+13.7%, 0 regressions, all safety checks pass), with **h1m@medium** (+10.8%) as the safer fallback.
- **Do NOT promote to base yet.** Acceptance requires Medium pass-rate / neg-run from the platform eval. The candidate is pass-safe BY CONSTRUCTION (protections + fragile guard verified) but that is a proxy, not proof.
- **Next:** run h1m@deep + h1m@medium through the SOMA eval on the H1 safe targets (Medium-first), then `run_experiment_matrix.py --results <file>` → gate in experiment_backlog.md.

## H1 evaluation-priority targets (Medium-first)
django-15851, django-11119, sympy-24539, django-14580, django-14855, django-10914, django-11603 (Medium); django-16255, django-13741 (Easy); django-14752 (Hard). Guard signatures: sympy-17139 (+ flip-only sympy-16766 / django-11239 / django-14493). Out of scope (solving gaps): django-14999, sympy-22714.

## Real-task experiment — Medium-first targets (2026-06-22)
Runner: `h1m_run.py` → `experiments/runs/<stamp>_H1M_eval/`. Basis: REAL m7 baseline (platform scrape)
+ OFFLINE candidate proxy/projection. Candidate real pass-rate/neg-run/broke = **PENDING_EVAL** (needs SOMA
SWE-bench; raw per-call task contexts unavailable offline — not invented).

**m7 baseline on the 7 Medium-first targets (REAL):** pass 7/7 (1.00) · negative-run rate 0.0% (all 0/5) ·
broke-baseline 0 · negative-score 0 · avg ratio **3.02×** · Medium est score (mean) **1.690**.

Per target — m7 ratio → projected h1m@deep (×1.137): django-14580 4.69→5.34 · django-14855 3.44→3.91 ·
django-10914 2.81→3.20 · django-11119 2.68→3.05 · django-11603 2.65→3.01 · sympy-24539 2.50→2.85 ·
django-15851 2.33→2.64 (all m7 pass, 0/5 neg).

| profile | offline ratio Δ | proj Medium-first ratio | est score Δ/task | protected | guard | real pass/neg |
|---|---|---|---|---|---|---|
| h1m@medium | +10.8% | ~3.34× | +0.051 | True | fires (offline) | PENDING_EVAL |
| h1m@deep | +13.7% | ~3.43× | +0.064 | True | fires (offline) | PENDING_EVAL |

**Fragile group** (sympy-17139, sympy-16766, django-11239, django-14493): m7 baseline — only sympy-17139
breaks (2/5); the rest are flip-only (m7 clean). Candidate: guard (ERROR_GUARD_MIN_HITS=3) routes these to
the m7 rich path → no deeper compression; offline harness confirmed the guard fires. Verify on eval.

**Decision gate:** compression ≥8% **PASS** (deep +13.7%) · guard works **PASS** · Medium est score no-drop
**PASS (projected)** · new broken baseline **PENDING_EVAL** · Medium neg-run increase **PENDING_EVAL** →
**ADVANCE (candidate-only); do NOT promote to base until the SOMA eval supplies real pass-rate/neg-run.**

_Note: this section's run-dir artifacts + the checkpoint were queued behind a temporary command-classifier
outage (2026-06-22); run `h1m_run.py` then `checkpoint_session.py` to materialize them._
