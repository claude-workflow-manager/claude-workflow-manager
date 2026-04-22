# Skill-Building Guidelines

Actionable reference for designing and writing Claude Code skills. Load this file during discovery and planning for projects with work type `skill`.

---

## When to Build a Skill (hub decision)

Build a skill when the knowledge or workflow is reusable across sessions, needs to carry scripts or assets alongside instructions, or would bloat CLAUDE.md if inlined. A one-off workflow that won't recur does not need a skill — inline it or handle it directly. The clearest signal: if you'd want to hand the same instructions to Claude twice, it's a skill.

Skills cluster into identifiable types: library/API reference, product verification, data analysis, business automation, scaffolding/templates, code quality/review, CI/CD, runbooks, infrastructure ops. The most durable skills fit cleanly into one type.

## SKILL.md Hub Budget (budget)

Keep SKILL.md at 30–50 lines. The hub dispatches; spoke files do the work. If SKILL.md is growing past 50 lines, it has taken on spoke responsibilities — split the overflow into named child files.

Split criteria:
- Each distinct topic or symptom gets its own file (`stuck-jobs.md`, `dead-letters.md`)
- Reference tables, full API signatures, and code snippets belong in `references/api.md` or similar
- If you're thinking "the model won't need this every time", it belongs in a spoke

A 30-line hub that routes cleanly beats a 200-line monolith that the model has to scan end-to-end.

## Symptom-Based Organization (symptom)

Organize by what went wrong or what the user is trying to do — not by what the code does internally. A runbook indexed by symptom ("jobs sit pending, never run" → `stuck-jobs.md`) is immediately useful. A runbook indexed by component ("Queue class", "Worker class") requires the user to know the answer before asking the question.

This applies beyond runbooks: scaffolding skills ("new migration", "new endpoint") should be organized by intent, not by internal layer order. Verification skills should be organized by scenario, not by assertion sequence.

## Description Field as Trigger (description)

The description field in SKILL.md's frontmatter is not a user-facing summary. Claude Code scans all available skill descriptions to decide which skill to invoke for a given request. Write it as a dispatch signal: what phrases or situations should trigger this skill?

Less effective:
```
description: A comprehensive tool for monitoring pull request status.
```

Better:
```
description: Monitors a PR until it merges. Trigger on 'babysit', 'watch CI', 'make sure this lands'.
```

One sentence, concrete triggers, no fluffy preamble.

## Gotchas Section Pattern (gotchas)

A `## Gotchas` or `## Common Pitfalls` section is the highest-signal content in any skill. It should be built iteratively from real failures — not written speculatively upfront. On Day 1, you might have nothing. By Week 2, you've seen Claude trip on one thing; add a line. By Month 3, the gotchas section is the most-read part of the file.

Format: bullet list, one failure per bullet, written as a concrete rule.

Example:
```
## Gotchas
- Proration rounds DOWN, not to nearest cent.
- test-mode skips the invoice.finalized hook.
- idempotency keys expire after 24h, not 70.
- refunds need charge ID, not invoice ID.
```

Never delete a gotcha unless the underlying issue is definitively fixed. Treat it as a changelog of observed failures.

## Script and Library Placement (lib)

Scripts, helper functions, and data files belong in subdirectories — not inline in SKILL.md or spoke files. Standard layout:

- `lib/` — reusable Python/shell helpers (the agent imports or sources these)
- `assets/` — templates, fixtures, static reference data
- `references/` — detailed markdown files too long for the hub

Giving Claude a library of pre-built helper functions means it spends its turns on composition ("what to do next") rather than reconstruction ("write the function again from scratch"). This is the leverage point.

Data files that must persist across skill upgrades go in `${CLAUDE_PLUGIN_DATA}` (a stable per-skill directory), not inside the skill folder itself.

## Anti-Proliferation Discipline (curation)

Every skill added to a shared marketplace or team install adds a small context cost on every session. Before publishing:
- Check whether an existing skill already covers the same ground
- The sandbox-then-traction model works: share the skill informally first, move to the marketplace only after it has demonstrated usefulness
- Redundant skills are worse than no skill — they cause the agent to scan two overlapping dispatch signals and potentially make wrong routing decisions

One sharp skill beats three vague ones.

## Anti-Railroading (railroading)

Skills are reused across many situations. Over-prescribed step sequences break when the situation is slightly different from what you imagined. Leave structural headroom.

Too prescriptive:
```
Step 1: Run git log. Step 2: Run git cherry-pick <hash>. Step 3: If conflicts, run git status...
```

Better:
```
Cherry-pick the commit onto a clean branch. Resolve conflicts preserving intent.
If it can't land cleanly, explain why.
```

Give the agent what it needs to know, not a script to follow blindly. Reserve tight sequencing for cases where order genuinely matters (e.g., safety gates, destructive operations).

## Cross-cutting conventions

- Rule-reminder pattern: `references/rule-reminder-pattern.md` — how to cite rules in workflow files (required for all new workflows).

---

## Source

`docs/research/building-skills/Lessons-from-Building-Claude-Code-How-We-Use-Skills.md`
