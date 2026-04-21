<purpose>
Abandon the active project. Archives it with a reason and removes it from the active list.
</purpose>

<required_reading>
(none — self-contained)
</required_reading>

<process>
<step name="Step 1 — Load project state">
Find the active project → read `projects/{name}/STATE.md`.
</step>

<step name="Step 2 — Ask for reason">
Print: "Why are you abandoning `{name}`?"

Wait for user response.
</step>

<step name="Step 3 — Record in STATE.md">
Append to `projects/{name}/STATE.md`:

```
## Abandoned
Abandoned — {reason} — {YYYY-MM-DD}
```
</step>

<step name="Step 4 — Archive">
1. Move `projects/{name}/` → `projects/archive/{name}-abandoned/`
2. Remove the project row from `projects/ACTIVE.md`
</step>

<step name="Step 5 — Confirm">
Print: "Project `{name}` abandoned and archived."
</step>
</process>
