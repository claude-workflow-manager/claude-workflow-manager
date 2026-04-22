<purpose>
Run implementation verification after execution. Applies the native verification ladder based on project tier. Checks done-when criteria from DECISIONS.md against actual files and behavior.
</purpose>

<required_reading>
@~/.claude/rules/review-rules.md
@~/.claude/rules/discovery-rules.md
@~/.claude/rules/communication-rules.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/gate-matrix.md
</required_reading>

<process>
<step name="Step 1 — Load project state (FIN-009e — progressive disclosure)">
Read **only what Step 2's gate needs** — do not front-load the full DECISIONS.md body into the main context:

1. `projects/{name}/STATE.md` — header + current state line only (line-range read, not whole file).
2. `projects/{name}/DECISIONS.md` — header block and the **index** of FIN IDs + titles. Use `grep -n '^### FIN-' DECISIONS.md` or an equivalent line-range read to produce the index. Do **not** read the full body of every FIN — Step 4 reads each `Done-when` line-range on demand per check.
3. `projects/{name}/plans/` — directory listing only, to determine tier from the plan file header (single-line read of the `Tier:` field).

This progressive disclosure keeps the main context under ~2K tokens at verification start. Step 4 expands to per-FIN done-when text only when that check runs — no earlier.
</step>

<step name="Step 2 — Gate: execution appears complete">
State must be `executing` and plan tasks should appear complete (check git log for task commits).

If state is not `executing`: "Not ready for verification. Current state: `{state}`." STOP.
</step>

<step name="Step 3 — Run verification ladder">
Follow [#Review Rules](rules/review-rules.md#review-rules) from rules/review-rules.md

Read `~/.claude/skills/wm/references/gate-matrix.md` for verification levels per tier.

**Scratch output rule (FIN-009d):** each ladder level writes its **raw** output to its own scratch file at `scratch/{YYYY-MM-DD}-{topic}-ladder-L{N}.md`. The chat surface shows **pass/fail + failure excerpts only** — ≤500 tokens per level. Long test logs, lint reports, and reviewer findings never blow up the main report; reviewers click into the scratch file for full detail.

Apply verification levels appropriate to the tier:

**Level 1 — Static checks (all tiers):**
Run available static analysis: lint, typecheck, formatting checks. Write full output to `scratch/{date}-{topic}-ladder-L1.md`. Show command + one-line pass/fail + (on failure) first 5-10 error lines in chat.

**Level 2 — Targeted tests (all tiers):**
Identify tests related to changed modules/files. Write full test output to `scratch/{date}-{topic}-ladder-L2.md`. Show command + one-line pass/fail + failure excerpts only in chat.

**Level 3 — Regression suite (T1, T2):**
Run broader test suite beyond just changed modules. Write full output to `scratch/{date}-{topic}-ladder-L3.md`. Chat shows the summary line + failure excerpts. If no test suite exists: note "No regression suite available — skipping L3."

**Level 4 — Runtime smoke (T2 only):**
If applicable: run the application/tool and validate key behavior path. Write commands, observed output, and behavioral assertions to `scratch/{date}-{topic}-ladder-L4.md`. Chat shows the assertion list with pass/fail. If not applicable (e.g., config files, documentation): note "No runtime smoke applicable — skipping L4."

**Level 5 — Reviewer subagent (FIN-010b + FIN-010c — T2 default-on):**

**Trigger (FIN-010c — default-on for T2):** For T2 projects, L5 runs for every plan step **unless** that step is explicitly marked `Review: false` with a logged reason. The opt-out reason is logged to `scratch/{date}-{topic}-ladder-L5.md` under a "Skipped steps" section. T1 projects still treat L5 as opt-in (`Review: true` required).

<!-- plugin-root-fallback -->
**Model pinning:** Read `@~/.claude/skills/wm/references/reviewer-config.md` for the default reviewer model. Do not hard-code a model name here — `reviewer-config.md` is the single source of truth so model pins can be updated in one place.

**Dispatch (FIN-010b — artifact-only input contract):** Spawn a read-only subagent with the pinned model. The subagent's input is **strictly** the three artifacts below — no primary-agent narrative, no explanation of what was done, no hints about which criteria matter. The reviewer must judge from artifacts alone to break inter-agent sycophancy.

Input contract:
1. **Diff** — `git diff` output for the step's changes (specific commit or file range)
2. **Test/lint output** — raw logs from `scratch/{date}-{topic}-ladder-L{1..4}.md` (not the chat summaries — the full scratch contents)
3. **Done-when** — the literal `Done-when:` string for each criterion being verified, read on-demand from DECISIONS.md via targeted line-range read (FIN-009e progressive disclosure). Nothing else — no FIN title, no rationale, no design-doc context.

Prompt:
> You are a code reviewer. You are read-only — do not modify any files.
>
> Below is a diff, test output, and the literal `Done-when` criteria for this verification. Judge whether the diff + test output satisfy each `Done-when` criterion, one at a time. You have no access to any explanation of what the primary agent did or why — base your verdicts on the artifacts alone.
>
> For each criterion, return: `{criterion-id}: met | not met | judgment call` with one-line evidence (file:line, test name, or diff hunk reference).

**Return payload:** structured verdicts keyed by criterion, ~1K token cap. Write the full reviewer output to `scratch/{date}-{topic}-ladder-L5.md`; chat shows the verdict table only.

**Status writeback (FIN-015):** For each criterion the L5 reviewer confirmed as `met`, find the corresponding FIN entry in `projects/{name}/DECISIONS.md` and transition `Status: done → Status: verified`. **Never regress status on failure** — if the reviewer returns `not met` or `judgment call` for a criterion, leave that FIN at `done` (or whatever its current state is) and surface the criterion as an issue in Step 6. Log every `done → verified` transition in the L5 scratch file under a "Status transitions" section for audit.
</step>

<step name="Step 4 — Run WM verification checks (FIN-009e — on-demand expansion)">
After ladder checks complete, run WM-specific checks. Expand content on demand:

- **DECISIONS.md**: read each FIN's `Done-when:` line-range via targeted line-range read (use the FIN index from Step 1 to find the line number, then read ±5 lines). Do not re-read the whole DECISIONS.md file — only the specific line-range per check.
- **Design file**: read section-by-section as each check needs it. No whole-file read.
- **Plan file**: read only the step's done-when + intent sections per check.
- **Actual files / git**: target reads to specific files/lines called out by the FIN's done-when.

**Evidence rule:** For every check, show the evidence (file path, command output, git log). Do not claim "met" without proving it. If you haven't run the command, you can't claim it passes.

Checks:

1. **Done-when** — For each DECISIONS.md entry, read the `Done-when:` criterion via a targeted line-range read (FIN-009e). Check actual files, git log, or run commands to verify. Show evidence for each.
2. **Compliance with design** — Re-read the design file. Check that the implementation matches what was designed. Flag deviations — intentional or accidental.
3. **Cross-file consistency** — Version numbers consistent across files. No stale references. Archive integrity (next-version/skill).
4. **Behavioral verification** — If tests exist, confirm they pass (from ladder results). If no tests, verify behavior manually (check files, run commands, inspect output).
</step>

<step name="Step 5 — Present report">
```
## Verification — {project-name}

**Verdict:** {Ready to release | Issues found ({N}) | Judgment calls needed ({N})}
**Ladder:** L1 {pass/fail/skip} · L2 {pass/fail/skip} · L3 {pass/fail/skip} · L4 {pass/fail/skip} · L5 {pass/fail/skip}
**Done-when:** {X}/{Y} met

If issues found, list **titles only** here (e.g., "Issue 1: FIN-003 done-when not met"). Do NOT include What / Why / Options / Recommendation in Step 5 — those belong to Step 6 and are presented one-by-one.

Full ladder detail, done-when table, compliance check, and cross-file consistency check live in `scratch/{YYYY-MM-DD}-{topic}-ladder-L{N}.md` files — the user can say "expand L5" / "show done-when" / "show compliance" to see detail. Do not front-load any of this in the Step 5 report.
```
</step>

<step name="Step 6 — Walk through issues">
If no issues: skip to Step 7.

**Present ONE issue at a time. STOP after each and wait for the user's response before rendering the next.** Never dump the full issue list with What/Why/Options in a single message — that defeats the walkthrough. For each:

```
### Issue {N}: {short title}

**What:** {Describe the problem clearly — what's missing, wrong, or broken}

**Why it matters:** {Consequences if released as-is — what breaks, what users hit, what degrades}

**Options:** Present the options that analysis actually supports — one, two, or more. Follow [#Discovery Rules](rules/discovery-rules.md#discovery-rules) from rules/discovery-rules.md

**Recommendation:** {letter or "only option"} — {one-sentence reasoning}
```

Wait for user response before moving to next issue.

**Interpreting user response:**
- "ok", "yes", "agreed" → accept the recommendation, move to next issue
- User picks a letter (e.g., "C") → apply that choice, move to next issue
- Do NOT re-confirm what was already confirmed

**Anti-pattern (forbidden) — wall-of-text failure mode:** Bundling issues into Step 5's verdict section, combining all issues into a single message with What/Why/Options inline, or asking one combined "apply all fixes?" question at the bottom. This is the exact failure mode observed on 2026-04-13 with the `2026-04-12-workflow-audit-improvement` project — do not reproduce it.
</step>

<step name="Step 7 — Summarize and apply">
After all issues walked through, present summary and offer to act:

```
**Resolved:**
- Issue 1: {letter}) {one-line summary}
- Issue 2: {letter}) {one-line summary}

Apply these fixes? (ok to confirm, or specify overrides like "Issue 1: C instead")
```

- "ok" / "yes" → implement fixes immediately, then move to Step 8
- User specifies overrides → apply those instead, then move to Step 8
</step>

<step name="Step 8 — Present final options">
If **no issues were found** (all checks passed): ask the user whether to proceed to release. Approval advances the project to `awaiting-release`; decline stays in `executing`.

If **issues were resolved** in Steps 6-7: ask the user to pick one of — proceed to release (advance to `awaiting-release`), re-verify after the fixes landed, or go back to executing. Wait for user choice.

Presentation follows communication rules — do not impose a canned shape.
</step>

<step name="Step 9 — Update state and auto-route to release">
If user chooses to proceed:
1. Update `projects/{name}/STATE.md`: `Current state: awaiting-release`
2. **Silent scratch cleanup:** delete any scratch files this verify run created (ladder files at `scratch/{date}-{topic}-ladder-L*.md`). The report already contains the results — the scratch files were per-level detail that has served its purpose. Do not prompt the user; just delete.
3. Immediately route to release — invoke the release workflow.

Do NOT stop and ask the user to run `/wm:release` separately — the "proceed" confirmation already serves as approval.
</step>
</process>
