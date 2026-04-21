---
name: wm:next
description: "Advance to next workflow stage with gate check. Trigger: /wm:next, next stage, advance, dalej."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Skill
---

<objective>
Advance the active project to the next workflow stage, enforcing gates from the gate matrix.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/next.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/next.md.
Load state, determine next state from state machine, check gates, update STATE.md, and route to framework.
</process>
