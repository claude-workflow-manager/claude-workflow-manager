#!/bin/bash
# UserPromptSubmit hook — injects global communication rules every N messages per session.
#
# Cadence: message 1, 5, 10, 15, ... (fires on message 1, then every 5 after)
# Source: ~/.claude/rules/communication-rules.md
# State: ~/.claude/hook-state/{session_id}.json
# Injection: stdout JSON with additionalContext field
#
# Why: rules loaded once at session start decay fast (Khare curve — compliance
# drops from 95% at msg 1-2 to 20-60% by msg 6-10). Periodic re-injection keeps
# the rules in attention before decay sets in.
#
# Platform notes:
# - Runs under bash on any Claude Code host (on Windows: MSYS/git-bash).
# - Uses cygpath if available to convert MSYS paths to native Windows paths
#   before handing them to Python. Falls back to the path as-is otherwise.
# - Relies on Python 3 for JSON encoding (avoids jq dependency).

set -euo pipefail

wm_root() {
  if [ -n "${WM_ROOT:-}" ]; then
    echo "$WM_ROOT"
  else
    echo "$HOME/.claude/skills/wm"
  fi
}

_WM_ROOT="$(wm_root)"
# Resolve the communication rules file.
# Priority: user shadow → plugin-parent rules/ → plugin rules/ → legacy home path.
RULES_FILE="${HOME}/.claude/rules/communication-rules.md"
for _candidate in \
    "${HOME}/.claude/rules/communication-rules.md" \
    "${_WM_ROOT}/../rules/communication-rules.md" \
    "${_WM_ROOT}/rules/communication-rules.md"; do
  if [ -f "$_candidate" ]; then
    RULES_FILE="$_candidate"
    break
  fi
done
STATE_DIR="${HOME}/.claude/hook-state"
INJECT_EVERY=5

# Defensive: if rules file missing, emit empty JSON and exit.
if [ ! -f "$RULES_FILE" ]; then
  echo '{}'
  exit 0
fi

# Read stdin payload from Claude Code.
INPUT=$(cat)

# Extract session_id via python (jq may not be present on Windows).
SESSION_ID=$(printf '%s' "$INPUT" | python -c 'import sys, json; print(json.loads(sys.stdin.read()).get("session_id", ""))' 2>/dev/null || echo "")

if [ -z "$SESSION_ID" ]; then
  echo '{}'
  exit 0
fi

# Scope check — skip injection when cwd (or any ancestor) contains a
# `.local-rules-only` marker file. Lets agent workspaces and client project
# directories opt out of the WM global communication rules.
CWD=$(printf '%s' "$INPUT" | python -c 'import sys, json; print(json.loads(sys.stdin.read()).get("cwd", ""))' 2>/dev/null || echo "")
if [ -n "$CWD" ]; then
  check_dir="$CWD"
  if command -v cygpath >/dev/null 2>&1 && [[ "$check_dir" =~ ^[A-Za-z]: ]]; then
    check_dir=$(cygpath -u "$check_dir")
  fi
  while [ -n "$check_dir" ] && [ "$check_dir" != "/" ]; do
    if [ -f "$check_dir/.local-rules-only" ]; then
      echo '{}'
      exit 0
    fi
    parent=$(dirname "$check_dir")
    [ "$parent" = "$check_dir" ] && break
    check_dir="$parent"
  done
fi

mkdir -p "$STATE_DIR"
STATE_FILE="${STATE_DIR}/${SESSION_ID}.json"

# Read current counter (default 0).
if [ -f "$STATE_FILE" ]; then
  COUNT=$(python -c "import json; print(json.load(open(r'$(command -v cygpath >/dev/null 2>&1 && cygpath -w "$STATE_FILE" || echo "$STATE_FILE")', encoding='utf-8')).get('count', 0))" 2>/dev/null || echo 0)
else
  COUNT=0
fi

COUNT=$((COUNT + 1))

# Atomic write of new counter.
TMP_FILE="${STATE_FILE}.tmp"
printf '{"count": %d}\n' "$COUNT" > "$TMP_FILE"
mv "$TMP_FILE" "$STATE_FILE"

# FIN-005 — on the first message of each session (counter == 1), sweep stale
# session state files older than 7 days from STATE_DIR. Keeps the directory
# bounded without unbounded growth over months.
# Cost: one `find` call per session, typically <5ms. Runs only once per session.
if [ "$COUNT" -eq 1 ]; then
  find "$STATE_DIR" -maxdepth 1 -type f -name '*.json' -mtime +7 -delete 2>/dev/null || true
fi

# Decide whether to inject on this turn.
SHOULD_INJECT=false
if [ "$COUNT" -eq 1 ]; then
  SHOULD_INJECT=true
elif [ $((COUNT % INJECT_EVERY)) -eq 0 ]; then
  SHOULD_INJECT=true
fi

if [ "$SHOULD_INJECT" = false ]; then
  echo '{}'
  exit 0
fi

# Convert rules file path to Windows-native form if cygpath exists.
if command -v cygpath >/dev/null 2>&1; then
  RULES_FILE_NATIVE=$(cygpath -w "$RULES_FILE")
else
  RULES_FILE_NATIVE="$RULES_FILE"
fi

# Build and emit the JSON payload via Python (clean UTF-8 handling).
# Force UTF-8 stdout — on Windows Python defaults to cp1252 which corrupts em-dashes.
export RULES_FILE_NATIVE COUNT PYTHONIOENCODING=utf-8
python <<'PY'
import json, os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
path = os.environ["RULES_FILE_NATIVE"]
count = os.environ["COUNT"]
with open(path, encoding="utf-8") as f:
    rules = f.read()
header = f"[communication-rules reminder \u2014 msg {count} of this session]"
footer = "[end reminder]"
payload = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": f"{header}\n\n{rules}\n{footer}",
    }
}
# ensure_ascii=True produces pure ASCII JSON with \uXXXX escapes — safest for
# cross-platform shell pipes and guarantees the consumer parses identically.
print(json.dumps(payload, ensure_ascii=True))
PY
