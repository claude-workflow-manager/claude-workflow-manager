"""Structural compatibility test with ag:map-ref (FIN-005).

Asserts the wm-doc-graph output shape is compatible with the shape
ag:map-ref would produce on the same fixture — compatibility at the
schema level, not byte-equal output. The two tools emit different
extension fields; FIN-005 only promises the common core is interchangeable.
"""

from __future__ import annotations

from pathlib import Path

from wm_doc_graph.builder import build_graph
from wm_doc_graph.schema import (
    KEY_FILES,
    KEY_GENERATED_AT,
    KEY_GENERATOR,
    KEY_GENERATOR_VERSION,
    KEY_HEADERS,
    KEY_MTIME,
    KEY_PATH,
    KEY_REFS_OUT,
    KEY_ROOT,
    KEY_SCHEMA_VERSION,
    KEY_SIGNALS,
    KEY_SIZE,
    SCHEMA_VERSION,
    SIGNAL_TAGS,
)


def test_top_level_keys_match_schema(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    required = {
        KEY_SCHEMA_VERSION,
        KEY_GENERATED_AT,
        KEY_GENERATOR,
        KEY_GENERATOR_VERSION,
        KEY_ROOT,
        KEY_FILES,
    }
    assert required.issubset(graph.keys())


def test_per_file_entry_shape(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    for entry in graph[KEY_FILES]:
        # Every entry must expose the core shape keys.
        assert KEY_PATH in entry
        assert KEY_MTIME in entry
        assert KEY_SIZE in entry
        assert KEY_HEADERS in entry
        assert KEY_SIGNALS in entry
        assert KEY_REFS_OUT in entry
        # Lists, not None — absence is represented by empty list.
        assert isinstance(entry[KEY_HEADERS], list)
        assert isinstance(entry[KEY_SIGNALS], list)
        assert isinstance(entry[KEY_REFS_OUT], list)


def test_headers_record_shape(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    for entry in graph[KEY_FILES]:
        for h in entry[KEY_HEADERS]:
            assert set(h.keys()) == {"level", "text", "line"}
            assert isinstance(h["level"], int)
            assert 1 <= h["level"] <= 6
            assert isinstance(h["text"], str)
            assert isinstance(h["line"], int)
            assert h["line"] >= 1


def test_signals_record_shape(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    for entry in graph[KEY_FILES]:
        for s in entry[KEY_SIGNALS]:
            assert set(s.keys()) == {"type", "line"}
            # Signal types must come from the documented set — FIN-005's
            # compatibility promise depends on this being a closed set.
            assert s["type"] in SIGNAL_TAGS
            assert isinstance(s["line"], int)
            assert s["line"] >= 1


def test_refs_out_record_shape(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    for entry in graph[KEY_FILES]:
        for r in entry[KEY_REFS_OUT]:
            assert set(r.keys()) == {"target", "line", "kind"}
            assert isinstance(r["target"], str) and r["target"]
            assert isinstance(r["line"], int)
            assert r["kind"] in ("include", "link", "path-mention")


def test_schema_version_is_pinned(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    assert graph[KEY_SCHEMA_VERSION] == SCHEMA_VERSION
    assert isinstance(graph[KEY_SCHEMA_VERSION], int)


def test_generator_identifies_as_wm_doc_graph(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    assert graph[KEY_GENERATOR] == "wm-doc-graph"
    # Version should look like semver-ish
    v = graph[KEY_GENERATOR_VERSION]
    assert isinstance(v, str) and "." in v


def test_files_sorted_deterministically(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    paths = [f[KEY_PATH] for f in graph[KEY_FILES]]
    assert paths == sorted(paths)


def test_refs_out_sorted_deterministically(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    for entry in graph[KEY_FILES]:
        refs = entry[KEY_REFS_OUT]
        keys = [(r["line"], r["kind"], r["target"]) for r in refs]
        assert keys == sorted(keys)


def test_paths_are_posix_style(markdown_repo: Path):
    """ag:map-ref uses forward-slash rel paths; we must too (FIN-005)."""
    graph = build_graph(markdown_repo)
    for entry in graph[KEY_FILES]:
        assert "\\" not in entry[KEY_PATH]
