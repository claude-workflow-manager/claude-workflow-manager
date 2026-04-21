# Workflow Manager — State Machine

## States

```
Full (T2):  between-cycles → backlog → planned → plan-verified → executing → awaiting-release → between-cycles
Light (T1): between-cycles → backlog → planned → executing → awaiting-release → between-cycles
Quick (T0): between-cycles → backlog → executing → awaiting-release → between-cycles
```

## Tier-Based State Flows

| Tier | Skipped states | Rationale |
|---|---|---|
| T0 ("Just do it") | `planned`, `plan-verified` | No plan file needed. Intent in commit message. |
| T1 ("Checklist") | `plan-verified` | Plan exists but too lightweight for formal verification. Step-level checks during execution. |
| T2 ("Plan-verified") | (none) | Full flow. Plan must be verified before execution. |

## State Descriptions

| State | Meaning | Valid actions |
|---|---|---|
| `between-cycles` | No active work. Starting point after release or project creation. | Start discover → advance to backlog |
| `backlog` | Discovery complete. Decisions captured in DECISIONS.md. Ready to plan. | Plan → advance to planned (T1/T2) or executing (T0) |
| `planned` | Plan written. Awaiting verification (T2) or execution (T1). | Verify plan (T2) → plan-verified. Execute (T1) → executing. |
| `plan-verified` | Plan verified and approved. Safe to execute. T2 only. | Execute → advance to executing |
| `executing` | Implementation in progress. Tasks being completed. | Complete tasks, verify → advance to awaiting-release |
| `awaiting-release` | Implementation verified. Ready to release. | Release → advance to between-cycles |

## State Transition Triggers

| Transition | Trigger | Tier |
|---|---|---|
| `between-cycles → backlog` | Discovery complete, at least one DECISIONS.md entry written | all |
| `backlog → planned` | Plan file written in `projects/{name}/plans/` | T1, T2 |
| `backlog → executing` | User starts execution directly (no plan file) | T0 |
| `planned → plan-verified` | Plan verification report presented and approved by user | T2 only |
| `planned → executing` | User starts execution (plan exists, verification skipped) | T1 only |
| `plan-verified → executing` | User starts execution (invokes `/wm:execute`) | T2 |
| `executing → awaiting-release` | All plan tasks complete, implementation verified | all |
| `awaiting-release → between-cycles` | Release steps complete, project archived | all |

## Gate-to-Transition Mapping

See `gate-matrix.md` for full gate details including tier-aware requirements.

| Transition | Gate | Hard/Soft/Skip by work type |
|---|---|---|
| `backlog → planned` | DECISIONS.md has entries | Hard: all types |
| `backlog → planned` | Archive copy made + committed | Soft: next-version, skill; Skip: others |
| `planned → plan-verified` | Plan verification report presented | Hard: T2 work types; Skip: T1 (verify-plan not required) |
| `plan-verified → executing` | Version bump recorded in DECISIONS.md | Hard: next-version, skill; Skip: others |
| `executing → awaiting-release` | All tasks have commits | Hard: all types |
| `awaiting-release → between-cycles` | DECISIONS.md entries all `status: applied` | Hard: next-version, skill, new, app; Skip: fix, new-agent, test |

## State Recovery

When `STATE.md` is missing or corrupt:

1. Check `projects/ACTIVE.md` for project entry — note last-updated state
2. Check `projects/{name}/plans/` — if plan exists, state is at least `planned`
3. Check git log for recent commits — if execution commits exist, state is `executing`
4. Check `projects/{name}/DECISIONS.md` — if entries exist, state is at least `backlog`
5. If no artifacts exist, state is `between-cycles`
6. Present inferred state to user: "I infer your state is [X] based on [evidence]. Confirm? (Y/N)"
7. On confirmation, write new STATE.md with inferred state
