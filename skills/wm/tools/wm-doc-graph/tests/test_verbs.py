"""Tests for wm_doc_graph.verbs.*.

Each verb is tested through its `run(args)` entry point so the test
surface matches how the CLI dispatches. Tests use `monkeypatch.chdir`
to satisfy the verbs' `Path.cwd()` calls without refactoring them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import make_args
from wm_doc_graph.verbs import build, check, impact, ls, outline, refs, search


# --- build -----------------------------------------------------------------


def test_build_cold(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    rc = build.run(make_args(force=True))
    assert rc == 0
    out = capsys.readouterr().out
    assert "cold build complete" in out
    assert "3 files" in out


def test_build_warm_noop(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    build.run(make_args(force=True))
    capsys.readouterr()  # drain
    rc = build.run(make_args(force=False))
    assert rc == 0
    out = capsys.readouterr().out
    assert "warm build complete" in out
    assert "parsed=0" in out
    assert "kept=3" in out


# --- outline ---------------------------------------------------------------


def test_outline_headers_and_signals(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    rc = outline.run(make_args(file="a.md"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "# a.md" in out
    assert "Alpha" in out  # header
    assert "<purpose>" in out  # signal


def test_outline_missing_file_fails_with_hint(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    with pytest.raises(SystemExit) as exc:
        outline.run(make_args(file="does-not-exist.md"))
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "not in graph" in err


def test_outline_rejects_path_outside_cwd(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    with pytest.raises(SystemExit) as exc:
        outline.run(make_args(file="../escape.md"))
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "outside cwd" in err


# --- ls --------------------------------------------------------------------


def test_ls_lists_all(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    rc = ls.run(make_args(path="."))
    assert rc == 0
    out = capsys.readouterr().out
    assert "a.md" in out
    assert "b.md" in out
    assert "sub/c.md" in out


def test_ls_filters_by_subdir(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    rc = ls.run(make_args(path="sub/"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "sub/c.md" in out
    assert "a.md" not in out


# --- refs ------------------------------------------------------------------


def test_refs_out(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    rc = refs.run(make_args(file="a.md", direction="out"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "refs_out" in out
    assert "gate-matrix.md" in out


def test_refs_in_finds_back_references(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    # a.md is referenced by sub/c.md via [back to a](../a.md).
    rc = refs.run(make_args(file="a.md", direction="in"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "refs_in" in out
    assert "sub/c.md" in out


def test_refs_both(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    rc = refs.run(make_args(file="a.md", direction="both"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "refs_out" in out
    assert "refs_in" in out


# --- check -----------------------------------------------------------------


def test_check_clean(tmp_path: Path, monkeypatch, capsys):
    (tmp_path / "a.md").write_text("# A\n[link](./b.md)\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# B\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    rc = check.run(make_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "check clean" in out


def test_check_broken_refs_nonzero_exit(tmp_path: Path, monkeypatch, capsys):
    (tmp_path / "src.md").write_text(
        "# src\n"
        "[missing](./nope.md)\n"
        "@~/.claude/this-xyzzy-will-not-exist-zzz.md\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    rc = check.run(make_args())
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAILED" in out
    assert "nope.md" in out
    assert "xyzzy" in out


def _build_archive_fixture(root: Path) -> None:
    """Three broken refs, each inside a differently-shaped archive path."""
    (root / "archive").mkdir()
    (root / "archive" / "a.md").write_text(
        "# a\n[gone](./vanished.md)\n", encoding="utf-8"
    )
    (root / "docs").mkdir()
    (root / "docs" / "archive").mkdir()
    (root / "docs" / "archive" / "b.md").write_text(
        "# b\n[gone](./gone.md)\n", encoding="utf-8"
    )
    (root / "archive" / "nest").mkdir()
    (root / "archive" / "nest" / "archive").mkdir()
    (root / "archive" / "nest" / "archive" / "c.md").write_text(
        "# c\n[gone](./absent.md)\n", encoding="utf-8"
    )


def test_check_excludes_archive_by_default(tmp_path: Path, monkeypatch, capsys):
    _build_archive_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = check.run(make_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "check clean" in out


def test_check_include_archives_restores_scope(tmp_path: Path, monkeypatch, capsys):
    _build_archive_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = check.run(make_args(include_archives=True))
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAILED" in out
    assert "vanished.md" in out
    assert "gone.md" in out
    assert "absent.md" in out


def test_check_archive_match_is_path_segment_not_substring(
    tmp_path: Path, monkeypatch, capsys
):
    # Filename contains the substring "archive" but has no "archive/" segment.
    (tmp_path / "live-archive.md").write_text(
        "# live\n[gone](./nope.md)\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    rc = check.run(make_args())
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAILED" in out
    assert "live-archive.md" in out


# --- search ----------------------------------------------------------------


def test_search_hit(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    rc = search.run(make_args(query="Alpha"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "match" in out
    assert "a.md" in out


def test_search_no_match(markdown_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(markdown_repo)
    rc = search.run(make_args(query="xyzzy-no-match-token"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "no matches" in out


# --- impact ----------------------------------------------------------------


def test_impact_light_finds_fin_and_downstream(
    wm_mock_project: Path, monkeypatch, capsys
):
    monkeypatch.chdir(wm_mock_project)
    rc = impact.run(
        make_args(files=["skills/wm/workflows/verify-plan.md"], mode="light")
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Impact Scan (light)" in out
    assert "FIN-001" in out
    assert "Verdict" in out
    assert "review needed" in out


def test_impact_deep_renders_tables(wm_mock_project: Path, monkeypatch, capsys):
    monkeypatch.chdir(wm_mock_project)
    rc = impact.run(
        make_args(files=["skills/wm/workflows/verify-plan.md"], mode="deep")
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Impact Scan (deep)" in out
    assert "### FIN affected" in out
    assert "### Downstream consumers" in out
    assert "### Plan / design drift" in out
    assert "### Verdict" in out
    assert "### Recommended action" in out
    assert "FIN-001" in out


def test_impact_rejects_path_outside_cwd(wm_mock_project: Path, monkeypatch, capsys):
    monkeypatch.chdir(wm_mock_project)
    with pytest.raises(SystemExit) as exc:
        impact.run(make_args(files=["../escape.md"], mode="light"))
    assert exc.value.code == 2


def test_impact_on_clean_file_verdict_clean(tmp_path: Path, monkeypatch, capsys):
    # No projects dir, no graph refs → every dimension empty → clean.
    (tmp_path / "lonely.md").write_text("# Lonely\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    rc = impact.run(make_args(files=["lonely.md"], mode="light"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "Verdict: clean" in out
