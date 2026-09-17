---
description: Strict invariants for technical writing and requirements
globs: ["**/*.md"]
alwaysApply: false
---

# Technical Writing Invariants

These are the strict, zero-token verifiable rules for all documentation and requirement writing.

---

## 1. British English

- All documentation MUST use British English spelling (e.g., `-ise` instead of `-ize`, `-our` instead of `-or`, `-re` instead of `-er`, `licence` (noun), `artefact`).
- Date format MUST be DD/MM/YYYY.

---

## 2. EARS Notation (Requirements)

Structured requirement syntax. All requirements (in `**/requirements.md`, `**/user-stories.md`) MUST use EARS patterns.

### Patterns

| Type | Syntax | Example |
|------|--------|---------|
| Ubiquitous | THE {system} SHALL {action} | THE system SHALL encrypt all user data |
| Event | WHEN {trigger}, THE {system} SHALL {action} | WHEN user clicks Save, THE system SHALL persist changes |
| State | WHILE {state}, THE {system} SHALL {action} | WHILE in maintenance mode, THE system SHALL show notice |
| Optional | IF {condition}, THE {system} SHALL {action} | IF user is admin, THE system SHALL show admin menu |
| Forbidden | THE {system} SHALL NOT {action} | THE system SHALL NOT log passwords |

### Combining

Chain clauses for complex requirements:

`WHEN {trigger}, IF {condition}, THE {system} SHALL {action}`

Example: WHEN user clicks Print, IF printer offline, THE system SHALL show error.
