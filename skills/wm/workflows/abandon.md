<purpose>
Abandon the active project. Archives it with a reason and removes it from the active list.
</purpose>

<required_reading>
@~/.claude/rules/communication-rules.md
@~/.claude/rules/editing-rules.md
</required_reading>

<process>
<step name="Step 1 — Load project state">
Find the active project → read `projects/{name}/STATE.md`.
</step>

<step name="Step 2 — Ask for reason">
Ask the user why the project is being abandoned. Presentation follows communication rules.

Wait for user response — Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md
</step>

<step name="Step 3 — Record in STATE.md">
Append to `projects/{name}/STATE.md`:

```
## Abandoned
Abandoned — {reason} — {YYYY-MM-DD}
```
</step>

<step name="Step 4 — Archive">
Follow [#Editing Rules](rules/editing-rules.md#editing-rules) from rules/editing-rules.md

1. Move `projects/{name}/` → `projects/archive/{name}-abandoned/`
2. Remove the project row from `projects/ACTIVE.md`
</step>

<step name="Step 5 — Confirm">
Announce that the project has been abandoned and archived. Presentation follows communication rules.
</step>
</process>
