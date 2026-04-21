# wm-doc-graph

Structural map builder/querier for markdown-heavy repositories. Implementation behind the `/wm:doc-graph` slash command.

**Scope:** markdown only (`.md` files). Code repos use `code-review-graph` directly via the separate `/wm:code-graph` slash command.

## References

- **Tech spec:** [`docs/tech-spec-wm-doc-graph.md`](../../../../docs/tech-spec-wm-doc-graph.md)
- **DECISIONS:** [`projects/archive/2026-04-11-workflow-commands-v2/DECISIONS.md`](../../../../projects/archive/2026-04-11-workflow-commands-v2/DECISIONS.md) — see FIN-005 through FIN-008 (architecture), FIN-018 (slash command + Skill dispatch)
- **Plan:** [`projects/archive/2026-04-11-workflow-commands-v2/plans/2026-04-11-workflow-commands-v2-plan.md`](../../../../projects/archive/2026-04-11-workflow-commands-v2/plans/2026-04-11-workflow-commands-v2-plan.md)

## Quick start

```bash
python -m wm_doc_graph --help
python -m wm_doc_graph build              # build / refresh the graph cache
python -m wm_doc_graph build --force      # full rebuild
python -m wm_doc_graph refs <file>        # show references for a file
python -m wm_doc_graph impact <files...>  # impact analysis
python -m wm_doc_graph check              # broken-reference scan (gate)
python -m wm_doc_graph search <query>     # keyword search
python -m wm_doc_graph ls <path>          # list files in graph under path
python -m wm_doc_graph outline <file>     # show headers + signals
```

Workflows invoke this tool via the `/wm:doc-graph` slash command (Skill dispatch), not raw Bash. The slash command + workflow file at `commands/wm/doc-graph.md` and `skills/wm/workflows/doc-graph.md` are the canonical entry point.

## Status

Plan steps 1.1 (this scaffold), 1.7, 1.8 are complete. Steps 1.2 (parser), 1.3 (cache), 2.1/2.2 (verb implementations), 3.1 (tests) are pending.
