<purpose>
Advance the active project to the next workflow stage, enforcing gates. Tier-aware — uses the appropriate state flow for the project's tier.
</purpose>

<required_reading>
@~/.claude/rules/communication-rules.md
@~/.claude/rules/editing-rules.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/state-machine.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/gate-matrix.md
</required_reading>

<process>
<step name="Step 1 — Load project state">
Find the active project → read `projects/{name}/STATE.md` to get current state and work type.

Determine tier: read plan file header for `Tier:` line, or infer from work type defaults in gate-matrix.md.
</step>

<step name="Step 2 — Determine next state">
Read `~/.claude/skills/wm/references/state-machine.md`.

Use the tier-appropriate state flow:
```
T2: between-cycles → backlog → planned → plan-verified → executing → awaiting-release → between-cycles
T1: between-cycles → backlog → planned → executing → awaiting-release → between-cycles
T0: between-cycles → backlog → executing → awaiting-release → between-cycles
```

Identify the next state from the current one based on the project's tier.
</step>

<step name="Step 3 — Check gates">
Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md

Read `~/.claude/skills/wm/references/gate-matrix.md`.

Look up all gates for this transition and tier. For each gate:

- **Hard** gate not met → STOP. Tell the user which gate is missing and the specific fix action. Do not advance.
- **Soft** gate not met → ask the user whether to do the specific fix action now (recommended) or skip and proceed without it. On approval, do the action and continue; on skip, continue without it. Presentation follows communication rules.
- **Skip** → auto-pass, no prompt.

If any Hard gate blocks, surface all blocking gates at once so the user can fix them all.
</step>

<step name="Step 4 — Update STATE.md">
Follow [#Editing Rules](rules/editing-rules.md#editing-rules) from rules/editing-rules.md

Update the `Current state:` line in `projects/{name}/STATE.md` to the new state.
</step>

<step name="Step 5 — Auto-route to next workflow">
Announce the state advance and that the workflow is routing to the next command. Presentation follows communication rules.

Then **automatically invoke** the appropriate WM workflow command — do not stop and ask the user to run it manually:

| New state | Auto-invoke |
|---|---|
| `backlog` | `/wm:plan` |
| `planned` | `/wm:verify-plan` (T2) or `/wm:execute` (T1/T0) |
| `plan-verified` | `/wm:execute` |
| `executing` | `/wm:execute` |
| `awaiting-release` | `/wm:release` |
| `between-cycles` | No action — cycle complete. Print: "Cycle complete. Project archived." |
</step>
</process>
