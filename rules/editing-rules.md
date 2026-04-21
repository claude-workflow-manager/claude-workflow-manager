# Editing Rules

Active during: file modifications, code changes, refactoring.

1. **Don't change what wasn't asked.** No drive-by refactors, no "while I'm here" improvements.
2. **Propose before changing.** Never edit files without approval. Present what you want to change, explain why, wait for confirmation. Exception: user explicitly asks for a specific described change.
3. **Verify before claiming done.** Run the check, read the output. Don't assume it passed.
4. **Simplicity first.** Prefer the simplest solution. Three similar lines > a premature abstraction. One clear file > three "well-organized" files.
5. **Root causes, not patches.** When something breaks, diagnose why. A proper fix now saves three debugging sessions later.
6. **Respect .gitignore.** Only stage files shown by `git status`. Never `git add -f`.
