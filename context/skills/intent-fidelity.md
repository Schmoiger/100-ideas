---
name: intent-fidelity
description: Procedural guidance for ensuring business and functional intent is clearly captured in requirements, tasks, and reflected faithfully in TDD and testing.
globs: ["**/requirements.md", "**/tasks.md", "**/user-stories.md"]
---

# Intent Fidelity Skill

**Applies to**: Writing requirements, defining tasks, and initiating implementation.

---

## 1. Capturing Intent in Requirements

When authoring or refining requirements, the underlying business or functional *intent* (the "why") must be unambiguous and verifiable.

- **Use EARS Notation**: Structure requirements using EARS patterns (e.g., `WHEN {trigger} THE {system} SHALL {action}`) to explicitly bind conditions to intended outcomes. (See `context/rules/tech-writing.md`).
- **State the "Why"**: Ensure that the overarching goal is stated before diving into mechanical constraints. A requirement should convey what value is being delivered or what invariant is being protected.

---

## 2. Reflecting Intent in Tasks

Task breakdowns (`tasks.md`) bridge the gap between high-level requirements and code implementation.

- **Direct Traceability**: Each task must explicitly serve a stated requirement. If a task's intent cannot be mapped back to a requirement or an architectural necessity, flag it for clarification.
- **Clear Acceptance Criteria**: Tasks must define *how* the completion of the intent will be verified. State what the system should do from an external observer's perspective when the task is complete.

---

## 3. Fidelity in Development and Testing (TDD)

The intent captured in requirements and tasks MUST be the driving force behind the development cycle, adhering strictly to the Detroit-School Test-Driven Development workflow defined in `context/skills/tdd-workflow.md`.

### The Intent-to-Test Pipeline

1. **RED Phase (Testing Intent)**:
   - Before writing any implementation code, translate the task's intent directly into a test.
   - Test names must describe the intended behaviour (e.g., `test_sync_should_abort_when_delist_rate_exceeds_threshold`).
   - Tests must assert the *business logic or user outcome* specified by the intent, rather than asserting internal implementation details or structural mechanics.

2. **GREEN Phase (Implementing Intent)**:
   - Write only the minimal implementation required to satisfy the intent defined by the failing test.

3. **Verification**:
   - The final suite of tests serves as the executable specification of the original intent. If the intent changes, the tests must change first.

---

## 4. Remediation

If at any point during task definition or TDD testing the intent becomes ambiguous, conflicting, or overly complex, **STOP**. Do not guess the intent. Escalate to the product owner or human user to clarify the requirements before proceeding to implementation.
