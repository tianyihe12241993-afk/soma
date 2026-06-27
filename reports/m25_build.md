# m25 — build + Phase-A verification (gated gentle break-fix + decoupled state)

_Date: 2026-06-26. File: `miner/cot_compression/upload_miner_m25.py` (sha8 52fe47f9). SEPARATE-HOTKEY candidate.
m12 LIVE (`upload_miner_m7_compliant.py`) untouched / git-clean. Built on user authorization to test the M,H thesis._

## What m25 is
m12 + three surgical, compliance-preserving changes, all confined to the HARVEST path:
1. **Gentle break-fix (CHANGE1 only):** at TRUNCATION sites, keep load-bearing lines (error/test/diff/sig/path via
   m12's own `extractive_compress`) instead of blind head/tail. **No drop-spans** (m22's CHANGE2 omitted — the bigger
   destabilizer). Worst case per result == m12.
2. **RESOLVED-gate:** break-fix applies ONLY when the working set is settled (recent results error-free over a window of
   6, not still-failing, not escalated, depth<80, ≥3 results, prev-mode≠rich). Every other turn = m12 byte-for-byte.
3. **Decoupled state:** emit the break-fix (model sees it) but SAVE the m12-exact build to state, so under native-feed
   (source-match) the rich/Hard path reads clean content next turn (hedges the m22 deep-Hard state-drift crater).
A reconciliation guard ships the break-fix only if ≤ m12 in BOTH tiktoken tokens AND chars; else falls back to m12.

## Phase-A safety (PASS) — `/tmp/m25_safety.py`
- **AST:** 54 functions byte-identical to m12 (incl. compress_gently/rich, all helpers, loop guard, run_event). Only
  `compress_structurally`/`handle_assemble`/`save_state` changed; `_harvest_build` added. m12 file untouched.
- **RICH identity:** deep (>90 msgs) trajectory → both rich → output byte-identical to m12. PASS.
- **PASSTHROUGH identity:** tiny context → both passthrough → byte-identical. PASS.
- **HARVEST gate-OFF:** recent error-bearing results → `m25Resolved=False` → output byte-identical to m12. PASS.
- **HARVEST gate-ON:** settled turn → output ≤ m12 in tokens AND chars; saved state.messages == m12-exact harvest
  (decoupling). PASS. (A uniform-noise synthetic didn't ship the break-fix — fragmentation > blind; that is the guard
  working, not a bug. Real-data ship-rate below.)
- **Determinism:** identical input → identical output. PASS.
- **Compliance:** emits only the allowed markers + loop-reason strings; "conclude"/"force-stop" appear ONLY in the
  inherited m12 docstring (m12 has the identical 2), never emitted. PASS.

## Real-trajectory behavior (15 comp-108 m12 trajectories; the honest experiment profile)
| cat | harvest turns | gate fires | break-fix ships | content-changed vs m12 |
|---|---|---|---|---|
| Easy | 2308 | 329 | 286 | 32 |
| Medium | 1628 | 286 | **250** | 43 |
| Hard | 2315 | **16** | 9 | **6** |

- **Active + targeted:** ships 545× total, concentrated on Easy/Medium; changes content on only 32 Easy / 43 Medium turns.
- **Hard well-protected:** gate fires on only 16 of 2315 Hard harvest turns, changes content on 6 — the gate + decouple
  contain Hard exposure (vs m22, which changed Hard broadly and cratered it via state-drift).
- **RESIDUAL FLIP-LEAK (the coin-flip risk):** on FLIP tasks the gate fired 240× and shipped **201** content-changes.
  Decouple protects DEEP flips (rich reads m12-clean) but NOT shallow flips (model directly sees break-fix → mechanism-2).
  So m25 is strictly safer than m22 on flips (gate skips active-failing turns; deep flips protected) but NOT flip-clean.

## Honest expectation
A coin-flip (~15–25%). m25 targets the real +4.958 Medium / Easy break-fix gains while hedging the two m22 craters
(deep-Hard via decouple, active-flip turns via gate). It does NOT eliminate the shallow-flip leak or the unpredictable
new-breaks on baseline-pass tasks (mechanism-2, non-gateable). The platform is the only way to resolve it — local replay
is faithful for routing/ship/leak counts but cannot predict break OUTCOMES (fresh-sample variance).

## ACCEPT GATE (platform, separate hotkey; reject on any miss)
Promote over m12 ONLY if, on ≥3 scrapes: **Medium ↑ AND Hard ≥ 0.919 AND flip-count ≥ m12's**. Else reject (m25 stays a
rejected reference; m12 LIVE). Same gate that correctly killed m22.

## Upload (USER runs; m12 stays LIVE on its own hotkey)
Register a NEW hotkey, then (same OpenRouter account as m12, the …1e8a lineage):
```
.venv/bin/python miner/upload_miner_with_openrouter_key.py \
  --platform_url https://platform.thesoma.ai --wallet_name tony-miner \
  --hotkey_name <NEW_M25_LABEL> \
  --solution_file miner/cot_compression/upload_miner_m25.py \
  --openrouter_api_key <OPENROUTER_KEY>
```
Then `make collect`; read m25's score ONLY when status=`scored`. Gate as above. Harnesses: `/tmp/m25_safety.py`.

---

## Codex pre-upload audit + reconciliation (2026-06-26 — first dual-agent protocol run)
Independent Codex (gpt-5-codex, ChatGPT auth) audited upload_miner_m25.py vs m12. Returned NO-GO w/ 3 blocking + 1 warning.
Main-session reconciliation (verified against code; NOT rubber-stamped):
1. **bare "…" not in allowed markers** — Codex BLOCKING → **NOT FATAL (over-flagged).** extractive_compress is BYTE-IDENTICAL
   to m12; m12 emits the same "…" in its RICH path (L753/757, used L1031/1036) and PASSED platform review at 0.768 →
   "…" is empirically review-compliant content-elision, not a governed bracketed marker. Harden later, not required.
2. **clean-state diverges from m12 on loop-guard turns** — Codex BLOCKING → **REAL but BENIGN.** clean_messages snapshotted
   before append_loop_guard; BUT resolve_stateful_messages (byte-identical m12) runs strip_loop_guard on load → washes out
   next turn → post-strip working identical. The "byte-identical saved state" invariant was overstated on loop turns; nil effect.
   (Phase-A gap: didn't test a loop-firing gate-off turn — good catch.)
3. **break-fix reaches rich via output-match** — Codex BLOCKING → **KNOWN/DOCUMENTED, not new.** = the decouple mode-dependence
   already flagged (decouple protects rich only under source-match; output-match ≈ gated-gentle-m22). The coin-flip residual.
4. **token guard degrades to char/4 if tiktoken absent** — Codex WARNING → **PLATFORM-SAFE** (tiktoken present in the
   compression-service image → exact on-platform). Optional fail-closed hardening.
VERDICT: none fatal to the queued m25/m23 → let it run as the M,H-thesis test; m12 LIVE untouched. Codex value = caught the
loop-guard state divergence + forced the output-match risk explicit; Claude caught the "…" over-flag via m12 review precedent.

### m26 hardening backlog (IF m25 scores promising → build a refined contender with these):
1. ★ FEED-MODE-ROBUST DECOUPLE: on output-match, reconstruct working = state["messages"](clean) + new_tail, not raw_messages
   → decouple works under BOTH connector modes → shrinks the coin-flip residual (biggest win). Touches resolve_stateful_messages
   (currently m12-identical) → re-verify rich/passthrough unaffected.
2. wrap extractive elisions in [[CMP]]…[[/CMP]] (removes the "…" doubt).
3. snapshot clean_messages AFTER append_loop_guard (exact byte-identical-state invariant).
4. fail-closed to legacy on any tiktoken import/call failure.
