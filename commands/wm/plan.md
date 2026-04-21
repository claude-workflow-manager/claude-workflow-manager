---
name: wm:plan
description: "Enter planning stage. Gate: DECISIONS.md entries must exist. Handles archive gate and version bump. Trigger: /wm:plan, plan, zaplanuj."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Skill
  - Agent
---

<objective>
Enter planning stage for the active project. Enforces gates (decisions exist, archive made, version bumped), then routes to framework planner.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/plan.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/plan.md.
Load state, check gates, handle archive and version bump, route to framework planner, update state.
</process>
