# Command + Workflow Structure

When building tools that combine a Claude Code command (`~/.claude/commands/`) with skill logic (`~/.claude/skills/`), follow this pattern.

## Architecture

```
~/.claude/commands/{namespace}/{command}.md   # Thin trigger (~20-25 lines)
~/.claude/skills/{namespace}/workflows/{command}.md  # Full procedural logic
~/.claude/skills/{namespace}/references/      # Shared config/lookup tables
```

Commands are **routers** — they define metadata and delegate to workflows.
Workflows are **executors** — they contain the step-by-step logic.
References are **config** — lookup tables, templates, static data.

## Command file format (thin trigger)

```markdown
---
name: {namespace}:{command}
description: "{One-line description. Include trigger phrases.}"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

<objective>
{2-4 sentence goal statement — what this command does and when to use it.}
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/{namespace}/workflows/{command}.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/{namespace}/workflows/{command}.md.
{1-2 sentence summary of the workflow steps.}
</process>
```

## Workflow file format

```markdown
<purpose>
{What this workflow does and when to use it.}
</purpose>

<required_reading>
<!-- plugin-root-fallback -->
@~/.claude/skills/{namespace}/references/{ref}.md
(or "(none — self-contained)" if no references needed)
</required_reading>

<process>
<step name="Step 1 — {name}">
{Detailed instructions for this step.}
</step>

<step name="Step 2 — {name}">
{Detailed instructions for this step.}
</step>
</process>
```

## Naming conventions

- Command file name = workflow file name (1:1 mapping)
- Use kebab-case: `new-project.md`, `verify-plan.md`
- Namespace matches the tool name: `wm`, `gsd`, etc.

## When to use this pattern

- Building a multi-command tool (like WM with 14 commands)
- Any command where the logic exceeds ~30 lines
- When multiple commands share references but have distinct workflows

## When NOT to use this pattern

- Single standalone command with simple logic (<30 lines)
- One-off scripts or utilities
- Commands that are purely informational (no workflow steps)

## Key principles

1. **Self-contained workflows** — Each workflow duplicates shared logic rather than extracting helpers. Extract only when duplication is proven painful.
2. **References are config, not logic** — Templates, lookup tables, routing tables. Never procedural steps.
3. **Frontmatter stays in commands** — `allowed-tools`, `description`, `name` live in the command file, not the workflow.
4. **@ references for loading** — Commands use `@path/to/workflow.md` to load workflow content at runtime.
