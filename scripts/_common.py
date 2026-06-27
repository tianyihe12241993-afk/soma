#!/usr/bin/env python3
"""Shared helpers for SOMA-ops scripts. Stdlib-only (no external deps) so sessions
stay disposable and the scripts run anywhere."""
from __future__ import annotations
import datetime as _dt
import json
import os
import re
import subprocess
import sys as _sys
from pathlib import Path

# Make console output UTF-8 everywhere (Windows defaults to cp1252 and crashes on
# ✓/×/→/⚠ etc.). Files are already written with encoding="utf-8"; this fixes prints.
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
    # match lines like:  m7: { hotkey: 5Gs..., version: v11.1, note: "..." }  AND every *sub entry
    # (m16sub..m26sub, np2sub, and future labels). The key capture is (\w+) — any entry whose line
    # starts a flow mapping with a valid 48-char ss58 hotkey is loaded; the hotkey pattern gates it,
    # so a broad key match is safe (re.M ^ anchors to the entry line). NOTE: *sub entries put label:
    # before version:, so the version capture (which expects ', version:' right after the hotkey) is
    # empty for them — fine; hotkey_to_name only needs the hotkey->name mapping.
    for m in re.finditer(r'^\s*(\w+):\s*\{\s*hotkey:\s*([1-9A-HJ-NP-Za-km-z]{48})'
                         r'(?:,\s*version:\s*([^,}]+))?(?:,\s*note:\s*"([^"]*)")?',
                         txt, re.M):
        out[m.group(1)] = {"hotkey": m.group(2),
                           "version": (m.group(3) or "").strip(),
                           "note": (m.group(4) or "").strip()}
    return out


def hotkey_to_name() -> dict:
    return {v["hotkey"]: k for k, v in load_miners().items()}


def latest_raw_snapshot() -> Path | None:
    files = [f for f in sorted(RAW.glob("*/*_leaderboard.json"))]
    return files[-1] if files else None


def latest_detail_snapshot() -> Path | None:
    files = sorted(RAW.glob("*/*_miner_detail.json"))
    return files[-1] if files else None


def _parse_flow(block: str) -> dict:
    """Parse a flow-style YAML mapping body 'k: v, k: "q", ...' -> dict (stdlib only)."""
    out = {}
    for m in re.finditer(r'(\w+):\s*("(?:[^"\\]|\\.)*"|[^,}]+)', block):
        k, v = m.group(1), m.group(2).strip()
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        elif v.lower() in ("true", "false"):
            v = v.lower() == "true"
        elif v.lower() in ("null", "none", "~"):
            v = None
        else:
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
        out[k] = v
    return out


def load_flow_section(path: Path, section: str) -> dict:
    """Load a flow-style block-mapping section (e.g. 'miners:' / 'top_miners:') from a
    config file as {key: {fields}}. Stdlib-only; tolerant of PyYAML-style flow one-liners."""
    txt = read_text(path)
    out = {}
    in_section = False
    for line in txt.splitlines():
        if re.match(rf'^{re.escape(section)}:\s*$', line):
            in_section = True
            continue
        if in_section and re.match(r'^\S', line):       # next top-level key ends the section
            break
        m = re.match(r'^\s+([A-Za-z0-9_]+):\s*\{(.*)\}\s*$', line)
        if in_section and m:
            out[m.group(1)] = _parse_flow(m.group(2))
    return out


def load_miners_rich() -> dict:
    """Focal miners (config/miners.yaml 'miners:' section) with all derived stat fields."""
    return load_flow_section(CONFIG / "miners.yaml", "miners")


def load_top_miners() -> dict:
    return load_flow_section(CONFIG / "top_miners.yaml", "top_miners")


def load_secrets() -> dict:
    """Parse config/secrets.env (git-ignored, KEY="value" lines) -> dict. Empty if absent."""
    out = {}
    txt = read_text(CONFIG / "secrets.env")
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


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
