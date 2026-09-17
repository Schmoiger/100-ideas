---
name: test-agent
model: sonnet
standards: [coding-standards.md, testing-standards.md]
rules: [conventional-commits.md]
---

## Role

This is a test agent for validation purposes.

---

## Required Standards (Read First!)

1. context/standards/coding-standards.md - Lines 1-50
2. context/standards/testing-standards.md - Lines 100-150

---

## Required Rules (Must Follow!)

1. context/rules/conventional-commits.md - Commit message format

---

## Critical Reminders (from standards above)

- ALWAYS use `uv run` for Python (tech-standards.md:34)
- Write tests BEFORE implementation (testing-standards.md:12)

---

## Workflow

1. Read requirements from {project-root}/artefacts/requirements.md
2. Execute task
3. Write output to {project-root}/artefacts/test/

---

## Deliverables

- Output files to {project-root}/artefacts/test/
