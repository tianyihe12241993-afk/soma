# Discord — comp-109 (CoT-Compression Round 5) announcement + comp-108 final incentives
_source: SOMA Discord, 2026-07-06 (user-pasted transcript; times local to poster). Raw snapshot — immutable._

## comp-108 (Round 4) — FINAL incentive results (oli | SOMA, ~2:25 PM)
> "the review is finished, weights should be soon set and these are the incentive results:"

| hotkey | incentive |
|---|---|
| 5DAbJikTa2iEQgeAU7RjFMrMDm6rNFRUYnverTK4aG94B7Lk (**ours — cap32+pin**) | **0.5714285714** |
| 5DMC61SU44skyFGazaqvvuiS4Q44YJYaTxU1VKdU6fB9W9oh | 0.1428571429 |
| 5F4g41c59ZzBLPS62xx6Co7Ph9ASzfF7X29RTAHYKHE9AJNX | 0.1428571429 |
| 5F9ZReArwp25LaG1D8cze9WgWEeo8uofCjbsLTKaJk5ft7Jp (**ours — np3**) | **0.0952380952** |
| 5DkJeMqYvyPc1F4Jupw9VJ6xLfN1u7AkhDTJHaoGcbcaxA6d | 0.0476190476 |

**OUR CONFIRMED TOTAL = 0.6667 (66.7%).** Matches the 2026-07-06 projection in state/CURRENT.md.
oli: "winners - please make sure your hotkey is registered".

## comp-108 DQ reason (Matt | SOMA, 10:30 AM)
> "There was hidden injection about not writing tests, also it was done in a way that would be banned
> too as word replacements was not allowed string modification method on this competition."
Rules enforced strictly per miner/README_prompting.md.

## comp-109 (Round 5) — official pre-review
- **Timeline:** Submission 6 Jul 14:00 → 13 Jul 14:00 UTC. Evaluation 13 Jul 14:00 → 20 Jul 14:00 UTC.
  (New standing schedule: 1 week submit+screener, 1 week eval.)
- **"New agent as a base, new model and new tasks! (still quite similar)"** (Matt). "Also should be way
  cheaper to miners too. Stability also did look better on local tests. Changes will be merged soon."
  → oli ~2:36 PM: **"we merged the dev today"** (DendriteHQ/SOMA updated).
- **NEW TASK TYPE: code search** — "measuring how compression affects an agent's ability to locate the
  correct file and the lines where the required changes should be made."
- **SCORING REPLACED: E/M/H layers → task-specific layers.** "Each task type will now have its own
  dedicated layer. The details of the new scoring methodology will be published in the repository soon."
- **Task volume:** 50 tasks per type × 3 types = **150 tasks**, 5 runs each = **750 agent runs**.
  Screener: 5 tasks (per Karim's read, confirmed "That's correct" then corrected to 50/type).
- **Model/provider: DeepSeek V4 Pro via the DeepSeek provider on OpenRouter.** MANDATORY miner setup:
  1. OpenRouter Settings → Privacy → enable BOTH Data Collection options (paid + free endpoints that
     may train on request data).
  2. Settings → Guardrails → Workspace → Model and Provider Access → ensure DeepSeek provider enabled.
  Baseline costs to be shared "tomorrow" (~07 Jul); "Deepseek is quite cheap".
- **Prompt rules:** README_prompting.md UNCHANGED for this round (no issue/PR before uploads → frozen).
  One PR proposed post-open; owners will review ~07 Jul and merge only "if it meets the criteria".
  Standing rule: submit prompt issues/PRs BEFORE uploads start.
- **Tasks may be HIDDEN this round** (oli: "we are also considering hiding tasks for this round…
  they come from SWE-bench verified, we just won't show the exact ones") — anti-overfitting.
- Screening starts when tasks appear ("tomorrow" ≈ 07 Jul).
