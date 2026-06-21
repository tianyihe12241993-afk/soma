#!/usr/bin/env python3
"""Shared helpers for SOMA-ops scripts. Stdlib-only (no external deps) so sessions
stay disposable and the scripts run anywhere."""
from __future__ import annotations
import datetime as _dt
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # repo root: /Users/user/SOMA
STATE = ROOT / "state"
DATA = ROOT / "data"
RAW = DATA / "raw" / "dashboard"
PROCESSED = DATA / "processed"
LATEST = DATA / "latest"
REPORTS = ROOT / "reports"
SESSIONS = ROOT / "sessions"
CONFIG = ROOT / "config"


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d_%H%M%S")


def read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def git_info(repo: Path = ROOT) -> dict:
    def run(*a):
        try:
            return subprocess.run(["git", "-C", str(repo), *a], capture_output=True,
                                  text=True, timeout=10).stdout.strip()
        except Exception:
            return ""
    branch = run("rev-parse", "--abbrev-ref", "HEAD") or "(no-git)"
    status = run("status", "--porcelain")
    changed = [l[3:] for l in status.splitlines()][:20]
    return {"branch": branch, "dirty": bool(status), "changed": changed}


def load_miners() -> dict:
    """Parse config/miners.yaml (simple format) -> {name: {hotkey, version, note}}."""
    txt = read_text(CONFIG / "miners.yaml")
    out = {}
    # match lines like:  m7:  { hotkey: 5Gs..., version: v11.1, note: "..." }
    for m in re.finditer(r'^\s*(m\d+):\s*\{\s*hotkey:\s*([1-9A-HJ-NP-Za-km-z]{48})'
                         r'(?:,\s*version:\s*([^,}]+))?(?:,\s*note:\s*"([^"]*)")?',
                         txt, re.M):
        out[m.group(1)] = {"hotkey": m.group(2),
                           "version": (m.group(3) or "").strip(),
                           "note": (m.group(4) or "").strip()}
    return out


def hotkey_to_name() -> dict:
    return {v["hotkey"]: k for k, v in load_miners().items()}


def latest_raw_snapshot() -> Path | None:
    files = sorted(RAW.glob("*/*_leaderboard.json"))
    return files[-1] if files else None


def latest_processed_rows() -> list:
    """Return rows from the most recent observed_at in the processed snapshots."""
    p = PROCESSED / "leaderboard_snapshots.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if not rows:
        return []
    newest = max(r["observed_at"] for r in rows)
    return [r for r in rows if r["observed_at"] == newest]
