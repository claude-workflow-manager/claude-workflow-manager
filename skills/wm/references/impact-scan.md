# Impact Scan

Shared primitive for "what does this change touch and what does it break". Called from `/wm:discover`, `/wm:verify-plan`, `/wm:execute`, and `/wm:change`.

## Purpose

Before any edit (or any plan that proposes edits), scan the proposed change against four dimensions and produce a report the calling workflow can act on. The same primitive runs in two depths so light scans stay cheap and deep scans stay thorough.

## When to use which mode

| Mode | Cost | Use when |
|---|---|---|
| **light** | ~3 cheap ops | Conceptual check — "does this idea conflict with what we already decided?" Used in `/wm:discover` (per FIN), `/wm:change` triage and scoped class. |
| **deep** | full traversal | Concrete check — "does this implementation break something downstream?" Used in `/wm:verify-plan`, `/wm:execute` (pre-wave), `/wm:change` deep class. |

## The four dimensions

Every scan, regardless of mode, reports on these four dimensions:

1. **Files touched** — which files the change modifies, creates, or deletes
2. **FIN affected** — which DECISIONS.md entries (in this project and other active projects) reference or depend on the touched files
3. **Downstream consumers** — which other files/modules reference the touched symbols
4. **Plan / design drift** — whether the change deviates from an approved plan or design doc

The difference between light and deep is *how* each dimension is checked, not *whether*.

## Light mode

Cheap, fast, conceptual. Maximum 5 tool calls.

**Procedure:**

1. **Files touched** — derive from the proposal text. No filesystem walk. If the proposal names files, list them; if it names a symbol, do one `Read` of the most likely target file.
2. **FIN affected** — `Grep` the touched file paths and primary symbol names against `projects/*/DECISIONS.md`. Read `projects/ACTIVE.md` to find other active projects to scan.
3. **Downstream consumers** — `Grep` the primary symbol name across the repo (one call). Count references; do not open them.
4. **Plan / design drift** — if an active project has a plan or design doc, check whether the proposal is mentioned there. One `Read` per artifact, max two artifacts.

**Output (light):**

```
## Impact Scan (light) — {short subject}

Touched (declared): {file list or "TBD — no files declared"}
FIN affected: {FIN-IDs with project names, or "none found"}
Downstream references: {symbol → N references in M files, or "none"}
Plan/design drift: {"none" | "{specific deviation}"}

Verdict: clean | review needed | conflict
Reason: {one sentence}
```

## Deep mode

Thorough, file-level, blast-radius. No hard ceiling on tool calls but stay focused.

**Procedure:**

1. **Files touched** — read each file the proposal targets. If the proposal references a symbol, locate and read every definition. Build a concrete file list.
2. **FIN affected** — for each touched file, grep across `projects/*/DECISIONS.md`. For each FIN hit, read the FIN entry to determine whether it is *amended* or *broken* by the change. Classify each FIN as: unaffected / needs amendment / blocked.
3. **Downstream consumers** — grep each touched symbol across the repo. For each reference site, read enough context to judge whether the change is backward-compatible at that call site. Classify each reference as: safe / needs update / breaking.
4. **Plan / design drift** — read the active plan and design docs. Compare the proposal against plan steps and design constraints. Flag any new files not in the plan, any non-goals being violated, any wave/dependency assumption broken.

**Output (deep):**

```
## Impact Scan (deep) — {short subject}

### Files touched
- {path} — {action: modify/create/delete} — {one-line reason}
...

### FIN affected
| FIN | Project | Status | Action needed |
|---|---|---|---|
| FIN-XXX | {project} | unaffected / needs amendment / blocked | {description} |

### Downstream consumers
| Symbol | Reference site | Classification |
|---|---|---|
| {symbol} | {file:line} | safe / needs update / breaking |

### Plan / design drift
- {finding 1}
- {finding 2}
(or "none — proposal matches plan and design")

### Verdict
clean | review needed | conflict | blocked

### Recommended action
{specific next action — e.g., "amend FIN-003 before applying", "add Step 11 to plan covering downstream update", "abort and re-plan"}
```

## How calling workflows use the output

The calling workflow decides what to do with the verdict. Standard interpretations:

- **clean** — proceed with original plan
- **review needed** — present output to user, get explicit Y/N before proceeding
- **conflict** — pause; user must choose between amend / revise / abort
- **blocked** — hard stop; cannot proceed without resolving the blocker

The scan never edits files. It never updates DECISIONS.md. It only produces the report. Acting on the report is the caller's responsibility, and any FIN amendments must follow propose-before-edit.

## Calling pattern

A workflow file invokes impact-scan by including this reference and following the procedure inline. There is no separate executable — the procedure is the contract.

**Example call from a workflow file:**

```markdown
<step name="Step N — Run impact scan">
Read `~/.claude/skills/wm/references/impact-scan.md` and run the scan in {light|deep} mode against {what is being scanned}.

Use the output to decide next action:
- clean → continue to Step N+1
- review needed → present to user, wait for Y/N
- conflict → present options A/B/C
- blocked → STOP
</step>
```

## Non-goals

- Not an automated dependency graph builder
- Not a static analyzer
- Not a substitute for tests
- Does not edit files or DECISIONS.md under any circumstances
