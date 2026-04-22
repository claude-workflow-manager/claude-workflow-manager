# Rule-Reminder Pattern

Convention for how WM workflow files cite rule files (`rules/*.md`). Applies to every workflow under `skills/wm/workflows/`. New workflows MUST follow this pattern; existing workflows are brought into conformance per release.

The pattern has two anchoring points that work together:

- **Top `<required_reading>` block** — every rule family whose rules will fire at any step in this workflow.
- **Inline reminder at step** — a canonical-form citation at the specific step that triggers the rule.

Top-load ensures context; inline reminder re-surfaces the specific rule at the moment it matters.

---

## 1. When to add a reminder

A reminder fires at the **step** where a rule actually applies — not in every workflow for completeness. Use the trigger table below to decide which rule family applies to which step.

| Trigger at this step | Rule family fires |
|---|---|
| Step asks the user a question / presents options | `communication-rules`, `discovery-rules` (if options are substantive) |
| Step edits files | `editing-rules` |
| Step runs implementation | `execution-rules` |
| Step reviews / verifies output | `review-rules` |
| Step outputs any text to the user | `communication-rules` (quasi-always-on) |

`communication-rules` is effectively always-on because every workflow produces user-visible output. It should appear in every workflow's `<required_reading>` block. Inline `communication-rules` reminders, however, fire only at high-intensity interaction moments — question prompts, option presentations, end-of-workflow summaries — not on every line of output.

Other rule families appear in `<required_reading>` only when at least one step in the workflow triggers them.

---

## 2. Canonical form

Inline reminders point to a **rule family** (the whole rule file), not to an individual rule within it. The canonical form is:

```
Follow [#{h1-header}]({rule-file}#{h1-slug}) from {rule-file}
```

Where:

- `{h1-header}` is the rule file's existing top-level H1 header text (e.g., `Discovery Rules`, `Global Communication Rules`). No rule-file restructuring is allowed.
- The leading `#` inside the link text is a **deliberate agent-readable signal** — it tells the agent "this link resolves to a rule file's header," distinguishing it from generic links.
- `{h1-slug}` is the standard GFM (GitHub-flavored-markdown) anchor slug of the H1 (lowercased, spaces → hyphens).
- `{rule-file}` is repeated in the trailing `from` clause so the source stays visible in plain-text renderings (chat transcripts, non-hyperlinked viewers).

The reminder loads the **whole rule family** into context — the agent re-reads all rules from that file, not a specific rule number.

### Worked examples

Discovery rules family (e.g., at a `/wm:discover` options-generation step):

```markdown
Follow [#Discovery Rules](rules/discovery-rules.md#discovery-rules) from rules/discovery-rules.md
```

Global Communication Rules family (e.g., at a user-confirmation step):

```markdown
Follow [#Global Communication Rules](rules/communication-rules.md#global-communication-rules) from rules/communication-rules.md
```

Execution Rules family (e.g., at an `/wm:execute` delegation step):

```markdown
Follow [#Execution Rules](rules/execution-rules.md#execution-rules) from rules/execution-rules.md
```

### Rule file H1 anchors (stable)

The 5 rule files and their canonical anchors:

| Rule file | H1 header | GFM slug |
|---|---|---|
| `rules/communication-rules.md` | `Global Communication Rules` | `global-communication-rules` |
| `rules/discovery-rules.md` | `Discovery Rules` | `discovery-rules` |
| `rules/editing-rules.md` | `Editing Rules` | `editing-rules` |
| `rules/execution-rules.md` | `Execution Rules` | `execution-rules` |
| `rules/review-rules.md` | `Review Rules` | `review-rules` |

**Stability requirement.** H1 header text of any rule file must be stable. Renaming an H1 is a breaking change — every workflow citing the old slug breaks. Do not rename without a repo-wide search-and-replace across `skills/wm/workflows/*.md`.

### Why whole-family, not per-rule

Rule files format individual rules as bold-in-numbered-list items, not as markdown headers — so per-rule GFM anchors do not exist. Rather than restructure the rule files or add explicit HTML anchors per rule, the pattern cites the file's H1 only. At workflow action moments, the agent typically needs the rule-family mindset (trade-off analysis, option scaling, plain-language test, etc.), not a single rule line. Whole-file pointers are simpler to maintain and match how humans mentally group rules.

### What the pattern replaces

The canonical form supersedes three ad-hoc variants observed in the repo before v1.1.0:

- Bare pointer: `follow \`rules/communication-rules.md\`.`
- Pointer + scope claim: `Follow the execution rules ... — especially rule #4 (...) and rule #5 (...).`
- Pointer + rule number + 35-word gloss: `Follow \`rules/discovery-rules.md\` rule #1: no padding, every option must earn its place...` (copy-pasted verbatim across three files — an active rot vector).

All of these are rewritten to the canonical form. The rot vector disappears because there is no separate gloss to drift from its source.

---

## 3. Anti-rot mechanism

Rule glosses are editorial paraphrases, not verbatim quotes — content-level lint is false-positive-prone. Freshness-level lint catches the real failure mode: rule file edited, reminder site forgotten.

### Staleness check (`check-rule-reminders`)

A verb on `/wm:doc-graph` scans `skills/wm/workflows/*.md` for canonical-form occurrences:

1. Parses every `Follow \[#{h1}\]({rule-file}#{slug}) from {rule-file}` match and extracts the cited `{rule-file}` path.
2. For each match, compares the containing workflow file's last-modified time vs. the cited rule file's last-modified time. Git commit time (`git log --format=%ct -1 -- <path>`) is preferred over filesystem mtime for portability.
3. If the rule file is newer than the workflow file, emits a staleness warning naming the workflow, the rule file, and the dates.

### Release-gate integration

`/wm:release` Step 3 already runs `/wm:doc-graph check` as a hard gate for broken references. `check-rule-reminders` runs alongside it.

**Rollout.** Warn-only in the v1.1.0 release (matches the FIN-018 hook-deployment pattern — one validation cycle at warn level before promoting to block). After one release cycle with no false-positive noise, the verb flips to a hard block: stale reminders fail `/wm:release` until the workflow file is touched (re-reviewed and re-committed).

### Invariant after v1.1.0

Any workflow file citing a rule file inline (canonical form) must have last-modified time greater than or equal to the cited rule file's last-modified time. This invariant is enforced mechanically by the staleness check.

---

## 4. Per-workflow audit

Audit built from `/wm:doc-graph refs <rule-file> --in` against each of the 5 rule files, cross-referenced with text-level inline-reminder occurrences. The graph measures **structural `<required_reading>` includes only** — text-mention-only references are not counted.

Target state as of v1.1.0 — every "Y" column means at least one step in that workflow triggers the corresponding rule family, so the rule family MUST appear in `<required_reading>` and a canonical-form inline reminder MUST sit at the triggering step(s).

| Workflow | `communication-rules` | `discovery-rules` | `editing-rules` | `execution-rules` | `review-rules` |
|---|---|---|---|---|---|
| `abandon.md` | Y | — | Y | — | — |
| `change.md` | Y | Y | Y | Y | — |
| `clean-up.md` | Y | — | Y | — | — |
| `code-graph.md` | Y | — | — | Y | — |
| `discover.md` | Y | Y | Y | — | — |
| `doc-graph.md` | Y | — | — | Y | — |
| `execute.md` | Y | — | Y | Y | — |
| `learn.md` | Y | — | Y | — | Y |
| `new-project.md` | Y | Y | Y | — | — |
| `next.md` | Y | — | Y | — | — |
| `plan.md` | Y | — | Y | Y | — |
| `release.md` | Y | — | Y | Y | Y |
| `resume.md` | Y | — | — | — | — |
| `save.md` | Y | — | Y | — | — |
| `skip.md` | Y | — | Y | — | — |
| `status.md` | Y | — | — | — | — |
| `verify.md` | Y | Y | — | — | Y |
| `verify-plan.md` | Y | Y | Y | — | Y |

### Notes

- `communication-rules` is always-on (every workflow outputs text) — it appears in every row.
- `discovery-rules` in `<required_reading>` is reserved for workflows that generate **substantive options** (multiple defensible paths, trade-off analysis). Simple yes/no confirmations, justification prompts, and single-route selections are not substantive — they trigger `communication-rules` only.
- `status.md` is read-only output only — no other rule family triggers.
- `code-graph.md` and `doc-graph.md` are thin wrappers that dispatch to implementation — they trigger `execution-rules` via the dispatch step, but no editing or discovery.
- `verify.md` and `verify-plan.md` historically cited `discovery-rules` inline without including it in `<required_reading>`. v1.1.0 closes that gap.

### Keeping the table in sync

When a workflow's step set changes (a new trigger is added or removed), update this table in the same PR. The staleness check does not catch structural drift — only time-based rot. Structural drift detection is future work.

---

## Related references

- `skills/wm/references/skill-building-guidelines.md` — `## Cross-cutting conventions` section points new workflow authors here.
- `rules/discovery-rules.md` — Rule 9 (Investigate artifact contracts) is the discovery-phase companion: check the project's own contract files before generating options. This convention doc is itself one such contract file for workflow authors.
- `skills/wm/workflows/doc-graph.md` — the `check-rule-reminders` verb dispatch lives here.
- `skills/wm/workflows/release.md` — wires `check-rule-reminders` into the release gate.
