---
name: wm:resume
description: "Resume work from last session. Loads project state, shows handoff summary, suggests next step. Trigger: /wm:resume, resume, wznów pracę, co dalej."
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
Resume work from the last session. Loads project state, shows handoff summary, and routes to the appropriate next action. Supports both project mode and scratch handoffs.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/resume.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/resume.md.
Detect projects/scratch, select project, load context, rename session, present summary, recommend and route to next action.
</process>
