---
name: wm:verify
description: "Run implementation verification. Gate: execution must be complete. Hard gate — waits for user approval. Trigger: /wm:verify, verify, zweryfikuj implementację."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Skill
---

<objective>
Run implementation verification after execution. Checks done-when criteria from DECISIONS.md against actual files and behavior. Hard gate — requires user approval to advance to release.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/verify.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/verify.md.
Load state, gate check (executing), route to framework verification, run WM checks (done-when, compliance, consistency, behavior), present report, walk through issues, update state on approval.
</process>
