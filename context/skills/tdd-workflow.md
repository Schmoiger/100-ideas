---
name: tdd-workflow
description: Strict Detroit-School Test-Driven Development (RED-GREEN-REFACTOR) procedural guide
globs: ["**/tests/**", "**/*.test.py", "**/*.test.ts"]
---

# TDD Workflow Skill

---

## Overview

This skill details the procedural workflow for Detroit-School Test-Driven Development. All tests written using this workflow MUST comply with the testing rules defined in `context/rules/testing.md`.

---

## 1. Phase 1: RED Phase (Write Tests)

**Context Constraint:** You are PROHIBITED from reading existing implementation files in `src/`. You may only read the task specification, API contract, and type definitions.

### Naming Convention
- Test names MUST describe a behaviour. Use the `should` pattern: `test_<subject>_should_<behaviour>_when_<condition>`.
- Examples:
  - VALID: `test_sync_should_abort_when_delist_rate_exceeds_threshold`
  - INVALID: `test_abort_sync`

### Rules for Writing Tests
- **Intent-First:** Tests must describe behaviour as a caller observes it.
- **Pre-computed Expectations:** Expected values MUST be derived manually from the domain specification. NEVER compute expected values using the same algorithm being implemented.
- **Commit message:** `test(scope): description`

### Verification
- Run the tests. They MUST fail.
- **Crucial Rule:** If a test passes on the first run *before* GREEN phase, it was written against existing code. Delete it and rewrite it.

---

## 2. Phase 2: GREEN Phase (Implement)

- Write the *minimal* amount of code required to make the failing tests pass.
- You are PROHIBITED from modifying the test files during this phase.
- **Commit message:** `feat(scope): description`

### Verification
- Run the tests. Confirm they all pass.

---

## 3. Phase 3: REFACTOR Phase (Optional)

- Improve code quality, readability, and performance.
- You may modify implementation files. You may NOT modify or add new tests.
- **Verification:** Tests MUST still pass after every refactoring step.
- **Commit message:** `refactor(scope): description`
