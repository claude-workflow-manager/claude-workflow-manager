#!/bin/bash
# UserPromptSubmit hook — injects state-appropriate rules every N messages per session.
#
# Cadence: message 1, 5, 10, 15, ... (fires on message 1, then every 5 after)
# Source: ~/.claude/rules/{discovery,execution,editing,review}-rules.md (selected by state)
# State: ~/.claude/hook-state/state-rules/{session_id}.json
# Injection: stdout JSON with additionalContext field
#
# Why: rules loaded once at session start decay fast (Khare curve — compliance
# drops from 95% at msg 1-2 to 20-60% by msg 6-10). Periodic re-injection keeps
# the state-relevant rules in attention before decay sets in. Complements
# inject-communication-rules.sh which covers the always-on communication rules.
#
# State detection:
# - Reads cwd from hook payload, walks up the directory tree looking for
#   projects/ACTIVE.md, parses the single active project row, reads
#   projects/{name}/STATE.md, and extracts the Current state: line.
# - Emits {} (no-op) when: no active project found, multiple active projects,
#   STATE.md missing or malformed, or state is unrecognized.
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

STATE_DIR="${HOME}/.claude/hook-state/state-rules"
INJECT_EVERY=5

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
# directories opt out of WM global rules injection.
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

# State detection — walk from cwd upwards looking for projects/ACTIVE.md.
ACTIVE_MD=""
if [ -n "$CWD" ]; then
  walk_dir="$CWD"
  if command -v cygpath >/dev/null 2>&1 && [[ "$walk_dir" =~ ^[A-Za-z]: ]]; then
    walk_dir=$(cygpath -u "$walk_dir")
  fi
  while [ -n "$walk_dir" ] && [ "$walk_dir" != "/" ]; do
    candidate="$walk_dir/projects/ACTIVE.md"
    if [ -f "$candidate" ]; then
      ACTIVE_MD="$candidate"
      break
    fi
    parent=$(dirname "$walk_dir")
    [ "$parent" = "$walk_dir" ] && break
    walk_dir="$parent"
  done
fi

if [ -z "$ACTIVE_MD" ]; then
  echo '{}'
  exit 0
fi

# Parse ACTIVE.md: find data rows (lines starting with | but NOT the header
# "| Project |" or the separator "|---|").
# Extract the project name from the first table column of the sole data row.
ACTIVE_MD_NATIVE="$ACTIVE_MD"
if command -v cygpath >/dev/null 2>&1; then
  ACTIVE_MD_NATIVE=$(cygpath -w "$ACTIVE_MD")
fi

PROJECT_NAME=$(python -c "
import sys
path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    lines = f.readlines()
data_rows = [
    l for l in lines
    if l.strip().startswith('|')
    and not l.strip().startswith('| Project')
    and not l.strip().startswith('|---')
    and l.strip() != '|'
]
if len(data_rows) == 0:
    print('')
    sys.exit(0)
if len(data_rows) > 1:
    import sys as _sys
    _sys.stderr.write('inject-state-rules: multiple active projects — skipping\n')
    print('')
    sys.exit(0)
cols = [c.strip() for c in data_rows[0].split('|')]
# cols[0] is empty (before first |), cols[1] is project name
name = cols[1] if len(cols) > 1 else ''
print(name.strip())
" "$ACTIVE_MD_NATIVE" 2>/dev/null || echo "")

if [ -z "$PROJECT_NAME" ]; then
  echo '{}'
  exit 0
fi

# Resolve the repo root (parent of the projects/ directory containing ACTIVE.md).
REPO_ROOT=$(dirname "$(dirname "$ACTIVE_MD")")

STATE_MD="$REPO_ROOT/projects/$PROJECT_NAME/STATE.md"
STATE_MD_NATIVE="$STATE_MD"
if command -v cygpath >/dev/null 2>&1; then
  STATE_MD_NATIVE=$(cygpath -w "$STATE_MD")
fi

if [ ! -f "$STATE_MD" ]; then
  echo '{}'
  exit 0
fi

# Extract the state name from "Current state: <name>" line.
PROJECT_STATE=$(python -c "
import sys, re
path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    for line in f:
        m = re.match(r'^Current state:\s+(\S+)', line)
        if m:
            print(m.group(1))
            sys.exit(0)
print('')
" "$STATE_MD_NATIVE" 2>/dev/null || echo "")

if [ -z "$PROJECT_STATE" ]; then
  echo '{}'
  exit 0
fi

# State → rules file mapping (single source of truth).
# Returns space-separated list of resolved rules/*.md paths for the state.
# Per-file shadow resolution: user ~/.claude/rules/<file> wins over plugin
# default if it exists; otherwise falls back to plugin-parent or plugin rules/.
_WM_ROOT_SR="$(wm_root)"
RULES_FILES=$(python -c "
import sys, os
from pathlib import Path

state = sys.argv[1]
wm_root = sys.argv[2]
home = Path.home()

mapping = {
    'discovery':          ['discovery-rules.md'],
    'backlog':            ['discovery-rules.md'],
    'planning':           ['execution-rules.md', 'editing-rules.md'],
    'planned':            ['execution-rules.md', 'editing-rules.md'],
    'plan-verified':      ['execution-rules.md', 'editing-rules.md'],
    'executing':          ['execution-rules.md', 'editing-rules.md'],
    'execution-paused':   ['execution-rules.md', 'editing-rules.md'],
    'awaiting-verification': ['review-rules.md'],
    'awaiting-release':   ['review-rules.md'],
}
files = mapping.get(state, [])
if not files:
    print('')
    sys.exit(0)

# Per-file shadow resolution: user shadow wins, then plugin-parent, then plugin.
wm = Path(wm_root)
plugin_candidates = [wm.parent / 'rules', wm / 'rules']
resolved = []
for fname in files:
    user_shadow = home / '.claude' / 'rules' / fname
    if user_shadow.exists():
        resolved.append(str(user_shadow))
        continue
    for plugin_dir in plugin_candidates:
        candidate = plugin_dir / fname
        if candidate.exists():
            resolved.append(str(candidate))
            break

print(' '.join(resolved))
" "$PROJECT_STATE" "$_WM_ROOT_SR" 2>/dev/null || echo "")

if [ -z "$RULES_FILES" ]; then
  echo '{}'
  exit 0
fi

# Verify at least one rules file exists on disk.
ALL_MISSING=true
for rf in $RULES_FILES; do
  if [ -f "$rf" ]; then
    ALL_MISSING=false
    break
  fi
done
if [ "$ALL_MISSING" = true ]; then
  echo '{}'
  exit 0
fi

mkdir -p "$STATE_DIR"
SESSION_STATE_FILE="${STATE_DIR}/${SESSION_ID}.json"
SESSION_STATE_FILE_NATIVE="$SESSION_STATE_FILE"
if command -v cygpath >/dev/null 2>&1; then
  SESSION_STATE_FILE_NATIVE=$(cygpath -w "$SESSION_STATE_FILE")
fi

# Read current counter (default 0).
if [ -f "$SESSION_STATE_FILE" ]; then
  COUNT=$(python -c "import json; print(json.load(open(r'$SESSION_STATE_FILE_NATIVE', encoding='utf-8')).get('count', 0))" 2>/dev/null || echo 0)
else
  COUNT=0
fi

COUNT=$((COUNT + 1))

# Atomic write of new counter.
TMP_FILE="${SESSION_STATE_FILE}.tmp"
printf '{"count": %d}\n' "$COUNT" > "$TMP_FILE"
mv "$TMP_FILE" "$SESSION_STATE_FILE"

# On first message of each session, sweep stale session state files older than
# 7 days from STATE_DIR. Keeps the directory bounded without unbounded growth.
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

# Convert rules file paths to Windows-native form if cygpath exists.
RULES_FILES_NATIVE=""
for rf in $RULES_FILES; do
  if command -v cygpath >/dev/null 2>&1; then
    rf_native=$(cygpath -w "$rf")
  else
    rf_native="$rf"
  fi
  RULES_FILES_NATIVE="$RULES_FILES_NATIVE $rf_native"
done
RULES_FILES_NATIVE="${RULES_FILES_NATIVE# }"  # strip leading space

# Build and emit the JSON payload via Python (clean UTF-8 handling).
# Force UTF-8 stdout — on Windows Python defaults to cp1252 which corrupts em-dashes.
export RULES_FILES_NATIVE COUNT PROJECT_STATE PYTHONIOENCODING=utf-8
python <<'PY'
import json, os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

state = os.environ["PROJECT_STATE"]
count = os.environ["COUNT"]
# Paths are space-separated; may contain Windows backslashes but no spaces in filenames.
paths = os.environ["RULES_FILES_NATIVE"].split()

# Build label names from filenames (strip path and extension).
labels = [os.path.splitext(os.path.basename(p))[0] for p in paths]

contents = []
for p in paths:
    try:
        with open(p, encoding="utf-8") as f:
            contents.append(f.read())
    except OSError:
        pass  # skip missing files silently

if not contents:
    print("{}")
    sys.exit(0)

if len(labels) == 1:
    header = f"[{labels[0]} reminder \u2014 msg {count} of this session]"
    body = contents[0]
else:
    combined_label = " + ".join(labels)
    header = f"[{combined_label} reminder \u2014 msg {count} of this session]"
    separator = "\n\n---\n\n"
    body = separator.join(contents)

footer = "[end reminder]"
payload = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": f"{header}\n\n{body}\n{footer}",
    }
}
# ensure_ascii=True produces pure ASCII JSON with \uXXXX escapes — safest for
# cross-platform shell pipes and guarantees the consumer parses identically.
print(json.dumps(payload, ensure_ascii=True))
PY
