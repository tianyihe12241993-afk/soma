# Improving "Hard" for comp-110 — the ENDURANCE mechanism (2026-07-07)

_Data: comp-108 archive per-run snapshot (13 miners × 50 tasks × 5 runs, source:platform).
Companion to `comp108_cap32pin_postmortem.md`. Codex re-derivation: `codex_postmortem_verification.md`._

## Finding 1 — "Hard tasks can't break" was WRONG; Hard is a high-stakes coin flip
Run-level scores on Hard tasks show fails scoring −1.6 to −2.4, not ~0. Cause: per-run scoring
compares the miner run against EACH baseline run pairwise, and 8 of the 17 Hard-bucket tasks have
PARTIALLY-passing baselines (inferred baseline pass-count b: 16792 b=3; 14976/18698/19346/20154/
20801/23824 b=2; 11149/13925 b=1; rest b=0). On a b-task: fail run ≈ −0.8·b, flip run ≈ +1.5…+2.0.
⇒ On b≥2 tasks a fail costs as much as a flip earns — **flip CONSISTENCY, not flip existence, is
the Hard lever.** H-winner took 0.718 by flipping 4–5/5 exactly where we flipped 1–2/5 and ate −2.3s
(16792: them 4/5 = +1.03/task, us 1/5 = −1.54/task — a 2.6-point swing on ONE task).

## Finding 2 — the mechanism behind flip consistency = per-step LEANNESS × run ENDURANCE
Across the 13 miners on all 85 Hard runs each:

| miner | Hard flip% | mean steps | tokens/step | early-deaths (<40 steps, fail) |
|---|---|---|---|---|
| **H-winner** | **51%** | **67** | **17.9k** | **5** |
| **E-winner** | 40% | 64 | 18.3k | 6 |
| king-DQ1 | 41% | 53 | 28.2k | 16 |
| np3+pin | 36% | 49 | 24.4k | 17 |
| np3 | 35% | 52 | 26.6k | 15 |
| cap32+pin | 34% | 51 | 24.3k | 12 |
| np2 | 31% | 52 | 23.9k | 14 |
| M-winner | 29% | 32 | 20.4k | 43 |
| nocap | 26% | 53 | 25.4k | 12 |

The two best Hard miners share one profile: **~25% leaner context per step AND ~15 more steps AND
almost zero early deaths.** Leaner per-step context lets the agent keep working (more actions before
token/context exhaustion) → more chances to crack a baseline-fail task. M-winner is the control case:
also lean per step but SHORT runs (32 steps, 43 early deaths) → Hard 0.220 while its depth won Medium
0.969. The winning Hard formula is the PAIR: lean per step + long-lived runs.

This refutes comp-108's standing belief ("Hard flips need CONTEXT → keep big results fuller").
cap32's fuller-keep bought a modest +0.11 H vs np2 (real but small); H-winner got +0.44 over us by
compressing MORE per step and simply outlasting everyone. It also explains the pin's failure
(pin = MORE per-step bulk = worse endurance) and nocap's crater.

_Caveats (honest): cross-sectional over 13 miners; steps/tok-per-step are partly agent-behavior
draws; the platform is the only arbiter. But the within-data consistency (early-death counts,
b≥2-task swings, M-winner control case) is strong, and the new local stack can A/B this directly._

## What this means for comp-110 (design inputs — USER decides)
comp-110 has no E/M/H — layers are per task-type. But the endurance thesis pays in ALL THREE:
1. **swebench_verified** keeps flip(+2)/break(−4) run-vs-baseline scoring → same math: lean per-step
   + never-die-early = flips on the baseline-fail tail + fewer breaks.
2. **swe_explorer_explore**: score = quality-gate × 2·log2(weighted savings). Leaner per-step IS the
   savings term; more surviving steps = more files examined = higher hit_file_rate. Aligned, not a tradeoff.
3. **swe_explorer_edit**: hinted-patch mode = shortest trajectories; lean context keeps it cheap.
Concretely for the `compress_messages` port:
- **Depth target: M-winner zone (~2.5×), not cap32's 1.45×** — comp-108 proved 2.5× is compliant and
  quality-compatible; comp-110's explore layer pays it directly.
- **Preserve endurance:** never inject anything that stalls or loops the agent; loop-guard only true
  no-progress repetition (H-winner profile: 5 early deaths / 425 runs). Byte-stable prefix for cache.
- **Quality floor:** never drop file-paths / error text / structural signal (the explore quality gate
  = hit_file_rate − noise_file_rate; margin ≤ −0.20 → −2 floor).
- **Consistency:** deterministic compression (no randomness, no state that diverges across runs) —
  the b≥2 lesson says variance on volatile tasks is where crowns are lost.
- ⚠️ **Compliance question to settle BEFORE building:** trajectory-shape-adaptive behavior (e.g.
  detecting explore-mode messages) — verify against README rules + ask on-channel if ambiguous.
  Content-size-adaptive caps (np2/np3-style) were always fine.

## Codex reconciliation (gate #2, dual-agent protocol)
Codex independently re-derived all six load-bearing claims from the raw JSON:
- **CONFIRMED exactly:** pin raised break-rates (7.2→10.4%, 7.6→9.2%); M-winner depth 2.5847× with
  M 0.954; our breaks/cache 7.60%/90.91% vs rivals; variance span 0.381–0.885.
- **CONFIRMED-under-map / PARTIAL:** pin & cap per-category deltas match to 4 decimals under the
  solved map; Codex notes the *Hard-specific* attributions are sensitive to bucket choice (under a
  naive Hard=baseline-fail grouping the pin's Hard delta turns positive, driven by 16792). Reconciled:
  the solved map matches the platform's actual difficulty formula (16792: b=3 → loss 0.4 → Hard by
  0.75·loss+0.25·tokens), so we keep it — but the pin verdict rests on the ROBUST parts (E/M damage +
  breaks), not on its Hard delta. Verdict unchanged: **pin does not get ported by default.**
