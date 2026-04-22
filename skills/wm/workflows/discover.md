<purpose>
Enter discovery stage for the active project. Two-phase unified discovery flow: open conversation as thinking partner, then structured gray areas exploration.
</purpose>

<required_reading>
@~/.claude/rules/discovery-rules.md
@~/.claude/rules/communication-rules.md
@~/.claude/rules/editing-rules.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/impact-scan.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/prd-guidelines.md (if PRD needed)
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/tech-spec-guidelines.md (if tech spec needed)
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/skill-building-guidelines.md (if work type is skill)
</required_reading>

<process>
<step name="Step 1 — Load context">
Find the active project → read `projects/{name}/STATE.md`, `projects/{name}/DECISIONS.md`, and `AGENTS.md`. For large files, use line-range reads — navigate structurally first (grep/glob), then read targeted sections.

If DECISIONS.md already has entries (lines starting with `### `), list them.

If codebase detected without description (no README, AGENTS.md, or PROJECT.md describing it): ask the user whether to review the existing code first (recommended — gives you grounding) or start fresh with the user describing the project. Presentation follows communication rules.

**Sub-step 1b — Cross-project overlap scan (FIN-004 — new projects only):**

If this invocation is starting a fresh discovery (not resuming mid-project), check whether any other active project already touches this project's scope. This is the canonical overlap detector — it supersedes the deferred `discover-overlap-scan` project.

1. Read `projects/ACTIVE.md` to enumerate active projects.
2. Collect a small set of scope tokens for this project: the `Target:` line from `projects/{name}/STATE.md` (split into file paths if it lists multiple), plus the primary keywords from the user's opening description. Prefer file paths over keywords when both are available — graph impact queries match precisely on file paths.
3. Dispatch `/wm:doc-graph impact <scope-tokens>` via Skill (not via raw `Bash` / `python -m` — the Python invocation lives only in `doc-graph.md` per FIN-018c). Use `--mode=light` for this overlap check.
4. Summarize the result in 5–15 lines:
   - **No FIN affected in other projects and no shared file mentions** → report "no overlap — clean" and continue to Step 2.
   - **Overlap found** → list each other project that the impact scan flagged, the shared files, and any FIN IDs from that project whose bodies mention the same paths. Ask the user: (A) abandon this project and contribute to the overlapping one, (B) narrow this project's scope to avoid the conflict, (C) proceed deliberately — log the overlap as a FIN in this project's `DECISIONS.md` so it is visible during verification.

If `/wm:doc-graph` is unavailable (tool not deployed / MCP not registered / `cwd` is not a markdown-heavy repo), print one line noting the check was skipped and continue — do not hard-fail discovery on a missing tool.

**Sub-step 1c — Graph-structured context load (FIN-006):**

Before Phase 1 opens, run graph queries to surface structural relationships (`<required_reading>` includes, back-references, header-anchor citations) that grep alone misses. This is the discovery-phase companion to `change.md`'s Step 2 graph triage.

1. Derive 2–5 keywords from the project's `Target:` line (in `projects/{name}/STATE.md`) and the user's opening description. Prefer multi-word phrases and concrete nouns over generic terms.
2. Dispatch `/wm:doc-graph search <keyword>` via Skill for each keyword. No direct `python -m wm_doc_graph` calls — dispatch routes through `doc-graph.md` per FIN-018c.
3. For any concrete file paths named by the user in the opening description, dispatch `/wm:doc-graph refs <path> --in` via Skill to surface back-references.
4. Summarize results in 5–15 lines: top hits per query, any unexpected cross-file relationships, structural anomalies worth flagging (empty `<required_reading>` blocks, inline citations without includes, dangling references). Note anything that looks like a pre-existing bug — same pattern that produced `verify.md`/`verify-plan.md`'s inline-without-include bug during this feature's own discovery.

**Code-heavy project extension.** `/wm:doc-graph` indexes only `.md` files. If the current working directory is a code-heavy repo — detected via presence of any of `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `tsconfig.json`, `pom.xml`, `build.gradle`, `Gemfile`, `composer.json`, `mix.exs`, `Makefile`, `CMakeLists.txt` (the same detection list `code-graph.md` uses) — AND the `code-review-graph` MCP server is available (probe via `mcp__code-review-graph__*` tool visibility), also dispatch equivalent `/wm:code-graph` queries in parallel. Same non-blocking posture: if the MCP is not registered, skip with a one-line note and continue with doc-graph only.

If `/wm:doc-graph` is unavailable, print a one-line skip note and continue — matches Sub-step 1b's non-blocking fallback.

**Sub-step 1d — Contract-file pre-load (FIN-007):**

Follow [#Discovery Rules](rules/discovery-rules.md#discovery-rules) from rules/discovery-rules.md

Before Phase 1 opens, pre-load the project's own contract files so Phase 2 option-generation does not invent alternatives for questions the project's contracts already answer. This is the companion to Rule 9 in `rules/discovery-rules.md` — the rule carries the *why*, this sub-step carries the *how*.

1. **Default globs.** Collect markdown files matching `references/**/*.md`, `rules/**/*.md`, and `docs/**/*.md` from the project's cwd.
2. **Project-specific override.** If cwd `AGENTS.md` has a `## Contract files` section listing explicit paths or globs, those **supplement** (not replace) the defaults.
3. **Pre-load strategy.** Read each matched file's content into context before Phase 1 opens. Files ≤200 lines load in full; larger files load headers (`grep -n "^#" {file}`) plus the first 100 lines — enough to surface the shape and the first substantive content.
4. **Non-blocking fallback.** If no contract files are detected, print "no contract files detected — proceeding with standard discovery" and continue. Matches Sub-step 1b / 1c fallback posture.

Contract files outrank any option set the agent later generates. When Phase 2 would present alternatives, first check whether a loaded contract file already mandates the answer — if so, report what the contract says rather than presenting options.
</step>

<step name="Step 2 — Phase 1: Open conversation">
Act as a **thinking partner**, not an interviewer.

Follow [#Discovery Rules](rules/discovery-rules.md#discovery-rules) from rules/discovery-rules.md

**How to conduct Phase 1:**
- **One question at a time.** Ask one question per message. Wait for response before asking the next. This lets the user think and add context naturally.
- Ask open questions about purpose, constraints, success criteria
- Challenge assumptions, propose alternatives, ask "what if..."
- Scale depth to work type and complexity (test/fix = 2-3 questions, skill/app = 10+)
- For work type `app`: naturally ask about purpose, target users, success criteria, scope boundaries (feeds PRD)
- For work type `skill`: load `~/.claude/skills/wm/references/skill-building-guidelines.md` and use it to frame questions — hub budget, hub-spoke split, description wording, gotchas plan, script placement
- Agent decides when enough info gathered to move to Phase 2

**Immediate save rule:** When the user confirms a decision during conversation (explicit "yes", "go with X", "agreed"), immediately append a FIN entry to `projects/{name}/DECISIONS.md`. Use the standard format (Decision, Rationale, Implementation, Done-when, Status: pending). This prevents decision loss if the session ends unexpectedly.
</step>

<step name="Step 3 — Phase 2: Gray areas">
Switch to **structured mode**. Analyze the conversation so far and generate 3-5 **domain-specific** gray areas (not generic categories like "UI/UX/Behavior").

**Domain heuristics — gray areas depend on what's being built:**
- Something users SEE → layout, density, interactions, states
- Something users CALL → responses, errors, auth, versioning
- Something users RUN → output format, flags, modes, error handling
- Something users READ → structure, tone, depth, flow
- Something being ORGANIZED → criteria, grouping, naming, exceptions

**Present the map of gray areas.** User selects which to discuss.

**For each selected area:**
- **One question at a time.** Ask one question per message. Wait for response before asking the next. This lets the user think and add context naturally.
- Natural flow of questions with options, tradeoffs, and recommendation
- Agent decides when topic is exhausted, moves to next
- User can say "this is for later" → record in DECISIONS.md with status: deferred
- For work type `app`: include technical gray areas that feed into tech spec (stack choices, data model, API shape)
- For work type `skill`: include structural gray areas drawn from `skill-building-guidelines.md` — hub vs spoke split, description wording, gotchas budget, lib placement
- **Immediate save rule applies here too** — save each confirmed decision to DECISIONS.md as it's confirmed

Agent decides when all areas are sufficiently covered.
</step>

<step name="Step 4 — Write artifacts">
Follow [#Editing Rules](rules/editing-rules.md#editing-rules) from rules/editing-rules.md

After discovery conversation, assess which artifacts would benefit this project:

**Artifact guidance (not strict rules):**

- **PRD** — Propose when the project has user-facing behavior, a clear problem to solve, or scope that needs bounding. Common for: `app`, `new`, `new-agent`. Less common for: `fix`, `test`, `next-version`.
- **Tech spec** — Propose when there are non-trivial architectural decisions, integrations, or data models. Common for: `app`. Occasionally useful for: `new`, `new-agent`.
- **Design doc** — Always write. Scale to complexity (few paragraphs for a fix, full design for a new skill).

**How to propose:**
For PRD and tech spec, name your recommendation with reasoning and ask the user to confirm or decline. Phrasing follows communication rules — keep it tight, do not impose a canned shape.

If user confirms PRD:
1. Read `~/.claude/skills/wm/references/prd-guidelines.md`
2. Write PRD → `docs/prd-{feature}.md`

If user confirms tech spec:
1. Read `~/.claude/skills/wm/references/tech-spec-guidelines.md`
2. Write tech spec → `docs/tech-spec-{feature}.md`

Always write design doc:
1. Write design doc → `projects/{name}/plans/YYYY-MM-DD-{topic}-design.md`

**Don't dump artifacts into chat.** Write the file, announce the path and a 1-2 line summary. User can read the file if they want details.

Write the complete file, announce the path, then ask for review.
</step>

<step name="Step 5 — Review DECISIONS.md entries">
By this point, decisions have already been saved incrementally during Phase 1 and Phase 2 (immediate save rule). This step reviews and cleans up:

1. Read `projects/{name}/DECISIONS.md` — list all entries
2. Check each entry for completeness (Decision, Rationale, Implementation, Done-when, Status)
3. Fix any entries with missing fields
4. Check for duplicates or contradictions between entries
5. Verify FIN numbering is sequential

**Sub-step 5b — Light impact scan per FIN:**

For each FIN entry, run an **impact-scan in light mode** (see `references/impact-scan.md`). Check:
- Conflict with other FIN entries in this project's DECISIONS.md
- Conflict with FIN entries in other active projects (read `projects/ACTIVE.md` to enumerate)
- Whether the FIN touches files already covered by another FIN

Present a brief conflict report:
```
## FIN-XXX impact (light)
- Same-project conflicts: {none | list}
- Cross-project conflicts: {none | list}
- File overlap with existing FIN: {none | list}
Verdict: clean | review needed | conflict
```

If verdict is `review needed` or `conflict`, ask the user to revise, accept, or defer. Do not silently continue.
</step>

<step name="Step 6 — Do NOT auto-advance">
Do NOT call `/wm:next` automatically. Print:

"Discovery complete. Run `/wm:next` to advance to planning, or `/wm:save` to resume later."
</step>
</process>
