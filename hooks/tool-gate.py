#!/usr/bin/env python3
"""PreToolUse/PostToolUse hook — ensures files are investigated before editing.

Two modes (sys.argv[1]):
  track — PostToolUse on Read|Grep|Glob|MCP: record investigated files
  gate  — PreToolUse on Write|Edit: check if target was investigated

Sidecar: ~/.claude/hook-state/tool-gate-{session_id}.json
FIN-002, FIN-013, FIN-018
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def _wm_root() -> Path:
    """Resolve the Workflow Manager plugin root.

    Priority:
    1. WM_ROOT environment variable (set by Claude Code plugin loader)
    2. Fallback: ~/.claude/skills/wm (legacy clone-install location)
    """
    env = os.environ.get("WM_ROOT")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "skills" / "wm"


def _wm_rule_path(rule_name: str) -> Path:
    """Resolve a rules file, preferring user shadow over plugin default."""
    user_shadow = Path.home() / ".claude" / "rules" / rule_name
    if user_shadow.exists():
        return user_shadow
    root = _wm_root()
    for candidate in [root.parent / "rules" / rule_name, root / "rules" / rule_name]:
        if candidate.exists():
            return candidate
    return user_shadow


MODE = "warn"  # "warn" or "enforce"
STATE_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hook-state")
WARNINGS_LOG = os.path.join(STATE_DIR, "tool-gate-warnings.log")


def state_path(sid):
    return os.path.join(STATE_DIR, f"tool-gate-{sid}.json")


def load_state(sid):
    fp = state_path(sid)
    try:
        if os.path.exists(fp):
            with open(fp, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"investigated": {}, "code_graph_used": False}


def save_state(sid, state):
    os.makedirs(STATE_DIR, exist_ok=True)
    fp = state_path(sid)
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, fp)


def norm(p):
    """Normalize path for cross-platform comparison."""
    return os.path.normpath(p).replace("\\", "/").lower()


def log_warning(msg):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(WARNINGS_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")


# -- Track mode (PostToolUse) ------------------------------------------------

def handle_track(data):
    sid = data.get("session_id", "")
    if not sid:
        print("{}")
        return

    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {})
    paths = set()

    if tool == "Read":
        fp = inp.get("file_path", "")
        if fp:
            paths.add(norm(fp))

    elif tool in ("Write", "Edit", "MultiEdit"):
        fp = inp.get("file_path", "")
        if fp:
            paths.add(norm(fp))

    elif tool in ("Grep", "Glob"):
        # Search path counts as investigated area
        p = inp.get("path", "")
        if p:
            paths.add(norm(p))
        # Try to extract matched file paths from response
        resp = data.get("tool_response", "")
        if isinstance(resp, str):
            for line in resp.splitlines():
                line = line.strip()
                if line and len(line) < 300 and ("/" in line or "\\" in line):
                    candidate = line.split(":")[0] if ":" in line else line
                    paths.add(norm(candidate))

    elif "code" in tool.lower() or "graph" in tool.lower():
        # Code graph MCP query — global gate bypass
        state = load_state(sid)
        state["code_graph_used"] = True
        save_state(sid, state)
        print("{}")
        return

    if paths:
        state = load_state(sid)
        for p in paths:
            state["investigated"][p] = True
        save_state(sid, state)

    print("{}")


# -- Gate mode (PreToolUse) ---------------------------------------------------

def handle_gate(data):
    sid = data.get("session_id", "")
    inp = data.get("tool_input", {})
    file_path = inp.get("file_path", "")

    if not sid or not file_path:
        emit_allow()
        return

    # New file creation — no investigation required
    try:
        if not os.path.exists(file_path):
            emit_allow()
            return
    except Exception:
        emit_allow()
        return

    state = load_state(sid)

    # Code graph query bypasses gate for all files
    if state.get("code_graph_used"):
        emit_allow()
        return

    # Check if file or parent was investigated
    target = norm(file_path)
    for inv in state.get("investigated", {}):
        if target == inv or target.startswith(inv + "/"):
            emit_allow()
            return

    # Not investigated
    if MODE == "enforce":
        reason = (
            f"BLOCKED: File not investigated before editing: {file_path}. "
            "Read the file or query the code graph first."
        )
        log_warning(f"ENFORCE {file_path}")
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }, sys.stdout)
    else:
        msg = f"Writing to uninvestigated file: {file_path}. Consider reading it first."
        log_warning(f"WARN {file_path}")
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": f"[tool-gate warning] {msg}",
            }
        }, sys.stdout)


def emit_allow():
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
        }
    }, sys.stdout)


# -- Main --------------------------------------------------------------------

def main():
    try:
        data = json.load(sys.stdin)
        mode = sys.argv[1] if len(sys.argv) > 1 else ""
        if mode == "track":
            handle_track(data)
        elif mode == "gate":
            handle_gate(data)
        else:
            print("{}")
    except Exception:
        # On error, always allow — never block work due to hook crash
        emit_allow()


if __name__ == "__main__":
    main()
