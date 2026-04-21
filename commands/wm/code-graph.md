---
name: wm:code-graph
description: "Code repository graph operations — thin wrapper around the code-review-graph MCP server. For markdown repos, use /wm:doc-graph instead. Trigger: /wm:code-graph."
allowed-tools:
  - Bash
  - Read
  - Skill
---

<objective>
Expose code repository graph operations through WM's unified `/wm:*`
slash-command surface. Thin wrapper around the existing
`code-review-graph` MCP server — dispatches verbs to the MCP's native
tools and relays their output. For markdown-heavy repositories, use
`/wm:doc-graph` instead.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/code-graph.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/code-graph.md.
Enforce the markdown-only scope guard, verify the MCP server is
available, parse the verb, dispatch to the appropriate
`mcp__code-review-graph__*` tool, relay output.
</process>
