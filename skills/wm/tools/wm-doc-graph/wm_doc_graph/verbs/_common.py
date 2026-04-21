"""Shared helpers for wm-doc-graph verb implementations.

FIN-008 enforcement, graph loading, entry lookup, and inverse-index
construction live here so every verb shares a single implementation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import NoReturn

from ..cache import ensure_graph
from ..schema import KEY_FILES, KEY_PATH, KEY_REFS_OUT


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
    """Resolve a rules file, preferring user shadow over plugin default.

    Priority:
    1. ~/.claude/rules/<rule_name>  (user shadow — always wins)
    2. <wm_root>/../rules/<rule_name>  (plugin-parent layout)
    3. <wm_root>/rules/<rule_name>    (plugin-embedded layout)
    Falls back to the user-shadow path (may not exist) when none found.
    """
    user_shadow = Path.home() / ".claude" / "rules" / rule_name
    if user_shadow.exists():
        return user_shadow
    root = _wm_root()
    for candidate in [root.parent / "rules" / rule_name, root / "rules" / rule_name]:
        if candidate.exists():
            return candidate
    return user_shadow


def _wm_resolve(rel_path: str) -> Path:
    """Resolve any plugin-bundled file, preferring user shadow.

    rel_path is relative to the WM skills-root (e.g. "references/templates.md").
    Resolves to ~/.claude/skills/wm/<rel_path> if that file exists (user shadow),
    otherwise falls back to the plugin default at <wm_root>/<rel_path>.
    """
    user_shadow = Path.home() / ".claude" / "skills" / "wm" / rel_path
    if user_shadow.exists():
        return user_shadow
    return _wm_root() / rel_path


def load_current_graph(root: Path) -> dict:
    """Run an incremental refresh and return the current graph."""
    graph, _ = ensure_graph(root)
    return graph


def fail(msg: str, code: int = 2) -> NoReturn:
    """Print an error to stderr and exit with `code`."""
    print(f"wm-doc-graph: error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def validate_in_repo(target: str, root: Path) -> str:
    """Resolve `target` relative to `root` and return the posix rel path.

    Exits non-zero with a clear error if the target escapes `root`
    (FIN-008: single-repo, cwd-scoped).
    """
    abs_path = (root / target).resolve()
    try:
        rel = abs_path.relative_to(root).as_posix()
    except ValueError:
        fail(f"path is outside cwd: {target}")
    return rel


def find_entry(graph: dict, rel_path: str) -> dict | None:
    """Look up a file entry by its posix-rel path. Returns None if absent."""
    for entry in graph.get(KEY_FILES, []):
        if entry.get(KEY_PATH) == rel_path:
            return entry
    return None


def build_inverse_index(graph: dict) -> dict[str, list[dict]]:
    """Compute refs_in from refs_out across every file in the graph.

    Keys are the raw target strings recorded in each source's refs_out
    (e.g. `~/.claude/skills/wm/foo.md` or `skills/wm/foo.md`). Values are
    lists of ``{source, line, kind}`` records. Callers match against
    these keys — exact, suffix, and basename matching all happen at the
    verb level because the target strings are not canonicalized at
    parse time (tech spec §11 Q2 — deliberate for v2.1 simplicity).
    """
    inverse: dict[str, list[dict]] = {}
    for entry in graph.get(KEY_FILES, []):
        source = entry.get(KEY_PATH, "")
        for ref in entry.get(KEY_REFS_OUT, []):
            target = ref.get("target", "")
            if not target:
                continue
            inverse.setdefault(target, []).append(
                {
                    "source": source,
                    "line": ref.get("line"),
                    "kind": ref.get("kind"),
                }
            )
    return inverse
