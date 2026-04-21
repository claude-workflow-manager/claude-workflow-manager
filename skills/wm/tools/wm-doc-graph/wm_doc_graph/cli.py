"""CLI entry point for wm-doc-graph.

Parses argv, dispatches to verb handlers under ``wm_doc_graph.verbs.*``.
All seven verbs are wired: ``build``, ``refs``, ``ls``, ``outline``,
``impact``, ``check``, ``search``.
"""

import argparse
import sys

from . import __version__
from .schema import SCHEMA_VERSION

# The 7 verbs the slash command exposes (per FIN-018b and tech spec §5).
VERBS = ("build", "refs", "impact", "check", "search", "ls", "outline")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wm_doc_graph",
        description=(
            "Structural map builder/querier for markdown-heavy repositories. "
            "Indexes files, references, headers, and signal markers in the "
            "current working directory."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__} (schema {SCHEMA_VERSION})",
    )

    subparsers = parser.add_subparsers(dest="verb", required=False, metavar="VERB")

    # build [--force]
    sp_build = subparsers.add_parser("build", help="build or refresh the structural graph")
    sp_build.add_argument("--force", action="store_true", help="full rebuild, skip mtime cache check")

    # refs <file> [--in | --out | --both]
    sp_refs = subparsers.add_parser("refs", help="show references for a file")
    sp_refs.add_argument("file", help="file path (relative to cwd)")
    direction = sp_refs.add_mutually_exclusive_group()
    direction.add_argument("--in", dest="direction", action="store_const", const="in",
                           help="back-references only (what references this file)")
    direction.add_argument("--out", dest="direction", action="store_const", const="out",
                           help="forward references only (what this file references)")
    direction.add_argument("--both", dest="direction", action="store_const", const="both",
                           help="both directions (default)")
    sp_refs.set_defaults(direction="both")

    # impact <files...> [--mode=light|deep]
    sp_impact = subparsers.add_parser("impact", help="impact analysis for a set of files")
    sp_impact.add_argument("files", nargs="+", help="file paths to analyze")
    sp_impact.add_argument("--mode", choices=("light", "deep"), default="light",
                           help="scan depth (default: light)")

    # check [--include-archives]
    sp_check = subparsers.add_parser(
        "check",
        help="repo-wide broken-reference scan (gate semantics)",
    )
    sp_check.add_argument(
        "--include-archives",
        action="store_true",
        help="include paths containing an 'archive/' directory segment "
             "(default: excluded)",
    )

    # search <query>
    sp_search = subparsers.add_parser("search", help="keyword/concept search across the graph")
    sp_search.add_argument("query", help="search query")

    # ls <path>
    sp_ls = subparsers.add_parser("ls", help="list files under a path (filtered by graph membership)")
    sp_ls.add_argument("path", help="directory path (relative to cwd)")

    # outline <file>
    sp_outline = subparsers.add_parser("outline", help="show headers + signals for a file")
    sp_outline.add_argument("file", help="file path (relative to cwd)")

    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.verb:
        parser.print_help()
        return 0

    from .verbs import build, check, impact, ls, outline, refs, search

    handlers = {
        "build": build.run,
        "refs": refs.run,
        "ls": ls.run,
        "outline": outline.run,
        "impact": impact.run,
        "check": check.run,
        "search": search.run,
    }
    handler = handlers.get(args.verb)
    if handler is None:
        parser.error(f"unknown verb: {args.verb}")
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
