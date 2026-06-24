# m12 pass/fail trajectory forensics — why same-task runs diverge (2026-06-24, analysis-only)

Question (provider ruled out): on m12 broken pass-pass tasks, why do some runs pass and others hit −4, at the
SAME provider/model/compressor? Hypothesis to test: a fail run loses a critical context/action pattern that a
task-agnostic preservation rule could restore. NO build, NO submit, m12 untouched.

## 1. SUMMARY VERDICT: run-variance is SOLVER STOCHASTICITY, not compression-caused → REJECT a miner change.
Trajectory comparison of same-window pass vs fail runs shows the fail runs are NOT missing compressed-away
context — they fail by taking a worse stochastic ACTION path (premature patch on one task, wandering on another),
with adequate or MORE context in hand. The failure archetypes are HETEROGENEOUS (opposite across tasks). This
satisfies every reject criterion: heterogeneous, no shared missing-context pattern, divergence is solver-random
not compression-caused. **No task-agnostic preservation rule is justified.**

## 2. Target tasks (data availability)
Local m12 pass+fail trajectory pairs exist ONLY for **django-13810** and **django-12039** (both ran m12 in the
m17 A/B, run 060037, same provider window — ideal: same task/window/compressor, opposite outcome). The other
four requested targets (django-11740, sympy-14531, django-11095, sympy-20590) have **no local trajectory** — they
are platform-only, and the platform scrape is summary-only (score/steps/tokens/pass; NO tool calls or patches).
So forensic depth is limited to the two tasks with local pairs; verdict triangulated against all prior evidence.

## 3-4. Per-task pass vs fail trajectory + first divergence
**django-13810** (m17 A/B 060037):
| run | result | tools | tokens | first_edit | pattern |
|---|---|---|---|---|---|
| r3 | PASS | 36 | 447k | step 5 (after 3 reads + GitHub-source fetch) | inspect → edit iteratively → 4 test files run |
| r1 | FAIL | 24 | 321k | **step 2 (after 1 read)** | premature edits (8), 1 test file, stops early |
First divergence = **step 2**: pass keeps reading + fetches the canonical Django source; fail jumps straight to
editing. Same starting context → different action choice.

**django-12039** (m17 A/B 060037):
| run | result | tools | tokens | first_edit | pattern |
|---|---|---|---|---|---|
| r1 | PASS | 38 | 539k | step 18 | inspect, edit, verify; concise |
| r4 | PASS | 43 | 646k | step 7 | — |
| r3 | FAIL | **56** | **955k** | step 15 | **wanders** — 9 reads in first 10 steps, ~50% more work |
| r5 | FAIL | **58** | **986k** | step 11 | wanders (consistent with r3) |
First divergence = the fail runs explore MORE (more reads, more total tokens) and still fail — opposite of 13810.

## 5. Missing-context analysis — the hypothesis is REFUTED
Neither fail mode is missing compressed-away context:
- django-13810 FAIL had the target file (read it at step 1) and edited it — it failed by patching prematurely,
  not by lacking the file/test/traceback.
- django-12039 FAILs read MORE files and used MORE tokens than the passes — they had MORE context, not less.
So none of archetypes A-E (missing test name / traceback / file / prior result / diff) is the cause. The fail
runs had what they needed; they chose worse trajectories.

## 6. Compression / tokens / cache comparison
m12 compresses each run deterministically from its (different) trajectory. Fail runs do NOT show less context or
worse cache — django-12039 fails carry MORE tokens (wander), django-13810 fail carries fewer only because it
stopped earlier. Compression is a function of the trajectory, not the cause of divergence; the divergence
originates in the agent's action sampling at the first decision point.

## 7. King / 5DtEz comparison — NOT POSSIBLE from available data
We have no local runs of the king or 5DtEz, and the platform scrape exposes only per-run SUMMARY (score, steps,
tokens) — no tool sequences/patches. So "do they preserve a pattern m12 loses / take a different first action"
CANNOT be answered. Summary-level only: across all tasks the king has fewer −4 runs (6 vs m12's 16) at the same
ratio/steps — but whether that's a compression bias or window/sampling luck is undeterminable without their
trajectories. (Given the m12 evidence that breaks are solver-stochastic, the king's edge is most consistent with
sampling/window luck or an unreplicable behavioral bias — not a preservation rule, since m12's fails aren't
missing context.)

## 8. Failure archetype classification
- django-13810 FAIL: **G (premature patch) + J (too short)**; root cause **L (stochastic solver variance)** —
  the agent sampled "edit now" after one read.
- django-12039 FAIL: **K (too long / wandering)**; root cause **L** — the agent sampled an exploratory path that
  burned 50% more steps/tokens without converging.
Within-task consistency confirmed (both django-12039 fails wander 56-58 tools; the pass runs are 38-43).

## 9. Global patterns — NONE (heterogeneous)
The two tasks fail by OPPOSITE mechanisms (premature-short vs wander-long). There is NO repeated missing-context
pattern (A-E all absent). The only common factor is the root: solver-trajectory stochasticity (L). A single
task-agnostic rule cannot fix opposite failure modes — preserving more context would not stop a premature patch
(13810 already had context) nor a wander (12039 already had more).

## 10. Proposed safe invariant rule — NONE
No invariant-preservation rule is justified. The reject conditions are all met (heterogeneous, no shared
missing-context, solver-random). Any preservation rule would (a) not address the actual cause (action sampling),
and (b) risk perturbing Medium/Hard trajectories — exactly the m17/m18 failure family.

## 11. RECOMMENDATION: REJECT further miner change → HOLD m12
m12's pass-pass run-variance is the qwen3-coder agent's inherent stochasticity (some runs patch too early, some
wander) — NOT a compression defect, NOT missing context. A compliant compressor cannot fix it: it can't steer the
agent, can't add attempts, and context is not the bottleneck. This closes the loop on every prior result (depth,
m17 selection, m18 adaptive-light, 5DtEz break-relocation all failed because they targeted compression, while the
cause is the solver). **HOLD m12.** The run-variance headroom (the 17 broken pass-pass tasks) is real but NOT
ours to capture via compression. Monitor only.
