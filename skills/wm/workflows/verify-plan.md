<purpose>
Run a plan verification report before execution. T2 only — T1 skips this step. Hard gate — requires user approval to proceed.
</purpose>

<required_reading>
@~/.claude/rules/review-rules.md
@~/.claude/rules/editing-rules.md
@~/.claude/rules/execution-rules.md
@~/.claude/rules/discovery-rules.md
@~/.claude/rules/communication-rules.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/gate-matrix.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/impact-scan.md
</required_reading>

<process>
<step name="Step 1 — Load project state">
Read `projects/{name}/STATE.md`, `projects/{name}/DECISIONS.md`, and list `projects/{name}/plans/`.

Check tier from plan file header. If T1: tell the user this change doesn't need formal plan verification, point them to `/wm:execute`. STOP.
</step>

<step name="Step 2 — Gate: plan file exists">
Check `projects/{name}/plans/` for at least one plan file (`.md`, not `.gitkeep`).

If none: "No plan file found. Run `/wm:plan` first." STOP.
</step>

<step name="Step 3 — Run verification checks (FIN-010a — reviewer subagent)">
Follow [#Review Rules](rules/review-rules.md#review-rules) from rules/review-rules.md

<!-- plugin-root-fallback -->
**Reviewer subagent dispatch (FIN-010a):** Read `@~/.claude/skills/wm/references/reviewer-config.md` for the default reviewer model. Dispatch a Sonnet reviewer subagent to run the eight checks below. Input contract: artifacts only — the plan file, DECISIONS.md, the design doc (if present), the investigation file from FIN-003 (`projects/{name}/plans/{date}-{topic}-investigation.md`), and `/wm:doc-graph` query results invoked from within the subagent. **No primary-agent narrative in the subagent's input** — the reviewer must derive verdicts from the artifacts alone to break inter-agent sycophancy.

The subagent returns a structured verdicts payload keyed by check number (`check_N: pass | fail | partial` + `evidence:` per row) which the main thread renders in Step 4.

If the reviewer subagent is unavailable (dispatcher missing, model error), fall back to in-thread check execution and note the degradation in the Step 4 report header.

**Evidence rule:** For every check, show the evidence (file path, line, git output, or `/wm:doc-graph` query result). Do not claim "covered" without pointing to the specific plan task that covers it. Rows where evidence cannot be computed — no matching plan step, no file line number to cite — auto-fail with status `missing` (FIN-011).

Checks:

1. **Coverage** — Map each DECISIONS.md entry to specific plan tasks. For each entry show which task covers it and how. Count: X/N decisions covered.
2. **Compliance** — Read the design file. Check that the plan implements what the design describes. Flag any plan tasks that deviate from the design, or design elements missing from the plan.
3. **Approach** — Evaluate task ordering and dependencies. Flag: tasks that depend on unfinished predecessors, missing integration steps, tasks too large to verify individually.
4. **Plan quality (FIN-002 — path existence + investigation intersection)** — Check that every step has: specific file paths (not vague), verify command, done-when criteria. Flag steps missing these.

   **Availability probe — MANDATORY before the Path existence sub-check dispatches anything.** Run one probe: `/wm:doc-graph ls .` via Skill. Interpret deterministically (no judgment calls):
   - **Exit 0 and non-empty output** → graph is available. Run the Path existence sub-check as specified below.
   - **Exit non-zero OR empty output** → graph is unavailable. **Skip the Path existence sub-check entirely** and record `Path existence: skipped — graph unavailable` in the Check 4 row. **Do not auto-fail rows on a missing graph** — that would fail correct plans whose only sin is that the graph wasn't built. Plan quality (vague paths, missing verify, missing done-when) is still checked without the graph.

   **You may not skip the probe** and decide availability by inference, session context, or memory of earlier failures.

   **Path existence sub-check (only if probe succeeded):** for every file path named by any plan step, dispatch `/wm:doc-graph refs <file>` via Skill. If the file does not resolve in the graph (or the verb exits non-zero for that specific file), **auto-fail the row** with status `missing` — a plan that names a guessed path is a broken plan. This is the canonical fix for the failure mode FIN-001 called out ("plans name guessed paths that don't exist").

   **Investigation intersection sub-check:** intersect the plan's file paths with the "Candidate paths" section of `projects/{name}/plans/{date}-{topic}-investigation.md` (produced by `plan.md` Step 6a per FIN-003). Any plan path not present in the investigation file's candidate list auto-fails the row — the planner should only name paths the investigation already surfaced. If the investigation file is missing (plan ran before FIN-003 landed, or `/wm:doc-graph` was unavailable at plan time), note the degradation but do not block verification on it.
5. **Wave integrity** — Check that steps in the same wave have no shared files. Flag file overlaps.
6. **Gates** — Archive committed? Version bump recorded?
7. **Impact (deep) (FIN-002 + FIN-009c)** — Replace the inline impact-scan with `/wm:doc-graph impact --mode=deep <plan-step-files...>` dispatched via Skill. The graph tool produces the same four-dimensional output as the `references/impact-scan.md` template (files touched, FIN affected, downstream consumers, plan/design drift) — no inline Grep walk needed.

   **Availability — reuse the Check 4 probe result.** If Check 4's probe succeeded, dispatch the full impact query below. If Check 4's probe failed, skip straight to the degraded path (`references/impact-scan.md` deep procedure) and note the degradation in the report header. Do not probe twice per verify-plan run, and do not make a fresh judgment call here.

   **Full report → scratch (FIN-009c):** Write the verb's full deep output to `scratch/{YYYY-MM-DD}-{topic}-impact.md`. The Step 4 report embeds a **≤500-token summary** (top 5 FINs affected, top 5 downstream consumer rows, verdict line) with a pointer to the scratch file for the full blast radius. This keeps the main verify-plan report reviewable in a single screen while preserving the full impact data on disk for audit.

8. **Design coverage** — Check `projects/{name}/plans/` for a file matching `*-design.md`. If none exists: note "No design doc — skipping design coverage check" and proceed. If present:
   a. Read the design doc in full.
   b. Enumerate decisions/requirements from prose — all sections are authoritative (Goals, Architecture, Components, Risks, Non-goals). Extract concrete implementable commitments: architecture choices, protocol specifics, contracts, named patterns, constraints stated in Risk mitigations, non-goals that imply implementation limits.
   c. Read the plan file in full.
   d. For each decision, identify covering plan step(s) by matching against each step's `Done-when`. A step "covers" a decision if its `Done-when`, when satisfied, directly demonstrates the decision was honored — not just that a related file exists. Test: if the `Done-when` can be satisfied while the decision is violated, it does not cover the decision.
   e. Produce a coverage table: `Decision | Covered by | Status`. Status values: `covered` (Done-when fully proves the decision), `partial` (Done-when exercises the decision but doesn't fully prove it — treat as gap unless user accepts), `gap` (no covering step).
   f. For each gap or partial (decision with no covering step, or partial coverage not explicitly accepted): present the decision and offer:
      - A) Fix now — propose a concrete `Done-when` amendment for the relevant step, wait for user approval before editing
      - B) Mark N/A — user provides reason (logged in report)
      - C) Accept — user provides reason (logged in report)
      Do not advance until every gap is resolved (fixed, N/A, or accepted).
</step>

<step name="Step 4 — Present report">
```
## Plan Verification — {project-name}

**Verdict:** {Ready to execute | Issues found ({N}) | Judgment calls needed ({N})}
**Checks:** 1 Coverage {✓/partial/fail} · 2 Design compliance {✓/partial/fail} · 3 Approach {✓/partial/fail} · 4 Plan quality {✓/partial/fail} · 5 Wave integrity {✓/partial/fail} · 6 Gates {✓/partial/fail} · 7 Impact {clean/review needed/conflict/blocked} · 8 Design coverage {✓/partial/fail}
**Coverage:** {X}/{N} FINs mapped to plan steps

If issues found, list **titles only** here (e.g., "Issue 1: Wave B file overlap"). Do NOT include What / Why / Options / Recommendation in Step 4 — those belong to Step 5 and are presented one-by-one.

Full per-check detail (Coverage table, Design compliance table, Approach bullets, Plan quality bullets, Gates bullets, Impact deep report, Design coverage table) lives in `scratch/{YYYY-MM-DD}-{topic}-verify-plan-detail.md` — the user can say "show coverage" / "show design compliance" / "show impact" to expand.

**Hard gate:** If Impact verdict is `conflict` or `blocked`, the overall verdict cannot be `Ready to execute` until the conflict is resolved or explicitly accepted by the user as a logged deviation.
```
</step>

<step name="Step 5 — Walk through issues">
If no issues: skip to Step 6.

**Present ONE issue at a time. STOP after each and wait for the user's response before rendering the next.** Never dump the full issue list with What/Why/Options in a single message — that defeats the walkthrough. For each:

```
### Issue {N}: {short title}

**What:** {Describe the problem clearly — what's missing, wrong, or risky}

**Why it matters:** {Consequences if ignored — what breaks, what gets harder, what gets skipped}

**Options:** Present the options that analysis actually supports — one, two, or more. Follow [#Discovery Rules](rules/discovery-rules.md#discovery-rules) from rules/discovery-rules.md

**Recommendation:** {letter or "only option"} — {one-sentence reasoning}
```

Wait for user response before moving to next issue.

**Interpreting user response:**
- "ok", "yes", "agreed" → accept the recommendation, move to next issue
- User picks a letter (e.g., "C") → apply that choice, move to next issue
- Do NOT re-confirm what was already confirmed
</step>

<step name="Step 6 — Summarize and apply">
After all issues walked through, present summary and offer to act:

```
**Resolved:**
- Issue 1: {letter}) {one-line summary}
- Issue 2: {letter}) {one-line summary}

Apply these fixes? (ok to confirm, or specify overrides like "Issue 1: C instead")
```

- "ok" / "yes" → implement fixes immediately (edit files, update DECISIONS.md, etc.), then move to Step 7
- User specifies overrides → apply those instead, then move to Step 7
</step>

<step name="Step 7 — Present final options">
If **no issues were found** (all checks passed): ask the user whether to proceed to execution. Approval advances the project to `plan-verified`; decline stays in `planned`.

If **issues were resolved** in Steps 5-6: ask the user to pick one of — proceed to `plan-verified`, re-verify after the fixes landed, or go back to planning (`/wm:plan`). Wait for user choice.

Presentation follows communication rules — do not impose a canned shape.
</step>

<step name="Step 8 — Update state and auto-route to execution">
If the user approves proceeding:
1. Update `projects/{name}/STATE.md`: `Current state: plan-verified`
2. **Silent scratch cleanup:** delete any scratch files this verify-plan run created (impact scan at `scratch/{date}-{topic}-impact.md`). The report already contains the summary — the scratch file was full-detail backup that has served its purpose. Do not prompt the user; just delete.
3. Immediately route to execution — invoke the execute workflow.

Do NOT stop and ask the user to run `/wm:execute` separately — the "proceed" confirmation already serves as approval.
</step>
</process>
