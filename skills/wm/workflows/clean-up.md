<purpose>
Tidy the wm workspace: archive stale projects, promote or remove aged scratch files. Always shows a dry-run report before making any changes.
</purpose>

<required_reading>
@~/.claude/rules/communication-rules.md
@~/.claude/rules/editing-rules.md
</required_reading>

<process>
<step name="Step 1 — Scan">
Collect two lists:

**Projects to review:** List all subdirectories in `projects/` (excluding `archive/`). For each, read its `STATE.md` to get current state and last session date. Include all projects regardless of age.

**Scratch files:** List all files under `scratch/` (recursively). Include all files regardless of age. For each, get last-modified date via Bash `stat` to show in the report.
</step>

<step name="Step 2 — Dry-run report">
Print report. Do not make any changes yet.

```
## /wm:clean-up report
Date: {YYYY-MM-DD}

### Projects ({N})
| Project | Work type | State | Last session |
|---|---|---|---|
| {name} | {type} | {state} | {date} |
...
(none) if empty

### Scratch files ({N})
| File | Last modified |
|---|---|
| {path} | {date} |
...
(none) if empty
```

Then ask: "Proceed with clean-up? Y/N"

If N → stop. Print "Clean-up cancelled."
If Y → continue to Step 3.
</step>

<step name="Step 3 — Handle projects">
For each project found in `projects/` (excluding `archive/`), in order:

**3a. Agent pre-scan:** Read `projects/{name}/STATE.md`, `projects/{name}/DECISIONS.md`, `projects/{name}/handoff.md`.
Form a judgment:
- "Looks done" — if STATE.md or handoff.md indicates all steps completed, or DECISIONS.md entries all have `Status: done`
- "Looks abandoned" — if handoff.md has open blockers and no recent progress, or STATE.md shows it was stuck
- "In progress" — state is executing, planned, or discovery-complete with recent activity
- "Unclear" — anything else

**3b. Present to user:**
Summarize the project — name, current state, last session date, your assessment (looks done, looks abandoned, in progress, or unclear), and a one-sentence reason. Then ask the user to pick one of four actions: archive as done, archive as abandoned, keep in place, or explain (investigate further and report before deciding). Presentation follows communication rules. Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md

**3c. Execute:** Follow [#Editing Rules](rules/editing-rules.md#editing-rules) from rules/editing-rules.md
- Done: `mv projects/{name}/ projects/archive/{name}/` then remove row from `projects/ACTIVE.md`
- Abandoned: `mv projects/{name}/ projects/archive/{name}-abandoned/` then remove row from `projects/ACTIVE.md`
- Keep: do nothing
- Explain: Read STATE.md, DECISIONS.md, handoff.md, and any plan files. Report:
  1. What the project is about (1-2 sentences)
  2. Whether the current state label is accurate
  3. For each DECISIONS.md entry: is it implemented? (check the target files)
  Then re-present the done/abandoned/keep prompt and wait for user response.

Move to next project.
</step>

<step name="Step 4 — Handle aged scratch files">
If no aged scratch files: print "No aged scratch files." Skip this step.

Show the aged scratch file list again. For each file, name the path and its age in days, then ask the user to pick one of four actions: promote (move to another folder), delete permanently, keep in scratch, or explain (show contents summary before deciding). Presentation follows communication rules. Wait for user response per file — Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md

**Promote:** Infer a default target path from the file/folder name (e.g. `scratch/research-X/` → `docs/research/X/`, `scratch/foo.md` → `docs/foo.md`). Propose the target path and ask the user to confirm or name an alternative. Then `mv {file} {target}`.
**Delete:** `rm {file}`
**Keep:** do nothing
**Explain:** Read the file, summarize in 2-3 sentences (what it is, whether it looks useful or stale). Then re-present the promote/delete/keep prompt.

After all files handled, print "Scratch clean-up done."
</step>

<step name="Step 5 — Summary">
Print a summary of all actions taken:

```
## Clean-up complete
Projects archived: {N} ({names})
Projects skipped: {N}
Scratch files promoted: {N}
Scratch files deleted: {N}
Scratch files kept: {N}
```
</step>
</process>
