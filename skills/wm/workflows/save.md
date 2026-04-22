<purpose>
Save workflow state and create a handoff for the next session. This replaces `/handoff`.
</purpose>

<required_reading>
@~/.claude/rules/communication-rules.md
@~/.claude/rules/editing-rules.md
</required_reading>

<process>
<step name="Step 1 — Detect project or scratch mode">
Look for `projects/` directory and `projects/ACTIVE.md` with at least one active project.

**If active project found:** continue to Step 2 (project mode).

**If no active project found (scratch mode):**
1. Write `scratch/handoff.md` using the structured checkpoint format from Step 4
2. No git commit (scratch/ is gitignored)
3. No STATE.md, DECISIONS.md, or ACTIVE.md updates
4. Print: "Scratch handoff saved to `scratch/handoff.md`. Resume with `/wm:resume`."
5. **STOP** — do not continue.
</step>

<step name="Step 2 — Check uncommitted changes">
Run `git status`. If there are uncommitted changes:
1. Stage relevant files
2. Commit: `wip: {project-name} — save state`
</step>

<step name="Step 3 — Update STATE.md last session">
Update the `## Last session` section in `projects/{name}/STATE.md`:

```
{YYYY-MM-DD} — {summary of what was done}. Done: {N}/{M} tasks. Next: {what to do next}.
```
</step>

<step name="Step 4 — Write structured handoff">
Follow [#Editing Rules](rules/editing-rules.md#editing-rules) from rules/editing-rules.md

Write `projects/{name}/handoff.md` as a **structured checkpoint** — compact, machine-readable, scoped to the immediate next action. The resuming agent starts fresh with zero context.

**Target: under 500 tokens.**

```markdown
# Handoff — {project-name}

Date: {YYYY-MM-DD}

## State
Tier: {T0/T1/T2}
Step: {N of M} (or "not started")
State: {executing/planned/etc.}

## Next action
{One sentence: what to do next}

## How to execute
1. {specific step — command, file path, or workflow}
2. {next step}
3. {success criteria — what "done" looks like}

## Key files
- {path} — {one-line purpose}

## Open questions
- {anything unresolved, or "none"}
```

**Rules:**
- No narrative "accomplished" section — completed work is in git history and STATE.md
- Next action must be concrete: a command to run, a file to read, a workflow to invoke
- "How to execute" must be followable without asking the user for clarification
- Key files: only files the next session actually needs, not everything touched
</step>

<step name="Step 5 — Collect session stats">
Read hook sidecar data if available (best-effort, skip silently if files don't exist):

1. Tool gate: `~/.claude/hook-state/tool-gate-{session_id}.json` — count of investigated files
2. Context monitor: `~/.claude/hook-state/context-monitor-{session_id}.json` — message count

Append a stats block to the handoff:

```markdown
## Session stats
- Messages: {count from context-monitor sidecar, or "N/A"}
- Files investigated: {count from tool-gate sidecar, or "N/A"}
```

If no sidecar data exists, skip this section entirely.
</step>

<step name="Step 6 — Update ACTIVE.md">
Update the project's row in `projects/ACTIVE.md` with:
- Last session date: `{YYYY-MM-DD}`
- State: `{current-state}`
</step>

<step name="Step 7 — Confirm and STOP">
Print: "State saved. Resume with `/wm:resume` → {project name}."

**STOP — do not continue working after save.**
</step>
</process>
