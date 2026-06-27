# m27 Easy+Hard specialist — PRE-BUILD ANALYSIS (dual-mode signal-retention vs trajectory-preservation)

_2026-06-26. NO miner file built (analysis gate). m12 LIVE untouched. Goal: a dual-mode compressor that gets m25's
Easy gain (signal-retention on "settled" turns) WHILE keeping Hard high (m12 trajectory-preservation on "exploration"
turns), routed by observable per-turn signals (settled vs exploring) — targeting Pair(E,H) (~0.825), needing E≥0.84 ∧ H≥0.79._

## VERDICT: **NO-GO** (extractive dual-mode). The Easy mechanism is inherently anti-flip + perturbing, and the
## settled-vs-exploration router cannot avoid the damage — m25's platform data proves it. (Codex audit appended below.)

## 1. Per-task m12→m25 (6 buckets, all 45 tasks)
| bucket | n | sum Δ |
|---|---|---|
| m12 break → m25 pass (break-fix) | 3 | **+4.65** |
| m12 pass → m25 higher (pass-pass boost) | 13 | **+7.05** |
| m12 pass → m25 BREAK (new break) | 2 | −4.01 |
| **m12 FLIP → m25 fail (flip-kill)** | 3 | **−6.14** |
| m12 fail → m25 pass (NEW flip gained) | **0** | **+0.00** |
| m12 pass → m25 lower (degraded) | 16 | **−6.59** |

Reads: Easy gain = break-fix (+4.65) **+ pass-pass boost (+7.05)** — the boost is real and needs *compression* (not
passthrough). **m25 gained ZERO new flips and killed 3** → the extractive mechanism is **strictly anti-flip**. The
biggest loss is **degrading/breaking 18 baseline-PASS tasks (−10.6)** = content-perturbation, not flip-specific.

## 2. Separability test — does the settled-signal router fire ONLY where extractive helps? (decisive)
Re-ran the RESOLVED-gate (m25's exact params: harvest ∧ prev≠rich ∧ ¬still_failing ∧ ¬escalated ∧ depth<80 ∧
recent_errors(6)==0 ∧ ≥3 results) over the available m12 trajectories; counted fires vs the m25 platform delta:
| task | gate fires | Δ(m25−m12) | |
|---|---|---|---|
| django-13810 | 213 | +2.20 | gate fires on a HELP |
| django-14122 | 16 | +2.31 | gate fires on a HELP |
| sympy-20590 | 26 | +1.05 | gate fires on a HELP |
| sympy-15349 | 57 | +0.97 | gate fires on a HELP |
| **django-12039** | 6 | **−1.02** | **gate fires on a HURT** |
| **sympy-23262** | 16 | **−1.12** | **gate fires on a HURT** |
| **sympy-24066** (flip) | **238** | **−0.87** | **gate fires heavily on a flip m25 HURT** |
| django-13158 | 0 | −0.97 | (gate=0 yet m25 hurt — local≠platform / rich-drift) |

**The gate fires on a MIX of helped (4) and hurt (3) tasks.** It fires 238× on sympy-24066 (a flip m25 damaged). The
−10.6 "degraded passing tasks" damage lands on **settled-looking** tasks the gate *should* fire on (they're
indistinguishable from Easy gainers). **No observable signal separates "extractive helps this settled task" from
"extractive destabilizes this settled task" — it is a per-task coin flip the router cannot predict.**

## 3. Which signals are in Easy gainers but absent in Hard/flip losers? — **none that separate cleanly.**
- Easy gainers and the destabilized passing-task losers BOTH present as "settled" (recent results clean, no active
  failure) → the gate fires on both. The user-listed exploration signals (active-failing-tests, patch/test-loop,
  traceback-density, unresolved-failure) are ABSENT on a flip's EARLY turns (the agent hasn't run the failing test
  yet) — exactly when the gate leaks (the m23 audit already proved this; m25's killed flips confirm it on platform).
- A gate strict enough to exclude flips (m23 audit's G4: depth<45 ∧ ≥3 prior errors ∧ last-10-clean) ALSO excludes the
  Easy gainers (it fired 0 on django-14122) → kills the Easy gain. The bind is intact.

## 4. Which m25 changes caused the Hard/flip losses?
The blind→extractive swap on harvest truncation: (a) shreds the CONTIGUOUS exploration content a still-solving agent
reasons over into scattered pinned lines → kills flips (−6.14, 0 gained); (b) perturbs content on passing tasks →
reroutes the solver → degrades/breaks 18 of them (−10.6). Both are intrinsic to extractive compression, not a tunable.

## 5. Dual-mode plausibility — NO (for the extractive Easy mechanism)
- **Extractive Easy mode** (keeps the +7.05 boost): perturbs + anti-flip; the router fires on hurt tasks it can't
  distinguish from gainers → Hard cratered (≈ m25's H 0.536, NOT ≥0.79). Hits NO-GO criteria: "leaks m25-style
  extractive into Hard/flip-sensitive tasks" + "cannot plausibly keep H≥0.79."
- **Passthrough-native Easy mode** (non-perturbing → Hard-safe even under router leak): BUT (a) the gate fires on
  HARVEST-eligible turns (observed≥3k tok); passthrough there sends the FULL native (often ≫ m12's 8k harvest target)
  → balloons tokens → fails the savings/qualification gate + perturbs via more-context; (b) loses the +7.05 boost →
  Easy likely < 0.84. Fails the Easy target AND the savings gate.
**Neither mode clears E≥0.84 ∧ H≥0.79.** The Easy-gain mechanism (compress settled turns for the boost) is inherently
perturbing/anti-flip; the only non-perturbing alternative (passthrough) balloons tokens and loses the boost.

## NO-GO criteria hit
- ✓ "leaks m25-style extractive behavior into Hard/flip-sensitive tasks" (router fires on flip sympy-24066 + can't separate).
- ✓ "cannot plausibly keep H≥0.79" (mechanism is anti-flip + destabilizes passing tasks; H ≈ m25's 0.536).
- ✓ "sacrifices the m25 Easy mechanism enough that E<0.84" — applies to the only Hard-safe variant (passthrough).

## NEED-DATA caveat (does not change the verdict)
The 4 named flip-losers (django-14017, sympy-23824, sympy-20801, django-13925) have NO local m12 trajectories, so the
gate-firing on THEM is inferred (not directly replayed). Evidence is already decisive: sympy-24066 (a flip we DO have)
fires 238× and m25 hurt it; m25 killed 3 flips + gained 0; the m23 audit proved the gate leaks on flips. A targeted
local eval of those 4 would make it 100%, but is not recommended (the conclusion is mechanism-level, not data-limited).

## The honest alternative (NOT an E+H specialist)
Pair(E,H) needs ONE miner high on BOTH E and H — which requires preserving flips/trajectory (Hard) WHILE compressing
settled turns for Easy. m25 proves that's self-contradictory with the extractive mechanism. The reachable portfolio play
remains **TWO singles**: m12 (Single-H, 0.919) + an Easy-ONLY specialist that ABANDONS Hard (Single-E, target >0.923).
That is the m26 direction — a Single-E specialist, NOT a Pair(E,H) dual-mode miner. Same ~9.52% share; reachable.

---

## Codex audit + reconciliation (2026-06-26) — NO-GO CONFIRMED by both models
Codex independently recomputed the buckets + separability from the raw JSON and CONFIRMED the NO-GO, adding two decisive sharpenings:
1. **The help-fires and hurt-fires have IDENTICAL per-turn signal distributions** (Codex measured them): helped gate-fires
   depth 4–59 / observed 3.6k–22k tok / still_failing=0; hurt gate-fires (incl. sympy-24066 @238) depth 4–73 / observed
   3.6k–17k / still_failing=0. **No threshold on depth, tokens, ratio, or pass-flags separates the two populations.** This
   is stronger than my "fires on a mix" finding — the signal space literally cannot separate help from hurt.
2. **The +7.05 boost is ~86% perturbation, only ~14% ratio**: token-ratio explains just **+0.96** of it; the remaining
   **+6.09 is content/outcome perturbation.** So a non-perturbing Easy mode (passthrough/dedup) loses the bulk of the gain
   → E drops. (Also: under STRICT pass-flag definitions my "break-fix" bucket is only +2.2/n=1, not +4.65/n=3 — i.e. the
   Easy gain is even MORE perturbation-boost and LESS clean break-fix than the hybrid labels implied.)
Codex rulings: m27 = m25's settled-gate relabeled as dual-mode (NOT distinct); Hard protection is mostly CLAIMED (early
shallow flip turns pass the settled gate before Hard signals appear; m12 fallback only engages turns the gate already
skipped); the router is legitimately observable but observably INEFFECTIVE; Pair(E,H) math unrealistic (H 0.536 vs 0.79,
structural conflict — the router supplying Easy is the one perturbing Hard, shared fires); the Easy mechanism is NOT
preservable without the perturbation.

## FINAL: NO-GO (both models, independent)
m27 as an Easy+Hard dual-mode specialist is not viable: the Easy gain is mostly content-perturbation that is intrinsically
anti-flip + destabilizes passing tasks, and the settled-vs-exploration router CANNOT separate where it helps from where it
hurts (identical signal distributions). Hard protection is therefore unachievable (≈ m25's H 0.536, not ≥0.79). The
non-perturbing alternative loses the boost + balloons tokens. NO file built; m12 LIVE untouched.

## Constructive note (a DIFFERENT candidate, not m27)
Pair(E,H) needs ONE balanced miner — impossible with this mechanism. The reachable ~9.52% comes from TWO singles: m12
(Single-H) + an Easy-ONLY specialist (Single-E, target >0.923, ABANDONS Hard — no dual-mode, no Hard to protect). That is
the m26 direction, a separate decision; it is NOT this m27 E+H specialist.
