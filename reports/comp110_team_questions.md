# comp-110 — questions for the SOMA team (Discord), 2026-07-07

Draft (USER to post/edit). Grounded in current upstream `9c1be25`: screener gate
`SWEBENCH_SCREENING_MIN_WEIGHTED_TOKEN_SAVING_RATIO=0.2`, cached weight `1/10`.

---

Hi team — a few clarifications on the comp-110 (CoT-Compression-5) scoring so we build to the right target:

1. **Screener savings gate timing/threshold:** Is the **≥20% weighted-token savings** requirement
   (`SWEBENCH_SCREENING_MIN_WEIGHTED_TOKEN_SAVING_RATIO=0.2`) a hard *qualification* gate that runs on
   the swebench_verified screener tasks *before* full evaluation — i.e. miss it and you're not scored at all?

2. **What the weighted token count includes:** Does the weighted total
   (`1·input + 1/10·cached + 3·output`) count the **full agent context** — system prompt, tool/function
   schemas and framing, cached tokens, and generated output — or only a subset? (We want to know how much
   of the total is even reducible by a context compressor.)

3. **Cached-token weight:** Is the cached-input weight now **1/10 everywhere** it matters (screener
   qualification AND the explore-layer tau/aggregate)? We see `1.0/10.0` in config as of today's merge.

4. **Intended qualification path:** Is the intended route to clear the savings gate primarily **context
   compression** (shrinking what's re-sent to the model), or **trajectory/output reduction** (helping the
   agent solve in fewer/tighter turns, cutting the ×3-weighted output)? With cached at 1/10 and output at
   3×, our analysis suggests pure context compression tops out well under 20% on the copilot agent's
   small-chunk reads, and that output reduction is the dominant lever — we want to confirm that's the
   intended design and not a misread.

Thanks!
