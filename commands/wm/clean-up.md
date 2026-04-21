---
name: wm:clean-up
description: "Clean up projects and state. Archives stale projects, promotes or removes scratch files. Trigger: /wm:clean-up, clean up, cleanup, sprzątnij."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Glob
---

<objective>
Tidy the wm workspace: dry-report stale projects and aged scratch files, then archive projects and promote/remove scratch files on user confirmation.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/clean-up.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/clean-up.md.
Scan for stale projects and aged scratch files, show dry-run report, then execute user-approved actions.
</process>
