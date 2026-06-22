# NEXT_ACTIONS (handoff to the next session)

- [ ] **Laptop migration:** to re-create the local eval pipeline on a new machine, follow
      `setup/EVAL_PIPELINE.md` (clone 3 repos, apply `setup/patches/*`, extract arm64 docker CLI,
      fill `.env`, `uv sync`). The harness patches live ONLY in those patch files — a fresh clone of
      SOMA-benchmark/SOMA-plugin does NOT have them.

- [ ] **FUND the shared OpenRouter account.** m9/m10/m11 keys + KEY_D share ONE account with ~$28.59 left;
      3 miners' eval needs ~$100+. If it drains mid-eval → incomplete runs → low scores. (User action: top up.)
- [x] ~~Track m9/m10/m11 eval~~ — DONE (2026-06-21): scored 0.92–1.04, all below m7 (flip bets confirmed a downgrade).
- [ ] **Watch the Medium element** (now 5FbqgypX ~1.620). We back into the Medium reward (~4.8%) ONLY if the
      Medium leader drops below m7's 1.421 — unlikely; monitor each collect.
- [ ] Given m9–m11 underperformed, next cycle: **replicate m7** (our proven recipe) rather than more flip variants.
- [ ] Re-run `make reward` after each `make collect` to refresh reports/reward_projection.md.
- [ ] Decide next-cycle play: replicate m7 vs ship v26 (m12 needs subnet registration + a separately-funded key).
- [ ] (Optional) wire collect to a browser/automation source; for now use live fetch or `make collect IMPORT=file`.
