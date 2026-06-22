# Label-mapping audit — m9/m10 (v22/v18)
_audit date 2026-06-21 · gating doc: per the research rules, resolve before any version-labelled analysis._

## The question
A chat message claimed `5CFqU2Ss…=v18` and `5GL4Kxda…=v22`, which is **swapped** versus
`config/miners.yaml` (`m9=5CFqU2Ss=v22`, `m10=5GL4Kxda=v18`). Which mapping is correct?

## Evidence gathered (primary → weak)
| source (git-tracked) | says | weight |
|---|---|---|
| `config/miners.yaml` | m9 `5CFqU2Ss` = **v22**; m10 `5GL4Kxda` = **v18** | registry (authoritative) |
| `state/DECISIONS.md` | "Shipped **v22→m9, v18→m10**, v24→m11 (2026-06-17)" | durable decision |
| `state/CURRENT.md` | "m9 / **v22** (0.937), m10 / **v18** (0.916)" | durable state |
| `state/SCOREBOARD.md` | m9 v22 / m10 v18 rows | durable state |
| miners.yaml notes | m9 note "flip-richness **+ release**" (=v22); m10 note "**v18 subset of v22**" | internally consistent w/ code |
| `upload_miner_v22_m10.py` (code) | contains the **v22 release-flip-on-pass** logic (lines 126, 1455–1470) → file IS v22 code | confirms file=version |
| `upload_miner_v18_m10.py` (code) | v18 logic only; no v22 release-flip → file IS v18 code | confirms file=version |
| chat message (NOT git-tracked) | swapped (5CFqU2Ss=v18, 5GL4Kxda=v22) | lowest (rules: chat ≠ source of truth) |

Note: the upload-script **filenames** both carry the suffix `_m10` (dev-slot tag), and the hotkey
is passed as a CLI arg, so filenames do **not** bind a hotkey to a version. The binding rests on
the four corroborating git-tracked files above.

## Resolution
**ACCEPTED (high confidence): `m9 = 5CFqU2Ss… = v22`, `m10 = 5GL4Kxda… = v18`.**
Four independent git-tracked files agree and are internally consistent (the v22 note mentions
"release", the v18 note says "subset of v22", matching the code). The only dissenting source was
chat, which the rules exclude.

## Why this does not endanger the analysis
**All per-task and category scores are keyed by HOTKEY** (scraped from the dashboard), not by
version string. So even if the version label were wrong, every numeric result by hotkey is
unaffected — only the human-readable "which code version" attribution would change. Forward
strategy (H1–H4) is built on **m7/v11.1** and explicitly drops the flip variants (v18/v22/v24),
so the residual m9/m10 version risk has near-zero impact.

## Residual uncertainty / how to close it to 100%
No hard primary artifact (a platform upload receipt showing hotkey + version + timestamp) was
available offline. To make this airtight, import such a receipt to
`data/raw/platform_results/` and re-run the audit. Until then: **do not relabel from chat; the
registry stands.**
