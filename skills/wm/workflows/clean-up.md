<purpose>
Tidy the wm workspace: archive stale projects, promote or remove aged scratch files. Always shows a dry-run report before making any changes.
</purpose>

<required_reading>
@~/.claude/rules/communication-rules.md
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
```
Project: {name} ({state}, last session {date})
Assessment: {looks done | looks abandoned | in progress | unclear}
Reason: {1-sentence justification}

Action?
  D) Done — archive as finished
  A) Abandoned — archive as abandoned
  K) Keep — leave in place
  E) Explain — investigate and report before deciding
```
Wait for user response — follow `rules/communication-rules.md`.

**3c. Execute:**
- D (done): `mv projects/{name}/ projects/archive/{name}/` then remove row from `projects/ACTIVE.md`
- A (abandoned): `mv projects/{name}/ projects/archive/{name}-abandoned/` then remove row from `projects/ACTIVE.md`
- K (keep): do nothing
- E (explain): Read STATE.md, DECISIONS.md, handoff.md, and any plan files. Report:
  1. What the project is about (1-2 sentences)
  2. Whether the current state label is accurate
  3. For each DECISIONS.md entry: is it implemented? (check the target files)
  Then re-present the D/A/K prompt and wait for user response.

Move to next project.
</step>

<step name="Step 4 — Handle aged scratch files">
If no aged scratch files: print "No aged scratch files." Skip this step.

Print the aged scratch file list again. For each file, ask:
```
File: {path} ({N days old})
  P) Promote — move to another folder
  X) Delete — remove permanently
  K) Keep — leave in scratch
  E) Explain — show file contents summary before deciding
```
Wait for user response per file — follow `rules/communication-rules.md`.

**Promote:** Infer a default target path from the file/folder name (e.g. `scratch/research-X/` → `docs/research/X/`, `scratch/foo.md` → `docs/foo.md`). Present: "Promote to: {suggested path} — confirm or enter alternative." Then `mv {file} {target}`.
**Delete:** `rm {file}`
**Keep:** do nothing
**Explain:** Read the file, summarize in 2-3 sentences (what it is, whether it looks useful or stale). Then re-present the P/X/K prompt.

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
