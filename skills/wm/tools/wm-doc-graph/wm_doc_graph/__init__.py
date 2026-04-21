"""wm-doc-graph: structural map builder and querier for markdown-heavy repositories.

Builds a YAML graph of files, references, headers, and signal markers.
Used by WM workflow commands via the /wm:doc-graph slash command.

Scope (per FIN-005, FIN-006, FIN-008):
- Markdown only (.md files)
- Single tool, no dispatcher, no backend abstraction
- Single repo only (cwd-scoped)
- Structural data only — WM-specific FIN data joined at query time

See docs/tech-spec-wm-doc-graph.md for full specification.
"""

__version__ = "0.1.0"
