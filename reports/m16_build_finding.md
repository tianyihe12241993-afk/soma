# m16_small_context_light_safe — BUILT, but the design does NOT achieve the Easy goal (2026-06-23)

_m16 = m12 + reactive "harvest-didn't-save → gentle rich" rescue (sha a6156a67). Compliant, M/H byte-identical,
deterministic. Offline verification (verify_m16.py) surfaced a design flaw that means it won't lift Easy._

## What's sound
- Compliance scanner PASS; only allowed markers/loop-reasons.
- **M/H byte-identical to m12** (Medium 12229=12229 harvest; Hard/deep = rich path, rescue is harvest-only). The
  moat is provably safe — the rescue fires only where harvest fails to save, which M/H never does.
- Deterministic across PYTHONHASHSEED; error markers + tool-call/result pairing preserved. No m13 constructs.

## The design flaw (verification-proven)
The rescue ("if harvest output ≥ raw input, use gentle rich; else raw") has NO useful middle ground:
- **Small context WITH redundancy** → m12's harvest ALREADY saves (drops the dups, e.g. 2.37×) → rescue never
  fires → **m16 = m12** (no Easy change).
- **Small context WITHOUT redundancy** → harvest can't save → rescue fires → but rich ALSO can't compress (no
  dups) → falls to **raw passthrough** (= m14/m15, explicitly excluded) → 0 savings (gate risk), and the loop
  guard can re-inflate after.
⇒ The cases where harvest fails to save are exactly the ones rich can't compress either. So the rescue is
either m12 or passthrough — **it never produces the king's light-positive 1.1–1.5×.** Confirmed on fixtures:
C-textinflate → rescue=raw_last_resort (ratio 0.997); D-redundant → harvest saves 2.37×, rescue idle.

## The deeper reason a runtime never-inflate rule can't fix this
The platform Easy "inflation" (ratio<1 = tokens_with > tokens_without) is almost certainly a PROVIDER-CACHE /
cumulative effect: compressing changes the context prefix → busts the provider cache → subsequent calls
re-process uncached → more total tokens than the byte-stable no-compression baseline. A runtime guard compares
the miner's OUTPUT text to its INPUT text — it never sees the no-compression baseline, so it cannot detect or
prevent cache-driven inflation. No "don't inflate this turn" rule (m14, m16) can target the platform ratio.

## Verdict: do NOT ship m16. The "light-safe small-context compression" lever needs a different mechanism.
m16 reduces to "m12, or passthrough where m12 would inflate" — i.e. ~m14 on the firing cases. It won't move
Easy. The king's light-positive Easy compression must come from something a runtime never-inflate can't do:
likely **cache-stable compression** (compress once, keep the prefix byte-stable so cache hits resume) or
**light truncation of verbose tool outputs even on small contexts** (a proactive trim, with break-risk).

## Recommended next (pick one)
1. **Cheap empirical pre-check (~6 solves, RUNS=1):** m12 vs m16 on 3 Easy-proxy comp-108 tasks — confirm m16
   ≈ m12 (rescue idle / passthrough) on real tasks before spending more. Low cost, settles it empirically.
2. **Investigate the king's Easy mechanism deeper:** is its Easy edge cache-stability (fewer prefix changes) or
   actual light trimming? Look at king per-run token *shape* (cached vs input split) vs m12 on Easy tasks —
   `b430e3c` now persists the split. This tells us WHAT to build.
3. **If we pursue it:** a cache-stable small-context path (minimize prefix churn) — a real engine change,
   validated ONLY on the re-pointed comp-108 real eval (offline text-estimate can't measure cache). Higher
   effort; do it only if (2) confirms cache-stability is the king's lever.
- m12 (0.768) stays LIVE/BEST throughout. m16 kept as reference (do not submit).
