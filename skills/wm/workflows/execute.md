<purpose>
Enter or resume execution of the plan for the active project. Native execution engine with tier-aware behavior, wave-based parallelism, deviation rules, and checkpoint protocol.
</purpose>

<required_reading>
@~/.claude/rules/execution-rules.md
@~/.claude/rules/editing-rules.md
@~/.claude/rules/communication-rules.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/gate-matrix.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/impact-scan.md
</required_reading>

<autonomy>
Execute the full plan autonomously. Do NOT pause between steps, waves, or checkpoints for confirmation. Only stop when:
- Pre-wave scan finds delta vs plan (Step 5 rules)
- Deviation Rule 2 or 3 triggers (plan gap / architecture drift)
- Circuit breaker fires (3x test fail / >50% scope creep)
- A step's verify command fails and auto-fix per Rule 1 isn't applicable
- You genuinely need input the plan doesn't answer

Checkpoints (Step 7) run silently: update handoff, commit, continue to next wave. Announce progress but do not ask "proceed?". The user approved the plan at /wm:verify-plan — that approval covers execution end-to-end.
</autonomy>

<process>
<step name="Step 1 — Load project state">
Read `projects/{name}/STATE.md` — check current state and determine tier.

- If `planned` and tier is T2: "Plan not verified. Run `/wm:verify-plan` first." STOP.
- If `planned` and tier is T1: proceed to Step 3 (T1 skips verification).
- If `between-cycles` or `backlog`: "Not ready for execution. Current state: `{state}`." STOP.
- If `plan-verified`: proceed to Step 3 (starting fresh).
- If `executing`: proceed to Step 2 (resuming).

**Determine tier:** Read the plan file header for `Tier:` line. If no plan file (T0), execute directly from DECISIONS.md.
</step>

<step name="Step 2 — Resume (if already executing)">
Read `projects/{name}/handoff.md` for last session context.

Run `git log --oneline -10` to verify recent commits.

Run `git status` to check for uncommitted changes.

Present a resume summary: project name, scope described naturally (e.g. "small fix", "checklist with 8 steps", "detailed plan, 3 waves"), last session summary from the handoff, progress (step N of M), whether uncommitted changes are present, and the next action from the handoff. Presentation follows communication rules.

Proceed to Step 4 (T1) or Step 5 (T2), starting from the first uncompleted step.
</step>

<step name="Step 3 — Start fresh execution">
Update `projects/{name}/STATE.md`:
- `Current state: executing`
</step>

<step name="Step 4 — T1 Execution (Checklist)">
Read the plan file. Work through checkbox steps sequentially in the main context.

For each step:
1. Read the step's file list — load only those files
2. Implement the change described in the step
3. Run the verify command — show output
4. If verify passes: mark checkbox `[x]` in plan file, commit the change
5. **FIN status writeback (FIN-014):** After committing, walk `projects/{name}/DECISIONS.md` and identify any FIN entry whose `Done-when` intersects with this step — intersection is a substring match on the step's file paths or the step's `done-when` text in the FIN's `Done-when` line. For each matched FIN currently at `Status: pending`, update to `Status: done`. Log which FIN IDs were transitioned in a one-line note appended to handoff.md under "Status transitions". Never regress a FIN's status on writeback — only `pending → done`, never the reverse.
6. If verify fails: apply deviation rules (Step 6)

**Gitignore guard:** When committing, only stage files that appear in `git status`. Never `git add` a file that `git status` doesn't list — it's likely gitignored workflow state. Never use `git add -f`.

After all steps complete: run checkpoint (Step 7), then proceed to Step 8.
</step>

<step name="Step 5 — T2 Execution (Wave-Based)">
Read the plan file. Parse wave assignments and dependencies.

**Execute wave by wave:**

For each wave (starting from Wave 1):

**Pre-wave impact scan (light, FIN-004):** Before entering the wave, dispatch `/wm:doc-graph impact --mode=light` via Skill against the union of files declared by all steps in this wave. This replaces the deep inline impact-scan that used to live here — `verify-plan` already ran the deep check, so per-wave execution only needs the cheap light variant.

Surface a 5-10 line pre-wave note showing: files touched by the wave, FINs affected (IDs only), downstream reference count, and the verdict line. Soft gate — **informational, not blocking**. The wave proceeds regardless of the verdict, but the note is logged to handoff.md under a "Pre-wave notes" section so downstream reviewers can see what the impact surface looked like at execution time.

Deviation path: only stop the wave if the light scan returns `verdict: conflict` or `verdict: blocked` — in those cases apply Rule 3 (architecture drift) from Step 6. A `review needed` verdict is logged and execution continues.

If `/wm:doc-graph` is unavailable (tool not deployed / not a markdown-heavy repo), skip the scan silently and proceed — do not hard-fail execution on a missing tool.

**5a. Single step in wave → execute in main context:**
1. Read the step's file list — navigate structurally first (grep/glob for symbols), then read targeted line ranges. Whole-file reads only for small files (<100 lines) or when full context is genuinely needed.
2. Implement the change
3. Run verify command — show output
4. If passes: mark step complete in plan, commit
5. If fails: apply deviation rules (Step 6)

**5b. Multiple independent steps in wave → spawn parallel subagents:**
1. Confirm steps have no shared files (single integrator rule)
2. Spawn up to `min(3, step_count)` subagents, one per step
3. Each subagent receives:
   - The step description (edit intent, files, verify, done-when)
   - Gitignore guard context
   - File scope restriction: "Only modify files listed in your step. Do not touch other files."
   - Return format requirement (see delegation rules below)
4. Wait for all subagents to complete
5. Review each subagent's structured return — verify all steps passed
6. Mark completed steps in plan, commit results
7. If any subagent fails: apply deviation rules (Step 6) for that step

Follow [#Execution Rules](rules/execution-rules.md#execution-rules) from rules/execution-rules.md

**Structured return schema** — all subagents must return:
```
## Result
Status: {pass|fail}
Files touched: {list}
Key findings: {bullet list, max 5}
Next action: {suggestion for main thread, or "none"}
```
Target: ~1K tokens max. No raw file dumps, no full command output. Main thread reads structured return only — expands by reading files if needed.

**L5 reviewer subagent** (when step has `review: true`):
The reviewer receives artifacts only — no primary agent narrative:
1. Git diff of the step's changes
2. Test/lint output (from verification-output.log if available)
3. The plan step's intent and done-when criteria (from the plan file)
Default model: Sonnet. The reviewer evaluates whether the diff satisfies the intent and done-when. No access to the primary agent's explanation of what it did or why.

**After each wave completes:**
- Verify all steps in wave are done
- **FIN status writeback (FIN-014):** walk `projects/{name}/DECISIONS.md` and identify any FIN entry whose `Done-when` intersects with any of this wave's completed steps — intersection is a substring match on the wave's touched file paths or the steps' `done-when` text against the FIN's `Done-when` line. For each matched FIN currently at `Status: pending`, update to `Status: done`. Log the transitioned FIN IDs in handoff.md under "Status transitions". Never regress status on writeback — only `pending → done`.
- Check if checkpoint needed (every 3-5 steps or >50% context used) → run Step 7
- Advance to next wave directly. **Do not pause for confirmation.**

After all waves complete: run final checkpoint (Step 7), then proceed to Step 8.
</step>

<step name="Step 6 — Deviation rules">
Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md

When execution encounters something unexpected:

**Rule 1 — Trivial fix** (typo, missing import, lint error, formatting):
- Auto-fix immediately
- Log: "Deviation (trivial): {what was fixed}"
- Continue execution

**Rule 2 — Plan gap** (step underspecified, missing dependency discovered, file doesn't exist where expected):
- Pause execution
- Show: "Plan gap found: {description of what's missing or wrong}"
- Propose amendment: "Suggested fix: {specific change to plan or additional step}"
- Wait for user approval
- Apply amendment, continue execution

**Rule 3 — Architecture drift** (step would change approach, requires new files not in plan, scope expanding beyond plan):
- Stop execution
- Show: "Architecture drift detected: {what changed and why}"
- Ask the user to pick one of three alternatives: amend the plan (and continue with the amendment), revert to the last checkpoint (and re-plan from there), or proceed with the deviation logged (risk: plan no longer matches implementation). Presentation follows communication rules.
- Wait for user choice.

**Hard rule:** Every deviation is logged in handoff.md under "Deviations" section, regardless of severity. No silent deviations.

**Circuit breakers:**
- Same test fails 3 consecutive times → pause and escalate. Tell the user the test is failing repeatedly and ask whether to debug, skip the step, or abort execution. Presentation follows communication rules.
- Execution scope exceeds plan by >50% (files or steps) → checkpoint and ask the user whether to continue with the current approach (recommended if progress is solid) or pause and re-plan from here. Presentation follows communication rules.
</step>

<step name="Step 7 — Checkpoint protocol">
Triggered after every 3-5 steps (T2), at end of execution (T1), or when context is >50% used.

1. Update plan file: mark completed steps `[x]` or note completion
2. Update `projects/{name}/handoff.md` with:
   - Current progress (step N of M)
   - What was completed (with evidence)
   - What's in progress
   - Any deviations logged
   - Key files touched
   - Next actions
3. Commit all work done so far, then **immediately continue to next wave without asking**
4. If new decisions were discovered during execution → append to DECISIONS.md
</step>

<step name="Step 8 — Execution complete">
After all steps are done:

1. **Final FIN sweep (FIN-014):** Walk every FIN entry still at `Status: pending` in `projects/{name}/DECISIONS.md`. For each, re-check whether its `Done-when` clause is now satisfied by the committed changes — substring-match the FIN's done-when text against the union of all touched files and all step done-wens in the plan. Update matching FINs to `Status: done`. Log the final transition list in handoff.md under "Status transitions — final sweep". Still-pending FINs after this sweep are flagged in the execution summary as "unresolved — needs manual review before `/wm:verify`".
2. Run final checkpoint (Step 7)
3. Update `projects/{name}/STATE.md`:
   - Update `Last session` with date and summary of what was done
4. Announce that execution is complete and name the next legitimate actions (verify the implementation with `/wm:verify`, or save progress with `/wm:save`). Presentation follows communication rules.

Do NOT auto-advance to verification.
</step>
</process>
