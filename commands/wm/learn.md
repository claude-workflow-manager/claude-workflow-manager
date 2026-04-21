---
name: wm:learn
description: "Capture a lesson from the current session and route it to the partition where it actually compounds. Investigates, recommends, never auto-saves. Trigger: /wm:learn, learn, capture lesson, naucz, zapisz lekcję."
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
Capture a lesson from the current session — either something that went wrong (Mode A: diagnose) or something that went well (Mode B: extract) — and route it to the partition where it earns its keep: a global communication file, a skill reference, an agent's craft knowledge, a hook script, or a project-level learnings file. The command investigates and recommends with reasoning; the user decides and approves every change. Nothing is saved automatically.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/learn.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/learn.md.
Load session context, classify mode, identify candidate partitions, investigate the lesson, classify into the appropriate bucket (text rule / hook / skill), run the five checks for text-rule recommendations, present the recommendation with reasoning, and on approval save the artifact with inline test metadata.
</process>
