<purpose>
Show current workflow status across all active projects. Read-only — does not change state.
</purpose>

<required_reading>
@~/.claude/rules/communication-rules.md
</required_reading>

<process>
<step name="Step 1 — Find projects">
Detect `projects/` location (current dir → parent). Read `projects/ACTIVE.md`.

If missing or empty: "No active projects." STOP.
</step>

<step name="Step 2 — Show project summary">
For each project in ACTIVE.md, read `projects/{name}/STATE.md` and summarize: name, work type, current state, last session, and the recommended next command. Pick a compact shape (table, pipe-separated line, or bulleted) — presentation follows communication rules.
</step>

<step name="Step 3 — Single project detail (if only one)">
If there's only one active project, also show:
- DECISIONS.md entry count and how many are `applied` vs `pending`
- Plan progress if state is `executing` (tasks done / total from plan file)
- Handoff summary (next action from handoff.md)
- Skips logged (if any)
</step>

<step name="Step 4 — Shadowed files">
Detect user-overridden plugin files and flag upstream drift.

**What a shadow is:** A shadow exists when a file from the WM plugin is also present at `$HOME/.claude/<rel_path>`, meaning the user's copy takes precedence over the plugin default.

**4.1 — Determine plugin root.**
Read `WM_ROOT` env variable. If unset, fall back to `~/.claude/skills/wm`.

**4.2 — Enumerate plugin files.**
Walk the plugin root and collect all files under:
- `rules/`
- `skills/wm/` (excluding `archive/` subtrees)
- `hooks/`
- `commands/wm/`

Use Bash + standard Unix tools: `find <plugin_root> -type f` filtered to those four subtrees. On Windows, substitute `dir /s /b` or use Python's `pathlib.Path.rglob`.

**4.3 — For each plugin file, check for a shadow.**
The shadow path is `$HOME/.claude/<rel_path>`, where `<rel_path>` is the file's path relative to the plugin root. Use the `_wm_resolve()` resolver from Step 3c if available; otherwise construct the path directly.

If the shadow does **not** exist: file is plugin-default. Do not list it.

**4.4 — If shadow exists, classify drift.**
Compare the plugin file and shadow file:

1. Compute content hashes: `md5sum <file>` on Unix; `CertUtil -hashfile <file> MD5` on Windows; or `python -c "import hashlib,sys; print(hashlib.md5(open(sys.argv[1],'rb').read()).hexdigest())" <file>` cross-platform.
2. Get mtimes: `stat -c %Y <file>` on Linux; `stat -f %m <file>` on macOS; `python -c "import os,sys; print(int(os.path.getmtime(sys.argv[1])))" <file>` cross-platform.

Classify each shadow as one of:
- **No drift** — hashes match (user copied but did not modify; note as "shadow present, no drift from plugin version at copy time").
- **`upstream-newer`** — hashes differ AND plugin file mtime is newer than shadow mtime. The plugin was updated after the user created their shadow; user's copy may be stale.
- **`customized`** — hashes differ AND shadow mtime is newer than plugin file mtime. User is actively iterating their own version.

Compute the mtime diff in days: `abs(plugin_mtime - shadow_mtime) / 86400`, rounded to nearest integer.

**4.5 — Render the section.**

Add a "Shadowed files" section. If no shadows exist, say so in one line. If shadows exist, show three columns of information per shadow: path (relative from the plugin root), the full expanded shadow path, and the drift classification (format: `—` for no drift, `upstream-newer (mtime diff: Nd)`, or `customized (mtime diff: Nd)`). A table is typically the right fit for this structured data; the exact column order and layout are presentation choices — follow communication rules.

Place this section after the single-project detail block and before any next-step or routing suggestion.
</step>
</process>
