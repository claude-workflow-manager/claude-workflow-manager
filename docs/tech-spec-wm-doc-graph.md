# Tech Spec — `/wm:doc-graph`

Status: draft (v2.1 discovery)
Source decisions: FIN-005, FIN-006, FIN-007, FIN-008 (architecture); FIN-002, FIN-003, FIN-004, FIN-012 (consumer requirements)
Companion design doc: `projects/2026-04-11-workflow-commands-v2/plans/2026-04-11-workflow-commands-v2-design.md`

---

## 1. Overview

`/wm:doc-graph` is a new structural-map tool for markdown-heavy repositories. It builds and queries a graph of files, references, headers, and signal markers, and exposes that data through a small set of verbs (`refs`, `impact`, `check`, `search`, `ls`, `outline`, `build`). Its purpose is to give every WM workflow command a cheap, reliable way to ask *"what's in this repo and what depends on what"* without each command re-implementing the same Read/Grep dance.

The tool is **structural-only** (no WM-specific data baked into the graph file), **single-tool with no dispatcher** (no backend abstraction, no project-type detection), **incrementally rebuilt via mtime** (no daemon, no full rebuild on every call), and **single-repo scoped** (no cross-repo indexing). Each of these properties is the result of a deliberate design decision in the v2.1 discovery — see the linked FINs for rationale.

## 2. Tech Stack

| Choice | Why |
|---|---|
| **Python 3.x** | Matches the existing `ag:map-ref` reference implementation (companion `agent-studio` project). FIN-005 commits to a structural core shared in shape with `ag:map-ref` — same language minimizes drift between the two. |
| **YAML output** | Same as `ag:map-ref`. Human-readable, diffable, easy to parse from any consumer. |
| **Standard library only (or near-zero deps)** | The tool runs in every WM workflow execution; dependency overhead is friction. Markdown parsing for `@`-includes / headers / signals can be done with regex; no full markdown AST needed. |
| **Filesystem stat for cache** | FIN-007: incremental rebuild via mtime check. Stdlib `os.stat` is sufficient. |

Justifications for non-obvious choices:
- **Python over shell:** the parsing logic for `@`-includes, signal markers, and cross-references is non-trivial — shell would be a source of bugs. Python is also the existing convention for WM-adjacent tooling.
- **Not Node/TypeScript:** WM has no JS toolchain. Adding one for one tool is disproportionate.
- **Not a compiled binary:** the user's environment already has Python; a binary adds build/distribution complexity for marginal speed gain on a tool that already has incremental caching.

## 3. Architecture

```
┌──────────────────────────────────────────────────────────┐
│  /wm:doc-graph (Python entry point)                          │
│                                                          │
│  ┌────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Verb      │ →  │  Cache       │ →  │  Builder     │  │
│  │  dispatch  │    │  (mtime      │    │  (markdown   │  │
│  │            │    │   check)     │    │   parser)    │  │
│  └────────────┘    └──────────────┘    └──────────────┘  │
│         │                  │                   │        │
│         ▼                  ▼                   ▼        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Graph store (YAML on disk + in-memory)            │  │
│  │  files / refs (in/out) / headers / signals         │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│         ┌────────────────┼────────────────┐              │
│         ▼                ▼                ▼              │
│   FIN join (impact)  Path lookup    Search index         │
│   reads DECISIONS    (refs, ls,     (search verb)        │
│   at query time      outline,                            │
│   per FIN-005        check)                              │
└──────────────────────────────────────────────────────────┘
```

**Key properties:**

- The **graph store** contains zero WM-specific data (FIN-005). FIN/DECISIONS lookups happen at query time inside the `impact` verb's join logic.
- There is **no dispatcher** (FIN-006). One code path for one repo type (markdown-heavy).
- The **cache** is checked on every invocation; only files with newer `mtime` than the cache timestamp get re-parsed (FIN-007). A `--force` flag bypasses the check.
- The tool **only sees `cwd`** (FIN-008). No path outside `cwd` is parsed, indexed, or referenced.

## 4. Graph Schema (data model)

The graph file is a single YAML document. Schema below is the v2.1 target — it intentionally mirrors `ag:map-ref`'s shape so a Markdown-Agents project's `references/ref-map.yaml` is structurally compatible (FIN-005).

```yaml
schema_version: 1
generated_at: 2026-04-11T14:22:00Z         # ISO 8601
generator: wm-doc-graph
generator_version: 0.1.0
root: /abs/path/to/cwd                     # for sanity-checking; FIN-008 enforces single-repo

files:
  - path: skills/wm/workflows/verify-plan.md
    mtime: 1712835412                      # epoch seconds, source for cache invalidation
    size: 4123                             # bytes, optional
    headers:
      - { level: 1, text: "Verify Plan", line: 1 }
      - { level: 2, text: "Step 1 — Load project state", line: 11 }
      # ...
    signals:
      - { type: "purpose", line: 1 }
      - { type: "required_reading", line: 5 }
      - { type: "process", line: 10 }
      # ...
    refs_out:                              # what this file references
      - { target: "~/.claude/skills/wm/references/impact-scan.md", line: 7, kind: "include" }
      - { target: "projects/{name}/STATE.md", line: 12, kind: "path-mention" }
    refs_in:                               # what references this file (inverse index)
      - { source: "skills/wm/commands/wm/verify-plan.md", line: 4, kind: "include" }

# Optional inverse index for fast back-reference lookup;
# can be reconstructed from refs_out if omitted.
inverse_index: {}
```

**Notes:**

- **`headers`** and **`signals`** support the `outline` verb cheaply (no need to re-read the file).
- **`refs_out`** powers the forward-reference query from FIN-003 (planner's investigation).
- **`refs_in`** powers the back-reference query from FIN-002 (`refs <file>`). Can be derived from `refs_out` at build time or stored explicitly for speed.
- **WM-specific data is absent by design** (FIN-005). No `fin_index`, no `decisions_index`, no project state.

## 5. Verb / CLI surface

The complete verb set required by v2.1's consumer FINs.

| Verb | Signature | Used by FINs | Behavior |
|---|---|---|---|
| `build` | `wm-doc-graph build [--force]` | (build-time) | Build or refresh the graph file. Without `--force`, only re-parses files whose `mtime` is newer than the cache. With `--force`, full rebuild. |
| `refs` | `wm-doc-graph refs <file> [--out\|--in\|--both]` | FIN-002, FIN-003, FIN-012a | Return references for `<file>`. Default `--both`. `--out` = forward (what this file references), `--in` = back (what references this file). Errors clearly if `<file>` does not exist in the graph. |
| `impact` | `wm-doc-graph impact <files...> [--mode=light\|deep]` | FIN-002, FIN-004 (execute), FIN-012a | For the given file set, return: (1) FIN affected — joined at query time by reading `projects/*/DECISIONS.md`; (2) downstream consumers via `refs_in`; (3) plan/design drift via comparison with `projects/{name}/plans/`. Output shape matches the existing `references/impact-scan.md` shapes (light vs deep). |
| `check` | `wm-doc-graph check` | FIN-004 (verify, release), FIN-012a | Repo-wide broken-reference scan. Returns a list of files whose `refs_out` targets do not resolve. Exits non-zero if any are broken (so calling commands can use it as a hard gate). |
| `search` | `wm-doc-graph search <query>` | FIN-004 (learn) | Keyword/concept search across the graph. Ranks files by header / signal / content match. Returns a ranked file list. |
| `ls` | `wm-doc-graph ls <path>` | FIN-003 | List files under `<path>` filtered by graph membership (i.e., only files the graph knows about). Lightweight directory walk. |
| `outline` | `wm-doc-graph outline <file>` | FIN-003 | Return the headers + signal markers for `<file>` from the graph (no need to re-read the file). |

**General properties of all verbs:**

- All verbs trigger an mtime check at the start (cheap) and rebuild the affected portion of the graph if anything changed (FIN-007), unless the user passed `--no-refresh` (escape hatch for batch operations).
- All verbs write their output to stdout in either YAML or a text format selectable via `--format=yaml|text`. Default for human use: text. Default when called from a workflow: yaml (so the calling command can parse it).
- All verbs exit non-zero on hard errors. `check` additionally exits non-zero on *finding* broken references (gate semantics).
- No verb writes to any file other than the graph cache itself. No verb touches `DECISIONS.md`, `STATE.md`, or any project file.

## 6. Folder Structure

```
skills/wm/tools/wm-doc-graph/                  # tool root (TBD — see open question 1)
├── wm_doc_graph/
│   ├── __init__.py
│   ├── cli.py                             # entry point + verb dispatch
│   ├── builder.py                         # markdown parser + graph construction
│   ├── cache.py                           # mtime check + incremental rebuild
│   ├── store.py                           # YAML load/save
│   ├── verbs/
│   │   ├── refs.py
│   │   ├── impact.py                      # joins DECISIONS.md at query time
│   │   ├── check.py
│   │   ├── search.py
│   │   ├── ls.py
│   │   ├── outline.py
│   │   └── build.py
│   └── schema.py                          # schema constants + version
├── tests/
│   ├── fixtures/                          # tiny markdown repos for tests
│   └── test_*.py
└── README.md
```

The graph cache file lives at a fixed location inside `cwd` (TBD — see open question 1).

## 7. Build & Cache Strategy

Per FIN-007, the cache is the centerpiece of the build strategy.

**On every `/wm:doc-graph` invocation:**

1. Load the cache file (if it exists). Note the `generated_at` timestamp.
2. Walk `cwd` and stat every markdown file.
3. Compare each file's `mtime` to `generated_at`.
4. **Re-parse only files where `mtime > generated_at`** (or files in the cache that no longer exist on disk → mark deleted).
5. Update the in-memory graph; write the updated graph back to the cache file with a new `generated_at`.
6. Run the requested verb against the in-memory graph.

**Cold start (no cache):**

1. Walk `cwd`, parse every markdown file, build the full graph, write the cache.
2. Run the verb.

**`--force` mode:**

1. Ignore the cache, re-parse everything from scratch.
2. Overwrite the cache.

**Performance targets** (informal — to confirm during build):
- Cold start on the WM repo (~300 markdown files): under 5 seconds.
- Steady state with no file changes: under 100 ms (just stat + load cache + run verb).
- Single-file change rebuild: under 500 ms.

## 8. Error Handling

| Failure mode | Behavior |
|---|---|
| Cache file corrupted / unreadable | Log a warning, fall back to full rebuild as if `--force`, continue. |
| Source file unreadable | Skip the file, log a warning, continue building. The verb output flags the missing file as `unreadable`. |
| Verb called on a file outside `cwd` | Hard error: refuse and explain (FIN-008). Exit non-zero. |
| `check` finds broken references | Print the list of broken refs, exit non-zero (gate semantics). |
| `refs` / `outline` called on a file not in graph | Print a clear error, exit non-zero with the suggestion *"run `wm-doc-graph build` and retry"*. |
| `impact` cannot read `DECISIONS.md` | Run with empty FIN data, mark the FIN dimension as `unknown` in the output, continue. |

The tool never silently swallows errors. Every degraded mode is logged.

## 9. Testing Strategy

**Unit tests** for each verb against a fixture repo (`tests/fixtures/`). Fixture is a tiny markdown directory with known references, headers, and signals — assertions are exact.

**Cache tests**: build cache, edit a file, re-run, assert only the edited file was re-parsed (instrument the builder to track which files it touched).

**Schema tests**: round-trip YAML → in-memory → YAML, assert byte-stable output.

**Integration tests**: run the tool in a fixture that mimics a real WM project (`projects/`, `skills/wm/`, `DECISIONS.md`). Assert that:
- `impact` correctly joins FIN data from `DECISIONS.md` at query time.
- `check` finds known broken references in the fixture.
- `search` ranks expected files first for known queries.

**Compatibility tests**: build a graph in a Markdown-Agents fixture; assert the file shape is compatible with what `ag:map-ref` would produce in the same fixture (modulo extension fields). FIN-005's promise.

**No tests against live repos** in CI. Live repos are a manual smoke-test before release.

## 10. Dependencies & Integrations

**Runtime dependencies:**

- Python 3.x (already present in user's environment)
- Standard library only, ideally. If a YAML library is needed, prefer `ruamel.yaml` for byte-stable output, but plain `pyyaml` is acceptable.

**WM workflow integrations** (consumer-side, not built into the tool itself):

- `verify-plan` (FIN-002): calls `refs`, `impact`
- `plan` (FIN-003): calls `refs --out`, `ls`, `outline` during the investigation step
- `discover` (FIN-004): calls cross-project search via `impact` against active project paths
- `execute` (FIN-004): calls `impact` per wave (light mode)
- `verify` (FIN-004): calls `check` as a hard gate post-execution
- `release` (FIN-004): calls `check` as a hard gate pre-deploy
- `learn` (FIN-004): calls `search` for routing target suggestion
- `change` (FIN-012a): calls `refs`, `search`, `impact`, `check` across triage / scoped / deep paths

**External integrations:**

- None. `/wm:doc-graph` does not call out to MCP servers, web services, or external binaries.
- `code-review-graph` is not invoked from `/wm:doc-graph` (FIN-006). It remains an independent MCP that users can use directly outside this tool.

## 11. Open Technical Questions

These are *implementation*-level questions that don't block discovery but need to be settled during planning or early build. They are not the same as the discovery open questions, which were resolved by FIN-005 through FIN-008.

1. **Graph cache file location and name.** Candidates: `.wm-doc-graph.yaml` at `cwd` root (hidden, git-ignorable), `docs/wm-doc-graph.yaml` (visible, follows the original handoff suggestion), `references/ref-map.yaml` (matches `ag:map-ref` exactly). Trade-off: visibility vs git noise vs cross-tool naming.

2. **Reference parsing scope.** Which reference syntaxes does the parser recognize? At minimum: `@~/.claude/...`, `@./...`, relative markdown links `[text](path.md)`. Open: should it follow `@`-includes recursively across files, or only record direct references?

3. **Signal marker syntax.** `ag:map-ref` recognizes a specific set of XML-like tags (`<purpose>`, `<process>`, `<step name="...">`). Does `wm-doc-graph` use the same set, a superset, or something pluggable per repo?

4. **Search ranking.** Simple substring match? TF-IDF? Header/signal proximity boost? Affects how useful `learn` routing suggestions are. Probably start simple, iterate.

5. **`impact` deep-mode FIN classification.** The `impact-scan.md` deep procedure classifies each FIN as `unaffected / needs amendment / blocked`. Can `wm-doc-graph impact --mode=deep` automate this classification, or does it return the raw join data and let the caller classify? Probably the latter — the classification needs human or LLM judgment.

6. **Output format default.** `--format=yaml` for machine-readable or `--format=text` for humans? Should the default depend on whether stdin is a tty?

7. **Concurrency.** If two `/wm:doc-graph` invocations run at the same time (e.g., two parallel subagents), how do they coordinate cache writes? Probably a simple lockfile or "last writer wins" with corruption detection.

8. **Graph schema versioning.** `schema_version: 1` is in the schema. What happens when v2 ships? Migration on read, or a hard error with a `build --force` suggestion?

These are deferred to plan time, not blockers for finalizing discovery.
