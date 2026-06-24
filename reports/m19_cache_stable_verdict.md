# m19 cache-stable — build + offline validation VERDICT: REJECT (2026-06-24)

Built per approval (surgical cache-stable harvest; NOT an H3 port). Offline validation caught a failure BEFORE
any paid eval. m19 = reference-only; m12 untouched/LIVE.

## Deliverables
1. Source: `miner/cot_compression/upload_miner_m19_cache_stable.py`  · sha `dc4e51896fedd8bc2db21b505df3b7737cd56770`
2. Diff vs m12 (surgical): froze truncation depth (removed trunc2/assist_cap/tail_cap escalation → always MID,
   never MID2), drop loop extended from relief_chars → target_chars (absorb pressure via drops), zone caps made
   unconditional (fixed). No other changes.
3. Compliance: **PASS** (only allowed CMP/BLOCK markers; ZERO H3 private markers leaked — H3 NOT ported).
4. Determinism: **PASS** (same input → byte-identical output).
5. **Prefix-stability: FAILED to improve** — re-morph count m12=288 vs m19=**288 (0% reduction)**.
6. **Ratio audit: FAILED on medium** — small +0%, **medium +31% MORE tokens (lighter = M/H regression)**, large +0%.
7. H3 NOT ported: confirmed (drop-based harvest kept; no mask-in-place; no H3 markers).

## Why it failed (the root cause, now pinned)
The dominant prefix churn is NOT truncation-depth re-morph (which I froze) — it is **assistant tool-call
STRIPPING, inherent to m12's drop-based harvest.** When an old interaction is dropped, its toolResult is removed
AND the invoking assistant's tool-call block is stripped (`strip_tool_call_blocks`) to preserve pairing. As the
drop boundary advances each turn, more assistants get progressively stripped → their content morphs → churn.
Freezing truncation depth doesn't touch this; extending drops to target made it (if anything) worse. And removing
the MID2 deepening under-compressed medium tasks (+31% tokens).

## The fundamental tension (confirmed by build + measurement, not just theory)
m12's M/H-winning quality comes from its **drop-based, recency-graded** harvest. But:
- Dropping inherently churns the assistants whose orphaned calls must be stripped → cache-instability that can't
  be removed while keeping drops.
- The only churn-free alternative is H3's **mask-in-place / never-drop** — which is LIGHTER and changes M/H
  (the m13 failure mode), and uses non-compliant markers.
So **there is no compliant, M/H-preserving cache-stable rewrite of m12's harvest.** Cache-stability and m12's
drop-based M/H aggressiveness are in direct tension. The prefix churn (~3 msgs/turn net) is the inherent cost of
the design that WINS Medium+Hard.

## Recommendation: REJECT m19 → HOLD m12
Do not gate/eval m19 (offline validation already disqualifies it: no churn improvement + medium ratio
regression). Keep as reference. This also closes the cache-stability lever: the measurable churn is dominated by
drop-stripping, which is inherent to the M/H-winning drop harvest and not removable without an H3-style
M/H-changing rewrite. Combined with the forensic finding (breaks are first-decision solver stochasticity, before
harvest churn even engages), the −4-break gap to the king remains window/sampling variance, not a fixable m12
stability defect. **HOLD m12** — it is at our compliant ceiling on every measured axis. The validation gauntlet
working as intended (caught this offline, zero paid-eval cost) is the win here.
