---
name: wm:discover
description: "Enter discovery stage. Two-phase discovery: open conversation then structured gray areas. Trigger: /wm:discover, discover, explore, zbadaj."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Agent
  - Glob
  - Grep
---

<objective>
Enter discovery stage for the active project. Two-phase unified discovery: open conversation as thinking partner, then structured gray areas exploration. Produces design doc and DECISIONS.md entries.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/discover.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/discover.md.
Load context, run Phase 1 (open conversation), run Phase 2 (gray areas), write artifacts, extract decisions.
</process>
