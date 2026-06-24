# H3 cache-stable harvest — port assessment (2026-06-24, de-risk before building m19)

Goal: can we port H3's `compress_cache_stable` into compliant m12 to fix m12's prefix-churn instability
(measured ~3 msgs/turn re-compressed, ~90% stable)? Conclusion: **the DESIGN is sound, but H3 is NOT a clean
port — build a surgical fix to m12's OWN harvest instead.**

## H3's design IS sound (validates the lever)
`compress_cache_stable` makes the harvest position-independent → byte-stable prefix:
- Frozen head (system + first user) + recent-intact tail = byte-identical always.
- Old tool results MASKED IN PLACE as a **pure function of their own body** (head/tail + pinned lines), never
  re-truncated by global state/position.
- Superseded file-views (a path re-read later) elided to a 1-line ref — MONOTONIC (flips once, then stable).
- Drop only as a last resort past a hard cap.
Each message transitions at most ONCE (intact→masked, or full→superseded-ref) → eliminates m12's repeated
re-truncation churn. So cache-stability is genuinely achievable. Good.

## BUT H3 is NOT portable cleanly — two hard blockers
1. **NON-COMPLIANT (confirmed: scanner FAIL).** H3 emits private/custom markers: `[SOMA`, `CONTEXT NOTE`,
   `COMPRESSED HISTORY` (docstring/H1M lineage) AND its mask functions emit `"[soma key lines: …]"`,
   `"[old output elided: N lines]"`, `"[old file view elided: … superseded by later read]"` — none are in the
   allowed set (only `[[CMP]]`/`[[BLOCK N]]`/"Same response as in [[BLOCK N]]." + 2 loop reasons). Porting
   requires rewriting ALL masking to use ONLY `[[CMP]]` wrappers.
2. **Changes M/H behavior (moat risk).** H3 MASKS in place / never drops (drop only past a hard cap) — that is
   LIGHTER than m12's drop-based harvest → different M/H compression ratio + content → the same softening risk
   that collapsed m13. Not byte-behavior-preserving on our M/H moat.

## The viable path: SURGICAL append-stability fix to m12's own harvest (borrow H3's PRINCIPLE, not its code)
m12's churn comes from re-truncating already-emitted old messages as pressure rises (the `trunc2` escalation
deepens MID→MID2 on messages it already emitted; the truncation boundary recomputes). The surgical fix:
- **Compress each surviving old tool result to a FIXED, content-only depth** (pure function of its own body),
  NOT escalation/position-dependent → an old message's emitted form never changes across turns.
- **Keep m12's existing DROP logic** (drop oldest under pressure) so aggressiveness / M-H ratio is preserved
  (new content + drops absorb pressure, not re-truncation of old survivors).
- **Keep m12's existing `[[CMP]]`/`[[BLOCK N]]` markers** → stays compliant by construction.
This eliminates the ~3-msg/turn churn, preserves M/H behavior (same drop aggressiveness, same markers), and is a
SMALL change (freeze the truncation depth of already-emitted messages) — NOT a wholesale harvest rewrite.

## Validation plan for the surgical m19 (before any paid eval)
1. compile + compliance PASS.
2. diff vs m12 = only the truncation-depth-freezing logic.
3. prefix-stability audit: re-run /tmp/m12_stability_audit.py → expect ~100% (churn → ~0).
4. M/H preservation: same-input harvest output ratio ≈ m12 (within a few %); unit-check that drops still fire.
5. small same-window gate (m12 vs m19, RUNS=5, MAXJOBS=3) on M/H tasks — must not regress M/H, should improve
   cache-hit; the −4-break impact is the open question (expected modest per the forensics, but low-risk to try).

## Recommendation
Do NOT port H3 (non-compliant + mask-vs-drop moat risk). **Build a surgical append-stability m19** — freeze the
emitted form of old harvested messages (content-only fixed depth), keep m12's drops + markers + aggressiveness.
It's the lowest-risk improvement available (perturbation-reducing, ratio-preserving, compliant-by-construction),
directly targets the measured churn, and on a 0.012 margin even a small reliability/cache gain could matter.
Honest caveat: forensics tie most −4 breaks to first-decision stochasticity (before harvest churn engages), so
expected break-recovery is MODEST — the firmer win is cache-hit (savings-multiplier headroom) + a stabler context.
