"""Unit tests for wm_doc_graph.cache and wm_doc_graph.store."""

from __future__ import annotations

import time
from pathlib import Path

import yaml

from wm_doc_graph.cache import default_cache_path, ensure_graph
from wm_doc_graph.schema import KEY_FILES, KEY_PATH, KEY_SCHEMA_VERSION, SCHEMA_VERSION
from wm_doc_graph.store import load_graph, save_graph


# Helper — bump a file's mtime by rewriting its content and optionally
# forcing a larger gap so the int(second-precision) mtime actually changes.
def _touch_with_delay(path: Path, new_content: str) -> None:
    time.sleep(1.1)  # Windows NTFS rounds mtime to whole seconds
    path.write_text(new_content, encoding="utf-8")


# --- store.py round-trip ---------------------------------------------------


def test_store_roundtrip(tmp_path: Path):
    graph = {
        "schema_version": 1,
        "generator": "wm-doc-graph",
        "files": [{"path": "a.md", "mtime": 123, "headers": [], "signals": [], "refs_out": []}],
    }
    cp = tmp_path / "cache.yaml"
    save_graph(graph, cp)
    loaded = load_graph(cp)
    assert loaded == graph


def test_store_load_missing_file_returns_none(tmp_path: Path):
    assert load_graph(tmp_path / "nope.yaml") is None


def test_store_load_malformed_yaml_returns_none(tmp_path: Path, capsys):
    cp = tmp_path / "bad.yaml"
    cp.write_text("bad: : : [\n", encoding="utf-8")
    assert load_graph(cp) is None
    err = capsys.readouterr().err
    assert "rebuilding" in err


def test_store_load_wrong_shape_returns_none(tmp_path: Path, capsys):
    cp = tmp_path / "list.yaml"
    cp.write_text("- just\n- a\n- list\n", encoding="utf-8")
    assert load_graph(cp) is None
    err = capsys.readouterr().err
    assert "unexpected shape" in err


# --- ensure_graph state machine -------------------------------------------


def test_ensure_graph_cold_start(markdown_repo: Path):
    graph, stats = ensure_graph(markdown_repo)
    assert stats == {"parsed": 3, "kept": 0, "deleted": 0, "cold": True}
    assert default_cache_path(markdown_repo).exists()
    assert len(graph[KEY_FILES]) == 3


def test_ensure_graph_warm_noop_fast_path(markdown_repo: Path):
    # Cold build first.
    ensure_graph(markdown_repo)
    cp = default_cache_path(markdown_repo)
    cold_mtime = cp.stat().st_mtime

    # Warm re-run with no changes must NOT rewrite the cache file.
    time.sleep(0.05)
    graph, stats = ensure_graph(markdown_repo)
    assert stats == {"parsed": 0, "kept": 3, "deleted": 0, "cold": False}
    assert cp.stat().st_mtime == cold_mtime


def test_ensure_graph_single_file_edit_reparses_only_that_file(markdown_repo: Path):
    ensure_graph(markdown_repo)
    _touch_with_delay(markdown_repo / "a.md", "# Alpha edited\n# extra header\n")
    graph, stats = ensure_graph(markdown_repo)
    assert stats["parsed"] == 1
    assert stats["kept"] == 2
    assert stats["deleted"] == 0
    assert stats["cold"] is False
    a_entry = next(f for f in graph[KEY_FILES] if f[KEY_PATH] == "a.md")
    assert len(a_entry["headers"]) == 2


def test_ensure_graph_deletion(markdown_repo: Path):
    ensure_graph(markdown_repo)
    (markdown_repo / "sub" / "c.md").unlink()
    graph, stats = ensure_graph(markdown_repo)
    assert stats["deleted"] == 1
    assert stats["cold"] is False
    paths = [f[KEY_PATH] for f in graph[KEY_FILES]]
    assert "sub/c.md" not in paths
    assert len(paths) == 2


def test_ensure_graph_force_rebuild(markdown_repo: Path):
    ensure_graph(markdown_repo)
    graph, stats = ensure_graph(markdown_repo, force=True)
    assert stats["cold"] is True
    assert stats["parsed"] == 3
    assert stats["kept"] == 0


def test_ensure_graph_corruption_triggers_full_rebuild(markdown_repo: Path, capsys):
    ensure_graph(markdown_repo)
    cp = default_cache_path(markdown_repo)
    cp.write_text("bad: : : [\n", encoding="utf-8")
    graph, stats = ensure_graph(markdown_repo)
    assert stats["cold"] is True
    assert stats["parsed"] == 3
    # Warning should have been emitted
    err = capsys.readouterr().err
    assert "rebuilding" in err
    # And the cache is valid again
    reloaded = load_graph(cp)
    assert reloaded is not None
    assert reloaded[KEY_SCHEMA_VERSION] == SCHEMA_VERSION


def test_ensure_graph_schema_mismatch_triggers_rebuild(markdown_repo: Path):
    ensure_graph(markdown_repo)
    cp = default_cache_path(markdown_repo)
    # Write a valid-YAML cache with the wrong schema version.
    reloaded = load_graph(cp)
    assert reloaded is not None
    reloaded[KEY_SCHEMA_VERSION] = 999
    cp.write_text(yaml.safe_dump(reloaded), encoding="utf-8")

    graph, stats = ensure_graph(markdown_repo)
    assert stats["cold"] is True
    assert graph[KEY_SCHEMA_VERSION] == SCHEMA_VERSION


def test_ensure_graph_new_file_added(markdown_repo: Path):
    ensure_graph(markdown_repo)
    (markdown_repo / "d.md").write_text("# Delta\n", encoding="utf-8")
    graph, stats = ensure_graph(markdown_repo)
    assert stats["parsed"] == 1
    assert stats["kept"] == 3
    paths = [f[KEY_PATH] for f in graph[KEY_FILES]]
    assert "d.md" in paths
