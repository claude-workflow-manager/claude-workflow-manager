"""`refs <file> [--out|--in|--both]` verb — forward/back references."""

from __future__ import annotations

from pathlib import Path

from ._common import (
    build_inverse_index,
    fail,
    find_entry,
    load_current_graph,
    validate_in_repo,
)


def _match_inverse(
    inverse: dict[str, list[dict]],
    rel: str,
) -> list[dict]:
    """Find back-references to `rel` in the inverse index.

    Target strings in refs_out are not canonicalized at parse time — the
    same file may be referenced as `~/.claude/skills/.../foo.md`,
    `skills/.../foo.md`, or a bare `foo.md`. This matcher accepts exact,
    suffix-after-slash, and basename matches. Basename matching is
    heuristic and can over-match when two files share a basename (the
    tradeoff is documented in tech spec §11 Q2 — deferred until a later
    version adds canonical target resolution at parse time).
    """
    basename = rel.rsplit("/", 1)[-1]
    out: list[dict] = []

    for target, records in inverse.items():
        if target == rel or target.endswith("/" + rel):
            out.extend(records)
            continue
        # Basename fallback for `@~/...` and `@./...` style targets that
        # don't share the rel path's directory prefix.
        if target == basename or target.endswith("/" + basename):
            out.extend(records)

    # Dedupe on (source, line, kind) — a single source may have matched
    # multiple targets that all resolved to the same file.
    seen: set[tuple] = set()
    unique: list[dict] = []
    for r in out:
        key = (r["source"], r.get("line"), r.get("kind"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    unique.sort(key=lambda r: (r["source"], r.get("line") or 0))
    return unique


def run(args) -> int:
    root = Path.cwd()
    rel = validate_in_repo(args.file, root)
    graph = load_current_graph(root)
    entry = find_entry(graph, rel)
    if entry is None:
        fail(f"{rel}: not in graph — run `wm-doc-graph build` and retry")

    direction = args.direction
    print(f"# {rel}")

    if direction in ("out", "both"):
        refs_out = entry.get("refs_out", [])
        print()
        print(f"## refs_out ({len(refs_out)})")
        for r in refs_out:
            print(f"  {r['line']:>5}  [{r['kind']:<13}] -> {r['target']}")

    if direction in ("in", "both"):
        inverse = build_inverse_index(graph)
        refs_in = _match_inverse(inverse, rel)
        print()
        print(f"## refs_in ({len(refs_in)})")
        for r in refs_in:
            line = r.get("line")
            line_str = f"{line:>5}" if line else "    ?"
            kind = r.get("kind") or "?"
            print(f"  {line_str}  [{kind:<13}] <- {r['source']}")

    return 0
