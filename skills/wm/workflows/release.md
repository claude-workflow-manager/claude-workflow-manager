<purpose>
Run release steps for the active project. Handles work-type-specific release actions and project archiving.
</purpose>

<required_reading>
@~/.claude/rules/execution-rules.md
@~/.claude/rules/communication-rules.md
@~/.claude/rules/editing-rules.md
@~/.claude/rules/review-rules.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/gate-matrix.md
</required_reading>

<process>
<step name="Step 1 — Gate: awaiting-release">
Read `projects/{name}/STATE.md`.

If state is not `awaiting-release`: "Not ready to release. Run `/wm:verify` first." STOP.
</step>

<step name="Step 2 — Sanitization gate (FIN-002)">
Run `bash scripts/sanitize.sh` from the repo root.

- Exit 0: proceed to next step.
- Non-zero exit: print the script's findings, STOP the workflow. Do not continue to any deploy, archive, version-bump, or publish step.

The gate applies regardless of whether `--publish` is requested — even internal-only releases must pass sanitization, since the dev repo is the source of truth and leaks compound over time. (Public push is opt-in via the `--publish` flag; see Step 7.)

If `scripts/sanitize.sh` is absent (pre-packaging era repo), print a one-line warning and skip the gate. This preserves backward compatibility for projects that pre-date FIN-002.
</step>

<step name="Step 3 — Work type dispatch">
Read `projects/{name}/DECISIONS.md` for work type and target version.

#### next-version
1. **Promote decisions (FIN-016):** for each DECISIONS.md entry with `Status: verified`, update to `Status: applied`. The new status flow is `pending → done → verified → applied` — release is the terminal promotion, not the first.

   **Stale-FIN warning:** for any FIN still at `Status: pending` or `Status: done` at release time, print a per-FIN warning: *"FIN-XXX is still {status} — execution or verification may be incomplete. Fix before releasing."* Require explicit user acknowledgment per stale FIN before proceeding. Log each acknowledgment (including FIN ID, status, and user's decision) in the release report so the decision is auditable.

2. Update DESIGN-DECISIONS.md in the target directory — append applied entries.
3. **Version bump (FIN-009a):** absorb the version-write capability that Step 4.1 removed from `plan.md`. Read the `Version source:` field from the DECISIONS.md header — that gives the repo-relative path to the file that stores the current version. Read the current version from that source file. Read the `Target version:` field from the DECISIONS.md header — that is the new value. Write the new value back to the source file at the location the current value occupied (e.g., `VERSION` file contents, or the `version: X.Y.Z` line in a SKILL.md header). This is the ONLY place in the v2.1 codebase that writes a version string — `plan.md` no longer touches versions.
4. Update CHANGELOG.md — add version entry with summary of changes.
5. Commit: `release: {target} v{version} — {summary}`

#### fix
1. Bump patch version in target files
2. One-line CHANGELOG entry
3. Commit: `fix: {target} v{version} — {summary}`

#### skill
1. **Version bump (FIN-009a):** same mechanism as next-version above — read `Version source:` + `Target version:` from DECISIONS.md header, write new value back to the source file.
2. Update CHANGELOG.md — add version entry.
3. **Promote decisions (FIN-016):** mark DECISIONS.md entries at `Status: verified` as `Status: applied`. Stale-FIN warnings apply identically to the next-version flow above.
4. Commit: `release: {target} v{version} — {summary}`

#### new-agent
1. Set version 1.0 in target files
2. Create initial CHANGELOG.md
3. Commit: `feat: {target} v1.0 — initial release`
</step>

<step name="Step 4 — Pre-deploy verification">
Follow [#Review Rules](rules/review-rules.md#review-rules) from rules/review-rules.md

Before deploying, verify all DECISIONS.md entries have `Status: applied`.
If any are still `pending` or `done` or `verified` (i.e. not yet `applied`): "Not all decisions applied: [list]. Fix before releasing." STOP.

**Pre-deploy graph check (FIN-004):** dispatch `/wm:doc-graph check` via Skill. This runs a repo-wide broken-reference scan — every `refs_out` entry in the graph is resolved against the filesystem. If any reference is broken, the check verb exits non-zero and prints the list of broken refs.

**Hard gate:** if `/wm:doc-graph check` fails, STOP the release with *"Pre-deploy reference check failed — broken references must be fixed before deploying."* and print the broken-ref list. Do not advance to Step 5. The release only deploys when the reference graph is fully resolvable — a broken reference shipped to production would cause every downstream workflow using `refs` / `impact` / `outline` on that file to hit a missing-target error.

**Archive subtrees are excluded by default.** `check` skips any path whose parent directories contain a segment named `archive/` — these subtrees are frozen historical state, so broken refs inside them are expected, not regressions. If a release genuinely needs whole-repo scanning (e.g., verifying an archive's internal consistency), dispatch `/wm:doc-graph check --include-archives` manually and review the output; do not waive this gate on archive-originating noise.

If `/wm:doc-graph` itself is unavailable (tool not deployed — this would be the first-ever release that ships it), print a one-line note that the check was skipped and continue. After the first v2.1 release, subsequent releases can rely on the check being available.

**Rule-reminder staleness check (FIN-003) — warn-only in v1.1.0.** Dispatch `/wm:doc-graph check-rule-reminders` via Skill alongside the broken-reference check above. The verb parses every FIN-002 canonical-form reminder in `skills/wm/workflows/*.md` and flags any workflow file whose last-modified time is older than the rule file it cites. In v1.1.0, the verb runs in warn-only mode: staleness output appears in the release log but does not block. After one release cycle with no false-positive noise, flip the verb to hard-block mode (see the final `exit 0` → `exit 1` switch documented inline in `doc-graph.md` Step 5). Until that flip, **do not treat a non-zero exit from `check-rule-reminders` as a release blocker** — only the `check` verb blocks.
</step>

<step name="Step 5 — Deploy dev → production">
Follow [#Editing Rules](rules/editing-rules.md#editing-rules) from rules/editing-rules.md

Dev repo is the source of truth. Production (`~/.claude/`) is a deployment target.

**4a. Commands and skills:**
1. `{dev}/commands/wm/` → `~/.claude/commands/wm/` (all `.md` files)
2. `{dev}/skills/wm/` → `~/.claude/skills/wm/` (full subtree except `archive/`)

**4b. Scoped agent rules:**
3. `{dev}/rules/*.md` → `~/.claude/rules/`
   - Create `~/.claude/rules/` directory if missing.
   - Deploys: all `.md` files in `{dev}/rules/` — currently `communication-rules.md`, `discovery-rules.md`, `execution-rules.md`, `editing-rules.md`, `review-rules.md`, plus any additional rule files added later.

**4c. Hooks:**
4. `{dev}/hooks/*.py` → `~/.claude/hooks/` (all `.py` files)
   - Create `~/.claude/hooks/` directory if missing.
   - Deploys: `tool-gate.py`, `context-monitor.py`, `verification-output.py`, plus any additional hook scripts present in `{dev}/hooks/`.
   - **Does NOT touch** `~/.claude/hooks/inject-communication-rules.sh` — it is retained on disk for rollback per FIN-017 but is no longer registered in settings.json.
   - On POSIX, set executable bit after copy: `chmod +x ~/.claude/hooks/*.py`. Windows MSYS-bash handles this as a no-op.

**4d. settings.json — manual only:**
5. The release workflow **does NOT modify** `~/.claude/settings.json`.
   - Rationale: settings.json is user-specific (permissions, env vars, plugins, model config) and merging is error-prone.
   - Hook registrations are managed during development and should already be in place by the time release runs.
   - If a new hook needs a settings.json entry, add it manually during execution before release.

**4e. Verify production matches dev:**
6. `diff -rq {dev}/commands/wm/ ~/.claude/commands/wm/` — must be empty
7. `diff -rq {dev}/skills/wm/ ~/.claude/skills/wm/ --exclude=archive` — must be empty
8. For each file in `{dev}/rules/*.md`: `diff {dev}/rules/{file} ~/.claude/rules/{file}` — must be empty
9. For each file in `{dev}/hooks/*.py`: `diff {dev}/hooks/{file} ~/.claude/hooks/{file}` — must be empty

If any dev file is missing or differs in prod: the deploy failed — investigate and re-run Step 5.

Files that exist in prod but NOT in dev are allowed (prod-only rules, legacy hooks, user customizations). Release owns what it owns; it does not police the rest.

**Idempotency guarantee:** running Step 5 twice in succession must produce zero changes on the second run.
</step>

<step name="Step 6 — Archive project">
1. Move `projects/{name}/` → `projects/archive/{name}/`
2. Remove the project row from `projects/ACTIVE.md`
3. Commit: `chore: archive project — {name}`
</step>

<step name="Step 7 — Publish public snapshot (FIN-006) — opt-in via `--publish`">
Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md

Push a sanitized snapshot of the current working tree to the public GitHub repo. **Opt-in only** — this step runs only when the user explicitly passes `--publish`.

**Opt-in condition:** If `--publish` flag was NOT passed, log "Publish step skipped — internal release only. Pass --publish to push to the public GitHub repo." and exit this step cleanly. This is the default behavior for every `/wm:release` invocation — internal-only, nothing leaves the dev repo.

**Rationale (FIN-006 + maintainer preference):** Public visibility is a deliberate act, not a side effect of `release`. Most release invocations are internal iterations (version bumps, dev-to-production sync, archive projects). Public push is reserved for when the maintainer explicitly says "ship this outside." This mirrors how `npm publish`, `docker push`, and similar tools work.

**Dry-run conditions:** If `--dry-run` flag was passed, print every git / rsync / rm command that would run, prefix each with `[dry-run]`, and do NOT execute any of them.

**Prerequisites (re-check before proceeding):**

1. Sanitization gate (Step 2) must have passed earlier in this workflow invocation. If somehow skipped, abort here.
2. The `public` git remote must be configured. Run `git remote get-url public`. If absent, print setup instructions — "Run `git remote add public git@github.com:<org>/claude-workflow-manager.git`" — and exit with an error.
3. `.claude-plugin/plugin.json` must exist at the repo root.

**Manifest version sync (FIN-009a — release is sole writer):**

Before staging for public push, overwrite `.claude-plugin/plugin.json`'s `version` field with the value from `skills/wm/VERSION`. Read the current content of `plugin.json`, locate the `version` key, replace its value with the VERSION string, and write the file back. Preserve key order and formatting. This step ensures the published manifest version matches the canonical version source; no other workflow step writes version values.

**Publish flow — ephemeral staging:**

1. Create a temp dir: `STAGE=$(mktemp -d -t wm-publish.XXXXXX)` — record the path for cleanup or failure inspection.
2. Clone the public remote into the temp dir: `git clone "$(git remote get-url public)" "$STAGE"`.
3. Rsync the current working tree into the temp dir, respecting `.gitignore` and excluding project artifacts:

   ```
   rsync -a --delete \
     --exclude='.git/' \
     --exclude='projects/' \
     --exclude='scratch/' \
     --exclude='research/' \
     --exclude='memory/' \
     --exclude='skills/wm/archive/' \
     --exclude='**/__pycache__/' \
     "$REPO_ROOT/" "$STAGE/"
   ```

   The `--delete` flag removes files from the temp clone that no longer exist in the dev repo. This keeps the public repo lean and accurate.

4. Change into the temp dir, stage all changes, and commit:

   ```
   cd "$STAGE"
   git add -A
   git commit -m "release: v$NEW_VERSION — <changelog-summary>"
   ```

   The commit message uses the version string from `skills/wm/VERSION` and the top line of the CHANGELOG entry for the new version.

5. Push: `git push public main` (or the public repo's default branch if different — detect via `git remote show public | grep "HEAD branch"`).
6. Cleanup: return to repo root and remove the temp dir — `cd "$REPO_ROOT"; rm -rf "$STAGE"`.

**Failure handling:**

- If any step (clone, rsync, commit, push) fails, do NOT delete the temp dir — preserve it for user inspection. Print the temp dir path and a note explaining which step failed.
- If the push fails due to a non-fast-forward error, print the error and exit without cleanup. The user can resolve divergence manually and re-push from the preserved temp dir.

**Verification (after successful push):**

- Run `git ls-remote public main | awk '{print $1}'` — should match the HEAD commit hash of the temp dir before it was deleted.
- A fresh clone of the public repo should contain `.claude-plugin/plugin.json` with the new version.
- The public repo on GitHub should show the new commit. (Manual check recommended on the first few releases — not automated.)

**Done for this step when:** the public repo has a new commit matching the dev repo's sanitized snapshot, `plugin.json` version matches `skills/wm/VERSION`, and the temp dir has been cleaned up.
</step>

<step name="Step 8 — Confirm">
Print: "Released `{target}` v{version}. Project `{name}` archived. State: between-cycles."
</step>
</process>
