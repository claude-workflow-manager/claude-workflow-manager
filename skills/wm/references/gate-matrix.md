# Workflow Manager — Gate Matrix

## Tier Classification

Work type sets a **default tier**. The agent can **upgrade** based on signals during planning.

### Default Tiers

| Work type | Default Tier | Description |
|---|---|---|
| `fix` | T0 | Bug fix, typo, small correction |
| `test` | T0 | Testing, validation, experimentation |
| `next-version` | T1 | Enhancement to existing skill/agent |
| `new` | T1 | New tool, plugin, utility |
| `skill` | T2 | New skill or major rewrite |
| `new-agent` | T2 | New agent from scratch |
| `app` | T2 | Application or major feature |

### Upgrade Rules

| Signal | Upgrade to | Rationale |
|---|---|---|
| Touches >3 files | T1 (if T0) or T2 (if T1) | Higher blast radius needs more planning |
| Touches public API, data model, or migration | T2 | High coupling, hard to reverse |
| Cross-module changes | T2 | Integration risk |
| Architectural ambiguity (new patterns, unknown approach) | T2 | Discovery needed before implementation |

**Auto-upgrade rule:** If ANY task touches >3 files or modifies shared state (public API, data model, migration), auto-upgrade to T2 regardless of initial classification.

### Tier Postures

| Tier | Posture | Planning | Execution | Verification |
|---|---|---|---|---|
| T0 | "Just do it" | No plan file. Intent in commit message. | Single-pass, main context | L1-L2 (static + targeted tests) |
| T1 | "Checklist" | 5-15 checkbox plan with files + verify commands | Sequential, main context | L1-L3 (static + targeted + regression at end) |
| T2 | "Plan-verified" | Full plan with waves, intent, risk, verification | Wave-based, parallel subagents for independent steps | L1-L4 mandatory + L5 opt-in (reviewer subagent) |

## Gate Matrix

| Gate | T0 | T1 | T2 |
|---|---|---|---|
| DECISIONS.md has entries | Soft | **Hard** | **Hard** |
| Archive copy made + committed | Skip | Soft (agent context only — FIN-017) | Soft (agent context only — FIN-017) |
| Plan file exists | Skip | **Hard** | **Hard** |
| Plan verification report | Skip | Skip | **Hard** |
| Version bump recorded | Skip | Soft (next-version/skill) | **Hard** (next-version/skill) |
| All tasks have commits | Soft | **Hard** | **Hard** |
| DECISIONS.md all `status: applied` | Skip | Soft | **Hard** |

## Gate Meanings

- **Hard:** Gate must be met before advancing. Blocked until resolved. `/wm:skip` can override with logged justification.
- **Soft:** Gate is recommended but not required. User is prompted with labeled options:
  ```
  Gate '{gate}' not met.
  A) Do it now — {specific action}  ← recommended
  B) Skip — proceed without it
  ```
  User types `ok` or `A` → do the action. `B` → skip. Always recommend A for soft gates.
- **Skip:** Gate does not apply at this tier. Auto-pass, no prompt.

## Verification Ladder

| Level | Method | T0 | T1 | T2 |
|---|---|---|---|---|
| L1 | Static (lint, typecheck, format) | per step | per step | per step |
| L2 | Targeted tests (changed module) | end | per step | per step |
| L3 | Regression suite (broader test run) | — | end | per step |
| L4 | Runtime smoke (run app, validate key path) | — | — | end |
| L5 | Reviewer subagent (read-only diff review) | — | — | opt-in (`review: true` in plan step) |

**Evidence rule:** Verification must produce external, reproducible output (command output, test results, lint output). Agent asserting "looks good" is not evidence.

## Gate Check Procedures

### DECISIONS.md has entries
1. Read `projects/{name}/DECISIONS.md`
2. Check for at least one entry block (lines starting with `### `)
3. Fail: "No decisions found. Run `/wm:discover` first."

### Archive copy made + committed
**Precondition (FIN-017):** This gate fires only when `cwd` contains `agent.md` (i.e., the project is an agent project, like a Markdown-Agents agent). For non-agent projects (WM dev work, generic dev tools, code repos), the gate is silently skipped — git already tracks history, so an additional archive snapshot is noise. Detection: `test -f cwd/agent.md`.

If precondition is met:
1. Read DECISIONS.md header for target skill/agent name and current version
2. Look for archive folder: `skills/{name}/archive/{name}-v{version}/` or equivalent
3. Run `git log --oneline -- "skills/{name}/archive/"` — confirm commit exists
4. Fail: "Archive gate not met. Copy `skills/{name}/` to `skills/{name}/archive/{name}-v{current}/` and commit."

If precondition is NOT met (no `agent.md` in cwd): skip silently — no prompt, no warning, no log.

### Plan file exists
1. Check `projects/{name}/plans/` for at least one `.md` file (not `.gitkeep`)
2. Fail: "No plan file found. Run `/wm:plan` first."

### Plan verification report
1. Check that user has presented or confirmed a plan verification in this session
2. Look for verification section in STATE.md or a recent message confirming plan review
3. Fail: "Plan not verified. Run `/wm:verify-plan` first."

### Version bump recorded
1. Read DECISIONS.md header for `Target version:` line — must not be `TBD`
2. Fail: "Version bump not recorded. Run `/wm:plan` to confirm version."

### All tasks have commits
1. Read plan file — count total tasks/steps
2. Run `git log --oneline -20` — look for task completion commits
3. If count mismatch, present:
   ```
   N of M tasks appear committed.
   A) Continue anyway  ← recommended
   B) Stop — review missing commits
   ```

### DECISIONS.md all `status: applied`
1. Read DECISIONS.md entries
2. Check each entry for `Status: applied`
3. List any entries missing applied status
4. Fail: "Entries not marked applied: [list]. Update DECISIONS.md before releasing."
