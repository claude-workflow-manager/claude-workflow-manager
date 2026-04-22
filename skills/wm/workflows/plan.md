<purpose>
Enter the planning stage for the active project. Classifies tier, enforces gates, handles archive and version bump, then generates a native plan scaled to the tier.
</purpose>

<required_reading>
@~/.claude/rules/execution-rules.md
@~/.claude/rules/editing-rules.md
@~/.claude/rules/communication-rules.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/gate-matrix.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/templates.md
</required_reading>

<process>
<step name="Step 1 — Load project state">
Read `projects/{name}/STATE.md` and `projects/{name}/DECISIONS.md`.
</step>

<step name="Step 2 — Gate: DECISIONS.md has entries">
Check for at least one entry block (lines starting with `### `).

If none: "No decisions found. Run `/wm:discover` first." STOP.
</step>

<step name="Step 3 — Classify tier">
Read `~/.claude/skills/wm/references/gate-matrix.md` for default tiers and upgrade rules.

**3a. Apply default tier** from work type:
- fix, test → T0
- next-version, new → T1
- skill, new-agent, app → T2

**3b. Check upgrade triggers** based on DECISIONS.md entries:
- Touches >3 files → upgrade T0→T1 or T1→T2
- Touches public API, data model, or migration → upgrade to T2
- Cross-module changes → upgrade to T2
- Architectural ambiguity → upgrade to T2

**3c. Announce tier in plain language:**

Tell the user what the tier means for their workflow — don't use tier codes (T0/T1/T2) in messages. Convey the key idea naturally based on context:

- T0 → small enough to skip planning, execute directly. STOP.
- T1 → needs a checklist plan, can execute right after without formal review
- T2 → needs a detailed plan that gets verified before building starts

If upgraded from default, explain what triggered it (e.g. many files, cross-module changes). Keep it brief — one sentence, not a paragraph.
</step>

<step name="Step 4 — Archive gate (FIN-017 — agent context only)">
Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md

Read `~/.claude/skills/wm/references/gate-matrix.md`.

**Trigger:** the archive gate fires when `cwd/agent.md` exists — that file marks a Markdown-Agents agent directory, the only context where archive semantics apply. For every other cwd (WM dev repo, plain codebase, mixed repo, etc.), skip this gate silently — the gate does nothing even if the project's work type is `next-version` or `skill`.

If `cwd/agent.md` does NOT exist → skip Step 4 entirely and continue to Step 5.

If `cwd/agent.md` exists:
1. Read DECISIONS.md header for target skill/agent name and current version
2. Check for archive folder: `docs/archive/{target}-v{version}/`
3. Check git log for archive commit

If not met (soft gate): ask the user whether to archive now (recommended — gives clean rollback and comparison against the new version) or skip archiving for this cycle. If the user approves archiving, copy `{target}/` to `docs/archive/{target}-v{current}/` and commit. Presentation follows communication rules.
</step>

<step name="Step 5 — Version source + target (FIN-009a — read-only, no writes)">
`plan.md` no longer writes versions. Per FIN-009a, all version-write capability moved to `release.md` Step 2 — `release.md` reads `Version source:` and `Target version:` from DECISIONS.md and writes the new value back to the source file.

`plan.md`'s job in this step is **read-only**: establish the source and target in DECISIONS.md so release can act on them later. No bytes are written to any version file from this workflow.

For work types `next-version` and `skill` (skip for all others):

If `Target version:` in DECISIONS.md is still `TBD`:

**5a. Detect version source (read-only):**
Look for known version files in the target directory, in order:
1. `VERSION` — plain text, single line (e.g., `1.0`)
2. `package.json` — read `"version"` field
3. `PROJECT.md` — look for version in header
4. `pyproject.toml` — read `[project] version`

**5b. If found:** Record the source path in DECISIONS.md header:
```
Version source: {path to version file}
```

**5c. If not found:** Ask the user to choose one of: create a VERSION file (recommended for skills and commands), point at an existing file that holds the version, or skip versioning for this project. Wait for their choice. If they choose to create or point at a file, record the source. **If they choose to create a VERSION file, create it as part of discovery scaffolding — not as a version write.** The initial file contents come from the current reality (e.g., `1.0` for a new skill), not from any release target. Presentation follows communication rules.

**5d. Propose target version (record only):**
Based on scope of DECISIONS.md entries, propose major/minor/patch. Wait for confirmation. Update **only** `Target version:` in DECISIONS.md header. The target value sits there until release reads it and writes the final version to the source file.

**Hard rule:** this step must not modify the file at `Version source:`. Any attempt to do so is an FIN-009a regression.
</step>

<step name="Step 6 — Generate plan">
Follow [#Editing Rules](rules/editing-rules.md#editing-rules) from rules/editing-rules.md

Read `~/.claude/skills/wm/references/templates.md` for plan templates.

**6a. Investigation artifact (FIN-003 — write before writing the plan):**

Before writing a single plan step, produce an investigation file at `projects/{name}/plans/{YYYY-MM-DD}-{topic}-investigation.md`. This file is the source of truth for every file path the plan names — `verify-plan` Check 4 later cross-references plan paths against this file and auto-fails any path not present.

**Availability probe — MANDATORY before you dispatch any graph query, and MANDATORY before you decide the graph is "unavailable".** Run exactly one probe via Skill: `/wm:doc-graph ls .` — this lists files under the current working directory that the graph knows about. Interpret the result deterministically (no judgment calls):

- **Exit 0 and non-empty output** → graph is available. Proceed with the dispatch bullets below. Do not go to the degraded path.
- **Exit non-zero OR empty output** → graph is unavailable. Go straight to the degraded path (last paragraph of this step). Do not attempt the per-file queries.

**You may not skip the probe** and decide availability by inference, session context, or memory of earlier failures. The probe is cheap and deterministic; an inferred "unavailable" is a silent degradation that loses verify-plan Check 4 coverage.

Collect the project's scope from DECISIONS.md (target paths mentioned in FIN entries + design doc file references). If the probe succeeded, for each in-scope file, dispatch the following via Skill (`/wm:doc-graph` — never raw `python -m`, FIN-018c):

1. `/wm:doc-graph refs --out <file>` — what this file references
2. `/wm:doc-graph refs --in <file>` — what references this file (back-references)
3. `/wm:doc-graph outline <file>` — headers and signals
4. `/wm:doc-graph ls <scope-dir>` — what other files live nearby

Write the investigation file with one section per in-scope file, each section containing the outline, forward refs, and back refs. Include a "Candidate paths" section at the bottom listing every file path the plan might touch (drawn from refs_out + ls results) — the planner uses this list to avoid naming files that don't exist.

**Line numbers — always via `grep -n`, never counted visually.** When the investigation file lists line numbers for specific strings (edit hotspots, occurrence tables, carve-outs), every line number must come from an actual `grep -n` / `rg -n` command output, not from counting lines in a `Read` result. Visual counting silently skips blank lines and off-by-ones on multi-line content, producing an investigation file that misleads downstream plan steps. If a line number appears in this file, it must be grep-derived.

If `/wm:doc-graph` is unavailable (tool not deployed / not a markdown-heavy repo), write a minimal investigation file that lists the scope files manually via `Read` + `Glob` and notes the degradation at the top. Do not hard-fail planning on missing graph. The grep-for-line-numbers rule above still applies in the degraded path.

**6b. Read design doc + DECISIONS via Haiku subagent (FIN-009b):**

Do not read the full design doc + all DECISIONS entries in the main thread — for any project past the third FIN this blows through context budget with content the main thread mostly doesn't need verbatim.

Dispatch a **Haiku discovery subagent** (`model: haiku`) that reads `projects/{name}/DECISIONS.md` and `projects/{name}/plans/{YYYY-MM-DD}-{topic}-design.md` (if it exists) and returns a structured summary of ~1K tokens:

```
## DECISIONS summary
FIN-NNN | one-line title | done-when summary | touches: {files}
FIN-NNN | ...

## Design doc summary
- Key architectural decisions: {bullets}
- Non-goals: {bullets}
- Constraints the plan must honor: {bullets}

## Coverage gaps
- Any FIN whose done-when is not obviously actionable from the design doc
```

The main thread uses this summary to structure the plan. If the planner needs the full text of a specific FIN or a specific design-doc section, it expands on demand via targeted line-range reads.

**6b-skill. Skill structural reference (work type `skill` only):**

When work type is `skill`, read `~/.claude/skills/wm/references/skill-building-guidelines.md` before writing the plan. Use it to inform structural plan decisions: SKILL.md hub budget (30–50 lines), hub-spoke split criteria, description field wording, Gotchas section approach, and script/library placement (`lib/`, `assets/`). The guidelines inform — they do not dictate structure. Adapt based on the project's actual scope.

**6c. Write the plan:**

**T1 (Checklist):**
1. Iterate the Haiku subagent's DECISIONS summary
2. For each entry, generate 1-3 checkbox steps with: what to do, file paths (drawn from the investigation file's candidate paths), verify command
3. Order steps logically (dependencies first)
4. Write plan to `projects/{name}/plans/{YYYY-MM-DD}-{topic}-plan.md` using T1 template
5. Total: 5-15 checkboxes

**T2 (Plan-Verified):**
1. Iterate the Haiku subagent's DECISIONS summary + design summary
2. Break work into ordered steps with: wave assignment, file paths (only paths from the investigation file's candidate list), edit intent, verify commands, done-when criteria
3. Assign waves: independent steps share a wave, dependent steps get later waves
4. For high-risk steps, add `Review: true` to trigger reviewer subagent during execution. Per `reviewer-config.md`, `Review:` defaults to `true` for T2 project steps (FIN-010c) — mark `Review: false` explicitly with a logged reason when opting out.
5. Write plan to `projects/{name}/plans/{YYYY-MM-DD}-{topic}-plan.md` using T2 template
6. Add machine-readable metadata block at end

**Plan quality rules:**
- Every step must name specific files **from the investigation file's candidate list** (no "update relevant files", no guessed paths)
- Every step must have a verify command (no "check that it works")
- Edit intent describes WHAT changes, not HOW (no literal code in plans)
- Steps should be atomic — one logical change per step
- No step should produce a diff exceeding ~200 lines (soft cap; explicit exceptions allowed with a diff-size note per plan step)
</step>

<step name="Step 7 — Update state">
Update `projects/{name}/STATE.md`:
- `Current state: planned`
- Update `Last session` with date and summary
</step>

<step name="Step 8 — Route based on tier">
**T1:** Plan saved. Let the user know they can execute directly — no formal verification needed. Mention `/wm:execute` and `/wm:save`.

**T2:** Plan saved. Let the user know the plan needs verification before execution. Mention `/wm:verify-plan` and `/wm:save`.

Do NOT auto-advance or propose execution for T2.
</step>
</process>
