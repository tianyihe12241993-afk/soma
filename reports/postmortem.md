# Post-competition post-mortem (our 5 submissions)
_computed 2026-06-21T16:30:50Z. Baseline of comparison = m7/v11.1 (total 1.279)._

## Did the flip variants (m8/m9/m10/m11) improve solving, or only add breakage?
| miner | ver | total | Δtotal vs m7 | pass | broke | neg | mean ratio | verdict |
|-------|-----|-------|--------------|------|-------|-----|-----------|---------|
| m7 | v11.1 | 1.279 | +0.000 | 38 | 1 | 3 | 2.99× | BASELINE (best) |
| m8 | v15 | 1.159 | -0.120 | 36 | 0 | 2 | 2.84× | Δpass -2, Δbroke -1 |
| m9 | v22 | 0.937 | -0.342 | 33 | 3 | 9 | 2.64× | no solving gain; +breakage |
| m10 | v18 | 0.916 | -0.363 | 33 | 2 | 8 | 2.66× | no solving gain; +breakage |
| m11 | v24 | 1.038 | -0.241 | 36 | 1 | 7 | 2.70× | no solving gain; +breakage |

## Conclusion
- All flip/persistence variants scored **below** m7. They did **not** raise pass count; they raised **broken-baseline** and **negative-score** counts (catastrophic −penalty tasks).
- Compression ratio did **not** improve under flip-routing (~2.6–2.8× vs m7 2.99×).
- **Drop permanently:** flip-mode rescue, persistent-failure→rich routing, release-flip-on-pass.
- **Keep:** m7-style structure-preserving harvest. Next gains come from **deeper pass-safe compression on m7**, evidence-ranked (see reports/m7_gap_analysis.md).
