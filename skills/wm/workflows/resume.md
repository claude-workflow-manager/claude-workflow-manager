<purpose>
Development workflow orchestrator — entry point for resuming work. Loads project state, shows handoff summary, suggests next step.
</purpose>

<required_reading>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/session-rename.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/gate-matrix.md
</required_reading>

<process>
<step name="Step 1 — Detect projects and scratch handoff">
Look for:
1. `projects/` directory with `projects/ACTIVE.md` (check cwd, then parent)
2. `scratch/handoff.md` in cwd

Track what was found: `has_projects` (boolean), `has_scratch` (boolean).

If neither found: "No projects or scratch handoff found. Run `/wm:new-project` to start a project, or `/wm:save` to create a scratch handoff." STOP.
</step>

<step name="Step 2 — Read ACTIVE.md">
If `has_projects`: read `projects/ACTIVE.md`. Parse active project rows.
If not `has_projects`: skip (projects list is empty).
</step>

<step name="Step 3 — Select project">
Build selection list from active projects + scratch:

- **Projects only, one project** → auto-select it.
- **Scratch only** → auto-select scratch.
- **Multiple options** → show unified list:
  ```
  Active projects:
  1) project-alpha — next-version — executing
  2) project-beta — fix — backlog

  ---
  S) (scratch) — last general session — {date from handoff}

  N) Start a new project (/wm:new-project)
  ```
  Wait for user to choose.
</step>

<step name="Step 4 — Load context (progressive disclosure)">
**If scratch selected:** Read `scratch/handoff.md`. Present its content as the resume summary. No state-machine routing — let user decide next step:
  ```
  Scratch session from {date}:
  {handoff content}

  What would you like to do?
  A) Continue where you left off
  B) Start a new project (/wm:new-project)
  X) Something else
  ```
  Wait for user choice. STOP (no routing to Steps 5-8).

**If project selected:** Load only what the next action needs — not everything.

Read `projects/{name}/STATE.md` (always — it's small) and `projects/{name}/handoff.md`.

**Scope context loading by state:**
- `executing` → read handoff + plan file (current step only, not full plan). Expand on demand.
- `plan-verified` → read handoff + plan file header (intent, steps count). Full plan loads when execution starts.
- `between-cycles` or `backlog` → read handoff + DECISIONS.md. No plan to load.
- `planned` → read handoff only. Plan loads when verify-plan starts.
- `awaiting-release` → read handoff only. Release workflow loads its own context.

Do NOT front-load all project state. The resuming agent can expand context on demand — reading additional files when the workflow it routes to actually needs them.
</step>

<step name="Step 5 — Rename session">
Generate a descriptive session title from the handoff context:
1. Read the "Next action" from handoff.md
2. Summarize it into a 2-3 word slug (e.g., `rerun-p2-reverse`, `fix-gate-logic`, `add-scratch-handoff`)
3. Combine: `{project-slug}: {action-slug}`

Read `~/.claude/skills/wm/references/session-rename.md` and run the bash snippet, but replace `PROJECT_SLUG` with the full descriptive title (e.g., `deep-research: rerun-p2-reverse`).
</step>

<step name="Step 6 — Present resume summary">
Print a concise summary:
```
Project: {name}
Work type: {work-type}
State: {current-state}
Last session: {last session line from STATE.md}
Handoff: {next action from handoff.md}
```
</step>

<step name="Step 7 — Recommend next action">
**Check handoff first:** If the handoff has a concrete "Next action" with actionable steps (commands, files, success criteria), offer continuing from the handoff as the primary option.

**If handoff is actionable:**
```
A) Continue from handoff — {next action summary} (recommended)
B) {state-based command} — follow workflow
C) /wm:skip — skip current stage
X) Something else — tell me
```

If user picks A: skip the state machine, go straight to executing the handoff steps. No state update needed — the user is just continuing their work.

**If handoff is not actionable** (vague, missing, or just says "start discovery"):
Fall back to state-based recommendation:

| State | Recommendation |
|---|---|
| `between-cycles` | "Run `/wm:discover` to start discovery" |
| `backlog` | "Run `/wm:plan` to write the plan" |
| `planned` | "Run `/wm:verify-plan` to verify before executing" |
| `plan-verified` | "Run `/wm:execute` to start execution" |
| `executing` | "Run `/wm:execute` to resume execution" |
| `awaiting-release` | "Run `/wm:release` to complete the release" |

```
A) {recommended command} (recommended)
B) /wm:status — see full status
C) /wm:skip — skip current stage
X) Something else — tell me
```

Wait for user confirmation.
</step>

<step name="Step 8 — Route to WM workflow">
Once user confirms, route directly to the appropriate WM command:

| State | Command |
|---|---|
| `between-cycles` | `/wm:discover` |
| `backlog` | `/wm:plan` |
| `planned` | `/wm:verify-plan` (T2) or `/wm:execute` (T1) |
| `plan-verified` | `/wm:execute` |
| `executing` | `/wm:execute` |
| `awaiting-release` | `/wm:release` |

Announce: "Routing to {command}."
</step>
</process>
