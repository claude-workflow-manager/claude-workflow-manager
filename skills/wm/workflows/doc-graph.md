<purpose>
Thin dispatcher for the `wm-doc-graph` Python tool. Parses the user's
verb + arguments from the slash command, runs `python -m wm_doc_graph`
via Bash with the correct PYTHONPATH, and relays the output back to chat.

This is the **only** file in the WM codebase that issues raw
`python -m wm_doc_graph` calls. Every other workflow that needs graph
data calls `/wm:doc-graph` via Skill dispatch, and Skill dispatch
routes through this workflow file (FIN-018c). Keeping the Python
invocation centralized here means the package path logic, error
handling, and output formatting live in one place.
</purpose>

<required_reading>
@~/.claude/rules/communication-rules.md
@~/.claude/rules/execution-rules.md
</required_reading>

<process>

<step name="Step 1 — Parse verb + arguments">
The user invokes `/wm:doc-graph <verb> [args...]`. Eight verbs are supported:

| Verb | Usage | Purpose |
|---|---|---|
| `build` | `build [--force]` | Build or refresh the structural graph cache |
| `refs` | `refs <file> [--out\|--in\|--both]` | Forward + back references for a file |
| `ls` | `ls <path>` | List graph files under a path |
| `outline` | `outline <file>` | Print headers + signals for a file |
| `impact` | `impact <files...> [--mode=light\|deep]` | Four-dimensional impact scan |
| `check` | `check` | Repo-wide broken-reference scan (exits non-zero on failure — gate semantics) |
| `search` | `search <query>` | Keyword search across headers / paths / signals |
| `check-rule-reminders` | `check-rule-reminders` | Staleness check: flags workflow files older than the rule files they cite |

If the user invokes `/wm:doc-graph` with no verb, print the verb table above and STOP — do not dispatch.

**Native vs Python verbs.** The first seven verbs dispatch to the Python `wm_doc_graph` module (Step 3). `check-rule-reminders` is a bash-native check — it runs a rule-reminder-staleness scan without the Python package, since the check is purely file-time comparison. It dispatches via Step 5 instead of Step 3.
</step>

<step name="Step 2 — Resolve the tool path">
The Python package lives in one of two locations depending on environment:

1. **Production** (`/wm:release`-deployed): `$HOME/.claude/skills/wm/tools/wm-doc-graph/`
2. **Dev repo** (Workflow-manager checkout): `./skills/wm/tools/wm-doc-graph/` (relative to `cwd`)

Prefer the production path. Fall back to the dev path. If neither
exists, print a clear error pointing the user at `/wm:release` and STOP.
</step>

<step name="Step 3 — Dispatch to the Python tool">
Follow [#Execution Rules](rules/execution-rules.md#execution-rules) from rules/execution-rules.md

Run the Python module via Bash, passing the user's arguments through
verbatim (do not rewrite, re-order, or trim them — the Python CLI has
its own argparse):

```bash
# Resolve wm-doc-graph tool path
if [ -d "$HOME/.claude/skills/wm/tools/wm-doc-graph/wm_doc_graph" ]; then
  PYPATH="$HOME/.claude/skills/wm/tools/wm-doc-graph"
elif [ -d "skills/wm/tools/wm-doc-graph/wm_doc_graph" ]; then
  PYPATH="skills/wm/tools/wm-doc-graph"
else
  echo "wm-doc-graph tool not found. Run /wm:release to deploy, or check PYTHONPATH." >&2
  exit 2
fi

# Dep-check: Python 3.x availability (FIN-008 plugin-path runtime guard)
WM_SKILLS_ROOT="${WM_ROOT:-$HOME/.claude/skills/wm}"
if [ -f "$WM_SKILLS_ROOT/lib/check-python.sh" ]; then
  # shellcheck source=/dev/null
  source "$WM_SKILLS_ROOT/lib/check-python.sh"
  if ! wm_check_python; then
    echo "wm-doc-graph requires Python 3.x. See message above." >&2
    exit 2
  fi
fi

# Dispatch
PYTHONPATH="$PYPATH" python -m wm_doc_graph {verb} {args...}
```

Replace `{verb}` and `{args...}` with the actual tokens the user passed to `/wm:doc-graph`. For example, `/wm:doc-graph build --force` becomes `PYTHONPATH="$PYPATH" python -m wm_doc_graph build --force`.
</step>

<step name="Step 4 — Relay output">
Print the command's stdout/stderr back to chat unchanged. Do not
summarize, reword, or trim the tool's output — other workflow files
parse it programmatically and rely on exact shapes (tech spec §5).

Exit codes are meaningful:
- `0` — success (or `check` clean)
- `1` — `check` found broken references (hard gate)
- `2` — path outside cwd (FIN-008), missing tool, or argument error
</step>

<step name="Step 5 — Dispatch: `check-rule-reminders` (bash-native)">
Runs only when the verb is `check-rule-reminders`. Does not invoke the Python module — pure bash + git.

**What it does.** Parses every canonical-form rule reminder in `skills/wm/workflows/*.md` and flags any workflow file whose last-modified time is older than the rule file it cites.

**Behavior — warn-only in v1.1.0, flips to hard-block after one validation cycle.** Per FIN-003's staged-rollout pattern (same shape as FIN-018 hook deployment): the first release ships this as a warning. Staleness reports appear in release output but do not block. After one release cycle with no false-positive noise, flip this check to exit non-zero on staleness to promote to a hard release gate.

```bash
# check-rule-reminders — bash-native staleness scan
#
# Scans skills/wm/workflows/*.md for the FIN-002 canonical form:
#   Follow [#<H1>](rules/<file>.md#<slug>) from rules/<file>.md
# For each match, compares the workflow file's commit time to the
# cited rule file's commit time via `git log --format=%ct -1 -- <path>`
# (git time preferred over filesystem mtime for portability).
# Emits a 5–15 line report. Exit 0 always in v1.1.0 (warn-only).

WORKFLOWS_DIR="skills/wm/workflows"
STALE_COUNT=0
TOTAL_REMINDERS=0

# Find every canonical-form reminder. grep -oE extracts the full match;
# we then parse each one to get the workflow file (via the containing
# line context) and the rule file (from the link target).
while IFS= read -r line; do
  TOTAL_REMINDERS=$((TOTAL_REMINDERS + 1))
  workflow_file="${line%%:*}"
  # Extract the rule file path from the match: everything between
  # "](" and "#" inside the canonical link.
  rule_path=$(echo "$line" | grep -oE '\]\(rules/[^#)]+' | head -1 | sed 's|^](||')
  [ -z "$rule_path" ] && continue

  workflow_t=$(git log --format=%ct -1 -- "$workflow_file" 2>/dev/null)
  rule_t=$(git log --format=%ct -1 -- "$rule_path" 2>/dev/null)

  # Skip if either side has no git history (not yet committed, etc.)
  [ -z "$workflow_t" ] || [ -z "$rule_t" ] && continue

  if [ "$rule_t" -gt "$workflow_t" ]; then
    STALE_COUNT=$((STALE_COUNT + 1))
    echo "STALE: $workflow_file cites $rule_path — rule edited after workflow (workflow $(date -d @$workflow_t +%Y-%m-%d), rule $(date -d @$rule_t +%Y-%m-%d))"
  fi
done < <(grep -rnE 'Follow \[#[^]]+\]\(rules/[^)]+\) from rules/' "$WORKFLOWS_DIR")

echo ""
echo "Scanned $TOTAL_REMINDERS canonical-form reminders across $WORKFLOWS_DIR/*.md"
if [ "$STALE_COUNT" -eq 0 ]; then
  echo "Staleness check: clean. No rule file is newer than its citing workflow."
else
  echo "Staleness check: $STALE_COUNT stale reminder(s) found (warn-only in v1.1.0 — not a release blocker yet)."
fi

# Warn-only mode — always exit 0 in v1.1.0.
exit 0
```

**Portability note.** `date -d @<epoch>` is GNU-style. On macOS / BSD, substitute `date -r <epoch> +%Y-%m-%d`. Detect via `uname -s` if cross-platform is needed.

**Hard-block flip.** After one release cycle with no false positives, change the final `exit 0` to:

```bash
if [ "$STALE_COUNT" -gt 0 ]; then
  exit 1   # promote to hard release gate
fi
exit 0
```

Document the flip in the CHANGELOG entry of the release that makes it.
</step>

</process>
