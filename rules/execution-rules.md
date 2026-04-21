# Execution Rules

Active during: `/wm:execute`, building, implementation.

1. **Protect the main context.** For files over ~200 lines or broad exploration (3+ files), delegate to a subagent. Return only findings relevant to the current task.
2. **Don't narrate routine actions.** No "Reading file...", "Let me check...". Just do it, show results.
3. **Line-range reads by default.** Navigate structurally first (grep, glob, code graph), then read targeted line ranges. Whole-file reads are a conscious exception for small files (<100 lines) or when the full picture is genuinely needed. A single large file can consume 100K tokens; line ranges cost 5-10% of that.
4. **Delegate wisely.** Subagents for exploration (3+ files), code review, read-heavy tasks. Main thread for planning, user interaction, small edits (<3 files). All subagents return structured summaries (~1K tokens): status, files touched, key findings, next action suggestion.
5. **Model routing.** Haiku for discovery subagents (grep, file exploration, repo search), Sonnet for reviewer subagents and code review, Opus for main-thread reasoning, planning, and complex edits.
   Override per step when needed by adding `model: haiku|sonnet` to the step description.
6. **Advance autonomously within the plan.** Once a plan is approved (via `/wm:verify-plan` or explicit user go-ahead like "continue from handoff"), execute each step and report results — don't stop at step/wave boundaries for pacing approval. Valid reasons to stop: (a) `context-monitor.py` hook has fired a threshold warning (see communication-rules.md rule 10 for save-recommendation discipline across all modes), (b) decision outside the plan's scope, (c) error needing user judgment, (d) destructive/hard-to-reverse action per CLAUDE.md risk guidance. Commit cadence and "continue?" pacing questions are not valid reasons — pick a sensible default (commit per step, proceed through the plan) and keep going. "Natural checkpoint after completing X" is not a trigger.
