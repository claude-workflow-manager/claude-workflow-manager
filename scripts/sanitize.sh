#!/usr/bin/env bash
# sanitize.sh — pre-publish sanitization gate (FIN-002)
# Usage: bash scripts/sanitize.sh
# Run from the repo root. Exits 0 if clean, 1 if any findings.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "Running sanitization scan..."
echo "Repo root: $REPO_ROOT"
echo ""

# ---------------------------------------------------------------------------
# 1. Dependency check — gitleaks
# ---------------------------------------------------------------------------

if ! command -v gitleaks &>/dev/null; then
    echo "ERROR: 'gitleaks' not found in PATH."
    echo ""
    echo "Install gitleaks for your OS:"
    echo "  macOS:          brew install gitleaks"
    echo "  Debian/Ubuntu:  sudo apt install gitleaks"
    echo "                  (if not in repos: https://github.com/gitleaks/gitleaks/releases)"
    echo "  Windows:        winget install gitleaks"
    echo ""
    exit 127
fi

# ---------------------------------------------------------------------------
# 2. gitleaks scan
# ---------------------------------------------------------------------------

GITLEAKS_EXIT=0
echo "--- gitleaks detect ---"
gitleaks detect \
    --source . \
    --config .gitleaks.toml \
    --no-git \
    --verbose \
    || GITLEAKS_EXIT=$?

echo ""

# ---------------------------------------------------------------------------
# 3. Secondary grep sweep — WM-specific patterns that may slip through
#
#    Pattern: match "Tomasz" ONLY when preceded by a path separator
#    (/ or \). This catches personal paths like "C:\Users\Tomasz\..."
#    or "/home/Tomasz/..." without flagging intentional maintainer
#    attribution ("Tomasz Maciag" in LICENSE, plugin.json, README).
# ---------------------------------------------------------------------------

GREP_EXIT=0
echo "--- grep sweep (personal path identifiers) ---"

GREP_HITS=$(
    grep -rnE \
        --include='*.md' \
        --include='*.py' \
        --include='*.sh' \
        --include='*.json' \
        --include='*.toml' \
        '[/\\]Tomasz' . 2>/dev/null \
    | grep -v -E '^(\.\/projects\/|\.\/scratch\/|\.\/\.git\/|\.\/memory\/|\.\/skills\/wm\/archive\/|\.\/scripts\/sanitize\.sh|\.\/\.gitleaks\.toml)' \
    || true
)

if [[ -n "$GREP_HITS" ]]; then
    echo "FINDINGS — personal identifier 'Tomasz' detected in tracked files:"
    echo "$GREP_HITS"
    GREP_EXIT=1
else
    echo "grep sweep: clean"
fi

echo ""

# ---------------------------------------------------------------------------
# 4. Final result
# ---------------------------------------------------------------------------

if [[ "$GITLEAKS_EXIT" -ne 0 || "$GREP_EXIT" -ne 0 ]]; then
    echo "Sanitization scan: FAILED — review findings above before public push."
    exit 1
fi

echo "Sanitization scan: clean."
exit 0
