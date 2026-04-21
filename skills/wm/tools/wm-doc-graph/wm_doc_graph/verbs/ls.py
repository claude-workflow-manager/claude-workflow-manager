"""`ls <path>` verb — list files under a path, filtered by graph membership."""

from __future__ import annotations

from pathlib import Path

from ._common import load_current_graph, validate_in_repo


def run(args) -> int:
    root = Path.cwd()
    rel = validate_in_repo(args.path, root)
    graph = load_current_graph(root)

    # Treat `rel` as a directory prefix. `.` and `""` match everything;
    # a non-empty prefix matches its exact entry (file) or anything under
    # `prefix + "/"` (subdirectory).
    prefix = rel.rstrip("/")
    files = graph["files"]
    if prefix in ("", "."):
        matched = [e["path"] for e in files]
    else:
        matched = [
            e["path"]
            for e in files
            if e["path"] == prefix or e["path"].startswith(prefix + "/")
        ]

    if not matched:
        print(f"(no graph files under {rel or '.'})")
        return 0

    for p in sorted(matched):
        print(p)
    return 0
