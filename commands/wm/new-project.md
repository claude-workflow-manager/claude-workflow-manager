---
name: wm:new-project
description: "Create a new workflow project with state tracking. Trigger: /wm:new-project, new project, nowy projekt."
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
---

<objective>
Create a new workflow project with full state tracking scaffold. Asks for work type, folder name, creates all project files, and routes to discovery.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/new-project.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/new-project.md.
Gather project info, create scaffold from templates, commit non-ignored files, rename session, and route to discover.
</process>
