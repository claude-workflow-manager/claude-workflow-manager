# PRD — Universal Handoff & Adaptive Artifact Routing

## 1. Introduction/Overview

The WM workflow currently requires an active project for `save`/`resume` to work, and only generates PRD + tech spec for `app` work type. This leaves two gaps:
1. Users lose session context when working outside a formal project
2. Tools, agents, and other non-app work types miss out on structured requirements documents that would improve their design

This enhancement makes handoff universal (works with or without a project) and makes PRD/tech spec generation adaptive based on project characteristics rather than a hard work-type rule.

## 2. Goals

1. `save` and `resume` work in any session — with or without an active project
2. PRD/tech spec generation is guided by project characteristics, not just work type
3. Zero friction added to existing workflows — project-based save/resume unchanged

## 3. User Stories

1. As a user working on a quick ad-hoc task, I can run `/wm:save` and later `/wm:resume` to pick up where I left off — without creating a formal project first.
2. As a user building a new CLI tool (work type `new`), I get a PRD during discovery because the agent recognizes user-facing behavior that benefits from structured requirements.
3. As a user doing a simple bug fix, the agent skips PRD/spec because the scope doesn't warrant it — no unnecessary ceremony.

## 4. Functional Requirements

1. **Scratch handoff on save:** When no active project exists, `save` writes `scratch/handoff.md` with session context. No git commit. No confirmation prompt.
2. **Scratch handoff overwrite:** Subsequent saves without a project overwrite `scratch/handoff.md` silently.
3. **Resume detects scratch:** `resume` checks both `projects/ACTIVE.md` and `scratch/handoff.md`. If both exist, shows unified list with scratch marked separately at the bottom. If only scratch exists, loads it directly.
4. **Handoff content is freeform:** Agent decides what to capture — no fixed template for scratch. Goal is enough context to resume in a new session.
5. **Adaptive PRD proposal:** During discovery, agent assesses whether a PRD would benefit the project (user-facing behavior, scope needing bounds). If yes, proposes with reasoning and asks for confirmation.
6. **Adaptive tech spec proposal:** Same logic — agent proposes tech spec when non-trivial architecture, integrations, or data models are involved. Proposes and asks.
7. **Guidance not rules:** Discovery instructions include heuristics (PRD common for `app`/`new`/`new-agent`, tech spec common for `app`) but agent can propose or skip for any work type based on context.
8. **Adaptive version detection:** `plan` gate auto-detects version source (VERSION, package.json, PROJECT.md, pyproject.toml) in the target directory. Records `Version source:` path in DECISIONS.md header. If no version file found, offers to create one, point to a file, or skip. `release` writes bumped version back to the detected source.

## 5. Non-Goals

1. No state machine tracking for scratch sessions — no STATE.md, DECISIONS.md, or ACTIVE.md row
2. No git integration for scratch — `scratch/` stays gitignored
3. No changes to project-based save/resume — existing workflow untouched
4. No auto-creation of projects from scratch sessions

## 6. Design Considerations

1. Resume list format separates projects from scratch with a visual divider (`---`)
2. Scratch entry uses `S)` label, not a number — avoids confusion with project indices
3. Agent's PRD/spec proposal during discovery should be conversational: "This has X, I'd recommend a PRD. Want one?" — not a checkbox or form

## 7. Technical Considerations

- `scratch/` is already in `.gitignore` — no changes needed
- `save` needs a new code path: detect no active project → write scratch handoff
- `resume` needs to check `scratch/handoff.md` in addition to `projects/ACTIVE.md`
- `discover` instructions need updated artifact routing — replace hard work-type check with guidance heuristics
- `plan` gate needs adaptive version detection — scan for VERSION, package.json, PROJECT.md, pyproject.toml

## 8. Success Metrics

1. `/wm:save` succeeds with no active project — `scratch/handoff.md` written
2. `/wm:resume` finds and offers scratch handoff alongside projects
3. During discovery for a `new` work type, agent proposes PRD when appropriate
4. Existing project-based workflows unchanged
5. `plan` gate detects version from multiple formats and proposes bump

## 9. Open Questions

(none — all gray areas resolved during discovery)
