#!/usr/bin/env python3
"""PostToolUse hook on Bash — captures test/lint/typecheck output.

Matches verification commands by pattern. When matched:
1. Appends full output to scratch/verification-output.log
2. Returns structured ~500 token summary as additionalContext

Non-verification commands (git, ls, cd, etc.) are ignored.

FIN-005, FIN-018
"""

import json
import os
import re
import sys
import shlex
from datetime import datetime
from pathlib import Path


def _wm_root() -> Path:
    """Resolve the Workflow Manager plugin root.

    Priority:
    1. WM_ROOT environment variable (set by Claude Code plugin loader)
    2. Fallback: ~/.claude/skills/wm (legacy clone-install location)
    """
    env = os.environ.get("WM_ROOT")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "skills" / "wm"


def _wm_rule_path(rule_name: str) -> Path:
    """Resolve a rules file, preferring user shadow over plugin default."""
    user_shadow = Path.home() / ".claude" / "rules" / rule_name
    if user_shadow.exists():
        return user_shadow
    root = _wm_root()
    for candidate in [root.parent / "rules" / rule_name, root / "rules" / rule_name]:
        if candidate.exists():
            return candidate
    return user_shadow


MODE = "warn"  # "warn" only — this hook is advisory

# First-token match: the command (after any leading env vars / redirections)
# must START with one of these tools. Prevents false positives from
# `echo "pytest output"`, `grep pytest log`, etc.
VERIFY_TOOLS = {
    "pytest",
    "jest",
    "vitest",
    "mocha",
    "eslint",
    "tsc",
    "mypy",
    "flake8",
    "pylint",
    "pyright",
}

# Multi-token prefixes — the command must start with this exact sequence.
# Trailing "*" means the next token must start with that string (covers
# npm scripts like "test:watch", "test:unit", "test:e2e").
VERIFY_PREFIXES = [
    ["python", "-m", "pytest"],
    ["python3", "-m", "pytest"],
    ["npm", "test"],
    ["npm", "run", "test*"],
    ["pnpm", "test"],
    ["pnpm", "run", "test*"],
    ["yarn", "test"],
    ["yarn", "run", "test*"],
    ["npx", "tsc"],
    ["npx", "jest"],
    ["npx", "vitest"],
    ["ruff", "check"],
    ["ruff", "format"],
    ["black", "--check"],
    ["cargo", "test"],
    ["cargo", "clippy"],
    ["go", "test"],
    ["go", "vet"],
]


def is_verification(command):
    """True if the command starts with a verification tool invocation."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        # Malformed quoting — fall back to naive split
        tokens = command.split()
    if not tokens:
        return False

    # Skip leading env var assignments like FOO=bar pytest
    i = 0
    while i < len(tokens) and re.match(r"^[A-Z_][A-Z0-9_]*=", tokens[i]):
        i += 1
    if i >= len(tokens):
        return False

    # Strip any path prefix: ./pytest → pytest, /usr/bin/pytest → pytest
    first = os.path.basename(tokens[i])

    if first in VERIFY_TOOLS:
        return True

    # Check multi-token prefixes (supporting trailing "*" wildcards)
    remaining = [first] + tokens[i + 1:]
    for prefix in VERIFY_PREFIXES:
        if len(remaining) < len(prefix):
            continue
        match = True
        for idx, part in enumerate(prefix):
            if part.endswith("*"):
                if not remaining[idx].startswith(part[:-1]):
                    match = False
                    break
            elif remaining[idx] != part:
                match = False
                break
        if match:
            return True

    return False


def summarize(command, output):
    """Build a structured summary from verification output."""
    lines = output.splitlines() if isinstance(output, str) else []
    total = len(lines)

    passed = failed = 0
    errors = []
    warnings = []

    for line in lines:
        low = line.lower().strip()

        # Count pass/fail (pytest, jest, go test, cargo test)
        m = re.search(r"(\d+)\s+passed", low)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+)\s+failed", low)
        if m:
            failed = int(m.group(1))

        # Collect error lines (capped at 200 chars each)
        if (
            low.startswith("e ")
            or low.startswith("error")
            or "FAILED" in line
            or "FAIL " in line
        ):
            errors.append(line.strip()[:200])

        if "warning:" in low or low.startswith("warning"):
            warnings.append(line.strip()[:200])

        # eslint/tsc summary line
        m = re.search(r"(\d+)\s+error", low)
        if m and not failed:
            failed = int(m.group(1))

    status = "PASS" if failed == 0 and not errors else "FAIL"

    parts = [
        f"Verification: {status}",
        f"Command: {command[:100]}",
        f"Passed: {passed} | Failed: {failed} | Lines: {total}",
    ]

    if errors:
        sample = errors[:5]
        parts.append("Errors:")
        parts.extend(f"  - {e}" for e in sample)
        if len(errors) > 5:
            parts.append(f"  ... +{len(errors) - 5} more")

    if warnings:
        sample = warnings[:3]
        parts.append("Warnings:")
        parts.extend(f"  - {w}" for w in sample)

    parts.append("Full output: scratch/verification-output.log")
    return "\n".join(parts)


def main():
    try:
        data = json.load(sys.stdin)
        command = data.get("tool_input", {}).get("command", "")

        if not command or not is_verification(command):
            print("{}")
            return

        # Extract output from tool_response
        resp = data.get("tool_response", "")
        if isinstance(resp, dict):
            output = resp.get("stdout", resp.get("output", str(resp)))
        elif isinstance(resp, str):
            output = resp
        else:
            output = str(resp)

        # Write full output to scratch/verification-output.log
        cwd = data.get("cwd", os.getcwd())
        scratch = os.path.join(cwd, "scratch")
        os.makedirs(scratch, exist_ok=True)
        log_path = os.path.join(scratch, "verification-output.log")

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"[{datetime.now().isoformat()}] {command}\n")
            f.write(f"{'=' * 60}\n")
            f.write(output)
            f.write("\n")

        # Return structured summary
        summary = summarize(command, output)
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"[verification-output]\n{summary}",
            }
        }, sys.stdout)

    except Exception:
        print("{}")


if __name__ == "__main__":
    main()
