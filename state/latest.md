# LATEST — 2026-06-23T03:40:37Z
_auto-written by checkpoint (manual)_

**Note:** m12.1 EVAL VERDICT: DO NOT SHIP. m12.1 cut 1 fragile break (2 vs 3) but OVER-ROUTED Medium: +28% tokens/call on Medium (less compression -> lower Medium score), consistent across all 4 Medium tasks. 1b gentle routing (shallow_small->passthrough + earlier error-guard) too aggressive, catches compressible Medium. Bad trade vs grow-H+M strategy. FIX=m12.1b: keep 1a never-inflate (pure win), tighten 1b to fire only on persistent/break-prone NOT shallow-Medium. m12 stays live.

**Best live miner:** m7=1.279 | pending: m12
**Our reward-element wins:** none

**Top of NEXT_ACTIONS:**
-       Add columns to the import schema when available.
- - [ ] (Optional) **platform upload receipts** (hotkey+version+timestamp) → close the label audit to 100%.
- - [ ] Re-run `make detail` periodically only if you want fresher rival scrapes (comp is over; board is static).
- - [x] ~~WSL env + soma_shared~~ — DONE (env ready; soma_shared 0.1.0 in venv). Upload path needs only a wallet,

_Full checkpoint: sessions/2026-06-23_034037_manual.md_
