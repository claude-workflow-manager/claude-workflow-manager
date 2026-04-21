"""Schema constants and field definitions for the wm-doc-graph structural map.

The schema is intentionally compatible in shape with Markdown-Agents' ag:map-ref
output format (per FIN-005), so a wm-doc-graph cache built in either kind of
project is structurally interoperable modulo extension fields.
"""

# Schema version. Increment when the on-disk format changes incompatibly.
SCHEMA_VERSION = 1

# Generator identification written to the cache file header.
GENERATOR_NAME = "wm-doc-graph"

# Signal marker tag set — XML-like tags the parser recognizes inside markdown.
# Mirrors ag:map-ref's set so a graph built in a Markdown-Agents project is
# structurally compatible with the existing tool's output.
SIGNAL_TAGS = (
    "purpose",
    "process",
    "step",
    "required_reading",
    "autonomy",
    "stop_after",
)

# File extensions to index. v2.1 is markdown-only (FIN-006). Extending this
# tuple is intentionally NOT supported in v2.1 — code repos use code-review-graph
# via the separate /wm:code-graph slash command.
INDEXED_EXTENSIONS = (".md",)

# Reference kinds the parser emits in refs_out / refs_in entries.
REF_KIND_INCLUDE = "include"            # @-include directives (@~/path, @./path)
REF_KIND_LINK = "link"                  # markdown links [text](path.md)
REF_KIND_PATH_MENTION = "path-mention"  # bare path text inside required_reading

# Default cache file name (relative to cwd). Tech spec §11 question 1 — defaults
# to a hidden file at the repo root; can be moved during build if convention
# changes.
DEFAULT_CACHE_FILENAME = ".wm-doc-graph.yaml"

# Top-level keys in the cache file (referenced by store.py and verbs).
KEY_SCHEMA_VERSION = "schema_version"
KEY_GENERATED_AT = "generated_at"
KEY_GENERATOR = "generator"
KEY_GENERATOR_VERSION = "generator_version"
KEY_ROOT = "root"
KEY_FILES = "files"

# Per-file keys.
KEY_PATH = "path"
KEY_MTIME = "mtime"
KEY_SIZE = "size"
KEY_HEADERS = "headers"
KEY_SIGNALS = "signals"
KEY_REFS_OUT = "refs_out"
KEY_REFS_IN = "refs_in"
