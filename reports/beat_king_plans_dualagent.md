# Beat-the-king alternative plans — dual-agent (Claude draft → Codex red-team)

_2026-06-26. Snapshot data/raw/dashboard/2026-06-26/043901 (98 miners, 49 eligible). Claude's draft below;
Codex independently verifies the load-bearing claims AND hunts for a compliant king-beating plan this missed._

## State of play (verified this session)
| miner | E | M | H | total | wins | note |
|---|---|---|---|---|---|---|
| king 5Ggq | 0.858 | 1.281 | 0.727 | 0.957 | Overall, (E,M), (M,H), Single-M | edge = run-to-run CONSISTENCY on baseline-PASS, NOT content/ratio; WORSE than m12 on Hard + flips |
| **m12 (OURS)** | 0.412 | 0.953 | 0.919 | 0.768 | **Single-H only (4.76%)** | Hard field-best; Medium #2; ratio ties king (1.61×) |
| 5DtEz | 0.837 | 0.499 | 0.813 | 0.714 | (E,H) | hardest compressor (1.79×); Medium-poor |
| 5GCWaCnb | 0.923 | 0.701 | 0.665 | 0.760 | Single-E | |
| old-king 5DFvym | 0.812 | 0.934 | 0.596 | 0.780 | — | dethroned |
| 5DCnA57 | 0.528 | 1.120 | 0.168 | 0.701 | — | penalized light-compressor (1.18×, inflates 11/45) → eff < m12 |
| 5CaFqLa | 1.26 | 1.61 | 3.15 | 2.02 | — | **failed-review cheater; sweeps ALL 7 if reinstated (existential)** |

m12 gaps to each element: Overall +0.194 / (E,M) +0.387 / (E,H) +0.159 / **(M,H) +0.068 (m12 #2, cheapest)** /
Single-E +0.511 / Single-M +0.328 / Single-H WE WIN.

## The walls (LOAD-BEARING CLAIMS — Codex: independently verify each from the raw data)
W1. **m12 ties the king on compression ratio** (1.61× / ~38% savings, same 80.9M baseline). Ratio is NOT the lever;
    harder compressors (5DtEz 1.79×, old-king 1.71×) score LOWER. (reports/cross_miner_ratio_reference.md)
W2. **The king's edge is consistency on baseline-PASS tasks** (fewer −4 break-runs), not content quality or flips —
    it is WORSE than m12 on Hard (0.727<0.919) and on flips. Consistency is agent-side (qwen3-coder sampling), which we
    are BANNED from steering (compliant prompting = markers + loop-detection only).
W3. **comp-108 E/M/H are non-separable by ANY per-call signal** (token size AND depth fully overlap; error-freq inverted).
    So a single compliant miner cannot lift one category without spending another. (DISCOVERIES top + m24/depth verdicts)
W4. **All single-miner content levers are dead** (platform-scored or offline-proven): m13 soften (Hard 0.919→0.434),
    m21 keep-more, m22 extractive break-fix (killed flips + Hard crater), m23 RESOLVED-gate (leaks on flips), m24/depth
    passthrough (overlap), loopguard (saturated), compress-harder (wander), cache/savings-floor (no-op). 
W5. **Overall is unreachable even on a king collapse** — m12 is only #5 on Overall (0.761), behind 5H6919 + old-king;
    a deep king-Hard collapse hands Overall to them, not us.

## Claude's alternative-plan slate (ranked by EV; honest)
P1. **m25 coin-flip (LIVE, queued as m23).** Active Medium/Easy break-fix, gated + decoupled. ~15-25%. Gate on scored:
    Medium↑ ∧ Hard≥0.919 ∧ flips≥m12. The only ACTIVE shot in flight.
P2. **Passive Pair(M,H) capture (FREE).** m12 is the clean #2 (0.936 vs king 1.004); INTACT (5DCnA57's penalty dropped
    it out). If the king's (M,H) pair re-draws <0.936 → m12 auto-inherits +9.52% → ~14.3%. Exogenous timing, no build, no risk.
P3. **m26 hardening (if m25 scores close).** Feed-mode-robust decouple shrinks the coin-flip residual; the refined contender.
P4. **Next-round prep (the real long game).** A from-scratch architecture targeting newking-style Medium CONSISTENCY
    (6% break vs m12 15%) — not an m12 patch. Build into a LIVE next round, gated.
P5. **Defensive (standing).** Monitor 5CaFqLa review-status (existential) + king Hard volatility (threat to Single-H AND
    the trigger for P2). A byte-identical m12 twin was KILLED (defends the wrong threat).

## CODEX — your job (Gate-3 strategy red-team)
1. Independently VERIFY W1–W5 from the raw data (data/raw/dashboard/*, data/raw/platform_results/*, the reports). Flag any
   claim that does NOT hold.
2. ADVERSARIAL: find a COMPLIANT, testable plan to grow our share past 4.76% (ideally beat the king on an element) that
   this slate MISSED. Compliance = markers ([[CMP]]/[[BLOCK]]/loop-reasons) only, no steering/task-awareness/LLM-calls;
   m12 stays LIVE; experiments on a separate hotkey. Do NOT rehash the W4 dead-ends. Be concrete + give an EV.
3. If you find nothing new, say so plainly — that itself strengthens the verdict.

---

## Codex red-team result + Claude reconciliation (2026-06-26)
Codex independently RE-DERIVED the numbers from raw per-run JSON (the load-bearing-number gate working):
- **W1 ratio HOLDS** — Codex recomputed m12 **1.611×** (37.9%) vs king **1.608×** (37.8%); harder=lower (old-king 1.71×→0.780, 5DtEz 1.79×→0.714). Matches our 1.61× tie exactly.
- **W2 consistency HOLDS** — Codex recomputed BREAK(−4): m12 **17/250** vs king **6/250**; all-5-pass m12 **18** vs king **24**; king worse on Hard (0.727<0.919). Matches our per-run counts. King edge = consistency, confirmed.
- **W3 non-separability PARTIALLY-HOLDS** — fair refinement: Easy-vs-Hard IS token-separable (AUC 0.762; m12 already exploits it), but Medium not isolable + no COMPLIANT signal → practical wall holds (we'd already refined this in m24 §1C).
- **W4 levers-dead PARTIALLY-HOLDS** — fair caveat: m25 still `in queue` = the one OPEN active variant; all NAMED levers confirmed dead.
- **W5 Overall-unreachable HOLDS** — Codex confirmed m12 is #5 on Overall (behind 5H6919, old-king, 5GCWaCnb); a king collapse hands Overall to them, not us.

Codex NEW idea + Claude reconciliation:
- **N1 — OFFENSIVE byte-identical m12 twin as a Pair(M,H) LOTTERY** (distinct from the KILLED defensive Single-H twin).
  Mechanism: a 2nd m12 hotkey hoping ITS (M,H) re-eval draws above the king's 1.004 (= m12 0.936 +0.068). Codex P=5-12%.
  **Claude reconcile: real + genuinely new, but prob is UNCERTAIN and likely LOWER (~2-8%, near-0 if m12's (M,H) mean is
  stable).** It needs +0.068 UPWARD variance on a category-pair mean (14 M + 20 H tasks ×5 = CLT-smoothed). The king's Hard
  volatility (0.43-0.98) proves the platform CAN swing categories, but m12's own (M,H) variance is UNOBSERVED (frozen, never
  re-evaluated). N1 does NOT dominate the FREE passive P2 (king-falls-to-0.936 is more likely than twin-rises-to-1.004 given
  the king's demonstrated volatility); it's a complementary 2nd path. Optional IF spare-hotkey cost is ~zero.
- N2 (sacrificial Single-M specialist) + N3 (Single-E specialist): Codex KILLED, matches our analysis (gaps +0.328/+0.511; rehash W4).

## SYNTHESIZED BOTTOM LINE (both models, independent)
Active dethroning of the king is **unrealistic** — CONFIRMED by independent re-derivation. We hold Single-H (4.76%). The
realistic ceiling is **+9.52% → ~14.3% via Pair(M,H), reached by VARIANCE not a compression breakthrough**: the FREE passive
P2 (king's (M,H) re-draws <0.936) is the primary path; N1 (a cheap offensive m12 twin) is an optional complementary lottery.
NEXT: hold m12 LIVE; let m25/m23 score (the one open active shot); monitor king (M,H) + 5CaFqLa (existential). No new
compression idea survived either model. Both models agree.
