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
- **The top miners beat m7 on COMPRESSION RATIO, not pass-rate (2026-06-21 top-10 detail).** All scored
  miners share the same 34 baseline passes. Leaders 5EkiFXSR/5FbqgypX/5E7hCCzj/5ERdwbn5 run **~4.7–5.0×**
  mean compression while still passing 37–39/45; m7 runs only **~3.0×** (passes 38). On the 45 scored tasks
  5EkiFXSR beats m7 on 34/45, 5FbqgypX on 31/45 — almost entirely via deeper compression (bigger 0.5·ln(ratio)
  token bonus), not extra passes. Exception: Hard-king 5DhHqmB1 wins via pass-rate (40 passes) at only 3.06×.
  ⚠️ This refines the prior "compression at its ceiling / 8k harvest is the sweet spot" decision — leaders get
  ~5× without losing the pass, so there may be ratio headroom above m7's ~3×. (Strategy call left to user.)
