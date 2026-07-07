cap32+pin - np3 BasePass 0.07101107440498919 29 Hard 0.009819819735394753 16

exec
/bin/zsh -lc 'python3 -c $'"'import json\\nfrom collections import defaultdict\\nraw=json.load(open(\"data/raw/platform_results/2026-07-07/045717_swe_runs.json\")); cm=json.load(open(\"data/latest/comp108_task_categories.json\"))\\nsolvedH={k for k,v in cm.items() if v in (\"H\",\"Hard\")}\\n# base pass consistency all non-screeners\\nbase={} ; screen=set()\\nfor m in raw[\"miners\"]:\\n for t in m[\"tasks\"]:\\n  k=t[\"task_name\"]\\n  if t.get(\"is_screener\"): screen.add(k); continue\\n  base.setdefault(k,t.get(\"pass_without_compression\"))\\nbaseH={k for k,b in base.items() if b is False}\\nprint(\"solvedH\",len(solvedH),\"baseH\",len(baseH),\"screen in solvedH\",sorted(solvedH & screen))\\nprint(\"solvedH - baseH\",len(solvedH-baseH), sorted(solvedH-baseH))\\nprint(\"baseH - solvedH\",len(baseH-solvedH), sorted(baseH-solvedH))\\nfor k in sorted((solvedH-baseH)|(baseH-solvedH)):\\n print(k, \"solved\",cm.get(k),\"base_pass\",base.get(k),\"screener\",k in screen)\\n'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
python3: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
python3: error: couldn't create cache file '/tmp/xcrun_db-Jf4bR5rH' (errno=Operation not permitted)
python3: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
python3: error: couldn't create cache file '/tmp/xcrun_db-v2aoXXhH' (errno=Operation not permitted)
solvedH 17 baseH 16 screen in solvedH []
solvedH - baseH 1 ['sympy__sympy-16792']
baseH - solvedH 0 []
sympy__sympy-16792 solved H base_pass True screener False

exec
/bin/zsh -lc 'python3 -c $'"'import json\\nraw=json.load(open(\"data/raw/platform_results/2026-07-07/045717_swe_runs.json\")); labels={\"5DAbJik\":\"cap32+pin\",\"5FLUziw\":\"np2+pin\",\"5E4Y4jz\":\"np3+pin\",\"5CPbtf\":\"np2\",\"5F9ZRe\":\"np3\"}; miners={}\\nfor m in raw[\"miners\"]:\\n for p,l in labels.items():\\n  if m[\"hotkey\"].startswith(p): miners[l]={t[\"task_name\"]:t for t in m[\"tasks\"]}\\nk=\"sympy__sympy-16792\"\\nprint(k)\\nfor lab in [\"cap32+pin\",\"np2\",\"np2+pin\",\"np3\",\"np3+pin\"]:\\n t=miners[lab][k]; print(lab,\"score\",t[\"platform_score\"],\"base_pass\",t[\"pass_without_compression\"],\"comp_pass\",t[\"pass_with_compression\"],\"screener\",t[\"is_screener\"])\\nprint(\"diffs\", \"np2pin-np2\", miners[\"np2+pin\"][k][\"platform_score\"]-miners[\"np2\"][k][\"platform_score\"], \"np3pin-np3\", miners[\"np3+pin\"][k][\"platform_score\"]-miners[\"np3\"][k][\"platform_score\"], \"cap-np2\", miners[\"cap32+pin\"][k][\"platform_score\"]-miners[\"np2\"][k][\"platform_score\"], \"cap-np3\", miners[\"cap32+pin\"][k][\"platform_score\"]-miners[\"np3\"][k][\"platform_score\"])\\n'" in /Users/eric.xiao/joshua-work/soma
 succeeded in 0ms:
python3: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
python3: error: couldn't create cache file '/tmp/xcrun_db-uV4UoNrK' (errno=Operation not permitted)
python3: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
python3: error: couldn't create cache file '/tmp/xcrun_db-z8I1yHHD' (errno=Operation not permitted)
sympy__sympy-16792
cap32+pin score -1.536458285410228 base_pass True comp_pass False screener False
np2 score -0.6734529331578479 base_pass True comp_pass False screener False
np2+pin score -1.552816046883527 base_pass True comp_pass False screener False
np3 score 0.11969915528878827 base_pass True comp_pass True screener False
np3+pin score -2.3569949947659765 base_pass True comp_pass False screener False
diffs np2pin-np2 -0.8793631137256791 np3pin-np3 -2.476694150054765 cap-np2 -0.8630053522523801 cap-np3 -1.6561574406990163

codex
I recomputed from [045717_swe_runs.json](/Users/eric.xiao/joshua-work/soma/data/raw/platform_results/2026-07-07/045717_swe_runs.json) first, then checked [analyze_cap32pin_comp108.py](/Users/eric.xiao/joshua-work/soma/scripts/analyze_cap32pin_comp108.py) afterward. The script’s conventions match the main recomputation: all 50 tasks, all 250 runs, screeners included.

Category map check: [comp108_task_categories.json](/Users/eric.xiao/joshua-work/soma/data/latest/comp108_task_categories.json) has `E=17, M=16, H=17`; all 50 tasks mapped. Mean task scores mostly match board category summaries, but max residual is `0.044`, not strictly `<=0.03`. Hard matches exactly; Easy/Medium have the residuals. Also, this validation is circular because the map was board-fitted.

| Claim | My recomputed numbers | Verdict | Methodological objection |
|---|---:|---|---|
| 1. PIN isolation negative | `np2+pin - np2`: E `-0.3479`, M `-0.1365`, H `-0.0177`; `np3+pin - np3`: E `-0.1035`, M `-0.0119`, H `-0.0192` | **CONFIRMED under fitted map; PARTIAL overall** | Under alternative `Hard=baseline-fail`, Hard flips positive: np2 `+0.0362`, np3 `+0.1344`. The fitted Hard bucket includes `sympy__sympy-16792`, a baseline-pass outlier with large negative PIN deltas. |
| 2. PIN raised breaks | np2 `18/250 = 7.20%`; np2+pin `26/250 = 10.40%`; np3 `19/250 = 7.60%`; np3+pin `23/250 = 9.20%` | **CONFIRMED** | Denominator is all 250 runs, as requested. |
| 3. CAP confirmed | `cap32+pin - np2`: E `-0.0485`, M `+0.0572`, H `+0.1081`; `cap32+pin - np3`: E `+0.1880`, M `+0.0215`, H `-0.0882` | **CONFIRMED under fitted map; PARTIAL overall** | Under `Hard=baseline-fail`, Hard becomes cap-vs-np2 `+0.1688`, cap-vs-np3 `+0.0098`; the cap-vs-np3 Hard deficit disappears. |
| 4. M-winner depth | Mean task-level `ln(tokens_without/tokens_with) = 0.9496`; `exp(mean) = 2.5847x`; `ln(2.58)=0.9478`; board Medium `0.953826` | **CONFIRMED** | This is raw task token depth. It supports “observed compression >1.5x”; policy/compliance conclusions need the actual ceiling rule. |
| 5. Breaks/cache | cap32+pin `19/250 = 7.60%`, cache `90.91%`; M-winner `25/250 = 10.00%`, cache `85.80%`; H-winner `26/250 = 10.40%`, cache `84.33%` | **CONFIRMED** | Cache share computed as `sum(cached_input) / sum(input + cached_input)` over all runs. |
| 6. Variance | cap32+pin attempt means: k1 `0.8745`, k2 `0.3807`, k3 `0.7685`, k4 `0.8853`, k5 `0.7049`; span `0.381-0.885` | **CONFIRMED** | Pseudo-draw is mean of run `platform_score` for attempt `k` across 50 tasks. |

Overall verdict: claims 2, 4, 5, and 6 are safe to act on. Claims 1 and 3 are numerically correct for the fitted category map, but the category-specific Hard conclusions are not robust to the alternative `Hard=baseline-fail` grouping. The broad PIN break-rate claim is robust; the fitted-map “Hard” attribution is the fragile part.
tokens used
33,839
I recomputed from [045717_swe_runs.json](/Users/eric.xiao/joshua-work/soma/data/raw/platform_results/2026-07-07/045717_swe_runs.json) first, then checked [analyze_cap32pin_comp108.py](/Users/eric.xiao/joshua-work/soma/scripts/analyze_cap32pin_comp108.py) afterward. The script’s conventions match the main recomputation: all 50 tasks, all 250 runs, screeners included.

Category map check: [comp108_task_categories.json](/Users/eric.xiao/joshua-work/soma/data/latest/comp108_task_categories.json) has `E=17, M=16, H=17`; all 50 tasks mapped. Mean task scores mostly match board category summaries, but max residual is `0.044`, not strictly `<=0.03`. Hard matches exactly; Easy/Medium have the residuals. Also, this validation is circular because the map was board-fitted.

| Claim | My recomputed numbers | Verdict | Methodological objection |
|---|---:|---|---|
| 1. PIN isolation negative | `np2+pin - np2`: E `-0.3479`, M `-0.1365`, H `-0.0177`; `np3+pin - np3`: E `-0.1035`, M `-0.0119`, H `-0.0192` | **CONFIRMED under fitted map; PARTIAL overall** | Under alternative `Hard=baseline-fail`, Hard flips positive: np2 `+0.0362`, np3 `+0.1344`. The fitted Hard bucket includes `sympy__sympy-16792`, a baseline-pass outlier with large negative PIN deltas. |
| 2. PIN raised breaks | np2 `18/250 = 7.20%`; np2+pin `26/250 = 10.40%`; np3 `19/250 = 7.60%`; np3+pin `23/250 = 9.20%` | **CONFIRMED** | Denominator is all 250 runs, as requested. |
| 3. CAP confirmed | `cap32+pin - np2`: E `-0.0485`, M `+0.0572`, H `+0.1081`; `cap32+pin - np3`: E `+0.1880`, M `+0.0215`, H `-0.0882` | **CONFIRMED under fitted map; PARTIAL overall** | Under `Hard=baseline-fail`, Hard becomes cap-vs-np2 `+0.1688`, cap-vs-np3 `+0.0098`; the cap-vs-np3 Hard deficit disappears. |
| 4. M-winner depth | Mean task-level `ln(tokens_without/tokens_with) = 0.9496`; `exp(mean) = 2.5847x`; `ln(2.58)=0.9478`; board Medium `0.953826` | **CONFIRMED** | This is raw task token depth. It supports “observed compression >1.5x”; policy/compliance conclusions need the actual ceiling rule. |
| 5. Breaks/cache | cap32+pin `19/250 = 7.60%`, cache `90.91%`; M-winner `25/250 = 10.00%`, cache `85.80%`; H-winner `26/250 = 10.40%`, cache `84.33%` | **CONFIRMED** | Cache share computed as `sum(cached_input) / sum(input + cached_input)` over all runs. |
| 6. Variance | cap32+pin attempt means: k1 `0.8745`, k2 `0.3807`, k3 `0.7685`, k4 `0.8853`, k5 `0.7049`; span `0.381-0.885` | **CONFIRMED** | Pseudo-draw is mean of run `platform_score` for attempt `k` across 50 tasks. |

Overall verdict: claims 2, 4, 5, and 6 are safe to act on. Claims 1 and 3 are numerically correct for the fitted category map, but the category-specific Hard conclusions are not robust to the alternative `Hard=baseline-fail` grouping. The broad PIN break-rate claim is robust; the fitted-map “Hard” attribution is the fragile part.
