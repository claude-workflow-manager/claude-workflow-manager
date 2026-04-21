---
name: wm:save
description: "Save workflow state and create handoff for next session. Replaces /handoff. Trigger: /wm:save, save state, zapisz stan, pause work."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
---

<objective>
Save workflow state and create a handoff for the next session. Supports both project mode and scratch mode.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/save.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/save.md.
Detect mode, commit uncommitted changes, update STATE.md, write handoff, update ACTIVE.md, and STOP.
</process>
