---
name: wm:execute
description: "Enter execution stage. Gate: plan must be verified. Supports resume. Trigger: /wm:execute, execute, start building, wykonaj."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Skill
  - Agent
  - TodoWrite
---

<objective>
Enter or resume execution of the plan for the active project. Gates: plan must be verified before starting fresh.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/execute.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/execute.md.
Check state, handle resume vs fresh start, route to framework executor.
</process>
