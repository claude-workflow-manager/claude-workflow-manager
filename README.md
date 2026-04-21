# Workflow Manager for Claude Code

A structured workflow manager — discovery, planning, execution, and release, with explicit state and gates.

---

## Install

### Option A: Claude Code plugin (recommended)

```
/plugin marketplace add claude-workflow-manager/claude-workflow-manager-marketplace
/plugin install workflow-manager
```

> `claude-workflow-manager` is resolved at Step 5a (GitHub org decision). Update this placeholder before first public release.

### Option B: Git clone (for contributors)

```bash
git clone https://github.com/claude-workflow-manager/claude-workflow-manager.git
cd claude-workflow-manager
./install.sh
```

On Windows, use `.\install.ps1` instead of `./install.sh`.

> `claude-workflow-manager` is resolved at Step 5a. Update this placeholder before first public release.

---

## Quickstart

After installing, open Claude Code and run:

```
/wm:status
```

This confirms WM is active and shows the current workflow state. To start a new project:

```
/wm:new-project
```

WM will guide you through naming the project and entering the discovery stage.

---

## What WM does

WM structures your work in Claude Code across six core commands:

- `/wm:discover` — Enter discovery: open conversation as a thinking partner, then structured gray-area exploration. Produces a design doc and decision log.
- `/wm:plan` — Enter planning: enforce decision gates, archive the previous version, produce a step-by-step T1/T2 plan.
- `/wm:verify-plan` — Verify the plan before execution: coverage check, approach soundness, gate compliance. Hard gate — requires your approval.
- `/wm:execute` — Enter execution: step through the approved plan, delegate subagents, track progress against Done-when criteria.
- `/wm:verify` — Verify the implementation after execution: checks Done-when criteria against actual files and behavior. Hard gate — requires your approval.
- `/wm:release` — Run the release: version bump, changelog, project archiving, and (when configured) publish to the public repo.

Additional commands: `/wm:status`, `/wm:new-project`, `/wm:resume`, `/wm:save`, `/wm:next`, `/wm:change`, `/wm:skip`, `/wm:abandon`, `/wm:clean-up`, `/wm:learn`, `/wm:doc-graph`, `/wm:code-graph`.

---

## Customization

WM uses a shadow-to-customize model. Every WM file has a default in the plugin install location. To override any file, copy it to the same relative path under `~/.claude/`:

```
# Example: override the discovery rules
cp <plugin-root>/rules/discovery-rules.md ~/.claude/rules/discovery-rules.md
# Edit ~/.claude/rules/discovery-rules.md — your copy takes precedence
```

When WM resolves a file, it checks `~/.claude/` first. Your shadow is never touched by plugin updates. Non-shadowed files update automatically via `/plugin marketplace update`.

Run `/wm:status` to see which files you have shadowed and whether any have upstream drift (the plugin default was updated after you copied).

---

## Requirements

| Dependency | Required | Notes |
|---|---|---|
| Claude Code | Always | Plugin system or manual install |
| git | Always | Used by install scripts and `/wm:release` |
| bash or PowerShell | Always (clone path) | `install.sh` (bash) or `install.ps1` (PowerShell) |
| Python 3.x | Optional | Only needed for `/wm:doc-graph`. Missing Python prints a guided install message; all other WM commands work without it. |

---

## License

MIT. See [LICENSE](LICENSE).

---

## Links

- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- Changelog — see `skills/wm/CHANGELOG.md` in the repo
