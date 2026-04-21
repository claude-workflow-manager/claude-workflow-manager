"""`build [--force]` verb — trigger cache build/refresh."""

from __future__ import annotations

from pathlib import Path

from ..cache import ensure_graph, default_cache_path


def run(args) -> int:
    root = Path.cwd()
    graph, stats = ensure_graph(root, force=args.force)
    cache_path = default_cache_path(root)

    mode = "cold" if stats["cold"] else "warm"
    print(
        f"wm-doc-graph: {mode} build complete — "
        f"{len(graph['files'])} files "
        f"(parsed={stats['parsed']}, "
        f"kept={stats['kept']}, "
        f"deleted={stats['deleted']})"
    )
    print(f"  cache: {cache_path.relative_to(root).as_posix()}")
    return 0
