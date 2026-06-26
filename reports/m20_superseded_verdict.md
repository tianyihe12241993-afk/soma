# m20 superseded-file-view dedup — build + offline validation VERDICT: REJECT (2026-06-24)

Built per approval (ratio-bonus lever: collapse superseded file re-reads to raise per-task ratio on passing
tasks). Offline validation REJECTS it before any eval. m20 = reference-only; m12 untouched/LIVE.
sha: 0be44494f84f9a8c2532e94d05ec7fdfafcf0600. Compliant PASS, deterministic, latest-view + error content preserved.

## The scoring headroom is REAL (user's instinct was sound)
per-run score = base + 0.5*clamp(ln(ratio),-2,2) for pass-pass(+1)/flip(+4). m12 at ratio ~1.75x => bonus +0.28;
max is +1.0 (~7.4x). So higher ratio on PASSING tasks = higher score, cross-category (incl. Easy passes), and
lifting M+H passes raises Overall toward #1. The headroom exists mathematically.

## But it is NOT safely capturable — three offline results converge:
1. Superseded branch FIRES (supersededViewCount=9 on same-path re-reads) but yields **ZERO token reduction**:
   the collapse uses extractive_message, which PINS all code signatures (def/class) + paths. A real file read is
   mostly signatures -> all pinned -> nothing drops -> no shrink. (multi-line code test: 60/60 methods survived.)
2. Truly-redundant re-reads (same lines) are ALREADY collapsed by m12's near-dup dedup (digit-stripping
   normalization caught all the near-identical-read test variants -> m12 == m20 there).
3. To get actual ratio gain, m20 would need to BLIND-truncate the superseded views (drop the code) -> loses
   content the agent read -> the proven wander/break family (depth/m17/m18). Scoping it to "superseded same-file
   reads" is the narrowest cut of that lever, but the forensics (PASS runs re-read files up to 14x and PASS)
   say those re-reads aren't safely droppable.

## Root principle (now fully pinned)
m12 already retains exactly the safe-to-keep content: code signatures + error/test/diff anchors + the latest
file view. Any further ratio gain requires dropping NEEDED content. The only purely-redundant content (re-reads
of identical lines) is already handled by near-dup. So the per-task ratio bonus, while mathematically real, has
NO safe headroom left for a compliant deterministic miner.

## Recommendation: REJECT m20 (do not eval the extractive version — no gain)
Optional last-resort: a m20-BLIND variant (blind-truncate superseded views for real shrink) is the narrowest,
most-targeted instance of "compress harder" — offline-unprovable (the ddmin-oracle problem: can't tell if
dropping an old view breaks the run without running the agent), so it could ONLY be settled by a same-window
A/B. Expectation per all prior evidence: modest-to-negative (in the proven-risky family). HOLD m12 otherwise.
