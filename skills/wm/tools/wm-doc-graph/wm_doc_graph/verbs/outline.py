"""`outline <file>` verb — print headers + signals for a cached file."""

from __future__ import annotations

from pathlib import Path

from ._common import fail, find_entry, load_current_graph, validate_in_repo


def run(args) -> int:
    root = Path.cwd()
    rel = validate_in_repo(args.file, root)
    graph = load_current_graph(root)
    entry = find_entry(graph, rel)
    if entry is None:
        fail(f"{rel}: not in graph — run `wm-doc-graph build` and retry")

    print(f"# {rel}")

    headers = entry.get("headers", [])
    signals = entry.get("signals", [])

    if headers:
        print()
        print(f"## headers ({len(headers)})")
        for h in headers:
            indent = "  " * (h["level"] - 1)
            print(f"  {h['line']:>5}  {indent}[h{h['level']}] {h['text']}")

    if signals:
        print()
        print(f"## signals ({len(signals)})")
        for s in signals:
            print(f"  {s['line']:>5}  <{s['type']}>")

    if not headers and not signals:
        print()
        print("(no headers or signals)")

    return 0
