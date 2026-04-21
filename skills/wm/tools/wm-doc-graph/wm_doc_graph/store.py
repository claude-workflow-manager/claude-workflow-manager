"""YAML load/save for the wm-doc-graph cache file.

Thin wrapper around PyYAML with explicit corruption/error handling so
`cache.ensure_graph` can fall back to a full rebuild per tech spec §8.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "wm-doc-graph requires PyYAML. Install with: pip install pyyaml"
    ) from e

# Prefer the libyaml-backed C implementations when available — they are
# ~5-10x faster on the WM repo's ~220KB cache. Falls back silently to the
# pure-Python loaders on installs without libyaml.
_SafeLoader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
_SafeDumper = getattr(yaml, "CSafeDumper", yaml.SafeDumper)


def load_graph(cache_path: Path) -> dict | None:
    """Load a graph from a YAML cache file.

    Returns None if the file does not exist, is unreadable, or contains
    malformed YAML or the wrong top-level shape. Real corruption is logged
    to stderr; the caller is expected to fall back to a full rebuild.
    """
    if not cache_path.exists():
        return None
    try:
        text = cache_path.read_text(encoding="utf-8")
    except OSError as e:
        print(
            f"wm-doc-graph: cache read failed ({e}) — rebuilding",
            file=sys.stderr,
        )
        return None
    try:
        data = yaml.load(text, Loader=_SafeLoader)
    except yaml.YAMLError as e:
        print(
            f"wm-doc-graph: cache parse failed ({e}) — rebuilding",
            file=sys.stderr,
        )
        return None
    if not isinstance(data, dict):
        print(
            "wm-doc-graph: cache has unexpected shape — rebuilding",
            file=sys.stderr,
        )
        return None
    return data


def save_graph(graph: dict, cache_path: Path) -> None:
    """Write `graph` to `cache_path`, creating parent dirs as needed."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.dump(
        graph,
        Dumper=_SafeDumper,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )
    cache_path.write_text(text, encoding="utf-8")
