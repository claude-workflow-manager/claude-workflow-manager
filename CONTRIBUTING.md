# Contributing to Workflow Manager

Thank you for your interest in contributing. WM is a structured workflow tool for Claude Code — contributions that improve clarity, reliability, or portability are welcome.

---

## Scope of contributions

In scope:
- Bug fixes in commands, skills, hooks, and the `wm-doc-graph` Python tool
- Documentation improvements (clearer install steps, better command descriptions)
- Portability fixes (Windows/macOS/Linux compatibility)
- New workflow primitives that fit within the existing gate-based model

Out of scope for v1.0.0:
- Rewriting WM's core architecture (state machine, gate matrix, workflow semantics)
- Migrating WM to a compiled language or package manager format
- Auto-installing system-level dependencies (Python, git)

If you are unsure whether a change fits, open an issue before submitting a PR.

---

## Local dev setup

1. Fork and clone the repo:
   ```bash
   git clone https://github.com/claude-workflow-manager/claude-workflow-manager.git
   cd claude-workflow-manager
   ```

2. Install into a sandboxed `HOME` to avoid touching your real `~/.claude/`:
   ```bash
   mkdir -p /tmp/wm-dev-home
   HOME=/tmp/wm-dev-home ./install.sh
   ```
   On Windows:
   ```powershell
   $env:HOME = "C:\Temp\wm-dev-home"; New-Item -ItemType Directory -Force $env:HOME
   .\install.ps1
   ```

3. Open Claude Code pointing at the sandboxed home and run `/wm:status` to confirm install.

4. Make your changes in the cloned repo, then re-run `install.sh` (or `install.ps1`) to sync into the sandbox.

5. To iterate on a release-style workflow locally, run `/wm:release` inside Claude Code — it runs against the active project, reads from the sandboxed `~/.claude/`, and does not push to any remote unless you have configured the `public` git remote.

### Maintainer-only dependency: `gitleaks`

`/wm:release` runs a sanitization gate that requires `gitleaks` to be installed. Install once:

- **macOS:** `brew install gitleaks`
- **Ubuntu/Debian:** `sudo apt install gitleaks` (or download from https://github.com/gitleaks/gitleaks/releases if not in repos)
- **Windows:** `winget install gitleaks`

`gitleaks` is **only** needed by maintainers running `/wm:release`. End users installing via the plugin or clone path do not need it.

If `gitleaks` is missing, `/wm:release` will block with a guided install message. This is intentional — the sanitization gate is strict by design to prevent accidental secret leaks on public push.

---

## PR flow

**Branch naming:**
```
fix/<short-description>
feat/<short-description>
docs/<short-description>
chore/<short-description>
```

**Commit message style** — short, prefixed:
```
fix: correct path resolver fallback when WM_ROOT is unset
feat: add /wm:learn command for capturing session lessons
docs: clarify install steps for Windows users
chore: update Contributor Covenant to v2.1
```

**Testing expectations:**
- For hook changes: confirm the hook fires correctly in a sandboxed install. For Python tool changes: run `python -m pytest` in `skills/wm/tools/wm-doc-graph/` if tests exist.
- For workflow changes: manually invoke the affected `/wm:*` command in a sandboxed Claude Code session and confirm expected behavior.
- For install script changes: test on at least one platform (macOS/Linux via bash, or Windows via PowerShell). Note the platform in the PR description.

**PR description:** Include what changed, why, and how you tested it.

---

## Code of conduct

All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.
