# COMP WATCH ALERT — 2026-07-06T14:46:39Z

_Auto-written by scripts/watch_comp_status.py. Monitor-only; verify on the platform before acting._

## What changed
- **King 5GpLcd… DROPPED from the leaderboard entirely.**

## Current readings
- README check exit=0  source_line=False  omit=False  removed=False
- King 5GpLcd…: present=False review=None eval=None total=None rank_eligible=None
- Our 3 pending uploads: cap32+pin (uphard_salience) 5DAbJi…=eval:?/total:None; np3+pin 5E4Y4j…=eval:?/total:None; np2+pin 5FLUzi…=eval:?/total:None

## What to do
- **One of OUR 3 pending uploads reached SCORED** → `python scripts/vet_draw.py --hotkey HK` (cache≥88%/break≤13%), then `make reward`; read E/M/H vs np2/np3 + **Overall vs 0.703**. Read scores ONLY at scored.
- **King 5EeUAVZ OR old-king 5DZLFZj dropped / failed-review** (oli's rule: both DQ'd for unapproved `#source line N`) → run `make reward`; with BOTH excluded we PROJECT **23.8%**: np2 reclaims **Pair(E,M) + Single(M)** (14.3%), np3 keeps **Pair(M,H)** (9.5%). DEFEND np2/np3/m26.
- **`#source line N` landed in README ALLOWED set** → it's now a compliant lever → build a line-number-annotation candidate (Codex audit first). Confirm ALLOWED, not a DISALLOWED example.
- **Karim omit-marker landed** → activate `upload_miner_uphard_omitcount.py` (set template, OMIT_COUNT_ENABLED=True, scanner + Codex).
- **Baseline string REMOVED** → our live miners may be NON-COMPLIANT → re-audit immediately.

Full context: `state/CURRENT.md` (top) + `reports/new_king_5EeUAVZ_analysis.md`.
