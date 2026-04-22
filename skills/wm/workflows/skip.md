<purpose>
Skip the current workflow stage with a logged justification. This is a conscious escape hatch — skips are recorded.
</purpose>

<required_reading>
@~/.claude/rules/communication-rules.md
@~/.claude/rules/editing-rules.md
</required_reading>

<process>
<step name="Step 1 — Load project state">
Find the active project → read `projects/{name}/STATE.md` to get current state.
</step>

<step name="Step 2 — Ask for justification">
Name the state being skipped and ask the user for the justification. Presentation follows communication rules.

Wait for user response — Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md
</step>

<step name="Step 3 — Log the skip">
Follow [#Editing Rules](rules/editing-rules.md#editing-rules) from rules/editing-rules.md

In `projects/{name}/STATE.md`, find the `## Skips` section (create it if missing, before end of file).

Append a line:
```
- Skipped {current-state} → {next-state} — {justification} — {YYYY-MM-DD}
```
</step>

<step name="Step 4 — Advance state">
Update the `Current state:` line to the next state in the sequence:
```
between-cycles → backlog → planned → plan-verified → executing → awaiting-release → between-cycles
```
</step>

<step name="Step 5 — Route">
Announce the state transition (old state skipped, new state now active) and recommend the next command based on the new state (same routing table as `/wm`). Presentation follows communication rules.
</step>
</process>
