#!/usr/bin/env python3
# <!-- learn-test
# scenario: {REPLACE: one sentence describing the situation the hook must catch}
# expected: {REPLACE: what the hook does on violation — usually "exits 2 with a message"}
# mode: inline
# last_run: {REPLACE: YYYY-MM-DD or never}
# result: {REPLACE: pass | fail | deferred}
# source: {REPLACE: session or incident reference}
# -->
"""
{Hook name} — Python template for /wm:learn-generated hooks.

Purpose: {REPLACE: one-paragraph description of what this hook prevents}

How Claude Code invokes this:
- Triggered by PreToolUse matcher: {REPLACE: matcher, e.g. "Bash" or "Edit"}
- Receives stdin JSON payload with tool_input and related fields
- Exit 0 -> tool call proceeds
- Exit 2 -> tool call blocked; Claude sees stderr as a reason
- Exit anything else -> hook error

Use Python over bash when the lesson requires:
- Complex file inspection (ast, tokenize, yaml/json parsing)
- State tracking across calls (read/write a sidecar file)
- Multi-step validation with branching logic
- Platform-specific handling too verbose for bash
"""

import json
import sys


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"hook: failed to parse stdin JSON: {e}", file=sys.stderr)
        return 0  # do not block on hook malfunction

    tool_name: str = payload.get("tool_name", "")
    tool_input: dict = payload.get("tool_input", {})
    cwd: str = payload.get("cwd", "")
    session_id: str = payload.get("session_id", "")

    # ------------------------------------------------------------------
    # BEGIN LESSON-SPECIFIC LOGIC
    # ------------------------------------------------------------------
    # Replace this block with the specific check your lesson requires.
    #
    # Example pattern 1 - block edits to a forbidden path:
    #     if tool_name in ("Edit", "Write"):
    #         target = tool_input.get("file_path", "")
    #         if "forbidden/path" in target:
    #             print(
    #                 f"BLOCKED: edits to {target} are not allowed (lesson: ...)",
    #                 file=sys.stderr,
    #             )
    #             return 2
    #
    # Example pattern 2 - block a specific bash command pattern:
    #     if tool_name == "Bash":
    #         cmd = tool_input.get("command", "")
    #         if "git push --force" in cmd:
    #             print(
    #                 "BLOCKED: force push requires explicit approval "
    #                 "(lesson: ...)",
    #                 file=sys.stderr,
    #             )
    #             return 2
    #
    # Example pattern 3 - warn without blocking (exit 0 with stderr):
    #     if tool_name == "Write" and tool_input.get("file_path", "").endswith(".env"):
    #         print(
    #             "WARNING: writing to .env file, proceeding (lesson: ...)",
    #             file=sys.stderr,
    #         )
    #
    # {REPLACE: write your check here}

    # ------------------------------------------------------------------
    # END LESSON-SPECIFIC LOGIC
    # ------------------------------------------------------------------

    # Default: allow the tool call to proceed.
    return 0


if __name__ == "__main__":
    sys.exit(main())
