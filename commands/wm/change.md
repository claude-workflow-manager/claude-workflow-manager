---
name: wm:change
description: "Adaptive change command. Auto-triages requests into trivial/scoped/deep and applies matching discipline. Replaces /wm:quick. Works standalone or in active project. Trigger: /wm:change, change, edit, fix this, popraw, zmień."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Glob
  - Grep
---

<objective>
Adaptive change command. Triages every request into trivial / scoped / deep and applies matching discipline — never edits without first looking. Works standalone or integrated with an active project.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/change.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/change.md.
Parse request, detect project context, run cheap triage, apply user overrides, route to trivial/scoped/deep path, propose-before-edit for non-trivial changes.
</process>
