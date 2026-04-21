<purpose>
Create a new workflow project with full state tracking scaffold.
</purpose>

<required_reading>
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/templates.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/session-rename.md
</required_reading>

<process>
<step name="Step 1 — Ask what the user is building">
Ask: "What are you building or fixing?"

Wait for response.
</step>

<step name="Step 2 — Determine work type">
Based on the user's description, propose a work type:

- **next-version** — Feature or enhancement to an existing skill/agent
- **fix** — Bug fix, typo, small correction
- **skill** — New skill creation or major skill rewrite
- **new-agent** — Creating a new agent or project from scratch
- **new** — Building something new that doesn't fit other types (tool, plugin, utility)
- **test** — Testing, validation, experimentation on existing features
- **app** — Application or major feature (produces PRD + tech spec)

**Context-adaptive presentation:**

If the work type is obvious from the user's description → propose directly:
```
Work type: **{type}** — {description}. OK? (or pick different: A-next-version / B-fix / C-skill / D-new-agent / E-new / F-test / G-app)
```

If ambiguous or no clear match → show full list:
```
Work type options:
A) next-version — enhancement to existing work
B) fix — bug fix or small correction
C) skill — new skill or major rewrite (Reference material: `skills/wm/references/skill-building-guidelines.md` — read during discovery and planning for structural decisions.)
D) new-agent — creating a new agent from scratch
E) new — something else (tool, plugin, utility)
F) test — testing, validation, experimentation
G) app — application or major feature (PRD + tech spec)

I suggest: {letter}) {type}. Confirm? (A/B/C/D/E/F/G)
```

Wait for confirmation.

**Command+skill detection:** If the project involves building a tool with commands (`~/.claude/commands/`) and skill logic (`~/.claude/skills/`), read `~/.claude/skills/wm/references/command-structure.md` for the established pattern. Inform the user:

"This project follows the command+workflow pattern. Commands are thin triggers, logic lives in workflow files. I've loaded the structure reference."

This context carries into discovery and planning — the agent will use the command trigger and workflow file templates from `templates.md` when planning implementation.
</step>

<step name="Step 3 — Propose folder name">
Generate a folder name that describes **what you're doing in this cycle**. Don't repeat the repo/project name — it's already in the path. Prefix with today's date.

Format: `{YYYY-MM-DD}-{slug}`
Examples: `2026-03-31-initial-build`, `2026-03-31-api-integration`, `2026-03-20-gate-fix`

Present: "Project folder: `{name}`. OK? (Y or suggest alternative)"

Wait for confirmation.
</step>

<step name="Step 4 — Detect projects/ location">
Look for `projects/` in current directory or parent. If not found, create `projects/` in the current directory.
</step>

<step name="Step 4b — Ensure git repo">
Check if `.git/` exists in the project root. If not, run `git init` and create an initial empty commit:

```bash
git init && git commit --allow-empty -m "chore: initialize repository"
```
</step>

<step name="Step 5 — Create scaffold">
Read templates from `~/.claude/skills/wm/references/templates.md` and create:

1. `projects/{name}/STATE.md` — from STATE.md template, fill in work type and date
2. `projects/{name}/DECISIONS.md` — from DECISIONS.md template, fill in work type and date
   - **FIN-001 archive auto-seed is conditional.** Include FIN-001 (archive) entry automatically **only if** work type is `next-version` or `skill` **AND** an `agent.md` file exists in the project root. Rationale (FIN-017, templates.md): v2.1 scoped the archive gate to agent projects only — `/wm:plan` Step 4 already skips the archive gate silently when `agent.md` is absent. Seeding a FIN that will immediately be marked n/a in discovery adds noise to every non-agent project's ledger. If `agent.md` is absent, do not seed FIN-001 — discovery can add an archive FIN later if the project actually has something to archive.
3. `projects/{name}/plans/` — create directory
4. `projects/{name}/handoff.md` — from handoff.md template
5. `projects/ACTIVE.md` — create if missing (from template), or append a new row
6. `AGENTS.md` — create from template **only if it does not exist** in project root
7. `.gitignore` — create from template **only if it does not exist** in project root
8. `scratch/` — create directory **only if it does not exist** in project root (already gitignored)
9. `docs/` — create directory **only if it does not exist** in project root
</step>

<step name="Step 6 — Commit non-ignored files">
Only commit files that are NOT gitignored. `projects/` and `.claude/` are typically gitignored.

```bash
git add AGENTS.md .gitignore docs/.gitkeep 2>/dev/null
git commit -m "chore: create project scaffold — {name}" 2>/dev/null || true
```

If nothing to commit (all files gitignored), skip silently.
</step>

<step name="Step 7 — Rename session">
Read `~/.claude/skills/wm/references/session-rename.md` and run the bash snippet with the project's folder name as `PROJECT_SLUG`.
</step>

<step name="Step 8 — Route to discover">
Print the one-liner route message:

"Project `{name}` created. Run `/wm:discover` to start discovery, or `/wm:next` to advance."

No permission-related output. Write/Edit permissions for `./projects|scratch|docs|research/**` are granted by the user's global `~/.claude/settings.json` — there is no per-project `settings.local.json` to create, nothing to restart.
</step>
</process>
