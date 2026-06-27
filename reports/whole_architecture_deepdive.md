# Whole-architecture deep-dive — "leave m12, is the architecture itself the ceiling?" (2026-06-26)

_User reframe: every candidate (m13→m27) was "m12 + a lever"; every wall was derived INSIDE m12. Step back: is m12's
architecture the ceiling, or just a local optimum? Re-derived from raw per-run JSON (data/raw/platform_results/2026-06-24/
{m12_5Dz7,newking_5Ggq,5DtEz}_perrun.json). All totals reproduce the board to 3 dp (m12 0.768 / king 0.957 / 5DtEz 0.714)._

## 0. Two corrections to the prior report-chain (re-derived from raw runs, 250 runs each)
| miner | mean | BREAK | FLIP | pass-pass | fail-fail |
|---|---|---|---|---|---|
| m12 | 0.768 | **17** | 16 | 152 | 65 |
| king 5Ggq | 0.957 | **6** | 17 | 161 | 66 |
| 5DtEz | 0.714 | 13 | 11 | 153 | 73 |

1. **Flips are TIED, not an m12 edge.** m12 16 vs king 17 flip-runs; they share 6 of 7-8 flip-tasks with near-identical
   per-task strength. The chain's "m12 out-flips the king / king doesn't preserve flips" was overgeneralized from ONE task
   (dj-14017: m12 3/5 vs king 1/5). Overall the king flips ≥ us. **We have no flip advantage to defend.**
2. **The gap is 100% breaks, re-confirmed:** king avoids 11 of m12's 17 breaks; pass-pass delta (+9) is mostly those
   avoided breaks; fail-fail tied (65≈66). Converting 11 breaks (−4) to pass-pass (~+1.3) ≈ +0.23/run > the +0.189 gap.

## 1. The break tasks are HIGH-VARIANCE, not failures (the key structural fact)
m12's 17 breaks sit on 10 tasks. On 7 of those 10, **m12 already passes 3/5 or 4/5** — they are wobbly, not lost. The
king passes 5/5 on 7 of the 10. Pass-count distribution (per-task # passing runs /5):

| #pass/5 | m12 | king | 5DtEz |
|---|---|---|---|
| 5/5 (deterministic win) | 18 | **24** | 21 |
| 1–4/5 (HIGH-VARIANCE, re-rollable) | **25** | 20 | 23 |
| 0/5 (deterministic loss) | 7 | 6 | 6 |

**The king's entire edge = converting ~5-6 of m12's high-variance tasks into deterministic 5/5.** It does this at NO
consistent token strategy: on m12's 10 break-tasks the king is 1.05× (near-passthrough) on dj-11551, 2.18× (compresses
MORE than m12) on dj-11095, and on sy-15349 m12 INFLATES (0.66×) while the king compresses. Aggregate ratios TIE (both
1.61×). **There is no "king keeps more context → fewer breaks" recipe — the token data refutes it.**

## 2. The frontier is EMPIRICAL across the whole field — not an m12 limitation
Every miner that is good at Easy PAYS somewhere; NO miner in the field has high E AND M AND H at once:
| miner | E | M | H | wins | what it sacrificed |
|---|---|---|---|---|---|
| **m12 (ours)** | 0.412 | 0.953 | **0.919** | Single-H | **Easy** (Hard vertex) |
| king 5Ggq | 0.858 | 1.281 | 0.727 | Overall+E,M+M,H+E+M | **Hard** (Easy/Medium vertex) |
| 5DtEz | 0.837 | 0.499 | 0.813 | Pair(E,H) | **Medium** (E/H vertex) |
| 5GCWaCnb | 0.923 | — | — | Single-E | (Easy vertex) |
| 5DCnA57 | eff 0.528 | 1.120 | eff 0.168 | none (penalty-capped 0.701) | over-light → savings penalty |
| m25 (ours) | 0.859 | 0.667 | 0.536 | — | **Hard** (= m12 + perturbation) |

**The king — the field's #1, a very well-tuned miner — tops out at Hard 0.727.** If IT can't hold Hard while winning
Easy/Medium, the E↔(M,H) tradeoff is a property of the task distribution + scoring + banned-steering, NOT an m12 defect.
"Leaving m12" does not unlock a better single architecture, because the frontier binds ALL architectures.

## 3. What "leave m12" DOES correctly unlock: the m24 NO-GO answered the wrong question
- m12 is the CORRECT choice for the **Hard vertex** (field-best Hard, +0.107 cushion). Keep it there.
- The growth move is not "improve m12" — it's **add specialists at OTHER vertices** (portfolio = MAX per element).
- **5DtEz proves E0.837 + H0.813 CAN coexist (Pair E,H = 0.825).** The earlier m24 EH-passthrough NO-GO required
  "Hard-routing == m12 (preserve 0.919)" — but **winning Pair(E,H) only needs the pair > 0.825, which 5DtEz does at Hard
  0.813.** Anchoring on m12's Hard made us reject a target that does NOT require m12's Hard. The reframe legitimately
  REOPENS Pair(E,H) (9.5%, double the Single-E play's 4.76%).

## 4. BUT 5DtEz is the SAME tradeoff — damage just landed on Medium, not Hard (the catch)
Dissecting 5DtEz vs m12 per task: its gains are the same break-prone tasks (dj-11740 −0.93→1.17, sy-14976 −0.76→1.11),
and its losses are the SAME signature as m25 — it **kills flips** (dj-14017 3/5→1/5, dj-13925 3/5→1/5, sy-18698 3/5→1/5)
and makes new breaks (dj-13033 4/5→1/5). 5DtEz is m12 + a perturbing Easy lever, identical in kind to m25. The ONLY
difference: **5DtEz's collateral damage fell on Medium (M0.499) and spared Hard (0.813); m25's fell on Hard (0.536).**

**The open question that decides Pair(E,H) (load-bearing, for Codex):** is "damage lands on Medium, spares Hard" a
STRUCTURAL property of 5DtEz's mechanism (→ replicable → build it) or a per-eval DRAW (→ luck → our clone's damage could
land on Hard like m25's did, giving E0.85/H0.55 = pair 0.70, LOSE)? We have ONE data point on OUR mechanism (m25) and its
damage landed on HARD. W-NS says we can't STEER which category the damage hits. So absent a structural reason, the base
rate says our E/H clone craters Hard, not Medium.

## 5. Resolved en route: does m12 ALREADY own Pair(M,H)? — NO.
The chain flagged king Medium as maybe 0.909 (per-run reconstruction) vs 1.281 (board). The board TOTAL settles it:
mean(0.858, 1.281, 0.727) = 0.955 ≈ board 0.957 ✓; mean(0.858, **0.909**, 0.727) = 0.831 ≠ 0.957. **King Medium really is
~1.281**, king's (M,H) pair ≈ 1.004 > m12's 0.936 → king owns Pair(M,H); **m12 is clean #2** (passive capture only if king
H re-draws low). The 0.909 reconstruction was wrong (likely old-king misattribution). No free element here.

## 6. VERDICT (Claude, pre-Codex)
- **The architecture is NOT the ceiling in the sense of "a better single miner exists" — the frontier binds the whole
  field (king caps at H0.727).** The reframe's literal hope (a from-scratch miner that beats the king on Overall) is
  blocked by the same E↔(M,H) tradeoff, now proven field-wide, not just on m12.
- **The reframe IS right that we were anchored wrong:** stop trying to make m12 do Easy; own multiple vertices. m12 = Hard
  vertex (keep). Reachable additions: **Single-E (m26, reliable, +4.76%)**; **Pair(E,H) (5DtEz's vertex, +9.5%) — a
  bigger prize that the m24 NO-GO wrongly foreclosed, BUT contingent on the §4 question (damage-to-Medium structural vs
  luck), where our one data point (m25) says our damage hits Hard.**
- **Single best next move:** the m26 build TARGETS Single-E (reliable) and gets Pair(E,H) as a lottery upside IF its Hard
  happens to hold. Same build, two possible elements. No new wall; no m12 risk (separate hotkey).

## 7. CODEX — independent red-team (Gate 2 + Gate 3)
1. **Re-derive §0/§1 from the raw JSON** — break/flip counts, the high-variance pass-count distribution, and the
   no-consistent-token-strategy finding. Confirm or refute "gap = 100% breaks; flips tied."
2. **§4 is the decision:** from 5DtEz's per-run/per-task data, is its "damage lands on Medium, spares Hard" STRUCTURAL
   (a mechanism we could replicate → Pair(E,H) buildable) or a per-eval DRAW (→ our clone likely craters Hard like m25)?
   This single question decides whether Pair(E,H) is worth a hotkey or is m27-style NO-GO. Push hard.
3. **Attack §2** — is there ANY field miner (use /tmp/miner_1..10.json if labelable) with E≥0.7 ∧ M≥0.7 ∧ H≥0.7
   simultaneously? If even one exists, the frontier claim is wrong and Overall is back on the table. If none, the frontier
   is confirmed empirically.

---

## 8. Codex red-team result + reconciliation (2026-06-26, agent ae75807e)
**Task 1 (diagnosis) — CONFIRM all 4 sub-claims, independently re-derived:** m12 17 / king 6 / 5DtEz 13 breaks; flips
m12 16 ≈ king 17 with 6 shared flip-tasks (267-set: 280,290,296,303,306,311) → m12 has NO flip edge; m12's breaks sit on
high-variance tasks (7/10 m12 passes 3-4/5) the king converts to 5/5; king/m12 token-ratio on break-tasks ranges 0.45–1.72
= no recipe. **§0/§1 stand. Both models agree the gap is break-avoidance, not flips or a token strategy.**

**Task 2 (Pair(E,H)) — Codex HARDENS my §4 catch to a firm NO-GO.** 5DtEz vs m12: E +0.425 / M −0.455 / **H −0.106 (Hard
is NOT untouched)**; per-task 26 up / 24 down, net −0.055; it adds NEW breaks (tasks 269, 285) and loses m12 flip-tasks =
same m25 signature. Decisive: **"No task-level E/M/H map exists for 267-316, so the claim that losses structurally target
Medium CANNOT be verified. One observed outcome is not a replicable mechanism."** → **Pair(E,H) as a deliberate TARGET =
NO-GO** (both models). RECONCILE: this does not forbid Pair(E,H) as an *incidental, unbankable upside* of a Single-E build
(if that build's Hard happens to land ~0.81) — but we cannot engineer it, cannot validate it offline (no map), and our one
real attempt (m25) put the damage on HARD, not Medium. So: do NOT build a miner *targeting* Pair(E,H); it is m27 again.

**Task 3 (frontier) — Codex REFUTES my §2 overclaim. I was wrong; correcting:** the king 5Ggq satisfies E0.858 ∧ M1.281 ∧
H0.727 — i.e. **all three ≥0.7 simultaneously.** "The frontier binds ALL architectures / nobody is good at all 3" is FALSE
at that threshold — the king IS balanced-decent. **The DEFENSIBLE frontier statement (adopt this):** *no observed miner
pairs king-level E/M (0.858/1.281) with m12-level Hard (0.919)* — pushing E/M to king-level forces Hard down to ~0.727,
far below m12's 0.919. This is UNOBSERVED-as-impossible, not proven impossible (only 4 miners' splits known). For US it is
moot: our Easy lever craters OUR Hard (m25), so balanced-high is out of OUR reach regardless — but I should not have
claimed a universal wall. Overall remains unreachable *for us*, not provably for everyone.

## 8b. "Why not push HARD over 1.2 like the king's Medium?" + "how is the king balanced?" (2026-06-26, follow-up)
**Q1 — Hard cannot reach 1.2; it is structurally capped ~0.92, and we are ALREADY AT that cap.** Field-wide (100-miner
leaderboard 2026-06-26 062001): **max legitimate Hard = 0.92 = m12**; the ONLY miner above Hard 1.0 is the failed-review
cheater 5CaFqLaP (3.151, prompt-cheat). Medium reaches 1.61 (2 miners >1.2). The asymmetry is SOLVABILITY: of 50 tasks,
**34 are natively solvable (baseline pass) and 16 are NOT (baseline fail → score 0 unless FLIPPED +4).** A category mean
of 1.2+ needs either heavy ratio-laden pass-pass (m12 all-PP ceiling = 1.689) OR flips on the baseline-fail tasks. Hard
has more baseline-unsolvable tasks and they are the LEAST flippable (m12 reliably flips only 4/16 baseline-fails; 7 stay
stuck-FF). So Hard's realized ceiling is low for EVERY miner. Two more nails: (a) **more Hard wins us NOTHING new** — we
already own Single-H; every element where higher Hard helps (Pair E/H, Pair M/H, Overall) ALSO needs Easy or Medium up;
(b) **Easy is the binding constraint, not Hard** — even Hard=1.5 (impossible, 60% over field max) gives m12 Overall mean
(0.412+0.953+1.5)/3=0.955 ≈ king; it's our Easy 0.412 that anchors us, not a Hard shortfall.

**Q2 — the king is NOT "well balanced"; its Hard (0.727) is WORSE than ours (0.919).** Gap decomposition (king−m12, /3):
Easy +0.149, Medium +0.109, Hard **−0.064**. The king's lead is Easy + Medium; Hard is where WE beat IT. Mechanism: king
and m12 face IDENTICAL solvability (same agent, same 34/16 split), TIE on flips (17≈16) and ratio (1.61×). The king's
entire E/M edge = **it breaks 6 times vs our 17**, and m12's breaks land on Easy/Medium baseline-pass tasks → drag our
E/M down. The king "loaded the two high-ceiling/solvable categories (E + the 1.6-ceiling Medium) by being consistent, and
ATE the Hard loss." We did the opposite (max Hard, eat Easy). The king's Overall moat is really **Medium 1.281** (its
single biggest weapon: even if we matched its Easy 0.858 holding M0.953/H0.919 we'd reach 0.910 < its 0.955 — Medium is
the difference), and Medium is exactly where the break-fix-kills-flips wall blocks us. The IRREDUCIBLE unknown stays: WHY
the king breaks less is not token-strategy/flips/ratio/visible-content; either compression-quality we can't reverse-engineer
without its code, or sampling on inherently-~80%-pass tasks. Our one attempt to manufacture consistency (m25) just re-rolled
the dice — helped Easy, cratered Hard — i.e. the king's consistency behaves frontier-bound, not as a transferable recipe.

## 9. FINAL (both models reconciled) — what the reframe changed and didn't
- **Changed (the reframe was right here):** stop improving m12; it is the Hard vertex, keep it. Grow by ADDING specialists.
  Corrected the record: flips are tied (no m12 edge); the "frontier" is "no king-E/M + m12-Hard," not "nobody is balanced."
- **Did NOT change (the honest disappointment):** no NEW reliable element beyond Single-E was unlocked. Pair(E,H) looked
  reopened (5DtEz proves E+H coexist, and the m24 NO-GO used the wrong Hard=0.919 constraint) — but it is NOT deliberately
  buildable (can't steer damage to Medium; no offline validation; m25 base-rate says our damage hits Hard). NO-GO as a target.
- **Net reachable ceiling is unchanged: ~9.52%** = m12 (Single-H) + m26 (Single-E specialist; Pair(E,H) only as a free
  lottery upside). Bigger elements (Overall 57%, pairs) need the king's consistency mechanism (unreachable/banned for us)
  or category-steered damage (non-separable). The deep-dive verified this adversarially rather than assuming it.
