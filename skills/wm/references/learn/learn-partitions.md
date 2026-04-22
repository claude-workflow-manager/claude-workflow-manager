# Learn — Partition Map

Prior knowledge for `/wm:learn` about where lessons land in known project archetypes. This is a **starting point, not a cage**: the agent always combines this map with a live scan of the current project and may route to partitions not in the map. When that happens, the agent proposes adding the new partition here for next time.

---

## Schema

Each archetype is one `## ` section below. Fields:

- **name** — short identifier used in recommendations
- **match** — rules for detecting whether the current cwd is inside this archetype. A match rule is either `cwd-prefix: <path>` (literal path prefix check) or `has-file: <relative-path>` (the file must exist relative to cwd or any ancestor up to match-ceiling). Multiple rules on one archetype are ANDed. If any archetype's rules all match, the archetype is a candidate.
- **partitions** — list of known lesson destinations for this archetype. Each partition entry has:
  - **kind** — one of `comms` (global communication rules), `skill-ref` (skill reference file), `agent-craft` (agent reference / craft knowledge), `project-learnings` (per-project learnings file), `hook` (enforcement hook script), `project-docs` (project-level documentation file)
  - **path** — path pattern relative to cwd or absolute; may contain `{agent}` or `{project}` placeholders to be resolved at runtime
  - **scope** — `global` (machine-wide), `project` (current project only), `agent` (specific agent), `session` (transient)
  - **load-behavior** — `always` (loaded every session — expensive), `on-demand` (loaded when skill/agent invoked — free until fired), `injected` (pushed into context via hook), `mechanical` (hook that blocks at tool level, not in context)
- **scope-hints** — free-text notes about when to prefer which partition in this archetype; the agent uses this as context during routing

## Matching order

Match all archetypes against the current cwd. If multiple archetypes match (e.g., a Fuse project inside a Dev root that also matches `generic-claude-code`), the most specific match wins — specificity is measured by the number of match rules satisfied. Ties are broken by declaration order (earlier archetype wins). The `generic-claude-code` archetype is the fallback and always matches.

---

## wm

**name:** wm (Workflow Manager itself)

**match:**
- has-file: `skills/wm/VERSION`

**partitions:**

| kind | path | scope | load-behavior |
|---|---|---|---|
| comms | `~/.claude/rules/communication-rules.md` | global | injected (hook) |
| skill-ref | `skills/wm/references/{topic}.md` | agent | on-demand |
| skill-ref | `skills/wm/references/learn/learn-{topic}.md` | agent | on-demand |
| project-learnings | `projects/{project}/DECISIONS.md` | project | on-demand |
| project-docs | `projects/{project}/design-doc.md` | project | on-demand |
| hook | `~/.claude/hooks/{name}.sh` | global | mechanical |

**scope-hints:**
- Baseline communication rules (the 9 global rules) go to `~/.claude/rules/communication-rules.md`. Hook re-injection keeps them fresh.
- Wm-specific workflow rules ("when in discover mode, always ask one question at a time") go to the relevant workflow file's embedded instructions OR to a new reference under `skills/wm/references/`.
- Procedural lessons about the wm lifecycle go to skill references, not rules. Example: "how to detect scope creep during execute" → `skills/wm/references/execute-scope-creep.md`.
- Project-specific lessons (this-project facts, decisions) stay in the project's `DECISIONS.md` — do not promote to the global skill.

---

## markdown-agents

**name:** markdown-agents (Markdown-Agents framework + agent collection)

**match:**
- cwd-prefix: `d:/Dev/Markdown-Agents`
- has-file: `docs/SPEC.md`

**partitions:**

| kind | path | scope | load-behavior |
|---|---|---|---|
| comms | `~/.claude/rules/communication-rules.md` | global | injected (hook) |
| agent-craft | `agents/{agent}/references/{topic}.md` | agent | on-demand |
| agent-craft | `agents/{agent}/docs/LEARNINGS.md` | agent | on-demand |
| project-learnings | `agents/{agent}/projects/{project}/learnings.md` | project | on-demand |
| project-docs | `agents/{agent}/docs/prd-{agent}.md` | agent | on-demand |

**scope-hints:**
- Craft knowledge earned while *using* an agent on a client project goes upstream into that agent's references (the "Cat 3 feeds Cat 2" loop). Example: Ad Builder used on client X produced a new ad-copy pattern → write to `agents/ad-builder/references/copy-patterns.md`, not to the client project.
- Lessons specific to one client stay in the client's project folder under `agents/{agent}/projects/{project}/learnings.md`.
- Methodology refinements (framework tweaks that apply across all uses of an agent) go to the agent's main references, not to per-project learnings.
- Spec-level changes (cross-agent architecture) do NOT belong here — those are spec-evolution decisions, out of `/wm:learn` scope.

---

## fuse-collective

**name:** fuse-collective (Fuse Collective client work — campaigns, case studies, content)

**match:**
- cwd-prefix: `d:/Dev/Fuse-Collective`

**partitions:**

| kind | path | scope | load-behavior |
|---|---|---|---|
| comms | `~/.claude/rules/communication-rules.md` | global | injected (hook) |
| agent-craft | `{project}/knowledge/writing-learnings.md` | project | on-demand |
| agent-craft | `{project}/knowledge/{topic}-learnings.md` | project | on-demand |
| project-learnings | `{project}/learnings/{slug}.md` | project | on-demand |
| project-docs | `{project}/AGENTS.md` | project | always |
| project-docs | `{project}/.docs/PRD.md` | project | on-demand |

**scope-hints:**
- The Fuse `writing-learnings.md` pattern is canonical here: per-post `learnings.md` captures raw session decisions, universal rules migrate to the `knowledge/writing-learnings.md` global craft file. `/wm:learn` formalizes this pipeline.
- Polish language is first-class — voice and tone rules often reference specific Polish phrasings. Preserve them verbatim when promoting across posts.
- Each sub-project (MKT-LinkedIn-Posts, ad-builder, case-study-creator usage, etc.) has its own `knowledge/` folder. Do not cross-pollinate between sub-projects without explicit user approval.
- Client-specific facts (ICPs, brand constraints, taboo topics) stay in that client's project, never promoted to global.

---

## creative-sparks

**name:** creative-sparks (Creative-Sparks web builds and UX R&D)

**match:**
- cwd-prefix: `d:/Dev/Creative-Sparks`

**partitions:**

| kind | path | scope | load-behavior |
|---|---|---|---|
| comms | `~/.claude/rules/communication-rules.md` | global | injected (hook) |
| agent-craft | `{project}/AGENTS.md` | project | always |
| agent-craft | `{project}/learnings/figma-patterns.md` | project | on-demand |
| project-learnings | `{project}/learnings/{slug}.md` | project | on-demand |
| project-docs | `{project}/DESIGN.md` | project | on-demand |
| project-docs | `{project}/sections-registry.md` | project | on-demand |

**scope-hints:**
- Figma extraction failures (SVG path integrity, asset extraction quirks, variable-def drift) are the most common lesson category. These belong in per-project `learnings/figma-patterns.md` first; promote to a shared pattern library only if the same failure appears in 2+ projects.
- VRT tolerance tweaks (pixel diff thresholds per component) are project-specific — do not generalize.
- Component discipline (line limits, extraction order) can promote to the web-developer agent if the lesson is repeatable across projects.

---

## generic-claude-code

**name:** generic-claude-code (fallback — any project not matching a specific archetype)

**match:**
- (no rules — always matches as fallback)

**partitions:**

| kind | path | scope | load-behavior |
|---|---|---|---|
| comms | `~/.claude/rules/communication-rules.md` | global | injected (hook) |
| project-docs | `./AGENTS.md` | project | always |
| project-docs | `./CLAUDE.md` | project | always |
| project-learnings | `./LEARNINGS.md` | project | on-demand |
| skill-ref | `./.claude/rules/{topic}.md` | project | always |
| hook | `./.claude/hooks/{name}.sh` | project | mechanical |

**scope-hints:**
- Use this fallback when the agent can't identify the project archetype. Ask the user after routing: "I used the generic map for this project. Should I add a specific archetype entry for it?"
- Default for repo-wide policy rules: `./AGENTS.md` if present, else `./CLAUDE.md`, else create `./AGENTS.md`.
- Default for narrow, directory-scoped rules: `./.claude/rules/{topic}.md` with appropriate `paths:` frontmatter.
- Default for hard constraints: `./.claude/hooks/{name}.sh` with `PreToolUse` matcher.

---

## Growth protocol

When `/wm:learn` routes a lesson to a partition not described in any archetype above, it proposes an update at the end of the recommendation:

```
Routing selected: {path}
This partition type is not in the map for archetype {name}. Add it?

Y) Add as new partition entry to {archetype} — future runs will know about it
N) Skip — one-off use only
```

Approved updates append a new row to the archetype's partitions table. The user can also reject the growth if the new partition should remain ad-hoc.
