# All-methods review + recombination/reorder space (can mixing m12's stages reach the king?)

_2026-06-26. Dual-agent: Claude review below; Codex independently red-teams the recombination space + the crux._

## 1. How m12 IS composed (the pipeline + order of operations)
m12 is a **3-mode sticky router** + shared sub-mechanisms. Mode is chosen per turn and only ever ESCALATES
(passthrough → harvest → rich, never reverts):
- **ROUTER** (handle_assemble): `rich` if depth≥90 OR observed≥120k tok OR cumulative≥600k OR still_failing(depth≥40 & ≥4 recent error-results) OR prev=rich; else `harvest` if observed≥3k OR prev=harvest; else `passthrough`.
- **passthrough**: native, unchanged (cache-warm).
- **HARVEST (compress_structurally)** — ORDER: (1) classify pre-tail interactions oldest-first, flag error-bearing as `protected`, detect duplicates; (2) mark duplicate+droppable → `drop`; (3) escalation ladder, each step only if planned>target(8k): **drop** oldest droppable (unprotected first, protected last) until 0.75·target → **trunc2** (tighter caps) → **assistCap** → **tailCap**; (4) emit: dropped→remove+strip its tool-call; protected→**blind** truncate to 5k; trunc→**blind** head/tail 1000/400; tail→16k; abs→40k. Newest 2 untouchable. **Key traits: DROPS oldest, BLIND head/tail truncation.**
- **RICH (compress_gently)** — ORDER: (1) build exact-hash + near-dup registries newest-first → survivor; (2) **NEVER drops**, last 10 msgs byte-intact; (3) emit: exact-dup→`[[BLOCK]]` back-ref; near-dup(non-load-bearing)→back-ref; load-bearing→**extractive** to 30k; stale→**extractive** to 6k. **Key traits: NEVER-drops, dedup-via-backref, EXTRACTIVE (not blind), load-bearing kept full.**
- **Shared sub-mechanisms** (the reusable "parts"): `extractive_compress` (pin error/test/diff/sig/path lines + TF-IDF fill), `is_error_bearing`/`recent_errors`, the load-bearing allowlist, `active_paths`, dedup, loop-guard (markers only), dual-fingerprint state, orphan guard.

The "parts" that could be mixed/reordered: **DROP vs NEVER-DROP**, **BLIND-truncate vs EXTRACTIVE-truncate**, **dedup-for-drop-priority vs dedup-via-[[BLOCK]]-backref**, the **routing trigger** (size vs depth), the **escalation order**.

## 2. Every method tried (what component/order it changed → result)
| candidate | what it changed (vs m12) | result |
|---|---|---|
| m8-m11 (v15/18/22/24) | ADDED flip/persistent-fail routing | leaked Medium, broke baselines — DEAD |
| **m12 (LIVE)** | the baseline composition | **0.768, wins Single-H** |
| m13 | SOFTER harvest (aggression cap + gentler routing) | Hard 0.919→**0.434** — DEAD (soften) |
| m14/m15 | never-inflate guard only | m14 key-confounded; never-inflate ≈ neutral |
| m16 | cleaner compression (fewer artifacts) for Easy | MORE agent steps — DEAD |
| m17 | BLIND→EXTRACTIVE truncate in harvest (trunc sites only) | NOT QUALIFIED (screener break) |
| m18 | size-gated ultralight on shallow turns | broke early-Hard — DEAD |
| m19 | cache-stable (freeze truncation depth) | churn not reduced; M/H lighter — DEAD |
| m20/m20b/m20b-v2 | drop redundant superseded file-views | wander / net −2.67, dented Hard — DEAD |
| m21 | keep-MORE harvest (lighter + retention class) | neutralized + Hard 0.461 — DEAD |
| m22 | EXTRACTIVE truncate + DROP-SPANS + reconciliation | 0.672: killed flips + Hard crater — DEAD |
| m24 / depth-gate | routing trigger: widen passthrough (size / depth) | Easy↔Hard overlap — NO-GO (offline) |
| loopguard | tune loop-detection threshold | saturated, no-op — NO-GO (offline) |
| **m23/m25 (QUEUED)** | extractive-trunc + RESOLVED-gate + DECOUPLED state | the live coin-flip — in queue |

## 3. The recombination / reorder space — TRIED vs UNTRIED, each vs the 3 walls
The 3 walls that bound EVERY recombination: **(W-NS)** E/M/H non-separable by any compliant per-call signal → can't target a category; **(W-HC)** any HARVEST content change feeds rich/Hard via save_state → craters Hard/flips; **(W-CONS)** the king's edge is agent-side consistency, not a compression recipe (below).
| recombination / reorder idea | status | verdict vs walls |
|---|---|---|
| extractive (rich) INTO harvest | TRIED (m17/m22/m25) | DQ'd / killed flips / coin-flip. Hits W-HC. |
| keep-more / never-drop INTO harvest | TRIED (m21) | Hard crater. Hits W-HC. |
| reorder: extractive-before-drop (keep span on dropped) | TRIED (m22 drop-spans) | killed flips. Hits W-HC. |
| rich's [[BLOCK]] dedup-backref INTO harvest (vs dropping dups) | ~UNTRIED | = keep-more direction → W-HC (maps to m21). |
| rich-EVERYWHERE (drop the harvest mode) | TRIED (v9/v10 lineage) | forfeits pass-task token bonus → why v11 ADDED harvest. Known regression. |
| harvest-EVERYWHERE (drop rich) | ≈TRIED (m13 soften) | rich exists for deep-Hard flips → Hard collapse. |
| different escalation ORDER (truncate-harder before drop) | ~UNTRIED | content change → W-HC + W-NS. Same wall. |
| route Medium→rich (mix routing) | UNTRIED | can't identify Medium (W-NS). |
| stability-via-compression (cache-stable mix) | TRIED (m19) | breaks are first-decision solver stochasticity, NOT churn — dead. |

**Finding:** every MAJOR recombination either maps onto a tested lever, is a known regression, or hits the same 3 walls.
The combination space is not literally exhausted, but it is BOUNDED — no reordering of compression stages escapes W-NS/W-HC,
and none produces W-CONS (consistency).

## 4. THE CRUX — "the king has a high score, why can't we reach it?"
Decomposed from per-run data (re-derived by both models): **the king's 0.957 vs our 0.768 is NOT a better compression
algorithm.** The king TIES us on ratio (1.61×), is WORSE than us on Hard (0.727<0.919) and on flips. Its ONLY edge is
**run-to-run CONSISTENCY**: it emits **6 break-runs vs our 17**, and has **24 all-5-pass tasks vs our 18**. Consistency =
the qwen3-coder agent sampling fewer failing trajectories on the king's contexts. **No mix or reorder of compression stages
produces consistency**, because compression is not what causes it — m12 is already deterministic, and the −4 breaks are
first-decision SOLVER stochasticity (proven, m19/forensics), not compression churn we can re-stage away. And we are BANNED
from steering the agent (compliant prompting = markers + loop-detection only). So: we are not failing to find the right
recipe — **the king's advantage is not a recipe.** Mixing/reordering changes WHICH content we keep (bounded by W-NS/W-HC);
it cannot change how often the agent fails (W-CONS), which is the entire gap.

## 5. CODEX — your red-team
1. Independently verify §4 (the crux): from the per-run JSON, is the king's edge consistency (fewer breaks) and NOT ratio/
   content/flips? Re-derive break counts + ratio.
2. Attack §3: is there a SPECIFIC mix/reorder of m12's stages (or a NEW stage from the existing parts) that plausibly
   escapes all 3 walls and could reach the king — that this review missed? Be concrete (name the stages + order). If you
   can construct one, give its mechanism + which wall it escapes + EV. If not, say so.
3. Sanity-check the walls themselves: is W-CONS truly unreachable by any COMPLIANT means (e.g., could a compression choice
   indirectly reduce agent failure-rate without steering)? This is the highest-value question — push hard on it.

---

## Codex red-team result + Claude reconciliation (2026-06-26)
**(A) Crux QUANTIFIED (Codex re-derived from per-run JSON — sharpens our claim):**
- m12 17 breaks (6.8%) vs king 6 (2.4%) = **11 extra m12 breaks** [matches our counts].
- Break-removal counterfactual: replacing m12's 11 extra −4s with m12's own passing mean (1.638) = **+0.248**, which
  OVERPOWERS the actual gap **+0.189** → residual **−0.059**. ⇒ **if m12 matched the king's break rate, m12 would EXCEED
  the king on everything else.** The gap is 100% breaks; there is NO second source.
- SMOKING GUN: on the 38 tasks where NEITHER breaks, m12's passing mean (1.638) is HIGHER than the king's (1.564), and m12
  has more HIGH-score runs (96 vs 81). **Our compression is BETTER; the king only wins by breaking less.**
- King's lower weighted tokens (457K vs 650K) = EFFECT of fewer breaks (break-runs are long/token-expensive), NOT a cause
  (ratio ties 1.61×). Rules out "king goes lighter → more context → fewer breaks."
**(B) Recombination verdict — Codex worked 7 specific reorders (harvest-first, rich-first, merge-modes, blind→extractive,
selective-drop-in-rich, remove-stickiness, [[BLOCK]]-dedup-in-harvest); EVERY one maps to a tested lever / known regression
/ hits W-NS or W-HC. The most interesting untried ([[BLOCK]] dedup in harvest) → reduces to m25's decoupling. NONE escapes
beyond m25.** Confirms §3.
**(C) W-CONS ruling (the key refinement):** consistency is **PARTIALLY content-reachable** by COMPLIANT means — preserving
the diff-hunk/test-assertion that BLIND truncation currently deletes can keep the agent oriented → fewer breaks (NOT
steering, just better information). This is **exactly m25's mechanism.** It is NOT (c) frozen-eval luck (the 7-task
m12-breaks/king-consistent asymmetry is too large across independent evals); NOT purely (b) banned task-awareness (the
mechanism exists in principle). BUT bounded to a ~20-30% coin-flip by: W-NS zero-sum (better content for a break-prone task
destabilizes a structurally-identical PASSING task — the m22 +new-breaks finding), and first-decision SOLVER stochasticity
(even better content may still fail 1-2/5). So the consistency wall is NOT absolute — m25 attacks it directly.
**(D) Action:** run m25 (already queued) — the one recombination that partially escapes the walls and directly targets the
100%-breaks gap. **Claude amendment to Codex's success criterion:** keep our STRICTER gate Hard≥0.919 (Codex proposed ≥0.85;
too loose — we don't dent the moat); promote only on Medium↑ ∧ Hard≥0.919 ∧ flips≥m12.

## REVISED CRUX ANSWER (both models, for the user)
"Why can't we reach the king?" = **we break 11 more times than the king out of 250 runs; that is the ENTIRE gap** (remove
it and we'd win). Breaking less is PARTIALLY reachable by better content selection (m25's extractive+decouple) — it is NOT
an unreachable agent-luck moat — but it's bounded to a coin-flip because helping break-prone tasks risks destabilizing
structurally-identical passing ones (non-separable) + residual solver stochasticity. **No mix/reorder we haven't tried
changes this; m25 is the live shot at the one mechanism that moves the gap.**
