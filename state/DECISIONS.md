# DECISIONS (durable; don't relitigate)

- **m7 / v11.1 is our confirmed best (1.279) and the recipe to protect/replicate.** Everything built on top
  (v15→v18→v22→v24) added persistent-failure flip-routing that, on the platform, *leaked Medium* (v15 → 1.183).
- **Compression is at its ceiling.** Six levers tried (v14 richer, v17 harder, v19 loop-coach, v20 snapshot,
  v21 reasoning-trim, v23 gentler-harvest) — all no-gain or harmful. m7's 8k harvest is the sweet spot.
- **The king's edge (decisiveness + Easy 1.43) is not reachable via compression** — it's agent/model behavior.
  Easy ceiling for us is ~1.13 across gentle/aggressive/adaptive. Stop chasing Easy/overall #1.
- **Shipped v22→m9, v18→m10, v24→m11 (2026-06-17)** as flip "king-shots" on fresh hotkeys (m7 untouched/floor).
  Expectation revised DOWN after v15's platform result: likely ≤ m7 (Medium leak outweighs unmeasurable Hard gain).
- **v26 (depth-gated threshold) validated for a future cycle**, not shipped (m12 unregistered).
- **Reward model is layer-based (7 elements), not top-3.** Winning a single category (~4.8%) is the only realistic
  path for us; overall/pairs need broad strength we lack.
- **Ops/tracking lives here (SOMA-ops). Miner code is NOT edited or submitted from this repo.**
- **PIVOT (2026-06-21): post-competition RESEARCH mode.** Comp 107 completed; we do NOT submit.
  Goal = design the strongest next-round miner offline, evidence-backed. Next direction is fixed:
  **m7-style architecture + deeper PASS-SAFE compression**, NOT more routing. Flip-mode rescue /
  persistent-failure routing / release-flip-on-pass are **permanently dropped** (postmortem: net-negative —
  no pass gain, more broken baselines + negative tasks). Hypotheses H1–H4 in experiments/manifests/.
- **Label audit RESOLVED (2026-06-21):** m9=5CFqU2Ss=v22, m10=5GL4Kxda=v18 (registry, corroborated by 4
  git-tracked files; chat label rejected per "chat ≠ source of truth"). Scores are hotkey-anchored, so
  analysis is label-independent. Full evidence: reports/label_mapping_audit.md.
- **Dev/ops env runs in WSL Ubuntu-22.04** (scope: "miner dev + ops"). One-shot idempotent installer
  `scripts/setup_wsl_env.sh` → venv at `~/.venvs/soma` (Linux fs, fast IO); repo stays at `/mnt/e/soma`.
  Pinned to the repo's known-good set; pin `async-substrate-interface==1.5.15` to avoid the cyscale↔scalecodec
  namespace clash that breaks `import bittensor`. Full guide: `docs/wsl-env.md`. NOT installed (upload-only):
  `soma_shared` (private DendriteHQ repo — sandbox blocks external git installs, user runs it) + a netuid-114 wallet.
- **TARGET = the OVERALL king t1 (5EkiFXSR, 1.460), via PASS-SAFE COMPRESSION DEPTH (2026-06-22).** The
  board has 7 reward elements; the winning recipe that fits us is the DEPTH strategy (t1/t2/t3 run mean
  ratio ~4.8–5.0× at pass 37–39). **We already match the king on the hard parts** — pass 38 (vs t1's 39),
  broke 1 (=), neg 3 (better) — and lose almost purely on ratio (2.99× vs 4.83×). The ratio model explains
  +0.231/task of the +0.157/task gap (residual −0.074), so **matching the king's depth ≈ closes the whole gap.**
  → Next-round plan: push m7's harvest from ~3× toward ~4.8–5× while HOLDING passes + protections. Per
  category: Medium ~5× (safest + closest element), Hard pass/pass ~5× (flips→rich, fragile guard), Easy ~4×
  (flakiest — t10 proves crude over-push crashes pass-rate: 5.24× but only 33 passes). t4's Hard 1.751 comes
  from pass-rate/decisiveness (agent behavior, only 3.06×) — not our reachable lever; depth is.
- **King-depth SWEEP is the next experiment (chosen by user 2026-06-22), AFTER the foundation batch.** Added
  `king` (TARGET 3600) + `ultra` (2400) profiles to h1m_miner.py (protections untouched; only stale-content
  truncation tightens). Sweep m7 → deep → king → ultra via run_batch_eval.sh (`PROFILES=...`) on a focused set
  to find the **pass-safe depth ceiling** per category = the next-comp baseline. Foundation batch (m7 vs
  h1m@deep, 15 tasks) runs first to validate eval-at-scale + the m7 baseline + the fragile guard.
- **STRATEGY UPDATE (2026-06-22): the top of comp 107 FAILED REVIEW — target + thesis shift.** t1–t5 + t7
  (incl the overall, Medium, AND Hard kings) are all "failed review" (excluded from reward); only t6/t8/t9/t10
  + our miners survive. Consequences: (1) **m7 is now review-PASSING top-tier** — #2 overall, Medium ≈TIE
  with t9 (1.421 vs 1.423), #2 (M,H). (2) **The king target drops from t1 (1.460, 4.83× deep) to t6 (1.335,
  2.88× — NOT a deep compressor; wins via Hard 1.525 + balance).** So **chasing extreme 4.8× depth is no
  longer required** to be king-competitive — de-prioritize the king/ultra depth chase; favor m7-class +
  modest-safe-depth + Hard. (3) **OPEN RISK — why did they fail review? Ratio is NOT the cause** (t10 survived
  at 5.24×, t5 failed at 2.40×) → per-miner manual/compliance review, cause unknown. **INVESTIGATE the review
  criteria (Discord / platform notes) BEFORE shipping aggressive-compression candidates** — H1M/H3 deep could
  carry an unquantified DQ risk. The H3 cache-stable work stays valuable (review-safe, modest depth, Medium
  edge), but reframed: beat t6's 1.335 + win Medium, not catch a (now-DQ'd) 4.8× king. Confirm element leaders
  vs the FULL comp-107 board (tracked recompute excludes untracked ranks 11+).
- **PROMPTING POLICY locked for next comp (2026-06-22, official `miner/README_prompting.md` + Discord).** The
  top failed review for **SWE hints injection (t1,t2,t3,t7)** + **non-compliant prompt modifications /
  behavior-steering (t4,t5)** — PROMPT-SIDE CHEATING + problem-targeting force-stops, **NOT compression depth.**
  Our compression is the intended focus; m7 passed = legitimate. **Next round ONLY two prompt edits allowed:**
  (1) compression markers (metadata only, exact published strings, preserve meaning/order/policy/output),
  (2) loop-detection guards (objective loops only, exact reason strings, no behavior change, no token-shortcut
  forcing). **Force-stop is BANNED.** Allowed strings: markers `[[CMP]]` `[[/CMP]]` `Compressed text
  starts/ends here` `[[BLOCK X]]` `[[/BLOCK X]]` `Same response as in [[BLOCK X]].`; loop reasons
  `loop_detected: repeated assistant response` / `loop_detected: repeated tool call signature`. New strings →
  discuss publicly first. **OUR m7/H1M/H3 are NON-COMPLIANT on the prompt side** (coach = force-stop "STOP NOW"
  + loop nudge "change your approach" + custom `[SOMA …]` markers). **Next-round baseline = m7 compression,
  COACH-FREE / force-stop-free, published `[[CMP]]` markers, loop-detection reduced to the 2 allowed reason
  strings; keep harvest/rich/H3 cache-stable compression.** Stripping the coach likely costs little (v12's
  forced-stop already FAILED to help). Full gap analysis: reports/prompting_policy_and_compliance.md.
