# Tech Spec Guidelines

## Purpose

Guide writing a Technical Specification for work type `app`. The tech spec answers "HOW technically" — it defines the implementation approach based on the PRD.

## Target audience

A developer who will implement the feature. Should contain enough detail to start coding without ambiguity about architecture, data model, or API shape.

## Tech Spec Structure

1. **Overview** — One paragraph summarizing what is being built and the technical approach.
2. **Tech Stack** — Languages, frameworks, libraries, and tools. Justify choices where non-obvious.
3. **Architecture** — High-level architecture (monolith, microservices, serverless, etc.). Component diagram if complex.
4. **Database Schema** — Tables/collections, fields, types, relationships, indexes. Include migration notes if modifying existing schema.
5. **API Endpoints** — Method, path, request/response format, auth requirements, error codes. For each endpoint.
6. **Folder Structure** — Project layout with brief description of each directory's purpose.
7. **Component Hierarchy** — For frontend: component tree, state management, data flow between components.
8. **Authentication & Authorization** — How auth works, roles, permissions, session handling.
9. **Error Handling** — Strategy for errors at each layer (API, UI, background jobs). User-facing error messages.
10. **Testing Strategy** — What to test, testing approach (unit, integration, e2e), coverage expectations.
11. **Dependencies & Integrations** — External services, third-party APIs, environment requirements.
12. **Open Technical Questions** — Unresolved technical decisions that need investigation or prototyping.

## How discovery feeds tech spec

During Phase 2 (gray areas), include technical gray areas:
- **Stack choices** — framework, language, database
- **Data model** — what entities, relationships, constraints
- **API shape** — REST/GraphQL, endpoint design, versioning
- **Auth approach** — how users authenticate, what permissions exist
- **Deployment** — where it runs, how it's deployed

## Inputs

- PRD (what to build)
- Design decisions from discovery conversation
- Existing codebase context (if applicable)

## Output

- **Format:** Markdown
- **Location:** `docs/tech-spec-{feature}.md`
