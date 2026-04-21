---
name: wm:verify-plan
description: "Run plan verification report. Gate: plan file must exist. Hard gate — waits for user approval. Trigger: /wm:verify-plan, verify plan, zweryfikuj plan."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Skill
---

<objective>
Run plan verification report before execution. Hard gate — checks coverage of decisions, compliance with design, approach soundness, and gates. Requires user approval to proceed.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/verify-plan.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/verify-plan.md.
Load state, check plan exists, route to framework verification, run WM checks, present report, walk through issues, update state on approval.
</process>
