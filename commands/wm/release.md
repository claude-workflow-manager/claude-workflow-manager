---
name: wm:release
description: "Run release steps. Gate: implementation must be verified. Handles release checklist and project archiving. Trigger: /wm:release, release, wydaj."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Skill
---

<objective>
Run release steps for the active project. Handles work-type-specific release actions (version bump, changelog, decisions promotion) and project archiving.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/release.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/release.md.
Gate check (awaiting-release), dispatch by work type, route to framework release, archive project.
</process>
