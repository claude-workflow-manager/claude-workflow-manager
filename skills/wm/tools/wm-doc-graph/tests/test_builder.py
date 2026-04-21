"""Unit tests for wm_doc_graph.builder."""

from __future__ import annotations

from pathlib import Path

from wm_doc_graph.builder import (
    _strip_code_fences,
    build_graph,
    iter_markdown_files,
    parse_file,
    parse_headers,
    parse_refs_out,
    parse_signals,
)
from wm_doc_graph.schema import (
    KEY_FILES,
    KEY_HEADERS,
    KEY_MTIME,
    KEY_PATH,
    KEY_REFS_OUT,
    KEY_SIGNALS,
    REF_KIND_INCLUDE,
    REF_KIND_LINK,
    REF_KIND_PATH_MENTION,
    SCHEMA_VERSION,
)


# --- parse_headers ---------------------------------------------------------


def test_parse_headers_basic():
    content = "# A\n## B\n### C\nplain text\n"
    headers = parse_headers(content)
    assert len(headers) == 3
    assert headers[0] == {"level": 1, "text": "A", "line": 1}
    assert headers[1] == {"level": 2, "text": "B", "line": 2}
    assert headers[2] == {"level": 3, "text": "C", "line": 3}


def test_parse_headers_ignores_fake_headers():
    # 7 hashes is not a valid markdown header, and indented # is also not.
    content = "####### Not a header\n    # also not\n"
    assert parse_headers(content) == []


def test_parse_headers_trailing_whitespace():
    content = "# Title with trailing   \n"
    headers = parse_headers(content)
    assert headers[0]["text"] == "Title with trailing"


# --- parse_signals ---------------------------------------------------------


def test_parse_signals_all_tag_kinds():
    content = (
        "<purpose>x</purpose>\n"
        "<process>\n"
        "<step name='Step 1'>y</step>\n"
        "<required_reading>\n"
        "</required_reading>\n"
        "<autonomy>z</autonomy>\n"
        "<stop_after/>\n"
    )
    signals = parse_signals(content)
    types = [s["type"] for s in signals]
    assert "purpose" in types
    assert "process" in types
    assert "step" in types
    assert "required_reading" in types
    assert "autonomy" in types
    assert "stop_after" in types


def test_parse_signals_line_numbers():
    content = "line 1\n\n<purpose>x</purpose>\n"
    signals = parse_signals(content)
    assert signals[0]["line"] == 3


def test_parse_signals_unknown_tags_ignored():
    # <metadata> is not in SIGNAL_TAGS — should not appear.
    content = "<metadata>x</metadata>\n"
    assert parse_signals(content) == []


# --- parse_refs_out --------------------------------------------------------


def test_parse_refs_out_include_directive():
    content = "See @~/.claude/foo.md for details.\n"
    refs = parse_refs_out(content)
    assert len(refs) == 1
    assert refs[0]["target"] == "~/.claude/foo.md"
    assert refs[0]["kind"] == REF_KIND_INCLUDE


def test_parse_refs_out_markdown_link():
    content = "[title](path.md)\n"
    refs = parse_refs_out(content)
    assert len(refs) == 1
    assert refs[0]["target"] == "path.md"
    assert refs[0]["kind"] == REF_KIND_LINK


def test_parse_refs_out_path_mention_in_required_reading():
    content = "<required_reading>\nskills/wm/foo.md\n</required_reading>\n"
    refs = parse_refs_out(content)
    # Bare path inside required_reading block → path-mention kind.
    assert any(r["kind"] == REF_KIND_PATH_MENTION for r in refs)
    assert any(r["target"] == "skills/wm/foo.md" for r in refs)


def test_parse_refs_out_no_double_count_for_include_inside_required_reading():
    content = "<required_reading>\n@~/skills/wm/foo.md\n</required_reading>\n"
    refs = parse_refs_out(content)
    # The @-include is captured once as `include`, NOT also as path-mention.
    kinds = [r["kind"] for r in refs]
    assert kinds.count(REF_KIND_INCLUDE) == 1
    assert kinds.count(REF_KIND_PATH_MENTION) == 0


def test_parse_refs_out_url_links_excluded():
    content = "[ext](https://example.com/foo.md)\n[anchor](#section)\n"
    assert parse_refs_out(content) == []


def test_parse_refs_out_email_not_an_include():
    content = "Contact user@example.md for help.\n"
    # Word-character lookbehind rejects `r@` — no include match.
    assert parse_refs_out(content) == []


# --- _strip_code_fences ----------------------------------------------------


def test_strip_code_fences_blanks_fence_content():
    content = "# Header\n```\n# Fake header inside fence\n```\n"
    stripped = _strip_code_fences(content)
    # Header inside the fence must be gone (replaced with spaces),
    # but the real header on line 1 must survive.
    assert parse_headers(stripped) == [{"level": 1, "text": "Header", "line": 1}]


def test_strip_code_fences_blanks_inline_backtick_spans():
    content = "Use `@~/fake.md` — this should not be captured.\n"
    stripped = _strip_code_fences(content)
    assert parse_refs_out(stripped) == []


def test_strip_code_fences_preserves_line_positions():
    content = "a\n```\nb\nc\n```\nd\n"
    stripped = _strip_code_fences(content)
    # Line count unchanged
    assert len(stripped.split("\n")) == len(content.split("\n"))


# --- parse_file + walker + build_graph -------------------------------------


def test_parse_file_produces_full_entry(markdown_repo: Path):
    root = markdown_repo.resolve()
    entry = parse_file(root / "a.md", root)
    assert entry is not None
    assert entry[KEY_PATH] == "a.md"
    assert entry[KEY_MTIME] > 0
    assert any(h["text"] == "Alpha" for h in entry[KEY_HEADERS])
    assert any(s["type"] == "purpose" for s in entry[KEY_SIGNALS])
    include_targets = [
        r["target"] for r in entry[KEY_REFS_OUT] if r["kind"] == REF_KIND_INCLUDE
    ]
    assert "~/.claude/skills/wm/references/gate-matrix.md" in include_targets


def test_parse_file_rejects_outside_root(tmp_path: Path):
    other = tmp_path / "other"
    other.mkdir()
    outside = other / "outside.md"
    outside.write_text("# outside\n", encoding="utf-8")
    inside = tmp_path / "inside"
    inside.mkdir()
    assert parse_file(outside, inside.resolve()) is None


def test_iter_markdown_files_skips_hidden_dirs(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD.md").write_text("# no\n", encoding="utf-8")
    (tmp_path / "real.md").write_text("# yes\n", encoding="utf-8")
    paths = list(iter_markdown_files(tmp_path))
    names = [p.name for p in paths]
    assert names == ["real.md"]


def test_iter_markdown_files_skips_node_modules(tmp_path: Path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.md").write_text("# no\n", encoding="utf-8")
    (tmp_path / "real.md").write_text("# yes\n", encoding="utf-8")
    paths = list(iter_markdown_files(tmp_path))
    assert [p.name for p in paths] == ["real.md"]


def test_build_graph_walks_repo(markdown_repo: Path):
    graph = build_graph(markdown_repo)
    assert graph["schema_version"] == SCHEMA_VERSION
    assert graph["generator"] == "wm-doc-graph"
    paths = [f[KEY_PATH] for f in graph[KEY_FILES]]
    assert paths == ["a.md", "b.md", "sub/c.md"]


def test_build_graph_accepts_explicit_paths(markdown_repo: Path):
    paths = [markdown_repo / "a.md"]
    graph = build_graph(markdown_repo, paths=paths)
    assert len(graph[KEY_FILES]) == 1
    assert graph[KEY_FILES][0][KEY_PATH] == "a.md"


def test_build_graph_silently_skips_outside_root(tmp_path: Path):
    inside = tmp_path / "inside"
    inside.mkdir()
    (inside / "a.md").write_text("# a\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "b.md").write_text("# b\n", encoding="utf-8")

    graph = build_graph(inside, paths=[inside / "a.md", outside / "b.md"])
    assert [f[KEY_PATH] for f in graph[KEY_FILES]] == ["a.md"]
