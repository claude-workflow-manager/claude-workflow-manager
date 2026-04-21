<purpose>
Skip the current workflow stage with a logged justification. This is a conscious escape hatch — skips are recorded.
</purpose>

<required_reading>
(none — self-contained, uses inline state transition order)
</required_reading>

<process>
<step name="Step 1 — Load project state">
Find the active project → read `projects/{name}/STATE.md` to get current state.
</step>

<step name="Step 2 — Ask for justification">
Print: "Skipping `{current-state}`. What's the justification?"

Wait for user response.
</step>

<step name="Step 3 — Log the skip">
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
Print: "Skipped `{old-state}`, now at `{new-state}`."

Recommend the next command based on the new state (same routing table as `/wm`).
</step>
</process>
