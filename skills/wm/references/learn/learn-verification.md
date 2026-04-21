# Learn — FIN Entry Quality Gate

Every lesson captured by `/wm:learn` is written as a FIN entry to a dev project's DECISIONS.md. Before writing, the entry must pass a quality gate that ensures the dev workflow can act on it without re-investigating.

A FIN entry that passes this gate is actionable — the dev team (or a future session) can go from the entry to a plan without needing to re-read the original session transcript.

---

## When this runs

Called from learn.md Step 6c, after the investigation checks (existing content scan, conflict detection, specificity). This gate evaluates the *FIN entry draft*, not the raw lesson.

---

## Quality criteria

### 1. Concrete trigger

The FIN entry's Decision field must describe *when* the change applies — not vague ("improve the workflow") but specific ("when Mode A identifies a fix, route to DECISIONS.md instead of editing the target file").

- **PASS:** The trigger names a specific step, mode, condition, or file.
- **NEEDS SHARPENING:** The trigger is identifiable but imprecise — could be made more specific.
- **REJECT:** No trigger is discernible — the entry is a wish, not a decision.

### 2. Actionable implementation

The Implementation field must describe enough for someone to write a plan without re-investigating:

- What file(s) to change
- What kind of change (add, edit, remove, restructure)
- What the change accomplishes in concrete terms

**PASS:** A developer reading only the FIN entry could draft a plan step.
**NEEDS SHARPENING:** The intent is clear but missing file paths or specifics.
**REJECT:** The implementation is vague ("update the workflow") with no concrete pointers.

### 3. Observable done-when

The Done-when field must describe something that can be checked — by reading a file, running a command, or observing behavior:

- **PASS:** "Step 5 contains a pre-check branch that runs before bucket classification" — verifiable by reading the file.
- **NEEDS SHARPENING:** "The routing works correctly" — true/false isn't observable without a test definition.
- **REJECT:** "Everything is improved" — not checkable.

---

## Procedure

1. Evaluate the FIN entry draft against all three criteria.
2. If all PASS → proceed to Step 7 (recommendation).
3. If any NEEDS SHARPENING → sharpen the entry (rewrite the weak field), re-evaluate. One retry. If still not PASS after retry, surface to user: "FIN entry quality issue: {field} is {problem}. Want to revise, accept as-is, or cancel?"
4. If any REJECT → do not proceed. Surface to user: "Cannot write FIN entry — {field} is too vague to act on. Revise or cancel?"

---

## Output

```
fin_quality:
  trigger: {PASS | NEEDS SHARPENING | REJECT}
  implementation: {PASS | NEEDS SHARPENING | REJECT}
  done_when: {PASS | NEEDS SHARPENING | REJECT}
  verdict: {PASS | NEEDS SHARPENING | REJECT}
  notes: {one-line summary if not all PASS}
```
