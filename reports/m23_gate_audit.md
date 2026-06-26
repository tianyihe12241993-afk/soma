# m23 RESOLVED-only break-fix — PRE-BUILD GATE AUDIT

_Date: 2026-06-25. Author: ops session (offline, read-only). Decision rule (user spec):
"If the resolved gate cannot separate Easy/resolved break-fix cases from flip/Hard cases,
do not build m23." / "If gate leakage is non-trivial, return NO-GO and do not build."_

## VERDICT: **NO-GO.** Do not build m23.

The conservative RESOLVED gate **cannot causally separate** settled-Easy break-fix turns from
flip-task turns. On a real comp-108 flip trajectory it leaks pervasively, and the only gate variant
that zeroed the leak did so by overfitting thresholds to 3 available flip tasks while *also* losing
real Easy gains. The "determinism pass" half of the plan is a confirmed no-op. The downside (cratering
the Hard 0.919 moat = our entire 4.8% income) is catastrophic and asymmetric against a "small"
(~45–55% odds) upside. **Hold m12.**

---

## What was tested

**Architecture (sound):** m22's `_harvest_build` is already parameterized — `use_extractive=False,
use_drop_span=False` ⇒ byte-identical to m12. m23 = gate those two flags: m22 break-fix on RESOLVED
turns, m12-exact everywhere else. Rich/passthrough/router untouched. The build itself is mechanically
clean. **The blocker is not the build — it is the gate.**

**Audit method (faithful offline replay):** simulated the platform connector-rewrite loop turn-by-turn
using m12's ACTUAL code (`/tmp/m23_gate_replay.py`, `/tmp/m23_gate_variants.py`), feeding each turn's
compressed output forward as the next turn's session, exactly as the platform does. At every turn we
recomputed m12's router signals (`mode`, `recent_errors`, `still_failing`, `msg_depth`, `escalation`)
and evaluated whether a candidate RESOLVED gate fires. Substrate = **real m12 trajectories on the real
comp-108 tasks** (native, uncompressed `session.jsonl` from `experiments/runs/`).

Caveat (stated honestly): local replay does not reproduce platform break *outcomes* (the m13/m20b-v2
trap). But the audit measures the gate's **firing pattern**, which is a property of trajectory shape
(does a flip task show clean/shallow/no-error windows during harvest?) — faithful, because it's the
same qwen3-coder agent on the same tasks, and the gate reads the same signals.

**Coverage:** 15 comp-108 tasks with saved m12 trajectories (≈150 runs). 3 flip tasks
(sympy-14976, sympy-18698, sympy-24066) + 2 Easy break-fix targets (django-14122, django-13810) +
the Hard-crater Pass target django-12050. **Not locally available:** the named Medium-flip craters
django-13925 / django-14017 and Hard-crater Pass sympy-16792 / django-15037 (audit gap — see below).

## The decisive result — flip leakage (fires must be 0 on flip tasks)

| Gate variant | sympy-24066 (Flip) | sympy-14976 (Flip) | sympy-18698 (Flip) | django-14122 (Easy✓) | django-13810 (Easy✓) |
|---|---|---|---|---|---|
| Lenient (recent_w8 clean, depth<70) | **217** | **2** | 0 | 16 | 192 |
| Strict (+ no error anywhere) | **104** | **2** | 0 | 16 | 137 |
| G3 resolution-sig (had≥2 err, then clean) | **70** | 0 | 0 | 0 | 21 |
| G5 res + no-early | **70** | 0 | 0 | 0 | 21 |
| G4 ultra-strict (depth<45, ≥3 err, last-10 clean) | **0** | 0 | 0 | **0** | 15 |

### Why it leaks (causal, not a tuning miss)
- **At an early harvest turn a flip task is signal-identical to a settled Easy task.** The agent
  hasn't run the failing test yet → no errors, recent window clean, shallow depth, no escalation.
  `sympy-24066` fires on rounds **3–10** (the earliest harvest turns) under the lenient gate.
- The "resolution signature" refinement (require errors-seen-then-clean, which early exploration
  can't fake) **still leaks 70 fires** on `sympy-24066`: a flip task genuinely passes through
  "hit-an-error → transiently-clean → still-shallow" windows mid-trajectory before it goes deep.
- **Only G4 zeroed the leak** — by tightening depth<45 ∧ ≥3 prior errors ∧ last-10-results-clean
  until `sympy-24066` happened to hit zero. That is **overfitting to 3 flip trajectories**, not a
  property. And G4 **fires 0 on django-14122** (a real Easy break-fix target) → even the flip-safe
  variant sacrifices part of the upside it exists to capture.

## Why no gate can be made safe here (the structural argument)
1. **Zero-sum under the mandated constraint.** The spec (correctly) requires m23 output ≤ m12 in
   BOTH chars AND tokens (prevents the m21 token-inflation crater). Under that ceiling, any content
   m23 *adds* (a kept error/diff span) must be *funded* by removing content elsewhere (kept-result
   detail / exploration). So firing is necessarily a content-class tradeoff (break-fix vs
   exploration) — exactly the antagonism that killed m22's flips.
2. **Propagation can't be undone.** `save_state` persists the compressed output; the connector feeds
   it back as the next turn's context. If a flip/Hard task is misclassified on ANY early harvest turn,
   the changed content is baked into the state rich reads later → Hard crater. There is no private
   state separate from output, so "decouple state from harvest" (option A) is not available to us.
3. **The gate is the only safety, and it is causal-blind to the one thing that matters** (whether the
   task will later become a flip/Hard trajectory). Empirically it leaks.

## The "determinism pass" half of option (b) — confirmed NO-OP
m12's compression path has **no randomness or time dependence** (`grep` for random/time/shuffle/now:
only `utc_now()` in `save_state` *metadata*, which never touches the output). m12 is already
deterministic given identical input. The king's lower −4-break variance therefore is **not** from
deterministic compression — it's the agent sampling fewer failing trajectories on the king's contexts
(content quality / behavior), which prior forensics already ruled outside our compliant reach
(run-variance = solver stochasticity). So there is no determinism lever to pull.

## Audit gap (honest)
The 4 most-relevant named tasks (django-13925, django-14017, sympy-16792, django-15037) have no local
trajectories. The verdict rests on the 3 available flips. However: (a) one of them (sympy-24066) already
leaks decisively under every non-overfit gate; (b) the leak is a *causal* property (early-exploration ≡
settled-Easy), so more flip data is overwhelmingly likely to confirm, not overturn, it. A targeted local
eval to capture those 4 trajectories is *possible* but not recommended — it would spend eval time to
harden a verdict the mechanism already makes clear. (If desired, it is the one thing that could change
the call.)

## Recommendation
**Hold m12 (the investigation's fallback (c)).** m12 overall 0.738 trails the king 0.755 ONLY on
consistency — a variance edge that is agent-side, not a compliant content lever. m12 beats every
candidate we've built (m17/m18/m20b-v2/m21/m22) and its Hard 0.919 is field-best (our entire 4.8%).
A 4th content-change attempt that risks that moat, on a threshold-fragile gate, is the malpractice the
investigation warned against. Three Hard craters (m18/m21/m22) + this leak audit = sufficient evidence.

## Artifacts
- Replay harnesses (read-only): `/tmp/m23_gate_replay.py`, `/tmp/m23_gate_variants.py`.
- Substrate: real m12 trajectories under `experiments/runs/*/m12__*/openclaw-gateway-state/agents/*/sessions/*.jsonl`.
- Baseline labels: `config/comp108_tasks.txt` (Pass/Flip per task).
- Build was NOT undertaken (NO-GO) → `m23_design.md` / `m23_verification.md` intentionally not produced;
  `upload_miner_m23.py` was NOT created. m12 LIVE file untouched.
