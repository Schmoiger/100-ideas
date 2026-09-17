# Handoff: {Service/Domain}

**From**: @{agent-name}
**To**: @{agent-name}
**Date**: {YYYY-MM-DD}
**Workflow**: {build|design|prototype|deploy|full-test|content|retrospective}
**Phase**: {phase-id from workflow YAML}
**Status**: {ready|blocked|needs_review|failed}

---

## Summary

{1-3 sentences describing what was completed and overall status. Max 500 characters.}

---

## Tasks Completed

| ID | Task | Status | Notes |
|----|------|--------|-------|
| {TASK-ID} | {task name} | complete/partial/blocked/skipped | {if not complete} |

---

## Next Tasks

| ID | Task | Priority | Depends On |
|----|------|----------|------------|
| {TASK-ID} | {task name} | critical/high/medium/low | {other task IDs} |

---

## Artefacts

- **Tests**: `{path}`
- **Source**: `{path}`
- **Config**: `{path}`
- **Docs**: `{path}`

---

## Blockers

{Only include if status ≠ "ready"}

| ID | Question | Impact |
|----|----------|--------|
| {BLOCKER-ID} | {what needs answering} | critical/high/medium/low |

---

## Context

**Architecture Reference**: `{path to architecture.md}`
**API Reference**: `{path to openapi.yaml}`

**Key Decisions**:
- {decision 1}
- {decision 2}

**Warnings**:
- {gotcha or non-obvious issue}

---

## Statistics

- **Tests**: {passing}/{total}
- **Coverage**: {percent}%
- **Files Created**: {count}
- **Files Modified**: {count}

---

## Commits

- `{hash}` - {commit message}
