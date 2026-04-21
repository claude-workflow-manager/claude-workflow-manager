# Learn — Three-Bucket Classification

Classify each lesson into exactly one of three types. The bucket is **metadata** — it describes what kind of change the lesson requires and helps structure the FIN entry written to the dev project's DECISIONS.md. The bucket does not determine where the lesson is saved (all lessons route to a dev project via `/wm:learn` Step 8).

---

## The three buckets

| Bucket | What it captures | What it means for the FIN entry |
|---|---|---|
| **text-rule** | Soft behavioral or communication expectations | FIN implementation describes a rule to add/update in a specific file. Advisory, not mechanical. |
| **hook** | Hard constraints on files, commands, or actions | FIN implementation describes a PreToolUse hook to create. Mechanical enforcement — the only type that blocks the agent. |
| **skill-reference** | Procedural sequences or domain craft knowledge | FIN implementation describes content to add/update in a skill or agent reference file. On-demand, context-specific. |

Every lesson routes to exactly one bucket. If a lesson seems to fit two buckets, it usually means it has two separable components (e.g., a behavioral rule + a hard constraint that enforces it); split it and route each component separately.

---

## Decision tree

Run these checks in order. The first yes wins the bucket.

### Check 1 — Does the lesson name a concrete file path, directory, command, or tool-call pattern that must never be done?

Signals:
- Lesson contains words like "never", "must not", "forbidden", "do not touch", "block"
- Lesson names a specific path: `migrations/`, `.env`, `~/.ssh/`, `prod config/*`
- Lesson names a specific command: `rm -rf`, `git push --force`, `kubectl delete`
- Violation would be catastrophic, irreversible, or a security breach
- A deterministic check can decide "did this fire or not" at tool-call time

**If yes → bucket: `hook`.** Generate a hook script using the templates in `templates/hook-bash-template.sh` or `templates/hook-python-template.py`. Text rules will not reliably prevent this failure (Rezvani's migration incident, wpostma's 33-session test).

### Check 2 — Is the lesson a multi-step procedure or a sequence of actions to perform in a specific order?

Signals:
- Lesson contains phrases like "when X, first do Y, then Z"
- Lesson describes a checklist of 3+ steps
- Lesson encodes a framework ("follow BDA structure: Before, During, After")
- Lesson is a decision tree with branching logic
- The lesson's value comes from the *order* or *completeness* of steps, not from a single instruction

**If yes → bucket: `skill-reference`.** The lesson belongs either inside an existing skill's workflow file (if the skill already exists and the lesson refines it) or in a new reference file under the skill's `references/` folder. Text rules cannot reliably carry procedures — they get summarized to their first step and the rest is lost.

### Check 3 — Is the lesson long enough that injecting it every 5 messages would pollute context?

Signals:
- Lesson is 5+ sentences or has multiple sub-points
- Lesson is craft knowledge (examples, patterns, counter-examples)
- Lesson only matters in a specific mode or context (e.g., "when writing LinkedIn hooks", "when editing React components")

**If yes → bucket: `skill-reference`** (long-form craft lives in on-demand references, not in always-on files).

### Check 4 — Fallback

Everything else is a **`text-rule`**. Short (1-3 sentences), behavioral or communication-oriented, needs to be present in the session but doesn't need mechanical enforcement. Routes to the partition identified by `learn-partitions.md` — most commonly `~/.claude/rules/communication-rules.md` for global behavior, or an agent's reference file for agent-specific behavior.

---

## Examples by bucket

### text-rule examples

1. "Lead with the point — every message starts with one line stating the decision."
   Why: short, behavioral, applies to every agent message. Routes to `communication-rules.md`.

2. "In Fuse LinkedIn posts, hook variants that start with a customer quote tend to outperform abstract claims."
   Why: short, behavioral, mode-specific (so not global), lives in the Ghostwriter's reference. Not a procedure — one principle the agent keeps in mind while drafting.

3. "Ad Builder recommendations should state the strategic objective before the copy variants."
   Why: short behavioral guidance, lives in the Ad Builder's reference.

### hook examples

1. "Never modify files under `migrations/` without explicit approval."
   Why: concrete path, must-not, deterministic check possible (intercept `Edit` calls with matching paths). This is exactly the Rezvani failure case — text rules documented the rule and the agent ignored it. Only a hook stops it.

2. "Never commit `.env` files."
   Why: concrete pattern, violation is catastrophic, `PreToolUse` on `Bash` can match `git add .env` or similar and block.

3. "Never run `rm -rf` without an explicit confirmation dialog."
   Why: existing `block-destructive.py` already covers variants of this. The template would extend that hook.

### skill-reference examples

1. "When building a new agent, run these 7 steps: (1) map the domain, (2) draft the constitution, (3) ..."
   Why: multi-step procedure, too long for a text rule, belongs as a workflow step or reference in the agent-building skill.

2. "Case study narrative arc — how to structure the Proof Objective Card section, with 4 examples of well-formed cards and 2 counter-examples."
   Why: long craft knowledge with examples. Belongs in `agents/case-study-creator/references/proof-objective-card.md`, loaded only when the Case Study Creator runs.

3. "LinkedIn hook patterns library — 8 patterns with source post, evidence of effectiveness, and counter-cases."
   Why: long library, mode-specific (hook writing), belongs as a reference file loaded when the Ghostwriter / Hook Master skill runs.

---

## Counter-examples (things that look like one bucket but aren't)

### Looks like hook, but is text-rule
*"Don't use `any` in TypeScript code."*

Why counter: concrete keyword, sounds like a constraint, BUT this is style/taste — reasonable use of `any` exists in tests and escape hatches. A hook that blocks all `any` would be over-restrictive and get disabled. Better as a text rule in an agent reference or a linter config (which is outside `/wm:learn` scope). Route to **text-rule**.

### Looks like text-rule, but is skill-reference
*"Always write descriptive commit messages."*

Why counter: short behavioral instruction, sounds like a rule, BUT "descriptive" is context-dependent — a bug fix commit is descriptive differently from a refactor commit. The real lesson is a procedure: *"For bug fix commits, include: (a) the symptom, (b) the root cause, (c) the fix."* That's a multi-step procedure → **skill-reference** (loaded when the agent is asked to commit).

### Looks like skill-reference, but is hook
*"Always run tests before committing."*

Why counter: sounds like a procedure ("first run tests, then commit"), BUT the intent is enforcement — the agent should not be able to commit without having run tests. A text reference saying "always run tests" will be ignored under pressure. The enforcement mechanism is a `PreToolUse` hook on `Bash` matching `git commit` that checks whether tests were run in the current session. Route to **hook**.

---

## Output contract

When the workflow uses this reference during bucket classification (learn.md Step 5d), it must output a one-line decision of the form:

```
Bucket: {text-rule | hook | skill-reference}
Reason: {which check fired — 1, 2, 3, or 4 fallback}
Signals: {specific words/phrases from the lesson that triggered the check}
```

This classification is used as metadata in the FIN entry's Implementation field and surfaced in the concise recommendation (learn.md Step 7) so the user can sanity-check the classification before approving project creation.
