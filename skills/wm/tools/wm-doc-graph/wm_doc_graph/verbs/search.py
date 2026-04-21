"""`search <query>` verb — keyword/concept ranking across the graph.

Simple weighted substring search over headers, signal types, and paths.
Future iterations can add TF-IDF, full content indexing, or header/signal
proximity boost (tech spec §11 Q4 — "probably start simple, iterate").
Per FIN-004, `/wm:learn` uses this verb to suggest routing targets.
"""

from __future__ import annotations

from pathlib import Path

from ._common import load_current_graph


_HEADER_WEIGHT = 3
_PATH_WEIGHT = 2
_SIGNAL_WEIGHT = 1


def _score_entry(query: str, entry: dict) -> int:
    q = query.lower()
    score = 0

    path = entry.get("path", "").lower()
    if q in path:
        score += _PATH_WEIGHT * path.count(q)

    for h in entry.get("headers", []):
        text = (h.get("text") or "").lower()
        if q in text:
            score += _HEADER_WEIGHT * text.count(q)

    for s in entry.get("signals", []):
        stype = (s.get("type") or "").lower()
        if q in stype:
            score += _SIGNAL_WEIGHT

    return score


def run(args) -> int:
    query = args.query
    root = Path.cwd()
    graph = load_current_graph(root)

    results: list[tuple[int, str]] = []
    for entry in graph.get("files", []):
        score = _score_entry(query, entry)
        if score > 0:
            results.append((score, entry["path"]))

    results.sort(key=lambda r: (-r[0], r[1]))

    if not results:
        print(f"wm-doc-graph: no matches for '{query}'")
        return 0

    print(f"wm-doc-graph: {len(results)} match(es) for '{query}'")
    print()
    for score, path in results:
        print(f"  {score:>4}  {path}")
    return 0
