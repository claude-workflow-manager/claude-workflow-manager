---
name: wm:status
description: "Show current workflow status. Quick check without changing state. Trigger: /wm:status, status, where are we, jaki status."
allowed-tools:
  - Read
  - Bash
---

<objective>
Show current workflow status across all active projects. Read-only — does not change state.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/status.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/status.md.
Read ACTIVE.md and each project's STATE.md to show status summary.
</process>
