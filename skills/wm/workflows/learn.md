<purpose>
Capture a lesson from the current session (Mode A: diagnose something that went wrong, or Mode B: extract what made something go well) and route it to the dev project where the fix belongs. The command investigates, classifies, and recommends; the user decides and approves. The lesson is written as a FIN entry to a dev project's DECISIONS.md — never edited directly into target files.
</purpose>

<required_reading>
@~/.claude/rules/review-rules.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/learn/learn-partitions.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/learn/learn-routing.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/learn/learn-checks.md
<!-- plugin-root-fallback -->
@~/.claude/skills/wm/references/learn/learn-verification.md
</required_reading>

<autonomy>
This workflow is interactive and gate-driven. Do NOT save any file, run any destructive operation, or commit without explicit user approval. Every recommendation must be surfaced with reasoning and wait for user confirmation or redirect. The principle: investigate and recommend, never auto-save.
</autonomy>

<process>

<step name="Step 1 — Load session context and read transcript window">
Read the recent session context so later steps can classify the mode, identify the artifact or failure, and investigate without guessing.

**What to read:**
1. The last **10 turns** of the current Claude Code session transcript. A turn is one user message plus its associated assistant response, counted as one unit.
2. If the user passed an optional hint in the command arguments (e.g. `/wm:learn the hook worked because...`), capture the hint verbatim — it overrides session inference in later steps.
3. If the user passed an explicit lookback override (e.g. `/wm:learn --lookback 20`), read that many turns instead of 10.

**How to find the transcript:**
- Prefer the `transcript_path` field if this workflow is running inside a context that exposes it (hooks do; top-level slash commands typically do not).
- Otherwise, locate the most recent JSONL under `~/.claude/projects/{cwd-hash}/*.jsonl`. The hash is derived from the cwd path using Claude Code's standard scheme. If unsure, read the most recently modified JSONL in the directory for the current project.

**What to extract per turn:**
- User message text (what did the user say or ask?)
- User message tone signals — corrections ("no", "don't", "again", "too long", "wall of text"), praise ("good", "great", "that worked"), neutral Q&A
- Assistant response summary — what the agent actually did, with special attention to recent tool calls (`Write`, `Edit`, `Bash`, file saves, skill completions)
- Any inline errors, failures, or retries

**Output of this step** (internal, passed to Step 2):
```
session_context:
  turn_count: {N}
  lookback: {default 10 or override}
  optional_hint: "{hint text or none}"
  recent_corrections: [{list of correction lines, if any}]
  recent_completions: [{list of recent Write/Edit/skill-finish events}]
  last_user_tone: {corrective | satisfied | neutral | mixed}
```

If the transcript cannot be read for any reason (file not found, parse error, permissions), report that clearly and ask the user: "I can't read the session transcript. Want to describe what happened in your own words, or cancel?"
</step>

<step name="Step 2 — Classify mode from session context">
Using the session_context from Step 1, decide which of four verdicts the current situation matches. Always surface reasoning in one sentence and wait for user confirmation before proceeding.

**The four verdicts:**

| Verdict | Trigger | Proposal text |
|---|---|---|
| **diagnose** (Mode A) | `recent_corrections` is non-empty, OR `last_user_tone: corrective`, OR hint text contains failure signals ("wall of text", "wrong", "ignored X") | "Looks like X went wrong — fix that?" |
| **extract** (Mode B) | `recent_completions` is non-empty AND `last_user_tone: satisfied` or `neutral`, OR hint text contains positive signals ("the hook worked", "this post was good") | "Looks like you just finished X — capture what worked?" |
| **nothing** | Neither corrections nor completions in the window, routine Q&A only | "Nothing here looks worth capturing. Sure you want to run `/wm:learn`?" |
| **ambiguous** | Both corrections AND completions present in the window (common when a good artifact was produced through a correction cycle) | "Two candidates: (1) {correction summary}, (2) {completion summary}. Which?" |

**Precedence when signals conflict:**
- Explicit optional hint always wins. If the hint says "capture from the last post", the mode is `extract` regardless of what the transcript shows.
- Correction text from the **last 2 turns** outweighs a completion that happened earlier in the window — recency matters because fresh pain is what the user typed `/wm:learn` for.

**Output format:**
Present the verdict in one sentence and stop for user confirmation:

```
Verdict: {diagnose | extract | nothing | ambiguous}
Reasoning: {one sentence naming the specific signal — e.g. "user said 'wall of text again' two turns ago"}

{Proposal text}
```

**Interpreting user response:**
- "ok" / "yes" / "Y" → accept verdict, proceed to Step 3
- "no, it's X instead" / picks a different verdict → re-classify with the user's correction and proceed
- For `ambiguous` → user picks (1) or (2), the workflow proceeds with the chosen candidate as the lesson focus
- For `nothing` → if user confirms there's nothing to save, exit the workflow cleanly

**Never auto-save or auto-route without confirmation at this step.** This is the user's first decision gate.
</step>

<step name="Step 3 — Identify candidate partitions">
Determine the set of lesson destinations (partitions) available for the current context, combining prior knowledge from the partition map with a live scan of the current project.

**3a. Read the partition map:**
<!-- plugin-root-fallback -->
Load `@~/.claude/skills/wm/references/learn/learn-partitions.md`. Parse each archetype's match rules (cwd-prefix and has-file checks) against the current working directory.

**3b. Match archetypes against the current cwd:**
- Evaluate each archetype's match rules in declaration order.
- An archetype matches only if all its match rules are satisfied.
- Multiple archetypes may match — most specific wins (higher number of match rules satisfied). Ties broken by declaration order.
- `generic-claude-code` always matches as fallback.

If a non-fallback archetype matches, record its name and the full list of partitions from its table. If only `generic-claude-code` matches, record its fallback partitions AND note internally: `archetype_unknown: true` — used to prompt the user at the end of the workflow to add an archetype entry for this cwd.

**3c. Live scan for partitions not in the map:**
Independent of the archetype match, scan the current project's actual file tree for partition-looking files that the map may not know about:
- Look for files matching `*LEARNINGS*.md`, `*learnings*.md`, `*rules*.md`, `AGENTS.md`, `CLAUDE.md` within the project root and one directory level deep
- Look for `.claude/rules/*.md`, `.claude/hooks/*` in the project
- Look for existing skill or agent reference directories near the cwd (`skills/*/references/`, `agents/*/references/`)

For each file found by scan that is NOT already in the matched archetype's partition table, record it as a **candidate-not-in-map**.

**3d. Merge and output:**
Produce the final partition candidate list. Sort candidates by relevance: in-map partitions first (they're confirmed fits for this archetype), then candidate-not-in-map partitions with a note that they were discovered live.

**Output of this step** (internal, passed to Step 4):
```
partition_candidates:
  archetype: {name or "generic-claude-code"}
  archetype_unknown: {true | false}
  in_map:
    - {kind}: {resolved path} ({scope}, {load-behavior})
    - ...
  not_in_map:
    - {path} (discovered by live scan)
    - ...
```

No user interaction at this step — the output is raw candidate data. Step 5 uses these candidates to identify the target system component and infer the dev workspace.
</step>

<step name="Step 4 — Investigate the lesson and bind artifact">
Build a concrete statement of the lesson itself — what happened, what should be preserved, and (for Mode B) which artifact the lesson came from.

**4a. Branch by mode:**

**If mode == diagnose (Mode A):**
- Identify the specific failure from `recent_corrections` in the session_context. Quote the user's exact words.
- Propose a root-cause hypothesis from among the four standard causes: (i) stochastic model noise, (ii) underspecification in the prompt, (iii) existing rule has a scope loophole, (iv) no rule covers this case.
- Do NOT jump to "add a rule" yet. The investigation has to name the cause before proposing a fix.
- Output: `failure_description`, `cause_hypothesis`, `candidate_lesson_seed`.

**If mode == extract (Mode B):**
- Identify the artifact the lesson should be extracted from. Apply the three-tier binding in order:
  1. **Explicit pointer** — if the command hint contains a path or a clear pointer (`/wm:learn from posts/xyz/draft-final.md`), use that path.
  2. **Most recent significant completion** — look at `recent_completions` for the most recent `Write`/`Edit` on a file matching artifact patterns (post drafts, docs, reference files, skill files, images in a post folder). Confirm the match with the user in one sentence before proceeding: "Extract from `{path}`? (Y to confirm, or name a different file)".
  3. **Ask** — if neither applies, ask: "I don't see a recent finished artifact in this session. What should I extract from? (path, or 'transcript only' if the finished thing was a conversation)".
- Artifact-less Mode B (transcript-only) is allowed — no special case.
- Output: `artifact_path` (or `none`), `session_turns_relevant` (the subset of turns where the creative decisions happened).

**4b. Read sources:**
- In both modes, the session transcript is the primary source for decisions — why X was chosen over Y, what was rejected, what was corrected.
- In Mode B, also read the artifact file (if bound) to see the final form.
- In Mode A, also read the target partition (from Step 3's candidates) if the cause hypothesis is "existing rule has a scope loophole" — the hypothesis is wrong unless a relevant existing rule is actually present.

**4c. Produce a draft lesson:**
Write a candidate lesson in concrete prose:
- **Trigger** — when does this rule/insight apply? (required; vague triggers fail Step 6 Check 3)
- **Expected behavior or principle** — what should happen? (required; vague behaviors fail Check 3)
- **Provenance** — one sentence linking back to the source (session date, artifact path, correction quote)

**Output** (internal, passed to Step 5):
```
lesson_draft:
  mode: {diagnose | extract}
  artifact_path: {path or none}
  failure_description: {Mode A only}
  cause_hypothesis: {Mode A only}
  trigger: "{when the lesson applies}"
  behavior: "{what should happen}"
  provenance: "{source pointer}"
```

**No user interaction at this step** — this is silent investigation. The user sees the draft in Step 7's recommendation and can edit, accept, or reject then.
</step>

<step name="Step 5 — Identify target workspace and classify bucket">
Two sub-tasks: (1) determine which dev project this lesson belongs to, and (2) classify the lesson type as metadata for the FIN entry.

**5a. Identify target system component:**
From the lesson_draft (Step 4), identify which system component the lesson targets. Use the `target_partition` candidates from Step 3 and the lesson's trigger/behavior to determine:
- Which file or component needs to change
- Which dev workspace owns that component (e.g., agent reference → agent dev folder, wm skill → Workflow-manager, global rule → whichever project manages globals)

**5a2. Rank routing candidates via graph search (FIN-004):**
Before falling back to the four-rule inference in 5b, ask the graph which files in this repo are most related to the lesson's concept. Dispatch `/wm:doc-graph search <concept-or-keywords>` via Skill (not via raw `python -m` — the Python invocation lives only in `doc-graph.md` per FIN-018c). Pick 3–5 keywords from `lesson_draft.trigger` and `lesson_draft.behavior` — concrete nouns and verbs, not stop words.

The ranked result gives up to N files scored by header / path / signal match. Combine this ranking with the partition candidates from Step 3 to form a final suggestion list:

1. Prefer files that appear in BOTH the search result AND Step 3's partition candidates — these are high-confidence routing targets.
2. Add any high-score search hits (top 3) that aren't already in the partition list as secondary suggestions.
3. Present all suggestions to the user in Step 5c with their provenance labelled ("partition match", "search hit", or "both").

If `/wm:doc-graph` is unavailable (tool not deployed / not a markdown-heavy repo), skip this sub-step silently and proceed to 5b on partition candidates alone.

**5b. Infer dev workspace:**
Determine which dev workspace owns the target component. Use the partition candidates from Step 3 to trace the target file back to its source project:

1. Check if the target file lives inside the current working directory — if so, the current project may be the dev workspace.
2. Check if the target file is a deployed artifact (e.g., under `~/.claude/skills/`, `~/.claude/commands/`, `~/.claude/rules/`, `~/.claude/hooks/`) — look for a dev repo that deploys to that location (check for `AGENTS.md` or similar project markers in likely dev folders).
3. Check if the target file belongs to an agent (`agents/{name}/...`) — the agent's own dev folder is the workspace.
4. If none of the above resolves, ask the user: "This lesson targets `{path}`. Which dev workspace should own the fix?"

**5c. Confirm with user:**
Present the inferred workspace in one line and ask for confirmation:
```
Fix targets {component} → dev workspace: {workspace path}. Correct? (Y to confirm, or name a different workspace)
```

**5d. Classify bucket (lightweight metadata):**
<!-- plugin-root-fallback -->
Read `@~/.claude/skills/wm/references/learn/learn-routing.md`. Run the 4-check decision tree on the lesson_draft to classify as `text-rule`, `hook`, or `skill-reference`. This classification is metadata — it describes what kind of change is needed and helps structure the FIN entry. It does not determine where the lesson is saved (all lessons route to a dev project).

```
bucket: {text-rule | hook | skill-reference}
reason: {which check fired}
signals: [{specific words or phrases that triggered the check}]
```

**5e. Check for archetype_unknown promotion:**
If Step 3 marked the archetype as unknown OR the chosen partition is a `not_in_map` candidate, queue a post-save prompt: "This partition type wasn't in my map for {archetype}. Add it for next time?" — asked in Step 8 after the project is created/updated.

**Output** (internal, passed to Step 6):
```
routing:
  dev_workspace: {path to dev workspace}
  target_component: {file or component that needs to change}
  target_file: {resolved path to the file that would be changed — used by Step 6 for investigation}
  bucket: {text-rule | hook | skill-reference}
  reason: {check that fired}
  archetype_unknown: {true | false}
  partition_not_in_map: {true | false}
```
</step>

<step name="Step 6 — Run investigation checks and FIN quality gate">
Run investigation checks against `routing.target_file` from Step 5 to understand the current state of the target and produce informed FIN entries. The checks investigate — they do not generate deliverables (no scripts, no diffs, no file content).

**6a. Common checks (all buckets):**
<!-- plugin-root-fallback -->
Read `@~/.claude/skills/wm/references/learn/learn-checks.md` and run these checks against the `routing.target_file` and `lesson_draft`:

1. **Check 1 — Existing content scan.** Read the target file. Find content with overlapping topic, keywords, or triggers. Capture verbatim with line numbers. Output: list of matches or "none found".

2. **Check 2 — Conflict detection.** For each existing element in the target file, ask whether the proposed lesson contradicts, duplicates, or conditionally overlaps with it. Output: CONTRADICTS / CONDITIONAL OVERLAP / none per element.

3. **Check 3 — Specificity.** Evaluate the lesson_draft against three criteria: concrete trigger, concrete expected behavior, failure detectability. Output: PASS / NEEDS SHARPENING / REJECT. If REJECT, the workflow cannot proceed without a sharpened rewrite or explicit override.

**6b. Bucket-specific investigation:**

- **text-rule:** Additionally run Check 4 (attention cost — current rule count vs ceiling) and Check 5 (staleness of related rules).
- **hook:** Identify the constraint, what tool/action it would block, and the failure case it prevents. Do NOT generate a hook script — that happens during the dev project's execution.
- **skill-reference:** Identify what content exists in the target file, what needs adding or changing, and whether existing content conflicts. Do NOT compose reference content or diffs.

**6c. FIN entry quality gate:**
<!-- plugin-root-fallback -->
Read `@~/.claude/skills/wm/references/learn/learn-verification.md`. Verify the lesson_draft meets FIN entry quality standards before proceeding:
- Is the trigger concrete enough to act on?
- Is the implementation description detailed enough that the dev workflow won't need to re-investigate?
- Is done-when observable?

If quality gate fails, loop back to sharpen the lesson_draft before proceeding.

**Output** (internal, passed to Step 7):
```
check_results:
  bucket: {text-rule | hook | skill-reference}
  existing_content: [{matches or "none"}]
  conflicts: [{CONTRADICTS / CONDITIONAL / none per element}]
  specificity: {PASS | NEEDS SHARPENING | REJECT}
  # text-rule only
  attention_cost: {OK | APPROACHING | AT-CEILING}
  staleness: [{STALE / CURRENT / UNVERIFIABLE per rule}]
  # hook only
  constraint: {what is blocked and why}
  # skill-reference only
  content_gap: {what needs adding/changing}
  # all buckets
  fin_quality: {PASS | NEEDS SHARPENING}
```
</step>

<step name="Step 7 — Present recommendation">
Present a concise routing recommendation. The user needs to decide: is this the right fix, going to the right place? All investigation details go to the project, not the chat.

**Recommendation format (same for all buckets):**

```
## /wm:learn recommendation

**Found:** {one sentence — what the lesson is about}
**Type:** {bucket} — {one sentence why}
**Targets:** {target_file} in {dev_workspace}
**Conflicts:** {none | one-line summary of conflicts from Step 6}
**Action:** {Create new project | Add to existing project "{name}"}

Approve? (Y to confirm, N to cancel, or suggest a different workspace/project)
```

Keep it under 10 lines. No code examples, no diffs, no detailed check dumps. The investigation details (existing content analysis, conflict specifics, quality assessment) are written to the project in Step 8.

**Wait for user response:**
- "ok" / "yes" / "Y" → proceed to Step 8.
- "edit" / user revises the lesson → incorporate the edit and re-run Steps 5-7.
- "reject" / "cancel" → exit the workflow. Note: "Workflow exited without saving per user decision."
- User names a different workspace or project → update routing, re-run Step 6 checks.

**Never proceed to save without explicit user approval.**
</step>

<step name="Step 8 — Create or update dev project">
After user approval in Step 7, route the lesson to the appropriate dev project.

**8a. Check for existing project match:**
Read `projects/ACTIVE.md` in the target dev workspace (from `routing.dev_workspace`). Look for active projects that cover the same target file or topic.

- If a matching project exists → offer: "Add FIN entry to existing project `{name}`? (Y to add, N to create new)"
- If no match → create a new project via the standard scaffold (same structure as `/wm:new-project`): `projects/{date}-{slug}/STATE.md`, `DECISIONS.md`, `handoff.md`. Add a row to `projects/ACTIVE.md` in the target dev workspace.

**8b. Seed DECISIONS.md with investigation findings:**
Write suggested FIN entries and investigation context. These are starting points for discovery, not final decisions — the dev workflow reviews and refines them.

```
### FIN-{NNN}: {lesson title} (suggested by /wm:learn)
Decision: {lesson_draft.trigger + behavior, concise}
Rationale: {lesson_draft.provenance + cause_hypothesis if Mode A}
Suggested implementation: {what might need to change — informed by bucket type and check_results}
Done-when: {concrete, observable criterion}
Status: suggested
```

The bucket classification shapes the Suggested implementation field:
- **text-rule** → "Add/update rule in {target_file}: {trigger} → {behavior}"
- **hook** → "Create hook: block {constraint} via PreToolUse on {tool}. {failure case it prevents}"
- **skill-reference** → "Add/update {content_gap} in {target_file}"

Below each suggested FIN entry, include the investigation context as visible prose (not hidden comments):
- Existing content found in target file (with line numbers)
- Conflicts detected
- Quality assessment notes
- Root cause hypothesis (Mode A) or artifact analysis (Mode B)

This context is the foundation for `/wm:discover` — it saves re-investigation.

**8c. Write handoff.md:**
Seed with session continuity info only (not investigation details — those live in DECISIONS.md):
- Goal → lesson summary
- Blockers / open questions → any unresolved issues from Step 6
- Next actions → `/wm:discover` to review suggestions and design the fix

**8d. Confirm to user:**

```
Project: {project name} ({created | updated})
FIN entry: {FIN-NNN title}
Workspace: {dev_workspace path}
Next: run /wm:discover in that workspace to design the fix
```

**8e. Run archetype growth prompt if flagged (from Step 5e):**

If `archetype_unknown == true` OR `partition_not_in_map == true`, ask:
"This partition type wasn't in my map for {archetype}. Add it to learn-partitions.md for future runs? (Y/N)"

- Y → append the new partition entry to `learn-partitions.md`.
- N → skip.

**End of workflow.** The user's next action is their own. Do not auto-advance to any other wm command.
</step>

</process>
