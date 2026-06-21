# DECISIONS (durable; don't relitigate)

- **m7 / v11.1 is our confirmed best (1.279) and the recipe to protect/replicate.** Everything built on top
  (v15→v18→v22→v24) added persistent-failure flip-routing that, on the platform, *leaked Medium* (v15 → 1.183).
- **Compression is at its ceiling.** Six levers tried (v14 richer, v17 harder, v19 loop-coach, v20 snapshot,
  v21 reasoning-trim, v23 gentler-harvest) — all no-gain or harmful. m7's 8k harvest is the sweet spot.
- **The king's edge (decisiveness + Easy 1.43) is not reachable via compression** — it's agent/model behavior.
  Easy ceiling for us is ~1.13 across gentle/aggressive/adaptive. Stop chasing Easy/overall #1.
- **Shipped v22→m9, v18→m10, v24→m11 (2026-06-17)** as flip "king-shots" on fresh hotkeys (m7 untouched/floor).
  Expectation revised DOWN after v15's platform result: likely ≤ m7 (Medium leak outweighs unmeasurable Hard gain).
- **v26 (depth-gated threshold) validated for a future cycle**, not shipped (m12 unregistered).
- **Reward model is layer-based (7 elements), not top-3.** Winning a single category (~4.8%) is the only realistic
  path for us; overall/pairs need broad strength we lack.
- **Ops/tracking lives here (SOMA-ops). Miner code is NOT edited or submitted from this repo.**
