# Learn — The Five Investigation Checks

When the bucket is **text-rule**, the recommendation that `/wm:learn` presents to the user must include the output of all five checks below. Each check catches a specific documented failure mode. Skipping any of them leaves one mode unaddressed and wastes the user's attention.

For `hook` and `skill-reference` buckets, these checks do NOT apply verbatim — those buckets have their own recommendation shapes (see the bottom of this file for a short summary).

---

## Why five checks, not more or fewer

Research (see the synthesized contrarian report in `scratch/research-compound-learning/`) identifies five ways new rules silently fail:

1. A similar rule already exists and should be edited, not duplicated
2. The new rule contradicts an existing rule and confusion results
3. The new rule is too vague to fire — the agent can't even recognize when to apply it
4. The file the rule goes into is already at or past its attention-budget ceiling
5. A related existing rule is stale and should be updated at the same time

Each check maps to one failure. Together they cover the documented pain.

---

## Check 1 — Existing-rule scan

**What the agent does:**
1. Identify the target partition (from `learn-partitions.md` + routing).
2. Read the target file.
3. Scan for rules whose topic, keywords, or concrete trigger overlap with the proposed rule. Use both lexical overlap (shared key terms) and semantic similarity (same behavior being governed).
4. If any candidate matches, capture it verbatim with its line number or section heading.

**Output in the recommendation:**

```
Check 1 — Existing rules on this topic:
  [{line N}] "{verbatim existing rule}"
  [{line M}] "{verbatim existing rule}"
  (or: none found)
```

**What the user sees:**
- If matches found → the user is shown each match and asked: "Edit one of these instead of adding a new rule?" Adding a new rule is possible but deliberately more friction.
- If no matches → the check simply reports "none found" and the workflow proceeds.

**Why this check matters:**
Most of the time when the user runs `/wm:learn` in Mode A (diagnose), the problem is that an existing rule has a scope loophole or buried wording, not that a rule is missing. Surfacing the existing rule lets the user widen or sharpen it instead of piling another rule on top. This was the Rule 1 case in the compound-learning-command discovery session — the fix was editing Rule 1's scope, not adding a new rule.

---

## Check 2 — Conflict detection

**What the agent does:**
1. Read the target file and all other partitions that would be loaded in the same context (for example: if the target is `communication-rules.md`, also consider `~/.claude/AGENTS.md` if present, and any project-level `AGENTS.md`).
2. For each existing rule, ask: "Does the proposed rule instruct the opposite, a subset, or a superset of this existing rule in any scenario?"
3. Flag any contradictions or conditional overlaps.

**Output in the recommendation:**

```
Check 2 — Conflicts with existing rules:
  CONTRADICTS: [{file}:{line}] "{existing rule}"
    Reason: {one-line explanation of the contradiction}
  CONDITIONAL OVERLAP: [{file}:{line}] "{existing rule}"
    Reason: {one-line explanation of the scope interaction}
  (or: no conflicts found)
```

**What the user sees:**
- CONTRADICTS → the user must resolve before the rule can be saved. Options: (a) drop the new rule, (b) delete/edit the old rule, (c) rewrite both so they're conditional on different contexts.
- CONDITIONAL OVERLAP → not a blocker. The user sees that two rules might both apply in different scopes; the agent asks whether the new rule should name its condition explicitly (e.g., "when writing case studies" vs the existing "when writing insight posts").

**Why this check matters:**
Claude Code concatenates instruction files without arbitrating between them — contradictions cause arbitrary rule selection (Anthropic docs). The Fuse `writing-learnings.md` already has conditional overlaps ("perspective of observer" vs "perspective of partner in case studies"); without the conditional qualifiers, those two rules would contradict. This check forces the qualifier to be written in.

---

## Check 3 — Specificity check

**What the agent does:**
Evaluate the proposed rule's phrasing against three requirements:

1. **Concrete trigger** — does the rule name a specific situation where it applies? ("when writing a LinkedIn hook", "every message that asks a question", "any file under `src/api/`"). Vague triggers like "generally", "when appropriate", "sometimes" fail this.
2. **Concrete expected behavior** — does the rule name a specific observable action or output? ("start with a customer quote", "include a one-line point on the first line", "run `pnpm test` before committing"). Vague expectations like "write well", "be clear", "do the right thing" fail this.
3. **Failure detectability** — can the agent (or the user reviewing output) tell whether the rule fired? "The first line contains a decision" is detectable. "The tone is friendly" is not easily detectable without judgment.

**Output in the recommendation:**

```
Check 3 — Specificity:
  Concrete trigger: yes | no — {why}
  Concrete behavior: yes | no — {why}
  Failure detectable: yes | no — {why}
  Verdict: PASS | NEEDS SHARPENING | REJECT
```

**What the user sees:**
- PASS (all three yes) → the workflow proceeds.
- NEEDS SHARPENING (1-2 nos) → the agent proposes a sharpened rewrite and asks for approval before continuing.
- REJECT (3 nos) → the rule is so vague it cannot be saved. The agent explains why and ends the workflow, suggesting the user either sharpen the lesson or accept "nothing to save".

**Why this check matters:**
Ned's A/B test of 7 Cursor rules: 2 rules (29%) did literally nothing because they were vague. A rule that can't be detected or can't name its trigger is attention tax for zero behavioral effect. Better to not save it.

---

## Check 4 — Attention cost display

**What the agent does:**
1. Count existing rules in the target file (lines, sections, numbered entries).
2. Compute approximate line count after the new rule is added.
3. Look up the file's ceiling from the table below.
4. Report current state and projected state.

**Ceilings (per FIN-006):**

| Target file | Ceiling | Load behavior |
|---|---|---|
| `~/.claude/rules/communication-rules.md` | ~10 rules / ~50 lines | injected every 5 messages — stay tight |
| `~/.claude/CLAUDE.md` or `AGENTS.md` | ~200 lines | loaded in full at session start |
| `.claude/rules/*.md` (path-scoped) | ~100 lines each | loaded when scope matches |
| Skill `references/*.md` (on-demand) | ~500 lines | loaded only when skill runs; generous budget |
| Agent `references/*.md` (on-demand) | ~500 lines | loaded only when agent runs; generous budget |
| Project-level learnings files | ~300 lines | on-demand, per-project scope |
| Hook scripts | n/a | mechanical, not context |

**Output in the recommendation:**

```
Check 4 — Attention cost:
  Target file: {path}
  Current: {N} rules / {M} lines
  After adding: {N+1} rules / ~{M+added} lines
  Ceiling: {ceiling} — at {X}% after save
  Verdict: OK | APPROACHING CEILING | AT CEILING
```

**What the user sees:**
- OK (under 70%) → no action needed.
- APPROACHING CEILING (70-90%) → informational nudge: "file is getting full; consider whether anything can be retired in the same pass".
- AT CEILING (>90%) → stronger prompt, but NOT a block. The user can still save; the agent asks if there's an obsolete rule to retire first.

**Why this check matters:**
The Curse of Instructions ($P = p^N$) bites when a file's rule count exceeds the model's attention budget. Making the cost visible lets the user make informed trades. The check is information, not enforcement — the user decides.

---

## Check 5 — Staleness check

**What the agent does:**
For each existing rule surfaced by Check 1, cross-check whether the rule still reflects current project reality:

1. If the rule mentions a file path → does the file still exist?
2. If the rule mentions a function, API, or framework version → grep the project for current usage to confirm the mentioned thing is still live.
3. If the rule mentions a convention ("we use `pnpm`") → verify the convention still holds by checking config files.
4. If the rule can't be cross-checked mechanically (pure behavioral) → mark as "cannot verify, assume current".

**Output in the recommendation:**

```
Check 5 — Staleness of related existing rules:
  [{file}:{line}] "{rule}" — STALE: {why}
    Evidence: {what the agent found that contradicts the rule}
    Suggested action: UPDATE | RETIRE | CONDITIONAL
  [{file}:{line}] "{rule}" — CURRENT
  [{file}:{line}] "{rule}" — UNVERIFIABLE (behavioral)
  (or: no related rules to check)
```

**What the user sees:**
- STALE → the workflow proposes updating or retiring the stale rule as part of the same recommendation. The user can approve the fix alongside the new rule, or defer.
- CURRENT → no action.
- UNVERIFIABLE → no action (common for behavioral rules like "lead with the point" that can't be grep-checked).

**Why this check matters:**
Stale rules are *actively harmful*, not just useless — the agent "confidently follows patterns your codebase has moved on from" (Kondratiuk). Catching staleness during an investigation of a related lesson is almost free and prevents a whole class of future failures.

---

## Short notes on other buckets

`/wm:learn` uses the five checks only for text-rule recommendations. For the other buckets:

### hook bucket

Recommendation includes:
- Which tool call(s) the hook will intercept (`PreToolUse` matcher)
- The exact failure mode the hook prevents
- Full hook script source (using `templates/hook-bash-template.sh` or `hook-python-template.py`)
- A test invocation demonstrating that the hook fires on the documented bad case and does not fire on benign cases
- Settings.json merge diff

No existing-rule or staleness check — hooks are independent scripts, each one is its own enforcement unit.

### skill-reference bucket

Recommendation includes:
- Which skill the reference belongs to (or which new skill is being created)
- The file path under `skills/{skill}/references/` or inside a workflow
- The lesson's content (preserving ASSETS verbatim per strict-synthesis rules — examples, frameworks, counter-examples)
- A short note on when the skill loads (so the user understands when the lesson will actually be in context)

No attention-cost check — on-demand references have generous budgets. Light existing-rule check if the skill already has a reference on the same topic.
