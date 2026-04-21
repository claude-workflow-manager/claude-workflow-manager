#!/usr/bin/env bash
# Shared Python 3.x availability check for Workflow Manager.
# Sourced by install.sh and /wm:doc-graph runtime dispatcher.
# Prints guided install message on miss; silent on present.
# Realizes FIN-008 plugin-path runtime guard.

set -u

wm_check_python() {
  local version_out minor cmd
  # Try python3 (macOS / Linux canonical) first, then python (Windows default).
  for cmd in python3 python; do
    if command -v "$cmd" > /dev/null 2>&1; then
      version_out="$("$cmd" --version 2>&1)"
      # Accept any Python 3.8+ regardless of minor version (3.8, 3.9, 3.10, ... 3.99+).
      minor="$(echo "$version_out" | sed -nE 's/^Python 3\.([0-9]+).*/\1/p')"
      if [ -n "$minor" ] && [ "$minor" -ge 8 ] 2>/dev/null; then
        return 0
      fi
    fi
  done

  # Python 3.8+ not found — detect OS and print guided install message
  local os
  os="$(uname -s 2>/dev/null || echo unknown)"

  if [ "$os" = "Darwin" ]; then
    echo "Python 3.8+ not found. Install via Homebrew:" >&2
    echo "  brew install python@3.11" >&2
    echo "  (Install Homebrew first if absent: https://brew.sh)" >&2
  elif [ "$os" = "Linux" ]; then
    local distro_id=""
    if [ -f /etc/os-release ]; then
      distro_id="$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]')"
    fi
    case "$distro_id" in
      ubuntu|debian)
        echo "Python 3.8+ not found. Install via apt:" >&2
        echo "  sudo apt update && sudo apt install python3 python3-venv" >&2
        ;;
      fedora)
        echo "Python 3.8+ not found. Install via dnf:" >&2
        echo "  sudo dnf install python3" >&2
        ;;
      arch)
        echo "Python 3.8+ not found. Install via pacman:" >&2
        echo "  sudo pacman -S python" >&2
        ;;
      *)
        echo "Python 3.8+ not found. Install from:" >&2
        echo "  https://www.python.org/downloads/" >&2
        ;;
    esac
  else
    echo "Python 3.8+ not found. Install from:" >&2
    echo "  https://www.python.org/downloads/" >&2
  fi

  return 127
}

# Standalone mode: run and exit. Sourced mode: only define the function.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  wm_check_python
  exit $?
fi
