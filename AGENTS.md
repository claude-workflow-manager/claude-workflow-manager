# AGENTS.md - Project Constitution

## Project Identity

**Project:** Workflow Manager
**Purpose:** Develop and release new versions of the WM commands and skills

## Workflow
framework: "superpowers"

## Agent Rules

Rules are scoped by activity in `rules/`:
- `discovery-rules.md` — decision-making, evaluating options
- `execution-rules.md` — delegation, context management, structural navigation
- `editing-rules.md` — change discipline, verification, simplicity
- `review-rules.md` — critical evaluation, self-challenge
- `communication-rules.md` — the 11 global communication rules (authoritative)

---

## Project Structure

**This is a dev project.** Dev repo is the source of truth. Production is a deploy target only.

- **All edits** go to files in this repo first
- **Never edit production directly** (`~/.claude/commands/wm/`, `~/.claude/skills/wm/`, or `~/.claude/AGENTS.md`)
- **`/wm:release`** deploys dev → production (commands, skills, and global files)

```
<repo-root>/                             # Dev repo (source of truth)
├── commands/wm/                         # Command files (thin triggers)
├── skills/wm/                           # Skill files
│   ├── workflows/                       # Workflow logic (1:1 with commands)
│   ├── references/                      # Config/lookup tables
│   ├── VERSION                          # Current version
│   ├── CHANGELOG.md                     # Release history
│   └── DESIGN-DECISIONS.md              # Accumulated design decisions
├── hooks/                               # Hook scripts (deployed to ~/.claude/hooks/)
├── rules/                               # Scoped agent rules (deployed to ~/.claude/rules/)
├── projects/                            # WM project scaffold (gitignored)
├── AGENTS.md                            # This file
└── .gitignore

Production (deploy target — DO NOT EDIT DIRECTLY):
├── ~/.claude/commands/wm/ # Deployed command files
├── ~/.claude/skills/wm/   # Deployed skill files
└── ~/.claude/hooks/       # Deployed hook scripts
```
