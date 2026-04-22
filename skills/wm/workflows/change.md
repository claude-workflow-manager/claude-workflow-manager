<purpose>
Adaptive change command. Triages every request into trivial / scoped / deep and applies matching discipline. Replaces `/wm:quick`. Works standalone or integrated with an active project. Always runs cheap triage before deciding behavior — never edits without first looking.
</purpose>

<required_reading>
@~/.claude/rules/discovery-rules.md
@~/.claude/rules/editing-rules.md
@~/.claude/rules/execution-rules.md
@~/.claude/rules/communication-rules.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/impact-scan.md
</required_reading>

<process>

<step name="Step 1 — Parse request and detect context">
Read the user's request. Identify:
- The intent (what to add, fix, remove, or rename)
- Any explicit target file/symbol named in the request
- Any override hint (see Step 3)

Check for active project:
- Look for `projects/ACTIVE.md` in current directory or parent
- If found, read it and identify the active project (most recent `Last session`)
- If not found → mode is **standalone** (no STATE/handoff/DECISIONS integration)
- If found → mode is **project-integrated**
</step>

<step name="Step 2 — Triage (FIN-012a — graph-driven, always runs)">
Cheap, fast classification. Maximum 3 queries to `/wm:doc-graph` via Skill dispatch (not raw `python -m` — FIN-018c).

1. **Forward + back refs on the target file** — if the request names a file, dispatch `/wm:doc-graph refs <file> --both`. The result shows (a) what the file references, and (b) what references it. If the request names only a symbol, dispatch `/wm:doc-graph search <symbol>` first, then `/wm:doc-graph refs <top-hit> --both`.
2. **Symbol search across the graph** — dispatch `/wm:doc-graph search <symbol>` and count matches. This replaces the inline `Grep` walk — the graph already has this data indexed.
3. **DECISIONS.md intersection** — if project-integrated, read only the FIN index of `projects/{active}/DECISIONS.md` (line-range read of FIN headings) and substring-match touched file paths and primary symbols against the index. Expand per-FIN body on demand only if a heading match is ambiguous.

If `/wm:doc-graph` is unavailable (not deployed / not a markdown-heavy repo), fall back to the inline `Read` + `Grep` triage from the pre-v2.1 version and note the degradation in a one-line triage note. Do not hard-fail triage on missing tool.

Classify based on signals:

| Signals observed | Classification |
|---|---|
| 1 file, no external references, no FIN match | **trivial** |
| Multiple files, OR external references exist, OR file is referenced in DECISIONS.md | **scoped** |
| Multiple FIN matches, OR plan/design doc references the area, OR symbol has many downstream consumers, OR change crosses module boundaries | **deep** |

Announce the classification briefly — name which bucket (trivial, scoped, or deep) and a one-sentence reason drawn from the signals. Presentation follows communication rules.
</step>

<step name="Step 3 — Apply user override (if any)">
Recognize override phrases in the request:

- **Force deep:** "zbadaj dokładnie", "investigate carefully", "this might affect", "to może wpływać na", "be careful here"
- **Force trivial:** "po prostu zrób", "just do it", "wiem co robię", "I know what I'm doing", "trust me"

If an override is detected, switch the classification and announce the switch — name the phrase that triggered the override and the before/after classification. Presentation follows communication rules.

User overrides win over auto-triage. Trivial override means the user takes responsibility — no propose step, but still log.
</step>

<step name="Step 4 — Trivial path">
Follow [#Editing Rules](rules/editing-rules.md#editing-rules) from rules/editing-rules.md

Conditions: classification = trivial.

1. Apply the edit directly via `Edit` or `Write`
2. Verify by reading the changed lines back
3. **Post-edit reference check (FIN-012a):** dispatch `/wm:doc-graph check` via Skill before committing. If it finds any broken reference touched by this edit, STOP and surface the broken refs — a trivial change that breaks a reference is no longer trivial. Hard-fail the commit on broken refs.
4. Commit with message: `fix: {one-line description}` or `chore: {one-line description}`
5. If project-integrated → append a one-line note to `projects/{active}/handoff.md` under "Quick changes" (create section if missing). No FIN updates, no STATE change.
6. Announce the completion in one line, summarizing what changed. Presentation follows communication rules.

STOP.
</step>

<step name="Step 5 — Scoped path">
Conditions: classification = scoped.

1. **Impact scan (FIN-012a):** dispatch `/wm:doc-graph impact --mode=light <files>` via Skill. The graph tool produces the same four-dimensional light report (files touched, FIN affected, downstream references, plan/design drift) as the inline `references/impact-scan.md` procedure — no inline Grep walk needed. Fall back to `references/impact-scan.md` light mode only if `/wm:doc-graph` is unavailable.
2. Based on the scan output, draft 1–2 options for the change. For each option capture: what changes, files touched, trade-off in one line.
3. Present the proposal to the user: the impact scan output, each option with its what/files/trade-off, your explicit recommendation with reasoning, and a request for approval. Presentation follows communication rules — name the recommendation, state the reason, state the trade-off.
4. Wait for user approval. Do not edit anything.
5. On approval: apply the chosen option, verify.
6. **Post-edit reference check (FIN-012a):** dispatch `/wm:doc-graph check` via Skill before committing. Hard-fail the commit on any broken reference touched by this edit — scoped changes that break references are back to drawing board.
7. Commit.
8. If project-integrated → append to `handoff.md` under "Scoped changes" with the scan summary, the chosen option, and the commit hash.

STOP.
</step>

<step name="Step 6 — Deep path">
Conditions: classification = deep.

Run the full 6-step investigated-fix process:

**6a. Investigate (FIN-012b — Haiku subagent)** — dispatch a Haiku discovery subagent (`model: haiku`) to read the relevant files thoroughly, trace cross-references (using `/wm:doc-graph refs` from within the subagent), and return a structured ~1K token summary: the root cause, the files involved, the cross-reference graph, and the 2-3 most plausible option directions. The main thread works from the summary, not from the raw files. Expand on demand only when drafting Option text needs a specific file snippet.

**6b. Options** — draft 2-3 options based on the subagent's summary. For each: what changes, what improves, trade-off, whether it's a design flaw / implementation gap / convention mismatch.

**6c. Recommend** — pick one with explicit reasoning.

**6d. Impact scan (FIN-012a + FIN-012b — deep, scratch output)** — dispatch `/wm:doc-graph impact --mode=deep <files>` via Skill. Write the full four-dimensional output to `scratch/{YYYY-MM-DD}-{topic}-change-impact.md`. The chat surface for this sub-step shows a **≤500-token summary** (top 5 FINs affected, top 5 downstream consumers, plan/design drift headline) with a pointer to the scratch file for the full blast radius. Fall back to `references/impact-scan.md` deep mode only if `/wm:doc-graph` is unavailable.

<!-- plugin-root-fallback -->
**6e. Propose and wait (FIN-012b — reviewer wrap)** — before rendering the proposal to the user, dispatch a Sonnet reviewer subagent (model from `@~/.claude/skills/wm/references/reviewer-config.md`) with artifacts only: the chosen option text, the plan steps, and the impact scan summary. The reviewer returns a structured verdict (`pass | flag: {concerns}`) that the main thread either acts on or surfaces alongside the proposal. Then present to the user the full proposal, which must include: the investigation summary (root cause), the options that analysis actually supports with per-option trade-offs, your explicit recommendation with reasoning, the ≤500-token impact summary from 6d with a pointer to the scratch file, the reviewer verdict, and the specific-action plan (numbered steps). Ask for approval. Presentation follows communication rules — name the recommendation, state the reason, state the trade-off. Follow [#Discovery Rules](rules/discovery-rules.md#discovery-rules) from rules/discovery-rules.md for the options-generation discipline.

Wait for user approval. Do not edit anything.

**6f. Apply** — on approval, make the changes. Keep edits minimal and surgical. Verify each change. **Post-edit reference check (FIN-012a):** dispatch `/wm:doc-graph check` via Skill before committing — hard-fail the commit on any broken reference. Then commit.

**6g. Decision update (propose-before-edit)** — if the impact scan identified FIN entries that need amendment, list each affected FIN (ID, current text, proposed amendment, and reason) and ask the user to approve, decline, or specify a subset. Wait for explicit approval before writing to DECISIONS.md. **Never auto-update.** If the change introduces a new decision not covered by any existing FIN, propose adding a new FIN-XXX entry the same way. Presentation follows communication rules.

7. If project-integrated → append a full entry to `handoff.md` under "Deep changes" with: investigation summary, chosen option, scan output, commit hash(es), FIN updates applied.

STOP.
</step>

<step name="Step 7 — Standalone mode notes">
When mode is **standalone** (no active project detected):
- Skip all `handoff.md`, `STATE.md`, `DECISIONS.md` references in Steps 4-6
- Skip the FIN update step in 6g entirely (no DECISIONS.md exists)
- Still run triage, still respect overrides, still propose-before-edit for scoped/deep
- This is the hot-fix-in-foreign-repo mode
</step>
</process>
