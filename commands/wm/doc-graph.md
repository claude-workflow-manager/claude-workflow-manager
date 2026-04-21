---
name: wm:doc-graph
description: "Structural map builder/querier for markdown-heavy repositories. Verbs: build, refs, ls, outline, impact, check, search. Trigger: /wm:doc-graph."
allowed-tools:
  - Bash
  - Read
  - Skill
---

<objective>
Build and query a structural graph of markdown files, references, headers,
and signal markers in the current repository. Wraps the Python wm-doc-graph
tool behind a unified slash-command interface so workflow files can query
graph data without issuing raw `python -m wm_doc_graph` calls.
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/workflows/doc-graph.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/wm/workflows/doc-graph.md.
Parse the verb + arguments, dispatch to the Python tool via Bash,
relay the output to chat. This workflow is the canonical entry point —
other WM workflows call `/wm:doc-graph` via Skill dispatch (FIN-018c).
</process>
