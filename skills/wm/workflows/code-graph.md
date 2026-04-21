<purpose>
Thin wrapper around the `code-review-graph` MCP server. Gives users a
consistent `/wm:*` interface for code-graph operations on **code
repositories** — separate from `/wm:doc-graph` (which is for
markdown-heavy repositories). The workflow does not implement any
graph logic of its own; it dispatches verbs to the MCP's native tools
and relays their output.

**Why two tools:** markdown-heavy repos (WM itself, agent definitions,
design doc trees) need a parser for `@`-includes, signal markers, and
markdown links — the concerns `code-review-graph` is not built for.
Code repos have functions, imports, and type graphs — things
`code-review-graph` already models with 24 native tools. One tool per
repo type, no dispatcher, no shared backend (FIN-006).
</purpose>

<required_reading>
(none — this workflow is a thin dispatcher)
</required_reading>

<process>

<step name="Step 1 — Scope guard (markdown-only refusal)">
`/wm:code-graph` is for code repos, not markdown trees. Before
dispatching, check the working directory and refuse if any of these
hold:

1. **`agent.md` exists at `cwd`** — a Markdown-Agents agent directory
   is a markdown repository by convention. Refuse.
2. **No code markers present** — the directory contains no recognizable
   code-project root file: none of `package.json`, `pyproject.toml`,
   `Cargo.toml`, `go.mod`, `tsconfig.json`, `pom.xml`, `build.gradle`,
   `Gemfile`, `composer.json`, `mix.exs`, `Makefile`, `CMakeLists.txt`,
   `*.sln`, `*.csproj`, or a `src/` directory with non-markdown files.
3. **Markdown dominance** — more than 80% of first-level files under
   `cwd` are `.md` files. Treat as markdown-only.

On refusal, print:

```
/wm:code-graph refuses to run here — this looks like a markdown-only
directory (no code project markers found / agent.md present / >80% md).

Use /wm:doc-graph instead for structural queries on markdown repos.
```

Then STOP. Exit 2.
</step>

<step name="Step 2 — MCP availability check">
`/wm:code-graph` depends on the `code-review-graph` MCP server being
installed and registered in the user's Claude Code settings. Check
tool availability by inspecting whether any `mcp__code-review-graph__*`
tools are visible in the current session.

If not available, print:

```
code-review-graph MCP server not found.

Install it first, register it in ~/.claude/settings.json or .mcp.json,
then re-run /wm:code-graph.
```

Then STOP. Exit 2. Do NOT attempt to dispatch.
</step>

<step name="Step 3 — Parse verb + arguments">
The user invokes `/wm:code-graph <verb> [args...]`. The wrapper exposes
a curated subset of the MCP's 24 native tools — the highest-value
operations for interactive use. Map verbs to MCP tools at dispatch
time by inspecting the live `mcp__code-review-graph__*` tool list.

**Initial verb set** (start here; add more on demand):

| Verb | Purpose | Dispatches to |
|---|---|---|
| `query` | Find symbols, functions, or code patterns | nearest `mcp__code-review-graph__*query*` tool |
| `impact` | Blast-radius analysis for a proposed change | nearest `*impact*` tool |
| `architecture` | High-level structural overview of the repo | nearest `*architecture*` or `*overview*` tool |
| `search` | Full-text or symbol search across the graph | nearest `*search*` tool |
| `refs` | Find references to a symbol | nearest `*references*` or `*refs*` tool |
| `callers` | Find callers of a function | nearest `*callers*` tool |

If the user's verb doesn't match any wrapped operation, print the verb
table above plus a one-line hint: "For the full 24-tool surface, call
the mcp__code-review-graph__* tools directly."

If the user invokes `/wm:code-graph` with no verb, print the verb table
and STOP — do not dispatch.
</step>

<step name="Step 4 — Dispatch and relay">
Call the selected `mcp__code-review-graph__*` tool with the user's
remaining arguments mapped to the tool's expected parameters. Relay
the tool's output back to chat unchanged — do not summarize or reword.

If the MCP tool returns an error, surface it verbatim and exit non-zero.
</step>

</process>
