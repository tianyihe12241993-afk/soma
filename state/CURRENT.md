# CURRENT — live status (2026-06-23)

_**Mode: ACTIVE COMPETITION — CoT-Compression-4 (competition 108) on SOMA / SN114.** New round, new prompt
policy (force-stop banned; only public compression markers + loop-detection). We submit compliant miners and
iterate. Files = source of truth; read this + NEXT_ACTIONS + DECISIONS + DISCOVERIES + SCOREBOARD before acting._

## ⏭ IMMEDIATE NEXT: build m12.1b
m12.1 was eval-rejected (over-routed Medium). Build **m12.1b** = m12 (`upload_miner_m7_compliant.py`) +
**1a never-inflate ONLY** (pure win), with **1b tightened** so gentle routing fires only on persistent /
genuinely break-prone signals — NOT on compressible Medium (m12.1's bug). Re-eval bar: **Medium tok/call ≈ m12
AND breaks ≤ m12**. Build offline + `scripts/check_prompt_compliance.py` PASS, then real-eval vs m12 on the Mac.

## What's LIVE
- **m12 = our submission in comp 108.** Hotkey `5Dz7JaCBw6t9ktdRVaLYi3ntEzvCDfb5XmTHyzPdDyT6KS9j` (wallet
  tony-miner, local hotkey label `m12`). Solution = `miner/cot_compression/upload_miner_m7_compliant.py`
  (m7 engine, COMPLIANT: coach/force-stop/digest-injection removed, only `[[CMP]]`/`[[BLOCK N]]`/loop_detected
  markers). Key attached = `sk-or-v1-…1e8a` (account ~$97). **SCORED 0.768, PASSED review, #2 among scored.**
  Cats: Easy 0.412 / Medium 0.953 / Hard 0.919.

## Standings + strategy (the plan)
- **New king = `5DFvymSeEw…` total 0.7801** (just +0.012 over m12). MIRROR IMAGE: king Easy 0.812 / Med 0.934 /
  **Hard 0.596**; us Easy 0.412 / Med 0.953 / **Hard 0.919**. We WIN Hard (+0.32) + Medium, LOSE only Easy.
- **7-element incentive math:** we already win (M,H)+M+H (~19%). Lifting **Easy to just ~0.49** flips Overall
  (57%) + (E,H) → **~86% of pool** (plateaus there; (E,M)/Easy-single need Easy~0.8 = not worth chasing).
- **STRATEGY (user, refined):** it's EARLY → **continuously GROW Hard+Medium** (extend the lead as the field
  rises) + **keep Easy competitive (~0.49 floor, not maximal)**. Moat = our H+M gap (king stuck at Hard 0.60)
  + iteration speed. Full plan: `reports/improvement_roadmap_comp108.md`.
- **H+M growth levers (ranked):** (1) flip conversion on HARD (+4 each, but TIGHT routing — must NOT leak
  Medium, the v15 lesson); (2) adaptive deeper-but-SAFE compression on H/M pass-pass; (3) cut H/M run-variance.
  Easy floor via reliability (never-inflate + targeted break-routing). Every push EVAL-GATED (no break, no
  Medium leak) before submit.

## Scoring + gate mechanics (decoded from mcp_platform/app/api/routes/scoring.py)
- Per-run score = `base + λ·clamp(ln(ratio),−2,+2)`; displayed per-task = mean of 5 runs. **break (base-pass→
  fail) = −4 (flat); flip (base-fail→pass) = +4; pass→pass = +1; both-fail = 0.** ⇒ avoiding a −4 break ≈ 3
  clean tasks; flips are gold; compression ratio is a secondary ±λ·ln bonus. Negatives on "passing" tasks =
  run-variance (some of 5 runs broke).
- **Qualification GATE = ≥10% WEIGHTED token savings** (input×1, cached×⅓, output×3). m12 cleared it; comp-108
  "not qualified" miners failed it. Output weighted 3× → fewer agent steps / less wander = high gate value.

## Candidate inventory (all in miner/cot_compression/ unless noted)
- `upload_miner_v11_m7.py` — ORIGINAL m7 (1.279 last round), NON-compliant (has coach). Do not submit as-is.
- `upload_miner_m7_compliant.py` — **= m12 (LIVE).** Compliant, scored 0.768.
- `upload_miner_m12_1.py` — **DO NOT SHIP** (over-routes Medium, +20% tok/call). Salvage → m12.1b.
- `upload_miner_h4b_compliant.py` — h1m@deep-compliant (deeper). Reference; deeper breaks more (wrong this round).
- `experiments/candidates/H3_cache_stable_depth_v1/h3_miner.py`, `H4_compliant_cache_stable/h4_miner.py` —
  cache-stable; **falsified** (didn't beat h1m@deep). Reference only.

## Eval pipeline (Mac, WORKS — real SWE-bench via SWE-rebench)
- Driver: `experiments/candidates/H1M_m7_deeper_safe_v1/run_batch_eval.sh` (PROFILES/RUNS/TASKS env; bakes the
  miner into SOMA-plugin/base_miner.py; profiles incl m7, h1m@*, h3@*, m12, m12_1). Needs OPENROUTER_API_KEY
  (env or config/secrets.env). macOS Docker Desktop only — NOT WSL2.
- Analyzer: `experiments/candidates/H1M_m7_deeper_safe_v1/analyze_batch.py` (per-task + per-category resolved/
  breaks/tokens/cache; gate CSVs). Compliance: `scripts/check_prompt_compliance.py`.
- Setup for a fresh machine: `setup/EVAL_PIPELINE.md`.

## Open items
- **Confirm upload cadence:** can we re-upload an improved solution to m12's hotkey mid-round, or does each
  iteration need a fresh registered hotkey (burn) / next window? Sets iteration speed.
- **Add known-Easy SWE-bench instances** (from config/task_categories.csv) to the eval — current regression set
  is fragile+Medium only, so the Easy lift is an unvalidated platform bet.
- Watch rivals each cycle (esp. `5CwZBKyL` in-queue 1.062, only 5 screeners done; the king 5DFvymSeEw).

## Hard rules (still in force)
Compliant only (scanner-clean: no coach/force-stop/steering, only allowed markers + 2 loop reasons). Never
commit secrets. Don't submit/replace m12 until a candidate BEATS it on the Mac eval (no break, no Medium leak).
Platform upload + git push to the backup repo are classifier-blocked for me → user runs those (external
terminal). Backup repo (private): `github.com/tianyihe12241993-afk/soma` (remote `myrepo`).
