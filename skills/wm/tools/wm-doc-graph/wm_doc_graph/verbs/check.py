"""`check` verb — repo-wide broken-reference scan (gate semantics).

Walks every file's refs_out in the current graph, attempts to resolve
each target against the filesystem, and reports unresolvable entries.
Exits non-zero when any broken reference is found so calling workflows
(`/wm:verify`, `/wm:release`) can treat it as a hard gate per FIN-004.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from ._common import load_current_graph
from ..schema import KEY_FILES, KEY_PATH, KEY_REFS_OUT


_URL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "ftp://")

# Directory-segment names that `check` skips by default. A path is excluded
# when any of its parent directory segments equals a name in this set. The
# test is segment-equality, not substring, so `live-archive.md` is scanned
# normally and only real `archive/` subtrees are dropped.
DEFAULT_EXCLUDE_SEGMENTS = frozenset({"archive"})


def _is_excluded(path: str, segments: frozenset[str]) -> bool:
    """True when any parent-directory segment of `path` is in `segments`."""
    if not segments:
        return False
    return bool(segments.intersection(PurePosixPath(path).parent.parts))


def _safe_resolve(p: Path) -> Path | None:
    try:
        return p.resolve()
    except (OSError, ValueError, RuntimeError):
        return None


def _resolve_candidates(target: str, source_path: str, root: Path) -> list[Path]:
    """Return the possible absolute paths a target might resolve to.

    Targets aren't canonicalized at parse time (tech spec §11 Q2) — the
    same logical file may appear as `~/foo.md`, `./foo.md`, a bare path,
    or a path relative to the source file's directory. Try every plausible
    interpretation; if any of them exists on disk, the ref is resolvable.
    """
    target = target.split("#", 1)[0].strip()
    if not target:
        return []
    if target.startswith(_URL_PREFIXES):
        return []

    candidates: list[Path] = []

    if target.startswith("~/"):
        r = _safe_resolve(Path.home() / target[2:])
        if r is not None:
            candidates.append(r)
    elif target == "~":
        r = _safe_resolve(Path.home())
        if r is not None:
            candidates.append(r)
    elif target.startswith("/") or (len(target) >= 2 and target[1] == ":"):
        r = _safe_resolve(Path(target))
        if r is not None:
            candidates.append(r)
    else:
        source_dir = (root / source_path).parent
        r1 = _safe_resolve(source_dir / target)
        if r1 is not None:
            candidates.append(r1)
        r2 = _safe_resolve(root / target)
        if r2 is not None and r2 not in candidates:
            candidates.append(r2)

    return candidates


def run(args) -> int:
    root = Path.cwd()
    graph = load_current_graph(root)

    include_archives = getattr(args, "include_archives", False)
    exclude_segments: frozenset[str] = (
        frozenset() if include_archives else DEFAULT_EXCLUDE_SEGMENTS
    )
    files = [
        entry
        for entry in graph.get(KEY_FILES, [])
        if not _is_excluded(entry.get(KEY_PATH, ""), exclude_segments)
    ]

    broken: list[dict] = []
    scanned = 0
    for entry in files:
        source = entry.get(KEY_PATH, "")
        for ref in entry.get(KEY_REFS_OUT, []):
            target = ref.get("target", "")
            if not target:
                continue
            scanned += 1
            candidates = _resolve_candidates(target, source, root)
            if candidates and any(c.exists() for c in candidates):
                continue
            broken.append(
                {
                    "source": source,
                    "line": ref.get("line"),
                    "kind": ref.get("kind"),
                    "target": target,
                }
            )

    total_files = len(files)
    if not broken:
        print(
            f"wm-doc-graph: check clean — {total_files} files, "
            f"{scanned} references scanned, 0 broken"
        )
        return 0

    print(
        f"wm-doc-graph: check FAILED — {len(broken)} broken references "
        f"in {total_files} files ({scanned} scanned)"
    )
    print()
    for b in broken:
        line_str = f"{b['line']:>5}" if b["line"] else "    ?"
        kind = b["kind"] or "?"
        print(f"  {b['source']}:{line_str}  [{kind:<13}] -> {b['target']}")
    return 1
