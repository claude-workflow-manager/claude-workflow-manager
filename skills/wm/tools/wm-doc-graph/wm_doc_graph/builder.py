"""Markdown structural parser for wm-doc-graph.

Per FIN-006 (markdown-only), FIN-008 (single-repo, cwd-scoped), and the tech
spec §4 schema. Does not follow @-includes recursively — forward references
only.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Iterable, Iterator

from . import __version__
from .schema import (
    GENERATOR_NAME,
    INDEXED_EXTENSIONS,
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
    REF_KIND_INCLUDE,
    REF_KIND_LINK,
    REF_KIND_PATH_MENTION,
    SCHEMA_VERSION,
    SIGNAL_TAGS,
)

# --- Compiled patterns ------------------------------------------------------

_SIGNAL_TAG_UNION = "|".join(re.escape(t) for t in SIGNAL_TAGS)

HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)

# Opening XML-like tag: <purpose>, <step name="...">, <required_reading>,
# also tolerates self-closing <tag/>.
SIGNAL_PATTERN = re.compile(rf"<({_SIGNAL_TAG_UNION})(?:\s[^>]*)?/?>")

# @-include directive. Lookbehind rejects word-char and backtick before `@`
# so `user@example.md` and inline-code `` `@x.md` `` do not match.
INCLUDE_PATTERN = re.compile(r"(?<![`\w])@([^\s<>`\"',;()\[\]]+\.md)")

# Markdown link [text](target). Optional trailing title is tolerated.
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

# Entire <required_reading>...</required_reading> block, lazy multiline.
REQUIRED_READING_BLOCK = re.compile(
    r"<required_reading[^>]*>(.*?)</required_reading>",
    re.DOTALL,
)

# Path-shaped token ending in .md. Used only inside <required_reading> blocks
# to catch bare paths that aren't @-includes. Lookbehind rejects any char that
# could be part of a preceding path (`~`, `/`, `.`, `-`), plus word-chars,
# backtick, and `@` — otherwise BARE_PATH would re-match tail segments of an
# @-include like `/.claude/...` after skipping past the leading `~`.
BARE_PATH_PATTERN = re.compile(r"(?<![`@\w~/.\-])([\w./~\-][\w./~\-]*\.md)")

_URL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "ftp://")

# os.walk dirs we prune. Anything starting with `.` is also pruned by
# iter_markdown_files so hidden trees stay out of the graph.
_SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
    }
)


# --- Helpers ----------------------------------------------------------------


def _line_of(content: str, pos: int) -> int:
    return content.count("\n", 0, pos) + 1


# Inline code span: double-backtick (for spans containing single backticks)
# or single-backtick. Matched per-line, so it never crosses a newline.
_INLINE_CODE_PATTERN = re.compile(r"``[^`\n]*?``|`[^`\n]+?`")


def _blank_inline_code(line: str) -> str:
    return _INLINE_CODE_PATTERN.sub(lambda m: " " * len(m.group(0)), line)


def _strip_code_fences(content: str) -> str:
    """Blank out fenced and inline code spans while preserving line offsets.

    Parsers run on the stripped form so patterns inside code samples (Python
    `#` comments, example `@`-includes, documentation showing literal
    `[text](path.md)` link syntax) do not match. Line positions and line
    lengths are unchanged, so `_line_of` still reports the right source line.
    """
    lines = content.split("\n")
    out: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.lstrip()
        is_fence = stripped.startswith("```") or stripped.startswith("~~~")
        if is_fence:
            in_fence = not in_fence
            out.append(" " * len(line))
            continue
        out.append(" " * len(line) if in_fence else _blank_inline_code(line))
    return "\n".join(out)


def _is_url(target: str) -> bool:
    return any(target.startswith(p) for p in _URL_PREFIXES)


# --- Parsers ----------------------------------------------------------------


def parse_headers(content: str) -> list[dict]:
    headers: list[dict] = []
    for match in HEADER_PATTERN.finditer(content):
        headers.append(
            {
                "level": len(match.group(1)),
                "text": match.group(2).strip(),
                "line": _line_of(content, match.start()),
            }
        )
    return headers


def parse_signals(content: str) -> list[dict]:
    signals: list[dict] = []
    for match in SIGNAL_PATTERN.finditer(content):
        signals.append(
            {
                "type": match.group(1),
                "line": _line_of(content, match.start()),
            }
        )
    return signals


def parse_refs_out(content: str) -> list[dict]:
    """Extract outgoing references: @-includes, markdown links, path-mentions.

    Result is deduplicated on (line, kind, target) and sorted for determinism.
    """
    seen: set[tuple[int, str, str]] = set()
    refs: list[dict] = []

    def _add(target: str, line: int, kind: str) -> None:
        key = (line, kind, target)
        if key in seen:
            return
        seen.add(key)
        refs.append({"target": target, "line": line, "kind": kind})

    for match in INCLUDE_PATTERN.finditer(content):
        _add(match.group(1), _line_of(content, match.start()), REF_KIND_INCLUDE)

    for match in LINK_PATTERN.finditer(content):
        target = match.group(1).strip()
        if not target or target.startswith("#") or _is_url(target):
            continue
        _add(target, _line_of(content, match.start()), REF_KIND_LINK)

    for block_match in REQUIRED_READING_BLOCK.finditer(content):
        block_text = block_match.group(1)
        block_start = block_match.start(1)
        for path_match in BARE_PATH_PATTERN.finditer(block_text):
            target = path_match.group(1)
            if _is_url(target):
                continue
            line = _line_of(content, block_start + path_match.start())
            # Skip if the same line already has this target as an include —
            # avoids double-counting `@~/x.md` sitting inside a block.
            if (line, REF_KIND_INCLUDE, target) in seen:
                continue
            _add(target, line, REF_KIND_PATH_MENTION)

    refs.sort(key=lambda r: (r["line"], r["kind"], r["target"]))
    return refs


# --- Per-file entry + walker ------------------------------------------------


def parse_file(path: Path, root: Path) -> dict | None:
    """Parse one markdown file into its graph entry.

    Returns None when the path is outside `root` (FIN-008), unreadable, or
    undecodable. `root` must be pre-resolved by the caller.
    """
    abs_path = path.resolve()
    try:
        rel = abs_path.relative_to(root).as_posix()
    except ValueError:
        return None
    try:
        content = abs_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        stat = abs_path.stat()
    except OSError:
        return None

    stripped = _strip_code_fences(content)

    return {
        KEY_PATH: rel,
        KEY_MTIME: int(stat.st_mtime),
        KEY_SIZE: stat.st_size,
        KEY_HEADERS: parse_headers(stripped),
        KEY_SIGNALS: parse_signals(stripped),
        KEY_REFS_OUT: parse_refs_out(stripped),
    }


def iter_markdown_files(root: Path) -> Iterator[Path]:
    """Yield every indexed markdown file under `root` (cwd-scoped per FIN-008)."""
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")
        ]
        for name in filenames:
            if name.endswith(INDEXED_EXTENSIONS):
                yield Path(dirpath) / name


# --- Top-level assembly -----------------------------------------------------


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def build_graph(
    root: Path,
    paths: Iterable[Path] | None = None,
) -> dict:
    """Build an in-memory graph dict from markdown files under `root`.

    When `paths` is None, walks the whole repo. When supplied, parses only
    those files — this is the hook the incremental cache (Step 1.3) uses to
    re-parse only the files whose mtime changed. Files outside `root` are
    silently skipped (FIN-008).
    """
    root = root.resolve()
    targets: Iterable[Path] = iter_markdown_files(root) if paths is None else paths

    files: list[dict] = []
    for path in targets:
        entry = parse_file(path, root)
        if entry is not None:
            files.append(entry)

    files.sort(key=lambda f: f[KEY_PATH])

    return {
        KEY_SCHEMA_VERSION: SCHEMA_VERSION,
        KEY_GENERATED_AT: _now_iso(),
        KEY_GENERATOR: GENERATOR_NAME,
        KEY_GENERATOR_VERSION: __version__,
        KEY_ROOT: str(root),
        KEY_FILES: files,
    }
