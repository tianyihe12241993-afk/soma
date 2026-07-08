# COPILOT CLI AGENT PROFILE (comp-110) — 2026-07-08
_141 captured runs profiled; 118 with graded outcomes (26 baseline / 92 candidate); provider pinned to DeepSeek._

## 1. History behavior
- Request size grows MONOTONICALLY; **NO client-side compaction or summarization ever** (33 apparent shrinks = `task`-tool SUB-AGENT threads with different system prompts — Copilot spawns sub-agents whose smaller histories interleave in the capture; the main thread never shrinks).
- Old tool results ARE re-sent verbatim every turn; assistant messages fully preserved; system prompt (23.5k) re-sent every request. Tool schemas live in the `tools` payload field (outside the miner's messages surface).

## 2. Good-run vs flail-run (same tasks, fastest-3 vs slowest-3)
- fast≈10 steps vs slow≈41. Extra steps = **bash +18.1, test runs +8.9, edits +2.8** vs re-reads only +4.5.
- Slow mode = FIRST FIX WRONG → test→edit→test loops (up to 17 test runs). Fast mode = right fix first try.
- The 8→51-step spread exists in PURE BASELINE runs (e.g. 15375 baseline draws: 8, 11, 20, 63 steps) — it is model stochasticity, not compression.

## 3. Re-read/flail triggers (causal analysis, n=118)
- **FLAIL RATE: baseline 12% vs candidates 16%; steps mean 27.3 vs 27.5** — compression adds only ~4pts of flail probability. Flails are mostly the agent's own lottery.
- markers vs steps corr +0.65, and flail runs carry 1556 markers vs 211 — but with near-equal flail rates this is largely REVERSE causation (longer runs accumulate more compressed history). Platform-verified causal exceptions: compressing the FRESH read (recoff → breaks) and interior-ultra-250 on Medium.
- Old-evidence REMOVAL (evidence-window) does causally inflate input (re-acquisition 2–3× input) on multi-read tasks; menus (line-range marker lists) correlate with targeted re-reads.

## 4. Tool-type taxonomy (tool_call_id-accurate; share of stream)
file-read 20.6% (UNTOUCHABLE — platform-proven breaks) · search/listing 7.4% (≈paths; must preserve) ·
bash-command 2.1% (median 96ch) · test-output 0.2% · traceback 0.1% · install 0.05% · other ~1.2% ·
protected roles (system 50.7%/user 6.8%/assistant 0.9%) = 68%. **Safe-compression ceiling = 0.4% of stream.**

## 5. Output/step
Output/step ≈ constant 270 tokens (fast 291, slow 269) ⇒ total output ∝ steps. Repeated reads: 2.9/run baseline (range-views mostly). Shorter runs' only pattern = correct first edit; no context feature predicts it.

## 6. Architecture implications
- VERBATIM required: fresh observation group, file reads, search results (paths), system/user, assistant msgs.
- Stub-able safely: bash/test/install noise — but it is ~2.4% of stream (irrelevant to Gate B).
- Flail causes (top 5): (1) wrong first fix → test-edit loops [dominant, stochastic]; (2) fresh-read compression [platform-fatal]; (3) old-evidence deletion → re-acquisition [evw, −26%]; (4) marker menus inviting targeted re-reads [secondary]; (5) infra dead-runs at ≥8 parallel lanes [local artifact].
- Safe compression targets (top 5, all tiny): install logs, repeated test spew (keep failures), long tracebacks (keep frames), bash stdout bulk, blank/ANSI noise. Sum ≈ 2–3% of stream.
- **EVIDENCE-WINDOW verdict: does NOT match the agent** — Copilot re-acquires deleted evidence at input-weight 1.0 (input 2–3× baseline; −27.6% pinned). The agent genuinely re-uses old tool results.
- **Gate B structural equation:** weighted ≈ f(steps) — steps drive cached re-send mass AND output. Content compression saves ≤~15% honest; step count is model-stochastic; no compliant message transform shortens it. **The screener is substantially a draw lottery around a sub-20% mean for every visible strategy** — consistent with 1/50+ field qualification.

## Redesign recommendation
No content architecture reaches Gate B on this agent under this formula. The evidence supports: HOLD
(stop-rule), keep f1km (Gate-A 25/25) frozen, treat eval-period announcements (PR#176 + comp-111 formula)
as the re-entry trigger. If leadership wants a lottery shot before 13 Jul: f1kt/f1km-class (~14-17% honest
mean) needs a ~+1σ draw-set to clear 20% — a gamble, USER decision, not an engineering recommendation.
