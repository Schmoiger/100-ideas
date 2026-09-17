---
name: architecture-fidelity
description: Procedural guidance for adhering to architecture docs and API contracts during implementation.
globs: ["**/*.py", "**/*.ts", "**/*.tsx"]
---

# Architecture Fidelity Skill

**Applies to**: All code implementation

---

## Before Writing Code

Read these architecture artefacts:

1. `{project-root}/artefacts/architecture/architecture.md` — service boundaries
2. `{project-root}/artefacts/architecture/api-catalogue.md` — port allocations
3. `{project-root}/artefacts/architecture/openapi.yaml` — API contracts

---

## Service Layer Rules

| Action | Correct | Wrong |
|--------|---------|-------|
| Fetch data | Call service layer (`DataService.get()`) | Direct Supabase/DB call from route or component |
| Service ports | Use port from api-catalogue.md | Invent new port or hardcode |
| API shape | Match openapi.yaml schema | Invent ad-hoc response format |
| New endpoint | Add to openapi.yaml first, then implement | Implement then document |

---

## Why

Skipping the service layer creates tight coupling to the database, makes testing harder, and creates tech debt. Port and API contract violations break service discovery and frontend integration.

---

## Forbidden

- Direct database calls outside the service layer
- Using ports not allocated in api-catalogue.md
- API responses that don't match openapi.yaml
- Creating new services without architecture.md entry
