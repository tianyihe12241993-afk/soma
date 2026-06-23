# DISCOVERIES (durable findings)

- **Incentive is layer-based (7 elements), not top-3.** Overall(E,M,H)=w1, pairs=1/6 each, singles=1/12 each.
  Winner of each = highest avg on that subset; failed-review excluded. Up to ~7 distinct miners can earn.
- **Flip-routing leaks Medium on the platform.** v15 (m7 + persistent-failure→rich) scored Medium **1.183**
  vs m7's 1.421 — the trigger pulls iterating medium tasks off the harvest bonus. Local validation under-detected
  this (only 2 medium instances). Implies m9/m10/m11 (more aggressive routing) likely also lose Medium.
- **Easy is ~1.13-bounded for us** across gentle/aggressive/adaptive compression. The king's Easy (1.347) and
  2nd's (1.433) come from agent *decisiveness* (fewer steps), not compression — unreachable via our lever.
- **King's Hard (1.751) = flip conversion @ comp_ratio ~0.85 + decisiveness.** We convert flips ~41% @ 0.52.
- **Gold-patch proxy under-counts** (equiv fixes: 11099 `\A..\Z`, 16429 `d.tzinfo if is_aware`, 14539 entity-loop).
  Real pass/fail needs SOMA_SWEREBENCH_EVAL (infeasible locally on arm64). Always manual-check gold=False.
- **Early-cutoff noise:** intermittent (~10–30% in bad windows) provider/agent variance — model emits a no-tool-call
  turn → session ends with empty/partial patch. NOT our code (same miner clean in one batch, cut in another).
- **Local e2e test-env is partly broken** (can't install some deps / run tests) → verification-wander inflates
  step counts vs the platform. Use the gold-PATCH metric + comp_ratio, not run-status, locally.
- **Dashboard:** thesoma.ai/dashboard embeds the leaderboard as JSON; per-miner: /dashboard/miner/107/<hotkey>.
  Display column order is total/Easy/Hard/Medium; JSON keys are {Easy,Medium,Hard}.
- **Per-task detail is scrapable** (collect_miner_detail.py): each miner page exposes 50 tasks with
  pass_with/without_compression, tokens_with/without, platform_score, run_count + sweSummary + swePenalties.
  Machine: data/latest/miner_detail.json + task_scores.csv; report: reports/task_detail.md.
- **The CORRECT detailed source is the platform JSON API, not the RSC scrape** (verified from
  mcp_platform/app/api/routes/frontend.py + live probe 2026-06-21). Endpoints under
  `…/api/public/frontend-key/swe/miners/{comp}[/{hotkey}[/tasks[/{task}/runs]]]`:
  leaderboard → summary → per-task → **per-RUN**. The per-run layer (`SweMinerTaskRunItem`:
  run_id, attempt_no, pass_with_compression, tokens_with_compression, platform_score,
  **time_taken_seconds, agent_steps**) is the granularity the RSC page NEVER embeds — it explains why
  pass/pass tasks can score low (some of the 5 attempts fail / cost more). DB tables: swe_bench_runs,
  swe_bench_run_validations.
- **API access (live probe):** `platform.thesoma.ai/api/public/frontend-key/...` = 401 (needs key);
  `/api/private/frontend/...` = 403 (private net); `thesoma.ai/api/...` = 404.
- **CORRECTION — per-run is KEYLESS via the dashboard's own Next.js server action.** No API key needed.
  The dashboard renders per-run rows by POSTing the server action `getSweTaskRunsAction` to
  `/dashboard/miner/{comp}/{hk}` with header `Next-Action: <hash>` and body `[comp, hk, task_id]`;
  the Flight `1:` line returns `runs[]`. The action-id hash is auto-discovered from the page JS bundle
  (survives redeploys). Tool: **`scripts/collect_runs.py` (make runs)** — vendored from
  E:/extension-sb114/soma_scraper.py (proven). The key-based fetch_platform_api.py was removed as redundant.
- **task→category map RESOLVED** (was the big missing piece). E:/extension-sb114/out/task_categories.json
  gave the 45-task E/M/H split (18 Medium, 14 Hard, 13 Easy) → config/task_categories.csv. Medium/Hard
  task-level attribution + H2 are now UNBLOCKED.
- **Per-run variance is real but is a NEAR-UNIVERSAL NOISE FLOOR, not m7's competitive gap** (full per-run
  sweep, 20 miners × 50 × 5 = 5000 runs, 2026-06-21). A 'pass/pass' task can score low because 1-of-5 runs
  breaks (−4): m7 has 19 flaky tasks / 15.3% of runs negative. BUT the top miners are the SAME: t1–t4 run
  13.6–14.4% negative, others 15.6–17.5% — m7 (15.3%) ≈ the leaders. So consistency is NOT where m7 loses.
  (m9/m10 at 22% ARE worse — part of why the flip variants cratered.) The idealized "fix all flaky runs"
  upper bound (~+0.68/45 for m7) helps everyone equally; it is not a differentiator. **Primary competitive
  lever stays COMPRESSION DEPTH** (m7 ~3.0× vs leaders ~4.9× on shared passes). Per-run data:
  data/processed/run_scores.jsonl; reports/run_variance.md. (Corrects an earlier over-claim that consistency
  was a co-equal lever.)
- **Per-task score is NOT pass + token-ratio alone.** Several pass/pass tasks score negative for m7
  (e.g. sympy-15809 ✓→✓ score −0.767, django-15499 ✓→✓ 0.237). run_count=5 → score averages 5 runs;
  some runs fail/cut off even when the task is marked "pass_with_compression". Variance is real per-task.
- **ROOT CAUSE of the real-eval block = WSL2, not Docker Desktop (CONFIRMED 2026-06-22).** The OpenClaw `rm .openclaw/sandbox-skills/skills: Device or resource busy` reproduces on BOTH Docker Desktop's WSL2 backend AND native docker.io 29.1.3 installed in WSL, on openclaw 2026.6.9 + 2026.6.8-beta.2, root + non-root — identical. Sole common factor: WSL2 kernel 6.18.33.1-microsoft-standard-WSL2 (mount-namespace/propagation under Docker-in-Docker leaves the skills bind-mount un-removable). User's past WORKING laptop was macOS (Docker Desktop = LinuxKit Linux VM, normal mounts). FIX: run the eval on a real-Linux Docker host (macOS/native Linux/VM/cloud), NOT WSL2. Turnkey: experiments/candidates/H1M_m7_deeper_safe_v1/run_real_eval.sh. ~$0 spent (agent dies ~12s pre-LLM every attempt).
- **Real eval stack BUILT but blocked by an upstream OpenClaw bug (2026-06-22).** Full stack works: uv+soma-bench, SWE-rebench harness (swebench 4.0.3), plugin, Docker builds compression-service(666MB)+django SWE-bench image(3.94GB)+alpine/openclaw+dind, m7 miner injected into the compression service (ready :8000), model openrouter/qwen/qwen3-coder. BUT the OpenClaw agent dies ~12s in workspace prep: `rm .openclaw/sandbox-skills/skills` fails — Permission denied (uid1000) / Device-or-resource-busy (root, it's a bind-mount). alpine/openclaw:latest seeds a root-owned skills bind-mount then rm's it. NOT an H1M/config issue; ~no spend. Config fixes found along the way: COMPACT_BENCH_COMPRESSION_SERVICE_CONTEXT=/mnt/e/soma/sandbox_service/compression_service, remove docker credsStore(desktop.exe), COMPACT_BENCH_LLM_BASE_URL, COMPACT_BENCH_PLUGIN_TEMPLATE_PATH, SOMA_OPENCLAW_USER=root. Unblock: pin a known-good openclaw image tag / skills-disable / raise with DendriteHQ. reports/H1M_real_eval.md, data/latest/h1m_real_eval_smoke.json.
- **Real SWE-bench eval is BLOCKED on infra not present here (2026-06-22).** Probe: Docker daemon NOT
  available (docker-desktop WSL distro Stopped; Docker Desktop not running), and soma_bench / openclaw /
  SOMA-benchmark / SOMA-plugin are absent (external; referenced only as /path/to/... in the miner README;
  no URL in this repo — likely private DendriteHQ). The eval runs OUTSIDE this ops repo: openclaw solves a
  SWE-bench task inside per-instance Docker images (ghcr.io/epoch-research/swe-bench.eval.x86_64.<inst>) with
  the miner injected as <SOMA-plugin>/base_miner.py via `python -m soma_bench benchmark-solve`. UNBLOCK needs
  (user): start Docker Desktop + WSL integration; provide+`pip install -e` SOMA-benchmark + the SOMA-plugin.
  Prepared & ready: experiments/manifests/H1M_real_eval_medium_first.yaml, candidate run_smoke_real_eval.sh
  (guarded; key read from secrets.env, never printed), and the proven --results gate. Smoke NOT run; no
  results invented. Cost est: smoke ~$3-18/1-3h; full Medium-first ~$10-60/3-9h (model + runs_per_task driven).
- **H1M real-task experiment run (2026-06-22): experiments/runs/2026-06-22_005707_H1M_eval/.** REAL m7
  baseline on the 7 Medium-first targets = 7/7 pass, 0% neg-run, 0 broke, avg 3.02×, Medium est score 1.690;
  fragile group (sympy-17139/-16766/django-11239/-14493) m7 baseline = pass 0.75, neg-run 40%, broke 1 (only
  sympy-17139 — the rest are flip-only breaks, m7 clean). Candidate projection (offline proxy × m7): h1m@deep
  ~3.43× (+13.7%, est +0.064/task), h1m@medium ~3.34× (+10.8%). Offline gate PASS (ratio≥8%, guard fires,
  protections intact); real pass-rate/neg-run/broke = PENDING_EVAL (SOMA SWE-bench; per-call contexts not
  available offline). Verdict: ADVANCE candidate-only; do NOT promote to base until the eval confirms.
- **Candidate H1M_m7_deeper_safe_v1 built + offline-validated (2026-06-21).** m7 derivative; a profile layer
  deepens ONLY the harvest path (lower TARGET 8k→{7k,6k,5.2k} + tighter MID/MID2/ASSIST/TAIL caps); rich path,
  all protections (load-bearing, ERROR_MARKERS, active paths, recent-intact, digest), and coach are UNCHANGED;
  fragile guard fires one error-hit sooner (ERROR_GUARD_MIN_HITS 4→3). Offline (ratio+structural-safety on
  sample+synthetic transcripts via the compression-service protocol): **h1m@deep = +13.7% deeper on 6/6 clean
  harvest cases, 0 regressions, 100% protected content kept, 0 broken tool-pairing**; fragile guard correctly
  sends error-dense transcripts to rich. A/B sanity: H1M_PROFILE=m7 ≡ m7 exactly. ~est per-call score lift
  (1+0.5ln model) +0.06 (deep). **PENDING_EVAL:** real platform pass-rate/neg-run/Medium need the SOMA SWE-bench
  env — NOT measurable offline, not invented. Files: experiments/candidates/H1M_m7_deeper_safe_v1/ (h1m_miner.py,
  h1m_eval.py), experiments/reports/H1M_m7_deeper_safe_v1.md, data/latest/h1m_candidate_results.json.
- **Deeper compression is NOT riskier (2026-06-21 risk analysis).** On shared-pass tasks, corr(ratio,
  neg-run-rate) ≈0 / slightly negative every category (overall −0.09; Easy −0.22, Med −0.03, Hard −0.12).
  27/36 shared-pass tasks have a leader passing CLEANLY (≤1 neg) at ≥4.5× → leader-level depth is
  demonstrably pass-safe. ⇒ H1 (deeper pass-safe compression) is the right call. reports/compression_depth_risk.md.
- **Per-category gap (m7 vs top-4):** Easy gap +0.41 & m7 is FLAKIEST here (26% neg-runs vs 20%) — m7's worst
  category. Medium gap −0.17 (m7 BEATS the top-4 average) & m7 is most STABLE (4.4% vs 10.1%) at only 2.84×
  → Medium = m7's strength + safest place to push depth + closest reward (1.421 vs 1.620). Hard gap +0.36;
  leaders compress DEEPER (5.40×) AND are LESS flaky (14.5%) than m7 (3.53×, 21.7%) → Hard flakiness is not
  caused by depth. reports/per_category_gap.md, data/latest/per_category_gap.json.
- **2 catastrophic Hard gaps are SOLVING gaps, not compression:** django-14999 (m7 1.10 vs leader 4.01 at
  ~equal ratio 2.46 vs 2.68) and sympy-22714 — m7 fails/flaky where the leader solves. Compression won't fix these.
- **Only ~4 fragile tasks total:** m7 breaks just sympy-17139; sympy-16766/django-11239/django-14493 were broken
  ONLY by flip variants (m9/m10/m11) → another nail in flip-routing. H1 targets: 19 safe / 12 moderate / 5 fragile.
- **NOTE token-type split still MISSING** (one compressed-token count per run; no input/cached/output) → H4
  weighted-cost + "compression vs output-token" remain blocked.
- **FIRST REAL SWE-bench eval RAN — on the Mac (2026-06-22). H1M smoke complete + VALID.** The WSL2 block is
  gone on macOS Docker Desktop. `run_real_eval.sh` had 4 latent bugs (it had never completed a solve anywhere):
  (1) Bash-4 assoc arrays → macOS ships Bash 3.2 (rewrote as `case`); (2) missing `--openclaw-current-user`
  (mandatory on macOS); (3) missing the macOS gateway env (`SOMA_HOST_DOCKER_BINARY`=arm64 static CLI +
  `SOMA_OPENCLAW_GATEWAY_IMAGE`=2026.5.27 pin + settle) — all baked into the .env it writes; (4) **`H1M_PROFILE`
  is NOT referenced in soma_bench → the host env var never reaches the compression container, so the miner
  (read at import) defaulted to "medium" and `h1m@deep` silently ran as medium.** FIX: bake the profile INTO
  `base_miner.py` (the file IS what's copied to `/app/miner/base_miner.py` in the container), via sed on copy.
  All 4 fixed; spend ~$0.15 total (failures were all pre-LLM).
- **H1M smoke RESULT (corrected run 2026-06-22_044503, profiles genuinely distinct): deeper compression is
  PASS-SAFE.** m7 / h1m@medium / h1m@deep each **resolved 2/2** (django-10914, django-15851), F2P + P2P 100%,
  0 new broken baselines, 0 integrity errors. **Gate: h1m@deep = ACCEPT** (all 5 checks, ratio +13.9%);
  h1m@medium = REJECT on ratio (−35.5%) — **BUT that ratio check is single-run NOISE** (agent path varied
  16–37 calls/run, which dominates token totals). The RELIABLE depth measure stays OFFLINE (deep +13.7%,
  medium +10.8%, 0 regressions, protections intact). So both profiles are pass-safe on the 2 tested tasks;
  deep compresses deepest with the same safety. Real neg-run / pass-rate at scale = still need the full
  Medium-first set (7 tasks, multiple runs). Tools: `analyze_smoke.py`; gate CSVs rebuilt from
  evaluation-summary.json (NOT output.jsonl `resolved`, which is always None — verdict lives in
  `evaluation-summary.json.patch_evaluation`).
- **The top miners beat m7 on COMPRESSION RATIO, not pass-rate (2026-06-21 top-10 detail).** All scored
  miners share the same 34 baseline passes. Leaders 5EkiFXSR/5FbqgypX/5E7hCCzj/5ERdwbn5 run **~4.7–5.0×**
  mean compression while still passing 37–39/45; m7 runs only **~3.0×** (passes 38). On the 45 scored tasks
  5EkiFXSR beats m7 on 34/45, 5FbqgypX on 31/45 — almost entirely via deeper compression (bigger 0.5·ln(ratio)
  token bonus), not extra passes. Exception: Hard-king 5DhHqmB1 wins via pass-rate (40 passes) at only 3.06×.
  ⚠️ This refines the prior "compression at its ceiling / 8k harvest is the sweet spot" decision — leaders get
  ~5× without losing the pass, so there may be ratio headroom above m7's ~3×. (Strategy call left to user.)
- **Compression-techniques survey (web, 2026-06-22; reports/compression_techniques_research.md).** The
  leaders' 4.8–5× pass-safe is NOT a smarter model — it's disciplined EXTRACTIVE masking. Three findings
  change our approach: (1) **CACHE-STABILITY is likely the leaders' real edge** — a prefix-mutating
  compressor cache-thrashes (cache_read invalidated → MORE tokens, not fewer); Manus reports cached input
  10× cheaper. So compression must be APPEND-ONLY / stable-prefix (keep system+task+recent-tail byte-
  identical, elide only the MIDDLE). This may explain our noisy/high real-eval token totals (we may be
  cache-thrashing). (2) **Context Rot (Chroma) tested the Qwen3 family** — our model degrades as input
  grows even under the window cap, so DEEPER compression can IMPROVE pass-rate (removing stale rot), not
  just save tokens — reconciles the old "aggression→wander" (crude load-bearing loss hurts; rot removal
  helps). (3) **Mask tool-result BODIES, never drop the message** (keep msg+tool_call_id) — structurally
  prevents the −4 orphan-pair fail AND tool outputs are the bulk of the ratio. TRAPS for us: compress-to-
  embeddings (AutoCompressor/ICAE/xRAG — impossible over a text API) and abstractive LLM summary at the head
  (cache-busting + hallucination). Closest real-world patterns: SWE-agent LastNObservations + keep_output,
  OpenHands ObservationMaskingCondenser, Manus append-only+file-offload. Lost-in-the-Middle (2307.03172)
  backs eliding the middle. ⇒ for the king-depth sweep, watch CACHE behavior, not just total tokens.
- **H1M FOUNDATION BATCH (real eval, 2026-06-22; 15 tasks × m7 + h1m@deep × 2 runs; run 2026-06-22_052602).**
  Per-category (resolved / neg-runs / broke): **Medium deep 14/14, 0 neg, 0 broke (BEAT m7's 13/14 — deep
  resolved sympy-24539 where m7 flaked); Hard-bonus deep 4/4, 0 broke; Easy deep 4/4, 0 broke.** → deep is
  PASS-SAFE + shippable-class on the non-fragile categories. **FRAGILE: deep 4/8 vs m7 5/8; deep broke a P2P
  baseline on django-14493 that m7 kept (1 NEW break) + went 0/2 on django-11239 (m7 1/2).** **GATE = REJECT,
  solely on `no_new_broken_baseline_vs_m7` (django-14493)**; ALL other checks PASS — compression **+8.2% real**
  (cleared +8%), Medium neg-run 0% (=m7), Medium score no-drop, 0 integrity errors. → the fragile guard
  (ERROR_GUARD_MIN_HITS=3) does NOT fully protect under deep compression; harden/exclude fragile before
  shipping deep. **Token totals NOISY at n=2 + show likely CACHE-THRASH:** deep used MORE tokens than m7 on
  some tasks (10914 40.5 calls/657k vs 29.5/443k; 13363) and far LESS on others (15851 18c/182k vs 31c/360k;
  14752; sympy-17139) — path variance + prefix-mutation eating depth gains, exactly the cache-stability
  concern. ⇒ king plan: depth-push on Medium/Hard-bonus/Easy is safe; fragile needs guard work; realizing the
  king's 5× needs CACHE-STABLE (append-only) deepening, not just lower targets.
- **🔴 TOP OF COMP 107 FAILED REVIEW (2026-06-22, dashboard re-check — a NEW competition cycle has opened; the
  default /dashboard now shows it).** Per-miner comp-107 pages (`/dashboard/miner/107/<hk>`, status in escaped
  Flight JSON `\"status\":\"failed review\"`) confirm: **FAILED = t1 5EkiFXSR (1.460, overall king), t2
  5E7hCCzj (1.436), t3 5FbqgypX (1.415, MEDIUM king), t4 5DhHqmB1 (1.410, HARD king), t5 5GEUZcud (1.355),
  t7 5ERdwbn5 (1.263).** STILL SCORED = t6 5G6J5dA1 (1.335), t8 5EPkREJ9 (1.256), t9 5CJs9EmL (1.222),
  t10 5GgUhFiG (1.158) + all our miners. **Ratio is NOT the discriminator** (t10 survived at 5.24×; t5 failed
  at 2.40×; t4 failed at 3.06×) → it's a per-miner manual/compliance review, cause UNKNOWN from the data —
  MUST investigate (Discord/review notes) before doubling down on aggressive compression (DQ risk for our
  H1M/H3 deep candidates is unquantified). **RECOMPUTED reward elements among VALID miners (tracked set only —
  untracked ranks 11+ may shift it): Overall t6 1.334 / m7(us) #2 1.276; Medium t9 1.423 / m7(us) 1.421
  (≈TIE, +0.003 wins it); (M,H) t6 1.361 / m7(us) #2 1.351; Hard t6 1.525; Easy t10 1.373; (E,M) t9 1.321.**
  → m7 is suddenly top-tier (review-PASSING): #2 overall + a hair from the Medium element + #2 (M,H). The
  king target drops from t1 (1.460, 4.83× deep) to **t6 (1.335, 2.88× — NOT a deep compressor; wins via Hard
  1.525 + balance)** → extreme-depth chase is no longer required to be king-competitive.
- **H4_compliant_cache_stable BUILT + offline-green (2026-06-22) — the next-round legal candidate.** Copied
  H3's compression engine, stripped ALL prompt-side steering: removed the coach (append_coach/build_coach_text/
  governor), force-stop ("STOP NOW"/"do not explore"/"if tests pass stop"), behavior-steering, and ALL private
  markers ([SOMA COMPRESSED HISTORY], [SOMA CONTEXT NOTE], [old output elided…]) + dead digest helpers. Now uses
  ONLY allowed markers (`[[CMP]]`/`[[/CMP]]` for masked/truncated regions; `[[BLOCK N]]` + `Same response as in
  [[BLOCK N]].` for dedup/superseded views) and loop-detection emits ONLY `loop_detected: repeated assistant
  response` / `loop_detected: repeated tool call signature`. Kept the full engine (cache-stable harvest, frozen
  head, masking, superseded-view elision, sticky keep-list, fragile guard, rich, load-bearing allowlist,
  pairing). **New scanner `scripts/check_prompt_compliance.py`: PASS on H4, FAIL on H3 + m7 (coach detected).**
  Offline: 12/12 tests PASS; **H4 compresses +5.69% vs H3** (compact markers replace verbose private ones; +15–18%
  on harvest synthetics); **prefix-stability identical to H3 (no regression)**; 0 protection regressions. Files:
  experiments/candidates/H4_compliant_cache_stable/{h4_miner.py,h4_eval.py}, scripts/check_prompt_compliance.py,
  data/latest/h4_compliance_results.json, experiments/reports/H4_compliant_cache_stable.md. NOT real-eval'd yet.
- **🔬 H3 CACHE-STABLE EVAL FALSIFIED THE CACHE THESIS — h1m_deep WINS (2026-06-22, run 2026-06-22_122215;
  m7 / h1m@deep / h3@cache_safe / h3@cache_king × 4 fragile + 4 Medium × 2 runs).** GATES: **h1m@deep =
  ACCEPT** (+28.1% real compression, 0 new breaks, Medium 8/8 vs m7 6/8); **h3_cache_safe = REJECT** (1 new
  break + compression **−12.8%**, WORSE than m7); **h3_cache_king = REJECT** (1 new break, +18.7%). Per-category
  cache_hit: fragile m7 0.84 / h1m 0.81 / **h3_safe 0.73 / h3_king 0.67**; Medium m7 0.63 / h1m 0.68 /
  h3_safe 0.70 / **h3_king 0.58** — **H3 cache_hit is LOWER than h1m, the OPPOSITE of its design goal** (one
  h3_king/sympy-24539 run had 0 cache_read), and H3 fresh-input + tokens are HIGHER. **The cache-stability
  re-architecture did NOT pay off in the live eval** — the digest-in-msg1 (h1m) cached BETTER than H3's "fix";
  per-message `[[CMP]]` masking makes MORE fresh-input bytes than bulk truncation, and the offline prefix-
  stability proof didn't translate to live cache gains. ROBUST across the noise: **Medium is pass-safe +
  more-reliable than m7 for ALL compressors (8/8 vs m7 6/8); fragile breaks MORE under any deep compression**
  (h3 2–3 new breaks vs h1m/m7 1; guard still imperfect). ⇒ **DROP the cache-stable H3/H4 engine; h1m@deep is
  the better base.** The next-round COMPLIANT candidate should apply the H4 coach-strip + `[[CMP]]` markers to
  **h1m@deep's engine, not H3's.** (n=2/task caveat, but gate + cache + break signals all agree.)
- **m12 (m7-compliant) FIRST NEW-ROUND SCORE — CoT-Compression-4/comp108 (2026-06-22): SCORED, PASSED REVIEW,
  total 0.768 = currently #1 among SCORED miners.** Cats Easy 0.412 / Medium 0.953 / Hard 0.919. → our
  compliant (coach-free, [[CMP]]) approach is review-clean + competitive. Per-task (45 non-screener): miner-pass
  33 vs baseline-pass 29 (**+4 flips**), mean ratio **1.75×**, mean score 0.738, **11 NEGATIVE-score tasks**.
  **DRAG DIAGNOSIS (gap analysis):** (1) **Easy 0.412 is the weak category** (vs M/H ~0.93) — same structural
  Easy weakness as old m7. (2) **7 baseline-PASS tasks scored NEGATIVE** (we broke / over-compressed): tasks
  270 (−1.98, failed a base-pass), 297 (−1.83, failed), 313 (−1.03, ratio 0.66× = we INFLATED tokens!), 292/295/
  307 (passed but run-variance negatives). These −1 to −2 hits are the main score drag. (3) flips modest (+4)
  and partly EATEN by the 7 broken baselines. Head-to-head vs #2 5GYxeJjd (0.661): m12 wins 24 / loses 21
  (CLOSE) — we win via more compression (1.75× vs their 1.34×) where we don't break, but LOSE the tasks we
  broke (rival is GENTLER → keeps those passes; e.g. task 295 m12 −1.02 vs rival +1.09). **LEVER = RELIABILITY,
  not more depth: cut the over-compression breaks (esp. Easy + the 7 base-pass negatives) by routing break-prone
  tasks gentler/pass-through — deeper (H4b) would break MORE, the wrong direction for this round.** Threat:
  5CwZBKyL in-queue 1.062 but only 5 screener tasks done (provisional, not a full eval yet).
- **NEW-ROUND SCORING + QUALIFICATION GATE decoded from DendriteHQ/SOMA source (2026-06-22; no new commits
  since the policy — origin/main 82dfc28, README_prompting unchanged → our compliance still holds).** Two
  mechanics, both new for comp 108:
  **(A) Per-run SCORE (mcp_platform/app/api/routes/scoring.py):** `score = base + λ·clamp(ln(ratio), −2, +2)`
  where ratio = tokens_without/tokens_with, and base/λ by pass-outcome: **pass→pass = +1.0 (λ0.5); break
  (base-pass→compressed-FAIL) = −4.0 (λ0, flat); FLIP (base-fail→compressed-pass) = +4.0 (λ0.5); both-fail =
  0 (λ0.1).** Displayed per-task score = mean of the 5 runs (so a "passing" task with some broken runs averages
  negative — explains m12's −1 to −2 "pass" tasks = run-variance breaks). There is ALSO an aggregate savings
  MULTIPLIER (`adjust_miner_score_with_token_savings`: −4+(raw+4)·smoothstep) that crushes scores toward −4 as
  savings→≤−20%. **Dominant terms: breaks −4 (flat) and flips +4 dwarf the compression term (±λ·ln ≈ ±0.3 at
  our 1.75×).** → **Avoiding a −4 break is worth ~3 clean pass-pass tasks; flips (+4) are gold.** Confirms
  reliability-first (m12.1's 1b break-cut is the top lever); compression ratio is a secondary per-task bonus.
  **(B) Screener QUALIFICATION GATE:** must achieve **≥10% WEIGHTED token savings** to qualify, weights
  **input×1.0 + cached_input×(1/3) + output×3.0** (configurable). The comp-108 "not qualified" miners failed
  this; m12 cleared it. **Output weighted 3× → reducing agent OUTPUT/steps (less wander via cleaner context)
  is the high-value gate lever; cached-input savings (our bulk) count only 1/3.** ⇒ strategy: (1) never break
  (−4), (2) win/keep flips (+4), (3) keep ≥10–20% real savings + reduce wander/output (gate + multiplier),
  (4) Easy is structurally low partly because short tasks lack compressible content to clear the savings floor.
- **NEW KING in comp 108 = 5DFvymSeEw (0.7801), barely above m12 (0.7685, +0.012) — and it's a MIRROR IMAGE
  of us (2026-06-23).** Category gap (king − m12): **Easy +0.401 (king 0.812 vs m12 0.412), Medium −0.019
  (m12 0.953), Hard −0.323 (m12 0.919 vs king 0.596).** We WIN Hard + Medium decisively and LOSE only Easy —
  but the Easy gap (+0.40) just outweighs our Hard lead (+0.32). KEY: the king does NOT beat us on the hard
  stuff — m12 passes MORE (33 vs 30), more FLIPS (7 vs 5), far better Hard; the king simply has FEWER NEGATIVES
  (7 vs m12's 11) at the SAME compression (~1.77× vs 1.75×), and those extra m12 negatives concentrate in EASY.
  ⇒ **The entire deficit to #1 is EASY RELIABILITY (cut our Easy breaks/run-variance/inflation negatives).
  That is EXACTLY what m12.1 targets** (never-inflate + shallow_small→passthrough + fewer breaks) — and it does
  NOT touch our Hard 0.92 moat (king is only 0.60 there). If m12.1 lifts Easy from 0.41 toward ~0.7+ while
  holding Hard, total → ~0.88+ >> king 0.78. CAVEAT: the m12-vs-m12.1 regression set is fragile+Medium (no
  Easy instances — comp-108 task names masked), so m12.1's Easy lift is a platform bet; ADD known-Easy
  SWE-bench instances (from config/task_categories.csv) to a follow-up eval to validate the Easy gain directly.
- **m12.1 REGRESSION EVAL VERDICT (2026-06-23, run 2026-06-22_235242, m12 vs m12.1, 8 tasks×2): DO NOT SHIP —
  m12.1 OVER-ROUTED Medium.** Breaks: m12.1 fragile=2 vs m12=3 (1 fewer — marginal reliability win); Medium
  breaks 0 for both. BUT tokens-PER-CALL (robust to call-count noise) shows **m12.1 uses +28% more tokens/call
  on Medium** (m12 17162 → m12.1 22009; consistent +25/+33/+4/+43% across all 4 Medium tasks) = ~28% LESS
  compression on Medium → lower ratio → lower Medium score. The 1b gentle routing (shallow_small→passthrough +
  earlier error-guard 24/6/3) is too aggressive — it catches compressible MEDIUM tasks and routes them to
  rich/passthrough, surrendering our Medium strength for a 1-break gain. BAD trade vs the strategy (grow/keep
  H+M). **FIX → m12.1b: keep 1a never-inflate (pure win, no downside); DROP/narrow the shallow_small→passthrough
  route + revert the over-sensitive error-guard so it fires ONLY on persistent/genuinely-break-prone signals,
  NOT shallow-Medium.** m12 stays live; do not replace with m12.1.
