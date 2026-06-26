# Depth-gated passthrough — OFFLINE PROBE VERDICT

_Date: 2026-06-25. Offline, read-only (no miner file written, no upload). The last untested ACTIVE growth idea._

## VERDICT: **NO-GO.** Depth does not separate Easy from Medium/Hard in comp-108 — same wall as token-gating.

## Idea
Mirror m12's own depth-based harvest→rich split, but for the passthrough→harvest transition: stay passthrough while the
conversation is SHALLOW (depth < D_pt), compress once deep. Hope: Easy tasks end shallow → stay passthrough → native
context → no breaks → Easy↑; Medium/Hard run deep → compress (preserve our M/H strength + savings).

## Feasibility test (the make-or-break): per-category DEPTH distribution
Measured max msg_depth reached per run over real comp-108 m12 trajectories (47 Easy / 33 Medium / 48 Hard runs):
```
  Easy    min=12  median=56  max=89
  Medium  min=20  median=49  max=112
  Hard    min=10  median=53  max=98
```
**The categories overlap almost completely, and Easy's median depth (56) is DEEPER than Hard's (53) and Medium's (49).**
Many Hard tasks are shallower than many Easy tasks. There is NO depth D with Easy < D ≤ Medium/Hard. (The m12 code
comment "easy ends shallow ~67-83, hard ~125" was based on COMP-107 trajectories; comp-108 tasks are 100% different and
the separation does not hold.)

## Confirming sweep (per-category passthrough% + routing damage + savings)
```
D_pt   savings   Easy_PT   Med_PT   Hard_PT   Med_route_chg   Hard_route_chg
  0     79.4%     6.4%      3.5%     5.5%       0               0            <- m12 baseline
 40     38.0%     61.8%     58.5%    48.2%      1518            2313
 56     35.0%     69.0%     63.0%    48.2%      1628            2315
 70+    34.9%     71.0%     63.0%    48.2%      1628            2315
```
Any D_pt that lifts Easy passthrough **equally floods Medium and Hard into passthrough**: Medium (our 0.953 strength, won
by m12's harvest) takes 1500+ route changes, Hard takes 2300+ (the m13 crater mode), and aggregate savings halves
(79%→35%). The depth gate cannot help Easy without damaging Medium/Hard, because they occupy the same depth band.

## Root finding (elevated to DISCOVERIES)
comp-108 E/M/H are **non-separable by ANY per-call signal — token size OR depth.** At compression time an Easy task is
indistinguishable from a Medium/Hard task; only the eventual OUTCOME distinguishes them, and we can't see it when we
decide. This is the unifying reason every Easy/Medium active lever fails (m13/m15/m16/m22/m23/m24/depth-gate) and why
m12's uniform-compress + depth-stickiness + content-protection is a defensible local optimum. **The active single-miner
growth space is closed.**

## What offline could NOT test (honest)
Whether early-native context would HELP Hard outcomes (vs m13's global softening which hurt) — moot here, because the
routing/savings damage already disqualifies it before any outcome question.

## Recommendation
Stop probing active single-miner content/routing levers — the impossibility is now proven on both the size and depth axes.
The reliable position-improving move is the **byte-identical insurance twin** (defend Single-Hard against the king's
volatile Hard + hold passive position for Pair(M,H) → ~14.3%). Artifact: inline scripts (this session); m12 LIVE untouched.
