#!/usr/bin/env python3
"""PreToolUse hook: auto-allows safe commands, prompts for destructive ones.

If the hook crashes for any reason, it defaults to "ask" so destructive
commands never slip through silently.
"""
import json
import os
import re
import sys
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


# Paths where rm is always safe (ephemeral, gitignored working dirs).
# If ALL rm targets are under one of these prefixes, auto-allow.
SAFE_RM_PATHS = [
    "scratch/",
    "./scratch/",
]


def _rm_targets_all_safe(command: str) -> bool:
    """Return True if the command is a single rm that only targets safe paths.

    Refuses to bypass if the command contains chain operators (&&, ||, ;)
    because the safe-path check can't guarantee the chained parts are safe.
    """
    if not re.search(r"\brm\b", command):
        return False
    # Reject chained commands — can't guarantee the whole chain is safe
    if re.search(r"[;&|]{1,2}", command):
        return False
    match = re.search(r"\brm\s+(?:-[rfiv]+\s+)*(.+)", command)
    if not match:
        return False
    targets = match.group(1).split()
    if not targets:
        return False
    return all(
        any(t.startswith(prefix) for prefix in SAFE_RM_PATHS)
        for t in targets
    )


# Substring patterns — matched anywhere in the command
DANGEROUS_SUBSTRINGS = [
    "reset --hard",
    "push --force",
    "push -f",
    "force-with-lease",
    "clean -f",
    "rm -rf",
    "rm -fr",
    "rm -r ",
    "rm -f ",
    "branch -D",
    "stash drop",
    "stash clear",
    "worktree remove --force",
    "worktree remove -f",
]

# Regex patterns — for cases where substring matching is too broad or too narrow
DANGEROUS_REGEXES = [
    (r"\bgit\b.*(?<!stash )\bpush\b", "git push (with any flags between)"),
    (r"\bgit\b.*\bcheckout\b.*\s--\s", "git checkout -- (discard changes)"),
    (r"\bgit\b.*\brestore\b", "git restore (discards changes)"),
]

def main():
    try:
        data = json.load(sys.stdin)
        command = data.get("tool_input", {}).get("command", "")
        cmd_lower = command.lower()

        # Safe-path bypass: rm targeting only scratch/ is always allowed
        if _rm_targets_all_safe(command):
            decide("allow", "")
            return

        for pattern in DANGEROUS_SUBSTRINGS:
            if pattern.lower() in cmd_lower:
                decide("ask", f"DESTRUCTIVE: contains '{pattern}'")
                return

        for regex, desc in DANGEROUS_REGEXES:
            if re.search(regex, cmd_lower):
                decide("ask", f"DESTRUCTIVE: {desc}")
                return

        # Safe command — auto-allow
        decide("allow", "")

    except Exception as e:
        # On any error, default to prompting — never silently allow
        decide("ask", f"Hook error: {e}")

def decide(decision, reason):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
        }
    }
    if reason:
        output["hookSpecificOutput"]["permissionDecisionReason"] = reason
    json.dump(output, sys.stdout)

if __name__ == "__main__":
    main()
