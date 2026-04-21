# PRD Guidelines

## Purpose

Guide writing a Product Requirements Document for work type `app`. The PRD answers "WHAT and WHY" — it defines the product, not the implementation.

## Target audience

Assume the reader is a **junior developer**. Requirements should be explicit, unambiguous, and avoid jargon where possible.

## PRD Structure

1. **Introduction/Overview** — Brief description of the feature and the problem it solves. State the goal.
2. **Goals** — Specific, measurable objectives for this feature.
3. **User Stories** — User narratives describing feature usage and benefits.
4. **Functional Requirements** — Specific functionalities the feature must have. Numbered, clear, concise (e.g., "The system must allow users to upload a profile picture.").
5. **Non-Goals (Out of Scope)** — What this feature will *not* include. Manages scope.
6. **Design Considerations** — UI/UX requirements, mockup references, relevant components/styles.
7. **Technical Considerations** — Known technical constraints, dependencies, suggestions (e.g., "Should integrate with the existing Auth module").
8. **Success Metrics** — How success will be measured (e.g., "Reduce support tickets related to X by 50%").
9. **Open Questions** — Remaining questions or areas needing further clarification.

## How discovery feeds PRD

During Phase 1 (open conversation), naturally ask about:
- **Problem/Goal** — "What problem does this solve for the user?"
- **Core Functionality** — "What are the key actions a user should be able to perform?"
- **Scope/Boundaries** — "Are there specific things this feature should NOT do?"
- **Success Criteria** — "How will we know when this is successfully implemented?"

Only ask when the answer isn't reasonably inferable from the conversation so far.

## Output

- **Format:** Markdown
- **Location:** `docs/prd-{feature}.md`
