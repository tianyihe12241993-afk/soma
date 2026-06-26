# m12 algorithm cons + strategy verdict (2026-06-25, workflow wie3sqfl0)

## PART 1 — m12 ALGORITHM CONS (ranked; mechanism / impact / fixable)
1. **CON1 (CRITICAL, fixable) — harvest routing is UPSIDE-DOWN.** All guards push hard tasks → rich (safe);
   nothing pushes small/resolved tasks toward LESS compression. Short tasks above the 3k passthrough cliff land
   in the MOST aggressive mode (harvest). Hard (already winning) gets the safe mode; the harvest band gets the
   riskiest. Root cause of low Easy + DQ exposure. FIX = graduated "small/resolved → gentle truncate-only, never-
   drop" band. **m21 does this.**
2. **CON2 (HIGH) — still_failing guard fires on bare substrings** ("0 failed", "errors=0" trip it), irreversible
   (sticky, no decay); over-fires on verbose-test Medium → forfeits Medium harvest bonus; 20k window blinds it to
   end-of-log failures. FIX: structured failing-test patterns + hysteresis.
3. **CON3 (HIGH) — monotonic mode ratchet never reverts** → one transient spike permanently mis-modes a task,
   leaks Medium into rich. FIX: hysteresis/decay (stickiness was for cache = dead lever).
4. **CON4 (HIGH, 1-line fix) — pressure-relief over-prunes 25% below budget** (relief=0.75×target) for a CACHE
   benefit that doesn't score. Pure over-compression tax. FIX: relief_chars=target_chars. **m21 does this.**
5. **CON5 (HIGH) — tail_cap/assist_cap truncate the LIVE working tail** (the 4 newest results + assistant tool-call
   args the agent is actively using). FIX: never truncate active tail; extractive (not blind) on assistants.
6. **CON6 (theory CRITICAL, magnitude UNVERIFIED) — whole-interaction drops oldest-first, no dependency analysis,
   no trace.** BUT red-team: the "65% breaks on hard-compressed runs" claim is NOT supported by comp-108 per-run
   data, and no category map confirms it drives Easy. Real smell, unproven impact. **m21 addresses (never-drop).**
7. **CON7 (MED-HIGH) — blind head/tail truncation in harvest; the good extractive summarizer is RICH-ONLY.** FIX:
   route harvest truncation through extractive_message (= m17/m21).
8. CON8 — near-dup collapse strips ALL digits (numeric assertions collapse) — hurts sympy Hard.
9. CON9 — prefix-match miss carries stale escalation onto fresh full trajectory.
10. CON10 — orphan guard baselines vs our own prior output, not raw → self-inflicted orphan can ship → DQ risk.
11. CON11 — transitive dup-chain → pointer-to-pointer; back-refs point forward.
12. CON12 — budget estimate ignores tool-call arg JSON → escalation mis-decides toward break-prone levers.

## PART 2 — STRATEGY VERDICT
- **GREATEST absolute = triple-threat (E-high, M-solid, H-solid) → wins Overall (57.1%).** Hinges on EASY (77% of
  our 0.194 Overall gap to king is Easy). For us: need Easy 0.412→~0.994 just to TIE → INFEASIBLE + DQ-prone. REJECT.
- **Pair(M,H) is the WRONG target for us** (red-team correction to the earlier preliminary read): needs Medium
  0.953→1.089, but pass-pass CAPS a category at ~1.0 → break-elimination CAN'T reach it; only NET-NEW FLIPS can =
  the risky/unvalidatable/upside lever. Knife-edge (avg 1.0040 vs king 1.0041; a 0.05 Hard slip or 0.036 Medium
  shortfall → zero) AND moat-correlated downside. REJECT.
- **BEST FOR US = Pair(E,H) = 14.29% (3× our 4.76%).** Needs Easy 0.412→≥0.731 (target ~0.78 buffer) holding Hard
  ≥0.919. Runs on the SAFE, UNCAPPED lever: Easy=baseline-passing → every point from NOT breaking (−4→+1), no flips,
  no 1.0 cap; does NOT touch Hard; Easy also feeds Overall (future upside). m21 IS this strategy, built.
- **RECOMMENDED two-track:** (1) DEFEND Single-Hard (hold m12 LIVE, guaranteed 4.76%, near-zero variance; any
  candidate must clear Hard≥0.919). (2) PURSUE Pair(E,H) via break-reduction = m21, gated on the board.

## ★ DECISIVE HONEST CAVEAT
The "Easy = m12 breaks baseline-passing tasks" causal story is **UNVERIFIED against comp-108 data**: the category
CSV covers task_ids 217-266 (comp-107), the scored per-run files cover 267-316 (comp-108) → ZERO overlap, so we
don't know which scored tasks are Easy. The per-run evidence we DO have shows (a) "65% breaks on hard-compressed
runs" is FALSE here, and (b) m12 and king break the SAME tasks (django-12039: m12 3/king 3) → breaks may be
substantially TASK-INTRINSIC (why every compression-aggressiveness fix died). So m21's premise is UNCERTAIN.
BINDING ACTIONS: (1) ship NOTHING blind — promote m21 only on ≥3 scrapes showing noise-clearing Easy/(E,H) gain +
Hard≥0.919, first signal = does it stop breaking django-11551 (the m17 DQ task). (2) BUILD THE COMP-108 CATEGORY
MAP (join scored per-run task_names 267-316 to platform E/M/H) before trusting any Easy-targeted number.
