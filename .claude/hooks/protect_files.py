#!/usr/bin/env python3
"""PreToolUse guard: block WRITES/DELETES to protected files; allow reads.

Protected:
  - *.env and any path containing 'secret' (except *.example)
  - data/raw/**            (immutable raw dashboard snapshots — never overwrite)
  - **/archive/**, **/submissions/**   (archived miner submissions)
  - **/.git/**             (git internals)

Blocks Edit/Write/NotebookEdit/MultiEdit whose file_path is protected, and Bash
commands that destructively touch a protected path. Reading is always allowed.
Block = exit code 2 with a reason on stderr (Claude sees it). Allow = exit 0.
Fail-open on any internal error (never wedge the session).
"""
import json
import re
import sys

PROTECTED = [
    (re.compile(r'(^|/)[^/]*\.env($|[^.]|\.[^e])', re.I), "env file"),   # .env but not .env.example
    (re.compile(r'secret', re.I), "secrets file"),
    (re.compile(r'/data/raw/'), "immutable raw dashboard snapshot"),
    (re.compile(r'/archive/|/submissions/'), "archived miner submission"),
    (re.compile(r'(^|/)\.git/'), "git internals"),
]
DESTRUCTIVE = re.compile(r'(\brm\b|\bmv\b|\bcp\b|\btruncate\b|\bdd\b|\btee\b|sed\s+-i|>{1,2}\s|>\|)')


def protected(path: str):
    if not path:
        return None
    if path.endswith(".example"):
        return None
    for rx, label in PROTECTED:
        if rx.search(path):
            return label
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0                                            # fail-open
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    target, why = None, None
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        target = ti.get("file_path") or ti.get("notebook_path") or ""
        why = protected(target)
    elif tool == "Bash":
        cmd = ti.get("command", "") or ""
        if DESTRUCTIVE.search(cmd):
            for rx, label in PROTECTED:
                if rx.search(cmd):
                    target, why = "(bash) " + label, label
                    break

    if why:
        sys.stderr.write(
            f"BLOCKED by protect_files.py: attempt to modify/delete a protected target "
            f"({why}). This path is read-only for safety. Target: {target}\n")
        return 2                                            # exit 2 = block (PreToolUse)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
