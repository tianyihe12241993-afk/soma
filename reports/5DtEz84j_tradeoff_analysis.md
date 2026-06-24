# 5DtEz84j tradeoff analysis — is there a safer Easy+Hard path? (2026-06-24, analysis-only)

Per user directive: investigate 5DtEz84j (high Easy AND Hard) before any m19 decision. NO building, NO submit,
m12 untouched. Use platform category scores as ground truth; per-task DELTAS where category labels can't be
reconstructed (they can't — the scrape has no per-task E/M/H, and our size buckets don't match platform truth).

## 1-2. Fresh scoreboard + status (all SCORED, not evaluating)
Snapshot 095500 + per-run scrapes 0955xx. All four `review=scored, eval=scored`:
| miner | total | Easy | Medium | Hard | profile |
|---|---|---|---|---|---|
| old king 5DFvymSe | 0.780 | 0.812 | 0.934 | 0.596 | balanced (wins Overall) |
| **m12 (us)** | 0.768 | 0.412 | 0.953 | 0.919 | M+H (Easy sacrificed) |
| 5DtEz84j | 0.714 | 0.837 | 0.499 | 0.813 | E+H (Medium sacrificed) |
| 5DAh2rUM | 0.051 | 0.853 | 0.976 | −3.600 | E+M (Hard collapsed) |

⚠️ **DATA CAUTION — 5DAh per-run scrape is INCONSISTENT with its scored leaderboard.** The scrape shows
avgScore 0.878, only 4 −4-runs, 8.6% global savings → multiplier 0.80, which CANNOT produce its leaderboard
H=−3.600 / total 0.051. So 5DAh's per-run rows are stale/evaluating-lag (or a penalty layer beyond per-run
scores drives the −3.6). **Trust 5DAh's leaderboard category truth; do NOT rely on its per-run details.** The
clean three (king, m12, 5DtEz) reconcile (per-run avgScore ≈ leaderboard total).

## 3. Per-miner aggregate (45 non-screener tasks × 5 runs = 225; reliable for king/m12/5DtEz)
| miner | avgScore | resolved | **−4 runs** | breaks | flips | avg ratio | avg steps | global savings | mult |
|---|---|---|---|---|---|---|---|---|---|
| king | 0.755 | 143/225 | **6** | 26 | 24 | 1.77× | 50.5 | 42.2% | 1.00 |
| **m12** | 0.738 | 144/225 | **16** | 30 | 29 | 1.75× | 51.1 | 37.7% | 1.00 |
| 5DtEz | 0.697 | 141/225 | 11 | 31 | 27 | 1.84× | 47.3 | 44.3% | 1.00 |
| 5DAh* | 0.878* | 151/225* | 4* | 21* | 27* | 1.33× | 58.2 | 8.6% | 0.80 |
*5DAh per-run unreliable (see caution).

## 4-5-7. 5DtEz vs m12 per-task deltas — where it wins / loses
**5DtEz WINS over m12 (its E+H edge):** almost all are tasks where **m12 BREAKS (has −4 runs) and 5DtEz does not.**
| task | 5DtEz | m12 | base tok |
|---|---|---|---|
| django-11740 | +1.17 (5/5, 0×−4) | −0.93 (3/5, **2×−4**) | 1.7M |
| sympy-14976 | +1.11 (3/5, 0×−4) | −0.76 (1/5) | 1.6M |
| django-14122 | +0.18 (4/5, 1×−4) | −1.02 (3/5, **2×−4**) | 1.7M |
| django-13810 | −0.84 (3/5, 2×−4) | −1.98 (2/5, **3×−4**) | 0.8M |
| django-12754 | +1.15 (5/5, 0×−4) | +0.01 (4/5, 1×−4) | 1.6M |

**5DtEz LOSES to m12 (its Medium sacrifice):** tasks where **5DtEz BREAKS and m12 solves cleanly.**
| task | 5DtEz | m12 | base tok |
|---|---|---|---|
| django-13033 | **−3.00 (1/5, 4×−4)** | +0.42 (4/5, 1×−4, 4.0×) | 2.2M |
| django-13158 | +0.48 (3/5) | +2.50 (5/5, 0×−4) | 1.9M |
| django-11292 | −0.35 (2/5) | +1.57 (4/5) | 1.6M |
| sympy-18698 | −0.55 (1/5) | +1.31 (3/5) | 3.6M |

**The key pattern: run-variance is RELOCATED, not eliminated.** 5DtEz breaks LESS on the tasks m12 breaks
(→ its high Easy) but breaks MORE on a different set (→ its Medium 0.50, e.g. django-13033 at 4×−4 where m12
gets 4/5). Squeeze breaks out of one category, they pop up in another. Net: 5DtEz total 0.714 < m12 0.768.

## 6. Compression-ratio comparison — 5DtEz is NOT a light compressor
5DtEz avg ratio **1.84× > m12's 1.75×** (it compresses MORE), global savings 44% > m12's 38%. So **5DtEz's Easy
success is NOT from lightness/near-passthrough** — it's a different reliability profile at similar-or-heavier
compression. This is important: it does NOT validate the "persistent-small light" mechanism.

## 8. Is 5DtEz useful to learn from?
Partially, as evidence — but NOT to copy:
- It REFUTES "Easy is impossible": Easy 0.84 + Hard 0.81 coexist (scored, real). Good.
- It REFUTES "lighter = easy wins": 5DtEz compresses MORE than m12. So Easy isn't a lightness lever.
- It does NOT validate persistent-small (it isn't doing that).
- Copying its tradeoff is NET NEGATIVE for us: E+H-but-low-M = 0.714 < m12's M+H-but-low-E = 0.768. m12's Medium
  (0.953) is worth more than the Easy 5DtEz would buy.

## 9. Is m19 (persistent-small / hard-safe) justified? — WEAK / NOT by this data
- The only profile that BEATS m12 is the **old king (0.780)**, and its edge is **pure reliability**: 6 −4-runs
  vs m12's 16, at the SAME ratio (1.77 vs 1.75) and SAME steps (50 vs 51). NOT lightness, NOT depth.
- So the lever that actually wins is "**same compression, fewer break-runs**" — which is exactly what m17
  (content-selection at same ratio) attempted and FAILED (perturbation). And whether m12's extra 10 breaks are
  even ours to fix vs provider-window/agent noise is unresolved (EXP-1b leaned noise).
- 5DtEz shows that changing the scheme RELOCATES breaks (easy↓, medium↑) rather than removing them → a
  persistent-small light mode would most likely trade easy-breaks for medium-breaks → net ≈ or < m12.
- m19 would also inherit: mid-task switch perturbation, narrow easy benefit window, untestable upside locally
  (m12 doesn't break easy tasks in our window), and the ≥20%-savings multiplier constraint.
- **Verdict: m19 is not justified by the 5DtEz evidence.** Build only as a last-resort close-the-book gate, with
  the prior that it returns ≈ m12.

## 10. Portfolio strategy (specialists) vs replacing m12 — the one structurally-new idea
The 7-element reward rewards SPECIALISTS (elements are per-category, independent of Overall). Current element map:
- **m12 wins Hard (0.919) + (M,H) (0.936)** ≈ 14% — KEEP m12 as the M/H specialist.
- 5DtEz wins **(E,H) (0.825)**; 5DAh (if review-counts) wins Easy/Medium/(E,M); king wins **Overall (57%)**.
- A second hotkey running an **E-focused specialist** could capture Easy-side elements (Easy 4.8% + (E,H) 9.5%)
  WITHOUT touching m12 — sidestepping the single-miner "can't win both" bind entirely. Combined m12 + E-specialist
  could roughly double our element share (~14% → ~25%+), IF both pass review and top their elements.
- **BUT blocked in practice:** we cannot currently BUILD a working Easy specialist — 5 attempts (depth, m17,
  uniform-light, adaptive-light, and the Easy candidates m13/m14/m15/m16) all failed, and 5DtEz/5DAh's mechanisms
  are opaque (we can't see their code) and partly window-luck. A specialist that only needs E+one-other (can
  sacrifice the third) MIGHT be more buildable than a balanced miner, but it's an open problem. Also needs a
  spare registered hotkey/slot.
- **Overall (57%) still needs a balanced miner**, which the structural bind says we can't build. So portfolio
  grabs the smaller side-elements, not the big prize.

## 11. Final recommendation: HOLD m12 (do NOT build m19; portfolio is the real direction but blocked)
1. **HOLD m12** — #2 (0.768), 0.012 behind the king, dominant Hard (0.919), penalty/multiplier/gate-robust
   (38% savings, all categories positive). Adopting any rival's tradeoff (5DtEz 0.714, 5DAh 0.051) is net WORSE.
2. **Do NOT build m19** — the 5DtEz data predicts break-RELOCATION (easy↓/medium↑), net ≈ or < m12; the king's
   winning edge is same-ratio reliability (not lightness), which compression-level gating doesn't address.
3. **Portfolio (m12 + a separate E-specialist hotkey) is the only structurally-new way to grow share** — it
   sidesteps the single-miner bind and the element math supports it. But it is GATED on an unsolved problem:
   building a working Easy specialist. Treat as a research track, not a ready move.
4. **Monitor** the board (ignore evaluating scores — 5DAh's −3.6 vs its stale per-run proves why) + the dormant
   `validator/llm-semantic-scoring` branch (the only thing that could reshape the run-variance dynamic).
