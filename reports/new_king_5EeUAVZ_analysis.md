# New King 5EeUAVZ — analysis (2026-06-30 ~08:05Z)

> ⚠️ **UPDATE 2026-06-30 ~08:35Z — KING UNDER COMPLIANCE REVIEW.** Discord (owner Matt|SOMA ~04:15Z): `5EeUAVZ` (Thomas_Colden's) **used `#source line N`, an UNAPPROVED prompt edit** ("not approved yet… not strictly following rules… upload+scoring done before approval… applies only to 1st place… team still discussing"). **The 0.852/90.5%/our-0% below may be INVALIDATED** — if DQ'd, np2/np3 (still scored+LIVE) auto-reclaim Single-M + Pair(M,H) → floor back to 14.3%. The flip/break edge below is likely the `#source line N` line-number annotation (informative provenance → right edits + structure-awareness), NOT "lighter compression" — and **we can't copy it (unapproved)**. ⇒ HOLD, don't chase the recipe; protect np2/np3. If the marker is later approved for all, adding line-number annotation becomes a new compliant candidate. The mechanism analysis below stands as the token/score decomposition; reinterpret the "lighter+cleaner" conclusion through the annotation lens.

**Hotkey:** `5EeUAVZDbk2jSYbtFFbQMAoqtArnDe5JLHzfKg7oCYmQhXmk` · status=**scored** · rank #1 (eligible) · source_code_available=False · penalty_total=0
**Snapshots:** leaderboard `data/raw/dashboard/2026-06-30/075706_leaderboard.json` · detail `075916_miner_detail.json` · per-run `data/raw/platform_results/2026-06-30/080429_swe_runs.json`

## Headline: it cratered our floor 14.3% → **0%**
`make reward` (2026-06-30T07:58Z, 110 eligible): **5EeUAVZ wins 5 of 7 elements = 90.5% of pool.**

| element | weight | winner | was |
|---|---|---|---|
| Overall (E,M,H) | 57.1% | **5EeUAVZ 0.856** | old king 5DZLFZj 0.728 |
| Pair (E,M) | 9.5% | **5EeUAVZ 1.017** | old king |
| Pair (E,H) | 9.5% | **5EeUAVZ 0.805** | 5GgVXz |
| Pair (M,H) | 9.5% | **5EeUAVZ 0.747** | **np3 (OURS)** |
| Single (M) | 4.8% | **5EeUAVZ 0.959** | **np2 (OURS)** |
| Single (E) | 4.8% | 5EKyJnby 1.225 *(evaluating)* | old king |
| Single (H) | 4.8% | 5GgVXz 0.676 | 5GgVXz |

**Our share now = 0%.** np2/np3 still score 0.684/0.682 (unchanged, still LIVE) — we didn't lose points, we lost the winner-take-all elements because 5EeUAVZ beat us on Medium AND (Medium,Hard). Closest reclaim = Single-M (need M>0.959 vs np2's 0.849, gap +0.110).

## What the king is (mechanism) — it is "np2 but lighter + cleaner", NOT a new trick
Head-to-head (45 non-screener tasks; per-run = 5 runs/task = 225 non-screener runs):

| miner | total | E | M | H | break-RUNS | flip-RUNS | cache% | raw ratio |
|---|---|---|---|---|---|---|---|---|
| **5EeUAVZ** | 0.852 | 1.076 | 0.959 | 0.535 | **13/145 = 9.0%** | **32/80 = 40%** | 93.6 | **1.33x** |
| old king 5DZLFZj | 0.728 | 1.105 | 0.832 | 0.269 | ~ | ~ | 93.8 | 1.42x |
| np2 (ours) | 0.684 | 1.052 | 0.849 | 0.173 | **18/145 = 12.4%** | **24/80 = 30%** | 94.0 | **1.49x** |
| np3 (ours) | 0.682 | 0.859 | 0.828 | 0.369 | 0-tasks | 5/16-tasks | 93.9 | 1.39x |

- **Savings are identical** (King +1.234 vs np2 +1.258 mean Trim(ln) on pass-pass → np2 even slightly higher). NOT the edge.
- **Cache identical** (~93-94%, all cache-stable). NOT the edge.
- **Compression: the king is LIGHTER (1.33x vs np2 1.49x).** It keeps MORE context.
- **The edge is two run-level levers, both from keeping more context:** the king **breaks fewer runs (9.0% vs 12.4%)** AND **flips more runs (40% vs 30%)**. Task-level binary pass/fail hid this (both "flip 5/16 tasks") — the difference is in how many of the 5 runs/task land.

## Where the gap lives (task-level, ACTIONABLE)
**Flip edge = sympy Hard (keeps them fuller → flips; np2 over-compresses → misses):**
- **sympy-18698: king 5/5 vs np2 1/5 (+4)** · sympy-23824 5/5 vs 3/5 · sympy-20801 5/5 vs 3/5 · sympy-19346 5/5 vs 4/5 · sympy-14976 2/5 vs 1/5 · django-13925 2/5 vs 1/5 · django-13121 1/5 vs 0/5
- (np2 wins a few back: sympy-13757 3/5 vs 1/5, sympy-20154 5/5 vs 4/5, sympy-24066 1/5 vs 0/5). Net king +8 flip-runs.

**Break edge = django baseline-pass (np2 breaks runs the king doesn't):**
- **django-12039: king 0 vs np2 4 break-runs** · sympy-23262 0 vs 2 · django-13158/11740 · sympy-11618/13647 (0 vs 1 each)
- (np2 cleaner on a few: django-14122 0 vs king 2, sympy-14531/22456 0 vs king 1). Net king −5 break-runs.

## Strategic read
1. **This VALIDATES our exact build direction.** The king is empirical proof that **lighter/fuller-keep + cleaner extraction → fewer breaks + more flips** is the winning recipe in the weighted-token regime (savings are dead weight; context-preservation drives the base score). That is precisely `uphard_cap32` (fuller-keep) + `uphard_salience` (import-pin). np2 OVER-compresses (1.49x) relative to the king (1.33x).
2. **Our running missed-flip A/B targets the king's 3 biggest flip wins** (sympy-18698 +4, 23824, 14976). If cap32/salience push np2 from 1/5 → toward 5/5 on sympy-18698, that's the mechanism confirmed locally.
3. **Beatability is narrow.** The king is balanced-strong; we are shut out of every element. Realistic reclaim = **Single-M** (need M>0.959), which requires matching the king's ~9% break rate on Medium AND keeping savings — a lighter+salience np2. The per-task variance is high (±2-3 pts/task), so a *favorable draw* of a king-recipe miner could edge it; a systematic beat is hard.
4. **Caveats:** the king's 0.852 has run-variance too (it is partly a favorable draw — see the ±3 per-task swings); 5EKyJnby (Single-E) is still *evaluating*. The board is active and can move.
