#!/bin/bash
# <!-- learn-test
# scenario: {REPLACE: one sentence describing the situation the hook must catch}
# expected: {REPLACE: what the hook does on violation — usually "exits 2 with a message"}
# mode: inline
# last_run: {REPLACE: YYYY-MM-DD or never}
# result: {REPLACE: pass | fail | deferred}
# source: {REPLACE: session or incident reference}
# -->
#
# {Hook name} — bash template for /wm:learn-generated hooks
#
# Purpose: {REPLACE: one-paragraph description of what this hook prevents}
#
# How Claude Code invokes this:
# - Triggered by PreToolUse matcher: {REPLACE: matcher, e.g. "Bash" or "Edit"}
# - Receives stdin JSON payload with tool_input and related fields
# - Exit 0 → tool call proceeds
# - Exit 2 → tool call blocked; Claude sees the hook's stderr as a reason
# - Exit anything else → hook error (claude continues with a warning)

set -euo pipefail

# Read stdin JSON payload from Claude Code.
INPUT=$(cat)

# Extract the fields this hook needs. Use python for cross-platform UTF-8 JSON
# parsing (jq may not be present on Windows).
# Common fields: tool_name, tool_input, cwd, session_id.
TOOL_NAME=$(printf '%s' "$INPUT" | python -c 'import sys, json; print(json.loads(sys.stdin.read()).get("tool_name", ""))' 2>/dev/null || echo "")
TOOL_INPUT=$(printf '%s' "$INPUT" | python -c 'import sys, json; print(json.dumps(json.loads(sys.stdin.read()).get("tool_input", {})))' 2>/dev/null || echo "{}")

# ---------------------------------------------------------------------------
# BEGIN LESSON-SPECIFIC LOGIC
# ---------------------------------------------------------------------------
# Replace this block with the specific check your lesson requires.
#
# Example pattern 1 — block edits to a forbidden path:
#   if echo "$TOOL_INPUT" | grep -q '"file_path".*forbidden-path'; then
#     echo "BLOCKED: edits to forbidden-path are not allowed (lesson: ...)" >&2
#     exit 2
#   fi
#
# Example pattern 2 — block a specific bash command:
#   if [ "$TOOL_NAME" = "Bash" ]; then
#     CMD=$(printf '%s' "$TOOL_INPUT" | python -c 'import sys, json; print(json.loads(sys.stdin.read()).get("command", ""))')
#     case "$CMD" in
#       *"git push --force"*)
#         echo "BLOCKED: force push requires explicit approval (lesson: ...)" >&2
#         exit 2
#         ;;
#     esac
#   fi
#
# Example pattern 3 — warn on a pattern but don't block (exit 0 with stderr):
#   if echo "$TOOL_INPUT" | grep -q 'suspicious-pattern'; then
#     echo "WARNING: suspicious pattern detected, proceeding (lesson: ...)" >&2
#   fi

# {REPLACE THIS LINE with the actual check}

# ---------------------------------------------------------------------------
# END LESSON-SPECIFIC LOGIC
# ---------------------------------------------------------------------------

# Default: allow the tool call to proceed.
exit 0
