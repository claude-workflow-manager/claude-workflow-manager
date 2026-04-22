<purpose>
Development workflow orchestrator — entry point for resuming work. Loads project state, shows handoff summary, suggests next step.
</purpose>

<required_reading>
@~/.claude/rules/communication-rules.md
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
Build a selection list from active projects + scratch:

- **Projects only, one project** → auto-select it.
- **Scratch only** → auto-select scratch.
- **Multiple options** → present each active project (name, work type, current state), the scratch session (with date from its handoff) if one exists, and the option to start a new project (`/wm:new-project`). Ask the user which to resume. Presentation follows communication rules.
</step>

<step name="Step 4 — Load context (progressive disclosure)">
**If scratch selected:** Read `scratch/handoff.md`. Present its content as the resume summary. No state-machine routing — ask the user what to do next (continue the scratch session, start a new project via `/wm:new-project`, or redirect to something else). Wait for user choice. STOP (no routing to Steps 5-8). Presentation follows communication rules.

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
Summarize the relevant project state before asking anything else: the project name, work type, current state, last session line from STATE.md, and the next action from handoff.md. Keep it compact; presentation follows communication rules.
</step>

<step name="Step 7 — Recommend next action">
Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md

**Check handoff first:** If the handoff has a concrete "Next action" with actionable steps (commands, files, success criteria), continuing from the handoff is the primary option. Otherwise fall back to the state-based recommendation.

**If handoff is actionable:** recommend continuing from the handoff. The legitimate alternatives are: run the state-based command for the current state (see the table below), skip the current stage (`/wm:skip`), or redirect to something else the user has in mind. Ask the user to pick. If they pick to continue from handoff, skip the state machine and execute the handoff steps directly — no state update needed.

**If handoff is not actionable** (vague, missing, or just says "start discovery"): fall back to the state-based recommendation. The legitimate alternatives are: see full status first (`/wm:status`), skip the current stage (`/wm:skip`), or redirect.

State-based recommendation table:

| State | Recommendation |
|---|---|
| `between-cycles` | "Run `/wm:discover` to start discovery" |
| `backlog` | "Run `/wm:plan` to write the plan" |
| `planned` | "Run `/wm:verify-plan` to verify before executing" |
| `plan-verified` | "Run `/wm:execute` to start execution" |
| `executing` | "Run `/wm:execute` to resume execution" |
| `awaiting-release` | "Run `/wm:release` to complete the release" |

Presentation follows communication rules — name your recommendation, state the reason, and pick a shape that fits the context. Wait for user confirmation.
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
