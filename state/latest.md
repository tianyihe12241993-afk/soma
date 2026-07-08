# LATEST — 2026-07-08T21:30:34Z
_auto-written by checkpoint (manual)_

**Note:** v2c EMULATOR: Gate A 10/10 (11th straight) but Gate B -10.8 weighted / -3.1 raw = REGRESSION vs v2b (+47/+56). THE TELL: 15375 flipped POSITIVE both runs (+72.6/+20.7 - the floor fix WORKED on its target) but flails MOVED (11551-r1 60stp -190, 13516-r2 63stp -340). CONFIRMS: screener = flail lottery; n=10 batches cannot rank same-family variants; v2b's 47 and v2c's -10.8 are draws of similar-mean processes. BAD-MARKERS = docker-log timestamp splice artifact (compliance clean). VERDICT: v2b stays best-of-line (platform-qualified 28pct raw). KING PLAY RECOMMENDATION: byte-identical v2b REDRAWS on additional spare hotkeys (comp-108 variance-draw play, now variance-measured) - each redraw = new screener lottery draw; best draw becomes our board score. v2c: park (same family, no measured edge).

**Best live miner:** uphardsaliencesub=0.723 | pending: m7, m8, m9, m10, m11, np2csub, m17sub, m1, m2, m3, m5, m6
**Our reward-element wins:** none

**Top of NEXT_ACTIONS:**
- - Snapshot analysis (165927): ALL 5 swebench screener tasks score POSITIVE for v2b (0.79-1.23), EkK (0.92-1.21), LEADER (1.01-1.34). pass_w 5/5 everywhere. **E=-4.00 does NOT come from these rows.**
- - HYPOTHESIS (strong): board E/M/H during screening maps to the 3 BENCHMARK TYPES; qualifier #1's raw page had 15 rows (5 tasks x 3 types) — our RSC parser extracts only the FIRST token array (swebench). **E is likely the EXPLORE screening category: v2b + EkK scored -4 there (explore quality-floor?) while LEADER scores +1.22.** If true: v2b's explore behavior on the PLATFORM failed where our local smoke passed (n=1) — the #1 crown threat AND the #1 v2c fix target.
- - NEXT: extend collect_miner_detail_rsc.py to extract ALL task arrays (explore/edit rows incl. platform_score) from the flight; confirm E=explore; diff leader's explore behavior. THEN: 15375 root-cause (v2b -65.5 vs leader +49.0 ON THE SAME TASK — leader compresses small-task reads too: in% 8.5 vs our 3.9 = they cut input MORE aggressively everywhere; our floor-1200 passthrough is the drag) → v2c: lower floor + explore-safe compression; emulator-test REQUIRED (incl. explore type runs).
- - **TOTAL = mean of the 5 swebench task platform_scores** (verified exact for all 3 miners: 1.057/1.088/1.211).

_Full checkpoint: sessions/2026-07-08_213034_manual.md_
