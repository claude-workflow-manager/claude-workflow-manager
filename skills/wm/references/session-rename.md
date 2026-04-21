# Session Rename

Renames the current Claude Code session to `cd: {project-slug}` so the session list stays navigable.

## When to use

- `/wm` — after selecting a project (Step 3)
- `/wm:new-project` — after scaffold is created (Step 6)

## Bash snippet

Replace `PROJECT_SLUG` with the actual project folder name (e.g. `phantom-cli-build`).

```bash
PROJECT_DIR=$(pwd | sed 's|^/\([a-zA-Z]\)/|\1--|' | sed 's|/|-|g')
SESSIONS_PATH="$HOME/.claude/projects/$PROJECT_DIR"
SESSION_FILE=$(ls -t "$SESSIONS_PATH"/*.jsonl 2>/dev/null | head -1)
if [ -z "$SESSION_FILE" ]; then
  echo "Session rename skipped — JSONL not found"
else
  SESSION_ID=$(grep -o '"sessionId":"[^"]*"' "$SESSION_FILE" | head -1 | sed 's/"sessionId":"//;s/"//')
  echo "{\"type\":\"custom-title\",\"sessionId\":\"$SESSION_ID\",\"customTitle\":\"cd: PROJECT_SLUG\"}" >> "$SESSION_FILE"
  echo "Session renamed to: cd: PROJECT_SLUG"
fi
```
