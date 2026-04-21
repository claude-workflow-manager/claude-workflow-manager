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
(none — this workflow is a thin dispatcher and has no cross-file dependencies)
</required_reading>

<process>

<step name="Step 1 — Parse verb + arguments">
The user invokes `/wm:doc-graph <verb> [args...]`. Seven verbs are supported:

| Verb | Usage | Purpose |
|---|---|---|
| `build` | `build [--force]` | Build or refresh the structural graph cache |
| `refs` | `refs <file> [--out\|--in\|--both]` | Forward + back references for a file |
| `ls` | `ls <path>` | List graph files under a path |
| `outline` | `outline <file>` | Print headers + signals for a file |
| `impact` | `impact <files...> [--mode=light\|deep]` | Four-dimensional impact scan |
| `check` | `check` | Repo-wide broken-reference scan (exits non-zero on failure — gate semantics) |
| `search` | `search <query>` | Keyword search across headers / paths / signals |

If the user invokes `/wm:doc-graph` with no verb, print the verb table above and STOP — do not dispatch.
</step>

<step name="Step 2 — Resolve the tool path">
The Python package lives in one of two locations depending on environment:

1. **Production** (`/wm:release`-deployed): `$HOME/.claude/skills/wm/tools/wm-doc-graph/`
2. **Dev repo** (Workflow-manager checkout): `./skills/wm/tools/wm-doc-graph/` (relative to `cwd`)

Prefer the production path. Fall back to the dev path. If neither
exists, print a clear error pointing the user at `/wm:release` and STOP.
</step>

<step name="Step 3 — Dispatch to the Python tool">
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

</process>
