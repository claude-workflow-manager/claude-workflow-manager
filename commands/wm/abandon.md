---
name: wm:abandon
description: "Abandon a project. Archives with reason, removes from active. Trigger: /wm:abandon, abandon project, porzuc projekt."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
---

<objective>
Abandon the active project. Archives it with a reason and removes it from the active list.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/abandon.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/abandon.md.
Ask for reason, record in STATE.md, move to archive, update ACTIVE.md.
</process>
