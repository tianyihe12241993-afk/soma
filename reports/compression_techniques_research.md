# Context/Prompt compression techniques — survey + fit for our compressor
_Web-researched 2026-06-22 (sources cited inline). Our system: rule-based stdlib in-loop compressor,
every agent step, message-list in/out, black-box API model (qwen3-coder/OpenRouter). Reward ≈
1+0.5·ln(baseline/compressed) per pass; a compression-induced fail ≈ −4. Provider caches the prefix._

## Bottom line
The path to the leaders' ~4.8–5× (we're ~3×) **without pass loss is NOT a smarter compressor model** —
it is disciplined, structure-aware **extractive masking** that (1) never breaks tool-call/tool-result
pairing, (2) never moves the cached prefix, (3) protects an explicit load-bearing allowlist, (4) leans on
position/recency/persistence priors. This is exactly what SWE-agent / OpenHands / Claude Code / Manus do.

## What to borrow (ranked, concrete)
1. **Mask tool-result BODIES, never drop the message** (keep msg + tool_call_id; replace body with
   `[old tool output elided: N lines]`). Structurally prevents the −4 orphan-pair failure AND tool outputs
   are the bulkiest/most-redundant content → most of the ratio gain. (SWE-agent LastNObservations,
   OpenHands ObservationMaskingCondenser, Claude Code `[Tool result cleared]`.)
2. **Append-only / stable-prefix discipline; elide from the MIDDLE.** Keep system+task (the "sink") and
   recent tail byte-identical; do all eliding inside a stable middle region so the cached prefix never
   moves. Likely the leaders' real secret at 4.8–5× (Manus reports cached input 10× cheaper: $0.30 vs
   $3.00/MTok). TRAP: a front-of-context running summary rewritten each step (MemGPT / LangChain /
   Anthropic-compaction) is prefix-mutating → cache-busting → costs MORE.
3. **Elide superseded file views to a one-line reference.** On re-read/edit, replace earlier full views of
   the same path with `[file X: earlier view of N lines, superseded]`; keep only the current view verbatim.
   High ratio, near-zero pass risk. (OpenHands BrowserOutputCondenser, Aider repo-map split.)
4. **Load-bearing allowlist that overrides all elision:** tracebacks/errors, failing-test output, diffs,
   current active-file contents. Everything else elide-eligible. (SWE-agent `keep_output` tagging.)
5. **Stage-aware + recency-as-query budgeting, sticky keep-list.** Use the recent tail as the "query"
   (SnapKV) to score older spans by identifier/path/symbol overlap; keep top spans as contiguous chunks;
   pin a span once proven important rather than re-scoring (Scissorhands persistence → also keeps prefix
   stable); lighter ratio while exploring, harder once converging (PyramidKV). Approximate self-information
   (Selective Context) + heavy-hitters (H2O) in stdlib: down-weight boilerplate, up-weight rare
   identifiers/paths/errors.

## Two traps for our setting
- **Compress-to-embeddings (AutoCompressor / ICAE / xRAG): N/A** — emits soft-prompt embeddings only a
  model you control can ingest; impossible over a text-only API, regardless of their ratios.
- **Abstractive / LLM summarization at the head (MemGPT, LangChain, Anthropic compaction, sleep-time):**
  model dependency + latency, hallucinates away load-bearing detail, AND prefix-mutating → cache-busting.
  Stay extractive, deterministic, append-only.

## Two findings that change strategy
- **Context Rot (Chroma, https://www.trychroma.com/research/context-rot) tested the Qwen3 family** — our
  exact model rots as input grows, even below the window limit; distractors compound it. → **deeper
  compression can IMPROVE pass-rate, not just save tokens** (removing stale rot helps the agent). This
  reconciles our old "aggression → wander" finding: crude loss of load-bearing hurts; removing stale ROT
  helps. Smart deep compression is plausibly net-positive on solving.
- **Lost in the Middle (https://arxiv.org/abs/2307.03172):** ~20-pt accuracy swing by position; mid-context
  is worst. Eliding the middle both saves tokens AND moves survivors to where the model reads. Holds across
  GPT-4/Claude/LLaMA.

## Technique table (what / numbers / fit)
| technique | what | reported | fit for us |
|---|---|---|---|
| LLMLingua (arxiv 2310.05736) | small-LM perplexity token pruning | up to 20× | LOW — needs LLaMA-7B-class, slow in-loop |
| LLMLingua-2 (2403.12968) | BERT keep/drop classifier | 2–5×, 3–6× faster | MEDIUM — lightest ML option; borrow idea not model; not structure-aware |
| LongLLMLingua (2310.06839) | question-aware variant | ~4×, +21% NQ | LOW — small-LM dep; RAG-shaped |
| Selective Context (2310.06201) | GPT-2 self-information pruning | 20% cut, tiny loss | LOW–MED — borrow stdlib self-info heuristic |
| RECOMP (2310.04408) | extractive+abstractive RAG compressor | to 6% | LOW — trained models, per-step gen |
| AutoCompressor/ICAE/xRAG | compress to embeddings | 4×/3.5× | N/A — embeddings, not text |
| MemGPT/Letta (2310.08560) | OS-style paged memory, LLM-managed | — | LOW system; externalize-with-reference idea HIGH |
| Recursive summarization (2109.10862) | digest old, keep recent | — | MEDIUM — adopt shape, make it extractive |
| Anthropic context engineering | compaction / tool-result clearing | — | HIGH — tool-result clearing + recall-then-precision |
| Manus (manus.im/blog) | stable prefix, append-only, file offload | cache 10× cheaper | HIGH — our reference model |
| StreamingLLM (2309.17453) | attention sinks | — | N/A direct; keep head+tail, cut middle |
| H2O (2306.14048) | heavy-hitter KV | — | N/A direct; few spans carry the load |
| Scissorhands (2305.17118) | persistence of importance | — | N/A direct; sticky keep-list |
| SnapKV (2404.14469) | recent tail as query | — | N/A direct; recency-as-query scoring |
| PyramidKV (2406.02069) | stage-aware budget | — | N/A direct; phase-varying ratio |
| SWE-agent (2405.15793) | LastNObservations, keep_output, cache breakpoints | n=5, 100-line file cap | HIGH — closest pattern |
| OpenHands condenser | masking / amortized-forgetting / LLM-summary | API cost ~−50% | HIGH — masking + keep-first+recent drop-middle |
| Aider repo-map | tree-sitter+PageRank skeleton | map-tokens 1024 | MED principle, LOW mechanism |
| Cline/Roo | anchored summary + verbatim tail, prune old tool outputs | 20k buffer, tail=2 | MED–HIGH — token tail, prune, reserved buffer |
