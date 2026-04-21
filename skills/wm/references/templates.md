# Workflow Manager — File Templates

## STATE.md Template

```markdown
# Project State — {project-name}

Work type: {next-version | fix | skill | new-agent | new | test | app}
Current state: between-cycles
Target: {target skill/agent name, or "TBD"}
Started: {YYYY-MM-DD}

## Last session
(none yet)

## Skips
(none)
```

## DECISIONS.md Template

```markdown
# Decisions — {project-name}

Work type: {next-version | fix | skill | new-agent | new | test | app}
Target version: TBD
Started: {YYYY-MM-DD}

---

<!-- Add entries below using the format:
### {FIN-XXX}: {Decision title}
Decision: {What was decided}
Rationale: {Why — be concise}
Implementation: {How it's done — specific, checkable}
Done-when: {Concrete, observable criterion}
Status: pending
-->
```

**FIN-001 Auto-include rule:** For work types `next-version` and `skill`, automatically add the following entry as the first entry in DECISIONS.md (consumed by `new-project.md`):

```markdown
### FIN-001: Archive previous version before making changes
Decision: Archive the current version before any modifications.
Rationale: Enables clean rollback and comparison.
Implementation: Copy `{target}/` to `{target}/archive/{target}-v{current}/` and commit.
Done-when: Archive folder exists and is committed to git.
Status: pending
```

> **Note (FIN-017):** v2.1 narrows the archive gate so it fires only when the project's `cwd` contains `agent.md` (an agent project), not on all `next-version`/`skill` work. The auto-include rule above is unchanged in v2.1 scope (`new-project.md` is not in v2.1's edit list per design §7); a future project should update `new-project.md` to make the auto-include conditional on agent context too.

### Status field — 4-state model (FIN-013)

`Status:` follows a 4-state machine: **`pending → done → verified → applied`**.

| State | Set by | Meaning |
|---|---|---|
| `pending` | discovery / plan | FIN exists in DECISIONS.md but no code has been written yet |
| `done` | `/wm:execute` (FIN-014) | Step is implemented and committed; not yet verified |
| `verified` | `/wm:verify` (FIN-015) | Done-when criterion confirmed met with evidence by reviewer subagent |
| `applied` | `/wm:release` (FIN-016) | Promoted at release; deployed |

State transitions are mechanical writebacks performed by the listed workflow command. Illegal transitions (e.g., `pending → applied` without passing through `done` and `verified`) trigger a hard warning at release time per FIN-016.

## ACTIVE.md Template

```markdown
# Active Projects

| Project | Work type | State | Last session | Notes |
|---|---|---|---|---|
| {name} | {work-type} | between-cycles | {YYYY-MM-DD} | {optional} |
```

## handoff.md Template

Structured checkpoint — compact, scoped to the immediate next action. Target: under 500 tokens.

```markdown
# Handoff — {project-name}

Date: {YYYY-MM-DD}

## State
Tier: {T0/T1/T2}
Step: {N of M} (or "not started")
State: {executing/planned/etc.}

## Next action
{One sentence: what to do next}

## How to execute
1. {specific step — command, file path, or workflow}
2. {next step}
3. {success criteria — what "done" looks like}

## Key files
- {path} — {one-line purpose}

## Open questions
- {anything unresolved, or "none"}
```

No narrative "accomplished" section — completed work is in git history and STATE.md.

## T1 Plan Template (Checklist)

```markdown
# Plan: {title}
Tier: T1
Work type: {type}

## Intent
Problem: {what's wrong or missing}
Target outcome: {what success looks like}
Non-goals: {what we're NOT doing}

## Steps
- [ ] Step 1 — {what to do} → files: [{file paths}] → verify: {command}
- [ ] Step 2 — {what to do} → files: [{file paths}] → verify: {command}
- [ ] Step 3 — {what to do} → files: [{file paths}] → verify: {command}
...
```

5-15 checkboxes max. Each step: what to do, which files, how to verify.

## T2 Plan Template (Plan-Verified)

```markdown
# Plan: {title}
Tier: T2
Work type: {type}

## Intent
Problem: {what's wrong or missing}
Target outcome: {what success looks like}
Non-goals: {what we're NOT doing}

## Risk & Constraints
Blast radius: {files/modules affected}
Novelty: {low/medium/high — what's new or unfamiliar}
Rollback plan: {how to undo if it goes wrong}

## Steps

### Step 1: {name}
Wave: {N}
Files: [{file paths}]
Edit intent: {what changes, not how — structured intent}
Verify: {command(s) to run for evidence}
Done-when: {acceptance criteria + evidence}

### Step 2: {name}
Wave: {N}
Depends-on: [{previous steps if any}]
Files: [{file paths}]
Review: {true — only if this step needs reviewer subagent}
Edit intent: {what changes}
Verify: {command(s)}
Done-when: {criteria}

...
```

Optional machine-readable metadata at end of plan:

```yaml
plan_meta:
  tier: T2
  waves: {N}
  steps: {M}
  parallel_steps: [{step numbers in same wave}]
  requires:
    plan_verification: true
    decisions_entry: true
```

**Wave rules:**
- Steps in the same wave with no shared files can run in parallel subagents
- Steps in later waves wait for all dependencies to complete
- Max 3 parallel subagents per wave
- No shared files across parallel subagents (single integrator rule)

## AGENTS.md Template

Create only if `AGENTS.md` does not exist in the project root.

```markdown
# AGENTS.md - Project Constitution

## Project Identity

**Project:** {project-name}
**Purpose:** {one-line purpose}

## Agent Rules

Rules are scoped by activity in `rules/`:
- `discovery-rules.md` — decision-making, evaluating options
- `execution-rules.md` — delegation, context management, structural navigation
- `editing-rules.md` — change discipline, verification, simplicity
- `review-rules.md` — critical evaluation, self-challenge
- `communication-rules.md` — the 9 global communication rules (authoritative)

---

## Project Structure

(describe your file layout here)
```

When creating a new project with AGENTS.md, also create the four scoped rule files in `.claude/rules/`. See the WM dev repo `rules/` for reference content.

## .gitignore Template

Create only if `.gitignore` does not exist in the project root.

```
# Temporary
scratch/

# Planning artifacts
.planning/
projects/
tests/

# Python
__pycache__/
*.pyc

# Claude settings
.claude/
```

## Verification Report Template (Plan)

```markdown
## Plan Verification — {project-name}

Date: {YYYY-MM-DD}
Plan file: projects/{name}/plans/{plan-file}.md

### Coverage
- DECISIONS.md entries: {N}
- Plan tasks: {M}
- Mapped: {X}/{N} decisions covered by plan tasks

### Gates
- [ ] Archive committed (next-version/skill only)
- [ ] Version bump recorded in DECISIONS.md
- [ ] Compliance scope declared (if spec work)

### Design coverage
Design doc: {path or "none — check skipped"}

| Decision | Covered by | Status |
|---|---|---|
| {decision text} | {Step N Done-when} | covered |
| {decision text} | — | gap (fixed: amended Step N) |
| {decision text} | — | gap (N/A: {reason}) |
| {decision text} | — | gap (accepted: {reason}) |

### Verdict
{Ready to execute | Issues to fix | Proceed with caution}

### Issues
{List any items with specific fix actions}
```

## Verification Report Template (Implementation)

```markdown
## Implementation Verification — {project-name}

Date: {YYYY-MM-DD}

### Done-when checks
{For each DECISIONS.md entry:}
- {FIN-XXX} {title}: {evidence | not met | judgment call}

### Cross-file consistency
- Version numbers consistent: {yes | no}
- Archive integrity: {yes | no | N/A}

### Verdict
{Ready to release | Fix required | Judgment call — user decision}

### Issues
{List items with fix actions}
{List items with A/B/C options}
```

## Command Trigger Template

For projects building command+skill combinations. See `references/command-structure.md` for full pattern docs.

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
{2-4 sentence goal statement.}
</objective>

<execution_context>
<!-- plugin-root-fallback -->
@~/.claude/skills/{namespace}/workflows/{command}.md
</execution_context>

<process>
<!-- plugin-root-fallback -->
Follow the workflow at @~/.claude/skills/{namespace}/workflows/{command}.md.
{1-2 sentence delegation summary.}
</process>
```

## Workflow File Template

```markdown
<purpose>
{What this workflow does and when to use it.}
</purpose>

<required_reading>
<!-- plugin-root-fallback -->
@~/.claude/skills/{namespace}/references/{ref}.md
</required_reading>

<process>
<step name="Step 1 — {name}">
{Detailed instructions.}
</step>

<step name="Step 2 — {name}">
{Detailed instructions.}
</step>
</process>
```
