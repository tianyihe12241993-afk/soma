# Improvement roadmap — CoT-Compression-4 (comp 108)
_Goal: iterate past m12 fast enough, and with enough algorithmic quality, that rivals can't follow.
Evidence base: reports/m12_comp108_analysis.md (m12 = 0.768, #1 scored)._

## 1. Where we stand (the opportunity)
m12 total 0.768 = **positives +42.2 − negatives 9.0** over 45 tasks. The −9.0 is almost entirely **avoidable**:
- **3 hard breaks** (baseline passed → we failed): −1.98, −1.83, −0.43 = **−4.24**
- **4 run-variance negatives** (passed overall, some of 5 runs broke): −1.03, −1.02, −0.93, −0.16 = **−3.14**
- **token-inflation tax**: 10 tasks compressed to <1× (we grew the context) — some scored negative, others had their bonus **capped** (e.g. passed at 0.66× → −1.03; passed at 0.51×/0.70× with capped bonus).
Recovering the negatives + un-capping the inflated tasks is plausibly **+6 to +10 raw → total ~0.95–1.05** — and it's **reliability work (low pass-risk), not more depth.** Our edge is compression + **7 flips** (scores +1.3…+3.0); our liability is breaks (the #2 rival wins the tasks we broke by being gentler).

## 2. The moat (why "they can't follow")
Prompt tricks are banned + the allowed list is public, so the game is **algorithm quality + reliability**, which is much harder to copy than a prompt string. Our durable advantages:
- **Reliability lead** — fewer broken baselines than rivals (each break = −2). Hard to reverse-engineer; comes from careful load-bearing preservation + routing.
- **Masked task names** — rivals see our aggregate ratio/pass on the dashboard but can't see *which* tasks → they can't targeted-copy.
- **Iteration speed + a staged pipeline** — always keep 1–2 validated-but-unshipped improvements ready, so when a rival closes the gap we ship the next. Stay ahead, don't dump everything at once.
- **Algorithmic sophistication** — invest in techniques that take real engineering to replicate (relevance-scored retention, structure-aware adaptive budgeting, robust extractive preservation), not copyable one-liners.

## 3. Roadmap (phased, each gated on the Mac real-eval before any submission)
### Phase 1 — Reliability quick wins → **m12.1** (biggest value, lowest risk; do first)
- **1a. Never-inflate guard:** if the compressed turn ≥ baseline tokens, emit pass-through (changed=False). Kills all 10 inflated tasks' tax. Zero pass-risk, pure points.
- **1b. Gentle routing on break-prone tasks:** detect error-dense / short-Easy / repeated-failure / fragile signatures → route to rich or pass-through (trade ratio for no −2). Targets the 3 hard breaks + softens the 4 run-variance negatives. (Tune the existing fragile guard — it's not catching these.)
- **Gate vs m12:** 0 new hard-breaks, fewer total negatives, compression ≥ m12, never-inflate verified, scanner-clean. Target total ~0.9+.

### Phase 2 — Smart adaptive depth → **m12.2** (push ratio where it's safe)
- Compress **deeper on proven-safe tasks** (high baseline-pass margin, low error-density, non-fragile) and **gentle on risky** — the "depth-where-safe" frontier, mapped on the Mac eval. More bonus on the ~20 clean-pass tasks without adding breaks. (NOT global deeper — H4b proved global depth breaks more.)

### Phase 3 — Run-variance / robustness (the 4 run-variance negatives)
- Score averages 5 runs; some runs break on "passing" tasks. Make compression **deterministic + never edge-pushing** (robust load-bearing preservation, stable per-call output). Cuts the negative-run rate.

### Phase 4 — Easy floor (structural 0.412)
- Easy is short (little to compress) + break-prone; the compliant lever is **don't break Easy** (mostly Phase 1b) + light compression. Accept Easy is bounded; protect it rather than chase ratio.

### Phase 5 — Moat / cadence (ongoing)
- Continuous loop each cycle: scrape dashboard (us + rivals' per-task ratio/pass) → find the gap → ship the next staged candidate. Keep the pipeline full.

## 4. Operational
- **Eval gate:** the m12 break + inflation tasks become a **regression set**; every candidate must beat m12 on it (on the Mac pipeline) before submitting. Never submit an un-eval'd change.
- **Upload cadence — CONFIRM the rule:** is it one upload per window per hotkey (107 was), or can we re-upload an improved solution to m12's hotkey mid-round? If re-upload is allowed → iterate on m12's hotkey cheaply. If not → each iteration needs a fresh registered hotkey (burn cost) or waits for the next window. This sets the iteration cadence — confirm via Discord/platform before planning burns.
- **Monitoring:** track m12 + rivals each cycle; especially **5CwZBKyL (in queue, 1.062, only 5 screeners done)** — see if it finalizes above us.
- **Keep H4b/H3 as references only** (deeper = more breaks = wrong direction this round).

## 5. Immediate next steps
1. **Build m12.1** (Phase 1a+1b) — offline + scanner-clean.
2. **Real-eval m12.1 vs m12** on the regression set (the break/inflation tasks + Medium sanity) on the Mac.
3. If it clears the gate → **submit** (re-upload to m12's hotkey if allowed, else a fresh hotkey).
4. In parallel, **confirm the upload/window cadence** so we know how fast we can iterate.

## STRATEGY REFINEMENT (2026-06-23) — continuous H+M growth + Easy floor (early-stage)
The 7-element math (vs the current king): our H+M dominance already wins (M,H)+M+H (~19%); lifting Easy to
just **~0.49** flips Overall (57%) + (E,H) → **~86% of pool** (plateaus there — chasing Easy past ~0.55 is
wasted: (E,M)/Easy-single need ~0.8). BUT it's EARLY — the field + thresholds will rise — so the play is:
- **CONTINUOUSLY grow Hard + Medium** (extend the lead as rivals improve), via — ranked by scoring value
  (per-run = base + λ·ln(ratio); break −4, flip +4, pass-pass +1):
  1. **Flip conversion on HARD** (+4 each, biggest lever) — TIGHT routing: rich context only on genuinely
     flip-likely Hard tasks. MUST NOT leak Medium (the v15 lesson: persistent-failure routing pulled
     iterating-Medium to rich → lost the harvest bonus → Medium 1.42→1.18). Gate every flip change on Medium.
  2. **Adaptive deeper-but-SAFE compression on H/M pass-pass** → more λ·ln bonus (Phase 2; depth only where
     proven-safe, never global — global deep breaks fragile).
  3. **Cut H/M run-variance** (−4 run-breaks → positive) — reliability.
  Also: the weighted GATE (output 3×) rewards fewer agent steps → cleaner context (less wander) helps H+M too.
- **Keep Easy COMPETITIVE (~0.49+ floor), not maximal** — m12.1 reliability holds it; re-check the threshold
  each cycle as the field's Overall/(E,H) bars rise; don't over-invest (risks the H/M we own).
- **Discipline (the moat):** every H+M push eval-gated (no new breaks, no Medium leak) before submit; iterate
  per cycle; stay ahead. Sequence: m12.1 (Easy floor + reliability, in eval) → Phase 2 (H+M growth).
