#!/usr/bin/env python3
"""UserPromptSubmit hook — warns when context usage crosses 40% ceiling.

Parses the transcript JSONL (tail) to find the last assistant message's
usage field, sums input_tokens + cache_read + cache_creation, compares
to the model's context window, and warns when crossing 40% (and higher
thresholds). Only fires on upward crossings — no spam, no false alarms.

Sidecar: ~/.claude/hook-state/context-monitor-{session_id}.json
FIN-003, FIN-018
"""

import json
import os
import sys
import time
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


MODE = "warn"
STATE_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hook-state")

# User setting: set to your Claude Code context window size.
# Options: 200_000 (standard models) or 1_000_000 (Opus 1M context tier).
# The JSONL does not record the window size — Claude Code tracks it from
# session metadata hooks cannot see. Adjust this constant to match your setup.
USER_CONTEXT_WINDOW = 1_000_000

WARN_THRESHOLDS = [40, 50, 60, 70, 80, 90]
TAIL_BYTES = 32 * 1024  # Read last 32KB of transcript


def state_path(sid):
    return os.path.join(STATE_DIR, f"context-monitor-{sid}.json")


def load_state(sid):
    fp = state_path(sid)
    try:
        if os.path.exists(fp):
            with open(fp, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"count": 0, "last_pct": 0}


def save_state(sid, state):
    os.makedirs(STATE_DIR, exist_ok=True)
    fp = state_path(sid)
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, fp)


def sweep_stale():
    try:
        cutoff = time.time() - 7 * 86400
        for f in os.listdir(STATE_DIR):
            if f.startswith("context-monitor-") and f.endswith(".json"):
                fp = os.path.join(STATE_DIR, f)
                if os.path.getmtime(fp) < cutoff:
                    os.remove(fp)
    except Exception:
        pass


def read_last_assistant_tokens(transcript_path):
    """Tail the JSONL and return total tokens from the last assistant entry,
    or None if unavailable."""
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    try:
        size = os.path.getsize(transcript_path)
        read_size = min(size, TAIL_BYTES)
        with open(transcript_path, "rb") as f:
            if read_size < size:
                f.seek(-read_size, os.SEEK_END)
            tail = f.read().decode("utf-8", errors="ignore")

        for line in reversed(tail.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") != "assistant":
                continue
            usage = d.get("message", {}).get("usage", {})
            if not usage:
                continue

            return (
                usage.get("input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
            )
    except Exception:
        pass
    return None


def main():
    try:
        data = json.load(sys.stdin)
        sid = data.get("session_id", "")
        if not sid:
            print("{}")
            return

        state = load_state(sid)
        count = state.get("count", 0) + 1
        state["count"] = count

        if count == 1:
            sweep_stale()

        transcript_path = data.get("transcript_path", "")
        tokens = read_last_assistant_tokens(transcript_path)

        if tokens is None:
            # No assistant entry yet — first prompt of session
            save_state(sid, state)
            print("{}")
            return

        # Adaptive window: if tokens exceed configured window, bump to 1M.
        # Protects against misconfigured USER_CONTEXT_WINDOW.
        window = USER_CONTEXT_WINDOW
        if tokens > window:
            window = 1_000_000

        pct = (tokens / window) * 100
        last_pct = state.get("last_pct", 0)
        state["last_pct"] = pct

        # Warn only when we cross UP through a threshold
        crossed = [t for t in WARN_THRESHOLDS if last_pct < t <= pct]
        save_state(sid, state)

        if not crossed:
            print("{}")
            return

        highest = max(crossed)
        tokens_fmt = f"{tokens:,}"
        window_fmt = f"{window:,}"
        warning = (
            f"[context-monitor \u2014 {pct:.0f}% used "
            f"({tokens_fmt} / {window_fmt} tokens)]\n"
            f"Context usage has crossed the {highest}% threshold. "
            "Reasoning quality, instruction-following, and investigation depth "
            "degrade significantly beyond 40% context utilization. "
            "Consider running /wm:save to checkpoint and starting a fresh session.\n"
            "\n"
            "AGENT INSTRUCTION: The VS Code plugin does not render hook "
            "`systemMessage` as a visible UI notification. When you see this "
            "warning in your context, surface it at the very top of your next "
            "response as a visible warning block (blockquote or clearly marked "
            "banner with the percentage and token count) so the user sees it "
            "immediately. Do not bury it in narrative. Do this every time this "
            "warning appears, not just the first time, and continue surfacing "
            "subsequent crossings (50%, 60%, etc.) the same way."
        )

        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": warning,
                    "systemMessage": warning,
                }
            },
            sys.stdout,
        )

    except Exception:
        print("{}")


if __name__ == "__main__":
    main()
