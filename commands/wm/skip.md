---
name: wm:skip
description: "Skip current stage with logged justification. Conscious escape hatch. Trigger: /wm:skip, skip stage, pomin krok."
allowed-tools:
  - Read
  - Write
  - Edit
---

<objective>
Skip the current workflow stage with a logged justification. Conscious escape hatch — skips are recorded in STATE.md.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/skip.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/skip.md.
Ask for justification, log skip, advance state, and route to next command.
</process>
