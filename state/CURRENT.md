# CURRENT

_Competition 107 (CoT-Compression), Bittensor subnet 114. Eval window ~17–22 Jun 2026 (closing)._

## Portfolio (our hotkeys; see config/miners.yaml)
- **m7 / v11.1 — BEST confirmed = 1.279** (E 1.127 / M 1.421 / H 1.281). The one to protect/replicate.
- m8 / v15 — scored **1.159** (E 1.057 / H 1.230 / M 1.183). NOTE: Medium leaked to 1.183 (vs m7 1.421).
- m3 / v6 ≈ 1.080, m6 / v8 ≈ 1.034, m2 / v4 ≈ 1.003, m1 / v2 ≈ 0.884, m5 / v7 — broken/negative.
- **m9 / v22 (0.937), m10 / v18 (0.916), m11 / v24 (1.038) — now SCORED (2026-06-21), all BELOW m7.**
  Flip-routing crushed Medium (0.93–1.07 vs m7 1.421); confirmed net downgrade. m7 stays best.
- m12 / v26 — built + validated (depth-gated threshold), **NOT registered on subnet, NOT shipped**.

## Reward status (as of last collect, 2026-06-21)
- **We win NO element → no projected reward.** Best position is Medium (m7 1.421), now well behind the
  Medium leader 5FbqgypX (1.620). Overall leader is now **5EkiFXSR (1.454)**, above the king 5DhHqmB1 (Hard 1.751).
- Reward split ≈ 5EkiFXSR 66.7% / 5FbqgypX 14.3% / 5DhHqmB1 14.3% / 5GgUhFiG 4.8%. 5EFLeDNS = FAILED REVIEW.

## What to run
`make collect` (snapshot) → `make reward` (winners + projection) → `make status`. Checkpoint after changes.
