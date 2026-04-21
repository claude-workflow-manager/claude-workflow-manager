#!/usr/bin/env bash
#
# install.sh — Workflow Manager clone-path installer (macOS / Linux)
#
# Copies commands, skills, hooks, and rules from the cloned repo into
# the user's ~/.claude/ directory. Detects deps and prints guided install
# commands when a dep is missing.
#
# FIN-008 — dep handling is hybrid: guided messages, never auto-installs.
# FIN-007 — user shadow files at ~/.claude/ take precedence; install does
#           not clobber existing user content outside WM-owned subdirs.
#
# Usage:
#   ./install.sh              # install
#   DRY_RUN=1 ./install.sh    # print operations without executing

set -euo pipefail

# Resolve script directory so we can source helpers and source content.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# run CMD [ARGS...] — execute or print depending on DRY_RUN
run() {
  if [ "${DRY_RUN:-}" = "1" ]; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# 1. OS detection
# ---------------------------------------------------------------------------

OS="$(uname -s)"
case "$OS" in
  Darwin)
    OS_LABEL="macOS"
    ;;
  Linux)
    OS_LABEL="Linux"
    ;;
  *)
    echo "Error: unsupported OS '$OS'. install.sh supports macOS and Linux only." >&2
    exit 1
    ;;
esac

echo "Detected OS: $OS_LABEL"

# ---------------------------------------------------------------------------
# 2a. Dependency check — git (REQUIRED)
# ---------------------------------------------------------------------------

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required but not installed." >&2
  if [ "$OS" = "Darwin" ]; then
    echo "Install git via Homebrew (https://brew.sh):" >&2
    echo "  brew install git" >&2
  else
    # Linux — detect distro
    DISTRO_ID=""
    if [ -f /etc/os-release ]; then
      DISTRO_ID="$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]')"
    fi
    case "$DISTRO_ID" in
      ubuntu|debian)
        echo "Install git via apt:" >&2
        echo "  sudo apt install git" >&2
        ;;
      fedora)
        echo "Install git via dnf:" >&2
        echo "  sudo dnf install git" >&2
        ;;
      arch)
        echo "Install git via pacman:" >&2
        echo "  sudo pacman -S git" >&2
        ;;
      *)
        echo "Install git from: https://git-scm.com/downloads" >&2
        ;;
    esac
  fi
  exit 127
fi

# ---------------------------------------------------------------------------
# 2b. Dependency check — python3 (OPTIONAL)
# ---------------------------------------------------------------------------

if [ -f "$SCRIPT_DIR/skills/wm/lib/check-python.sh" ]; then
  # shellcheck source=skills/wm/lib/check-python.sh
  source "$SCRIPT_DIR/skills/wm/lib/check-python.sh"
  if ! wm_check_python; then
    echo "Python 3.x is optional — required only for /wm:doc-graph. Continuing." >&2
  fi
else
  echo "Warning: Python dep-check helper missing at skills/wm/lib/check-python.sh" >&2
fi

# ---------------------------------------------------------------------------
# 3. Determine install target
# ---------------------------------------------------------------------------

# Honor $HOME for sandboxed installs (e.g. HOME=/tmp/wm-dev-home ./install.sh)
CLAUDE_DIR="${HOME}/.claude"

echo "Install target: $CLAUDE_DIR"

# ---------------------------------------------------------------------------
# 4. Create target subdirectories
# ---------------------------------------------------------------------------

run mkdir -p \
  "$CLAUDE_DIR/commands/wm" \
  "$CLAUDE_DIR/skills/wm" \
  "$CLAUDE_DIR/hooks" \
  "$CLAUDE_DIR/rules"

# ---------------------------------------------------------------------------
# 5. Copy WM-owned subdirectories
#
# rsync --delete removes stale files only inside the named WM-owned subdir.
# $HOME/.claude/settings.json, CLAUDE.md, AGENTS.md, hook-state/, and all
# other top-level user files are never touched (FIN-007).
# ---------------------------------------------------------------------------

if command -v rsync >/dev/null 2>&1; then
  run rsync -a --delete "$SCRIPT_DIR/commands/wm/" "$CLAUDE_DIR/commands/wm/"
  run rsync -a --delete "$SCRIPT_DIR/skills/wm/"   "$CLAUDE_DIR/skills/wm/"
  run rsync -a --delete "$SCRIPT_DIR/hooks/"       "$CLAUDE_DIR/hooks/"
  run rsync -a --delete "$SCRIPT_DIR/rules/"       "$CLAUDE_DIR/rules/"
else
  # cp -R without --delete; stale files may linger on reinstall without rsync.
  run cp -R "$SCRIPT_DIR/commands/wm/." "$CLAUDE_DIR/commands/wm/"
  run cp -R "$SCRIPT_DIR/skills/wm/."   "$CLAUDE_DIR/skills/wm/"
  run cp -R "$SCRIPT_DIR/hooks/."       "$CLAUDE_DIR/hooks/"
  run cp -R "$SCRIPT_DIR/rules/."       "$CLAUDE_DIR/rules/"
fi

# ---------------------------------------------------------------------------
# 6. Set executable bits on hooks and the Python helper
# ---------------------------------------------------------------------------

run chmod +x "$CLAUDE_DIR/hooks/"*.sh "$CLAUDE_DIR/hooks/"*.py 2>/dev/null || true
run chmod +x "$CLAUDE_DIR/skills/wm/lib/check-python.sh" 2>/dev/null || true

# ---------------------------------------------------------------------------
# 7. Done
# ---------------------------------------------------------------------------

echo ""
echo "Workflow Manager installed to: $CLAUDE_DIR"
echo "Run /wm:status in Claude Code to verify."
