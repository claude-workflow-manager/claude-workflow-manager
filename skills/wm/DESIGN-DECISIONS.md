# WM Design Decisions

## v2.0 — Agent Reasoning Quality + Token Optimization (2026-04-11)

Project: `2026-04-10-agent-reasoning-quality`

### FIN-002: Tool-gated investigation (PreToolUse Write|Edit)
Decision: Block or warn on writes to files the agent has not investigated. File read OR code graph query satisfies the gate.
Rationale: Mechanical enforcement of "investigate before editing" — can't be sycophanted away by rules text.

### FIN-003: 40% context ceiling with auto-warning (UserPromptSubmit)
Decision: Parse transcript JSONL tail on every prompt. Read last assistant entry's `usage.input_tokens + cache_read + cache_creation`, compare to context window, warn when crossing 40/50/60/70/80/90%.
Rationale: F1 drops from 0.55 to 0.3 at 40-50% context utilization. Proactive warning prevents degradation. User sets `USER_CONTEXT_WINDOW` constant (200K or 1M) since JSONL doesn't record window mode.

### FIN-005: Verification output capture (PostToolUse Bash)
Decision: First-token matcher on Bash commands (shlex tokenization, skip env vars, strip path prefix). When matched, write full output to `scratch/verification-output.log` and return ~500 token summary.
Rationale: Verification evidence is critical but raw output is the biggest context polluter. First-token matching prevents false positives from `echo pytest`, `grep pytest`, etc.

### FIN-006: Save/resume redesign — structured checkpoint + progressive disclosure
Decision: `handoff.md` is now a structured checkpoint under 500 tokens with State, Next action, How to execute, Key files. `resume.md` loads context scoped by state (executing→current plan step, between-cycles→DECISIONS.md, etc.). No full project state dump on resume.
Rationale: Disposable agents reason better without prior conversation baggage.

### FIN-007: Immediate decision save during discovery
Decision: `discover.md` saves each confirmed decision to `DECISIONS.md` immediately, not at the end of Phase 2. Step 5 becomes review-only.
Rationale: Long discovery sessions risk losing decisions on unexpected session end.

### FIN-008: Scoped agent rules replace monolithic AGENTS.md
Decision: AGENTS.md cut to ~310 tokens (project identity + pointers). 15 numbered rules moved to `.claude/rules/{discovery,execution,editing,review}-rules.md` (each under 300 tokens).
Rationale: ETH Zurich: LLM-generated context files degrade performance 3%. Attention dilution from always-on rule stacking.

### FIN-009: Subagent delegation rules + structured returns
Decision: Delegate discovery (3+ files), code review, read-heavy tasks to subagents. Keep planning, user interaction, small edits (<3 files) in main thread. All subagents return structured ~1K token summaries.
Rationale: Subagents cost 4-7x per spawn but protect main context from 80K+ token pollution. Net positive only with structured returns.

### FIN-010: L5 reviewer sees artifacts only
Decision: L5 reviewer subagent receives diff + test output + plan step intent. No primary agent narrative. Default model: Sonnet.
Rationale: Inter-agent sycophancy — reviewers validate framing instead of independently evaluating.

### FIN-011: Line-range reads as default
Decision: Navigate structurally first (grep, glob, code graph), then read targeted line ranges. Whole-file reads only for small files (<100 lines) or when the full picture is needed.
Rationale: One large file can consume 100K tokens; line ranges cost 5-10% of that.

### FIN-013: Code graph MCP server
Decision: Install `code-review-graph` as MCP server. Agent queries impact/callers/callees before editing. Abstracted behind interface — MCP server name is config, not workflow code.
Rationale: Structural navigation replaces expensive full-file reads (6.8-49x token savings per benchmarks).

### FIN-014: Cheap model routing for subagents
Decision: Haiku for discovery subagents, Sonnet for reviewer subagents, Opus for main thread. Configurable per step.
Rationale: Extends usage cap. Discovery/review don't need Opus-level reasoning.

### FIN-017: Retire inject-communication-rules.sh hook
Decision: Remove from `settings.json` UserPromptSubmit registration. Hook script retained on disk for rollback. Scoped rules + shorter sessions + disposable agents replace the periodic re-injection band-aid.
Rationale: Proper fix is three-layered (scoped rules + 40% ceiling + disposable agents). Re-injection was a band-aid for rule decay caused by the stacking it was supposed to work around.

### FIN-018: Hooks deploy in warn-only mode first
Decision: All 3 new hooks have `MODE = "warn"` by default. Log warnings but don't block. Flip to enforce after validation period.
Rationale: Tool gating false positives would block legitimate writes. Safer to validate accuracy first.

### Related improvements
- `execute.md` 5b: delegation rules block with model routing + structured return schema + L5 reviewer artifacts-only prompt (FIN-009, FIN-010, FIN-014)
- `verify.md` Step 3: L5 reviewer updated to match — artifacts only, Sonnet default
- `release.md` Step 4: rewritten — deploys scoped rules + new hooks, does not modify settings.json (manual), does not reinstall the retired injection hook

## v1.4 — Impact Scan & Adaptive Change (2026-04-07)

Project: `2026-04-07-verify-improvements`

### FIN-002: Shared impact-scan reference
Decision: One reference file (`references/impact-scan.md`) defining a 4-dimension scan (files / FIN / downstream / plan-design drift) with two modes (light, deep). Called from 4 entry points.
Rationale: Same scanning logic was needed in 4 places. A single source of truth prevents drift between callers.

### FIN-003: Adaptive `/wm:change` replaces `/wm:quick`
Decision: Hard-replace `/wm:quick` with `/wm:change`. New command always runs cheap triage (read target + grep symbol + DECISIONS check) and classifies as trivial/scoped/deep.
Rationale: `/wm:quick` could not self-assess scope without looking. Splitting into two commands was artificial — depth is the only real variable, and it can be auto-detected.

### FIN-004: `/wm:change` standalone + project-integrated
Decision: Auto-detect active project. If present, integrate with STATE / handoff / DECISIONS. If absent, run clean.
Rationale: Hot-fix in foreign repo is a real use case; forcing project context kills the lightweight value.

### FIN-005: Propose-before-edit applies to FIN updates
Decision: When deep mode discovers FIN entries that need amendment, agent must propose and wait. Never auto-update DECISIONS.md.
Rationale: Propose-before-edit is the core principle. Auto-updating FIN would violate it.

### FIN-006: Two-stage decision impact scanning
Decision: Light scan in `/wm:discover` (FIN-FIN conflict, conceptual) + deep scan in `/wm:verify-plan` and `/wm:execute` (file-level blast radius).
Rationale: Different lenses catch different classes of conflict — early/conceptual vs late/concrete. Both are cheap relative to the bugs they prevent.

## v1.3 — Native Planning & Execution (2026-03-22)

### FIN-002: Replace framework delegation with 3-tier native system
Decision: WM handles planning and execution natively using 3 tiers (T0/T1/T2) instead of routing to superpowers or GSD.
Rationale: Full control over process, scale ceremony by project type, no external dependencies.

### FIN-003: Hybrid tier classification — work type default + upgrade rules
Decision: Work type sets default tier (fix→T0, next-version→T1, app→T2). Agent auto-upgrades if task touches >3 files or modifies shared state.
Rationale: Fixed mapping too rigid, pure PI scoring too much friction. Sensible defaults with escape hatches.

### FIN-006: Native execution engine with RPI pattern and wave-based parallelism
Decision: T2 execution follows RPI. Steps in same wave with no shared files spawn parallel subagents (max 3).
Rationale: RPI keeps context clean. Wave parallelism proven effective. Single integrator rule prevents conflicts.

### FIN-007: Three deviation rules during execution
Decision: (1) Trivial fix → auto-fix + log. (2) Plan gap → pause + propose. (3) Architecture drift → stop + escalate. All logged.
Rationale: Plan drift is top AI failure mode. Simple rules prevent silent deviation.

### FIN-009: Native verification ladder
Decision: 5-level ladder: static, targeted tests, regression, smoke, reviewer subagent. Tier determines which levels activate.
Rationale: LLM self-verification unreliable. External reproducible evidence required.

## v1.2 — Command Decomposition (2026-03-18)

### FIN-002: Create workflows directory with 14 workflow files
Decision: Extract procedural logic from all 14 command files into `~/.claude/skills/wm/workflows/`.
Rationale: Separates routing (commands) from logic (workflows) — easier to maintain and evolve.

### FIN-003: Convert all 14 commands to thin triggers
Decision: Replace inline instructions in command files with GSD-style thin triggers.
Rationale: Commands should be routers, not executors — follows GSD proven pattern.

### FIN-004: 1:1 command-to-workflow mapping, self-contained workflows
Decision: Each command maps to exactly one workflow file. No shared helper workflows.
Rationale: Simplicity first — extract shared logic only when duplication is proven painful.

### FIN-005: Preserve existing references unchanged
Decision: Do not modify existing reference files (state-machine, gate-matrix, templates, etc.).
Rationale: References are config/lookup tables that already work.
