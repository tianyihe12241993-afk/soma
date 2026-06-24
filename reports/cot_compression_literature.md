# CoT-Compression literature scan — what helps us, what can't (2026-06-24)

_Prompted by the user: find the famous CoT-compression papers/repos and judge whether they help our SN114
comp-108 miner. The decisive filter is our two hard compliance rules:_
1. **The miner may NOT call an LLM** (no OpenRouter/model call inside the compressor). It is a deterministic
   text→text transform run between agent turns.
2. **We do NOT train or control the solving model** (qwen3-coder via OpenRouter). We can't fine-tune it.

These two rules sort the entire field. Most famous methods need an LM scorer *or* model fine-tuning — both
banned. So the literature's value to us is mostly **confirmatory + principle-level**, not plug-in code.

## The three families and our verdict on each

### A. Learned token-pruning prompt compressors — NON-COMPLIANT (can't use the method, can borrow the principle)
- **LLMLingua / LongLLMLingua / LLMLingua-2** (Microsoft, EMNLP'23/ACL'24) — a small LM (GPT2/LLaMA) scores
  token perplexity, coarse-to-fine drops low-info tokens; up to 20× with small accuracy loss. `microsoft/LLMLingua`.
- **Selective Context** (Li et al., EMNLP'23) — a base LM computes *self-information* per lexical unit; drops the
  low-self-information ones. 2× content, −40% memory. `liyucheng09/Selective_Context`.
- **Verdict:** the compressor IS an LLM call → **banned for us**. BUT the core principle ("drop the
  lowest-information, most-predictable tokens; structure matters more than prose") is implementable
  *deterministically as a proxy* (see §Actionable).

### B. CoT step/token compression via fine-tuning — INAPPLICABLE (we don't own the model)
- **TokenSkip** (EMNLP'25, `hemingkx/TokenSkip`) — prune unimportant CoT tokens, LoRA-finetune the model to emit
  the short CoT. 40% fewer tokens, <0.4% accuracy drop on Qwen2.5-14B.
- **LightThinker** (EMNLP'25) — train the model to compress thoughts into "gist" tokens mid-generation; up to 70%
  token cut, 26% faster, marginal accuracy drop.
- **C3oT** (Kang et al., 2025) — train on long↔short CoT pairs (uses GPT-4 as the compressor in data prep).
- **Verdict:** all require **fine-tuning the solver** (and C3oT uses GPT-4 to build data). We sit *outside* the
  model as a deterministic transform → **none applicable**. Useful only as evidence that ~40% token reduction is
  achievable with tiny accuracy loss *when the model is trained for it* — we have neither lever.

### C. Agent context/memory management — SAME SETTING AS US → most informative (findings transfer, code doesn't)
- **ACON** (Optimizing Context Compression for Long-horizon LLM Agents, arXiv 2510.00615) — closest paper to our
  problem. A compressor LLM summarizes (a) interaction history and (b) latest observations, but ONLY past a length
  threshold. **Key findings (these transfer to us):**
  - **Moderate thresholds beat aggressive.** "Smaller thresholds reduce tokens but incur more frequent compression
    and DEGRADE accuracy; larger thresholds preserve accuracy at higher cost." → independent confirmation of our
    EXP-1 result (deeper compression → agent wanders → worse).
  - **Preservation priorities** (what compression must keep or the agent fails): factual history, **action→outcome
    relationships**, evolving environment state, success preconditions, task-relevant decision cues.
  - Naive prompting fails; they tune the guidelines via contrastive "full-context-passes / compressed-fails"
    failure analysis. (Their tuning uses o3 — non-compliant for us, but the *category list* is reusable.)
- **Active Context Compression** (arXiv 2601.07190, Jan 2026) + LangChain/DeepAgents context-management writeups —
  same theme: prune redundant history, "store signatures/metadata not full tool outputs," consolidate to a
  knowledge block. The deterministic ideas ("for code searches store function signatures not full
  implementations") are borrowable; the autonomous-decision parts are LLM-driven (banned).
- **Verdict:** the compressor LLM is banned, but the SETTING is identical (long-horizon tool-using agent solving
  tasks) so the **findings are the most trustworthy guide we have** for a deterministic compressor.

### D. Cross-cutting findings that DO transfer (no LLM needed)
- **Lost in the Middle** (Liu et al. 2023) — U-shaped recall: models use head + tail well, lose the middle (>30%
  drop). RoPE long-term decay + softmax concentration. → **Actionable for HOW we truncate:** protect the task
  statement (head) and most-recent state (tail); compress the *middle*. Check whether our harvest already does this.
- **DocString Compression** ("Less is More," arXiv 2410.22793) — rule-based docstring trimming; finding: **code
  generators rely on code structure/signatures far more than on natural-language prose** → in code contexts, prose
  verbosity is the safe thing to trim, code blocks/signatures/diffs/tracebacks are the thing to keep.
- **Dedup** (our existing `[[BLOCK N]]`) — the whole field agrees redundancy removal is the safest, near-lossless
  compression. Our dedup is already best-practice; literature says lean into it harder (near-dup, repeated tool
  outputs, repeated file dumps), not into lossy token-dropping.

## What this means for OUR miner (the honest bottom line)
1. **No famous method is plug-in usable.** Every high-compression result in the literature buys its ratio with
   either an LM scorer (LLMLingua/Selective Context/ACON) or model fine-tuning (TokenSkip/LightThinker/C3oT).
   Both are banned. Anyone citing "20× compression with no accuracy loss" is using a tool we cannot use.
2. **The literature CONFIRMS our EXP-1 conclusion.** ACON independently finds aggressive compression degrades
   long-horizon agent accuracy and moderate is best — exactly our "deeper → agent wanders → worse, m12's ~1.75×
   is near the equilibrium." This strengthens **HOLD m12; depth is not the lever.**
3. **The one compliant, NEW direction the literature points to: content-SELECTIVITY, not depth.** Reframe the lever
   from "how hard to compress" (EXP-1 killed that) to "WHAT to protect vs compress" — a deterministic content-aware
   harvest that:
   - **Protects action→outcome pairs** (error messages, test/traceback output, file diffs, the latest state) —
     ACON says losing these is what makes the agent fail.
   - **Compresses prose/boilerplate/log-noise** (verbose narration, repeated banners, ANSI, restated obvious docs)
     — DocString + Selective-Context principle: prose is low-information in a code task.
   - **Protects head + tail, compresses the middle** — Lost-in-the-Middle.
   - **Leans harder on dedup** (near-dup blocks, repeated tool outputs) — safest ratio gain.
   This targets **run-variance / breaks** (our biggest leak per comp108_headroom.md) WITHOUT raising aggressiveness
   — it's a refinement of `compress_gently`'s selection, not a TARGET_TOKENS change. Compliant (pure deterministic
   rules, no LLM, no task-ID, no steering), and it's the only literature-backed idea that isn't already ruled out.

## Caveats before acting
- This is a HYPOTHESIS, not a proven win. Any content-selectivity change must clear the same bar as everything
  else: **same-window local A/B on the real comp-108 tasks**, must NOT regress M/H (the moat), must net positive
  after the weighted-token-savings gate. The literature lowers the search cost; it does not lower the eval bar.
- Risk: "protect code, compress prose" can backfire if the agent actually re-reads compressed prose it needed.
  Lost-in-the-Middle and ACON both warn that the *wrong* drop is what breaks agents. So: protect-list first
  (additive, low risk), aggressive-drop second (only if A/B shows headroom).
- This does NOT touch Easy (still agent-decisiveness-bound, dead lever) and does NOT chase ratio depth (illusory).
  It's a reliability play on M/H + flips, which is where comp108_headroom located the real points.

## Sources
- LLMLingua — https://arxiv.org/abs/2310.05736 · https://github.com/microsoft/LLMLingua
- Selective Context — https://arxiv.org/pdf/2503.19114 (info-preservation follow-up) · https://github.com/liyucheng09/Selective_Context
- TokenSkip — https://arxiv.org/pdf/2502.12067 · https://github.com/hemingkx/TokenSkip
- LightThinker — https://arxiv.org/html/2502.15589v1 · https://aclanthology.org/2025.emnlp-main.673/
- Awesome-Efficient-Reasoning-LLMs (survey/repo index) — https://github.com/Eclipsess/Awesome-Efficient-Reasoning-LLMs
- ACON (long-horizon agent context compression) — https://arxiv.org/html/2510.00615v1
- Active Context Compression — https://arxiv.org/abs/2601.07190
- DocString Compression ("Less is More") — https://arxiv.org/pdf/2410.22793
- Lost in the Middle — https://arxiv.org/html/2510.10276v1 (mechanism follow-up to Liu et al. 2023)
