---
description: Strict invariants for testing and quality gates
globs: ["**/tests/**", "**/*.test.*", "**/pytest*", "**/vitest*"]
alwaysApply: false
---

# Testing Invariants

**Applies to**: All agents running tests or writing code.

---

## 1. Quality Gates

1. **Never declare "success" without evidence**. You MUST report the actual coverage % and pass rate % (e.g. `Coverage: 91% | Pass rate: 100%`).
2. **Phase Thresholds**: Compare against the phase threshold defined in `testing-standards.md`.
3. **Actionable Suggestions**: Always end your testing report with 3 suggested next actions and a recommendation.

---

## 2. Testing Constraints

1. **Assert on Outcomes, Not Interactions**: You MUST assert against state, return values, or observable side effects.
2. **Minimise Mocks**: You are PROHIBITED from using interaction-based assertions (e.g., `mock.assert_called_once_with(...)`) for internal business-logic collaborators. Use real objects.
3. **Valid Mocking Boundaries**: You may ONLY use mocks at absolute I/O boundaries where using real objects is impossible or non-deterministic (Network, Database, Filesystem, Clock/Randomness).
