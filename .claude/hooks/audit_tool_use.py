#!/usr/bin/env python3
"""PostToolUse audit: append a redacted tool-usage event to sessions/tool_audit.jsonl.

Logs: timestamp, tool name, file path or command summary, git branch.
Never logs secret values (OpenRouter keys, .env contents, passwords are redacted).
Fast, stdlib-only, fail-open.
"""
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parent.parent.parent / "sessions" / "tool_audit.jsonl"
SECRET = re.compile(r'(sk-or-v1-[A-Za-z0-9]{6})[A-Za-z0-9]+|(--openrouter[_-]?api[_-]?key\s+)\S+'
                    r'|(password\s*[=:]\s*)\S+|([A-Za-z0-9_]*KEY[A-Za-z0-9_]*\s*=\s*)\S+', re.I)


def redact(s: str) -> str:
    if not s:
        return s
    return SECRET.sub(lambda m: (m.group(1) or m.group(2) or m.group(3) or m.group(4) or "") + "***REDACTED***", s)[:300]


def git_branch(cwd: str) -> str:
    try:
        return subprocess.run(["git", "-C", cwd or ".", "rev-parse", "--abbrev-ref", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip() or "(no-git)"
    except Exception:
        return "(no-git)"


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    cwd = data.get("cwd", "")

    if tool == "Bash":
        summary = redact(ti.get("command", ""))
    elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit", "Read"):
        summary = ti.get("file_path") or ti.get("notebook_path") or ""
    else:
        summary = redact(json.dumps({k: v for k, v in ti.items()
                                     if k in ("pattern", "path", "url", "query", "description")})[:200])

    row = {"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "tool": tool, "summary": summary, "branch": git_branch(cwd)}
    try:
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass                                                 # fail-open
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
