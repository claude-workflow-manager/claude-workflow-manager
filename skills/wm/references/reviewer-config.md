# Reviewer Config

Single source of truth for the reviewer subagent model used by WM verification commands.

## Default reviewer model

```yaml
default_reviewer_model: claude-sonnet-4-6
```

Workflow commands that spawn a reviewer subagent read the model name from this file at the start of their reviewer step. Changing the model is a one-line edit here, not a sweep across multiple workflow files.

## Why an independent reviewer

When the same agent (or the same model in the same context) reviews its own work, it tends to validate the original framing instead of critically evaluating it. The v2.0 research flagged this as the highest-impact failure mode in WM verification — *inter-agent sycophancy*. A reviewer that shares context with the planner almost always agrees with the planner.

The mitigation has three parts, applied together:

1. **Pinned model** — the reviewer runs on a fresh Sonnet thread. Different instance, no inherited reasoning, no shared context with the planner.
2. **Artifact-only input** — the reviewer receives `git diff`, raw test/lint output, and the literal `Done-when` string from the plan step. It does **not** receive narrative summaries from the primary agent, the planner's reasoning, or any "what I did and why" explanation.
3. **No prior context** — the reviewer evaluates the artifacts on their merits, not the plan's claims about them. Its only question is *"does this diff satisfy this Done-when string?"*

If any of the three is dropped, the failure mode returns. Don't optimize one away.

## How workflow commands consume this file

A workflow that needs to spawn a reviewer follows this pattern:

1. Read `~/.claude/skills/wm/references/reviewer-config.md` to get `default_reviewer_model`.
2. Assemble the artifact bundle: `git diff` of the step's changes, raw test/lint output (from `verification-output.log` if available), the plan step's `Done-when` string, and any `/wm:doc-graph` query results relevant to the check.
3. Spawn a `general-purpose` subagent with `model: <default_reviewer_model>` and the artifact bundle as the only input.
4. Receive the structured verdict (pass/fail per check, evidence pointers, concerns).
5. Render the verdict in the workflow's chat report.

The reviewer subagent itself does **not** read this file — it only knows it has been spawned with a specific model and a specific input bundle. The choice of model is made by the spawning workflow.

## Per-step override

If a specific plan step needs a different reviewer model (e.g., a higher-stakes step wants Opus instead of Sonnet), the step can declare it inline:

```
Review: true
Reviewer-model: claude-opus-4-6
```

When a step has `Reviewer-model:`, that value wins over `default_reviewer_model` from this file. Use sparingly — the default is the right choice for almost all steps.

## Related FINs

- **FIN-010a** — `verify-plan` reviewer subagent (Sonnet, artifact-only input)
- **FIN-010b** — `verify` L5 reviewer pinned to Sonnet, artifact-only input contract
- **FIN-010c** — L5 reviewer default-on for T2 projects
- **FIN-010d** — this file: single reviewer-model config reference
- **FIN-012b** — `change.md` deep-path reviewer subagent (uses this file)
