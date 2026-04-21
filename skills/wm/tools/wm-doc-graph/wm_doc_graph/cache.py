"""Mtime-based incremental rebuild for the wm-doc-graph cache (FIN-007).

Tech spec §7: load the YAML cache, stat every markdown file under cwd,
re-parse only entries whose mtime changed, drop entries for files that
disappeared, merge with untouched entries, write back. Corruption and
schema-version mismatches trigger an automatic full rebuild with a
stderr warning (emitted by `store.load_graph`).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from . import __version__
from .builder import build_graph, iter_markdown_files, parse_file
from .schema import (
    DEFAULT_CACHE_FILENAME,
    GENERATOR_NAME,
    KEY_FILES,
    KEY_GENERATED_AT,
    KEY_GENERATOR,
    KEY_GENERATOR_VERSION,
    KEY_MTIME,
    KEY_PATH,
    KEY_ROOT,
    KEY_SCHEMA_VERSION,
    SCHEMA_VERSION,
)
from .store import load_graph, save_graph


def default_cache_path(root: Path) -> Path:
    return root / DEFAULT_CACHE_FILENAME


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _full_rebuild(root: Path, cache_path: Path) -> tuple[dict, dict]:
    graph = build_graph(root)
    save_graph(graph, cache_path)
    stats = {
        "parsed": len(graph[KEY_FILES]),
        "kept": 0,
        "deleted": 0,
        "cold": True,
    }
    return graph, stats


def ensure_graph(
    root: Path,
    force: bool = False,
    cache_path: Path | None = None,
    verbose: bool = False,
) -> tuple[dict, dict]:
    """Load cache, incrementally rebuild as needed, save, return (graph, stats).

    Behavior:
    - `force=True`: skip the cache, do a full rebuild.
    - Missing cache: full rebuild (cold start).
    - Corrupt or version-mismatched cache: full rebuild (warning emitted
      by `store.load_graph`).
    - Otherwise: stat every markdown file under `root`, re-parse only files
      whose mtime no longer equals the cached value, drop entries that no
      longer exist, merge, save.

    Stats dict shape:
        {"parsed": int,   # files parsed in this call
         "kept": int,     # cache entries reused unchanged
         "deleted": int,  # cache entries dropped (file vanished)
         "cold": bool}    # True when a full rebuild happened
    """
    root = root.resolve()
    if cache_path is None:
        cache_path = default_cache_path(root)

    if force:
        return _full_rebuild(root, cache_path)

    old = load_graph(cache_path)
    if old is None or old.get(KEY_SCHEMA_VERSION) != SCHEMA_VERSION:
        return _full_rebuild(root, cache_path)

    old_files_by_path: dict[str, dict] = {
        f[KEY_PATH]: f for f in old.get(KEY_FILES, []) if KEY_PATH in f
    }

    current_paths: dict[str, Path] = {}
    for path in iter_markdown_files(root):
        try:
            rel = path.resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        current_paths[rel] = path

    kept: list[dict] = []
    changed: list[Path] = []
    for rel, abs_path in current_paths.items():
        try:
            mtime = int(abs_path.stat().st_mtime)
        except OSError:
            continue
        cached_entry = old_files_by_path.get(rel)
        # `!=` rather than `<` so backdated edits (e.g. restored from a
        # backup with an older mtime) still trigger a re-parse.
        if cached_entry is None or cached_entry.get(KEY_MTIME) != mtime:
            changed.append(abs_path)
        else:
            kept.append(cached_entry)

    deleted_rels = set(old_files_by_path.keys()) - set(current_paths.keys())

    # Fast-path: nothing changed and nothing deleted — return the loaded
    # graph unchanged and skip the YAML round-trip. Steady-state invocations
    # hit this path and stay well under the 100ms target from tech spec §7.
    if not changed and not deleted_rels:
        stats = {
            "parsed": 0,
            "kept": len(kept),
            "deleted": 0,
            "cold": False,
        }
        if verbose:
            print(
                f"wm-doc-graph: 0 re-parsed, 0 removed, {stats['kept']} unchanged",
                file=sys.stderr,
            )
        return old, stats

    reparsed: list[dict] = []
    for path in changed:
        entry = parse_file(path, root)
        if entry is not None:
            reparsed.append(entry)

    merged = sorted(kept + reparsed, key=lambda f: f[KEY_PATH])

    graph = {
        KEY_SCHEMA_VERSION: SCHEMA_VERSION,
        KEY_GENERATED_AT: _now_iso(),
        KEY_GENERATOR: GENERATOR_NAME,
        KEY_GENERATOR_VERSION: __version__,
        KEY_ROOT: str(root),
        KEY_FILES: merged,
    }

    save_graph(graph, cache_path)

    stats = {
        "parsed": len(reparsed),
        "kept": len(kept),
        "deleted": len(deleted_rels),
        "cold": False,
    }

    if verbose:
        print(
            f"wm-doc-graph: {stats['parsed']} re-parsed, "
            f"{stats['deleted']} removed, "
            f"{stats['kept']} unchanged",
            file=sys.stderr,
        )

    return graph, stats
